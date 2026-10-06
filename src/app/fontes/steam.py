"""Fonte Steam: API pública da loja, sem chave. Uma fonte nova copia este contrato: listar(limite, termo)."""
import html
import json
import re
import unicodedata
from datetime import date
from urllib.parse import quote
from urllib.request import Request, urlopen

LOJA = "https://store.steampowered.com/api"
MESES = {  # português e inglês, abreviados sem acento (IMP-10)
    "jan": 1, "fev": 2, "feb": 2, "mar": 3, "abr": 4, "apr": 4, "mai": 5, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "aug": 8, "set": 9, "sep": 9, "out": 10, "oct": 10, "nov": 11, "dez": 12, "dec": 12,
}
PLATAFORMAS = {"windows": "Windows", "mac": "macOS", "linux": "Linux"}


VERTICAL = "https://cdn.cloudflare.steamstatic.com/steam/apps/{}/library_600x900.jpg"


def _existe(url):
    """HEAD 200 com content-type de imagem; qualquer falha conta como inexistente (CAP-02)."""
    try:
        with urlopen(Request(url, method="HEAD"), timeout=10) as r:
            return r.status == 200 and r.headers.get("content-type", "").startswith("image")
    except Exception:
        return False


def capa(appid, horizontal):
    """Capa vertical (3:4, combina com os cartões) se existir; senão a horizontal da loja (CAP-01, CAP-02)."""
    url = VERTICAL.format(appid)
    return url if _existe(url) else horizontal


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
        "cover_url": capa(appid, d.get("header_image")),
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
