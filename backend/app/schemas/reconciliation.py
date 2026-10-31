from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ReconciliationTransactionResponse(BaseModel):
    id: UUID
    transaction_date: datetime
    amount: Decimal
    currency: str
    bank_reference: Optional[str]
    transaction_id: Optional[str]
    customer_email: Optional[str]
    description: Optional[str]
    status: str
    match_notes: Optional[str]
    customer_id: Optional[UUID]
    payment_id: Optional[UUID]
    invoice_id: Optional[UUID]
    duplicate_of_id: Optional[UUID]
    confirmed_by_id: Optional[UUID]
    confirmed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvalidReconciliationRow(BaseModel):
    row_number: int
    error: str


class ReconciliationImportResponse(BaseModel):
    imported_count: int
    duplicate_count: int
    invalid_count: int
    transactions: list[ReconciliationTransactionResponse]
    errors: list[InvalidReconciliationRow]


class ReconciliationMatchRequest(BaseModel):
    transaction_id: UUID
    payment_id: Optional[UUID] = None
    invoice_id: Optional[UUID] = None

    @model_validator(mode="after")
    def require_single_target(self):
        if (self.payment_id is None) == (self.invoice_id is None):
            raise ValueError("Provide exactly one of payment_id or invoice_id")
        return self


class ReconciliationListResponse(BaseModel):
    items: list[ReconciliationTransactionResponse]
    skip: int
    limit: int
