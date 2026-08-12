from fastapi import Depends, FastAPI, HTTPException, Request, status

from app.core.config import Settings, get_settings
from app.db.session import Database
from app.security.auth import Permission, Principal, require_permission


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or get_settings()
    database = Database(runtime_settings)
    application = FastAPI(
        title=runtime_settings.app_name,
        version=runtime_settings.service_version,
        description="BFSI document intake and intelligence platform",
    )
    application.state.database = database
    application.state.settings = runtime_settings

    @application.get("/v1/health/live", tags=["health"])
    def liveness() -> dict[str, str]:
        """Return success when the API process is able to serve requests."""

        return {"status": "ok"}

    @application.get("/v1/health/ready", tags=["health"])
    async def readiness(request: Request) -> dict[str, str]:
        """Report whether configured dependencies can serve requests."""

        runtime_database: Database = request.app.state.database
        if not runtime_database.configured:
            return {"status": "ok", "database": "not_configured"}
        if not await runtime_database.ping():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"status": "unavailable", "database": "unreachable"},
            )
        return {"status": "ok", "database": "ok"}

    @application.get("/v1/auth/me", tags=["identity"])
    async def current_user(
        principal: Principal = Depends(require_permission(Permission.CASE_READ)),
    ) -> dict[str, object]:
        """Return the masked identity and authorization context for the caller."""

        return {
            "user_id": str(principal.user_id),
            "tenant_id": str(principal.tenant_id),
            "subject": principal.subject,
            "roles": sorted(principal.roles),
            "permissions": sorted(permission.value for permission in principal.permissions),
        }

    return application


app = create_app()
