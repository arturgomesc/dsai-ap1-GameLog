#!/usr/bin/env bash
# Sobe o GameLog localmente: ./dev.sh  → http://127.0.0.1:5000  (admin: admin@gamelog.local / admin12345)
# ./dev.sh test  → só roda os testes.  ./dev.sh reset → apaga o banco local e recria o seed.
set -e
cd "$(dirname "$0")"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -r requirements.txt
if [ "$1" = "test" ]; then exec .venv/bin/python -m pytest -q; fi
export DATABASE_URL="${DATABASE_URL:-sqlite:///gamelog-dev.db}"
export ADMIN_EMAIL="${ADMIN_EMAIL:-admin@gamelog.local}" ADMIN_PASSWORD="${ADMIN_PASSWORD:-admin12345}"  # só para dev local
export SECRET_KEY="${SECRET_KEY:-dev-local-key}"
cd src
[ "$1" = "reset" ] && rm -f instance/gamelog-dev.db

../.venv/bin/flask --app app seed
../.venv/bin/flask --app app import-games --limite 40 || true  # jogos reais da Steam; sem rede, segue sem eles
exec ../.venv/bin/flask --app app run --debug
