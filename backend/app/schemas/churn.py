from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


class ChurnPredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tenure_months: int = Field(ge=1, le=600)
    monthly_charges: float = Field(gt=0, le=1000000)
    payment_failures_90d: int = Field(ge=0, le=100)
    days_since_last_payment: int = Field(ge=0, le=3650)
    support_tickets_90d: int = Field(ge=0, le=1000)
    usage_sessions_30d: int = Field(ge=0, le=10000)
    plan_type: Literal["Basic", "Standard", "Premium"]
    discount_used: int = Field(ge=0, le=1)
    renewal_count: int = Field(ge=0, le=1000)
    auto_renew: int = Field(ge=0, le=1)
    late_payment_count: int = Field(ge=0, le=1000)


class ChurnPredictionResponse(BaseModel):
    churn_probability: float
    churn_percentage: float
    risk_level: Literal["Low", "Medium", "High"]
    recommendation: str
    model_version: str
