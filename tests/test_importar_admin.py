from datetime import date

import pytest

from app.fontes import steam
from app.models import AuditLog, Game
from conftest import login, make_user

DETALHE = {"external_id": "42", "title": "Hades", "synopsis": "Fuja do inferno.", "release_date": date(2020, 9, 17),
           "developer": "Supergiant", "genres": ["Ação"], "platforms": ["Windows"], "cover_url": "https://img/42.jpg"}


@pytest.fixture
def adm(app, client, monkeypatch):
    make_user(app, "root", role="admin")
    login(client, "root")
    monkeypatch.setattr(steam, "buscar", lambda q, n=10: [
        {"external_id": "42", "title": "Hades", "cover_url": "https://img/42.jpg"},
        {"external_id": "43", "title": "Hades II", "cover_url": None}][:n])
    monkeypatch.setattr(steam, "detalhe", lambda i: DETALHE if i == "42" else None)
    return client


def importar(c, i="42"):
    return c.post("/admin/importar", data={"external_id": i, "q": "hades"})


def test_iad01_so_admin_e_link_no_painel(app, client, adm):
    assert b"/admin/importar" in adm.get("/admin/").data
    make_user(app, "ana")
    anon, outro = app.test_client(), app.test_client()
    assert anon.get("/admin/importar").status_code in (302, 401, 403)
    login(outro, "ana")
    assert outro.get("/admin/importar").status_code == 403


def test_iad02_busca_lista_resultados_e_marca_existentes(adm):
    assert adm.get("/admin/importar?q=h").data.count(b"Importar</button>") == 0  # mínimo 2 caracteres
    html = adm.get("/admin/importar?q=hades").data.decode()
    assert html.count("Importar</button>") == 2 and "https://img/42.jpg" in html
    importar(adm)
    html = adm.get("/admin/importar?q=hades").data.decode()
    assert html.count("Importar</button>") == 1 and "No catálogo" in html


def test_iad03_importar_cria_e_redireciona(app, adm):
    r = importar(adm)
    assert r.status_code == 302 and r.headers["Location"] == "/jogos/hades"
    with app.app_context():
        g = Game.query.one()
        assert (g.source, g.external_id, g.cover_url) == ("steam", "42", "https://img/42.jpg")
    assert "importado" in adm.get("/jogos/hades").data.decode()


def test_iad04_nao_duplica(app, adm):
    importar(adm)
    r = importar(adm, "42")
    assert r.headers["Location"] == "/jogos/hades"
    assert "já estava no catálogo" in adm.get("/jogos/hades").data.decode()
    with app.app_context():
        assert Game.query.count() == 1


def test_iad05_fonte_fora_do_ar(app, adm, monkeypatch):
    def cai(*a, **k):
        raise OSError("sem rede")
    monkeypatch.setattr(steam, "buscar", cai)
    monkeypatch.setattr(steam, "detalhe", cai)
    r = adm.get("/admin/importar?q=hades")
    assert r.status_code == 200 and "A fonte não respondeu" in r.data.decode()
    assert importar(adm).status_code == 302
    assert "A fonte não respondeu" in adm.get("/admin/importar?q=hades").data.decode()
    with app.app_context():
        assert Game.query.count() == 0


def test_iad06_item_invalido(app, adm, monkeypatch):
    monkeypatch.setattr(steam, "detalhe", lambda i: {**DETALHE, "release_date": None} if i == "7" else None)
    for i in ("7", "99"):
        assert importar(adm, i).headers["Location"] == "/admin/importar?q=hades"
        assert "não é um jogo" in adm.get("/admin/importar?q=hades").data.decode()
    with app.app_context():
        assert Game.query.count() == 0


def test_iad07_auditoria(app, adm):
    importar(adm)
    importar(adm)  # duplicado não audita
    with app.app_context():
        logs = AuditLog.query.filter_by(action="jogo.importar").all()
        assert len(logs) == 1 and "Hades" in logs[0].detail and "steam:42" in logs[0].detail


def test_iad08_fonte_steam_tem_buscar_e_detalhe():
    assert callable(steam.buscar) and callable(steam.detalhe)


def test_iad09_csrf_exigido(app, monkeypatch):
    app.config["CSRF"] = True
    make_user(app, "root", role="admin")
    c = app.test_client()
    login(c, "root")
    assert c.post("/admin/importar", data={"external_id": "42"}).status_code == 400
