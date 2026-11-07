import logging

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from src.db import Session
from src.routers.match import redis

health_router = APIRouter()


@health_router.get("/healthz", include_in_schema=False)
async def healthz() -> dict:
    """Liveness: the process answers. Depends on nothing else, so an outage of
    Postgres or Redis doesn't restart every pod."""
    return {"status": "ok"}


@health_router.get("/readyz", include_in_schema=False)
async def readyz(response: Response) -> dict:
    """Readiness: Postgres and Redis both answer."""
    checks = {"postgres": True, "redis": True}
    try:
        async with Session() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        logging.exception("Readiness check failed for Postgres")
        checks["postgres"] = False
    try:
        await redis.ping()
    except Exception:
        logging.exception("Readiness check failed for Redis")
        checks["redis"] = False

    if not all(checks.values()):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return checks
