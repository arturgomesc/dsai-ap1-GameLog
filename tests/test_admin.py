import pytest

from app.cli import create_admin
from app.models import AuditLog, Developer, Game, Genre, Report, Review, User, db, game_stats
from conftest import login, make_game, make_user

ROUTES = ["/admin/", "/admin/jogos", "/admin/jogos/novo", "/admin/generos", "/admin/plataformas",
          "/admin/desenvolvedoras", "/admin/denuncias", "/admin/auditoria"]


@pytest.fixture
def adm(app, client):
    make_user(app, "root", role="admin")
    login(client, "root")
    return client


def form_ok(app, **over):
    with app.app_context():
        g, d = Genre.query.first(), Developer.query.first()
        from app.models import Platform

        p = Platform.query.first()
        return {"title": "Novo Jogo", "synopsis": "Sinopse", "release_date": "2024-03-01", "developer_id": d.id,
                "genre_ids": [g.id], "platform_ids": [p.id], **over}


def test_adm01_403_para_nao_admin_e_login_para_visitante(app, client):
    for r in ROUTES:
        assert client.get(r).status_code == 302 and "/entrar" in client.get(r).headers["Location"]
    make_user(app, "ana")
    login(client, "ana")
    for r in ROUTES:
        assert client.get(r).status_code == 403, r
    assert client.post("/admin/jogos/1/remover").status_code == 403
    assert client.post("/admin/denuncias/1/ocultar").status_code == 403


def test_adm02_adm03_criar_editar_remover_restaurar(app, adm):
    make_game(app)
    ok = form_ok(app)
    assert adm.post("/admin/jogos/novo", data=ok).status_code == 302
    with app.app_context():
        g = Game.query.filter_by(title="Novo Jogo").one()
        gid = g.id
        assert g.slug == "novo-jogo"
    adm.post(f"/admin/jogos/{gid}/editar", data={**ok, "title": "Título Editado"})
    adm.post(f"/admin/jogos/{gid}/remover")
    with app.app_context():
        assert db.session.get(Game, gid).title == "Título Editado" and db.session.get(Game, gid).removed_at
    assert app.test_client().get("/jogos/novo-jogo").status_code == 404
    adm.post(f"/admin/jogos/{gid}/restaurar")
    with app.app_context():
        assert db.session.get(Game, gid).removed_at is None


@pytest.mark.parametrize("campo,valor", [("title", ""), ("synopsis", ""), ("release_date", "xx"),
                                          ("developer_id", ""), ("genre_ids", []), ("platform_ids", [])])
def test_adm03_validacao_por_campo(app, adm, campo, valor):
    make_game(app)
    r = adm.post("/admin/jogos/novo", data=form_ok(app, **{campo: valor}))
    assert r.status_code == 400 and 'class="err"' in r.get_data(as_text=True)
    with app.app_context():
        assert Game.query.count() == 1


def test_adm04_taxonomias_crud_e_item_em_uso(app, adm):
    make_game(app, genre="RPG", dev="Dev Z")
    adm.post("/admin/generos", data={"name": "Novo Gênero"})
    with app.app_context():
        novo = Genre.query.filter_by(name="Novo Gênero").one().id
        rpg = Genre.query.filter_by(name="RPG").one().id
        dev = Developer.query.one().id
    adm.post(f"/admin/generos/{novo}/editar", data={"name": "Renomeado"})
    adm.post(f"/admin/generos/{novo}/apagar")
    with app.app_context():
        assert Genre.query.filter_by(name="Renomeado").first() is None
    r = adm.post(f"/admin/generos/{rpg}/apagar", follow_redirects=True)
    assert "em uso" in r.get_data(as_text=True)
    assert "em uso" in adm.post(f"/admin/desenvolvedoras/{dev}/apagar", follow_redirects=True).get_data(as_text=True)
    with app.app_context():
        assert Genre.query.filter_by(name="RPG").count() == 1 and Developer.query.count() == 1
    adm.post("/admin/plataformas", data={"name": "Nova Plat"})
    assert adm.post("/admin/plataformas", data={"name": "Nova Plat"}, follow_redirects=True).status_code == 200


def reported(app, adm_client):
    slug = make_game(app)
    make_user(app, "autor")
    make_user(app, "denunciante")
    ca, cd = app.test_client(), app.test_client()
    login(ca, "autor")
    login(cd, "denunciante")
    ca.post(f"/jogos/{slug}/avaliar", data={"score": 10, "text": "texto polêmico"})
    with app.app_context():
        rid = Review.query.one().id
    cd.post(f"/avaliacoes/{rid}/denunciar", data={"reason": "ofensivo", "comment": "agressivo"})
    return slug, rid


def test_adm05_fila_pendentes_mais_antigas_primeiro(app, adm):
    slug, rid = reported(app, adm)
    make_user(app, "outro")
    co = app.test_client()
    login(co, "outro")
    co.post(f"/avaliacoes/{rid}/denunciar", data={"reason": "spam"})
    h = adm.get("/admin/denuncias").get_data(as_text=True)
    assert "texto polêmico" in h and "@autor" in h and "ofensivo" in h and "@denunciante" in h
    assert h.index("@denunciante") < h.index("@outro")


def test_adm06_decisao_registra_quem_e_quando(app, adm):
    slug, rid = reported(app, adm)
    with app.app_context():
        repid = Report.query.one().id
    adm.post(f"/admin/denuncias/{repid}/rejeitar")
    with app.app_context():
        r = Report.query.one()
        assert r.status == "rejeitada" and r.decided_at and r.decider.username == "root"
        assert Review.query.one().hidden is False
    assert adm.post(f"/admin/denuncias/{repid}/ocultar", follow_redirects=True).status_code == 200
    with app.app_context():
        assert Review.query.one().hidden is False  # já decidida


def test_adm07_adm08_ocultar_atualiza_e_reverter(app, adm):
    slug, rid = reported(app, adm)
    c = app.test_client()
    make_user(app, "seguidor")
    login(c, "seguidor")
    c.post("/u/autor/seguir")
    assert "texto polêmico" in app.test_client().get(f"/jogos/{slug}").get_data(as_text=True)
    assert "avaliou" in c.get("/feed").get_data(as_text=True)
    with app.app_context():
        repid = Report.query.one().id
        gid = Review.query.one().game_id
    adm.post(f"/admin/denuncias/{repid}/ocultar")
    with app.app_context():
        assert game_stats(gid)["total"] == 0 and Report.query.one().status == "ocultada"
    assert "texto polêmico" not in app.test_client().get(f"/jogos/{slug}").get_data(as_text=True)
    assert "avaliou" not in c.get("/feed").get_data(as_text=True)
    adm.post(f"/admin/avaliacoes/{rid}/reverter")
    with app.app_context():
        assert game_stats(gid)["total"] == 1 and Report.query.one().status == "revertida"
    assert "texto polêmico" in app.test_client().get(f"/jogos/{slug}").get_data(as_text=True)


def test_adm09_auditoria_paginada(app, adm):
    make_game(app)
    for i in range(25):
        adm.post("/admin/generos", data={"name": f"G{i}"})
    h = adm.get("/admin/auditoria").get_data(as_text=True)
    assert "generos.criar" in h and "@root" in h and "Página 1 de 2" in h
    assert adm.get("/admin/auditoria?page=2").status_code == 200


def test_adm10_admin_criado_por_cli_com_env(app, monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "chefe@ex.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "segredo-longo")
    r = app.test_cli_runner().invoke(args=["create-admin"])
    assert "admin criado" in r.output
    with app.app_context():
        u = User.query.filter_by(email="chefe@ex.com").one()
        assert u.is_admin and "segredo-longo" not in u.password_hash
    assert "admin já existe" in app.test_cli_runner().invoke(args=["create-admin"]).output
    monkeypatch.delenv("ADMIN_EMAIL")
    assert app.test_cli_runner().invoke(args=["create-admin"]).exit_code != 0
    import pathlib

    assert "segredo-longo" not in "".join(p.read_text() for p in pathlib.Path("src").rglob("*.py"))
