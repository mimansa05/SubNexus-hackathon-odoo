from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate


def create_customer(db: Session, data: CustomerCreate):

    existing_customer = db.scalar(
        select(Customer).where(Customer.email == data.email)
    )

    if existing_customer:
        raise HTTPException(
            status_code=409,
            detail="Customer with this email already exists"
        )

    customer = Customer(**data.model_dump())

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def get_customers(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    search: str | None = None
):

    query = select(Customer)

    if search:
        search_term = f"%{search}%"

        query = query.where(
            or_(
                Customer.name.ilike(search_term),
                Customer.email.ilike(search_term),
                Customer.company_name.ilike(search_term)
            )
        )

    query = query.order_by(Customer.created_at.desc())
    query = query.offset(skip).limit(limit)

    return db.scalars(query).all()


def get_customer(db: Session, customer_id: UUID):

    customer = db.get(Customer, customer_id)

    if not customer:
        raise HTTPException(
            status_code=404,
            detail="Customer not found"
        )

    return customer


def update_customer(
    db: Session,
    customer_id: UUID,
    data: CustomerUpdate
):

    customer = get_customer(db, customer_id)

    update_data = data.model_dump(exclude_unset=True)

    if "email" in update_data:
        existing = db.scalar(
            select(Customer).where(
                Customer.email == update_data["email"],
                Customer.id != customer_id
            )
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="Email already belongs to another customer"
            )

    for key, value in update_data.items():
        setattr(customer, key, value)

    db.commit()
    db.refresh(customer)

    return customer


def delete_customer(db: Session, customer_id: UUID):

    customer = get_customer(db, customer_id)

    # Do not delete customers with financial or subscription history.
    if (
        customer.subscriptions
        or customer.quotations
        or customer.invoices
        or customer.payments
    ):
        raise HTTPException(
            status_code=409,
            detail="Cannot delete customer with existing business records"
        )

    db.delete(customer)
    db.commit()

    return {"message": "Customer deleted successfully"}