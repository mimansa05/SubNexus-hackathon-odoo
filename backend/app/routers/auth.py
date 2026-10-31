from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

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
    db: Session = Depends(get_db)
):
    return register_user(db, data)


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