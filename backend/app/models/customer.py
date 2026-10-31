import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.db import Base

if TYPE_CHECKING:
    from app.models.discount import DiscountUsage
    from app.models.invoice import Invoice
    from app.models.log import AuditLog
    from app.models.payment import Payment
    from app.models.quotation import Quotation
    from app.models.subscription import Subscription


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        index=True,
        nullable=False,
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    company_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    billing_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    tax_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
    )
    custom_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    subscriptions: Mapped[List["Subscription"]] = relationship(
        "Subscription",
        back_populates="customer",
        cascade="all, delete-orphan",
    )
    quotations: Mapped[List["Quotation"]] = relationship(
        "Quotation",
        back_populates="customer",
    )
    invoices: Mapped[List["Invoice"]] = relationship(
        "Invoice",
        back_populates="customer",
    )
    payments: Mapped[List["Payment"]] = relationship(
        "Payment",
        back_populates="customer",
    )
    discount_usages: Mapped[List["DiscountUsage"]] = relationship(
        "DiscountUsage",
        back_populates="customer",
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="customer",
    )
