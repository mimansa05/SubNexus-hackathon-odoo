import csv
import hashlib
import io
from datetime import date, datetime, time, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.invoice import Invoice
from app.models.log import AuditLog
from app.models.payment import Payment, PaymentAttempt
from app.models.reconciliation import ReconciliationTransaction
from app.models.user import User
from app.schemas.reconciliation import ReconciliationMatchRequest


CENT = Decimal("0.01")
MAX_CSV_BYTES = 5 * 1024 * 1024
REQUIRED_HEADERS = {"transaction_date", "amount", "currency"}
OPTIONAL_HEADERS = {
    "bank_reference",
    "transaction_id",
    "customer_email",
    "description",
}


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _parse_transaction_date(value: str) -> datetime:
    value = value.strip()
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed_date = date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("transaction_date must be an ISO date or datetime") from exc
        parsed = datetime.combine(parsed_date, time.min)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _parse_csv_row(row: dict[str, str]) -> dict:
    date_value = (row.get("transaction_date") or "").strip()
    if not date_value:
        raise ValueError("transaction_date is required")
    transaction_date = _parse_transaction_date(date_value)

    amount_value = (row.get("amount") or "").strip()
    try:
        amount = Decimal(amount_value)
    except InvalidOperation as exc:
        raise ValueError("amount must be a valid decimal number") from exc
    if not amount.is_finite() or amount <= 0:
        raise ValueError("amount must be greater than zero")
    if amount >= Decimal("10000000000"):
        raise ValueError("amount must be less than 10000000000")
    if amount != _money(amount):
        raise ValueError("amount must have no more than two decimal places")

    currency = (row.get("currency") or "").strip().upper()
    if len(currency) != 3 or not currency.isascii() or not currency.isalpha():
        raise ValueError("currency must be a three-letter code")

    bank_reference = (row.get("bank_reference") or "").strip() or None
    bank_transaction_id = (row.get("transaction_id") or "").strip() or None
    customer_email = (row.get("customer_email") or "").strip().lower() or None
    description = (row.get("description") or "").strip() or None
    for field_name, value in (
        ("bank_reference", bank_reference),
        ("transaction_id", bank_transaction_id),
        ("customer_email", customer_email),
    ):
        if value and len(value) > 255:
            raise ValueError(f"{field_name} must be 255 characters or fewer")
    if customer_email and ("@" not in customer_email or customer_email.startswith("@")):
        raise ValueError("customer_email must be a valid email address")

    identity = (
        f"reference:{bank_reference.casefold()}"
        if bank_reference
        else f"transaction:{bank_transaction_id.casefold()}"
        if bank_transaction_id
        else "|".join(
            (
                transaction_date.isoformat(),
                format(_money(amount), "f"),
                currency,
                customer_email or "",
                (description or "").casefold(),
            )
        )
    )
    return {
        "transaction_date": transaction_date,
        "amount": _money(amount),
        "currency": currency,
        "bank_reference": bank_reference,
        "transaction_id": bank_transaction_id,
        "customer_email": customer_email,
        "description": description,
        "deduplication_key": hashlib.sha256(identity.encode("utf-8")).hexdigest(),
    }


def import_transactions(
    db: Session,
    content: bytes,
    filename: Optional[str],
    user: User,
) -> dict:
    if not filename or not filename.lower().endswith(".csv"):
        raise HTTPException(400, "Upload a .csv file")
    if len(content) > MAX_CSV_BYTES:
        raise HTTPException(413, "CSV file must be 5 MB or smaller")

    try:
        text_content = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(400, "CSV must use UTF-8 encoding") from exc

    reader = csv.reader(io.StringIO(text_content, newline=""), strict=True)
    try:
        raw_headers = next(reader, None)
    except csv.Error as exc:
        raise HTTPException(400, "CSV header is malformed") from exc
    if not raw_headers:
        raise HTTPException(400, "CSV file is empty")

    headers = [header.strip().lower() for header in raw_headers]
    if len(headers) != len(set(headers)):
        raise HTTPException(400, "CSV headers must not contain duplicates")
    missing_headers = REQUIRED_HEADERS.difference(headers)
    if missing_headers:
        names = ", ".join(sorted(missing_headers))
        raise HTTPException(400, f"CSV is missing required headers: {names}")
    unsupported_headers = set(headers).difference(REQUIRED_HEADERS | OPTIONAL_HEADERS)
    if unsupported_headers:
        names = ", ".join(sorted(unsupported_headers))
        raise HTTPException(400, f"CSV contains unsupported headers: {names}")

    transactions = []
    errors = []
    imported_count = 0
    duplicate_count = 0
    try:
        for row_number, values in enumerate(reader, start=2):
            if not any(value.strip() for value in values):
                continue
            if len(values) != len(headers):
                errors.append({
                    "row_number": row_number,
                    "error": f"Expected {len(headers)} columns but found {len(values)}",
                })
                continue

            try:
                row = _parse_csv_row(dict(zip(headers, values)))
            except ValueError as exc:
                errors.append({"row_number": row_number, "error": str(exc)})
                continue

            existing = db.scalar(
                select(ReconciliationTransaction).where(
                    ReconciliationTransaction.deduplication_key
                    == row["deduplication_key"],
                    ReconciliationTransaction.status != "duplicate",
                )
            )
            transaction = ReconciliationTransaction(
                **row,
                status="duplicate" if existing else "unmatched",
                duplicate_of_id=existing.id if existing else None,
            )
            try:
                with db.begin_nested():
                    db.add(transaction)
                    db.flush()
            except IntegrityError:
                existing = db.scalar(
                    select(ReconciliationTransaction).where(
                        ReconciliationTransaction.deduplication_key
                        == row["deduplication_key"],
                        ReconciliationTransaction.status != "duplicate",
                    )
                )
                if existing is None:
                    raise
                transaction.status = "duplicate"
                transaction.duplicate_of_id = existing.id
                db.add(transaction)
                db.flush()

            action = (
                "duplicate_imported"
                if transaction.status == "duplicate"
                else "imported"
            )
            db.add(
                AuditLog(
                    user_id=user.id,
                    entity_type="bank_reconciliation",
                    entity_id=transaction.id,
                    action=action,
                    new_values={
                        "status": transaction.status,
                        "row_number": row_number,
                        "duplicate_of_id": (
                            str(transaction.duplicate_of_id)
                            if transaction.duplicate_of_id
                            else None
                        ),
                    },
                )
            )
            transactions.append(transaction)
            if transaction.status == "duplicate":
                duplicate_count += 1
            else:
                imported_count += 1
    except csv.Error as exc:
        db.rollback()
        raise HTTPException(400, "CSV contains malformed data") from exc

    db.commit()
    return {
        "imported_count": imported_count,
        "duplicate_count": duplicate_count,
        "invalid_count": len(errors),
        "transactions": transactions,
        "errors": errors,
    }


def list_transactions(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    status: Optional[str] = None,
    customer_id: Optional[UUID] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    unmatched_only: bool = False,
) -> list[ReconciliationTransaction]:
    query = select(ReconciliationTransaction)
    if unmatched_only:
        query = query.where(ReconciliationTransaction.status != "matched")
    if status:
        query = query.where(ReconciliationTransaction.status == status)
    if customer_id:
        query = query.where(ReconciliationTransaction.customer_id == customer_id)
    if date_from:
        query = query.where(
            ReconciliationTransaction.transaction_date
            >= datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        )
    if date_to:
        query = query.where(
            ReconciliationTransaction.transaction_date
            <= datetime.combine(date_to, time.max, tzinfo=timezone.utc)
        )
    return db.scalars(
        query.order_by(ReconciliationTransaction.transaction_date.desc())
        .offset(skip)
        .limit(limit)
    ).all()


def _record_audit(
    db: Session,
    user: User,
    transaction: ReconciliationTransaction,
    action: str,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
) -> None:
    db.add(
        AuditLog(
            user_id=user.id,
            customer_id=transaction.customer_id,
            entity_type="bank_reconciliation",
            entity_id=transaction.id,
            action=action,
            old_values=old_values,
            new_values=new_values,
        )
    )


def _customer_mismatch(
    customer: Customer,
    transaction: ReconciliationTransaction,
) -> bool:
    return bool(
        transaction.customer_email
        and transaction.customer_email.casefold() != customer.email.casefold()
    )


def propose_match(
    db: Session,
    data: ReconciliationMatchRequest,
    user: User,
) -> ReconciliationTransaction:
    transaction = db.scalar(
        select(ReconciliationTransaction)
        .where(ReconciliationTransaction.id == data.transaction_id)
        .with_for_update()
    )
    if not transaction:
        raise HTTPException(404, "Reconciliation transaction not found")
    if transaction.status == "duplicate" or transaction.status == "matched":
        raise HTTPException(400, "This transaction cannot be matched")

    old_values = {
        "status": transaction.status,
        "payment_id": str(transaction.payment_id) if transaction.payment_id else None,
        "invoice_id": str(transaction.invoice_id) if transaction.invoice_id else None,
    }
    transaction.payment_id = None
    transaction.invoice_id = None
    transaction.customer_id = None
    notes = []

    if data.payment_id:
        payment = db.scalar(
            select(Payment)
            .where(Payment.id == data.payment_id)
            .with_for_update()
        )
        if not payment:
            raise HTTPException(404, "Payment not found")
        invoice = db.scalar(
            select(Invoice)
            .where(Invoice.id == payment.invoice_id)
            .with_for_update()
        ) if payment.invoice_id else None
        customer = db.get(Customer, payment.customer_id)
        transaction.payment_id = payment.id
        transaction.invoice_id = payment.invoice_id
        transaction.customer_id = payment.customer_id

        if payment.status != "pending":
            notes.append("Payment is not pending")
        if not invoice:
            notes.append("Payment is not linked to an invoice")
        elif invoice.status not in ("issued", "overdue", "partially_paid"):
            notes.append("Invoice is not payable")
        elif payment.amount > _money(invoice.total_amount - invoice.amount_paid):
            notes.append("Payment exceeds the invoice's outstanding balance")
        if invoice and invoice.currency.upper() != transaction.currency:
            notes.append("Transaction currency does not match invoice currency")
        if payment.customer_id != (invoice.customer_id if invoice else None):
            notes.append("Payment customer does not match invoice customer")
        if payment.amount != transaction.amount:
            notes.append("Transaction amount does not match payment amount")
        if payment.currency.upper() != transaction.currency:
            notes.append("Transaction currency does not match payment currency")
        if transaction.transaction_date.date() < payment.created_at.date():
            notes.append("Transaction date predates payment record")
        bank_reference = transaction.bank_reference or transaction.transaction_id
        if (
            bank_reference
            and payment.gateway_transaction_id
            and bank_reference.casefold()
            != payment.gateway_transaction_id.casefold()
        ):
            notes.append("Bank reference does not match payment transaction ID")
        if customer and _customer_mismatch(customer, transaction):
            notes.append("Transaction customer does not match payment customer")
    else:
        invoice = db.scalar(
            select(Invoice)
            .where(Invoice.id == data.invoice_id)
            .with_for_update()
        )
        if not invoice:
            raise HTTPException(404, "Invoice not found")
        customer = db.get(Customer, invoice.customer_id)
        transaction.invoice_id = invoice.id
        transaction.customer_id = invoice.customer_id

        if invoice.status not in ("issued", "overdue", "partially_paid"):
            notes.append("Invoice is not payable")
        if transaction.amount > _money(invoice.total_amount - invoice.amount_paid):
            notes.append("Transaction exceeds the invoice's outstanding balance")
        if invoice.currency.upper() != transaction.currency:
            notes.append("Transaction currency does not match invoice currency")
        if transaction.transaction_date.date() < invoice.created_at.date():
            notes.append("Transaction date predates invoice")
        if customer and _customer_mismatch(customer, transaction):
            notes.append("Transaction customer does not match invoice customer")

    transaction.status = "mismatched" if notes else "pending_confirmation"
    transaction.match_notes = "; ".join(notes) if notes else None
    _record_audit(
        db,
        user,
        transaction,
        "match_mismatched" if notes else "match_proposed",
        old_values=old_values,
        new_values={
            "status": transaction.status,
            "payment_id": str(transaction.payment_id) if transaction.payment_id else None,
            "invoice_id": str(transaction.invoice_id) if transaction.invoice_id else None,
            "match_notes": transaction.match_notes,
        },
    )
    db.commit()
    db.refresh(transaction)
    return transaction


def _set_invoice_paid(invoice: Invoice, amount: Decimal) -> None:
    invoice.amount_paid = _money(invoice.amount_paid + amount)
    if invoice.amount_paid >= invoice.total_amount:
        invoice.status = "paid"
        invoice.paid_at = datetime.now(timezone.utc)
    else:
        invoice.status = "partially_paid"


def confirm_match(
    db: Session,
    transaction_id: UUID,
    user: User,
) -> ReconciliationTransaction:
    transaction = db.scalar(
        select(ReconciliationTransaction)
        .where(ReconciliationTransaction.id == transaction_id)
        .with_for_update()
    )
    if not transaction:
        raise HTTPException(404, "Reconciliation transaction not found")
    if transaction.status != "pending_confirmation":
        raise HTTPException(400, "Only proposed matches can be confirmed")

    invoice = db.scalar(
        select(Invoice)
        .where(Invoice.id == transaction.invoice_id)
        .with_for_update()
    ) if transaction.invoice_id else None
    if not invoice:
        raise HTTPException(409, "Matched invoice no longer exists")
    if invoice.status not in ("issued", "overdue", "partially_paid"):
        raise HTTPException(409, "Invoice is no longer payable")

    if transaction.payment_id:
        payment = db.scalar(
            select(Payment)
            .where(Payment.id == transaction.payment_id)
            .with_for_update()
        )
        if not payment or payment.status != "pending":
            raise HTTPException(409, "Matched payment is no longer pending")
        if payment.invoice_id != invoice.id or payment.amount != transaction.amount:
            raise HTTPException(409, "Matched payment no longer matches the transaction")
        if payment.currency.upper() != transaction.currency:
            raise HTTPException(409, "Payment currency changed after match proposal")
        if payment.customer_id != invoice.customer_id:
            raise HTTPException(409, "Payment customer no longer matches the invoice")
    else:
        payment = None

    outstanding = _money(invoice.total_amount - invoice.amount_paid)
    if transaction.amount > outstanding:
        raise HTTPException(409, "Transaction exceeds the invoice's outstanding balance")
    if invoice.currency.upper() != transaction.currency:
        raise HTTPException(409, "Invoice currency changed after match proposal")
    customer = db.get(Customer, invoice.customer_id)
    if customer and _customer_mismatch(customer, transaction):
        raise HTTPException(409, "Transaction customer changed after match proposal")

    external_reference = transaction.bank_reference or transaction.transaction_id
    gateway_transaction_id = external_reference or f"reconciliation:{transaction.id}"
    existing_payment = db.scalar(
        select(Payment).where(
            Payment.gateway_transaction_id == gateway_transaction_id
        )
    )
    if existing_payment and (payment is None or existing_payment.id != payment.id):
        raise HTTPException(409, "Bank reference is already linked to another payment")
    if payment and payment.gateway_transaction_id not in (None, gateway_transaction_id):
        raise HTTPException(409, "Payment already has a different gateway transaction")

    old_values = {
        "invoice_status": invoice.status,
        "invoice_amount_paid": str(invoice.amount_paid),
        "payment_status": payment.status if payment else None,
    }
    if payment is None:
        payment = Payment(
            customer_id=invoice.customer_id,
            invoice_id=invoice.id,
            amount=transaction.amount,
            currency=transaction.currency,
            status="succeeded",
            payment_method="bank_transfer",
            gateway="manual",
            gateway_transaction_id=gateway_transaction_id,
        )
        db.add(payment)
        db.flush()
        db.add(
            PaymentAttempt(
                payment_id=payment.id,
                attempt_number=1,
                status="succeeded",
            )
        )
    else:
        payment.status = "succeeded"
        payment.gateway_transaction_id = gateway_transaction_id
        attempt = db.scalar(
            select(PaymentAttempt)
            .where(PaymentAttempt.payment_id == payment.id)
            .order_by(PaymentAttempt.attempt_number.desc())
            .with_for_update()
        )
        if attempt:
            attempt.status = "succeeded"
            attempt.error_code = None
            attempt.error_message = None
        else:
            db.add(
                PaymentAttempt(
                    payment_id=payment.id,
                    attempt_number=1,
                    status="succeeded",
                )
            )

    _set_invoice_paid(invoice, transaction.amount)
    transaction.customer_id = invoice.customer_id
    transaction.payment_id = payment.id
    transaction.status = "matched"
    transaction.match_notes = None
    transaction.confirmed_by_id = user.id
    transaction.confirmed_at = datetime.now(timezone.utc)
    _record_audit(
        db,
        user,
        transaction,
        "match_confirmed",
        old_values=old_values,
        new_values={
            "invoice_status": invoice.status,
            "invoice_amount_paid": str(invoice.amount_paid),
            "payment_id": str(payment.id),
            "payment_status": payment.status,
        },
    )
    db.commit()
    db.refresh(transaction)
    return transaction
