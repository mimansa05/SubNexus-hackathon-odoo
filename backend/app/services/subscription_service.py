import calendar
from uuid import UUID
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.subscription import Subscription, SubscriptionEvent
from app.models.customer import Customer
from app.models.plan import Plan
from app.schemas.subscription import SubscriptionCreate


def add_months(value: datetime, months: int):
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])

    return value.replace(year=year, month=month, day=day)


def calculate_period_end(start: datetime, plan: Plan):
    count = plan.interval_count

    if plan.billing_interval == "daily":
        return start + timedelta(days=count)

    if plan.billing_interval == "weekly":
        return start + timedelta(weeks=count)

    if plan.billing_interval == "monthly":
        return add_months(start, count)

    if plan.billing_interval == "yearly":
        return add_months(start, count * 12)

    raise HTTPException(400, "Unsupported billing interval")


def record_event(
    db: Session,
    subscription_id: UUID,
    event_type: str,
    details: dict | None = None
):
    event = SubscriptionEvent(
        subscription_id=subscription_id,
        event_type=event_type,
        details=details
    )

    db.add(event)


def get_subscription(db: Session, subscription_id: UUID):
    subscription = db.get(Subscription, subscription_id)

    if not subscription:
        raise HTTPException(404, "Subscription not found")

    return subscription


def create_subscription(db: Session, data: SubscriptionCreate):
    customer = db.get(Customer, data.customer_id)

    if not customer:
        raise HTTPException(404, "Customer not found")

    plan = db.get(Plan, data.plan_id)

    if not plan:
        raise HTTPException(404, "Plan not found")

    if not plan.is_active:
        raise HTTPException(400, "Plan is inactive")

    now = datetime.now(timezone.utc)

    subscription = Subscription(
        customer_id=data.customer_id,
        plan_id=data.plan_id,
        status="draft",
        current_period_start=now,
        current_period_end=calculate_period_end(now, plan),
        cancel_at_period_end=False
    )

    if data.start_trial:
        if plan.trial_period_days <= 0:
            raise HTTPException(400, "This plan has no trial period")

        subscription.status = "trialing"
        subscription.trial_start = now
        subscription.trial_end = now + timedelta(days=plan.trial_period_days)
        subscription.current_period_end = subscription.trial_end

    db.add(subscription)
    db.flush()

    record_event(
        db,
        subscription.id,
        "created",
        {"status": subscription.status, "plan_id": str(plan.id)}
    )

    db.commit()
    db.refresh(subscription)

    return subscription


def list_subscriptions(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    customer_id: UUID | None = None,
    plan_id: UUID | None = None,
    status: str | None = None
):
    query = select(Subscription)

    if customer_id:
        query = query.where(Subscription.customer_id == customer_id)

    if plan_id:
        query = query.where(Subscription.plan_id == plan_id)

    if status:
        query = query.where(Subscription.status == status)

    query = query.order_by(Subscription.created_at.desc())
    query = query.offset(skip).limit(limit)

    return db.scalars(query).all()


def activate_subscription(db: Session, subscription_id: UUID):
    subscription = get_subscription(db, subscription_id)

    if subscription.status == "trialing":
        if subscription.trial_end and datetime.now(timezone.utc) < subscription.trial_end:
            raise HTTPException(400, "Trial period is still active")

        plan = db.get(Plan, subscription.plan_id)
        subscription.current_period_start = subscription.trial_end
        subscription.current_period_end = calculate_period_end(
            subscription.trial_end, plan
        )

    elif subscription.status != "draft":
        raise HTTPException(400, "Only draft or completed-trial subscriptions can be activated")

    subscription.status = "active"

    record_event(db, subscription.id, "activated")
    db.commit()
    db.refresh(subscription)

    return subscription


def pause_subscription(db: Session, subscription_id: UUID):
    subscription = get_subscription(db, subscription_id)

    if subscription.status != "active":
        raise HTTPException(400, "Only active subscriptions can be paused")

    subscription.status = "paused"

    record_event(db, subscription.id, "paused")
    db.commit()
    db.refresh(subscription)

    return subscription


def resume_subscription(db: Session, subscription_id: UUID):
    subscription = get_subscription(db, subscription_id)

    if subscription.status != "paused":
        raise HTTPException(400, "Only paused subscriptions can be resumed")

    subscription.status = "active"

    record_event(db, subscription.id, "resumed")
    db.commit()
    db.refresh(subscription)

    return subscription


def cancel_subscription(
    db: Session,
    subscription_id: UUID,
    at_period_end: bool = False
):
    subscription = get_subscription(db, subscription_id)

    if subscription.status not in ("active", "trialing", "paused", "draft"):
        raise HTTPException(400, "Subscription cannot be canceled")

    if at_period_end:
        subscription.cancel_at_period_end = True
        event_type = "cancellation_scheduled"
    else:
        subscription.status = "canceled"
        subscription.canceled_at = datetime.now(timezone.utc)
        subscription.cancel_at_period_end = False
        event_type = "canceled"

    record_event(
        db,
        subscription.id,
        event_type,
        {"at_period_end": at_period_end}
    )

    db.commit()
    db.refresh(subscription)

    return subscription


def renew_subscription(db: Session, subscription_id: UUID):
    subscription = get_subscription(db, subscription_id)

    if subscription.status not in ("active", "expired"):
        raise HTTPException(400, "Only active or expired subscriptions can be renewed")

    if subscription.cancel_at_period_end:
        raise HTTPException(400, "Subscription has scheduled cancellation")

    plan = db.get(Plan, subscription.plan_id)

    if not plan or not plan.is_active:
        raise HTTPException(400, "Plan is unavailable")

    now = datetime.now(timezone.utc)

    # Do not renew early: extend from the existing period end.
    start = max(subscription.current_period_end, now)

    subscription.current_period_start = start
    subscription.current_period_end = calculate_period_end(start, plan)
    subscription.status = "active"

    record_event(
        db,
        subscription.id,
        "renewed",
        {"new_period_start": start.isoformat()}
    )

    db.commit()
    db.refresh(subscription)

    return subscription


def get_subscription_events(db: Session, subscription_id: UUID):
    get_subscription(db, subscription_id)

    query = (
        select(SubscriptionEvent)
        .where(SubscriptionEvent.subscription_id == subscription_id)
        .order_by(SubscriptionEvent.created_at.desc())
    )

    return db.scalars(query).all()
