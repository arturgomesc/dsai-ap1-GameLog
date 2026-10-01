import pytest

from app.models import Activity, Follow, Game, GameList, Review, User, db, now
from conftest import login, make_game, make_user


@pytest.fixture
def duo(app):
    make_user(app, "ana")
    make_user(app, "bia")
    ca, cb = app.test_client(), app.test_client()
    login(ca, "ana")
    login(cb, "bia")
    return ca, cb


def feed(c, q=""):
    return c.get("/feed" + q).get_data(as_text=True)


def test_soc01_seguir_e_deixar_de_seguir_nao_a_si_mesmo(app, duo):
    ca, _ = duo
    ca.post("/u/ana/seguir")
    with app.app_context():
        assert Follow.query.count() == 0
    ca.post("/u/bia/seguir")
    with app.app_context():
        assert Follow.query.count() == 1
    ca.post("/u/bia/deixar-de-seguir")
    with app.app_context():
        assert Follow.query.count() == 0


def test_soc02_sem_duplicata(app, duo):
    ca, _ = duo
    ca.post("/u/bia/seguir")
    ca.post("/u/bia/seguir")
    with app.app_context():
        assert Follow.query.count() == 1


def test_soc03_contagens_e_listas_paginadas(app, duo):
    ca, cb = duo
    ca.post("/u/bia/seguir")
    h = app.test_client().get("/u/bia").get_data(as_text=True)
    assert "<strong>1</strong> seguidores" in h and "<strong>0</strong> seguindo" in h
    assert "@ana" in app.test_client().get("/u/bia/seguidores").get_data(as_text=True)
    assert "@bia" in app.test_client().get("/u/ana/seguindo").get_data(as_text=True)
    assert app.test_client().get("/u/bia/seguidores?page=99").status_code == 200


def test_soc04_feed_so_de_quem_sigo_do_mais_recente_e_paginado(app, duo):
    ca, cb = duo
    make_user(app, "caio")
    cc = app.test_client()
    login(cc, "caio")
    slugs = [make_game(app, f"G{i:02d}") for i in range(22)]
    for s in slugs:
        cb.post(f"/jogos/{s}/avaliar", data={"score": 5})
    cc.post(f"/jogos/{slugs[0]}/avaliar", data={"score": 1})  # caio: não seguido
    ca.post("/u/bia/seguir")
    h = feed(ca)
    assert h.count('class="panel"') == 20 and "caio" not in h
    assert h.index("G21") < h.index("G20")  # mais recente primeiro
    assert "Página 1 de 2" in h and feed(ca, "?page=2").count('class="panel"') == 2


def test_soc05_atividades_geradoras(app, duo):
    ca, cb = duo
    s = make_game(app)
    cb.post(f"/jogos/{s}/avaliar", data={"score": 7})  # avaliar
    cb.post("/jogos/" + s + "/status", data={"status": "jogando"})
    cb.post("/jogos/" + s + "/status", data={"status": "jogado"})  # mudar para jogado
    r = cb.post("/listas", data={"name": "Pública", "visibility": "publica"})  # criar lista pública
    lid = r.headers["Location"].rsplit("/", 1)[1]
    cb.post(f"/jogos/{s}/adicionar-a-lista", data={"list_id": lid})  # adicionar a lista pública
    with app.app_context():
        assert sorted(a.kind for a in Activity.query) == ["avaliou", "jogado", "lista", "lista_jogo"]
    ca.post("/u/bia/seguir")
    h = feed(ca)
    for t in ("avaliou", "como jogado", "criou a lista", "à lista"):
        assert t in h


def test_soc06_lista_privada_nunca_no_feed(app, duo):
    ca, cb = duo
    s = make_game(app)
    ca.post("/u/bia/seguir")
    r = cb.post("/listas", data={"name": "Segredinha", "visibility": "privada"})
    lid = r.headers["Location"].rsplit("/", 1)[1]
    cb.post(f"/jogos/{s}/adicionar-a-lista", data={"list_id": lid})
    assert "Segredinha" not in feed(ca)
    cb.post("/listas", data={"name": "Aberta", "visibility": "publica"})
    pub = cb.post("/listas", data={"name": "Aberta2", "visibility": "publica"}).headers["Location"].rsplit("/", 1)[1]
    cb.post(f"/listas/{pub}/editar", data={"name": "Aberta2", "visibility": "privada"})  # virou privada depois
    assert "Aberta2" not in feed(ca) and "Aberta" in feed(ca)


def test_soc07_oculta_ou_removido_fora_do_feed(app, duo):
    ca, cb = duo
    a, b = make_game(app, "Visivel"), make_game(app, "Escondido")
    c = make_game(app, "Removido")
    for s in (a, b, c):
        cb.post(f"/jogos/{s}/avaliar", data={"score": 5})
    ca.post("/u/bia/seguir")
    with app.app_context():
        Review.query.join(Game).filter(Game.slug == b).one().hidden = True
        Game.query.filter_by(slug=c).one().removed_at = now()
        db.session.commit()
    h = feed(ca)
    assert "Visivel" in h and "Escondido" not in h and "Removido" not in h


def test_soc08_deixar_de_seguir_remove_do_feed(app, duo):
    ca, cb = duo
    cb.post(f"/jogos/{make_game(app, 'Zed')}/avaliar", data={"score": 5})
    ca.post("/u/bia/seguir")
    assert "Zed" in feed(ca)
    ca.post("/u/bia/deixar-de-seguir")
    assert "Zed" not in feed(ca)


def test_soc09_feed_vazio_sugere_mais_ativos(app, duo):
    ca, cb = duo
    make_user(app, "caio")
    cb.post(f"/jogos/{make_game(app)}/avaliar", data={"score": 5})
    h = feed(ca)
    assert "Seu feed está vazio" in h
    assert h.index("@bia") < h.index("@caio") and "@ana" not in h.split("Sugestões")[1]
    ca.post("/u/bia/seguir")
    assert "Seu feed está vazio" not in feed(ca)


def test_soc10_visitante_nao_acessa_feed(client):
    r = client.get("/feed")
    assert r.status_code == 302 and "/entrar?next=/feed" in r.headers["Location"]
