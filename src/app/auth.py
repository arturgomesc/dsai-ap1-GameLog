import re
from datetime import timedelta

from flask import Blueprint, abort, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from .models import Activity, Follow, GameList, LoginAttempt, Review, User, db, now
from .perfil import dados as dados_perfil
from .util import current_user, login_required, safe_next

bp = Blueprint("auth", __name__)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USER_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")
MAX_FAILS, WINDOW = 5, timedelta(minutes=15)


def validate_signup(username, email, password):
    errors = {}
    if not USER_RE.match(username):
        errors["username"] = "Use de 3 a 20 caracteres (letras, números ou _)."
    elif User.query.filter_by(username_lower=username.lower()).first():
        errors["username"] = "Nome de usuário já em uso."
    if not EMAIL_RE.match(email):
        errors["email"] = "Informe um e-mail válido."
    elif User.query.filter_by(email=email.lower()).first():
        errors["email"] = "E-mail já cadastrado."
    if len(password) < 8:
        errors["password"] = "A senha deve ter no mínimo 8 caracteres."
    return errors


def start_session(user):
    session.clear()
    session["uid"], session["sv"] = user.id, user.session_version


@bp.route("/cadastro", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        f = request.form
        username, email, password = f.get("username", "").strip(), f.get("email", "").strip(), f.get("password", "")
        errors = validate_signup(username, email, password)
        if errors:
            return render_template("auth/cadastro.html", errors=errors, form=f), 400
        user = User(
            username=username,
            username_lower=username.lower(),
            email=email.lower(),
            password_hash=generate_password_hash(password),
            display_name=username,
            role="jogador",  # CAD-10: todo cadastro novo é jogador
        )
        db.session.add(user)
        db.session.commit()
        start_session(user)
        flash("Conta criada! Bem-vindo ao GameLog.", "ok")
        return redirect(safe_next(request.args.get("next")))
    return render_template("auth/cadastro.html", errors={}, form={})


@bp.route("/entrar", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email, password = request.form.get("email", "").strip().lower(), request.form.get("password", "")
        since = now() - WINDOW
        fails = LoginAttempt.query.filter(LoginAttempt.email == email, LoginAttempt.at >= since).count()
        if fails >= MAX_FAILS:  # CAD-04
            flash("Muitas tentativas. Tente novamente em 15 minutos.", "erro")
            return render_template("auth/login.html", form=request.form), 429
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            LoginAttempt.query.filter_by(email=email).delete()
            db.session.commit()
            start_session(user)
            return redirect(safe_next(request.args.get("next")))
        db.session.add(LoginAttempt(email=email))
        db.session.commit()
        flash("E-mail ou senha incorretos.", "erro")  # CAD-03: mensagem genérica
        return render_template("auth/login.html", form=request.form), 401
    return render_template("auth/login.html", form={})


@bp.route("/sair", methods=["POST"])
def logout():
    u = current_user()
    if u:
        u.session_version += 1
        db.session.commit()
    session.clear()
    return redirect("/")


@bp.route("/u/<username>")
def profile(username):
    user = User.query.filter_by(username_lower=username.lower()).first_or_404()
    me = current_user()
    own = me is not None and me.id == user.id
    lists = GameList.query.filter_by(user_id=user.id)
    if not own:
        lists = lists.filter_by(public=True)
    extra = dados_perfil(user.id, request.args.get("page"))
    stats = {
        "avaliacoes": extra["total"],  # PRF-06: mesmo critério das estatísticas (sem ocultas nem jogos removidos)
        "listas": lists.count(),
        "seguidores": Follow.query.filter_by(followed_id=user.id).count(),
        "seguindo": Follow.query.filter_by(follower_id=user.id).count(),
    }
    following = bool(me and not own and Follow.query.filter_by(follower_id=me.id, followed_id=user.id).first())
    return render_template(
        "auth/perfil.html", u=user, own=own, stats=stats, following=following, lists=lists.limit(10).all(),
        **extra,
    )


@bp.route("/u/<username>/editar", methods=["GET", "POST"])
@login_required
def edit_profile(username):
    user = User.query.filter_by(username_lower=username.lower()).first_or_404()
    if current_user().id != user.id:
        abort(403)  # CAD-09
    errors = {}
    if request.method == "POST":
        name, bio = request.form.get("display_name", "").strip(), request.form.get("bio", "").strip()
        if not 1 <= len(name) <= 60:
            errors["display_name"] = "Nome de exibição deve ter de 1 a 60 caracteres."
        if len(bio) > 280:
            errors["bio"] = "A bio deve ter até 280 caracteres."
        if not errors:
            user.display_name, user.bio = name, bio
            db.session.commit()
            flash("Perfil atualizado.", "ok")
            return redirect(f"/u/{user.username}")
        return render_template("auth/editar.html", u=user, errors=errors, form=request.form), 400
    return render_template("auth/editar.html", u=user, errors={}, form={"display_name": user.display_name, "bio": user.bio})
