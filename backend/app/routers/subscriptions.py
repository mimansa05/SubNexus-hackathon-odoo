from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.core.dependencies import require_staff_or_admin

from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionEventResponse
)

from app.services.subscription_service import (
    create_subscription,
    list_subscriptions,
    get_subscription,
    activate_subscription,
    pause_subscription,
    resume_subscription,
    cancel_subscription,
    renew_subscription,
    get_subscription_events
)


router = APIRouter(
    prefix="/api/v1/subscriptions",
    tags=["Subscriptions"]
)


@router.post(
    "/",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED
)
def create(
    data: SubscriptionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return create_subscription(db, data)


@router.get("/", response_model=list[SubscriptionResponse])
def list_all(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    customer_id: UUID | None = None,
    plan_id: UUID | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return list_subscriptions(
        db, skip, limit, customer_id, plan_id, status
    )


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
def get_one(
    subscription_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return get_subscription(db, subscription_id)


@router.get(
    "/{subscription_id}/events",
    response_model=list[SubscriptionEventResponse]
)
def get_events(
    subscription_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return get_subscription_events(db, subscription_id)


@router.post(
    "/{subscription_id}/activate",
    response_model=SubscriptionResponse
)
def activate(
    subscription_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return activate_subscription(db, subscription_id)


@router.post(
    "/{subscription_id}/pause",
    response_model=SubscriptionResponse
)
def pause(
    subscription_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return pause_subscription(db, subscription_id)


@router.post(
    "/{subscription_id}/resume",
    response_model=SubscriptionResponse
)
def resume(
    subscription_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return resume_subscription(db, subscription_id)


@router.post(
    "/{subscription_id}/cancel",
    response_model=SubscriptionResponse
)
def cancel(
    subscription_id: UUID,
    at_period_end: bool = False,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return cancel_subscription(
        db, subscription_id, at_period_end
    )


@router.post(
    "/{subscription_id}/renew",
    response_model=SubscriptionResponse
)
def renew(
    subscription_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return renew_subscription(db, subscription_id)
