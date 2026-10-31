"""
Shared metadata module.
Imports Base from canonical db.py and imports all models so that Alembic and metadata reflection discover all tables.
"""

from app.database.db import Base
from app.models import (
    User,
    Customer,
    Product,
    Plan,
    Subscription,
    Quotation,
    QuotationItem,
    Invoice,
    InvoiceItem,
    Payment,
    PaymentAttempt,
    WebhookEvent,
    Refund,
    Discount,
    DiscountUsage,
    Approval,
    AgentLog,
    AuditLog,
    SubscriptionEvent,
)

metadata = Base.metadata

__all__ = [
    "Base",
    "metadata",
    "User",
    "Customer",
    "Product",
    "Plan",
    "Subscription",
    "Quotation",
    "QuotationItem",
    "Invoice",
    "InvoiceItem",
    "Payment",
    "PaymentAttempt",
    "WebhookEvent",
    "Refund",
    "Discount",
    "DiscountUsage",
    "Approval",
    "AgentLog",
    "AuditLog",
    "SubscriptionEvent",
]
