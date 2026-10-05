"""Fonte `arquivo`: lê o snapshot versionado de jogos reais, sem rede (gerado por `flask export-games`)."""
import json
from datetime import date
from itertools import islice
from pathlib import Path

CAMINHO = Path(__file__).resolve().parent.parent / "dados" / "jogos.json"


def listar(limite, termo=None):
    jogos = json.loads(CAMINHO.read_text(encoding="utf-8"))
    achados = (j for j in jogos if not termo or termo.lower() in j["title"].lower())
    for j in islice(achados, limite):
        yield {**j, "release_date": date.fromisoformat(j["release_date"])}
