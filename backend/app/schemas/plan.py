from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal

from pydantic import BaseModel, Field, ConfigDict, field_validator

BillingInterval = Literal["daily", "weekly", "monthly", "yearly"]


class PlanCreate(BaseModel):
    product_id: UUID
    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=2, max_length=100)
    description: Optional[str] = None
    price: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    billing_interval: BillingInterval = "monthly"
    interval_count: int = Field(default=1, ge=1, le=120)
    trial_period_days: int = Field(default=0, ge=0, le=3650)
    currency: str = Field(default="USD", min_length=3, max_length=3)

    @field_validator("code", "currency")
    @classmethod
    def normalize_uppercase(cls, value):
        return value.strip().upper()


class PlanUpdate(BaseModel):
    product_id: Optional[UUID] = None
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    code: Optional[str] = Field(default=None, min_length=2, max_length=100)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    billing_interval: Optional[BillingInterval] = None
    interval_count: Optional[int] = Field(default=None, ge=1, le=120)
    trial_period_days: Optional[int] = Field(default=None, ge=0, le=3650)
    currency: Optional[str] = Field(default=None, min_length=3, max_length=3)
    is_active: Optional[bool] = None

    @field_validator("code", "currency")
    @classmethod
    def normalize_uppercase(cls, value):
        return value.strip().upper() if value is not None else value


class PlanResponse(BaseModel):
    id: UUID
    product_id: UUID
    name: str
    code: str
    description: Optional[str]
    price: Decimal
    billing_interval: str
    interval_count: int
    trial_period_days: int
    currency: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
