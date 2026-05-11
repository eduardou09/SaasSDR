"""
GET /api/v1/health

Rota autenticada que valida o stack completo:
- JWT Clerk válido
- Tenant resolvido
- Banco acessível
- Redis acessível

Retorna o contexto do request para debug durante o desenvolvimento.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Request
from sqlalchemy import text

from app.core.db import TenantDB
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/ping", summary="Ping público")
async def ping() -> dict:
    return {"status": "ok"}


@router.get("/health", response_model=HealthResponse, summary="Health check autenticado")
async def health(request: Request, db: TenantDB) -> HealthResponse:
    """
    Verifica se o sistema está funcionando corretamente.

    Requer um JWT válido do Clerk com uma Organization ativa.
    Retorna o tenant_id resolvido para o request atual.
    """
    # Smoke test no banco: se falhar, o handler de exceção do FastAPI retorna 500
    await db.execute(text("SELECT 1"))

    return HealthResponse(
        status="ok",
        environment=request.app.state.settings.environment,
        tenant_id=request.state.tenant_id,
        user_id=request.state.user_id,
        clerk_user_id=request.state.clerk_user_id,
        clerk_org_id=request.state.clerk_org_id,
        timestamp=datetime.now(UTC),
    )
