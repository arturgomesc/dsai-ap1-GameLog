import re

from app.models import Game, Review, Status, db, now
from conftest import login, make_game, make_user


def add_review(app, user, slug, score, text="", hidden=False):
    with app.app_context():
        from app.models import User

        uid = User.query.filter_by(username=user).one().id
        g = Game.query.filter_by(slug=slug).one()
        db.session.add(Review(user_id=uid, game_id=g.id, score=score, text=text, hidden=hidden))
        db.session.commit()


def test_pag01_conteudo_basico(app, client):
    slug = make_game(app, "Alfa", genre="RPG", platform="Switch", dev="Estúdio X")
    html = client.get(f"/jogos/{slug}").get_data(as_text=True)
    for s in ("Alfa", "Sinopse.", "01/05/2020", "Estúdio X", "RPG", "Switch", f"/capa/{slug}.svg"):
        assert s in html


def test_pag02_pag03_pag04_media_histograma_ignora_ocultas(app, client):
    slug = make_game(app)
    assert "sem avaliações" in client.get(f"/jogos/{slug}").get_data(as_text=True)
    for n, sc, h in (("a", 8, False), ("b", 7, False), ("c", 0, True)):
        make_user(app, n)
        add_review(app, n, slug, sc, hidden=h)
    html = client.get(f"/jogos/{slug}").get_data(as_text=True)
    assert "★ 7.5" in html and "(2 avaliações)" in html  # oculta ignorada
    assert len(re.findall(r'title="Nota \d+: \d+"', html)) == 11  # histograma 0..10
    assert 'title="Nota 0: 0"' in html


def test_pag05_ordem_curtidas_ou_recentes(app, client):
    slug = make_game(app)
    for n in "ab":
        make_user(app, n)
    add_review(app, "a", slug, 5, "primeira")
    add_review(app, "b", slug, 5, "segunda")
    with app.app_context():
        from app.models import Like, User

        rid = Review.query.filter_by(text="primeira").one().id
        db.session.add(Like(user_id=User.query.filter_by(username="b").one().id, review_id=rid))
        db.session.commit()
    h = client.get(f"/jogos/{slug}").get_data(as_text=True)
    assert h.index("primeira") < h.index("segunda")
    h = client.get(f"/jogos/{slug}?ordem=recentes").get_data(as_text=True)
    assert h.index("segunda") < h.index("primeira")


def test_pag06_visitante_ve_tudo_e_acoes_levam_ao_login(app, client):
    slug = make_game(app)
    r = client.get(f"/jogos/{slug}")
    assert r.status_code == 200 and f"/entrar?next=/jogos/{slug}" in r.get_data(as_text=True)
    assert client.post(f"/jogos/{slug}/status", data={"status": "jogado"}).status_code == 302


def test_pag07_logado_ve_status_e_avaliacao(app, client):
    slug = make_game(app)
    make_user(app, "ana")
    login(client, "ana")
    client.post(f"/jogos/{slug}/status", data={"status": "jogando"})
    client.post(f"/jogos/{slug}/avaliar", data={"score": 9, "text": "ótimo"})
    html = client.get(f"/jogos/{slug}").get_data(as_text=True)
    assert 'value="jogando" selected' in html and 'value="9"' in html and "Editar minha avaliação" in html


def test_pag08_relacionados_por_generos_em_comum_e_nota(app, client):
    a = make_game(app, "Base", genre="Ação")
    with app.app_context():
        from app.models import Genre

        rpg = Genre(name="RPG", slug="rpg")
        db.session.add(rpg)
        db.session.commit()
        base = Game.query.filter_by(slug=a).one()
        base.genres.append(rpg)
        db.session.commit()
    um = make_game(app, "UmGenero", genre="Ação")
    dois = make_game(app, "DoisGeneros", genre="Ação")
    outro = make_game(app, "Outro", genre="Corrida")
    with app.app_context():
        from app.models import Genre

        g2 = Game.query.filter_by(slug=dois).one()
        g2.genres.append(Genre.query.filter_by(slug="rpg").one())
        db.session.commit()
    slugs = re.findall(r'<a class="card" href="/jogos/([^"]+)"', client.get(f"/jogos/{a}").get_data(as_text=True))
    assert slugs == [dois, um] and outro not in slugs
    for i in range(8):
        make_game(app, f"Extra{i}", genre="Ação")
    assert len(re.findall(r'<a class="card"', client.get(f"/jogos/{a}").get_data(as_text=True))) == 6  # máximo 6


def test_pag09_404_para_inexistente_ou_removido(app, client):
    slug = make_game(app)
    assert client.get("/jogos/nao-existe").status_code == 404
    with app.app_context():
        Game.query.one().removed_at = now()
        db.session.commit()
    r = client.get(f"/jogos/{slug}")
    assert r.status_code == 404 and "Página não encontrada" in r.get_data(as_text=True)


def test_pag10_metadados(app, client):
    slug = make_game(app, "Meu Jogo")
    html = client.get(f"/jogos/{slug}").get_data(as_text=True)
    assert "<title>Meu Jogo — GameLog</title>" in html and 'property="og:title" content="Meu Jogo — GameLog"' in html
    assert 'name="description" content="Sinopse."' in html
