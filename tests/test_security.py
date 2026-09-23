"""Security module tests."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException

from src.config.security import add_cors_middleware, verify_api_key


def test_verify_api_key_with_valid_key() -> None:
    """Verify verify_api_key passes with correct key."""
    with patch("src.config.security.get_settings") as mock_settings:
        mock_settings.return_value.api_key = "secret-key"
        mock_request = MagicMock()
        mock_request.headers = {"X-API-Key": "secret-key"}
        verify_api_key(mock_request)


def test_verify_api_key_with_invalid_key() -> None:
    """Verify verify_api_key raises HTTPException with wrong key."""
    with patch("src.config.security.get_settings") as mock_settings:
        mock_settings.return_value.api_key = "secret-key"
        mock_request = MagicMock()
        mock_request.headers = {"X-API-Key": "wrong-key"}
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(mock_request)
    assert exc_info.value.status_code == 401


def test_verify_api_key_with_missing_key() -> None:
    """Verify verify_api_key raises HTTPException when key is missing."""
    with patch("src.config.security.get_settings") as mock_settings:
        mock_settings.return_value.api_key = "secret-key"
        mock_request = MagicMock()
        mock_request.headers = {}
        with pytest.raises(HTTPException) as exc_info:
            verify_api_key(mock_request)
    assert exc_info.value.status_code == 401


def test_verify_api_key_no_api_key_set() -> None:
    """Verify verify_api_key passes when API_KEY is not set."""
    with patch("src.config.security.get_settings") as mock_settings:
        mock_settings.return_value.api_key = ""
        mock_request = MagicMock()
        mock_request.headers = {}
        verify_api_key(mock_request)


def test_add_cors_middleware() -> None:
    """Verify add_cors_middleware adds CORS middleware to app."""
    app = FastAPI()
    add_cors_middleware(app)
    assert len(app.user_middleware) > 0
