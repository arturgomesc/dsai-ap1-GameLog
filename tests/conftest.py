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
