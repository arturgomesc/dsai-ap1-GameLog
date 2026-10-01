# GameLog — AP1 DSAI 2026

Catálogo de jogos com avaliações, listas/status (wishlist = "planejado"), feed social, recomendações e painel de moderação.
Desenvolvido com **Spec-Driven Development**: cada parte tem uma spec datada em [`SPEC/`](SPEC/), commitada antes do código.

- **URL pública:** _preencher após o deploy no Render_
- **Equipe:** Artur ([@arturgomesc](https://github.com/arturgomesc)) — implementação · Fernanda Borges ([@fenalk](https://github.com/fenalk)) — specs
- **Stack:** Python 3.12+, Flask 3, Flask-SQLAlchemy (SQLite), Jinja2, pytest, gunicorn. Sem JS de build, sem serviços externos.
- **Ferramentas/modelos de IA:** Claude Code — Opus 5.5 (planejamento) e Sonnet 5.5 (implementação). Sessões brutas em [`prompts/sessoes/`](prompts/sessoes/).

## Como rodar

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cd src
export ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=<senha>   # ver .env.example
flask --app app seed        # 300 jogos, 15 gêneros, 10 plataformas, 40 devs, 30 usuários (senha dos fictícios: senha1234)
flask --app app run
cd .. && pytest             # 91 testes, um ou mais por critério de aceitação
```

Deploy: `render.yaml` (Render, plano gratuito; o seed reproduzível recria o banco a cada start).
Variáveis: `SECRET_KEY` (gerada), `ADMIN_EMAIL`, `ADMIN_PASSWORD`.

## Specs → código → testes

| Spec | Código | Testes |
|---|---|---|
| cadastro-e-login (CAD-01..10) | `src/app/auth.py` | `tests/test_auth.py` |
| catalogo (CAT-01..09) | `models.py`, `seed.py`, `catalogo.py` | `tests/test_catalogo.py` |
| busca-e-filtros (BUS-01..09) | `busca.py` | `tests/test_busca.py` |
| pagina-do-jogo (PAG-01..10) | `jogo.py` | `tests/test_jogo.py` |
| avaliacoes (AVA-01..11) | `avaliacoes.py` | `tests/test_avaliacoes.py` |
| listas (LIS-01..11) | `listas.py` | `tests/test_listas.py` |
| social (SOC-01..10) | `social.py` | `tests/test_social.py` |
| recomendacoes (REC-01..09) | `recomendacoes.py` | `tests/test_recomendacoes.py` |
| painel-admin (ADM-01..10) | `admin.py` | `tests/test_admin.py` |

## cloc

```
$ cloc src tests
Python  26 files   code 2218
HTML    23 files   code  486
CSS      1 file    code   42
SUM:                     2751  (+ ~540 blank, 28 comment)
```

**Nota sobre a meta de 100 mil linhas:** o escopo das 10 specs (≈85 critérios de aceitação) resulta em ~2,7 mil linhas de
código real. Preferimos entregar a aplicação completa e testada a inflar o número com código duplicado ou gerado;
o valor medido está reportado acima sem ajuste.
