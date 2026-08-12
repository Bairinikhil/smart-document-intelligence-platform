from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings


class Permission(StrEnum):
    CASE_READ = "case:read"
    CASE_WRITE = "case:write"
    DOCUMENT_READ = "document:read"
    DOCUMENT_WRITE = "document:write"
    REVIEW_MANAGE = "review:manage"
    AUDIT_READ = "audit:read"
    ADMIN = "admin"


ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    "customer": frozenset({Permission.CASE_READ, Permission.DOCUMENT_WRITE}),
    "analyst": frozenset(
        {
            Permission.CASE_READ,
            Permission.CASE_WRITE,
            Permission.DOCUMENT_READ,
            Permission.REVIEW_MANAGE,
        }
    ),
    "officer": frozenset(
        {
            Permission.CASE_READ,
            Permission.CASE_WRITE,
            Permission.DOCUMENT_READ,
            Permission.REVIEW_MANAGE,
        }
    ),
    "auditor": frozenset({Permission.CASE_READ, Permission.DOCUMENT_READ, Permission.AUDIT_READ}),
    "admin": frozenset(Permission),
}


@dataclass(frozen=True)
class Principal:
    """Authenticated caller context carried through the request boundary."""

    user_id: UUID
    tenant_id: UUID
    subject: str
    roles: frozenset[str]
    permissions: frozenset[Permission]

    def can(self, permission: Permission) -> bool:
        return Permission.ADMIN in self.permissions or permission in self.permissions


class AuthenticationError(ValueError):
    """Raised when a token cannot establish an authenticated principal."""


bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str = "invalid authentication credentials") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _as_uuid(value: Any, claim: str) -> UUID:
    try:
        return UUID(str(value))
    except (AttributeError, TypeError, ValueError) as exc:
        raise AuthenticationError(f"invalid {claim} claim") from exc


def encode_access_token(
    *,
    settings: Settings,
    user_id: UUID,
    tenant_id: UUID,
    roles: list[str],
    subject: str | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed access token for the future identity service.

    This helper is deliberately not exposed as an HTTP login endpoint. Credential
    issuance belongs to the client identity provider integration.
    """

    now = datetime.now(timezone.utc)
    expires = now + (expires_delta or timedelta(minutes=settings.access_token_ttl_minutes))
    payload = {
        "sub": subject or str(user_id),
        "user_id": str(user_id),
        "tenant_id": str(tenant_id),
        "roles": roles,
        "iss": settings.jwt_issuer,
        "iat": now,
        "exp": expires,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_principal(token: str, settings: Settings) -> Principal:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            options={"require": ["exp", "iat", "iss", "sub", "tenant_id"]},
        )
        subject = str(payload["sub"])
        user_id = _as_uuid(payload.get("user_id", subject), "user_id")
        tenant_id = _as_uuid(payload["tenant_id"], "tenant_id")
        raw_roles = payload.get("roles", [])
        if not isinstance(raw_roles, list) or not all(isinstance(role, str) for role in raw_roles):
            raise AuthenticationError("invalid roles claim")
        roles = frozenset(raw_roles)
        permissions = frozenset(
            permission for role in roles for permission in ROLE_PERMISSIONS.get(role, frozenset())
        )
        return Principal(
            user_id=user_id,
            tenant_id=tenant_id,
            subject=subject,
            roles=roles,
            permissions=permissions,
        )
    except (jwt.PyJWTError, KeyError, AuthenticationError) as exc:
        raise AuthenticationError("invalid authentication credentials") from exc


async def get_current_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> Principal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    try:
        return decode_principal(credentials.credentials, request.app.state.settings)
    except AuthenticationError as exc:
        raise _unauthorized(str(exc)) from exc


def require_permission(permission: Permission):
    async def dependency(
        principal: Principal = Depends(get_current_principal),
    ) -> Principal:
        if not principal.can(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="insufficient permissions",
            )
        return principal

    return dependency


async def get_tenant_id(
    principal: Principal = Depends(get_current_principal),
) -> UUID:
    """Return tenant scope only from verified token claims."""

    return principal.tenant_id
