import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.invoice import Invoice, InvoiceItem
from app.models.customer import Customer
from app.models.product import Product
from app.models.subscription import Subscription
from app.schemas.invoice import InvoiceCreate


CENT = Decimal("0.01")


def money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def get_invoice(db: Session, invoice_id):
    invoice = db.scalar(
        select(Invoice)
        .options(selectinload(Invoice.items))
        .where(Invoice.id == invoice_id)
    )
    if not invoice:
        raise HTTPException(404, "Invoice not found")
    return invoice


def create_invoice(db: Session, data: InvoiceCreate):
    if not db.get(Customer, data.customer_id):
        raise HTTPException(404, "Customer not found")

    if data.subscription_id:
        subscription = db.get(Subscription, data.subscription_id)
        if not subscription:
            raise HTTPException(404, "Subscription not found")
        if subscription.customer_id != data.customer_id:
            raise HTTPException(400, "Subscription does not belong to customer")

    subtotal = Decimal("0.00")
    items = []

    for item in data.items:
        if item.product_id:
            product = db.get(Product, item.product_id)
            if not product or not product.is_active:
                raise HTTPException(404, "Active product not found")

        line_total = money(item.unit_price * item.quantity)
        subtotal += line_total

        items.append(InvoiceItem(
            product_id=item.product_id,
            description=item.description,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=line_total
        ))

    subtotal = money(subtotal)
    if data.discount_amount > subtotal:
        raise HTTPException(400, "Discount cannot exceed subtotal")

    taxable = subtotal - data.discount_amount
    tax = money(taxable * data.tax_percent / Decimal("100"))
    total = money(taxable + tax)

    now = datetime.now(timezone.utc)
    if data.due_date and data.due_date <= now:
        raise HTTPException(400, "Due date must be in the future")

    invoice = Invoice(
        invoice_number=f"INV-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}",
        customer_id=data.customer_id,
        subscription_id=data.subscription_id,
        status="draft",
        subtotal=subtotal,
        discount_amount=money(data.discount_amount),
        tax_amount=tax,
        total_amount=total,
        amount_paid=Decimal("0.00"),
        currency=data.currency.upper(),
        due_date=data.due_date,
        items=items
    )

    db.add(invoice)
    db.commit()
    return get_invoice(db, invoice.id)


def list_invoices(db, skip=0, limit=20, customer_id=None, status=None):
    query = select(Invoice).options(selectinload(Invoice.items))
    if customer_id:
        query = query.where(Invoice.customer_id == customer_id)
    if status:
        query = query.where(Invoice.status == status)

    query = query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit)
    return db.scalars(query).unique().all()


def issue_invoice(db, invoice_id):
    invoice = get_invoice(db, invoice_id)
    if invoice.status != "draft":
        raise HTTPException(400, "Only draft invoices can be issued")

    invoice.status = "issued"
    db.commit()
    return get_invoice(db, invoice_id)


def cancel_invoice(db, invoice_id):
    invoice = get_invoice(db, invoice_id)
    if invoice.status not in ("draft", "issued", "overdue"):
        raise HTTPException(400, "Invoice cannot be cancelled")
    if invoice.amount_paid > 0:
        raise HTTPException(400, "Refund or reverse payments before cancelling")

    invoice.status = "cancelled"
    db.commit()
    return get_invoice(db, invoice_id)
