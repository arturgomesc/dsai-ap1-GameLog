from flask import Blueprint, render_template, request
from sqlalchemy import func

from .models import (
    REPORT_REASONS, STATUSES, Game, GameList, Like, Review, Status, avg_subquery, db, game_genres, game_stats,
    visible_games,
)
from .util import current_user, paginate

bp = Blueprint("jogo", __name__)


def related_games(game, limit=6):
    """PAG-08: compartilham gênero; ordena por gêneros em comum e depois nota média."""
    sub = avg_subquery()
    shared = func.count(game_genres.c.genre_id)
    return (
        visible_games()
        .join(game_genres, game_genres.c.game_id == Game.id)
        .outerjoin(sub, sub.c.gid == Game.id)
        .filter(game_genres.c.genre_id.in_([g.id for g in game.genres]), Game.id != game.id)
        .group_by(Game.id)
        .order_by(shared.desc(), sub.c.avg.is_(None), sub.c.avg.desc(), Game.title)
        .limit(limit)
        .add_columns(sub.c.avg)
        .all()
    )


@bp.route("/jogos/<slug>")
def game_page(slug):
    game = visible_games().filter_by(slug=slug).first_or_404()
    me = current_user()
    likes = func.count(Like.id)
    q = (
        db.session.query(Review, likes.label("likes"))
        .outerjoin(Like, Like.review_id == Review.id)
        .filter(Review.game_id == game.id, Review.hidden.is_(False), Review.text != "")
        .group_by(Review.id)
    )
    sort = "recentes" if request.args.get("ordem") == "recentes" else "curtidas"
    q = q.order_by(likes.desc(), Review.created_at.desc()) if sort == "curtidas" else q.order_by(Review.created_at.desc())
    page = paginate(q, request.args.get("page"))
    mine = status = None
    liked, my_lists = set(), []
    if me:
        mine = Review.query.filter_by(user_id=me.id, game_id=game.id).first()
        s = Status.query.filter_by(user_id=me.id, game_id=game.id).first()
        status = s.value if s else None
        liked = {x.review_id for x in Like.query.filter_by(user_id=me.id)}
        my_lists = GameList.query.filter_by(user_id=me.id).order_by(GameList.name).all()
    stats = game_stats(game.id)
    return render_template(
        "jogo/pagina.html", game=game, stats=stats, page=page, sort=sort, mine=mine, status=status, liked=liked,
        my_lists=my_lists, statuses=STATUSES, reasons=REPORT_REASONS, related=related_games(game),
        hist_max=max(stats["hist"].values()) or 1,
    )
