from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.plan import Plan
from app.models.subscription import Subscription


def find_expiring_subscriptions(db: Session, days: int) -> list[Subscription]:
    """Return active subscriptions whose current period ends within the window."""
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(days=days)
    return db.scalars(
        select(Subscription)
        .where(
            Subscription.status.in_(("active", "trialing")),
            Subscription.current_period_end >= now,
            Subscription.current_period_end <= cutoff,
            Subscription.cancel_at_period_end.is_(False),
        )
        .order_by(Subscription.current_period_end.asc())
    ).all()


def subscription_context(db: Session, subscription: Subscription) -> dict:
    customer = db.get(Customer, subscription.customer_id)
    plan = db.get(Plan, subscription.plan_id)
    return {
        "subscription_id": str(subscription.id),
        "customer_name": customer.name if customer else "Unknown customer",
        "customer_email": customer.email if customer else "",
        "plan_name": plan.name if plan else "Unknown plan",
        "price": str(plan.price) if plan else "0.00",
        "currency": plan.currency if plan else "INR",
        "expires_at": subscription.current_period_end.isoformat(),
    }
