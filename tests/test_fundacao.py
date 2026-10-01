from app.util import paginate
from app.models import Genre


def test_erro_404_amigavel(client):
    r = client.get("/nao-existe")
    assert r.status_code == 404 and "Página não encontrada" in r.get_data(as_text=True)


def test_paginate_fora_do_intervalo_cai_na_ultima(app):
    with app.app_context():
        from app.models import db

        for i in range(45):
            db.session.add(Genre(name=f"g{i}", slug=f"g{i}"))
        db.session.commit()
        p = paginate(Genre.query.order_by(Genre.id), 99)
        assert (p.page, p.pages, len(p.items)) == (3, 3, 5)
        assert paginate(Genre.query, "abc").page == 1
