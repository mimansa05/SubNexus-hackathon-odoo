from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class QuotationItemCreate(BaseModel):
    product_id: Optional[UUID] = None
    description: str = Field(min_length=2, max_length=500)
    quantity: int = Field(default=1, ge=1, le=100000)
    unit_price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    discount_percent: Decimal = Field(
        default=Decimal("0.00"), ge=0, le=100,
        max_digits=5, decimal_places=2
    )


class QuotationCreate(BaseModel):
    customer_id: UUID
    items: list[QuotationItemCreate] = Field(min_length=1)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    tax_percent: Decimal = Field(
        default=Decimal("0.00"), ge=0, le=100,
        max_digits=5, decimal_places=2
    )
    valid_until: Optional[datetime] = None
    notes: Optional[str] = None


class QuotationItemResponse(BaseModel):
    id: UUID
    quotation_id: UUID
    product_id: Optional[UUID]
    description: str
    quantity: int
    unit_price: Decimal
    discount_percent: Decimal
    total_price: Decimal

    model_config = ConfigDict(from_attributes=True)


class QuotationResponse(BaseModel):
    id: UUID
    quotation_number: str
    customer_id: UUID
    created_by_user_id: Optional[UUID]
    status: str
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str
    valid_until: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    items: list[QuotationItemResponse]

    model_config = ConfigDict(from_attributes=True)
