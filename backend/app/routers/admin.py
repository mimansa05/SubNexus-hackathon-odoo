
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.schemas.auth import StaffCreateRequest, UserResponse
from app.services.auth_service import create_staff

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin"]
)


@router.get("/dashboard")
def admin_dashboard(
    current_user: User = Depends(require_admin)
):
    return {
        "message": "Welcome Admin!",
        "email": current_user.email,
        "role": current_user.role
    }


@router.post(
    "/staff",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_staff(
    data: StaffCreateRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    return create_staff(db, data)
