"""Health check endpoint tests."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")

from unittest.mock import patch

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_health_check() -> None:
    """Verify health endpoint returns healthy status."""
    with patch("src.config.security.get_settings") as mock_settings:
        mock_settings.return_value.api_key = ""
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
