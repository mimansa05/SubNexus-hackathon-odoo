from fastapi import FastAPI

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