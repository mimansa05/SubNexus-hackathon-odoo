from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_email_token
)
from sqlalchemy import select
from fastapi import HTTPException, status

from app.models.user import User
from app.core.security import hash_password
from app.schemas.auth import StaffCreateRequest

def register_user(db: Session, data: RegisterRequest):

    # Check if email already exists
    existing_user = db.scalar(
        select(User).where(User.email == str(data.email).lower())
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Create new customer (must confirm email before first login)
    new_user = User(
        full_name=data.full_name,
        email=str(data.email).lower(),
        hashed_password=hash_password(data.password),
        role="customer",
        email_verified=False
    )

    db.add(new_user)

    try:
        db.commit()
        db.refresh(new_user)
    except Exception:
        db.rollback()
        raise

    return new_user


def verify_email(db: Session, token: str):
    user_id = decode_email_token(token)
    user = db.get(User, user_id) if user_id else None

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This confirmation link is invalid or has expired"
        )

    if not user.email_verified:
        user.email_verified = True
        db.commit()

    return {"message": "Email confirmed. You can now sign in."}


def login_user(db: Session, data: LoginRequest):

    user = db.scalar(
        select(User).where(User.email == str(data.email).lower())
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

    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please confirm your email first. Check your inbox for the confirmation link."
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
