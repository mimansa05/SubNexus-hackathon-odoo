from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class OrchestrationRequest(BaseModel):
    request: str = Field(min_length=4, max_length=2000)


class SubscriptionCandidate(BaseModel):
    subscription_id: UUID
    customer_name: str
    customer_email: str
    plan_name: str
    price: Decimal
    currency: str
    expires_at: datetime


class OrchestrationPlanResponse(BaseModel):
    task_id: UUID
    intent: str
    summary: str
    requires_confirmation: bool
    candidates: list[SubscriptionCandidate]
    reconciliation_items: list[dict] = Field(default_factory=list)
    agents: list[str] = Field(default_factory=list)
    steps: list[str] = Field(default_factory=list)


class OrchestrationExecutionResponse(BaseModel):
    task_id: UUID
    status: str
    created_count: int
    skipped_count: int
    invoice_ids: list[UUID]
    message: str
