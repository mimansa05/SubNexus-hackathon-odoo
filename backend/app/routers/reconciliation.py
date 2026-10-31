from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.dependencies import require_staff_or_admin
from app.database.db import get_db
from app.models.user import User
from app.schemas.reconciliation import (
    ReconciliationImportResponse,
    ReconciliationListResponse,
    ReconciliationMatchRequest,
    ReconciliationTransactionResponse,
)
from app.services.reconciliation_service import (
    MAX_CSV_BYTES,
    confirm_match,
    import_transactions,
    list_transactions,
    propose_match,
)


router = APIRouter(
    prefix="/api/v1/reconciliation",
    tags=["Bank Reconciliation"],
)


@router.post("/upload", response_model=ReconciliationImportResponse)
async def upload_csv(
    file: UploadFile = File(
        ...,
        description=(
            "UTF-8 CSV with transaction_date, amount, and currency headers. "
            "Optional headers: bank_reference, transaction_id, customer_email, description."
        ),
    ),
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
):
    content = await file.read(MAX_CSV_BYTES + 1)
    if len(content) > MAX_CSV_BYTES:
        raise HTTPException(413, "CSV file must be 5 MB or smaller")
    return import_transactions(db, content, file.filename, user)


@router.get("/", response_model=ReconciliationListResponse)
def list_all(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    customer_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(400, "date_from must be on or before date_to")
    return {
        "items": list_transactions(
            db,
            skip,
            limit,
            status,
            customer_id,
            date_from,
            date_to,
        ),
        "skip": skip,
        "limit": limit,
    }


@router.get("/unmatched", response_model=ReconciliationListResponse)
def list_unmatched(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    customer_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(400, "date_from must be on or before date_to")
    return {
        "items": list_transactions(
            db,
            skip,
            limit,
            customer_id=customer_id,
            date_from=date_from,
            date_to=date_to,
            unmatched_only=True,
        ),
        "skip": skip,
        "limit": limit,
    }


@router.post("/match", response_model=ReconciliationTransactionResponse)
def match(
    data: ReconciliationMatchRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
):
    return propose_match(db, data, user)


@router.post(
    "/{transaction_id}/confirm",
    response_model=ReconciliationTransactionResponse,
)
def confirm(
    transaction_id: UUID,
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
):
    return confirm_match(db, transaction_id, user)
