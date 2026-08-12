from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_readiness_is_explicit_when_database_is_not_configured() -> None:
    client = TestClient(create_app(Settings(database_url=None)))

    response = client.get("/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "not_configured"}


def test_liveness_does_not_require_database() -> None:
    client = TestClient(create_app(Settings(database_url=None)))

    response = client.get("/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
