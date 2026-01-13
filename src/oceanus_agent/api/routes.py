from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from oceanus_agent.config.settings import settings
from oceanus_agent.services.mysql_service import MySQLService

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.app.env,
    )


@router.get("/ready")
async def readiness_check() -> dict[str, str]:
    """Readiness check (database connectivity)."""
    try:
        service = MySQLService(settings.mysql)
        # Just check if we can connect
        async with service.async_session() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database not ready: {str(e)}"
        )
