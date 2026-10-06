"""Fonte Steam: API pública da loja, sem chave. Uma fonte nova copia este contrato: listar(limite, termo)."""
import html
import json
import re
import unicodedata
from datetime import date
from urllib.parse import quote
from urllib.request import urlopen

LOJA = "https://store.steampowered.com/api"
MESES = {m: i for i, m in enumerate("jan feb fev mar apr abr may mai jun jul aug ago sep set oct out nov dec dez".split(), 1)}
MESES.update(feb=2, fev=2, apr=4, abr=4, may=5, mai=5, aug=8, ago=8, sep=9, set=9, oct=10, out=10, dec=12, dez=12)
PLATAFORMAS = {"windows": "Windows", "mac": "macOS", "linux": "Linux"}


def _get(path):
    with urlopen(f"{LOJA}/{path}", timeout=15) as r:
        return json.load(r)


def parse_data(texto):
    """'24/fev./2022', '12 Oct, 2020' ou 'Oct 12, 2020' -> date; None se não der."""
    t = unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().lower()
    ano, mes = re.search(r"\b(\d{4})\b", t), re.search(r"[a-z]{3}", t)
    dia = re.search(r"\b(\d{1,2})\b", t)
    if not (ano and mes and dia and mes.group() in MESES):
        return None
    try:
        return date(int(ano.group(1)), MESES[mes.group()], int(dia.group(1)))
    except ValueError:
        return None


def _ids(limite, termo):
    if termo:
        itens = _get(f"storesearch/?term={quote(termo)}&cc=br&l=brazilian")["items"]
    else:
        cats = _get("featuredcategories?cc=br&l=brazilian")
        itens = [i for c in ("top_sellers", "new_releases", "specials") for i in cats.get(c, {}).get("items", [])]
    return list(dict.fromkeys(i["id"] for i in itens))[:limite]


def _jogo(appid):
    bloco = _get(f"appdetails?appids={appid}&cc=br&l=brazilian")[str(appid)]
    d = bloco.get("data") if bloco.get("success") else None
    if not d or d.get("type") != "game":
        return None
    return {
        "external_id": str(appid),
        "title": d["name"],
        "synopsis": html.unescape(d.get("short_description") or ""),
        "release_date": parse_data(d.get("release_date", {}).get("date")),
        "developer": (d.get("developers") or [""])[0],
        "genres": [g["description"] for g in d.get("genres", [])],
        "platforms": [n for k, n in PLATAFORMAS.items() if d.get("platforms", {}).get(k)],
        "cover_url": d.get("header_image"),
    }


def buscar(termo, limite=10):
    """Candidatos para a tela do admin: só o básico, sem custo de um appdetails por item."""
    itens = _get(f"storesearch/?term={quote(termo)}&cc=br&l=brazilian")["items"][:limite]
    return [{"external_id": str(i["id"]), "title": i["name"], "cover_url": i.get("tiny_image")} for i in itens]


def detalhe(external_id):
    return _jogo(int(external_id))


def listar(limite, termo=None):
    """Itens com falha viram {'erro': ...} para o importador contar, sem abortar (IMP-05)."""
    for appid in _ids(limite, termo):
        try:
            j = _jogo(appid)
        except Exception as e:  # rede, JSON, chave ausente: o item é pulado
            yield {"erro": f"{appid}: {e}"}
            continue
        if j:
            yield j
