from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_admin, require_staff_or_admin
from app.database.db import get_db
from app.models.approval import Approval
from app.models.invoice import Invoice
from app.models.log import AuditLog, Notification
from app.models.payment import Payment
from app.models.quotation import Quotation
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.governance import (
    ApprovalCreate, ApprovalDecision, ApprovalResponse, ApproverPermission, AuditLogResponse,
    NotificationResponse,
)

router = APIRouter(tags=["Approvals, Audit Logs and Notifications"])
TARGET_MODELS = {"quotation": Quotation, "invoice": Invoice, "subscription": Subscription, "payment": Payment}
ACTION_TARGETS = {"exceptional_discount": "quotation", "invoice_cancellation": "invoice", "subscription_closure": "subscription", "refund": "payment", "quotation_review": "quotation"}


@router.patch("/api/v1/admin/users/{user_id}/approver", response_model=dict)
def set_approver(user_id: UUID, data: ApproverPermission, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    user.can_approve = data.can_approve
    db.commit()
    return {"user_id": user.id, "can_approve": user.can_approve}


def _audit(db: Session, user: User, entity: str, entity_id: UUID, action: str, old=None, new=None):
    db.add(AuditLog(user_id=user.id, entity_type=entity, entity_id=entity_id, action=action, old_values=old, new_values=new))


@router.post("/api/v1/approvals/", response_model=ApprovalResponse, status_code=201)
def create_approval(data: ApprovalCreate, db: Session = Depends(get_db), user: User = Depends(require_staff_or_admin)):
    if ACTION_TARGETS[data.action_type] != data.target_entity:
        raise HTTPException(400, "Action type does not match its target entity")
    target = db.get(TARGET_MODELS[data.target_entity], data.target_id)
    if target is None:
        raise HTTPException(404, "Approval target not found")
    row = Approval(action_type=data.action_type, target_entity=data.target_entity, target_id=data.target_id,
                   quotation_id=data.target_id if data.target_entity == "quotation" else None,
                   requested_by_id=user.id, status="pending", reason=data.reason)
    db.add(row)
    db.flush()
    _audit(db, user, "approval", row.id, "created", new={"action_type": row.action_type, "target_entity": row.target_entity, "target_id": str(row.target_id), "status": row.status})
    approvers = db.scalars(select(User).where(User.is_active.is_(True), ((User.role == "admin") | User.can_approve.is_(True)))).all()
    for recipient in approvers:
        db.add(Notification(recipient_id=recipient.id, title="Approval pending", message=f"{data.action_type} requires review.", type="approval_pending", entity_type="approval", entity_id=row.id))
    db.commit()
    db.refresh(row)
    return row


@router.get("/api/v1/approvals/", response_model=list[ApprovalResponse])
def list_approvals(db: Session = Depends(get_db), user: User = Depends(get_current_user), skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    query = select(Approval)
    if user.role != "admin" and not user.can_approve:
        query = query.where(Approval.requested_by_id == user.id)
    elif user.role != "admin":
        query = query.where((Approval.requested_by_id == user.id) | (Approval.status == "pending"))
    return db.scalars(query.order_by(Approval.created_at.desc()).offset(skip).limit(limit)).all()


@router.get("/api/v1/approvals/{approval_id}", response_model=ApprovalResponse)
def get_approval(approval_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.get(Approval, approval_id)
    if row is None:
        raise HTTPException(404, "Approval not found")
    if user.role != "admin" and not user.can_approve and row.requested_by_id != user.id:
        raise HTTPException(403, "You cannot view this approval")
    if user.role != "admin" and user.can_approve and row.status != "pending" and row.requested_by_id != user.id:
        raise HTTPException(403, "You cannot view this approval")
    return row


def _decide(approval_id: UUID, decision: str, payload: ApprovalDecision, db: Session, user: User):
    if user.role != "admin" and not user.can_approve:
        raise HTTPException(403, "Only an admin or authorized approver can decide")
    row = db.scalar(select(Approval).where(Approval.id == approval_id).with_for_update())
    if row is None:
        raise HTTPException(404, "Approval not found")
    if row.status != "pending":
        raise HTTPException(409, "Only pending approvals can be decided")
    if not row.target_entity or row.target_entity not in TARGET_MODELS or not row.target_id or db.get(TARGET_MODELS[row.target_entity], row.target_id) is None:
        raise HTTPException(409, "Approval target is no longer available")
    old = {"status": row.status}
    row.status = decision
    row.approved_by_id = user.id
    row.decided_at = datetime.now(timezone.utc)
    if payload.reason:
        row.reason = payload.reason
    _audit(db, user, "approval", row.id, decision, old=old, new={"status": decision, "reason": payload.reason})
    if row.requested_by_id:
        db.add(Notification(recipient_id=row.requested_by_id, title=f"Approval {decision}", message=f"Your {row.action_type} request was {decision}.", type=f"approval_{decision}", entity_type="approval", entity_id=row.id))
    db.commit()
    db.refresh(row)
    return row


@router.post("/api/v1/approvals/{approval_id}/approve", response_model=ApprovalResponse)
def approve(approval_id: UUID, data: ApprovalDecision = ApprovalDecision(), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return _decide(approval_id, "approved", data, db, user)


@router.post("/api/v1/approvals/{approval_id}/reject", response_model=ApprovalResponse)
def reject(approval_id: UUID, data: ApprovalDecision, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if not data.reason:
        raise HTTPException(422, "A rejection reason is required")
    return _decide(approval_id, "rejected", data, db, user)


@router.get("/api/v1/audit-logs/", response_model=list[AuditLogResponse])
def list_audit_logs(user_id: UUID | None = None, action: str | None = None, entity_type: str | None = None,
                    entity_id: UUID | None = None, from_date: datetime | None = None, to_date: datetime | None = None,
                    skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100),
                    db: Session = Depends(get_db), user: User = Depends(require_staff_or_admin)):
    query = select(AuditLog)
    for value, column in ((user_id, AuditLog.user_id), (action, AuditLog.action), (entity_type, AuditLog.entity_type), (entity_id, AuditLog.entity_id)):
        if value is not None:
            query = query.where(column == value)
    if from_date:
        query = query.where(AuditLog.created_at >= from_date)
    if to_date:
        query = query.where(AuditLog.created_at <= to_date)
    return db.scalars(query.order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)).all()


@router.get("/api/v1/audit-logs/{log_id}", response_model=AuditLogResponse)
def get_audit_log(log_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_staff_or_admin)):
    row = db.get(AuditLog, log_id)
    if row is None:
        raise HTTPException(404, "Audit log not found")
    return row


@router.get("/api/v1/notifications/", response_model=list[NotificationResponse])
def list_notifications(skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.scalars(select(Notification).where(Notification.recipient_id == user.id).order_by(Notification.created_at.desc()).offset(skip).limit(limit)).all()


@router.patch("/api/v1/notifications/{notification_id}/read", response_model=NotificationResponse)
def read_notification(notification_id: UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    row = db.scalar(select(Notification).where(Notification.id == notification_id, Notification.recipient_id == user.id).with_for_update())
    if row is None:
        raise HTTPException(404, "Notification not found")
    row.is_read = True
    db.commit()
    db.refresh(row)
    return row


@router.patch("/api/v1/notifications/read", response_model=dict)
def read_all_notifications(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Notification).where(Notification.recipient_id == user.id, Notification.is_read.is_(False)).with_for_update()).all()
    for row in rows:
        row.is_read = True
    db.commit()
    return {"updated": len(rows)}
