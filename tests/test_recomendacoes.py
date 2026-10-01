import time

import pytest

from app.models import Game, Genre, Review, Status, db, now
from app.recomendacoes import recommend
from app.seed import run
from conftest import login, make_game, make_user


def names(app, uid):
    with app.app_context():
        return [g.title for g, _, _ in recommend(uid)[0]]


@pytest.fixture
def world(app, client):
    uid = make_user(app, "ana")
    login(client, "ana")
    for t, gen in (("Acao1", "Ação"), ("Acao2", "Ação"), ("Acao3", "Ação"), ("Corrida1", "Corrida"), ("Puzzle1", "Puzzle")):
        make_game(app, t, genre=gen)
    return client, uid


def rate(client, title, score):
    client.post(f"/jogos/{title.lower()}/avaliar", data={"score": score})


def test_rec01_exclui_avaliados_e_com_status(app, world):
    client, uid = world
    rate(client, "Acao1", 9)
    client.post("/jogos/acao2/status", data={"status": "planejado"})
    n = names(app, uid)
    assert "Acao1" not in n and "Acao2" not in n and "Acao3" in n


def test_rec02_rec03_afinidade_e_motivo(app, world):
    client, uid = world
    rate(client, "Acao1", 10)
    rate(client, "Corrida1", 2)
    with app.app_context():
        recs, notice = recommend(uid)
    assert notice is None and recs[0][0].title == "Acao2"  # gênero preferido primeiro
    assert recs[0][2] == "porque você gostou de Acao1"
    assert len(recs) <= 20


def test_rec03_limite_de_20(app, client):
    uid = make_user(app, "ana")
    login(client, "ana")
    for i in range(30):
        make_game(app, f"J{i:02d}")
    client.post("/jogos/j00/avaliar", data={"score": 9})
    assert len(names(app, uid)) == 20


def test_rec04_sem_avaliacoes_mostra_mais_bem_avaliados_com_aviso(app, world):
    client, uid = world
    make_user(app, "bia")
    cb = app.test_client()
    login(cb, "bia")
    cb.post("/jogos/puzzle1/avaliar", data={"score": 10})
    cb.post("/jogos/acao1/avaliar", data={"score": 4})
    with app.app_context():
        recs, notice = recommend(uid)
    assert recs[0][0].title == "Puzzle1" and "ainda não avaliou" in notice
    assert "ainda não avaliou" in client.get("/recomendacoes").get_data(as_text=True)


def test_rec05_deterministico_desempate_por_titulo(app, world):
    client, uid = world
    rate(client, "Acao1", 8)
    a = names(app, uid)
    assert a == names(app, uid)
    assert a.index("Acao2") < a.index("Acao3")  # empate → título


def test_rec06_removidos_e_ocultos_nunca(app, world):
    client, uid = world
    make_user(app, "bia")
    cb = app.test_client()
    login(cb, "bia")
    cb.post("/jogos/acao2/avaliar", data={"score": 10})
    cb.post("/jogos/acao3/avaliar", data={"score": 10})
    rate(client, "Corrida1", 9)
    with app.app_context():
        Game.query.filter_by(slug="acao2").one().removed_at = now()
        db.session.commit()
    n = names(app, uid)
    assert "Acao2" not in n
    with app.app_context():  # review oculta do usuário não conta como gosto
        Review.query.filter_by(user_id=uid).one().hidden = True
        db.session.commit()
        assert "ainda não avaliou" in recommend(uid)[1]


def test_rec07_dispensar(app, world):
    client, uid = world
    rate(client, "Acao1", 9)
    with app.app_context():
        gid = Game.query.filter_by(slug="acao2").one().id
    client.post(f"/recomendacoes/{gid}/dispensar")
    assert "Acao2" not in names(app, uid)


def test_rec08_recalcula_ao_avaliar(app, world):
    client, uid = world
    rate(client, "Acao1", 9)
    assert "Acao3" in names(app, uid)
    rate(client, "Acao3", 5)
    assert "Acao3" not in names(app, uid)


def test_rec09_desempenho_com_seed(app, client):
    with app.app_context():
        run(42)
    login(client, "jogador01", "senha1234")
    client.post("/entrar", data={"email": "jogador01@example.com", "password": "senha1234"})
    t = time.perf_counter()
    r = client.get("/recomendacoes")
    assert r.status_code == 200 and time.perf_counter() - t < 0.8
