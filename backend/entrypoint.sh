#!/bin/bash
# =============================================================================
# Convo Backend — Entrypoint
#
# RUN_MIGRATIONS=true  → roda alembic upgrade head antes de subir o server
# RUN_MIGRATIONS=false → pula migrations (use migrate.sh no CI/CD de prod)
#
# Argumentos extras passados ao uvicorn (ex: --reload --log-level debug)
# =============================================================================
set -e

echo "==> Convo Backend starting (ENVIRONMENT=${ENVIRONMENT:-development})"

if [ "${RUN_MIGRATIONS}" = "true" ]; then
    echo "==> Running Alembic migrations..."
    uv run alembic upgrade head
    echo "==> Migrations complete."
fi

echo "==> Starting Uvicorn..."
exec uv run uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    "$@"
