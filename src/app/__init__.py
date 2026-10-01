import os
import secrets

from flask import Flask, abort, render_template, request, session

from .models import db
from .util import avatar_style, current_user

BLUEPRINTS = []  # preenchido por register_blueprints(); um módulo por spec


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
        SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "sqlite:///gamelog.db"),
        CSRF=True,
    )
    app.config.update(config or {})
    db.init_app(app)

    @app.before_request
    def csrf_protect():
        if request.method == "POST" and app.config["CSRF"]:
            token = session.get("csrf")
            if not token or token != request.form.get("csrf_token"):
                abort(400, "Token CSRF inválido")

    app.jinja_env.globals["avatar_style"] = avatar_style
    app.jinja_env.filters["dictupdate"] = lambda d, u: {**d, **u}

    @app.context_processor
    def inject():
        def csrf_token():
            session.setdefault("csrf", secrets.token_hex(16))
            return session["csrf"]

        return {"me": current_user(), "csrf_token": csrf_token}

    for code, msg in {400: "Requisição inválida", 403: "Acesso negado", 404: "Página não encontrada"}.items():
        app.register_error_handler(
            code, lambda e, code=code, msg=msg: (render_template("erro.html", code=code, msg=msg), code)
        )
    app.register_error_handler(500, lambda e: (render_template("erro.html", code=500, msg="Erro interno"), 500))

    from . import cli, routes

    routes.register(app)
    cli.register(app)
    with app.app_context():
        db.create_all()
    return app
