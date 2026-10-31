from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.reconciliation import ReconciliationTransaction


def explain_unmatched_payments(db: Session, limit: int = 50) -> list[dict]:
    """Explain unresolved bank entries using recorded reconciliation evidence."""
    rows = db.scalars(
        select(ReconciliationTransaction)
        .where(ReconciliationTransaction.status.in_(("unmatched", "mismatched", "pending_confirmation")))
        .order_by(ReconciliationTransaction.transaction_date.desc())
        .limit(limit)
    ).all()
    results = []
    for row in rows:
        if row.match_notes:
            explanation = row.match_notes
        elif row.status == "pending_confirmation":
            explanation = "A candidate match is awaiting staff confirmation."
        else:
            explanation = "No payment or invoice match has been recorded for this bank transaction yet."
        results.append({
            "transaction_id": str(row.id),
            "transaction_date": row.transaction_date.isoformat(),
            "amount": str(row.amount),
            "currency": row.currency,
            "bank_reference": row.bank_reference,
            "customer_email": row.customer_email,
            "status": row.status,
            "explanation": explanation,
        })
    return results
