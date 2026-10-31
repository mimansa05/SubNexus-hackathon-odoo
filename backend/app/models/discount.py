import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.db import Base

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.invoice import Invoice


class Discount(Base):
    __tablename__ = "discounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    discount_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    value: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )
    max_uses: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )
    used_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    starts_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
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
    usages: Mapped[List["DiscountUsage"]] = relationship(
        "DiscountUsage",
        back_populates="discount",
        cascade="all, delete-orphan",
    )


class DiscountUsage(Base):
    __tablename__ = "discount_usages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    discount_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("discounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    invoice_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("invoices.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    discount: Mapped["Discount"] = relationship(
        "Discount",
        back_populates="usages",
    )
    customer: Mapped["Customer"] = relationship(
        "Customer",
        back_populates="discount_usages",
    )
    invoice: Mapped[Optional["Invoice"]] = relationship(
        "Invoice",
        back_populates="discount_usages",
    )
