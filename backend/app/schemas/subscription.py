from uuid import UUID
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field, ConfigDict


SubscriptionStatus = Literal[
    "draft", "trialing", "active", "paused",
    "canceled", "expired"
]


class SubscriptionCreate(BaseModel):
    customer_id: UUID
    plan_id: UUID
    start_trial: bool = False


class SubscriptionResponse(BaseModel):
    id: UUID
    customer_id: UUID
    plan_id: UUID
    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    canceled_at: Optional[datetime]
    trial_start: Optional[datetime]
    trial_end: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubscriptionEventResponse(BaseModel):
    id: UUID
    subscription_id: UUID
    event_type: str
    details: Optional[dict]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
