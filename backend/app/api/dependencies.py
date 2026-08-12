from collections.abc import AsyncIterator

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Provide a request-scoped transaction only when PostgreSQL is configured."""

    database = request.app.state.database
    if not database.configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database is not configured",
        )
    async with database.session_factory() as session:
        yield session
