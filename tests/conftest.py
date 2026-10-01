import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from app import create_app  # noqa: E402
from app.models import db  # noqa: E402


@pytest.fixture
def app(tmp_path):
    app = create_app({"TESTING": True, "CSRF": False, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path}/t.db"})
    yield app
    with app.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


def make_user(app, username="ana", email=None, password="senha1234", role="jogador"):
    from werkzeug.security import generate_password_hash

    from app.models import User

    with app.app_context():
        u = User(
            username=username,
            username_lower=username.lower(),
            email=email or f"{username}@ex.com",
            password_hash=generate_password_hash(password),
            display_name=username,
            role=role,
        )
        db.session.add(u)
        db.session.commit()
        return u.id


def login(client, username="ana", password="senha1234"):
    return client.post("/entrar", data={"email": f"{username}@ex.com", "password": password})


def make_game(app, title="Jogo Teste", genre="Ação", platform="PC", dev="Dev Um", year=2020):
    from datetime import date

    from app.models import Developer, Game, Genre, Platform
    from app.util import slugify

    with app.app_context():
        g = Genre.query.filter_by(name=genre).first() or Genre(name=genre, slug=slugify(genre))
        p = Platform.query.filter_by(name=platform).first() or Platform(name=platform, slug=slugify(platform))
        d = Developer.query.filter_by(name=dev).first() or Developer(name=dev, slug=slugify(dev))
        game = Game(title=title, slug=slugify(title), synopsis="Sinopse.", release_date=date(year, 5, 1),
                    developer=d, genres=[g], platforms=[p])
        db.session.add(game)
        db.session.commit()
        return game.slug
