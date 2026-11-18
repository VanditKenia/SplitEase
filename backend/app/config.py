from functools import lru_cache
from typing import Annotated, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration, read from environment variables or backend/.env (TRD.md §8)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    supabase_url: str
    supabase_jwt_audience: str = "authenticated"
    # NoDecode: read "a,b" as a plain string so the validator below can split it.
    cors_origins: Annotated[list[str], NoDecode] = []
    env: Literal["dev", "prod"] = "dev"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: str | list[str]) -> list[str]:
        origins = value.split(",") if isinstance(value, str) else value
        origins = [origin.strip() for origin in origins if origin.strip()]
        if "*" in origins:
            raise ValueError("CORS_ORIGINS must list explicit origins, not '*'")
        return origins

    @property
    def is_dev(self) -> bool:
        return self.env == "dev"


@lru_cache
def get_settings() -> Settings:
    return Settings()
