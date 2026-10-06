import json

import pytest
from sqlalchemy import event

from app.models import Game, GameList, Like, Review, User, db, now
from conftest import login, make_user
from test_perfil import avalia, jogo, status


@pytest.fixture
def mundo(app, client):
    make_user(app, "ana")
    make_user(app, "bia")
    ids = {t: jogo(app, t, g) for t, g in (("Alfa", "Ação"), ("Beta", "RPG"), ("Gama", "Ação"))}
    avalia(app, "ana", ids["Alfa"], 9, "ótimo")
    avalia(app, "bia", ids["Alfa"], 7)
    return client, ids


def get(c, url):
    r = c.get(url)
    return r, json.loads(r.get_data(as_text=True))


def test_api01_indice_json_e_cors(client):
    r, d = get(client, "/api")
    assert r.status_code == 200 and d["versao"] == "1" and "/api/jogos" in d["endpoints"]
    assert r.headers["Content-Type"] == "application/json; charset=utf-8"
    assert r.headers["Access-Control-Allow-Origin"] == "*"
    assert client.get("/api/").status_code == 200


def test_api02_lista_com_paginacao_e_filtros(mundo):
    c, _ = mundo
    _, d = get(c, "/api/jogos")
    assert d["total"] == 3 and d["page"] == 1 and d["pages"] == 1 and len(d["items"]) == 3
    assert [j["slug"] for j in get(c, "/api/jogos?genero=rpg")[1]["items"]] == ["beta"]
    assert [j["slug"] for j in get(c, "/api/jogos?q=gam")[1]["items"]] == ["gama"]
    assert get(c, "/api/jogos?ordem=titulo")[1]["items"][0]["slug"] == "alfa"
    assert get(c, "/api/jogos?ano_de=abc&nota_min=x")[0].status_code == 200  # inválido é ignorado
    _, p = get(c, "/api/jogos?per_page=2&page=99")
    assert p["page"] == 2 and p["pages"] == 2 and len(p["items"]) == 1  # fora do intervalo cai na última


def test_api03_per_page(mundo):
    c, _ = mundo
    assert get(c, "/api/jogos")[1]["per_page"] == 20
    assert get(c, "/api/jogos?per_page=1")[1]["per_page"] == 1
    for ruim in ("0", "-3", "abc", "51", "1000"):
        assert get(c, f"/api/jogos?per_page={ruim}")[1]["per_page"] == 20, ruim
    assert get(c, "/api/jogos?per_page=50")[1]["per_page"] == 50


def test_api04_campos_do_item(mundo):
    c, _ = mundo
    alfa = next(j for j in get(c, "/api/jogos")[1]["items"] if j["slug"] == "alfa")
    assert set(alfa) == {"slug", "titulo", "lancamento", "desenvolvedora", "generos", "plataformas", "capa",
                         "nota_media", "avaliacoes", "url"}
    assert alfa["nota_media"] == 8.0 and alfa["avaliacoes"] == 2 and alfa["generos"] == ["Ação"]
    assert alfa["lancamento"] == "2020-05-01" and alfa["url"].endswith("/jogos/alfa")
    assert alfa["capa"].startswith("http") and alfa["capa"].endswith("/capa/alfa.svg")
    beta = next(j for j in get(c, "/api/jogos")[1]["items"] if j["slug"] == "beta")
    assert beta["nota_media"] is None and beta["avaliacoes"] == 0


def test_api05_detalhe_e_404(app, mundo):
    c, ids = mundo
    r, d = get(c, "/api/jogos/alfa")
    assert d["sinopse"] == "Sinopse." and d["histograma"]["9"] == 1 and d["histograma"]["7"] == 1
    assert list(d["histograma"]) == [str(i) for i in range(11)]
    r, d = get(c, "/api/jogos/nao-existe")
    assert r.status_code == 404 and d == {"erro": "Jogo não encontrado"}
    with app.app_context():
        db.session.get(Game, ids["Beta"]).removed_at = now()
        db.session.commit()
    assert get(c, "/api/jogos/beta")[0].status_code == 404
    assert "beta" not in [j["slug"] for j in get(c, "/api/jogos")[1]["items"]]


def test_api06_avaliacoes_visiveis_paginadas(app, mundo):
    c, ids = mundo
    with app.app_context():
        rid = Review.query.filter_by(user_id=User.query.filter_by(username="ana").one().id).one().id
        db.session.add(Like(user_id=User.query.filter_by(username="bia").one().id, review_id=rid))
        db.session.commit()
    _, d = get(c, "/api/jogos/alfa/avaliacoes")
    assert d["total"] == 2 and {a["usuario"] for a in d["items"]} == {"ana", "bia"}
    ana = next(a for a in d["items"] if a["usuario"] == "ana")
    assert ana == {"usuario": "ana", "nota": 9, "texto": "ótimo", "spoiler": False, "editada": False,
                   "data": ana["data"], "curtidas": 1}
    with app.app_context():
        Review.query.filter_by(user_id=User.query.filter_by(username="bia").one().id).one().hidden = True
        db.session.commit()
    assert [a["usuario"] for a in get(c, "/api/jogos/alfa/avaliacoes")[1]["items"]] == ["ana"]
    _, p = get(c, "/api/jogos/alfa/avaliacoes?per_page=1&page=5")
    assert p["page"] == 1 and p["pages"] == 1
    assert get(c, "/api/jogos/nada/avaliacoes")[0].status_code == 404


def test_api06_ordem_mais_recente_primeiro(app, mundo):
    from datetime import timedelta
    c, ids = mundo
    with app.app_context():
        ana = User.query.filter_by(username="ana").one().id
        for r in Review.query.filter_by(game_id=ids["Alfa"]):
            r.created_at = now() - timedelta(days=5 if r.user_id == ana else 1)
        db.session.commit()
    assert [a["usuario"] for a in get(c, "/api/jogos/alfa/avaliacoes")[1]["items"]] == ["bia", "ana"]


def test_api07_sem_dados_de_conta(app, mundo):
    c, ids = mundo
    with app.app_context():
        ana = User.query.filter_by(username="ana").one().id
        db.session.add(GameList(user_id=ana, name="SegredoPrivado", public=False))
        db.session.commit()
    status(app, "ana", ids["Gama"], "jogando")
    corpo = "".join(c.get(u).get_data(as_text=True) for u in
                    ("/api", "/api/jogos", "/api/jogos/alfa", "/api/jogos/alfa/avaliacoes"))
    for proibido in ("@ex.com", "password", "hash", "email", "SegredoPrivado", "jogando", "session"):
        assert proibido not in corpo.lower(), proibido


def test_api08_metodos_e_rotas_desconhecidas_em_json(mundo):
    c, _ = mundo
    for metodo in (c.post, c.put, c.delete, c.patch):
        r = metodo("/api/jogos")
        assert r.status_code == 405 and r.is_json and json.loads(r.get_data(as_text=True))["erro"]
        assert r.headers["Content-Type"] == "application/json; charset=utf-8"
    r = c.get("/api/nada")
    assert r.status_code == 404 and json.loads(r.get_data(as_text=True)) == {"erro": "Página não encontrada"}
    assert c.head("/api/jogos").status_code == 200
    assert "<html" in c.get("/nada").get_data(as_text=True)  # fora de /api continua HTML


def test_api09_cache_so_em_leituras_ok(mundo):
    c, _ = mundo
    assert c.get("/api/jogos").headers["Cache-Control"] == "public, max-age=60"
    assert "Cache-Control" not in c.get("/api/nada").headers
    assert "Cache-Control" not in c.post("/api/jogos").headers
    assert "max-age=60" not in c.get("/").headers.get("Cache-Control", "")  # só /api tem esse cache


def test_api10_consultas_nao_crescem_com_a_pagina(app, client):
    make_user(app, "ana")
    ids = [jogo(app, f"G{i:02d}", f"Gen{i % 4}") for i in range(30)]
    for g in ids:
        avalia(app, "ana", g, 8)
    contagens = []
    for n in (2, 30):
        qs = []

        def conta(*a, _l=qs):
            _l.append(1)
        with app.app_context():
            event.listen(db.engine, "before_cursor_execute", conta)
            assert client.get(f"/api/jogos?per_page={n}").status_code == 200
            event.remove(db.engine, "before_cursor_execute", conta)
        contagens.append(len(qs))
    assert contagens[1] <= 6 and contagens[1] <= contagens[0] + 1
