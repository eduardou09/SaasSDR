"""
Configuração do SQLAlchemy async + helpers de sessão com tenant isolation via RLS.

Padrão de uso em rotas:
    @router.get("/items")
    async def list_items(db: TenantDB) -> list[Item]:
        result = await db.execute(select(Item))
        return result.scalars().all()

O tipo `TenantDB` é uma anotação Annotated que injeta uma sessão já configurada
com o `app.current_tenant_id` correto para o RLS do Postgres.
"""

import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verifica conexão antes de usar do pool
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ---------------------------------------------------------------------------
# Dependência base (sem tenant context — para uso interno/admin)
# ---------------------------------------------------------------------------
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


# ---------------------------------------------------------------------------
# Dependência com tenant isolation via RLS
# ---------------------------------------------------------------------------
async def get_tenant_db(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> AsyncGenerator[AsyncSession, None]:
    """
    Injeta uma AsyncSession com o `app.current_tenant_id` setado para RLS.
    Requer que o middleware de auth já tenha populado `request.state.tenant_id`.
    """
    tenant_id: uuid.UUID | None = getattr(request.state, "tenant_id", None)
    if tenant_id is None:
        raise HTTPException(status_code=401, detail="Tenant context not established")

    try:
        await session.begin()
        # Usa set_config dentro da transação para evitar erro de bind param em SET LOCAL.
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, true)"),
            {"tid": str(tenant_id)},
        )
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise


# ---------------------------------------------------------------------------
# Tipo anotado para injeção de dependência limpa nas rotas
# ---------------------------------------------------------------------------
RawDB = Annotated[AsyncSession, Depends(get_db_session)]
TenantDB = Annotated[AsyncSession, Depends(get_tenant_db)]
