from datetime import date
from types import SimpleNamespace

from app.fontes import FONTES, importar, steam
from app.models import Developer, Game, Genre, db


def item(i="1", **kw):
    base = dict(external_id=i, title=f"Jogo Real {i}", synopsis="Texto", release_date=date(2022, 2, 24),
                developer="Estúdio X", genres=["Ação", "RPG"], platforms=["Windows"], cover_url=f"https://img/{i}.jpg")
    return {**base, **kw}


def fonte(*itens):
    return SimpleNamespace(listar=lambda limite, termo=None: list(itens)[:limite])


def test_imp01_imp02_comando_e_fonte_plugavel(app):
    assert "steam" in FONTES and callable(FONTES["steam"].listar)
    FONTES["falsa"] = fonte(item("1"), item("2"))
    try:
        r = app.test_cli_runner().invoke(args=["import-games", "--fonte", "falsa", "--limite", "1"])
    finally:
        del FONTES["falsa"]
    assert "importados=1 ignorados=0 falhas=0" in r.output
    r = app.test_cli_runner().invoke(args=["import-games", "--fonte", "nao-existe"])
    assert r.exit_code != 0


def test_imp03_imp04_sem_duplicar_e_idempotente(app):
    with app.app_context():
        assert importar("falsa", modulo=fonte(item("1"), item("2", developer="Estúdio X", genres=["Ação"]))) == (2, 0, 0)
        assert Developer.query.count() == 1 and Genre.query.count() == 2
        g = Game.query.filter_by(external_id="1").one()
        assert g.source == "falsa" and [x.name for x in g.platforms] == ["Windows"]
        assert importar("falsa", modulo=fonte(item("1"), item("2"))) == (0, 2, 0)
        assert Game.query.count() == 2


def test_imp05_imp06_falha_e_dados_invalidos_nao_abortam(app):
    with app.app_context():
        r = importar("falsa", modulo=fonte({"erro": "x"}, item("1", title=""), item("2", release_date=None), item("3")))
        assert r == (1, 2, 1) and Game.query.count() == 1


def test_imp07_capa_real_ou_svg(app, client):
    with app.app_context():
        importar("falsa", modulo=fonte(item("1")))
        g = Game.query.one()
        slug = g.slug
        db.session.add(Game(title="Sem capa", slug="sem-capa", synopsis="s", release_date=date(2020, 1, 1), developer=g.developer))
        db.session.commit()
    assert b'src="https://img/1.jpg"' in client.get(f"/jogos/{slug}").data
    assert b'src="https://img/1.jpg"' in client.get("/").data or b"https://img/1.jpg" in client.get("/jogos").data
    assert b'src="/capa/sem-capa.svg"' in client.get("/jogos/sem-capa").data


def test_imp08_parse_de_data_da_steam():
    assert steam.parse_data("24/fev./2022") == date(2022, 2, 24)
    assert steam.parse_data("12 Oct, 2020") == date(2020, 10, 12)
    assert steam.parse_data("Oct 12, 2020") == date(2020, 10, 12)
    assert steam.parse_data("Em breve") is None and steam.parse_data("2023") is None


def test_imp08_listar_nao_levanta_com_rede_fora(monkeypatch):
    monkeypatch.setattr(steam, "_ids", lambda l, t: [1, 2])
    def falha(_):
        raise OSError("sem rede")
    monkeypatch.setattr(steam, "_jogo", falha)
    assert [x["erro"][:2] for x in steam.listar(2)] == ["1:", "2:"]


def test_imp09_deploy_importa_depois_do_seed():
    from pathlib import Path
    cmd = (Path(__file__).parent.parent / "render.yaml").read_text()
    assert cmd.index("seed") < cmd.index("import-games") and "|| true" in cmd
