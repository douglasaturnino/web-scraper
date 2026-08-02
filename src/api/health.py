"""Health check endpoint."""

from fastapi import APIRouter

from src.schemas.scraper import HealthCheckResponse

router = APIRouter()


@router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> dict[str, str]:
    """Return service health status.

    Returns:
        dict[str, str]: Health status response.
    """
    return {"status": "healthy"}
