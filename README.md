# Convo

SaaS multi-tenant de agentes SDR para WhatsApp.

## Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.x async, Alembic, Celery, Redis
- **Frontend**: Next.js 15, TypeScript strict, Tailwind CSS 4, shadcn/ui
- **Banco**: PostgreSQL 16 + pgvector (Neon em prod)
- **Auth**: Clerk (Organizations = tenants)
- **Deploy**: Railway (backend) + Vercel (frontend) + Neon (DB) + Upstash (Redis)

## Setup local (< 10 minutos)

### Pré-requisitos

- Docker + Docker Compose
- Python 3.12 (`uv` será instalado automaticamente)
- Node.js 20+
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

### 1. Clone e configure variáveis

```bash
git clone <repo>
cd convo
cp .env.example .env
# Edite .env com suas chaves do Clerk
```

### 2. Suba os serviços de infraestrutura

```bash
docker compose up -d postgres redis
```

### 3. Backend

```bash
cd backend
uv sync
# Migrations rodam automaticamente no startup via RUN_MIGRATIONS=true
uv run uvicorn app.main:app --reload
```

Ou usando docker compose completo (com hot reload):

```bash
docker compose up
```

### 4. Frontend

```bash
cd frontend
cp .env.local.example .env.local
# Edite .env.local com NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
npm install
npm run dev
```

A aplicação estará em:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Docs (Swagger): http://localhost:8000/docs
- Docs (ReDoc): http://localhost:8000/redoc

### 5. Instalar pre-commit hooks (recomendado)

```bash
pip install pre-commit
pre-commit install
```

## Estrutura

```
convo/
├── backend/          # FastAPI + Celery
├── frontend/         # Next.js 15
├── docker-compose.yml
└── .env.example      # Todas as variáveis documentadas
```

## Migrations

**Dev** (automático no startup):
```bash
RUN_MIGRATIONS=true  # já vem no .env.example
```

**Prod** (CI/CD pipeline):
```bash
cd backend && bash migrate.sh
```

**Criar nova migration**:
```bash
cd backend
uv run alembic revision --autogenerate -m "descrição"
```

## Testes

```bash
cd backend
uv run pytest
```

## Configuração do Clerk

1. Crie uma conta em clerk.com
2. Crie uma Application
3. Habilite **Organizations** em `Configure > Organizations`
4. Em `Configure > JWT Templates`, certifique-se que `org_id`, `org_slug` e `org_role` estão incluídos no token
5. Copie `Publishable Key` e `Secret Key` para o `.env`
6. A JWKS URL é `https://<sua-instância>.clerk.accounts.dev/.well-known/jwks.json`
