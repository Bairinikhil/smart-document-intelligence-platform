from datetime import timedelta
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.security.auth import Permission, decode_principal, encode_access_token


def _settings() -> Settings:
    return Settings(jwt_secret="test-secret", jwt_issuer="test-issuer")


def _token(settings: Settings, roles: list[str]) -> str:
    return encode_access_token(
        settings=settings,
        user_id=uuid4(),
        tenant_id=uuid4(),
        roles=roles,
    )


def test_role_permissions_are_derived_from_verified_claims() -> None:
    settings = _settings()
    principal = decode_principal(_token(settings, ["analyst"]), settings)

    assert principal.can(Permission.CASE_READ)
    assert principal.can(Permission.REVIEW_MANAGE)
    assert not principal.can(Permission.AUDIT_READ)


def test_me_requires_a_bearer_token() -> None:
    client = TestClient(create_app(_settings()))

    response = client.get("/v1/auth/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_me_returns_tenant_and_rbac_context() -> None:
    settings = _settings()
    client = TestClient(create_app(settings))
    token = _token(settings, ["auditor"])

    response = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["roles"] == ["auditor"]
    assert Permission.AUDIT_READ.value in response.json()["permissions"]


def test_me_rejects_a_role_without_case_read_permission() -> None:
    settings = _settings()
    client = TestClient(create_app(settings))
    token = _token(settings, ["unknown-role"])

    response = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403


def test_expired_token_is_rejected() -> None:
    settings = _settings()
    token = encode_access_token(
        settings=settings,
        user_id=uuid4(),
        tenant_id=uuid4(),
        roles=["analyst"],
        expires_delta=timedelta(seconds=-1),
    )
    client = TestClient(create_app(settings))

    response = client.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
