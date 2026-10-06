from flask import Blueprint, redirect, render_template, request
from sqlalchemy.orm import selectinload

from .afinidade import notas, resumo
from .models import Dismissed, Game, Review, Status, User, avg_subquery, db, visible_games
from .util import current_user, login_required

bp = Blueprint("recomendacoes", __name__)
LIMIT = 20
AFINIDADE_MIN = 70  # COL-01
NOTA_BOA = 8  # COL-02


def avg_map():
    sub = avg_subquery()
    return {gid: avg for gid, avg in db.session.query(sub.c.gid, sub.c.avg)}


def vizinhos(user_id):
    """[(afinidade 0-1, username, {game_id: nota})] das pessoas com gosto parecido (COL-01).

    ponytail: lê as notas de todo mundo numa consulta; com muitos usuários, pré-calcular os vizinhos.
    """
    ids = [i for (i,) in db.session.query(User.id).filter(User.id != user_id)]
    if not ids:
        return []
    n = notas(ids + [user_id])
    nomes = dict(db.session.query(User.id, User.username_lower).filter(User.id.in_(ids)))
    out = []
    for uid in ids:
        pct, _ = resumo(n[user_id], n[uid])
        if pct is not None and pct >= AFINIDADE_MIN:
            out.append((pct / 100, nomes[uid], n[uid]))
    return out


def colaborativo(viz):
    """{game_id: (pontuação, afinidade, username, nota)} pelo vizinho mais afim que recomenda (COL-02, COL-04)."""
    pont, melhor = {}, {}
    for pct, nome, notas_viz in viz:
        for gid, nota in notas_viz.items():
            if nota >= NOTA_BOA:
                pont[gid] = pont.get(gid, 0) + pct
                if gid not in melhor or (-pct, nome) < (-melhor[gid][0], melhor[gid][1]):
                    melhor[gid] = (pct, nome, nota)
    return {gid: (p / len(viz), *melhor[gid]) for gid, p in pont.items()}


def recommend(user_id, limit=LIMIT):
    """Retorna (lista de (jogo, nota, motivo), aviso). Determinístico: desempate por título (REC-05)."""
    avgs = avg_map()
    reviews = (
        Review.query.filter_by(user_id=user_id, hidden=False).options(selectinload(Review.game).selectinload(Game.genres)).all()
    )
    seen = {r.game_id for r in reviews} | {s.game_id for s in Status.query.filter_by(user_id=user_id)}  # REC-01
    seen |= {d.game_id for d in Dismissed.query.filter_by(user_id=user_id)}  # REC-07
    games = [g for g in visible_games().options(selectinload(Game.genres), selectinload(Game.developer)) if g.id not in seen]  # REC-06
    if not reviews:  # REC-04
        top = sorted(games, key=lambda g: (-(avgs.get(g.id) or 0), g.title))[:limit]
        return [(g, avgs.get(g.id), "bem avaliado pela comunidade") for g in top], (
            "Você ainda não avaliou nenhum jogo, então mostramos os mais bem avaliados. Avalie jogos para recomendações personalizadas."
        )
    # REC-02: afinidade por gênero; notas altas pesam mais (peso quadrático)
    affinity = {}
    for r in reviews:
        for gen in r.game.genres:
            affinity[gen.id] = affinity.get(gen.id, 0) + (r.score / 10) ** 2
    top_aff = max(affinity.values()) or 1
    colab = colaborativo(viz) if (viz := vizinhos(user_id)) else {}
    ranked = []
    for g in games:
        aff = sum(affinity.get(x.id, 0) for x in g.genres) / (len(g.genres) or 1) / top_aff
        avg = avgs.get(g.id)
        ranked.append((-(aff + 0.5 * (avg or 0) / 10 + colab.get(g.id, (0,))[0]), g.title, g, avg))
    ranked.sort(key=lambda t: (t[0], t[1]))
    liked = sorted(reviews, key=lambda r: (-r.score, r.game.title))
    out = []
    for _, _, g, avg in ranked[:limit]:
        gids = {x.id for x in g.genres}
        if g.id in colab:  # COL-04
            _, pct, nome, nota = colab[g.id]
            out.append((g, avg, f"@{nome}, com {round(pct * 100)}% de afinidade com você, deu nota {nota}"))
            continue
        why = next((r.game.title for r in liked if r.score >= 6 and gids & {x.id for x in r.game.genres}), None)
        out.append((g, avg, f"porque você gostou de {why}" if why else "bem avaliado pela comunidade"))
    return out, None


@bp.route("/recomendacoes")
@login_required
def page():
    recs, notice = recommend(current_user().id)
    return render_template("recomendacoes/pagina.html", recs=recs, notice=notice)


@bp.route("/recomendacoes/<int:gid>/dispensar", methods=["POST"])
@login_required
def dismiss(gid):
    me = current_user()
    db.get_or_404(Game, gid)
    if not Dismissed.query.filter_by(user_id=me.id, game_id=gid).first():
        db.session.add(Dismissed(user_id=me.id, game_id=gid))
        db.session.commit()
    return redirect(request.referrer or "/recomendacoes")
