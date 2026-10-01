from app.models import User, db
from conftest import login, make_user

OK = {"username": "ana", "email": "ana@ex.com", "password": "senha1234"}


def signup(client, **kw):
    return client.post("/cadastro", data={**OK, **kw})


def test_cad01_validacoes(client, app):
    assert signup(client, username="ab").status_code == 400
    assert signup(client, username="x" * 21).status_code == 400
    assert signup(client, email="invalido").status_code == 400
    assert signup(client, password="curta").status_code == 400
    assert signup(client).status_code == 302
    assert signup(client, username="ANA", email="outro@ex.com").status_code == 400  # sem diferenciar maiúsculas
    assert signup(client, username="bia", email="ANA@ex.com").status_code == 400  # e-mail único


def test_cad02_hash_com_salt(client, app):
    signup(client)
    with app.app_context():
        h = User.query.one().password_hash
        assert "senha1234" not in h and h.count("$") >= 2


def test_cad03_login_generico(client, app):
    make_user(app)
    assert login(client).status_code == 302
    c2 = app.test_client()
    a = c2.post("/entrar", data={"email": "ana@ex.com", "password": "errada123"})
    b = c2.post("/entrar", data={"email": "nao@existe.com", "password": "errada123"})
    assert a.status_code == b.status_code == 401
    assert "E-mail ou senha incorretos" in a.get_data(as_text=True)
    assert "E-mail ou senha incorretos" in b.get_data(as_text=True)


def test_cad04_bloqueio_apos_5_falhas(client, app):
    make_user(app)
    for _ in range(5):
        client.post("/entrar", data={"email": "ana@ex.com", "password": "x"})
    r = login(client)  # senha certa, mas bloqueado
    assert r.status_code == 429


def test_cad05_logout_invalida_sessao_no_servidor(client, app):
    make_user(app)
    login(client)
    with client.session_transaction() as s:
        old = dict(s)
    client.post("/sair")
    with client.session_transaction() as s:
        s.update(old)  # reaproveita o cookie antigo
    assert client.get("/u/ana/editar").status_code == 302  # continua deslogado


def test_cad06_volta_a_acao_apos_login(client, app):
    make_user(app)
    r = client.get("/u/ana/editar")
    assert r.status_code == 302 and "next=" in r.headers["Location"]
    r = client.post("/entrar?next=/u/ana/editar", data={"email": "ana@ex.com", "password": "senha1234"})
    assert r.headers["Location"] == "/u/ana/editar"
    # open redirect bloqueado
    c2 = app.test_client()
    r = c2.post("/entrar?next=//evil.com", data={"email": "ana@ex.com", "password": "senha1234"})
    assert r.headers["Location"] == "/"


def test_cad07_perfil_publico(client, app):
    make_user(app)
    html = client.get("/u/ana").get_data(as_text=True)
    assert "avaliações" in html and "seguidores" in html and "no GameLog desde" in html
    assert client.get("/u/fantasma").status_code == 404


def test_cad08_edicao_e_avatar(client, app):
    make_user(app)
    login(client)
    assert client.post("/u/ana/editar", data={"display_name": "Ana", "bio": "x" * 281}).status_code == 400
    assert client.post("/u/ana/editar", data={"display_name": "Ana Lima", "bio": "oi"}).status_code == 302
    html = client.get("/u/ana").get_data(as_text=True)
    assert "Ana Lima" in html and 'class="avatar big" style="background:hsl(' in html


def test_cad09_nao_edita_outro(client, app):
    make_user(app)
    make_user(app, "bia")
    login(client)
    assert client.get("/u/bia/editar").status_code == 403
    assert client.post("/u/bia/editar", data={"display_name": "hack"}).status_code == 403


def test_cad10_novo_cadastro_e_jogador(client, app):
    signup(client)
    with app.app_context():
        assert User.query.one().role == "jogador"


def test_csrf_bloqueia_post_sem_token(tmp_path):
    from app import create_app

    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path}/c.db"})
    assert app.test_client().post("/cadastro", data=OK).status_code == 400
