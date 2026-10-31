from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.core.dependencies import require_staff_or_admin

from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse
)

from app.services.customer_service import (
    create_customer,
    get_customers,
    get_customer,
    update_customer,
    delete_customer
)

router = APIRouter(
    prefix="/api/v1/customers",
    tags=["Customers"]
)


@router.post(
    "/",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED
)
def create(
    data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return create_customer(db, data)


@router.get("/", response_model=list[CustomerResponse])
def list_all(
    skip: int = 0,
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return get_customers(db, skip, limit, search)


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_one(
    customer_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return get_customer(db, customer_id)


@router.patch("/{customer_id}", response_model=CustomerResponse)
def update(
    customer_id: UUID,
    data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return update_customer(db, customer_id, data)


@router.delete("/{customer_id}")
def delete(
    customer_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return delete_customer(db, customer_id)