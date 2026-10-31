from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db

app = FastAPI(
    title="SubscriptIQ API",
    description="AI Powered Subscription Management and Revenue Intelligence",
    version="1.0.0"
)


@app.get("/")
def home():
    return {
        "message": "Welcome to SubscriptIQ API",
        "status": "running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.get("/health/db")
def health_check_db(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "status": "healthy",
        "database": "connected"
    }