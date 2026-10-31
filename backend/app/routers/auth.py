from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.email import send_verification_email
from app.core.security import create_email_token
from app.schemas.auth import ResendRequest, VerifyEmailRequest
from app.services.auth_service import verify_email

from app.core.dependencies import require_admin
from app.schemas.auth import StaffCreateRequest
from app.services.auth_service import create_staff
from app.database.db import get_db
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse
)
from app.services.auth_service import register_user, login_user
from app.core.dependencies import get_current_user
from app.models.user import User


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)


# Register
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register(
    data: RegisterRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db)
):
    user = register_user(db, data)
    background.add_task(
        send_verification_email, user.email, user.full_name, create_email_token(str(user.id))
    )
    return user


# Confirm email (link in the confirmation email)
@router.post("/verify-email")
def confirm_email(data: VerifyEmailRequest, db: Session = Depends(get_db)):
    return verify_email(db, data.token)


# Resend confirmation email. Always answers the same, so it cannot be used to probe accounts.
@router.post("/resend-verification")
def resend_verification(
    data: ResendRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db)
):
    user = db.scalar(select(User).where(User.email == str(data.email).lower()))
    if user and not user.email_verified:
        background.add_task(
            send_verification_email, user.email, user.full_name, create_email_token(str(user.id))
        )
    return {"message": "If that account is awaiting confirmation, a new email has been sent."}


# Login
@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    return login_user(db, data)


# Get logged-in user
@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user

@router.post(
    "/staff",
    response_model=UserResponse,
    status_code=201
)
def register_staff(
    data: StaffCreateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return create_staff(db, data)