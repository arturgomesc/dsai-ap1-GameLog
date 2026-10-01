from flask import Blueprint, flash, redirect, render_template, request
from sqlalchemy import func

from .models import Activity, Follow, Game, GameList, Review, User, db
from .util import current_user, login_required, paginate

bp = Blueprint("social", __name__)


def get_user(username):
    return User.query.filter_by(username_lower=username.lower()).first_or_404()


@bp.route("/u/<username>/seguir", methods=["POST"])
@login_required
def follow(username):
    target, me = get_user(username), current_user()
    if target.id == me.id:  # SOC-01
        flash("Você não pode seguir a si mesmo.", "erro")
    elif not Follow.query.filter_by(follower_id=me.id, followed_id=target.id).first():  # SOC-02
        db.session.add(Follow(follower_id=me.id, followed_id=target.id))
        db.session.commit()
    return redirect(f"/u/{target.username}")


@bp.route("/u/<username>/deixar-de-seguir", methods=["POST"])
@login_required
def unfollow(username):
    target = get_user(username)
    Follow.query.filter_by(follower_id=current_user().id, followed_id=target.id).delete()
    db.session.commit()
    return redirect(f"/u/{target.username}")


def people(username, kind):
    u = get_user(username)
    col, other = (Follow.followed_id, Follow.follower_id) if kind == "seguidores" else (Follow.follower_id, Follow.followed_id)
    q = User.query.join(Follow, other == User.id).filter(col == u.id).order_by(User.username_lower)
    return render_template("social/pessoas.html", u=u, kind=kind, page=paginate(q, request.args.get("page")))


@bp.route("/u/<username>/seguidores")
def followers(username):
    return people(username, "seguidores")


@bp.route("/u/<username>/seguindo")
def following(username):
    return people(username, "seguindo")


def feed_query(user_id):
    """SOC-04..08: só de quem sigo; esconde lista privada, avaliação oculta e jogo removido."""
    return (
        Activity.query.join(Follow, (Follow.followed_id == Activity.user_id) & (Follow.follower_id == user_id))
        .outerjoin(Review, Review.id == Activity.review_id)
        .outerjoin(Game, Game.id == Activity.game_id)
        .outerjoin(GameList, GameList.id == Activity.list_id)
        .filter(
            (Activity.review_id.is_(None)) | (Review.hidden.is_(False)),
            (Activity.game_id.is_(None)) | (Game.removed_at.is_(None)),
            (Activity.list_id.is_(None)) | (GameList.public.is_(True)),
        )
        .order_by(Activity.created_at.desc(), Activity.id.desc())
    )


def suggestions(me, limit=5):
    """SOC-09: usuários mais ativos que ainda não sigo."""
    followed = db.session.query(Follow.followed_id).filter(Follow.follower_id == me.id)
    return (
        User.query.outerjoin(Activity, Activity.user_id == User.id)
        .filter(User.id != me.id, User.id.not_in(followed))
        .group_by(User.id)
        .order_by(func.count(Activity.id).desc(), User.username_lower)
        .limit(limit)
        .all()
    )


@bp.route("/feed")
@login_required
def feed():
    me = current_user()
    page = paginate(feed_query(me.id), request.args.get("page"))
    return render_template("social/feed.html", page=page, suggestions=suggestions(me) if not page.items else [])
