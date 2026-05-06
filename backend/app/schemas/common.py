"""Schemas Pydantic compartilhados entre os módulos."""

import uuid
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class APIModel(BaseModel):
    """Base para todos os schemas de API. Aceita leitura de ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(APIModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool


class HealthResponse(APIModel):
    status: str
    environment: str
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    clerk_user_id: str
    clerk_org_id: str
    timestamp: datetime
