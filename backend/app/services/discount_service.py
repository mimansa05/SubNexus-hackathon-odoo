from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.discount import Discount
from app.schemas.discount import DiscountCreate, DiscountValidationRequest


CENT = Decimal("0.01")


def money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def create_discount(db: Session, data: DiscountCreate):
    code = data.code.strip().upper()

    existing = db.scalar(
        select(Discount).where(Discount.code == code)
    )
    if existing:
        raise HTTPException(409, "Discount code already exists")

    if data.discount_type == "percentage" and data.value > 100:
        raise HTTPException(400, "Percentage discount cannot exceed 100")

    if data.starts_at and data.expires_at:
        if data.expires_at <= data.starts_at:
            raise HTTPException(400, "Expiry must be after start date")

    discount = Discount(
        code=code,
        discount_type=data.discount_type,
        value=data.value,
        max_uses=data.max_uses,
        starts_at=data.starts_at,
        expires_at=data.expires_at,
        used_count=0,
        is_active=True
    )

    db.add(discount)
    db.commit()
    db.refresh(discount)
    return discount


def list_discounts(db: Session, skip=0, limit=20, active_only=False):
    query = select(Discount)

    if active_only:
        query = query.where(Discount.is_active.is_(True))

    query = query.order_by(Discount.created_at.desc()).offset(skip).limit(limit)
    return db.scalars(query).all()


def get_discount(db: Session, discount_id):
    discount = db.get(Discount, discount_id)
    if not discount:
        raise HTTPException(404, "Discount not found")
    return discount


def deactivate_discount(db: Session, discount_id):
    discount = get_discount(db, discount_id)
    discount.is_active = False
    db.commit()
    db.refresh(discount)
    return discount


def validate_discount(db: Session, data: DiscountValidationRequest):
    code = data.code.strip().upper()

    discount = db.scalar(
        select(Discount)
        .where(Discount.code == code)
        .with_for_update()
    )

    if not discount:
        raise HTTPException(404, "Discount code not found")

    now = datetime.now(timezone.utc)

    if not discount.is_active:
        raise HTTPException(400, "Discount is inactive")

    if discount.starts_at and now < discount.starts_at:
        raise HTTPException(400, "Discount is not active yet")

    if discount.expires_at and now > discount.expires_at:
        raise HTTPException(400, "Discount has expired")

    if discount.max_uses is not None and discount.used_count >= discount.max_uses:
        raise HTTPException(400, "Discount usage limit reached")

    if discount.discount_type == "percentage":
        amount = money(data.amount * discount.value / Decimal("100"))
    else:
        amount = money(discount.value)

    amount = min(amount, money(data.amount))
    final_amount = money(data.amount - amount)

    return {
        "valid": True,
        "code": discount.code,
        "discount_type": discount.discount_type,
        "original_amount": money(data.amount),
        "discount_amount": amount,
        "final_amount": final_amount,
        "message": "Discount is valid"
    }
