from app.routers.discounts import router as discounts_router
from app.routers.analytics import router as analytics_router
from app.routers.reconciliation import router as reconciliation_router
from app.routers.payments import router as payments_router
from app.routers.invoices import router as invoices_router
from app.routers.quotations import router as quotations_router
from app.routers.subscriptions import router as subscriptions_router
from app.routers.plans import router as plans_router
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import Depends

from app.database.db import get_db
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router

from app.routers.admin import router as admin_router
from app.routers.customers import router as customers_router
from app.routers.products import router as products_router
from app.routers.governance import router as governance_router

# app = FastAPI(...) ke baad


# 1. First create FastAPI app
app = FastAPI(
    title="SubNexus",
    description="AI Powered Subscription Management and Revenue Intelligence",
    version="1.0.0"
)


# 2. Then include routers
app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(admin_router)
app.include_router(customers_router)
app.include_router(products_router)

# 3. Home route
@app.get("/")
def home():
    return {
        "message": "Welcome to SubNexus",
        "status": "running"
    }


# 4. Health route
@app.get("/health")
def health_check():
    return {"status": "healthy"}


# 5. Database health
@app.get("/health/database")
def database_health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "connected"}
app.include_router(plans_router)

app.include_router(subscriptions_router)

app.include_router(quotations_router)

app.include_router(invoices_router)

app.include_router(payments_router)

app.include_router(discounts_router)
app.include_router(reconciliation_router)
app.include_router(analytics_router)
app.include_router(governance_router)
