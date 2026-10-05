from flask import Blueprint, Response, abort, render_template, request

from .models import Developer, Game, Genre, Platform, avg_subquery, db, visible_games
from .util import cover_svg, paginate

bp = Blueprint("catalogo", __name__)


def with_avg(query):
    """Junta nota média (ignora avaliações ocultas) a uma query de jogos."""
    sub = avg_subquery()
    return query.outerjoin(sub, sub.c.gid == Game.id).add_columns(sub.c.avg), sub


@bp.route("/")
def home():
    q, sub = with_avg(visible_games())
    destaques = q.add_columns(sub.c.n).filter(sub.c.n >= 3).order_by(sub.c.avg.desc(), Game.title).limit(12).all()
    recentes = q.order_by(Game.release_date.desc(), Game.title).limit(6).all()
    return render_template("catalogo/home.html", destaques=destaques, recentes=recentes,
                           genres=Genre.query.order_by(Genre.name).all(), total=visible_games().count())


@bp.route("/capa/<slug>.svg")
def cover(slug):
    g = Game.query.filter_by(slug=slug).first()
    title = g.title if g else ""
    return Response(cover_svg(slug, title), mimetype="image/svg+xml", headers={"Cache-Control": "public, max-age=86400"})


def listing(model, slug, kind):
    obj = model.query.filter_by(slug=slug).first_or_404()
    base = visible_games().filter(getattr(Game, kind).any(model.id == obj.id) if kind != "developer" else Game.developer_id == obj.id)
    q, sub = with_avg(base)
    page = paginate(q.order_by(Game.title), request.args.get("page"))
    return render_template("catalogo/lista.html", obj=obj, kind=kind, page=page)


@bp.route("/generos/<slug>")
def genre(slug):
    return listing(Genre, slug, "genres")


@bp.route("/plataformas/<slug>")
def platform(slug):
    return listing(Platform, slug, "platforms")


@bp.route("/desenvolvedoras/<slug>")
def developer(slug):
    return listing(Developer, slug, "developer")
