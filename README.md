# GameLog — AP1 DSAI 2026

Catálogo de jogos com avaliações, listas/status (wishlist = "planejado"), feed social, recomendações e painel de moderação.
Desenvolvido com **Spec-Driven Development**: cada parte tem uma spec datada em [`SPEC/`](SPEC/), commitada antes do código.

- **URL pública:** https://gamelog-r41f.onrender.com
- **Equipe:** Artur ([@arturgomesc](https://github.com/arturgomesc)) — implementação · Fernanda Borges ([@fenalk](https://github.com/fenalk)) — specs
- **Stack:** Python 3.12+, Flask 3, Flask-SQLAlchemy (SQLite), Jinja2, pytest, gunicorn. Sem JS de build, sem serviços externos.
- **Ferramentas/modelos de IA:** Claude Code — Opus 5.5 (planejamento) e Sonnet 5.5 (implementação). Sessões brutas em [`prompts/sessoes/`](prompts/sessoes/).

## Como rodar

Atalho: `./dev.sh` (cria venv, instala, faz seed e sobe em http://127.0.0.1:5000; admin `admin@gamelog.local` / `admin12345`, só local). `./dev.sh test` roda os testes; `./dev.sh reset` recria o banco.

Manual:

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cd src
export ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=<senha>   # ver .env.example
flask --app app seed        # 139 jogos reais (snapshot da Steam), 30 usuários fictícios com avaliações em ~30 jogos (senha: senha1234)
flask --app app run
cd .. && pytest             # 123 testes, um ou mais por critério de aceitação
```

O catálogo vem de `src/app/dados/jogos.json` (gerado com `flask --app app export-games --termos "Nome 1;Nome 2" --saida src/app/dados/jogos.json`). Pelo painel, o admin busca e importa jogos em `/admin/importar`. Pela linha de comando: `flask --app app import-games [--fonte steam] [--limite 40] [--termo nome]` (API pública da Steam, sem chave). Para somar outra fonte (RAWG, IGDB), crie `src/app/fontes/<nome>.py` com `listar(limite, termo)` e registre em `FONTES`. Em banco local antigo, rode `./dev.sh reset` (o Game ganhou colunas).

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
| importacao-steam (IMP-01..09) | `fontes/`, `cli.py` | `tests/test_importacao.py` |
| perfil-rico (PRF-01..09) | `perfil.py`, `auth.py`, `templates/auth/perfil.html` | `tests/test_perfil.py` |
| importar-pelo-admin (IAD-01..09) | `admin.py`, `fontes/steam.py`, `templates/admin/importar.html` | `tests/test_importar_admin.py` |
| catalogo-real (CRE-01..09) | `seed.py`, `fontes/arquivo.py`, `dados/jogos.json` | `tests/test_catalogo_real.py` |

## cloc

```
$ cloc . --vcs=git --exclude-dir=node_modules,vendor,dist,build,prompts --exclude-lang=Markdown,JSON,YAML,CSV,Text,SVG --not-match-f='(lock|\.min\.)'
Language        files   blank   comment   code
Python           34     680        41   2791
HTML             24       5         0    528
CSS               1       0         0     42
Bourne Shell      1       1         2     13
INI               1       0         0      3
SUM:             61     686        43   3377
```

**Nota sobre a meta de 100 mil linhas:** o escopo das 14 specs (≈125 critérios de aceitação) resulta em ~3 mil linhas de
código real. Preferimos entregar a aplicação completa e testada a inflar o número com código duplicado ou gerado;
o valor medido está reportado acima sem ajuste.
