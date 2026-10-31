from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi import Depends

from app.database.db import get_db
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router


# 1. First create FastAPI app
app = FastAPI(
    title="SubNexus",
    description="AI Powered Subscription Management and Revenue Intelligence",
    version="1.0.0"
)


# 2. Then include routers
app.include_router(auth_router)
app.include_router(admin_router)


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