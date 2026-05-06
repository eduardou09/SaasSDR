# =============================================================================
# Convo Backend — Dockerfile multi-stage
#
# Stages:
#   base        → Python + uv instalados
#   development → deps + código, hot reload via volume mount
#   production  → imagem final enxuta, sem dev deps
# =============================================================================

FROM python:3.12-slim AS base

# Instala uv (gerenciador de pacotes)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Dependências de sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# =============================================================================
FROM base AS development

# Copia manifesto e instala deps (incluindo dev) com cache de camada
COPY pyproject.toml ./
RUN uv sync --no-install-project

# Código copiado por último para aproveitar cache de deps
# Em dev, este COPY é sobrescrito pelo volume mount do docker-compose
COPY . .

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]

# =============================================================================
FROM base AS production

# Instala apenas deps de produção (sem dev deps)
COPY pyproject.toml ./
RUN uv sync --no-install-project --no-dev

COPY . .

COPY entrypoint.sh /entrypoint.sh
COPY migrate.sh /migrate.sh
RUN chmod +x /entrypoint.sh /migrate.sh

# Em prod, RUN_MIGRATIONS deve ser false — use migrate.sh no pipeline
ENV RUN_MIGRATIONS=false
ENV ENVIRONMENT=production

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
