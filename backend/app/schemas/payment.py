from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class PaymentCreate(BaseModel):
    customer_id: UUID
    invoice_id: UUID
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    payment_method: str = Field(default="bank_transfer", max_length=50)
    gateway: str = Field(default="manual", max_length=50)


class PaymentResponse(BaseModel):
    id: UUID
    customer_id: UUID
    invoice_id: Optional[UUID]
    amount: Decimal
    currency: str
    status: str
    payment_method: str
    gateway: str
    gateway_transaction_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentAttemptResponse(BaseModel):
    id: UUID
    payment_id: UUID
    attempt_number: int
    status: str
    error_code: Optional[str]
    error_message: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RefundCreate(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    reason: Optional[str] = Field(default=None, max_length=255)


class RefundResponse(BaseModel):
    id: UUID
    payment_id: UUID
    amount: Decimal
    currency: str
    reason: Optional[str]
    status: str
    gateway_refund_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
