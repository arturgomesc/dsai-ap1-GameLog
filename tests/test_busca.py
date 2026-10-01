import re
import time

import pytest

from app.models import Developer, Game, db, now
from app.seed import run


@pytest.fixture
def seeded(app):
    with app.app_context():
        run(42)
    return app


def slugs(html):
    return re.findall(r'href="/jogos/([^"]+)"', html)


def test_bus01_texto_sem_caixa_nem_acento(client, seeded):
    with seeded.app_context():
        g = Game.query.filter(Game.title.like("%Sombrio%")).first()
        dev, genre = g.developer.name, g.genres[0].name
        slug = g.slug
    # acento: "Ação" encontrado por "acao"
    assert client.get("/buscar?q=acao").get_data(as_text=True).count('class="card"') > 0
    assert client.get("/buscar?q=" + dev.upper()).get_data(as_text=True).count('class="card"') > 0
    r = client.get("/buscar?q=" + genre.lower()).get_data(as_text=True)
    assert r.count('class="card"') > 0
    html = client.get(f"/buscar?q={g.title.upper()}").get_data(as_text=True)
    assert slug in slugs(html)  # título exato aparece (relevância o põe primeiro)
    assert slugs(html)[0] == slug


def test_bus02_filtros_combinados(client, seeded):
    with seeded.app_context():
        g = Game.query.first()
        gen, plat, year = g.genres[0].slug, g.platforms[0].slug, g.release_date.year
        slug = g.slug
    html = client.get(f"/buscar?genero={gen}&plataforma={plat}&ano_de={year}&ano_ate={year}").get_data(as_text=True)
    assert slug in slugs(html)
    assert slug not in slugs(client.get(f"/buscar?ano_de={year + 1}&ano_ate={year + 1}").get_data(as_text=True))
    assert client.get("/buscar?genero=a&genero=b").status_code == 200  # múltiplos
    todos = client.get("/buscar").get_data(as_text=True)
    exigente = client.get("/buscar?nota_min=9.9").get_data(as_text=True)
    assert "resultado(s)" in exigente and len(slugs(exigente)) < len(slugs(todos))


def test_bus03_ordenacao(client, seeded):
    t = slugs(client.get("/buscar?ordem=titulo").get_data(as_text=True))
    with seeded.app_context():
        titles = [Game.query.filter_by(slug=s).one().title for s in t]
    from app.util import fold

    assert [fold(x) for x in titles] == sorted(fold(x) for x in titles)
    d = slugs(client.get("/buscar?ordem=data").get_data(as_text=True))
    with seeded.app_context():
        dates = [Game.query.filter_by(slug=s).one().release_date for s in d]
    assert dates == sorted(dates, reverse=True)
    assert client.get("/buscar?ordem=nota").status_code == 200


def test_bus04_paginacao_20_e_fora_do_intervalo(client, seeded):
    assert len(slugs(client.get("/buscar").get_data(as_text=True))) == 20
    assert client.get("/buscar?page=9999").status_code == 200
    r = client.get("/buscar?page=9999").get_data(as_text=True)
    assert "Página 15 de 15" in r
    assert client.get("/buscar?page=-3").status_code == 200


def test_bus05_estado_na_url_e_paginacao_preserva_filtros(client, seeded):
    html = client.get("/buscar?genero=acao&genero=rpg&ordem=titulo").get_data(as_text=True)
    assert 'value="acao" checked' in html and 'value="rpg" checked' in html
    assert "genero=acao" in html and "genero=rpg" in html and "ordem=titulo" in html and "page=2" in html


def test_bus06_sem_resultados(client, seeded):
    html = client.get("/buscar?q=zzzzzzzz").get_data(as_text=True)
    assert "Nenhum jogo encontrado" in html and "Limpar filtros" in html


def test_bus07_removidos_nunca_aparecem(client, seeded):
    with seeded.app_context():
        g = Game.query.first()
        g.removed_at = now()
        db.session.commit()
        title, slug = g.title, g.slug
    assert slug not in slugs(client.get("/buscar?q=" + title).get_data(as_text=True))


def test_bus08_parametros_invalidos(client, seeded):
    for qs in ("ordem=xyz", "ano_de=abc", "ano_ate=99999999999", "nota_min=zz", "page=abc", "genero=", "ano_de=0"):
        assert client.get("/buscar?" + qs).status_code == 200, qs


def test_bus09_responde_em_500ms(client, seeded):
    client.get("/buscar?q=a")
    t = time.perf_counter()
    client.get("/buscar?q=acao&ordem=nota")
    assert time.perf_counter() - t < 0.5
