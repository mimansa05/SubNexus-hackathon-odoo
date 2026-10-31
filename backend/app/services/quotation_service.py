import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.quotation import Quotation, QuotationItem
from app.models.customer import Customer
from app.models.product import Product
from app.schemas.quotation import QuotationCreate


CENT = Decimal("0.01")


def money(value):
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def get_quotation(db: Session, quotation_id: uuid.UUID):
    quotation = db.scalar(
        select(Quotation)
        .options(selectinload(Quotation.items))
        .where(Quotation.id == quotation_id)
    )

    if not quotation:
        raise HTTPException(404, "Quotation not found")

    return quotation


def create_quotation(db: Session, data: QuotationCreate, user_id):
    customer = db.get(Customer, data.customer_id)

    if not customer:
        raise HTTPException(404, "Customer not found")

    subtotal = Decimal("0.00")
    total_discount = Decimal("0.00")
    quotation_items = []

    for item_data in data.items:
        if item_data.product_id:
            product = db.get(Product, item_data.product_id)

            if not product:
                raise HTTPException(404, "Product not found")

            if not product.is_active:
                raise HTTPException(400, "Product is inactive")

        gross = money(item_data.unit_price * item_data.quantity)

        discount = money(
            gross * item_data.discount_percent / Decimal("100")
        )

        line_total = money(gross - discount)

        subtotal += gross
        total_discount += discount

        quotation_items.append(
            QuotationItem(
                product_id=item_data.product_id,
                description=item_data.description,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                discount_percent=item_data.discount_percent,
                total_price=line_total
            )
        )

    subtotal = money(subtotal)
    total_discount = money(total_discount)

    taxable_amount = subtotal - total_discount

    tax_amount = money(
        taxable_amount * data.tax_percent / Decimal("100")
    )

    total_amount = money(taxable_amount + tax_amount)

    now = datetime.now(timezone.utc)

    if data.valid_until and data.valid_until <= now:
        raise HTTPException(400, "valid_until must be in the future")

    quotation = Quotation(
        quotation_number=f"QT-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}",
        customer_id=data.customer_id,
        created_by_user_id=user_id,
        status="draft",
        subtotal=subtotal,
        discount_amount=total_discount,
        tax_amount=tax_amount,
        total_amount=total_amount,
        currency=data.currency.upper(),
        valid_until=data.valid_until,
        notes=data.notes,
        items=quotation_items
    )

    db.add(quotation)
    db.commit()

    return get_quotation(db, quotation.id)


def list_quotations(
    db: Session,
    skip=0,
    limit=20,
    customer_id=None,
    status=None
):
    query = (
        select(Quotation)
        .options(selectinload(Quotation.items))
    )

    if customer_id:
        query = query.where(Quotation.customer_id == customer_id)

    if status:
        query = query.where(Quotation.status == status)

    query = (
        query.order_by(Quotation.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    return db.scalars(query).unique().all()


def send_quotation(db: Session, quotation_id):
    quotation = get_quotation(db, quotation_id)

    if quotation.status != "draft":
        raise HTTPException(400, "Only draft quotations can be sent")

    if quotation.valid_until and quotation.valid_until <= datetime.now(timezone.utc):
        raise HTTPException(400, "Quotation has expired")

    quotation.status = "sent"
    db.commit()

    return get_quotation(db, quotation_id)


def accept_quotation(db: Session, quotation_id):
    quotation = get_quotation(db, quotation_id)

    if quotation.status != "sent":
        raise HTTPException(400, "Only sent quotations can be accepted")

    if quotation.valid_until and quotation.valid_until <= datetime.now(timezone.utc):
        quotation.status = "expired"
        db.commit()
        raise HTTPException(400, "Quotation has expired")

    quotation.status = "accepted"
    db.commit()

    return get_quotation(db, quotation_id)


def reject_quotation(db: Session, quotation_id):
    quotation = get_quotation(db, quotation_id)

    if quotation.status != "sent":
        raise HTTPException(400, "Only sent quotations can be rejected")

    quotation.status = "rejected"
    db.commit()

    return get_quotation(db, quotation_id)


def cancel_quotation(db: Session, quotation_id):
    quotation = get_quotation(db, quotation_id)

    if quotation.status not in ("draft", "sent"):
        raise HTTPException(
            400,
            "Only draft or sent quotations can be cancelled"
        )

    quotation.status = "cancelled"
    db.commit()

    return get_quotation(db, quotation_id)
