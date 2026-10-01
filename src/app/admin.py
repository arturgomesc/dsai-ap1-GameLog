from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request

from .models import AuditLog, Developer, Game, Genre, Platform, Report, Review, db, now
from .util import admin_required, current_user, paginate, slugify

bp = Blueprint("admin", __name__, url_prefix="/admin")
TAXONOMIES = {"generos": (Genre, "Gêneros"), "plataformas": (Platform, "Plataformas"), "desenvolvedoras": (Developer, "Desenvolvedoras")}


@bp.before_request
@admin_required  # ADM-01: toda rota /admin/* exige administrador (403) ou login (redirect)
def _guard():
    pass


def audit(action, detail=""):
    db.session.add(AuditLog(admin_id=current_user().id, action=action, detail=detail[:300]))  # ADM-09


@bp.route("/")
def index():
    return render_template(
        "admin/index.html", pending=Report.query.filter_by(status="pendente").count(), games=Game.query.count()
    )


# ---------- jogos ----------
def parse_game_form(f):
    errors, data = {}, {}
    title, synopsis = f.get("title", "").strip(), f.get("synopsis", "").strip()
    if not 1 <= len(title) <= 150:
        errors["title"] = "O título é obrigatório (até 150 caracteres)."
    if not synopsis:
        errors["synopsis"] = "A sinopse é obrigatória."
    try:
        data["release_date"] = date.fromisoformat(f.get("release_date", ""))
    except ValueError:
        errors["release_date"] = "Informe uma data de lançamento válida."
    dev = db.session.get(Developer, int(f["developer_id"])) if f.get("developer_id", "").isdigit() else None
    if not dev:
        errors["developer_id"] = "Escolha uma desenvolvedora."
    genres = Genre.query.filter(Genre.id.in_([int(x) for x in f.getlist("genre_ids") if x.isdigit()])).all()
    plats = Platform.query.filter(Platform.id.in_([int(x) for x in f.getlist("platform_ids") if x.isdigit()])).all()
    if not genres:
        errors["genre_ids"] = "Escolha ao menos um gênero."
    if not plats:
        errors["platform_ids"] = "Escolha ao menos uma plataforma."
    data.update(title=title, synopsis=synopsis, developer=dev, genres=genres, platforms=plats)
    return data, errors


def unique_slug(title, ignore_id=None):
    base = slug = slugify(title) or "jogo"
    n = 2
    while (other := Game.query.filter_by(slug=slug).first()) and other.id != ignore_id:
        slug, n = f"{base}-{n}", n + 1
    return slug


def game_form(game=None):
    errors, form = {}, request.form
    if request.method == "POST":
        data, errors = parse_game_form(request.form)
        if not errors:
            new = game is None
            game = game or Game()
            if new or game.title != data["title"]:
                game.slug = unique_slug(data["title"], game.id)  # antes de tocar nos atributos (autoflush)
            for k, v in data.items():
                setattr(game, k, v)
            db.session.add(game)
            db.session.flush()
            audit("jogo.criar" if new else "jogo.editar", f"{game.title} (#{game.id})")
            db.session.commit()
            flash("Jogo salvo.", "ok")
            return redirect("/admin/jogos")
    elif game:
        form = {"title": game.title, "synopsis": game.synopsis, "release_date": game.release_date.isoformat(),
                "developer_id": str(game.developer_id)}
    sel = {"genre_ids": {str(g.id) for g in game.genres} if game and request.method == "GET" else set(request.form.getlist("genre_ids")),
           "platform_ids": {str(p.id) for p in game.platforms} if game and request.method == "GET" else set(request.form.getlist("platform_ids"))}
    return render_template(
        "admin/jogo_form.html", game=game, errors=errors, form=form, sel=sel,
        genres=Genre.query.order_by(Genre.name).all(), platforms=Platform.query.order_by(Platform.name).all(),
        developers=Developer.query.order_by(Developer.name).all(),
    ), (400 if errors else 200)


@bp.route("/jogos")
def games():
    q = Game.query.order_by(Game.title)
    if request.args.get("q"):
        q = q.filter(Game.title.ilike(f"%{request.args['q']}%"))
    return render_template("admin/jogos.html", page=paginate(q, request.args.get("page")))


@bp.route("/jogos/novo", methods=["GET", "POST"])
def game_new():
    return game_form()


@bp.route("/jogos/<int:gid>/editar", methods=["GET", "POST"])
def game_edit(gid):
    return game_form(db.get_or_404(Game, gid))


@bp.route("/jogos/<int:gid>/remover", methods=["POST"])
def game_remove(gid):
    g = db.get_or_404(Game, gid)
    g.removed_at = now()  # soft delete (CAT-07)
    audit("jogo.remover", f"{g.title} (#{g.id})")
    db.session.commit()
    return redirect("/admin/jogos")


@bp.route("/jogos/<int:gid>/restaurar", methods=["POST"])
def game_restore(gid):
    g = db.get_or_404(Game, gid)
    g.removed_at = None
    audit("jogo.restaurar", f"{g.title} (#{g.id})")
    db.session.commit()
    return redirect("/admin/jogos")


# ---------- gêneros, plataformas, desenvolvedoras ----------
def taxonomy(kind):
    if kind not in TAXONOMIES:
        abort(404)
    return TAXONOMIES[kind]


@bp.route("/<kind>", methods=["GET", "POST"])
def tax_list(kind):
    model, label = taxonomy(kind)
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not 1 <= len(name) <= 80:
            flash("O nome é obrigatório (até 80 caracteres).", "erro")
        elif model.query.filter((model.name == name) | (model.slug == slugify(name))).first():
            flash("Já existe um item com esse nome.", "erro")
        else:
            db.session.add(model(name=name, slug=slugify(name)))
            audit(f"{kind}.criar", name)
            db.session.commit()
    items = model.query.order_by(model.name).all()
    return render_template("admin/taxonomia.html", kind=kind, label=label, items=items)


@bp.route("/<kind>/<int:iid>/editar", methods=["POST"])
def tax_edit(kind, iid):
    model, _ = taxonomy(kind)
    item, name = db.get_or_404(model, iid), request.form.get("name", "").strip()
    clash = model.query.filter(model.id != iid, (model.name == name) | (model.slug == slugify(name))).first()
    if not 1 <= len(name) <= 80 or clash:
        flash("Nome inválido ou já existente.", "erro")
    else:
        audit(f"{kind}.editar", f"{item.name} → {name}")
        item.name, item.slug = name, slugify(name)
        db.session.commit()
    return redirect(f"/admin/{kind}")


@bp.route("/<kind>/<int:iid>/apagar", methods=["POST"])
def tax_delete(kind, iid):
    model, _ = taxonomy(kind)
    item = db.get_or_404(model, iid)
    if item.games:  # ADM-04: item em uso não pode ser apagado
        flash(f"“{item.name}” está em uso por {len(item.games)} jogo(s) e não pode ser apagado.", "erro")
    else:
        audit(f"{kind}.apagar", item.name)
        db.session.delete(item)
        db.session.commit()
    return redirect(f"/admin/{kind}")


# ---------- moderação ----------
@bp.route("/denuncias")
def reports():
    status = request.args.get("status", "pendente")
    q = Report.query.filter_by(status=status)
    q = q.order_by(Report.created_at, Report.id) if status == "pendente" else q.order_by(Report.decided_at.desc())
    return render_template("admin/denuncias.html", page=paginate(q, request.args.get("page")), status=status)


def decide(rid, new_status, hide):
    rep = db.get_or_404(Report, rid)
    if rep.status != "pendente":
        flash("Esta denúncia já foi decidida.", "erro")
        return redirect("/admin/denuncias")
    targets = [rep]
    if hide:  # ocultar encerra todas as denúncias pendentes da mesma avaliação
        rep.review.hidden = True
        targets = Report.query.filter_by(review_id=rep.review_id, status="pendente").all()
    for r in targets:
        r.status, r.decided_by, r.decided_at = new_status, current_user().id, now()  # ADM-06
    audit(f"denuncia.{new_status}", f"avaliação #{rep.review_id}")
    db.session.commit()  # ADM-07: médias, histogramas e feed leem is hidden em tempo de consulta
    return redirect("/admin/denuncias")


@bp.route("/denuncias/<int:rid>/ocultar", methods=["POST"])
def report_hide(rid):
    return decide(rid, "ocultada", True)


@bp.route("/denuncias/<int:rid>/rejeitar", methods=["POST"])
def report_reject(rid):
    return decide(rid, "rejeitada", False)


@bp.route("/avaliacoes/<int:rid>/reverter", methods=["POST"])
def revert(rid):
    review = db.get_or_404(Review, rid)  # ADM-08
    review.hidden = False
    for r in Report.query.filter_by(review_id=rid, status="ocultada"):
        r.status = "revertida"
    audit("avaliacao.reverter", f"avaliação #{rid}")
    db.session.commit()
    return redirect("/admin/denuncias?status=ocultada")


@bp.route("/auditoria")
def audit_log():
    q = AuditLog.query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
    return render_template("admin/auditoria.html", page=paginate(q, request.args.get("page")))
