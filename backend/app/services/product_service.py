from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def create_product(db: Session, data: ProductCreate):

    if data.sku:
        existing = db.scalar(
            select(Product).where(Product.sku == data.sku)
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Product SKU already exists"
            )

    product = Product(**data.model_dump())

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


def get_products(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    search: str | None = None
):

    query = select(Product)

    if search:
        term = f"%{search}%"

        query = query.where(
            or_(
                Product.name.ilike(term),
                Product.sku.ilike(term),
                Product.description.ilike(term)
            )
        )

    query = query.order_by(Product.created_at.desc())
    query = query.offset(skip).limit(limit)

    return db.scalars(query).all()


def get_product(db: Session, product_id: UUID):

    product = db.get(Product, product_id)

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


def update_product(
    db: Session,
    product_id: UUID,
    data: ProductUpdate
):

    product = get_product(db, product_id)

    update_data = data.model_dump(exclude_unset=True)

    if "sku" in update_data and update_data["sku"]:
        existing = db.scalar(
            select(Product).where(
                Product.sku == update_data["sku"],
                Product.id != product_id
            )
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="SKU already belongs to another product"
            )

    for key, value in update_data.items():
        setattr(product, key, value)

    db.commit()
    db.refresh(product)

    return product


def delete_product(db: Session, product_id: UUID):

    product = get_product(db, product_id)

    # Preserve products that have business history.
    if product.plans or product.quotation_items or product.invoice_items:
        raise HTTPException(
            status_code=409,
            detail="Product has associated records. Deactivate it instead."
        )

    # Soft delete: retain the database record.
    product.is_active = False

    db.commit()
    db.refresh(product)

    return {"message": "Product deactivated successfully"}