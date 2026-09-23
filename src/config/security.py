"""Security configuration for the internal API."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.config.settings import get_settings


def get_api_key() -> str:
    """Return the expected API key from settings.

    Returns:
        str: The API key.
    """
    return get_settings().api_key


def verify_api_key(request: Request) -> None:
    """Verify the API key in the request header.

    Args:
        request (Request): Incoming HTTP request.

    Raises:
        HTTPException: If the API key is missing or invalid.
    """
    api_key = get_api_key()
    if not api_key:
        return

    provided_key = request.headers.get("X-API-Key")
    if provided_key != api_key:
        logger.warning("Invalid API key provided")
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
        )


def add_cors_middleware(app: FastAPI) -> None:
    """Add CORS middleware to the FastAPI application.

    Args:
        app (FastAPI): FastAPI application instance.
    """
    settings = get_settings()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
