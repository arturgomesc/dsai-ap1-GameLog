from datetime import timedelta

from sqlalchemy import event

from app.models import Game, GameList, Review, Status, User, db, now
from conftest import login, make_game, make_user


def jogo(app, titulo, genero="Ação", **kw):
    make_game(app, titulo, genre=genero, **kw)
    with app.app_context():
        return Game.query.filter_by(title=titulo).one().id


def avalia(app, user, gid, nota, texto="", dias=0, hidden=False):
    with app.app_context():
        uid = User.query.filter_by(username=user).one().id
        db.session.add(Review(user_id=uid, game_id=gid, score=nota, text=texto, hidden=hidden,
                              created_at=now() - timedelta(days=dias)))
        db.session.commit()


def status(app, user, gid, valor):
    with app.app_context():
        uid = User.query.filter_by(username=user).one().id
        db.session.add(Status(user_id=uid, game_id=gid, value=valor))
        db.session.commit()


def perfil(client, q=""):
    return client.get("/u/ana" + q).get_data(as_text=True)


def secao(html, ini, fim):
    return html.split(ini)[1].split(fim)[0]


def test_prf01_jogos_por_status(app, client):
    make_user(app, "ana")
    a, b = jogo(app, "A"), jogo(app, "B")
    status(app, "ana", a, "jogado")
    status(app, "ana", b, "jogado")
    html = secao(perfil(client), "Jogos por status", "Notas")
    assert "Jogado: <strong>2</strong>" in html and "Abandonado: <strong>0</strong>" in html
    assert "Planejado: <strong>0</strong>" in html and "Jogando: <strong>0</strong>" in html


def test_prf02_media_e_histograma(app, client):
    make_user(app, "ana")
    ids = [jogo(app, t) for t in "ABC"]
    for g, n in zip(ids, (10, 7, 7)):
        avalia(app, "ana", g, n)
    html = secao(perfil(client), "<h2>Notas</h2>", "Gêneros favoritos")
    assert "<strong>8.0</strong>" in html and "3 avaliações" in html
    assert 'title="Nota 7: 2"' in html and 'title="Nota 10: 1"' in html and 'title="Nota 0: 0"' in html


def test_prf03_generos_favoritos(app, client):
    make_user(app, "ana")
    acoes = [jogo(app, f"Ac{i}", "Ação") for i in range(3)]
    rpgs = [jogo(app, f"Rp{i}", "RPG") for i in range(2)]
    for g in acoes[:2] + rpgs[:1]:
        avalia(app, "ana", g, 5)
    status(app, "ana", acoes[2], "jogado")  # jogado conta; planejado não
    status(app, "ana", rpgs[1], "planejado")
    html = secao(perfil(client), "Gêneros favoritos", "Linha do tempo")
    assert html.index("Ação") < html.index("RPG")
    assert "3 jogos" in html and "1 jogo<" in html and 'href="/generos/acao"' in html


def test_prf03_no_maximo_5_generos(app, client):
    make_user(app, "ana")
    for i in range(7):
        avalia(app, "ana", jogo(app, f"J{i}", f"Gen{i}"), 5)
    html = secao(perfil(client), "Gêneros favoritos", "Linha do tempo")
    assert html.count('href="/generos/') == 5


def test_prf04_favoritos_ordenados_e_limitados(app, client):
    make_user(app, "ana")
    notas = {"Baixa": 7, "Nove velho": 9, "Dez": 10, "Nove novo": 9, "Oito": 8, "Oito b": 8, "Oito c": 8}
    for i, (t, n) in enumerate(notas.items()):
        avalia(app, "ana", jogo(app, t), n, dias=10 - i if t != "Nove novo" else 0)
    html = secao(perfil(client), "Jogos favoritos", "Linha do tempo")
    ordem = [t for t in ("Dez", "Nove novo", "Nove velho") if t in html]
    assert ordem == ["Dez", "Nove novo", "Nove velho"]
    assert html.index("Dez") < html.index("Nove novo") < html.index("Nove velho")
    assert html.count('class="card"') == 5 and "Baixa" not in html


def test_prf04_sem_favoritos_some_a_secao(app, client):
    make_user(app, "ana")
    avalia(app, "ana", jogo(app, "Mediano"), 6)
    assert "Jogos favoritos" not in perfil(client)


def test_prf05_linha_do_tempo_paginada(app, client):
    make_user(app, "ana")
    for i in range(12):
        avalia(app, "ana", jogo(app, f"T{i:02d}"), 5, texto="x" * 200 if i == 0 else "", dias=i)
    p1 = secao(perfil(client), "Linha do tempo", "<h2>Listas")
    assert "T00" in p1 and "T09" in p1 and "T10" not in p1 and "Página 1 de 2" in p1
    assert "x" * 140 + "…" in p1 and "x" * 141 not in p1
    p2 = secao(perfil(client, "?page=2"), "Linha do tempo", "<h2>Listas")
    assert "T10" in p2 and "T11" in p2 and "T00" not in p2
    assert "Página 2 de 2" in secao(perfil(client, "?page=99"), "Linha do tempo", "<h2>Listas")


def test_prf06_ocultas_e_removidas_ficam_de_fora(app, client):
    make_user(app, "ana")
    ok, oculta, removida = jogo(app, "Visivel"), jogo(app, "Oculta", "Terror"), jogo(app, "Removida", "Luta")
    avalia(app, "ana", ok, 9)
    avalia(app, "ana", oculta, 10, hidden=True)
    avalia(app, "ana", removida, 10)
    status(app, "ana", removida, "jogado")
    with app.app_context():
        db.session.get(Game, removida).removed_at = now()
        db.session.commit()
    html = perfil(client)
    assert "Oculta" not in html and "Removida" not in html and "Terror" not in html and "Luta" not in html
    assert "1 avaliações" in html and "Jogado: <strong>0</strong>" in html and "<strong>9.0</strong>" in html


def test_prf07_perfil_vazio(app, client):
    make_user(app, "ana")
    r = client.get("/u/ana")
    html = r.get_data(as_text=True)
    assert r.status_code == 200 and "Nenhuma avaliação ainda." in html and "Ainda sem dados suficientes." in html
    assert "<strong>—</strong>" in html and "Jogos favoritos" not in html
    assert client.get("/u/ninguem").status_code == 404


def test_prf08_lista_privada_continua_invisivel(app, client):
    uid = make_user(app, "ana")
    with app.app_context():
        db.session.add_all([GameList(user_id=uid, name="Publica", public=True),
                            GameList(user_id=uid, name="Secreta", public=False)])
        db.session.commit()
    html = perfil(client)
    assert "Publica" in html and "Secreta" not in html and "<strong>1</strong> listas" in html


def test_prf09_consultas_nao_crescem_com_avaliacoes(app):
    make_user(app, "ana")
    ids = [jogo(app, f"G{i}", f"Gen{i % 3}") for i in range(30)]
    contagens = []
    for n in (3, 30):
        for g in ids[(3 if contagens else 0):n]:
            avalia(app, "ana", g, 9, texto="ok")
        c = app.test_client()
        consultas = []

        def conta(*a, _l=consultas):
            _l.append(1)
        with app.app_context():
            event.listen(db.engine, "before_cursor_execute", conta)
            assert c.get("/u/ana").status_code == 200
            event.remove(db.engine, "before_cursor_execute", conta)
        contagens.append(len(consultas))
    assert contagens[1] <= 15 and contagens[1] <= contagens[0] + 1
