"""
Comprehensive Database Architecture Verification Script.
Tests:
1. PostgreSQL connectivity
2. All 19 expected tables
3. User creation & unique email constraint
4. Foreign key integrity constraints
5. Subscription and Invoice relationships
6. Payment and PaymentAttempt records
7. Webhook event idempotency constraint (gateway + event_id)
"""

import sys
import uuid
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from app.database.db import engine, SessionLocal
from app.models import (
    User,
    Customer,
    Product,
    Plan,
    Subscription,
    SubscriptionEvent,
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
)


def run_tests():
    print("=" * 60)
    print("SUBNEXUS DATABASE ARCHITECTURE TEST SUITE")
    print("=" * 60)

    # 1. Verify Connectivity
    print("\n[Test 1] Testing PostgreSQL Connectivity...")
    with engine.connect() as conn:
        res = conn.execute(text("SELECT version();")).scalar()
        print(f"  -> SUCCESS: Connected! Version: {res[:45]}...")

    # 2. Verify all 19 expected tables
    print("\n[Test 2] Verifying Expected Tables...")
    expected_tables = {
        "users",
        "customers",
        "products",
        "plans",
        "subscriptions",
        "subscription_events",
        "quotations",
        "quotation_items",
        "invoices",
        "invoice_items",
        "payments",
        "payment_attempts",
        "webhook_events",
        "refunds",
        "discounts",
        "discount_usages",
        "approvals",
        "agent_logs",
        "audit_logs",
    }
    inspector = inspect(engine)
    actual_tables = set(inspector.get_table_names())
    missing_tables = expected_tables - actual_tables
    if missing_tables:
        raise AssertionError(f"Missing tables in DB: {missing_tables}")
    print(f"  -> SUCCESS: All {len(expected_tables)} domain tables present in database!")

    # 3. Test User creation & Unique email
    print("\n[Test 3] Testing User creation and Unique Email constraint...")
    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    db = SessionLocal()
    try:
        user1 = User(
            email=test_email,
            hashed_password="hashed_secret_password_123",
            full_name="Test Architect",
            role="admin",
            is_active=True,
        )
        db.add(user1)
        db.commit()
        db.refresh(user1)
        print(f"  -> User created with UUID: {user1.id}")

        # Attempt duplicate email
        duplicate_user = User(
            email=test_email,
            hashed_password="another_password",
            full_name="Duplicate User",
            role="member",
        )
        db.add(duplicate_user)
        try:
            db.commit()
            raise AssertionError("Duplicate email did not raise IntegrityError!")
        except IntegrityError:
            db.rollback()
            print("  -> SUCCESS: Unique email constraint enforced (IntegrityError caught).")

        # Clean up user1
        db.delete(user1)
        db.commit()
    finally:
        db.close()

    # 4. Test Foreign Key Constraint Enforcement
    print("\n[Test 4] Testing Foreign Key Constraints...")
    db = SessionLocal()
    try:
        orphan_plan = Plan(
            product_id=uuid.uuid4(),  # Non-existent product ID
            name="Orphan Plan",
            code=f"ORPHAN_{uuid.uuid4().hex[:6]}",
            price=Decimal("49.99"),
            billing_interval="monthly",
            interval_count=1,
            trial_period_days=0,
            currency="USD",
        )
        db.add(orphan_plan)
        try:
            db.commit()
            raise AssertionError("Foreign key violation did not raise IntegrityError!")
        except IntegrityError:
            db.rollback()
            print("  -> SUCCESS: Foreign key constraint enforced (IntegrityError caught).")
    finally:
        db.close()

    # 5. Test Subscription, Quotation, and Invoice Relationships
    print("\n[Test 5] Testing Product -> Plan -> Customer -> Subscription -> Invoice Flow...")
    db = SessionLocal()
    try:
        # Create Product
        product = Product(
            name="SubNexus AI Platform",
            sku=f"SKU_{uuid.uuid4().hex[:8]}",
            description="Enterprise AI subscription automation",
            is_active=True,
        )
        db.add(product)
        db.commit()
        db.refresh(product)

        # Create Plan
        plan = Plan(
            product_id=product.id,
            name="Pro Tier",
            code=f"PLAN_PRO_{uuid.uuid4().hex[:6]}",
            price=Decimal("99.99"),
            billing_interval="monthly",
            interval_count=1,
            trial_period_days=14,
            currency="USD",
        )
        db.add(plan)
        db.commit()
        db.refresh(plan)

        # Create Customer
        customer = Customer(
            name="Acme Corporation",
            email=f"billing_{uuid.uuid4().hex[:8]}@acme.corp",
            company_name="Acme Corp",
            currency="USD",
            custom_metadata={"industry": "Technology", "segment": "Enterprise"},
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)

        # Create Subscription
        now = datetime.now(timezone.utc)
        subscription = Subscription(
            customer_id=customer.id,
            plan_id=plan.id,
            status="active",
            current_period_start=now,
            current_period_end=now + timedelta(days=30),
            cancel_at_period_end=False,
        )
        db.add(subscription)
        db.commit()
        db.refresh(subscription)

        # Create Subscription Event
        sub_event = SubscriptionEvent(
            subscription_id=subscription.id,
            event_type="activated",
            details={"source": "api_test", "tier": "pro"},
        )
        db.add(sub_event)
        db.commit()

        # Create Invoice for this Subscription
        invoice = Invoice(
            invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}",
            customer_id=customer.id,
            subscription_id=subscription.id,
            status="paid",
            subtotal=Decimal("99.99"),
            discount_amount=Decimal("0.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("99.99"),
            amount_paid=Decimal("99.99"),
            currency="USD",
            paid_at=now,
        )
        db.add(invoice)
        db.commit()
        db.refresh(invoice)

        # Create Invoice Item
        inv_item = InvoiceItem(
            invoice_id=invoice.id,
            product_id=product.id,
            description="Pro Tier Monthly Subscription",
            quantity=1,
            unit_price=Decimal("99.99"),
            total_price=Decimal("99.99"),
        )
        db.add(inv_item)
        db.commit()

        # Verify relationship traversals
        db.refresh(subscription)
        db.refresh(invoice)
        assert len(subscription.invoices) == 1
        assert subscription.invoices[0].id == invoice.id
        assert len(invoice.items) == 1
        assert invoice.customer.company_name == "Acme Corp"
        print("  -> SUCCESS: Subscription, Invoice, and Item relationships verified!")

        # 6. Test Payment and PaymentAttempt Records
        print("\n[Test 6] Testing Payment & PaymentAttempt Records...")
        payment = Payment(
            customer_id=customer.id,
            invoice_id=invoice.id,
            amount=Decimal("99.99"),
            currency="USD",
            status="succeeded",
            payment_method="card",
            gateway="stripe",
            gateway_transaction_id=f"ch_{uuid.uuid4().hex}",
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)

        attempt = PaymentAttempt(
            payment_id=payment.id,
            attempt_number=1,
            status="succeeded",
            gateway_response={"network_status": "approved_by_network"},
        )
        db.add(attempt)
        db.commit()
        db.refresh(payment)
        assert len(payment.attempts) == 1
        print("  -> SUCCESS: Payment and PaymentAttempt successfully linked.")

        # Clean up relationship chain
        db.delete(attempt)
        db.delete(payment)
        db.delete(inv_item)
        db.delete(invoice)
        db.delete(sub_event)
        db.delete(subscription)
        db.delete(customer)
        db.delete(plan)
        db.delete(product)
        db.commit()
    finally:
        db.close()

    # 7. Test Webhook Idempotency Constraint
    print("\n[Test 7] Testing Webhook Idempotency Constraint (gateway, event_id)...")
    db = SessionLocal()
    try:
        shared_event_id = f"evt_{uuid.uuid4().hex}"
        webhook1 = WebhookEvent(
            gateway="stripe",
            event_id=shared_event_id,
            event_type="invoice.paid",
            payload={"id": shared_event_id, "amount": 9999},
            status="processed",
        )
        db.add(webhook1)
        db.commit()
        print(f"  -> Inserted first webhook event: {shared_event_id}")

        # Try duplicate
        duplicate_webhook = WebhookEvent(
            gateway="stripe",
            event_id=shared_event_id,
            event_type="invoice.paid",
            payload={"id": shared_event_id, "duplicate": True},
            status="pending",
        )
        db.add(duplicate_webhook)
        try:
            db.commit()
            raise AssertionError("Duplicate webhook event did not raise IntegrityError!")
        except IntegrityError:
            db.rollback()
            print("  -> SUCCESS: Webhook idempotency constraint enforced (IntegrityError caught).")

        # Clean up webhook1
        db.delete(webhook1)
        db.commit()
    finally:
        db.close()

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY! ARCHITECTURE FULLY VERIFIED.")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
