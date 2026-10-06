import pytest
from sqlalchemy import event

from app.afinidade import resumo
from app.models import Follow, Game, User, db, now
from conftest import login, make_user
from test_perfil import avalia, jogo, status


@pytest.fixture
def duo(app):
    make_user(app, "ana")
    make_user(app, "bia")
    c = app.test_client()
    login(c, "ana")
    return c


def par(app, notas_ana, notas_bia, prefixo="J"):
    """Cria jogos e avaliações; devolve os ids. Notas None = não avaliou."""
    ids = []
    for i, (a, b) in enumerate(zip(notas_ana, notas_bia)):
        g = jogo(app, f"{prefixo}{i}")
        ids.append(g)
        if a is not None:
            avalia(app, "ana", g, a)
        if b is not None:
            avalia(app, "bia", g, b)
    return ids


def pagina(c, user="bia"):
    return c.get(f"/u/{user}/comparar").get_data(as_text=True)


def test_afi01_exige_login(app, client):
    make_user(app, "bia")
    for url in ("/comparar", "/u/bia/comparar"):
        r = client.get(url)
        assert r.status_code == 302 and "/entrar?next=" in r.headers["Location"]


def test_afi02_formula_e_minimo_de_jogos(app, duo):
    assert resumo({1: 10, 2: 8, 3: 5}, {1: 10, 2: 6, 3: 5}) == (93, 3)  # média da diferença 0,67
    assert resumo({1: 10, 2: 10, 3: 10}, {1: 0, 2: 0, 3: 0}) == (0, 3)
    assert resumo({1: 7, 2: 7, 3: 7}, {1: 7, 2: 7, 3: 7}) == (100, 3)
    assert resumo({1: 5, 2: 5}, {1: 5, 2: 5}) == (None, 2)
    par(app, [10, 8, 5], [10, 6, 5])
    assert "<strong>93%</strong>" in pagina(duo)
    par(app, [5, 5], [5, 5], "K")  # mais 2 jogos iguais: 5 em comum
    assert "5 jogos em comum" in pagina(duo)


def test_afi02_dados_insuficientes(app, duo):
    par(app, [5, 5], [5, 5])
    html = pagina(duo)
    assert "Dados insuficientes" in html and "%</strong> de afinidade" not in html


def test_afi03_tabela_ordenada_por_diferenca_e_titulo(app, duo):
    par(app, [9, 5, 8, 2], [9, 5, 6, 8], "Z")
    html = pagina(duo).split("Jogos em comum</h2>")[1]
    assert [html.index(f"Z{i}") for i in (0, 1, 2, 3)] == sorted(html.index(f"Z{i}") for i in (0, 1, 2, 3))
    assert "<td>2</td></tr>" in html and "<td>6</td></tr>" in html  # diferenças 2 e 6


def test_afi04_concordam_e_divergem(app, duo):
    par(app, [8, 8, 9, 3, 9, 6], [8, 7, 9, 9, 3, 4], "C")
    html = pagina(duo)
    conc = html.split("Concordam</h2>")[1].split("Divergem</h2>")[0]
    div = html.split("Divergem</h2>")[1].split("Indicações de")[0]
    assert all(f"C{i}" in conc for i in (0, 1, 2)) and "C5" not in conc  # diferença 2 fica fora dos dois
    assert "C3" in div and "C4" in div and "C5" not in div


def test_afi04_listas_vazias_com_mensagem(app, duo):
    par(app, [5, 5, 5], [8, 8, 7], "V")  # diferenças 3,3,2 → divergem tem 2, concordam nenhum
    html = pagina(duo)
    assert "Nenhum jogo com notas parecidas." in html and "V0" in html.split("Divergem</h2>")[1]


def test_afi05_indicacoes(app, duo):
    ids = par(app, [None, 9, None, None, None, None, None], [10, 10, 9, 8, 7, 9, 9], "I")
    status(app, "ana", ids[3], "planejado")  # já marcou: não indica
    html = pagina(duo).split("Indicações de")[1].split("Jogos em comum")[0]
    assert html.index("I0") < min(html.index("I2"), html.index("I5"), html.index("I6"))  # nota 10 primeiro
    assert "I1" not in html and "I3" not in html and "I4" not in html  # avaliado por mim, com status, nota 7
    assert html.count("/jogos/") == 4  # sobram I0, I2, I5 e I6


def test_afi05_limite_de_5(app, duo):
    par(app, [None] * 7, [9] * 7, "L")
    assert pagina(duo).split("Indicações de")[1].split("</section>")[0].count("/jogos/") == 5


def test_afi06_indice_ordenado(app, duo):
    for nome in ("caio", "dani", "edu"):
        make_user(app, nome)
    jogos = [jogo(app, f"X{i}") for i in range(3)]
    for g in jogos:
        avalia(app, "ana", g, 8)
    for nome, nota in (("bia", 8), ("caio", 5), ("dani", 8)):
        for g in jogos:
            avalia(app, nome, g, nota)
    avalia(app, "edu", jogos[0], 8)  # só 1 em comum: sem percentual, vai por último
    for nome in ("bia", "caio", "dani", "edu"):
        duo.post(f"/u/{nome}/seguir")
    html = duo.get("/comparar").get_data(as_text=True)
    ordem = [html.index(f"@{n}") for n in ("bia", "dani", "caio", "edu")]  # 100 (bia<dani por nome), 70, sem dados
    assert ordem == sorted(ordem) and "<strong>100%</strong>" in html and "<strong>70%</strong>" in html
    assert "dados insuficientes" in html and "1 jogo em comum" in html


def test_afi06_sem_seguidos(duo):
    assert "ainda não segue ninguém" in duo.get("/comparar").get_data(as_text=True)


def test_afi07_si_mesmo_e_inexistente(duo):
    r = duo.get("/u/ana/comparar")
    assert r.status_code == 302 and r.headers["Location"] == "/u/ana"
    assert duo.get("/u/ninguem/comparar").status_code == 404


def test_afi08_link_no_perfil(app, duo, client):
    par(app, [5, 5, 5], [5, 5, 5])
    assert "Afinidade com você: <strong>100%</strong>" in duo.get("/u/bia").get_data(as_text=True)
    assert 'href="/u/bia/comparar"' in duo.get("/u/bia").get_data(as_text=True)
    assert "Afinidade" not in duo.get("/u/ana").get_data(as_text=True)
    assert "Afinidade" not in client.get("/u/bia").get_data(as_text=True)


def test_afi09_ocultas_removidas_e_simetria(app, duo):
    from app.models import Review
    ids = par(app, [8, 8, 8, 8, 2], [8, 8, 8, 2, 8], "S")
    with app.app_context():
        db.session.get(Game, ids[4]).removed_at = now()  # removido: sai
        Review.query.filter_by(game_id=ids[3], user_id=User.query.filter_by(username="bia").one().id).one().hidden = True
        db.session.commit()
    html = pagina(duo)
    assert "<strong>100%</strong>" in html and "3 jogos em comum" in html
    with app.app_context():
        a, b = (User.query.filter_by(username=n).one().id for n in ("ana", "bia"))
        from app.afinidade import resumo_com
        assert resumo_com(a, b) == resumo_com(b, a)


def test_afi10_consultas_nao_crescem_com_seguidos(app, duo):
    jogos = [jogo(app, f"Q{i}") for i in range(4)]
    for g in jogos:
        avalia(app, "ana", g, 7)
    contagens = []
    for total in (2, 12):
        for i in range(len(contagens) and 2 or 0, total):
            nome = f"p{i:02d}"
            make_user(app, nome)
            duo.post(f"/u/{nome}/seguir")
            for g in jogos:
                avalia(app, nome, g, 6)
        qs = []

        def conta(*a, _l=qs):
            _l.append(1)
        with app.app_context():
            event.listen(db.engine, "before_cursor_execute", conta)
            assert duo.get("/comparar").status_code == 200
            event.remove(db.engine, "before_cursor_execute", conta)
        contagens.append(len(qs))
    assert contagens[1] <= 12 and contagens[1] <= contagens[0] + 1
