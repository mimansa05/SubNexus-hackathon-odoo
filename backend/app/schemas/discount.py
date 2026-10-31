from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class DiscountCreate(BaseModel):
    code: str = Field(min_length=3, max_length=50)
    discount_type: str = Field(pattern="^(percentage|fixed)$")
    value: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    max_uses: Optional[int] = Field(default=None, ge=1)
    starts_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class DiscountResponse(BaseModel):
    id: UUID
    code: str
    discount_type: str
    value: Decimal
    max_uses: Optional[int]
    used_count: int
    starts_at: Optional[datetime]
    expires_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DiscountValidationRequest(BaseModel):
    code: str = Field(min_length=3, max_length=50)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)


class DiscountValidationResponse(BaseModel):
    valid: bool
    code: str
    discount_type: str
    original_amount: Decimal
    discount_amount: Decimal
    final_amount: Decimal
    message: str
