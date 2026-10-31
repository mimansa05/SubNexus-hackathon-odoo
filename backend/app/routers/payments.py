from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.core.dependencies import require_admin, require_staff_or_admin

from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentAttemptResponse,
    RefundCreate,
    RefundResponse
)

from app.services.payment_service import (
    create_payment,
    list_payments,
    get_payment,
    verify_payment,
    fail_payment,
    list_attempts,
    create_refund,
    list_refunds
)


router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


@router.post("/", response_model=PaymentResponse,
             status_code=status.HTTP_201_CREATED)
def create(data: PaymentCreate, db: Session = Depends(get_db),
           user=Depends(require_staff_or_admin)):
    return create_payment(db, data)


@router.get("/", response_model=list[PaymentResponse])
def list_all(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    customer_id: UUID | None = None,
    invoice_id: UUID | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    user=Depends(require_staff_or_admin)
):
    return list_payments(db, skip, limit, customer_id, invoice_id, status)


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_one(payment_id: UUID, db: Session = Depends(get_db),
            user=Depends(require_staff_or_admin)):
    return get_payment(db, payment_id)


@router.post("/{payment_id}/verify", response_model=PaymentResponse)
def verify(payment_id: UUID, db: Session = Depends(get_db),
           user=Depends(require_admin)):
    return verify_payment(db, payment_id)


@router.post("/{payment_id}/fail", response_model=PaymentResponse)
def fail(payment_id: UUID, error_message: str = "Payment failed",
         db: Session = Depends(get_db),
         user=Depends(require_admin)):
    return fail_payment(db, payment_id, error_message)


@router.get("/{payment_id}/attempts",
            response_model=list[PaymentAttemptResponse])
def attempts(payment_id: UUID, db: Session = Depends(get_db),
             user=Depends(require_staff_or_admin)):
    return list_attempts(db, payment_id)


@router.post("/{payment_id}/refunds",
             response_model=RefundResponse,
             status_code=status.HTTP_201_CREATED)
def refund(payment_id: UUID, data: RefundCreate,
           db: Session = Depends(get_db),
           user=Depends(require_admin)):
    return create_refund(db, payment_id, data)


@router.get("/{payment_id}/refunds",
            response_model=list[RefundResponse])
def refunds(payment_id: UUID, db: Session = Depends(get_db),
             user=Depends(require_staff_or_admin)):
    return list_refunds(db, payment_id)
