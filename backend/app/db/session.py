from collections.abc import AsyncIterator

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings


class Database:
    """Lazy async database resources with an explicit unconfigured state."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    @property
    def configured(self) -> bool:
        return bool(self.settings.database_url)

    @property
    def engine(self) -> AsyncEngine:
        if not self.settings.database_url:
            raise RuntimeError("SDI_DATABASE_URL is not configured")
        if self._engine is None:
            self._engine = create_async_engine(
                self.settings.database_url,
                pool_size=self.settings.db_pool_size,
                max_overflow=self.settings.db_max_overflow,
                pool_pre_ping=True,
            )
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker[AsyncSession]:
        if self._session_factory is None:
            self._session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        return self._session_factory

    async def ping(self) -> bool:
        if not self.configured:
            return False
        try:
            async with self.engine.connect() as connection:
                await connection.execute(text("SELECT 1"))
            return True
        except (SQLAlchemyError, OSError):
            return False

    async def session(self) -> AsyncIterator[AsyncSession]:
        async with self.session_factory() as session:
            yield session

    async def dispose(self) -> None:
        if self._engine is not None:
            await self._engine.dispose()
