import enum
import uuid

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class TenantPlan(str, enum.Enum):
    trial = "trial"
    starter = "starter"
    growth = "growth"
    scale = "scale"


class TenantStatus(str, enum.Enum):
    active = "active"
    suspended = "suspended"
    cancelled = "cancelled"


class Tenant(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tenants"

    clerk_org_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    plan: Mapped[TenantPlan] = mapped_column(
        Enum(TenantPlan, name="tenantplan"),
        default=TenantPlan.trial,
        nullable=False,
    )
    status: Mapped[TenantStatus] = mapped_column(
        Enum(TenantStatus, name="tenantstatus"),
        default=TenantStatus.active,
        nullable=False,
    )
    trial_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class TenantMember(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "tenant_members"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(
        Enum("owner", "admin", "operator", name="memberrole"),
        default="operator",
        nullable=False,
    )
