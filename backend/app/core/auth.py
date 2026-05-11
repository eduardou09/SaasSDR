"""
Middleware de autenticação e resolução de tenant.

Fluxo por request:
1. Extrai Bearer token do header Authorization
2. Verifica JWT via Clerk JWKS (cache de 5 min)
3. Extrai `sub` (clerk_user_id) e `org_id` (clerk_org_id)
4. Busca tenant no banco por clerk_org_id (cache Redis)
5. Popula request.state.tenant_id, request.state.user_id, request.state.clerk_org_id

Notas:
- Rotas sem org_id ativo (usuário sem organização) recebem 403
- O tenant é auto-criado se não existir (fluxo de first login com nova org do Clerk)
- Tenant lookup usa cache Redis (TTL 60s) para evitar query por request
"""

import logging
import uuid
from typing import Any

import jwt
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from jwt import PyJWKClient
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from app.config import settings
from app.core.db import AsyncSessionLocal

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# JWKS client — valida tokens Clerk com cache automático de chaves públicas
# ---------------------------------------------------------------------------
_jwks_client = PyJWKClient(
    settings.clerk_jwks_url,
    cache_jwk_set=True,
    lifespan=300,  # Cache de 5 minutos
)

# Rotas públicas que não precisam de autenticação
PUBLIC_PATHS = {
    "/health",
    "/api/v1/ping",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
}

PUBLIC_PREFIXES = (
    "/webhooks/",  # Webhooks validam assinatura própria
    "/api/v1/webhooks/",
)


def _is_public(path: str) -> bool:
    if path in PUBLIC_PATHS:
        return True
    return any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)


def _decode_clerk_token(token: str) -> dict[str, Any]:
    """Verifica e decodifica um JWT do Clerk. Levanta HTTPException em caso de falha."""
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},  # Clerk não usa audience por padrão
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Token inválido: {e}")


def _extract_org_id(claims: dict[str, Any]) -> str:
    """Extrai org_id de diferentes formatos possíveis de claims do Clerk."""
    direct = claims.get("org_id") or claims.get("orgId")
    if isinstance(direct, str) and direct:
        return direct

    org_obj = claims.get("org") or claims.get("o")
    if isinstance(org_obj, dict):
        org_id = org_obj.get("id")
        if isinstance(org_id, str) and org_id:
            return org_id

    orgs = claims.get("orgs")
    if isinstance(orgs, list) and len(orgs) == 1 and isinstance(orgs[0], dict):
        org_id = orgs[0].get("id")
        if isinstance(org_id, str) and org_id:
            return org_id

    return ""


async def _resolve_tenant(clerk_org_id: str, org_name: str = "") -> uuid.UUID:
    """
    Busca o tenant pelo clerk_org_id. Cria automaticamente se não existir.
    Em produção, considere usar o webhook do Clerk para criar tenants em vez de auto-criar.
    """
    # Import aqui para evitar circular import
    from app.models.tenant import Tenant

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Tenant).where(Tenant.clerk_org_id == clerk_org_id)
        )
        tenant = result.scalar_one_or_none()

        if tenant is None:
            # Auto-cria o tenant na primeira requisição com essa org
            slug = clerk_org_id.replace("org_", "")[:50]
            tenant = Tenant(
                clerk_org_id=clerk_org_id,
                name=org_name or clerk_org_id,
                slug=slug,
            )
            session.add(tenant)
            await session.commit()
            await session.refresh(tenant)
            logger.info("Novo tenant criado: %s (%s)", tenant.id, clerk_org_id)

        return tenant.id  # type: ignore[return-value]


async def _resolve_user(clerk_user_id: str, email: str = "", name: str = "") -> uuid.UUID:
    """Busca ou cria o usuário pelo clerk_user_id."""
    from app.models.user import User

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.clerk_user_id == clerk_user_id)
        )
        user = result.scalar_one_or_none()

        if user is None:
            user = User(clerk_user_id=clerk_user_id, email=email or clerk_user_id, name=name)
            session.add(user)
            await session.commit()
            await session.refresh(user)

        return user.id  # type: ignore[return-value]


class TenantAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware que autentica o request e popula request.state com contexto de tenant.

    Após execução bem-sucedida, request.state contém:
      - tenant_id: uuid.UUID
      - user_id: uuid.UUID
      - clerk_user_id: str
      - clerk_org_id: str
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Preflight CORS — deixa o CORSMiddleware responder sem auth
        if request.method == "OPTIONS":
            return await call_next(request)

        if _is_public(request.url.path):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Authorization header ausente ou inválido"},
            )

        token = auth_header.removeprefix("Bearer ").strip()

        try:
            claims = _decode_clerk_token(token)
        except HTTPException as e:
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})

        clerk_user_id: str = claims.get("sub", "")
        clerk_org_id: str = _extract_org_id(claims)
        if not clerk_org_id:
            header_org_id = request.headers.get("X-Clerk-Org-Id", "").strip()
            if header_org_id.startswith("org_"):
                clerk_org_id = header_org_id
        org_name: str = claims.get("org_slug", "")

        if not clerk_org_id:
            logger.warning(
                "JWT sem org_id ativa. claims_keys=%s sub=%s path=%s",
                sorted(list(claims.keys())),
                clerk_user_id,
                request.url.path,
            )
            return JSONResponse(
                status_code=403,
                content={
                    "detail": (
                        "Nenhuma organização ativa. "
                        "Selecione uma organização no OrganizationSwitcher "
                        "e recarregue a página."
                    )
                },
            )

        try:
            tenant_id = await _resolve_tenant(clerk_org_id, org_name)
            user_id = await _resolve_user(
                clerk_user_id,
                email=claims.get("email", ""),
                name=claims.get("name", ""),
            )
        except Exception:
            logger.exception("Erro ao resolver tenant/user para org %s", clerk_org_id)
            return JSONResponse(
                status_code=500,
                content={"detail": "Erro interno ao estabelecer contexto de tenant"},
            )

        request.state.tenant_id = tenant_id
        request.state.user_id = user_id
        request.state.clerk_user_id = clerk_user_id
        request.state.clerk_org_id = clerk_org_id

        return await call_next(request)
