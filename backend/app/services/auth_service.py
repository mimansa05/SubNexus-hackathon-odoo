from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.user import User
from app.core.security import hash_password
from app.schemas.auth import StaffCreateRequest

def register_user(db: Session, data: RegisterRequest):

    # Check if email already exists
    existing_user = db.scalar(
        select(User).where(User.email == data.email)
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Create new customer
    new_user = User(
        full_name=data.name,
        email=str(data.email),
        hashed_password=hash_password(data.password),
        role="customer"
    )

    db.add(new_user)

    try:
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        raise

    return new_user


def login_user(db: Session, data: LoginRequest):

    user = db.scalar(
        select(User).where(User.email == data.email)
    )

    if not user or not verify_password(
        data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    token = create_access_token({
        "sub": str(user.id)
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }

def create_staff(db: Session, data):

    existing_user = db.scalar(
        select(User).where(User.email == data.email)
    )

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    staff = User(
        full_name=data.name,
        email=str(data.email),
        hashed_password=hash_password(data.password),
        role="staff"
    )

    db.add(staff)

    try:
        db.commit()
        db.refresh(staff)
    except Exception:
        db.rollback()
        raise

    return staff


def create_staff(db, data: StaffCreateRequest):

    # Check whether email already exists
    existing_user = db.scalar(
        select(User).where(User.email == data.email)
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Create staff account
    staff = User(
        full_name=data.full_name,
        email=data.email,
        hashed_password=hash_password(data.password),
        role="staff",
        is_active=True
    )

    db.add(staff)
    db.commit()
    db.refresh(staff)

    return staff
