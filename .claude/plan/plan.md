# Plano de trabalho — GameLog (AP1 / DSAI 2026)

Fontes: enunciado da AP1 (gustavopinto.org/assets/slides/dsai-2026/ap1.html) + `SPEC/2026-10-01-*.md`.
Atualizado: 2026-10-01 15:10.

> ⚠️ **Prazo:** pelo enunciado, o último commit que conta é **01/10 às 18h** e a apresentação é no mesmo dia.
> Se isso vale para nós, sobram **~3h**. Este plano está cortado para caber nisso. Se o prazo for outro,
> o mesmo plano vale — só com mais folga em cada fase.

---

## 0. O que conta na nota (checklist do enunciado)

| Item | Estado | Ação |
|---|---|---|
| URL pública no `README.md` | ❌ | deploy na F4 |
| Specs datadas em `SPEC/` **antes** do código | ✅ 10 specs commitadas | não mexer; ajuste = nova spec datada |
| `src/`, `tests/` | ❌ | F0 |
| `prompts/sessoes/` com export bruto de **todas** as sessões | ❌ | F5 (inclui esta sessão e as anteriores) |
| Ferramentas/modelos no `README.md` | ❌ | F5 |
| Commits com trailers `Agent:` e `Spec:` | ❌ commits até agora não têm | **todo commit daqui pra frente** (seção 4) |
| Saída do `cloc` ≥ 100k linhas | ❌ | ver seção 5 |
| Sem segredos no repo | ✅ por enquanto | `.gitignore` + varredura na F5 |
| As duas pessoas commitando com a própria conta | ⚠️ só Fernanda até agora | Artur commita da conta dele |
| Sem squash/rebase do que já foi pushado | — | só `git pull --no-rebase` / merge |

Apresentação (sem slides): demo do fluxo principal · spec em 1 min · 3 prompts (melhor, pior, que mudou a direção) · métricas (linhas, specs, prompts, sessões, horas).

> "Wishlist" = status **planejado** (LIS-01) — não precisa de feature nova.

---

## 1. Stack (decidido, não rediscutir)

Python + Flask + Jinja2 + SQLite + SQLAlchemy + pytest. Sem build de front, sem serviço externo.
Deploy: **Render** (web service Python, `gunicorn "app:create_app()"`), SQLite efêmero recriado com `flask seed`
no start — o seed é reproduzível (CAT-04), então perder o banco no redeploy não é problema.
Config só por env var: `SECRET_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` (ADM-10).

```
src/app/
  __init__.py      create_app, blueprints, erros 403/404/500
  models.py        TODOS os modelos de uma vez (F0) → elimina dependência entre fases
  util.py          paginate (20/pág), login_required, admin_required, avatar, capa SVG
  seed.py          random.Random(42): 300 jogos, 15 gêneros, 10 plataformas, 40 devs, usuários, avaliações…
  auth.py catalogo.py busca.py jogo.py avaliacoes.py listas.py social.py recomendacoes.py admin.py
  templates/  static/style.css
tests/
  conftest.py  test_<spec>.py   (um teste por critério: CAD-01 … ADM-10, nomeado com o ID)
prompts/sessoes/
```

---

## 2. Divisão da dupla

Atualizado 15:12: a Fernanda não participa desta etapa (já fez as specs). **Artur + Claude Code fazem todo o código**,
em sequência: F0 → cadastro-e-login → catálogo+seed → busca → avaliações → página-do-jogo → listas → social →
recomendações → admin → deploy. Commits saem da conta do Artur; os commits das specs ficam na conta da Fernanda,
o que mostra quem conduziu cada sessão.

A Fernanda precisa só mandar o export das sessões dela (as que geraram as specs) para `prompts/sessoes/`.

---

## 3. Cronograma (time-box)

| Horário | Fase | Quem | Entrega |
|---|---|---|---|
| 15:15–15:50 | **F0 Fundação** | Artur | `create_app`, `models.py` completo, `util.py`, `base.html`, CSS responsivo, `conftest.py`, teste de fumaça. Push. |
| 15:15–15:50 | F0' Infra | Fernanda | `.gitignore` (`.venv/ .env *.db __pycache__/`), `.env.example`, conta Render ligada ao repo, esqueleto do README |
| 15:50–17:10 | **F1–F3 Features** | ambos | cada parte = rotas + templates + testes por AC. Commit por parte. Push a cada parte pronta. |
| 17:10–17:30 | **F4 Integração + deploy** | Artur | fluxo principal ponta a ponta no navegador, `pytest` verde, deploy, URL no README |
| 17:10–17:30 | F4' Admin + seed admin | Fernanda | `flask create-admin` lendo env, testar 403 |
| 17:30–17:50 | **F5 Entrega** | ambos | export das sessões, varredura de segredos, `cloc`, README final, push |
| 17:50–18:00 | buffer | — | **nada novo**. Último push antes das 18:00. |

Corte de escopo se apertar (ordem do que cai primeiro): REC-07 dispensar · LIS-07 reordenar · ADM-09 auditoria
paginada · CAD-04 rate-limit de login · SOC-09 sugestões de usuários. O **fluxo principal** (visão geral, passos 1–9)
não pode cair — é a demo.

### Prioridade dentro de cada parte
1. Caminho do fluxo principal funcionando.
2. Regras de domínio (unicidade, 0–10, soft delete, 403/404).
3. Um teste por AC.
4. Polimento visual.

---

## 4. Padrão de commit (obrigatório)

```bash
git commit -m "feat(avaliacoes): nota 0-10 e edição única por jogo" \
  --trailer "Agent: claude-code/claude-opus-5-5" \
  --trailer "Spec: SPEC/2026-10-01-avaliacoes.md"
```
Trabalho manual: `Agent: none`. Commits pequenos, no mínimo um por spec. Nunca `--amend`/rebase depois de push.

---

## 5. Sobre as 100 mil linhas

Realidade: uma app Flask completa com as 9 partes + testes de todos os ~85 critérios dá na faixa de
**10–20 mil linhas** em `cloc`. 100k em 3h não sai com código que faça sentido.

O que fazer:
- **Não inflar com lixo** (código duplicado, arquivos gerados, dados disfarçados de código). O professor vai abrir o
  repo, e `cloc` já exclui dados/locks/build — encher linguiça custa mais na avaliação do processo do que ganha.
- Volume legítimo que já está no escopo: testes por AC (GLOBAL-08) com casos de borda parametrizados, templates
  completos para cada tela, mensagens de validação por campo (ADM-03), testes de autorização para cada rota.
- **Perguntar ao professor hoje** se a meta de 100k é eliminatória ou proporcional, e reportar o `cloc` real no
  README e na apresentação, explicando a decisão. Transparência aqui é parte do que a disciplina avalia.

---

## 6. F5 — Entrega (passo a passo)

```bash
# 1. sessões (cada um na própria máquina)
mkdir -p prompts/sessoes
for f in ~/.claude/projects/-home-artur-projetos-dsai-ap1-GameLog/*.jsonl; do
  cp "$f" "prompts/sessoes/$(date -r "$f" +%F-%H%M)-claude-code.jsonl"
done
# 2. segredos — tem que voltar vazio
grep -rniE 'api[_-]?key|secret_key\s*=|password\s*=|sk-[a-z0-9]{20}|BEGIN .*PRIVATE' prompts/ src/ tests/
# 3. linhas
sudo apt install -y cloc && cloc src tests --exclude-dir=.venv
```

README final: URL pública · dupla (nome + GitHub) · stack · ferramentas e modelos usados · saída do `cloc` ·
como rodar (`pip install -r requirements.txt && flask --app src/app seed && flask --app src/app run`) · `pytest`.

Para a apresentação, anotar durante o dia: hora de início/fim de cada sessão (métrica "horas"),
e marcar o prompt que funcionou melhor, o que falhou e o que mudou a direção.
