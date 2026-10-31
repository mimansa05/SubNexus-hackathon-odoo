import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.payment import Payment, PaymentAttempt, Refund
from app.models.invoice import Invoice
from app.schemas.payment import PaymentCreate, RefundCreate


CENT = Decimal("0.01")


def money(value):
    return Decimal(value).quantize(CENT, rounding=ROUND_HALF_UP)


def get_payment(db, payment_id):
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(404, "Payment not found")
    return payment


def create_payment(db: Session, data: PaymentCreate):
    invoice = db.get(Invoice, data.invoice_id)
    if not invoice:
        raise HTTPException(404, "Invoice not found")

    if invoice.customer_id != data.customer_id:
        raise HTTPException(400, "Invoice does not belong to customer")

    if invoice.status not in ("issued", "overdue", "partially_paid"):
        raise HTTPException(400, "Invoice is not payable")

    outstanding = money(invoice.total_amount - invoice.amount_paid)
    if data.amount > outstanding:
        raise HTTPException(400, "Payment exceeds outstanding invoice balance")

    payment = Payment(
        customer_id=data.customer_id,
        invoice_id=data.invoice_id,
        amount=money(data.amount),
        currency=data.currency.upper(),
        status="pending",
        payment_method=data.payment_method,
        gateway=data.gateway
    )

    db.add(payment)
    db.flush()

    db.add(PaymentAttempt(
        payment_id=payment.id,
        attempt_number=1,
        status="pending"
    ))

    db.commit()
    db.refresh(payment)
    return payment


def list_payments(db, skip=0, limit=20, customer_id=None,
                  invoice_id=None, status=None):
    query = select(Payment)
    if customer_id:
        query = query.where(Payment.customer_id == customer_id)
    if invoice_id:
        query = query.where(Payment.invoice_id == invoice_id)
    if status:
        query = query.where(Payment.status == status)

    query = query.order_by(Payment.created_at.desc()).offset(skip).limit(limit)
    return db.scalars(query).all()


def verify_payment(db: Session, payment_id):
    payment = get_payment(db, payment_id)

    if payment.status != "pending":
        raise HTTPException(400, "Only pending payments can be verified")

    if not payment.invoice_id:
        raise HTTPException(400, "Payment has no invoice")

    invoice = db.scalar(
        select(Invoice).where(Invoice.id == payment.invoice_id).with_for_update()
    )
    if not invoice:
        raise HTTPException(404, "Invoice not found")

    if invoice.status not in ("issued", "overdue", "partially_paid"):
        raise HTTPException(400, "Invoice is not payable")

    outstanding = money(invoice.total_amount - invoice.amount_paid)
    if payment.amount > outstanding:
        raise HTTPException(400, "Payment exceeds outstanding balance")

    payment.status = "succeeded"
    invoice.amount_paid = money(invoice.amount_paid + payment.amount)

    if invoice.amount_paid == invoice.total_amount:
        invoice.status = "paid"
        invoice.paid_at = datetime.now(timezone.utc)
    else:
        invoice.status = "partially_paid"

    attempt = db.scalar(
        select(PaymentAttempt)
        .where(PaymentAttempt.payment_id == payment.id)
        .order_by(PaymentAttempt.attempt_number.desc())
    )
    if attempt:
        attempt.status = "succeeded"

    db.commit()
    db.refresh(payment)
    return payment


def fail_payment(db: Session, payment_id, error_message="Payment failed"):
    payment = get_payment(db, payment_id)

    if payment.status != "pending":
        raise HTTPException(400, "Only pending payments can be marked failed")

    payment.status = "failed"

    attempt = db.scalar(
        select(PaymentAttempt)
        .where(PaymentAttempt.payment_id == payment.id)
        .order_by(PaymentAttempt.attempt_number.desc())
    )
    if attempt:
        attempt.status = "failed"
        attempt.error_message = error_message

    db.commit()
    db.refresh(payment)
    return payment


def list_attempts(db, payment_id):
    get_payment(db, payment_id)
    return db.scalars(
        select(PaymentAttempt)
        .where(PaymentAttempt.payment_id == payment_id)
        .order_by(PaymentAttempt.created_at.desc())
    ).all()


def create_refund(db: Session, payment_id, data: RefundCreate):
    payment = get_payment(db, payment_id)

    if payment.status != "succeeded":
        raise HTTPException(400, "Only successful payments can be refunded")

    already_refunded = db.scalar(
        select(Refund).where(
            Refund.payment_id == payment_id,
            Refund.status.in_(["pending", "succeeded"])
        )
    )

    refunded_amount = sum(
        (r.amount for r in db.scalars(
            select(Refund).where(
                Refund.payment_id == payment_id,
                Refund.status.in_(["pending", "succeeded"])
            )
        ).all()),
        Decimal("0.00")
    )

    if money(refunded_amount + data.amount) > payment.amount:
        raise HTTPException(400, "Refund exceeds captured payment amount")

    refund = Refund(
        payment_id=payment_id,
        amount=money(data.amount),
        currency=payment.currency,
        reason=data.reason,
        status="pending"
    )

    db.add(refund)
    db.commit()
    db.refresh(refund)
    return refund


def list_refunds(db, payment_id):
    get_payment(db, payment_id)
    return db.scalars(
        select(Refund)
        .where(Refund.payment_id == payment_id)
        .order_by(Refund.created_at.desc())
    ).all()
