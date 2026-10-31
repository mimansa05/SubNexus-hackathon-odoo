from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class InvoiceItemCreate(BaseModel):
    product_id: Optional[UUID] = None
    description: str = Field(min_length=2, max_length=500)
    quantity: int = Field(default=1, ge=1)
    unit_price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class InvoiceCreate(BaseModel):
    customer_id: UUID
    subscription_id: Optional[UUID] = None
    items: list[InvoiceItemCreate] = Field(min_length=1)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    due_date: Optional[datetime] = None


class InvoiceItemResponse(BaseModel):
    id: UUID
    invoice_id: UUID
    product_id: Optional[UUID]
    description: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal

    model_config = ConfigDict(from_attributes=True)


class InvoiceResponse(BaseModel):
    id: UUID
    invoice_number: str
    customer_id: UUID
    subscription_id: Optional[UUID]
    status: str
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    amount_paid: Decimal
    currency: str
    due_date: Optional[datetime]
    paid_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    items: list[InvoiceItemResponse]

    model_config = ConfigDict(from_attributes=True)
