from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.models.plan import Plan
from app.models.product import Product
from app.schemas.plan import PlanCreate, PlanUpdate


def check_product(db: Session, product_id: UUID):
    product = db.get(Product, product_id)

    if not product:
        raise HTTPException(404, "Product not found")

    if not product.is_active:
        raise HTTPException(400, "Product is inactive")

    return product


def create_plan(db: Session, data: PlanCreate):
    check_product(db, data.product_id)

    existing = db.scalar(
        select(Plan).where(Plan.code == data.code)
    )

    if existing:
        raise HTTPException(409, "Plan code already exists")

    plan = Plan(**data.model_dump())

    db.add(plan)
    db.commit()
    db.refresh(plan)

    return plan


def get_plans(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    search: str | None = None,
    product_id: UUID | None = None,
    active_only: bool = True
):
    query = select(Plan)

    if active_only:
        query = query.where(Plan.is_active.is_(True))

    if product_id:
        query = query.where(Plan.product_id == product_id)

    if search:
        term = f"%{search}%"
        query = query.where(
            or_(
                Plan.name.ilike(term),
                Plan.code.ilike(term),
                Plan.description.ilike(term)
            )
        )

    query = query.order_by(Plan.created_at.desc())
    query = query.offset(skip).limit(limit)

    return db.scalars(query).all()


def get_plan(db: Session, plan_id: UUID):
    plan = db.get(Plan, plan_id)

    if not plan:
        raise HTTPException(404, "Plan not found")

    return plan


def update_plan(db: Session, plan_id: UUID, data: PlanUpdate):
    plan = get_plan(db, plan_id)

    updates = data.model_dump(exclude_unset=True)

    required_fields = {
        "product_id", "name", "code", "price",
        "billing_interval", "interval_count",
        "trial_period_days", "currency", "is_active"
    }

    for field, value in updates.items():
        if field in required_fields and value is None:
            raise HTTPException(422, f"{field} cannot be null")

    if "product_id" in updates:
        check_product(db, updates["product_id"])

    if "code" in updates and updates["code"] != plan.code:
        existing = db.scalar(
            select(Plan).where(
                Plan.code == updates["code"],
                Plan.id != plan_id
            )
        )

        if existing:
            raise HTTPException(409, "Plan code already exists")

    for key, value in updates.items():
        setattr(plan, key, value)

    db.commit()
    db.refresh(plan)

    return plan


def deactivate_plan(db: Session, plan_id: UUID):
    plan = get_plan(db, plan_id)

    plan.is_active = False

    db.commit()

    return {"message": "Plan deactivated successfully"}
