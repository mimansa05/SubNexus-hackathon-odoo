from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.core.dependencies import require_staff_or_admin

from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse
)

from app.services.product_service import (
    create_product,
    get_products,
    get_product,
    update_product,
    delete_product
)

router = APIRouter(
    prefix="/api/v1/products",
    tags=["Products"]
)


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED
)
def create(
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return create_product(db, data)


@router.get("/", response_model=list[ProductResponse])
def list_all(
    skip: int = 0,
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return get_products(db, skip, limit, search)


@router.get("/{product_id}", response_model=ProductResponse)
def get_one(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return get_product(db, product_id)


@router.patch("/{product_id}", response_model=ProductResponse)
def update(
    product_id: UUID,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return update_product(db, product_id, data)


@router.delete("/{product_id}")
def delete(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return delete_product(db, product_id)