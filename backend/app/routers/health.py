from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db.database import engine

router = APIRouter()


@router.get("/api/v1/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={
            "status": "degraded",
            "service": "ai-support-agent",
            "database": "unreachable",
        })
    return {
        "status": "ok",
        "service": "ai-support-agent",
        "database": "ok",
    }
