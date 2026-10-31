from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.core.dependencies import require_admin, require_staff_or_admin

from app.schemas.discount import (
    DiscountCreate,
    DiscountResponse,
    DiscountValidationRequest,
    DiscountValidationResponse
)

from app.services.discount_service import (
    create_discount,
    list_discounts,
    get_discount,
    deactivate_discount,
    validate_discount
)


router = APIRouter(prefix="/api/v1/discounts", tags=["Discounts"])


@router.post("/", response_model=DiscountResponse,
             status_code=status.HTTP_201_CREATED)
def create(data: DiscountCreate, db: Session = Depends(get_db),
           user=Depends(require_admin)):
    return create_discount(db, data)


@router.get("/", response_model=list[DiscountResponse])
def list_all(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    active_only: bool = False,
    db: Session = Depends(get_db),
    user=Depends(require_staff_or_admin)
):
    return list_discounts(db, skip, limit, active_only)


@router.get("/{discount_id}", response_model=DiscountResponse)
def get_one(discount_id: UUID, db: Session = Depends(get_db),
            user=Depends(require_staff_or_admin)):
    return get_discount(db, discount_id)


@router.post("/validate", response_model=DiscountValidationResponse)
def validate(data: DiscountValidationRequest,
             db: Session = Depends(get_db),
             user=Depends(require_staff_or_admin)):
    return validate_discount(db, data)


@router.patch("/{discount_id}/deactivate",
              response_model=DiscountResponse)
def deactivate(discount_id: UUID, db: Session = Depends(get_db),
               user=Depends(require_admin)):
    return deactivate_discount(db, discount_id)
