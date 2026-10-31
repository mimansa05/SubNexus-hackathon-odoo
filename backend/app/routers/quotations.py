from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.core.dependencies import require_staff_or_admin
from app.models.user import User

from app.schemas.quotation import (
    QuotationCreate,
    QuotationResponse
)

from app.services.quotation_service import (
    create_quotation,
    list_quotations,
    get_quotation,
    send_quotation,
    accept_quotation,
    reject_quotation,
    cancel_quotation
)


router = APIRouter(
    prefix="/api/v1/quotations",
    tags=["Quotations"]
)


@router.post(
    "/",
    response_model=QuotationResponse,
    status_code=status.HTTP_201_CREATED
)
def create(
    data: QuotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_staff_or_admin)
):
    return create_quotation(db, data, current_user.id)


@router.get("/", response_model=list[QuotationResponse])
def list_all(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    customer_id: UUID | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return list_quotations(db, skip, limit, customer_id, status)


@router.get("/{quotation_id}", response_model=QuotationResponse)
def get_one(
    quotation_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return get_quotation(db, quotation_id)


@router.post("/{quotation_id}/send", response_model=QuotationResponse)
def send(
    quotation_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return send_quotation(db, quotation_id)


@router.post("/{quotation_id}/accept", response_model=QuotationResponse)
def accept(
    quotation_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return accept_quotation(db, quotation_id)


@router.post("/{quotation_id}/reject", response_model=QuotationResponse)
def reject(
    quotation_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return reject_quotation(db, quotation_id)


@router.post("/{quotation_id}/cancel", response_model=QuotationResponse)
def cancel(
    quotation_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return cancel_quotation(db, quotation_id)
