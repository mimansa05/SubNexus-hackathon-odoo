from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import require_staff_or_admin
from app.database.db import get_db
from app.models.user import User
from app.schemas.orchestrator import OrchestrationExecutionResponse, OrchestrationPlanResponse, OrchestrationRequest
from app.services.orchestrator_service import create_plan, execute_plan

router = APIRouter(prefix="/api/v1/orchestrator", tags=["AI Orchestrator"])


@router.post("/plan", response_model=OrchestrationPlanResponse)
def plan(data: OrchestrationRequest, db: Session = Depends(get_db), user: User = Depends(require_staff_or_admin)):
    return create_plan(db, user, data.request)


@router.post("/tasks/{task_id}/execute", response_model=OrchestrationExecutionResponse)
def execute(task_id: UUID, db: Session = Depends(get_db), user: User = Depends(require_staff_or_admin)):
    return execute_plan(db, user, task_id)
