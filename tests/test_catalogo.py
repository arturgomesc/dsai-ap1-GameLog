from datetime import date

from app.models import Developer, Game, Genre, Platform, Review, User, db, now
from app.seed import run
from conftest import make_user


def snapshot():
    return (
        sorted((g.slug, g.synopsis, str(g.release_date), g.developer.name, sorted(x.name for x in g.genres),
                sorted(x.name for x in g.platforms)) for g in Game.query),
        sorted((r.user_id, r.game_id, r.score, r.text) for r in Review.query),
    )


def test_cat03_cat05_volumes_do_seed(app):
    with app.app_context():
        run(42)
        assert Game.query.count() >= 300 and Genre.query.count() == 15
        assert Platform.query.count() == 10 and Developer.query.count() == 40
        assert User.query.count() >= 20 and Review.query.count() > 0
        from app.models import Follow, GameList
        assert Follow.query.count() > 0 and GameList.query.count() > 0


def test_cat04_seed_reproduzivel(tmp_path):
    from app import create_app

    snaps = []
    for i in (1, 2):
        a = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path}/s{i}.db"})
        with a.app_context():
            run(42)
            snaps.append(snapshot())
            db.session.remove(); db.engine.dispose()
    assert snaps[0] == snaps[1]


def test_cat01_cat02_modelo(app):
    with app.app_context():
        run(42)
        for g in Game.query:
            assert g.title and g.slug and g.synopsis and g.release_date and g.developer and g.platforms and g.genres
        assert any(len(g.genres) > 1 for g in Game.query)
        assert any(len(d.games) > 1 for d in Developer.query)


def test_cat06_capa_deterministica(client, app):
    with app.app_context():
        run(42)
        slug = Game.query.first().slug
    a, b = client.get(f"/capa/{slug}.svg"), client.get(f"/capa/{slug}.svg")
    assert a.mimetype == "image/svg+xml" and a.data == b.data
    assert client.get("/capa/outro-slug.svg").data != a.data


def test_global01_home_publica_com_destaques(client, app):
    with app.app_context():
        run(42)
    r = client.get("/")
    html = r.get_data(as_text=True)
    assert r.status_code == 200 and "Em destaque" in html and 'class="card"' in html


def test_cat07_jogo_removido_some_das_listagens(client, app):
    with app.app_context():
        run(42)
        g = Game.query.first()
        gen, slug = g.genres[0].slug, g.slug
        g.removed_at = now()
        db.session.commit()
    html = client.get(f"/generos/{gen}").get_data(as_text=True)
    assert f'href="/jogos/{slug}"' not in html


def test_cat08_remocao_preserva_historico(app):
    with app.app_context():
        run(42)
        r = Review.query.first()
        g = r.game
        g.removed_at = now()
        db.session.commit()
        assert Review.query.get(r.id) is not None and Review.query.get(r.id).game.title == g.title


def test_cat09_paginas_de_genero_plataforma_dev_paginadas(client, app):
    with app.app_context():
        run(42)
        gen, plat, dev = Genre.query.first().slug, Platform.query.first().slug, Developer.query.first().slug
    for url in (f"/generos/{gen}", f"/plataformas/{plat}", f"/desenvolvedoras/{dev}"):
        r = client.get(url)
        assert r.status_code == 200 and r.get_data(as_text=True).count('class="card"') <= 20
    assert client.get(f"/generos/{gen}").get_data(as_text=True).count('class="card"') == 20
    assert client.get(f"/generos/{gen}?page=999").status_code == 200
    assert client.get("/generos/inexistente").status_code == 404
