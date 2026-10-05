import os

import click
from werkzeug.security import generate_password_hash

from .models import User, db


def create_admin(email, password, username="admin"):
    """ADM-10: credenciais vêm de variável de ambiente, nunca do código."""
    if User.query.filter_by(email=email.lower()).first():
        return False
    db.session.add(
        User(
            username=username,
            username_lower=username.lower(),
            email=email.lower(),
            password_hash=generate_password_hash(password),
            display_name="Administrador",
            role="admin",
        )
    )
    db.session.commit()
    return True


def register(app):
    @app.cli.command("seed")
    @click.option("--seed", default=42)
    def seed_cmd(seed):
        """Popula o banco com dados fictícios reproduzíveis."""
        from .seed import run

        run(seed)
        click.echo("seed ok")
        email, pw = os.environ.get("ADMIN_EMAIL"), os.environ.get("ADMIN_PASSWORD")
        if email and pw and create_admin(email, pw):
            click.echo("admin criado")

    @app.cli.command("create-admin")
    def create_admin_cmd():
        email, pw = os.environ.get("ADMIN_EMAIL"), os.environ.get("ADMIN_PASSWORD")
        if not (email and pw):
            raise click.UsageError("defina ADMIN_EMAIL e ADMIN_PASSWORD")
        click.echo("admin criado" if create_admin(email, pw) else "admin já existe")

    @app.cli.command("import-games")
    @click.option("--fonte", default="steam")
    @click.option("--limite", default=40)
    @click.option("--termo", default=None)
    def import_games_cmd(fonte, limite, termo):
        """Importa jogos reais de uma fonte externa (padrão: Steam, sem chave)."""
        from .fontes import FONTES, importar

        if fonte not in FONTES:
            raise click.UsageError(f"fonte desconhecida; use uma de {sorted(FONTES)}")
        ok, ign, erro = importar(fonte, limite, termo)
        click.echo(f"importados={ok} ignorados={ign} falhas={erro}")
