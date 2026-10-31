from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class CurrencyAmount(BaseModel):
    currency: str
    amount: Decimal


class AnalyticsOverviewResponse(BaseModel):
    as_of: datetime
    period_start: date
    period_end: date
    mrr: list[CurrencyAmount]
    arr: list[CurrencyAmount]
    collected_revenue: list[CurrencyAmount]
    outstanding_revenue: list[CurrencyAmount]
    active_subscriptions: int
    overdue_invoices: int


class RevenuePoint(BaseModel):
    date: date
    amount: Decimal


class RevenueSeries(BaseModel):
    currency: str
    total: Decimal
    values: list[RevenuePoint]


class RevenueResponse(BaseModel):
    start_date: date
    end_date: date
    series: list[RevenueSeries]


class RecurringRevenueResponse(BaseModel):
    as_of: datetime
    metric: Literal["mrr", "arr"]
    values: list[CurrencyAmount]


class ChurnResponse(BaseModel):
    period: Literal["month", "quarter", "year"]
    period_start: datetime
    period_end: datetime
    definition: str
    starting_subscriptions: int
    canceled_subscriptions: int
    churn_rate_percent: Decimal


class SubscriptionStatusCount(BaseModel):
    status: str
    count: int


class SubscriptionAnalyticsResponse(BaseModel):
    as_of: datetime
    active_count: int
    active_statuses: list[str]
    status_counts: list[SubscriptionStatusCount]


class OutstandingResponse(BaseModel):
    as_of: datetime
    outstanding_revenue: list[CurrencyAmount]
    overdue_revenue: list[CurrencyAmount]
    overdue_invoices: int


class RankedCustomer(BaseModel):
    rank: int
    customer_id: UUID
    name: str
    email: str
    currency: str
    collected_revenue: Decimal


class TopCustomersResponse(BaseModel):
    start_date: date
    end_date: date
    ranked_by: Literal["collected_revenue"]
    customers: list[RankedCustomer]


class RankedPlan(BaseModel):
    rank: int
    plan_id: UUID
    name: str
    currency: str
    monthly_recurring_revenue: Decimal


class TopPlansResponse(BaseModel):
    as_of: datetime
    ranked_by: Literal["monthly_recurring_revenue"]
    plans: list[RankedPlan]
