import json
from pathlib import Path

from app.fontes import steam

HORIZ = "https://x/header.jpg"
SNAPSHOT = Path(__file__).parent.parent / "src" / "app" / "dados" / "jogos.json"


class Resp:
    def __init__(self, status=200, tipo="image/jpeg"):
        self.status, self.headers = status, {"content-type": tipo}

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


def test_cap01_usa_a_vertical_quando_existe(monkeypatch):
    pedidos = []
    monkeypatch.setattr(steam, "urlopen", lambda req, timeout: pedidos.append(req) or Resp())
    assert steam.capa(42, HORIZ) == "https://cdn.cloudflare.steamstatic.com/steam/apps/42/library_600x900.jpg"
    assert pedidos[0].get_method() == "HEAD"


def test_cap02_cai_para_a_horizontal(monkeypatch):
    for resp in (lambda r, timeout: Resp(404), lambda r, timeout: Resp(200, "text/html")):
        monkeypatch.setattr(steam, "urlopen", resp)
        assert steam.capa(42, HORIZ) == HORIZ

    def cai(req, timeout):
        raise OSError("sem rede")
    monkeypatch.setattr(steam, "urlopen", cai)
    assert steam.capa(42, HORIZ) == HORIZ


def test_cap02_item_do_jogo_nao_aborta_sem_a_vertical(monkeypatch):
    monkeypatch.setattr(steam, "_get", lambda p: {"7": {"success": True, "data": {
        "type": "game", "name": "Jogo", "short_description": "s", "release_date": {"date": "24/fev./2022"},
        "developers": ["Dev"], "genres": [], "platforms": {}, "header_image": HORIZ}}})
    monkeypatch.setattr(steam, "urlopen", lambda r, timeout: Resp(404))
    assert steam._jogo(7)["cover_url"] == HORIZ


def test_cap03_cap04_snapshot_usa_vertical_ou_header():
    jogos = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    verticais = [j for j in jogos if j["cover_url"].endswith("library_600x900.jpg")]
    assert len(verticais) >= len(jogos) * 0.9
    assert all(j["cover_url"].startswith("https://") for j in jogos)
    assert all(j["external_id"] in j["cover_url"] for j in verticais)


def test_cap05_css_cartao_preenche_e_pagina_do_jogo_nao_corta():
    css = (Path(__file__).parent.parent / "src" / "app" / "static" / "style.css").read_text()
    assert "aspect-ratio:3/4;object-fit:cover" in css.replace(" ", "")
    hero = [l for l in css.splitlines() if ".hero img.cover" in l][0]
    assert "aspect-ratio" not in hero and "object-fit:cover" not in hero.replace(" ", "")
