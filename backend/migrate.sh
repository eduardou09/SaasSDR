#!/bin/bash
# =============================================================================
# Convo Backend — Script de migração para produção
#
# Use este script no pipeline de CI/CD antes de fazer deploy da nova imagem.
# Nunca sete RUN_MIGRATIONS=true em produção — use este script.
#
# Uso:
#   bash migrate.sh
#   bash migrate.sh --check  (apenas verifica se há migrations pendentes)
# =============================================================================
set -e

echo "==> Convo — Alembic migrations (ENVIRONMENT=${ENVIRONMENT})"

if [ "$1" = "--check" ]; then
    echo "==> Checking pending migrations..."
    uv run alembic check
    echo "==> No pending migrations."
    exit 0
fi

echo "==> Current revision:"
uv run alembic current

echo "==> Running: alembic upgrade head"
uv run alembic upgrade head

echo "==> Migration complete. Current revision:"
uv run alembic current
