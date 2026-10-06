import time

import pytest
from sqlalchemy import event

from app.models import Dismissed, Game, Review, User, db, now
from app.recomendacoes import recommend, vizinhos
from app.seed import run
from conftest import login, make_user
from test_perfil import avalia, jogo, status


@pytest.fixture
def mundo(app, client):
    """ana avaliou C0..C2 com 8; bia (afim) e caio (oposto) avaliaram os mesmos."""
    for n in ("ana", "bia", "caio"):
        make_user(app, n)
    comuns = [jogo(app, f"C{i}", "Ação") for i in range(3)]
    for g in comuns:
        avalia(app, "ana", g, 8)
        avalia(app, "bia", g, 8)
        avalia(app, "caio", g, 0)
    login(client, "ana")
    return client


def recs(app, nome="ana"):
    with app.app_context():
        uid = User.query.filter_by(username=nome).one().id
        return [(g.title, why) for g, _, why in recommend(uid)[0]]


def test_col01_so_viram_vizinhos_afins_com_3_comuns(app, mundo):
    with app.app_context():
        uid = User.query.filter_by(username="ana").one().id
        assert [(round(p, 2), n) for p, n, _ in vizinhos(uid)] == [(1.0, "bia")]  # caio: 20%; abaixo do mínimo
    make_user(app, "dani")
    with app.app_context():
        comuns = [r.game_id for r in Review.query.filter_by(user_id=User.query.filter_by(username="ana").one().id)][:2]
    for g in comuns:  # só 2 em comum com ana: sem percentual, não é vizinha
        avalia(app, "dani", g, 8)
    with app.app_context():
        ana = User.query.filter_by(username="ana").one().id
        assert "dani" not in [n for _, n, _ in vizinhos(ana)]


def test_col02_vizinho_empurra_jogo_para_cima(app, mundo):
    mau = jogo(app, "Amau", "Ação")  # "A" vem antes no desempate por título
    bom = jogo(app, "Zbom", "Ação")
    avalia(app, "bia", bom, 9)
    avalia(app, "bia", mau, 5)  # nota baixa do vizinho não conta
    titulos = [t for t, _ in recs(app)]
    assert titulos.index("Zbom") < titulos.index("Amau")


def test_col02_peso_proporcional_a_afinidade_e_divide_por_vizinhos(app, mundo):
    from app.recomendacoes import colaborativo
    viz = [(1.0, "bia", {1: 9}), (0.8, "dani", {1: 8, 2: 10})]
    c = colaborativo(viz)
    assert c[1][0] == pytest.approx(0.9) and c[1][2] == "bia" and c[2][0] == pytest.approx(0.4)


def test_col03_excluidos_continuam_fora(app, mundo):
    a, b, c, d = (jogo(app, t, "Ação") for t in ("Vista", "Marcada", "Dispensada", "Removida"))
    for g in (a, b, c, d):
        avalia(app, "bia", g, 10)
    avalia(app, "ana", a, 6)
    status(app, "ana", b, "planejado")
    with app.app_context():
        uid = User.query.filter_by(username="ana").one().id
        db.session.add(Dismissed(user_id=uid, game_id=c))
        db.session.get(Game, d).removed_at = now()
        db.session.commit()
    titulos = [t for t, _ in recs(app)]
    assert not {"Vista", "Marcada", "Dispensada", "Removida"} & set(titulos)


def test_col03_avaliacao_oculta_do_vizinho_nao_conta(app, mundo):
    g = jogo(app, "Oculto", "Ação")
    avalia(app, "bia", g, 10, hidden=True)
    assert all("@bia" not in why for _, why in recs(app))


def test_col04_motivo_cita_o_vizinho_mais_afim(app, mundo):
    g = jogo(app, "Alvo", "Ação")
    avalia(app, "bia", g, 9)
    motivo = dict(recs(app))["Alvo"]
    assert motivo == "@bia, com 100% de afinidade com você, deu nota 9"
    # sem vizinho que recomende, volta o motivo de gênero
    outro = jogo(app, "Sem vizinho", "Ação")
    assert dict(recs(app))["Sem vizinho"].startswith("porque você gostou de")
    assert outro


def test_col04_desempate_por_afinidade_e_nome(app, mundo):
    make_user(app, "ale")  # mesma afinidade que bia
    with app.app_context():
        for r in list(Review.query.filter_by(user_id=User.query.filter_by(username="bia").one().id)):
            db.session.add(Review(user_id=User.query.filter_by(username="ale").one().id, game_id=r.game_id, score=8))
        db.session.commit()
    g = jogo(app, "Alvo", "Ação")
    avalia(app, "bia", g, 9)
    avalia(app, "ale", g, 10)
    assert dict(recs(app))["Alvo"].startswith("@ale,")  # empate de afinidade: nome em ordem alfabética


def test_col05_sem_vizinhos_nada_muda(app, client):
    for n in ("ana", "bia"):
        make_user(app, n)
    g = [jogo(app, f"G{i}", "Ação") for i in range(3)]
    avalia(app, "ana", g[0], 8)
    avalia(app, "bia", jogo(app, "Fora", "Ação"), 10)  # bia sem jogos em comum
    with app.app_context():
        uid = User.query.filter_by(username="ana").one().id
        assert vizinhos(uid) == []
    assert all(not why.startswith("@") for _, why in recs(app))


def test_col06_sem_avaliacoes_so_mais_bem_avaliados(app, client, monkeypatch):
    make_user(app, "ana")
    make_user(app, "bia")
    avalia(app, "bia", jogo(app, "Top", "Ação"), 10)
    import app.recomendacoes as m
    monkeypatch.setattr(m, "vizinhos", lambda *_: pytest.fail("não deve consultar vizinhos"))
    with app.app_context():
        recs_, aviso = m.recommend(User.query.filter_by(username="ana").one().id)
    assert aviso and recs_[0][2] == "bem avaliado pela comunidade"


def test_col07_deterministico(app, mundo):
    for t in "XYZ":
        avalia(app, "bia", jogo(app, t, "Ação"), 9)
    assert recs(app) == recs(app)


def test_col08_desempenho_e_consultas(app, client):
    with app.app_context():
        run(42, real=True)
    c = app.test_client()
    c.post("/entrar", data={"email": "jogador03@example.com", "password": "senha1234"})
    qs = []

    def conta(*a, _l=qs):
        _l.append(1)
    with app.app_context():
        event.listen(db.engine, "before_cursor_execute", conta)
        t0 = time.perf_counter()
        r = c.get("/recomendacoes")
        dt = time.perf_counter() - t0
        event.remove(db.engine, "before_cursor_execute", conta)
    assert r.status_code == 200 and dt < 0.8 and len(qs) <= 14
    assert b"de afinidade com voc" in r.data  # há vizinhos no seed real


def test_motivo_preserva_maiusculas_do_titulo(app, mundo):
    html = mundo.get("/recomendacoes").get_data(as_text=True)
    assert "Sem recomendações" in html or "porque você gostou de C" not in html  # título não vai para minúsculas
    jogo(app, "Outro", "Ação")
    assert "Porque você gostou de C" in mundo.get("/recomendacoes").get_data(as_text=True)
