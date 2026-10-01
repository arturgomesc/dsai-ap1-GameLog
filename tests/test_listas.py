import pytest

from app.models import Game, GameList, ListItem, Review, Status, db, now
from conftest import login, make_game, make_user


@pytest.fixture
def ctx(app, client):
    make_user(app, "ana")
    login(client, "ana")
    return client


def new_list(client, name="L", vis="publica"):
    r = client.post("/listas", data={"name": name, "visibility": vis})
    return int(r.headers["Location"].rsplit("/", 1)[1]) if r.status_code == 302 else None


def add(client, slug, lid):
    return client.post(f"/jogos/{slug}/adicionar-a-lista", data={"list_id": lid}, follow_redirects=True)


def test_lis01_lis02_um_status_trocar_remover(app, ctx):
    slug = make_game(app)
    ctx.post(f"/jogos/{slug}/status", data={"status": "planejado"})
    ctx.post(f"/jogos/{slug}/status", data={"status": "jogando"})
    with app.app_context():
        assert [s.value for s in Status.query] == ["jogando"]
    ctx.post(f"/jogos/{slug}/status", data={"status": "invalido"})
    with app.app_context():
        assert Status.query.one().value == "jogando"
    ctx.post(f"/jogos/{slug}/status", data={"status": ""})
    with app.app_context():
        assert Status.query.count() == 0


def test_lis03_meus_jogos_agrupa_filtra_pagina(app, ctx):
    slugs = [make_game(app, f"J{i:02d}") for i in range(25)]
    for i, s in enumerate(slugs):
        ctx.post(f"/jogos/{s}/status", data={"status": "jogado" if i < 22 else "planejado"})
    h = ctx.get("/meus-jogos").get_data(as_text=True)
    assert h.count('class="panel"') == 20 and "Planejado (3)" in h
    h = ctx.get("/meus-jogos?status=planejado").get_data(as_text=True)
    assert h.count('class="panel"') == 3
    assert ctx.get("/meus-jogos?page=2").status_code == 200


def test_lis04_criar_lista_validacoes(app, ctx):
    assert new_list(ctx, "") is None
    assert ctx.post("/listas", data={"name": "x" * 81}).status_code == 400
    lid = new_list(ctx, "x" * 80)
    assert lid and ctx.get(f"/listas/{lid}").status_code == 200
    with app.app_context():
        assert db.session.get(GameList, new_list(ctx, "Priv", "privada")).public is False


def test_lis05_so_o_dono_edita_e_apaga(app, ctx):
    lid = new_list(ctx)
    make_user(app, "bia")
    c2 = app.test_client()
    login(c2, "bia")
    assert c2.post(f"/listas/{lid}/editar", data={"name": "hack"}).status_code == 403
    assert c2.post(f"/listas/{lid}/apagar").status_code == 403
    ctx.post(f"/listas/{lid}/editar", data={"name": "Novo nome"})
    with app.app_context():
        assert db.session.get(GameList, lid).name == "Novo nome"
    ctx.post(f"/listas/{lid}/apagar")
    assert ctx.get(f"/listas/{lid}").status_code == 404


def test_lis06_uma_vez_por_lista_varias_listas(app, ctx):
    slug = make_game(app)
    a, b = new_list(ctx, "A"), new_list(ctx, "B")
    add(ctx, slug, a)
    assert "já está na lista" in add(ctx, slug, a).get_data(as_text=True)
    add(ctx, slug, b)
    with app.app_context():
        assert ListItem.query.count() == 2


def test_lis07_reordenar_persiste(app, ctx):
    s = [make_game(app, n) for n in ("Um", "Dois", "Tres")]
    lid = new_list(ctx)
    for x in s:
        add(ctx, x, lid)
    with app.app_context():
        gid = Game.query.filter_by(slug=s[2]).one().id
    ctx.post(f"/listas/{lid}/jogos/{gid}/mover", data={"dir": "up"})
    ctx.post(f"/listas/{lid}/jogos/{gid}/mover", data={"dir": "up"})
    with app.app_context():
        order = [i.game.slug for i in db.session.get(GameList, lid).items]
    assert order == [s[2], s[0], s[1]]


def test_lis08_privada_404_para_outros_e_visitantes(app, ctx):
    lid = new_list(ctx, "Secreta", "privada")
    make_user(app, "bia")
    c2 = app.test_client()
    login(c2, "bia")
    assert c2.get(f"/listas/{lid}").status_code == 404
    assert app.test_client().get(f"/listas/{lid}").status_code == 404
    assert ctx.get(f"/listas/{lid}").status_code == 200
    assert "Secreta" not in c2.get("/u/ana").get_data(as_text=True)


def test_lis09_removido_some_da_publica_fica_para_o_dono(app, ctx):
    slug = make_game(app, "Sumido")
    lid = new_list(ctx)
    add(ctx, slug, lid)
    with app.app_context():
        Game.query.one().removed_at = now()
        db.session.commit()
    assert "Sumido" not in app.test_client().get(f"/listas/{lid}").get_data(as_text=True)
    h = ctx.get(f"/listas/{lid}").get_data(as_text=True)
    assert "Sumido" in h and "removido do catálogo" in h


def test_lis10_limites(app, ctx, monkeypatch):
    from app import listas

    monkeypatch.setattr(listas, "MAX_LISTS", 2)
    monkeypatch.setattr(listas, "MAX_ITEMS", 1)
    a = new_list(ctx, "A")
    new_list(ctx, "B")
    r = ctx.post("/listas", data={"name": "C"})
    assert r.status_code == 400 and "Limite de 2 listas" in r.get_data(as_text=True)
    add(ctx, make_game(app, "G1"), a)
    assert "Limite de 1 jogos" in add(ctx, make_game(app, "G2"), a).get_data(as_text=True)


def test_lis11_apagar_lista_nao_afeta_status_nem_avaliacoes(app, ctx):
    slug = make_game(app)
    ctx.post(f"/jogos/{slug}/avaliar", data={"score": 8})
    lid = new_list(ctx)
    add(ctx, slug, lid)
    ctx.post(f"/listas/{lid}/apagar")
    with app.app_context():
        assert Status.query.count() == 1 and Review.query.count() == 1 and GameList.query.count() == 0
