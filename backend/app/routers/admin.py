from fastapi import APIRouter, Depends
from app.core.dependencies import require_admin

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["Admin"]
)

@router.get("/dashboard")
def admin_dashboard(
    current_user=Depends(require_admin)
):
    return {
        "message": "Welcome Admin!",
        "email": current_user.email,
        "role": current_user.role
    }