from ..models import Developer, Game, Genre, Platform, db
from ..util import slugify
from . import arquivo, steam

FONTES = {"steam": steam, "arquivo": arquivo}  # nova fonte: um módulo com listar(limite, termo) e uma linha aqui


def _obter(model, nome):
    obj = model.query.filter_by(slug=slugify(nome)).first()
    if not obj:
        obj = model(name=nome[:80], slug=slugify(nome))
        db.session.add(obj)
        db.session.flush()
    return obj


def importar_item(fonte, j):
    """Cria um jogo. Devolve (status, jogo) com status 'ok', 'duplicado' ou 'invalido'."""
    if not j.get("title") or not j.get("release_date"):
        return "invalido", None
    existente = Game.query.filter_by(source=fonte, external_id=j["external_id"]).first()
    if existente:
        return "duplicado", existente
    slug = slugify(j["title"]) or j["external_id"]
    if Game.query.filter_by(slug=slug).first():
        slug = f"{slug}-{fonte}-{j['external_id']}"
    game = Game(
        title=j["title"][:150], slug=slug[:170], synopsis=j["synopsis"] or "Sem descrição.",
        release_date=j["release_date"], developer=_obter(Developer, j["developer"] or "Desenvolvedora desconhecida"),
        genres=[_obter(Genre, g) for g in j["genres"]], platforms=[_obter(Platform, p) for p in j["platforms"]],
        source=fonte, external_id=j["external_id"], cover_url=j["cover_url"],
    )
    db.session.add(game)
    return "ok", game


def importar(fonte, limite=40, termo=None, modulo=None):
    """Devolve (importados, ignorados, falhas). `modulo` permite injetar uma fonte falsa nos testes."""
    modulo = modulo or FONTES[fonte]
    ok = ign = erro = 0
    for j in modulo.listar(limite, termo):
        if "erro" in j:
            erro += 1
            continue
        status, _ = importar_item(fonte, j)
        db.session.commit()
        ok, ign = ok + (status == "ok"), ign + (status != "ok")
    return ok, ign, erro
