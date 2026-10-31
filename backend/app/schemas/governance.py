from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class ApprovalCreate(BaseModel):
    action_type: str = Field(pattern="^(exceptional_discount|invoice_cancellation|subscription_closure|refund|quotation_review)$")
    target_entity: str = Field(pattern="^(quotation|invoice|subscription|payment)$")
    target_id: UUID
    reason: str = Field(min_length=1, max_length=2000)


class ApprovalDecision(BaseModel):
    reason: str | None = Field(default=None, max_length=2000)


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    action_type: str
    target_entity: str
    target_id: UUID | None
    requested_by_id: UUID | None
    approved_by_id: UUID | None
    status: str
    reason: str | None
    decided_at: datetime | None
    created_at: datetime


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    user_id: UUID | None
    customer_id: UUID | None
    entity_type: str
    entity_id: UUID
    action: str
    old_values: dict | None
    new_values: dict | None
    ip_address: str | None
    created_at: datetime


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    recipient_id: UUID
    title: str
    message: str
    type: str
    entity_type: str | None
    entity_id: UUID | None
    is_read: bool
    created_at: datetime


class ApproverPermission(BaseModel):
    can_approve: bool
