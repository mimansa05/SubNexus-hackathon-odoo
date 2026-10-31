from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.plan import Plan
from app.models.subscription import Subscription, SubscriptionEvent


CENT = Decimal("0.01")
ZERO = Decimal("0.00")
ACTIVE_STATUSES = ("active", "trialing")
OPEN_INVOICE_STATUSES = ("issued", "overdue", "partially_paid")


def _money(amount: Decimal) -> Decimal:
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def monthly_recurring_amount(
    price: Decimal,
    billing_interval: str,
    interval_count: int,
) -> Decimal:
    """Convert plan pricing to a monthly equivalent without float arithmetic."""
    if interval_count < 1:
        raise ValueError("interval_count must be at least one")
    if billing_interval == "daily":
        monthly_amount = price * Decimal("365") / Decimal("12")
    elif billing_interval == "weekly":
        monthly_amount = price * Decimal("52") / Decimal("12")
    elif billing_interval == "monthly":
        monthly_amount = price
    elif billing_interval == "yearly":
        monthly_amount = price / Decimal("12")
    else:
        raise ValueError(f"Unsupported billing interval: {billing_interval}")
    return _money(monthly_amount / interval_count)


def _utc_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _date_range(
    start_date: Optional[date],
    end_date: Optional[date],
    today: date,
) -> tuple[date, date]:
    end = end_date or today
    start = start_date or end.replace(day=1)
    if start > end:
        raise HTTPException(400, "start_date must be on or before end_date")
    return start, end


def _day_bounds(start: date, end: date) -> tuple[datetime, datetime]:
    return (
        datetime.combine(start, time.min, tzinfo=timezone.utc),
        datetime.combine(end + timedelta(days=1), time.min, tzinfo=timezone.utc),
    )


def _totals_by_currency(
    db: Session,
    amount_column,
    currency_column,
    *conditions,
) -> dict[str, Decimal]:
    rows = db.execute(
        select(currency_column, func.sum(amount_column))
        .where(*conditions)
        .group_by(currency_column)
    )
    return {
        currency: _money(amount or ZERO)
        for currency, amount in rows
    }


def _currency_amounts(totals: dict[str, Decimal]) -> list[dict]:
    return [
        {"currency": currency, "amount": amount}
        for currency, amount in sorted(totals.items())
    ]


def _active_subscriptions(db: Session, as_of: datetime):
    return (
        select(Subscription, Plan)
        .join(Plan, Subscription.plan_id == Plan.id)
        .where(
            Subscription.status == "active",
            Subscription.current_period_start <= as_of,
            Subscription.current_period_end > as_of,
        )
    )


def _mrr_totals(db: Session, as_of: datetime) -> dict[str, Decimal]:
    totals: defaultdict[str, Decimal] = defaultdict(lambda: ZERO)
    for subscription, plan in db.execute(_active_subscriptions(db, as_of)):
        totals[plan.currency.upper()] += monthly_recurring_amount(
            plan.price,
            plan.billing_interval,
            plan.interval_count,
        )
    return {currency: _money(value) for currency, value in totals.items()}


def _collected_totals(
    db: Session,
    start_date: date,
    end_date: date,
) -> dict[str, Decimal]:
    start, end = _day_bounds(start_date, end_date)
    return _totals_by_currency(
        db,
        Payment.amount,
        Payment.currency,
        Payment.status == "succeeded",
        Payment.updated_at >= start,
        Payment.updated_at < end,
    )


def _outstanding_totals(
    db: Session,
    as_of: datetime,
) -> tuple[dict[str, Decimal], dict[str, Decimal], int]:
    rows = db.execute(
        select(
            Invoice.total_amount,
            Invoice.amount_paid,
            Invoice.currency,
            Invoice.due_date,
        ).where(Invoice.status.in_(OPEN_INVOICE_STATUSES))
    )
    outstanding: defaultdict[str, Decimal] = defaultdict(lambda: ZERO)
    overdue: defaultdict[str, Decimal] = defaultdict(lambda: ZERO)
    overdue_count = 0
    for total, paid, currency, due_date in rows:
        balance = max(total - paid, ZERO)
        if balance <= ZERO:
            continue
        currency = currency.upper()
        outstanding[currency] += balance
        if due_date and _utc_datetime(due_date) < as_of:
            overdue[currency] += balance
            overdue_count += 1
    return (
        {currency: _money(amount) for currency, amount in outstanding.items()},
        {currency: _money(amount) for currency, amount in overdue.items()},
        overdue_count,
    )


def _active_count(db: Session, as_of: datetime) -> int:
    return db.scalar(
        select(func.count(Subscription.id)).where(
            Subscription.status.in_(ACTIVE_STATUSES),
            Subscription.current_period_start <= as_of,
            Subscription.current_period_end > as_of,
        )
    ) or 0


def _period_dates(
    period: Literal["month", "quarter", "year"],
    now: datetime,
) -> tuple[datetime, datetime]:
    if period == "month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif period == "quarter":
        quarter_start_month = ((now.month - 1) // 3) * 3 + 1
        start = now.replace(
            month=quarter_start_month,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
    else:
        start = now.replace(
            month=1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
    return start, now


def _event_status(event_type: str, details: Optional[dict]) -> Optional[str]:
    if event_type == "created":
        return (details or {}).get("status", "draft")
    if event_type in ("activated", "resumed", "renewed"):
        return "active"
    if event_type == "paused":
        return "paused"
    if event_type == "canceled":
        return "canceled"
    if event_type == "expired":
        return "expired"
    return None


def _starting_active_subscriptions(db: Session, period_start: datetime) -> int:
    subscriptions = db.scalars(
        select(Subscription).where(Subscription.created_at < period_start)
    ).all()
    if not subscriptions:
        return 0

    events = db.execute(
        select(
            SubscriptionEvent.id,
            SubscriptionEvent.subscription_id,
            SubscriptionEvent.event_type,
            SubscriptionEvent.details,
        )
        .join(Subscription, Subscription.id == SubscriptionEvent.subscription_id)
        .where(
            Subscription.created_at < period_start,
            SubscriptionEvent.created_at < period_start,
            SubscriptionEvent.event_type != "cancellation_scheduled",
        )
        .order_by(SubscriptionEvent.created_at, SubscriptionEvent.id)
    )
    states: dict[UUID, str] = {}
    for _, subscription_id, event_type, details in events:
        state = _event_status(event_type, details)
        if state:
            states[subscription_id] = state

    active_count = 0
    for subscription in subscriptions:
        state = states.get(subscription.id)
        if state is None:
            state = subscription.status
            if (
                state == "canceled"
                and subscription.canceled_at
                and _utc_datetime(subscription.canceled_at) >= period_start
            ):
                state = "trialing" if (
                    subscription.trial_end
                    and _utc_datetime(subscription.trial_end) > period_start
                ) else "active"
        if (
            state in ACTIVE_STATUSES
            and _utc_datetime(subscription.current_period_end) > period_start
        ):
            active_count += 1
    return active_count


def analytics_overview(db: Session) -> dict:
    now = datetime.now(timezone.utc)
    today = now.date()
    start_date = today.replace(day=1)
    mrr = _mrr_totals(db, now)
    outstanding, _, overdue_count = _outstanding_totals(db, now)
    return {
        "as_of": now,
        "period_start": start_date,
        "period_end": today,
        "mrr": _currency_amounts(mrr),
        "arr": _currency_amounts(
            {currency: _money(amount * 12) for currency, amount in mrr.items()}
        ),
        "collected_revenue": _currency_amounts(
            _collected_totals(db, start_date, today)
        ),
        "outstanding_revenue": _currency_amounts(outstanding),
        "active_subscriptions": _active_count(db, now),
        "overdue_invoices": overdue_count,
    }


def revenue_analytics(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> dict:
    today = datetime.now(timezone.utc).date()
    start_date, end_date = _date_range(start_date, end_date, today)
    start, end = _day_bounds(start_date, end_date)
    rows = db.execute(
        select(Payment.updated_at, Payment.amount, Payment.currency).where(
            Payment.status == "succeeded",
            Payment.updated_at >= start,
            Payment.updated_at < end,
        )
    )
    totals: defaultdict[str, Decimal] = defaultdict(lambda: ZERO)
    amounts: defaultdict[str, defaultdict[date, Decimal]] = defaultdict(
        lambda: defaultdict(lambda: ZERO)
    )
    for updated_at, amount, currency in rows:
        currency = currency.upper()
        day = _utc_datetime(updated_at).date()
        totals[currency] += amount
        amounts[currency][day] += amount

    series = []
    day_count = (end_date - start_date).days + 1
    for currency in sorted(totals):
        values = [
            {
                "date": start_date + timedelta(days=offset),
                "amount": _money(amounts[currency][start_date + timedelta(days=offset)]),
            }
            for offset in range(day_count)
        ]
        series.append({
            "currency": currency,
            "total": _money(totals[currency]),
            "values": values,
        })
    return {"start_date": start_date, "end_date": end_date, "series": series}


def recurring_revenue(db: Session, annualized: bool = False) -> dict:
    now = datetime.now(timezone.utc)
    mrr = _mrr_totals(db, now)
    multiplier = 12 if annualized else 1
    return {
        "as_of": now,
        "metric": "arr" if annualized else "mrr",
        "values": _currency_amounts({
            currency: _money(amount * multiplier)
            for currency, amount in mrr.items()
        }),
    }


def churn_analytics(
    db: Session,
    period: Literal["month", "quarter", "year"] = "month",
) -> dict:
    now = datetime.now(timezone.utc)
    period_start, period_end = _period_dates(period, now)
    starting_count = _starting_active_subscriptions(db, period_start)
    canceled_count = db.scalar(
        select(func.count(distinct(SubscriptionEvent.subscription_id)))
        .where(
            SubscriptionEvent.event_type == "canceled",
            SubscriptionEvent.created_at >= period_start,
            SubscriptionEvent.created_at <= period_end,
        )
    ) or 0
    rate = (
        _money(Decimal(canceled_count) * Decimal("100") / Decimal(starting_count))
        if starting_count
        else ZERO
    )
    return {
        "period": period,
        "period_start": period_start,
        "period_end": period_end,
        "definition": (
            "Subscription churn: distinct subscriptions canceled during the calendar "
            "period divided by subscriptions active or trialing at the period start; "
            "paused subscriptions are excluded."
        ),
        "starting_subscriptions": starting_count,
        "canceled_subscriptions": canceled_count,
        "churn_rate_percent": rate,
    }


def subscription_analytics(db: Session) -> dict:
    now = datetime.now(timezone.utc)
    grouped = db.execute(
        select(Subscription.status, func.count(Subscription.id))
        .group_by(Subscription.status)
        .order_by(Subscription.status)
    )
    return {
        "as_of": now,
        "active_count": _active_count(db, now),
        "active_statuses": list(ACTIVE_STATUSES),
        "status_counts": [
            {"status": status, "count": count}
            for status, count in grouped
        ],
    }


def outstanding_analytics(db: Session) -> dict:
    now = datetime.now(timezone.utc)
    outstanding, overdue, overdue_count = _outstanding_totals(db, now)
    return {
        "as_of": now,
        "outstanding_revenue": _currency_amounts(outstanding),
        "overdue_revenue": _currency_amounts(overdue),
        "overdue_invoices": overdue_count,
    }


def top_customers(
    db: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 10,
) -> dict:
    today = datetime.now(timezone.utc).date()
    start_date, end_date = _date_range(start_date, end_date, today)
    start, end = _day_bounds(start_date, end_date)
    rows = db.execute(
        select(
            Customer.id,
            Customer.name,
            Customer.email,
            Payment.currency,
            func.sum(Payment.amount).label("collected_revenue"),
        )
        .join(Payment, Payment.customer_id == Customer.id)
        .where(
            Payment.status == "succeeded",
            Payment.updated_at >= start,
            Payment.updated_at < end,
        )
        .group_by(Customer.id, Customer.name, Customer.email, Payment.currency)
        .order_by(func.sum(Payment.amount).desc())
    )
    ranked = []
    ranks: defaultdict[str, int] = defaultdict(int)
    for customer_id, name, email, currency, amount in rows:
        currency = currency.upper()
        ranks[currency] += 1
        if ranks[currency] > limit:
            continue
        ranked.append({
            "rank": ranks[currency],
            "customer_id": customer_id,
            "name": name,
            "email": email,
            "currency": currency,
            "collected_revenue": _money(amount),
        })
    return {
        "start_date": start_date,
        "end_date": end_date,
        "ranked_by": "collected_revenue",
        "customers": ranked,
    }


def top_plans(db: Session, limit: int = 10) -> dict:
    now = datetime.now(timezone.utc)
    ranked = []
    ranks: defaultdict[str, int] = defaultdict(int)
    for subscription, plan in db.execute(
        _active_subscriptions(db, now).order_by(Plan.currency, Plan.name)
    ):
        currency = plan.currency.upper()
        amount = monthly_recurring_amount(
            plan.price,
            plan.billing_interval,
            plan.interval_count,
        )
        ranked.append((currency, plan, amount))

    totals: defaultdict[tuple[UUID, str], Decimal] = defaultdict(lambda: ZERO)
    plan_data = {}
    for currency, plan, amount in ranked:
        key = (plan.id, currency)
        totals[key] += amount
        plan_data[key] = plan
    ordered = sorted(
        (
            (currency, plan_data[(plan_id, currency)], _money(amount))
            for (plan_id, currency), amount in totals.items()
        ),
        key=lambda item: (item[0], -item[2]),
    )
    plans = []
    for currency, plan, amount in ordered:
        ranks[currency] += 1
        if ranks[currency] > limit:
            continue
        plans.append({
            "rank": ranks[currency],
            "plan_id": plan.id,
            "name": plan.name,
            "currency": currency,
            "monthly_recurring_revenue": amount,
        })
    return {
        "as_of": now,
        "ranked_by": "monthly_recurring_revenue",
        "plans": plans,
    }
