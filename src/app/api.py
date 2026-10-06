"""API JSON pública e somente leitura (API-01..10). Reaproveita a busca e as estatísticas das páginas."""
import json

from flask import Blueprint, Response, request
from sqlalchemy import func
from sqlalchemy.orm import joinedload, selectinload

from .busca import search_games
from .models import Game, Like, Review, db, game_stats, visible_games
from .util import paginate

bp = Blueprint("api", __name__, url_prefix="/api")
PER_PAGE, PER_PAGE_MAX = 20, 50
ENDPOINTS = {
    "/api/jogos": "lista e busca (q, genero, plataforma, ano_de, ano_ate, nota_min, ordem, page, per_page)",
    "/api/jogos/<slug>": "detalhe de um jogo",
    "/api/jogos/<slug>/avaliacoes": "avaliações visíveis de um jogo (page, per_page)",
}


def resposta(dados, status=200):
    return Response(json.dumps(dados, ensure_ascii=False), status, content_type="application/json; charset=utf-8")


def erro(status, msg):
    return resposta({"erro": msg}, status)


def per_page():
    try:
        n = int(request.args.get("per_page", ""))
    except ValueError:
        return PER_PAGE
    return n if 1 <= n <= PER_PAGE_MAX else PER_PAGE  # API-03


def absoluta(url):
    return request.url_root.rstrip("/") + url if url.startswith("/") else url


def item(game, avg, n):
    return {
        "slug": game.slug,
        "titulo": game.title,
        "lancamento": game.release_date.isoformat(),
        "desenvolvedora": game.developer.name,
        "generos": sorted(g.name for g in game.genres),
        "plataformas": sorted(p.name for p in game.platforms),
        "capa": absoluta(game.cover),
        "nota_media": round(avg, 1) if avg is not None else None,
        "avaliacoes": n,
        "url": absoluta(f"/jogos/{game.slug}"),
    }


def paginado(page, itens):
    return {"items": itens, "page": page.page, "pages": page.pages, "total": page.total, "per_page": per_page()}


@bp.route("/")
@bp.route("")
def indice():
    return resposta({"versao": "1", "endpoints": ENDPOINTS})


@bp.route("/jogos")
def jogos():
    q, _ = search_games(request.args)
    q = q.options(selectinload(Game.genres), selectinload(Game.platforms), selectinload(Game.developer))
    page = paginate(q, request.args.get("page"), per_page())
    ids = [g.id for g, _ in page.items]
    contagem = dict(
        db.session.query(Review.game_id, func.count())
        .filter(Review.game_id.in_(ids), Review.hidden.is_(False)).group_by(Review.game_id).all()
    ) if ids else {}
    return resposta(paginado(page, [item(g, avg, contagem.get(g.id, 0)) for g, avg in page.items]))


def jogo_ou_404(slug):
    return visible_games().filter_by(slug=slug).first()


@bp.route("/jogos/<slug>")
def detalhe(slug):
    g = jogo_ou_404(slug)
    if not g:
        return erro(404, "Jogo não encontrado")
    s = game_stats(g.id)
    return resposta({**item(g, s["avg"], s["total"]), "sinopse": g.synopsis,
                     "histograma": {str(k): v for k, v in s["hist"].items()}})


@bp.route("/jogos/<slug>/avaliacoes")
def avaliacoes(slug):
    g = jogo_ou_404(slug)
    if not g:
        return erro(404, "Jogo não encontrado")
    q = (Review.query.filter_by(game_id=g.id, hidden=False).options(joinedload(Review.user))
         .order_by(Review.created_at.desc(), Review.id.desc()))
    page = paginate(q, request.args.get("page"), per_page())
    ids = [r.id for r in page.items]
    curtidas = dict(
        db.session.query(Like.review_id, func.count()).filter(Like.review_id.in_(ids)).group_by(Like.review_id).all()
    ) if ids else {}
    return resposta(paginado(page, [
        {"usuario": r.user.username, "nota": r.score, "texto": r.text, "spoiler": r.spoiler, "editada": r.edited,
         "data": r.created_at.isoformat(), "curtidas": curtidas.get(r.id, 0)}
        for r in page.items
    ]))


@bp.after_app_request
def cabecalhos(resp):
    """CORS aberto e cache curto só para leituras bem-sucedidas sob /api (API-01, API-09)."""
    if request.path == "/api" or request.path.startswith("/api/"):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        if resp.status_code == 200 and request.method in ("GET", "HEAD"):
            resp.headers["Cache-Control"] = "public, max-age=60"
    return resp
