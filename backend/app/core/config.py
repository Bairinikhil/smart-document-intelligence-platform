from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables.

    The database URL is optional during local domain development. Production and
    deployed environments must provide it explicitly through secret configuration.
    """

    model_config = SettingsConfigDict(
        env_prefix="SDI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Smart Document Intelligence API"
    environment: str = "development"
    service_version: str = "0.2.0"
    database_url: str | None = None
    db_pool_size: int = 5
    db_max_overflow: int = 10


@lru_cache
def get_settings() -> Settings:
    return Settings()
