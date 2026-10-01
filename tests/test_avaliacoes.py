import pytest

from app.models import Activity, Like, Report, Review, Status, db, game_stats
from conftest import login, make_game, make_user


@pytest.fixture
def ctx(app, client):
    make_user(app, "ana")
    slug = make_game(app)
    login(client, "ana")
    return client, slug


def rate(client, slug, **data):
    return client.post(f"/jogos/{slug}/avaliar", data=data, follow_redirects=True)


def test_ava01_exige_login_e_nota(app, client):
    slug = make_game(app)
    r = client.post(f"/jogos/{slug}/avaliar", data={"score": 5})
    assert r.status_code == 302 and "/entrar" in r.headers["Location"]
    make_user(app, "ana")
    login(client, "ana")
    for bad in ("", "11", "-1", "abc", "5.5"):
        assert "nota é obrigatória" in rate(client, slug, score=bad).get_data(as_text=True)
    with app.app_context():
        assert Review.query.count() == 0
    for ok in (0, 10):
        client.post(f"/jogos/{slug}/avaliar", data={"score": ok})
    with app.app_context():
        assert Review.query.one().score == 10


def test_ava02_uma_por_jogo_edita_existente(app, ctx):
    client, slug = ctx
    rate(client, slug, score=3)
    rate(client, slug, score=8, text="mudei")
    with app.app_context():
        r = Review.query.one()
        assert (r.score, r.text) == (8, "mudei")
        db.session.add(Review(user_id=r.user_id, game_id=r.game_id, score=1))
        with pytest.raises(Exception):
            db.session.commit()


def test_ava03_resenha_opcional_ate_5000(app, ctx):
    client, slug = ctx
    rate(client, slug, score=5)  # sem texto
    assert "até 5000" in rate(client, slug, score=5, text="x" * 5001).get_data(as_text=True)
    rate(client, slug, score=5, text="x" * 5000)
    with app.app_context():
        assert len(Review.query.one().text) == 5000


def test_ava04_apagar_recalcula_media_e_so_o_autor(app, ctx):
    client, slug = ctx
    make_user(app, "bia")
    rate(client, slug, score=10)
    with app.app_context():
        rid = Review.query.one().id
        gid = Review.query.one().game_id
    c2 = app.test_client()
    login(c2, "bia")
    assert c2.post(f"/avaliacoes/{rid}/apagar").status_code == 403
    c2.post(f"/jogos/{slug}/avaliar", data={"score": 4})
    with app.app_context():
        assert game_stats(gid)["avg"] == 7.0
    client.post(f"/avaliacoes/{rid}/apagar")
    with app.app_context():
        assert game_stats(gid)["avg"] == 4.0 and Review.query.count() == 1


def test_ava05_indicador_editada(app, ctx):
    client, slug = ctx
    rate(client, slug, score=5)
    with app.app_context():
        assert Review.query.one().edited is False
    rate(client, slug, score=6)
    with app.app_context():
        assert Review.query.one().edited is True
    assert "editada" in client.get(f"/jogos/{slug}").get_data(as_text=True)


def test_ava06_ava07_curtidas(app, ctx):
    client, slug = ctx
    make_user(app, "bia")
    rate(client, slug, score=7, text="boa")
    with app.app_context():
        rid = Review.query.one().id
    client.post(f"/avaliacoes/{rid}/curtir")  # própria
    with app.app_context():
        assert Like.query.count() == 0
    c2 = app.test_client()
    login(c2, "bia")
    c2.post(f"/avaliacoes/{rid}/curtir")
    c2.post(f"/avaliacoes/{rid}/curtir")  # duplicada
    with app.app_context():
        assert Like.query.count() == 1
    assert "1 curtida" in c2.get(f"/jogos/{slug}").get_data(as_text=True)
    c2.post(f"/avaliacoes/{rid}/descurtir")
    with app.app_context():
        assert Like.query.count() == 0


def test_ava08_denuncia(app, ctx):
    client, slug = ctx
    make_user(app, "bia")
    rate(client, slug, score=7)
    with app.app_context():
        rid = Review.query.one().id
    c2 = app.test_client()
    login(c2, "bia")
    c2.post(f"/avaliacoes/{rid}/denunciar", data={"reason": "xyz"})
    with app.app_context():
        assert Report.query.count() == 0
    c2.post(f"/avaliacoes/{rid}/denunciar", data={"reason": "spam", "comment": "ads"})
    r = c2.post(f"/avaliacoes/{rid}/denunciar", data={"reason": "spam"}, follow_redirects=True)
    assert "já denunciou" in r.get_data(as_text=True)
    with app.app_context():
        assert Report.query.count() == 1 and Report.query.one().status == "pendente"


def test_ava09_oculta_some_para_todos_menos_autor(app, ctx):
    client, slug = ctx
    make_user(app, "bia")
    rate(client, slug, score=7, text="texto-secreto")
    with app.app_context():
        r = Review.query.one()
        r.hidden = True
        db.session.commit()
    assert "texto-secreto" not in app.test_client().get(f"/jogos/{slug}").get_data(as_text=True)
    c2 = app.test_client()
    login(c2, "bia")
    assert "texto-secreto" not in c2.get(f"/jogos/{slug}").get_data(as_text=True)
    own = client.get(f"/jogos/{slug}").get_data(as_text=True)
    assert "texto-secreto" in own and "ocultada" in own


def test_ava10_spoiler_atras_de_clique(app, ctx):
    client, slug = ctx
    rate(client, slug, score=7, text="o vilão morre", spoiler="on")
    html = app.test_client().get(f"/jogos/{slug}").get_data(as_text=True)
    assert '<details class="spoiler">' in html


def test_ava11_avaliar_marca_jogado_se_sem_status(app, ctx):
    client, slug = ctx
    rate(client, slug, score=7)
    with app.app_context():
        assert Status.query.one().value == "jogado"
        Status.query.one().value = "jogando"
        db.session.commit()
    rate(client, slug, score=9)
    with app.app_context():
        assert Status.query.one().value == "jogando"  # não sobrescreve
        assert Activity.query.filter_by(kind="avaliou").count() == 1
