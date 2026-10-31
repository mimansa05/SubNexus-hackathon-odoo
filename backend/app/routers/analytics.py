from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_staff_or_admin
from app.database.db import get_db
from app.models.user import User
from app.schemas.analytics import (
    AnalyticsOverviewResponse,
    ChurnResponse,
    OutstandingResponse,
    RecurringRevenueResponse,
    RevenueResponse,
    SubscriptionAnalyticsResponse,
    TopCustomersResponse,
    TopPlansResponse,
)
from app.services.analytics_service import (
    analytics_overview,
    churn_analytics,
    outstanding_analytics,
    recurring_revenue,
    revenue_analytics,
    subscription_analytics,
    top_customers,
    top_plans,
)


router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def overview(
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
):
    return analytics_overview(db)


@router.get("/revenue", response_model=RevenueResponse)
def revenue(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
):
    return revenue_analytics(db, start_date, end_date)


@router.get("/mrr", response_model=RecurringRevenueResponse)
def mrr(
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
):
    return recurring_revenue(db)


@router.get("/arr", response_model=RecurringRevenueResponse)
def arr(
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
):
    return recurring_revenue(db, annualized=True)


@router.get("/churn", response_model=ChurnResponse)
def churn(
    period: Literal["month", "quarter", "year"] = Query("month"),
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
):
    return churn_analytics(db, period)


@router.get("/subscriptions", response_model=SubscriptionAnalyticsResponse)
def subscriptions(
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
):
    return subscription_analytics(db)


@router.get("/outstanding", response_model=OutstandingResponse)
def outstanding(
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
):
    return outstanding_analytics(db)


@router.get("/top-customers", response_model=TopCustomersResponse)
def customers(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
):
    return top_customers(db, start_date, end_date, limit)


@router.get("/top-plans", response_model=TopPlansResponse)
def plans(
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_staff_or_admin),
):
    return top_plans(db, limit)
