import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.invoice import Invoice, InvoiceItem
from app.models.plan import Plan
from app.models.subscription import Subscription


def create_renewal_invoices(db: Session, subscription_ids: list[uuid.UUID]) -> tuple[list[uuid.UUID], int]:
    """Create one draft renewal invoice per eligible subscription, in caller transaction."""
    created: list[uuid.UUID] = []
    skipped = 0
    for subscription_id in subscription_ids:
        subscription = db.scalar(
            select(Subscription).where(Subscription.id == subscription_id).with_for_update()
        )
        if subscription is None or subscription.status not in ("active", "trialing") or subscription.cancel_at_period_end:
            skipped += 1
            continue
        # The subscription + period pair is the natural idempotency key.
        existing = db.scalar(select(Invoice.id).where(
            Invoice.subscription_id == subscription.id,
            Invoice.due_date == subscription.current_period_end,
        ).limit(1))
        if existing:
            skipped += 1
            continue
        plan = db.get(Plan, subscription.plan_id)
        if plan is None or not plan.is_active:
            skipped += 1
            continue
        now = datetime.now(timezone.utc)
        invoice_id = uuid.uuid4()
        amount = Decimal(plan.price)
        invoice = Invoice(
            id=invoice_id,
            invoice_number=f"INV-{now:%Y%m%d}-{uuid.uuid4().hex[:8].upper()}",
            customer_id=subscription.customer_id,
            subscription_id=subscription.id,
            status="draft",
            subtotal=amount,
            discount_amount=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            total_amount=amount,
            amount_paid=Decimal("0.00"),
            currency=plan.currency.upper(),
            due_date=subscription.current_period_end,
            items=[InvoiceItem(
                description=f"Renewal: {plan.name}",
                quantity=1,
                unit_price=amount,
                total_price=amount,
            )],
        )
        db.add(invoice)
        db.flush()
        created.append(invoice.id)
    return created, skipped
