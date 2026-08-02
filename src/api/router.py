"""API router aggregating all endpoints."""

from fastapi import APIRouter, Depends

from src.api.health import router as health_router
from src.api.metrics import router as metrics_router
from src.api.scraper import router as scraper_router
from src.config.security import verify_api_key

router = APIRouter()

router.include_router(
    health_router,
    dependencies=[Depends(verify_api_key)],
)

router.include_router(
    metrics_router,
    dependencies=[Depends(verify_api_key)],
)

router.include_router(
    scraper_router,
    dependencies=[Depends(verify_api_key)],
)
