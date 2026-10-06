"""Comparação de gosto entre a pessoa logada e outra (AFI-01..10)."""
from math import floor

from flask import Blueprint, redirect, render_template
from sqlalchemy import func

from .models import Follow, Game, Review, Status, User, db
from .util import current_user, login_required

bp = Blueprint("afinidade", __name__)
MIN_COMUNS = 3


def notas(user_ids):
    """{user_id: {game_id: nota}} em uma consulta; sem avaliações ocultas nem jogos removidos (AFI-09)."""
    rows = (
        db.session.query(Review.user_id, Review.game_id, Review.score)
        .join(Game, Game.id == Review.game_id)
        .filter(Review.user_id.in_(user_ids), Review.hidden.is_(False), Game.removed_at.is_(None))
        .all()
    )
    out = {uid: {} for uid in user_ids}
    for uid, gid, score in rows:
        out[uid][gid] = score
    return out


def resumo(a, b):
    """(afinidade % ou None, nº de jogos em comum) a partir de dois {game_id: nota} (AFI-02)."""
    comuns = a.keys() & b.keys()
    if len(comuns) < MIN_COMUNS:
        return None, len(comuns)
    media = sum(abs(a[g] - b[g]) for g in comuns) / len(comuns)
    return floor(100 * (1 - media / 10) + 0.5), len(comuns)


def resumo_com(me_id, outro_id):
    n = notas([me_id, outro_id])
    return resumo(n[me_id], n[outro_id])


@bp.route("/comparar")
@login_required
def indice():
    me = current_user()
    seguidos = User.query.join(Follow, Follow.followed_id == User.id).filter(Follow.follower_id == me.id).all()
    n = notas([me.id] + [u.id for u in seguidos])
    linhas = []
    for u in seguidos:
        pct, comuns = resumo(n[me.id], n[u.id])
        linhas.append((u, pct, comuns))
    linhas.sort(key=lambda r: (r[1] is None, -(r[1] or 0), r[0].username_lower))  # AFI-06
    return render_template("afinidade/indice.html", linhas=linhas)


@bp.route("/u/<username>/comparar")
@login_required
def comparar(username):
    outro = User.query.filter_by(username_lower=username.lower()).first_or_404()
    me = current_user()
    if outro.id == me.id:
        return redirect(f"/u/{me.username}")  # AFI-07
    n = notas([me.id, outro.id])
    pct, qtd = resumo(n[me.id], n[outro.id])
    comuns = n[me.id].keys() & n[outro.id].keys()
    jogos = {g.id: g for g in Game.query.filter(Game.id.in_(comuns))} if comuns else {}
    linhas = sorted(
        ((jogos[g], n[me.id][g], n[outro.id][g], abs(n[me.id][g] - n[outro.id][g])) for g in comuns),
        key=lambda r: (r[3], r[0].title),
    )
    concordam = [r for r in linhas if r[3] <= 1][:5]
    divergem = sorted((r for r in linhas if r[3] >= 3), key=lambda r: (-r[3], r[0].title))[:5]
    indicacoes = (
        Review.query.join(Game, Game.id == Review.game_id)
        .filter(Review.user_id == outro.id, Review.hidden.is_(False), Review.score >= 8, Game.removed_at.is_(None),
                Review.game_id.notin_(db.session.query(Review.game_id).filter(Review.user_id == me.id)),
                Review.game_id.notin_(db.session.query(Status.game_id).filter(Status.user_id == me.id)))
        .order_by(Review.score.desc(), Game.title)
        .limit(5)
        .all()
    )
    return render_template("afinidade/comparar.html", outro=outro, pct=pct, qtd=qtd, linhas=linhas,
                           concordam=concordam, divergem=divergem, indicacoes=indicacoes)
