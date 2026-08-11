from fastapi import FastAPI

app = FastAPI(
    title="Smart Document Intelligence API",
    version="0.1.0",
    description="BFSI document intake and intelligence platform",
)


@app.get("/v1/health/live", tags=["health"])
def liveness() -> dict[str, str]:
    """Return success when the API process is able to serve requests."""

    return {"status": "ok"}


@app.get("/v1/health/ready", tags=["health"])
def readiness() -> dict[str, str]:
    """Dependency checks will be added with the persistence slice."""

    return {"status": "ok", "dependencies": "not_configured"}
