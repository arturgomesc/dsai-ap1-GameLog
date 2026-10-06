import os
import secrets
from urllib.parse import urlencode

import sqlite3

from flask import Flask, abort, render_template, request, session

from sqlalchemy import event
from sqlalchemy.engine import Engine

from .models import db
from .util import avatar_style, current_user, fold

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

    @event.listens_for(Engine, "connect")
    def _sqlite_fold(conn, _):  # busca sem acento/caixa (BUS-01)
        if isinstance(conn, sqlite3.Connection):
            conn.create_function("fold", 1, fold, deterministic=True)

    @app.before_request
    def csrf_protect():
        if request.method == "POST" and app.config["CSRF"]:
            token = session.get("csrf")
            if not token or token != request.form.get("csrf_token"):
                abort(400, "Token CSRF inválido")

    app.jinja_env.globals["avatar_style"] = avatar_style

    def page_url(n):  # preserva filtros multi-valor na paginação (BUS-05)
        args = [(k, v) for k, v in request.args.items(multi=True) if k != "page"] + [("page", n)]
        return f"{request.path}?{urlencode(args)}"

    app.jinja_env.globals["page_url"] = page_url
    app.jinja_env.filters["dictupdate"] = lambda d, u: {**d, **u}

    @app.context_processor
    def inject():
        def csrf_token():
            session.setdefault("csrf", secrets.token_hex(16))
            return session["csrf"]

        return {"me": current_user(), "csrf_token": csrf_token}

    def erro(code, msg):
        def handler(e):
            if request.path == "/api" or request.path.startswith("/api/"):  # API-08: JSON, nunca HTML
                from .api import erro as erro_json
                return erro_json(code, msg)
            return render_template("erro.html", code=code, msg=msg), code
        return handler

    for code, msg in {400: "Requisição inválida", 403: "Acesso negado", 404: "Página não encontrada",
                      405: "Método não permitido", 500: "Erro interno"}.items():
        app.register_error_handler(code, erro(code, msg))

    from . import cli, routes

    routes.register(app)
    cli.register(app)
    with app.app_context():
        db.create_all()
    return app
