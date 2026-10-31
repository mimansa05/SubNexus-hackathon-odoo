from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.core.dependencies import require_staff_or_admin
from app.schemas.invoice import InvoiceCreate, InvoiceResponse
from app.services.invoice_service import (
    create_invoice, list_invoices, get_invoice,
    issue_invoice, cancel_invoice
)


router = APIRouter(prefix="/api/v1/invoices", tags=["Invoices"])


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create(data: InvoiceCreate, db: Session = Depends(get_db),
           user=Depends(require_staff_or_admin)):
    return create_invoice(db, data)


@router.get("/", response_model=list[InvoiceResponse])
def list_all(skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
             customer_id: UUID | None = None, status: str | None = None,
             db: Session = Depends(get_db),
             user=Depends(require_staff_or_admin)):
    return list_invoices(db, skip, limit, customer_id, status)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_one(invoice_id: UUID, db: Session = Depends(get_db),
            user=Depends(require_staff_or_admin)):
    return get_invoice(db, invoice_id)


@router.post("/{invoice_id}/issue", response_model=InvoiceResponse)
def issue(invoice_id: UUID, db: Session = Depends(get_db),
          user=Depends(require_staff_or_admin)):
    return issue_invoice(db, invoice_id)


@router.post("/{invoice_id}/cancel", response_model=InvoiceResponse)
def cancel(invoice_id: UUID, db: Session = Depends(get_db),
            user=Depends(require_staff_or_admin)):
    return cancel_invoice(db, invoice_id)
