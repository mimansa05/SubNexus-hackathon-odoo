from fastapi import APIRouter, Depends

from app.core.dependencies import require_staff_or_admin
from app.models.user import User
from app.schemas.churn import (
    ChurnPredictionRequest,
    ChurnPredictionResponse
)
from app.services.churn_service import predict_customer_churn


router = APIRouter(
    prefix="/api/v1/churn",
    tags=["Churn Prediction"]
)


@router.post(
    "/predict",
    response_model=ChurnPredictionResponse
)
def predict_churn(
    data: ChurnPredictionRequest,
    user: User = Depends(require_staff_or_admin)
):
    """
    Predict churn probability for a subscription customer.
    Accessible to Admin and Staff.
    """

    return predict_customer_churn(data)
