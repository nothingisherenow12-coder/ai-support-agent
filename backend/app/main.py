from fastapi import FastAPI
from app.routers import health

app=FastAPI(
    title="AI Support & Operations Agent",
    version="0.1.0",
    description="backend API for the AI Support & Operations Agent")

app.include_router(health.router)