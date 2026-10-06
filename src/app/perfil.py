"""Dados do perfil público (PRF-01..09): tudo agregado no banco, sem consulta por avaliação."""
from sqlalchemy import func, or_
from sqlalchemy.orm import contains_eager

from .models import Game, Genre, Review, Status, STATUSES, db, game_genres
from .util import paginate

FAVORITO_MIN = 8
TRECHO = 140


def _avaliadas(user_id):
    """Avaliações visíveis de jogos que ainda estão no catálogo (PRF-06)."""
    return (
        Review.query.join(Game, Review.game_id == Game.id)
        .filter(Review.user_id == user_id, Review.hidden.is_(False), Game.removed_at.is_(None))
    )


def dados(user_id, page):
    por_status = dict(
        db.session.query(Status.value, func.count())
        .join(Game, Status.game_id == Game.id)
        .filter(Status.user_id == user_id, Game.removed_at.is_(None))
        .group_by(Status.value)
        .all()
    )
    status = {k: (nome, por_status.get(k, 0)) for k, nome in STATUSES.items()}

    notas = dict(
        _avaliadas(user_id).with_entities(Review.score, func.count()).group_by(Review.score).all()
    )
    total = sum(notas.values())
    hist = {n: notas.get(n, 0) for n in range(11)}
    media = sum(n * c for n, c in notas.items()) / total if total else None

    conhecidos = or_(
        Game.id.in_(_avaliadas(user_id).with_entities(Review.game_id)),
        Game.id.in_(db.session.query(Status.game_id).filter(Status.user_id == user_id, Status.value == "jogado")),
    )
    generos = (
        db.session.query(Genre.name, Genre.slug, func.count(func.distinct(Game.id)).label("n"))
        .join(game_genres, game_genres.c.genre_id == Genre.id)
        .join(Game, Game.id == game_genres.c.game_id)
        .filter(Game.removed_at.is_(None), conhecidos)
        .group_by(Genre.id)
        .order_by(func.count(func.distinct(Game.id)).desc(), Genre.name)
        .limit(5)
        .all()
    )

    favoritos = (
        _avaliadas(user_id)
        .filter(Review.score >= FAVORITO_MIN)
        .order_by(Review.score.desc(), Review.created_at.desc(), Game.title)
        .options(contains_eager(Review.game))
        .limit(5)
        .all()
    )
    linha = paginate(
        _avaliadas(user_id).order_by(Review.created_at.desc(), Review.id.desc()).options(contains_eager(Review.game)),
        page, per_page=10,
    )
    return {"status": status, "media": media, "hist": hist, "hist_max": max(hist.values()) or 1, "total": total,
            "generos": generos, "favoritos": favoritos, "linha": linha}
