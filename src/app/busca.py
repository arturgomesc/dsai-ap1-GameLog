from datetime import date

from flask import Blueprint, render_template, request
from sqlalchemy import case, func, literal

from .models import Developer, Game, Genre, Platform, avg_subquery, visible_games
from .util import fold, paginate

bp = Blueprint("busca", __name__)
SORTS = {"relevancia": "Relevância", "nota": "Nota média", "data": "Lançamento", "titulo": "Título (A–Z)"}


def _int(value, lo, hi):
    """BUS-08: valor inválido vira None (ignorado), nunca erro."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return None
    return n if lo <= n <= hi else None


def search_games(args):
    sub = avg_subquery()
    q = visible_games().join(Developer).outerjoin(sub, sub.c.gid == Game.id).add_columns(sub.c.avg)
    text = fold(args.get("q", "").strip())
    for term in text.split():
        like = f"%{term}%"
        q = q.filter(
            func.fold(Game.title).like(like)
            | func.fold(Developer.name).like(like)
            | Game.genres.any(func.fold(Genre.name).like(like))
        )
    genres = [g for g in args.getlist("genero") if g]
    if genres:
        q = q.filter(Game.genres.any(Genre.slug.in_(genres)))
    plats = [p for p in args.getlist("plataforma") if p]
    if plats:
        q = q.filter(Game.platforms.any(Platform.slug.in_(plats)))
    y0, y1 = _int(args.get("ano_de"), 1, 9999), _int(args.get("ano_ate"), 1, 9999)
    if y0:
        q = q.filter(Game.release_date >= date(y0, 1, 1))
    if y1:
        q = q.filter(Game.release_date <= date(y1, 12, 31))
    try:
        nmin = float(args.get("nota_min", ""))
    except ValueError:
        nmin = None
    if nmin is not None and 0 < nmin <= 10:
        q = q.filter(sub.c.avg >= nmin)
    sort = args.get("ordem") if args.get("ordem") in SORTS else "relevancia"
    if sort == "nota":
        q = q.order_by(sub.c.avg.is_(None), sub.c.avg.desc(), Game.title)
    elif sort == "data":
        q = q.order_by(Game.release_date.desc(), Game.title)
    elif sort == "titulo":
        q = q.order_by(func.fold(Game.title))
    else:  # relevância: título exato > começa com > contém > casou por dev/gênero
        t = f"%{text}%"
        rel = case((func.fold(Game.title) == text, 0), (func.fold(Game.title).like(f"{text}%"), 1),
                   (func.fold(Game.title).like(t), 2), else_=3) if text else literal(0)
        q = q.order_by(rel, sub.c.avg.is_(None), sub.c.avg.desc(), func.fold(Game.title))
    return q, sort


@bp.route("/buscar")
def search():
    q, sort = search_games(request.args)
    page = paginate(q, request.args.get("page"))
    return render_template(
        "busca/buscar.html", page=page, sort=sort, sorts=SORTS,
        genres=Genre.query.order_by(Genre.name).all(), platforms=Platform.query.order_by(Platform.name).all(),
        sel_genres=request.args.getlist("genero"), sel_plats=request.args.getlist("plataforma"),
        filtered=any(request.args.get(k) for k in ("q", "genero", "plataforma", "ano_de", "ano_ate", "nota_min")),
    )
