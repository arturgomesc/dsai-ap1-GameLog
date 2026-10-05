import json

from app.fontes import FONTES, arquivo
from app.models import Game, Review, User, db
from app.seed import run


def snapshot():
    return (sorted((g.slug, g.cover_url) for g in Game.query),
            sorted((r.user_id, r.game_id, r.score, r.text) for r in Review.query))


def test_cre01_cre02_seed_so_com_jogos_reais(app):
    with app.app_context():
        run(42, real=True)
        assert Game.query.count() >= 100 and User.query.count() >= 20
        assert Game.query.filter(Game.source.is_(None)).count() == 0
        assert Game.query.filter(Game.cover_url.is_(None)).count() == 0
        assert all(g.genres and g.developer for g in Game.query)


def test_cre03_fonte_arquivo_filtra_por_termo():
    assert FONTES["arquivo"] is arquivo
    todos = list(arquivo.listar(10**6))
    achados = list(arquivo.listar(10**6, todos[0]["title"][:6].upper()))
    assert achados and todos[0]["title"] in [j["title"] for j in achados]


def test_cre04_export_games(app, tmp_path, monkeypatch):
    from datetime import date

    from app.fontes import steam
    monkeypatch.setattr(steam, "listar", lambda l, t: [{"external_id": t, "release_date": date(2020, 1, 2), "title": t}]
                        if t != "nada" else [])
    saida = tmp_path / "j.json"
    r = app.test_cli_runner().invoke(args=["export-games", "--termos", "a;b;nada;a", "--saida", str(saida)])
    assert "jogos=2 sem_resultado=1" in r.output
    assert [j["release_date"] for j in json.loads(saida.read_text())] == ["2020-01-02"] * 2


def test_cre05_seed_real_determinístico(tmp_path):
    from app import create_app
    out = []
    for i in range(2):
        a = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path}/{i}.db"})
        with a.app_context():
            run(7, real=True)
            out.append(snapshot())
            db.session.remove()
            db.engine.dispose()
    assert out[0] == out[1]


def test_cre06_cre07_destaques_na_home(app, client):
    with app.app_context():
        run(42, real=True)
        por_jogo = {}
        for r in Review.query:
            por_jogo.setdefault(r.game_id, []).append(r)
        assert 25 <= len(por_jogo) <= 35 and all(len(v) >= 3 for v in por_jogo.values())
        assert sum(bool(r.text) for r in Review.query) > Review.query.count() / 2
        sem = Game.query.filter(~Game.id.in_(por_jogo)).first()
        com = Game.query.get(next(iter(por_jogo)))
        titulo_sem = sem.title
        # esconde avaliações de um jogo até sobrar menos de 3: ele sai do destaque
        alvo = Game.query.get(max(por_jogo, key=lambda k: len(por_jogo[k])))
        for r in por_jogo[alvo.id][:-2]:
            r.hidden = True
        db.session.commit()
        titulo_alvo = alvo.title
    html = client.get("/").data.decode()
    destaque = html.split("Em destaque")[1].split("Lançamentos recentes")[0]
    assert "avaliações" in destaque and "★" in destaque
    assert titulo_sem not in destaque and titulo_alvo not in destaque
