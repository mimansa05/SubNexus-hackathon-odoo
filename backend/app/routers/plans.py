from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.core.dependencies import require_staff_or_admin

from app.schemas.plan import (
    PlanCreate,
    PlanUpdate,
    PlanResponse
)

from app.services.plan_service import (
    create_plan,
    get_plans,
    get_plan,
    update_plan,
    deactivate_plan
)


router = APIRouter(
    prefix="/api/v1/plans",
    tags=["Plans"]
)


@router.post(
    "/",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED
)
def create(
    data: PlanCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return create_plan(db, data)


@router.get("/", response_model=list[PlanResponse])
def list_all(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    search: str | None = None,
    product_id: UUID | None = None,
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return get_plans(
        db, skip, limit, search, product_id, active_only
    )


@router.get("/{plan_id}", response_model=PlanResponse)
def get_one(
    plan_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return get_plan(db, plan_id)


@router.patch("/{plan_id}", response_model=PlanResponse)
def update(
    plan_id: UUID,
    data: PlanUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return update_plan(db, plan_id, data)


@router.delete("/{plan_id}")
def delete(
    plan_id: UUID,
    db: Session = Depends(get_db),
    current_user=Depends(require_staff_or_admin)
):
    return deactivate_plan(db, plan_id)
