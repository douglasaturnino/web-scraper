"""FastAPI application entrypoint."""

from fastapi import FastAPI

from src.api.router import router as api_router
from src.config.logger import configure_logging
from src.config.security import add_cors_middleware
from src.config.settings import get_settings
from src.schemas.scraper import HealthCheckResponse

settings = get_settings()
configure_logging()

app = FastAPI(title="Job Scraper Service", version="0.1.0")

add_cors_middleware(app)

app.include_router(api_router)


@app.get("/health", response_model=HealthCheckResponse)
async def health_check() -> dict[str, str]:
    """Return service health status."""
    return {"status": "healthy"}
