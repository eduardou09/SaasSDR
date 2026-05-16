"""
Convo Backend — FastAPI application entry point.
"""

import logging

import logfire
import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import agents as agents_router
from app.api.v1 import health as health_router
from app.api.v1 import settings as settings_router
from app.api.v1 import webhooks as webhooks_router
from app.config import settings
from app.core.auth import TenantAuthMiddleware

# ---------------------------------------------------------------------------
# Observabilidade
# ---------------------------------------------------------------------------
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=0.1 if settings.is_production else 1.0,
    )

if settings.logfire_token:
    logfire.configure(token=settings.logfire_token, environment=settings.environment)

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Convo API",
    description="API do Convo — SaaS de agentes SDR para WhatsApp",
    version="0.1.0",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# Expõe settings no app.state para acesso em handlers (ex: health endpoint)
app.state.settings = settings

# ---------------------------------------------------------------------------
# Middlewares
# ---------------------------------------------------------------------------
app.add_middleware(TenantAuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"https://.*\.(vercel|railway)\.app|https://.*\.rush4ai\.com",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.logfire_token:
    logfire.instrument_fastapi(app)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(health_router.router, prefix="/api/v1")
app.include_router(agents_router.router, prefix="/api/v1")
app.include_router(settings_router.router, prefix="/api/v1")
app.include_router(webhooks_router.router, prefix="/api/v1")

# ---------------------------------------------------------------------------
# Eventos de lifecycle
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def on_startup() -> None:
    logging.getLogger(__name__).info(
        "Convo backend starting (env=%s)", settings.environment
    )


@app.on_event("shutdown")
async def on_shutdown() -> None:
    from app.core.db import engine

    await engine.dispose()
    logging.getLogger(__name__).info("Convo backend shutdown complete")
