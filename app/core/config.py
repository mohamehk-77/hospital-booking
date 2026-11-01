from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(env_file=".env")

    @field_validator("DATABASE_URL")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        # Some hosts still hand out the legacy postgres:// scheme.
        if value.startswith("postgres://"):
            value = "postgresql://" + value[len("postgres://") :]
        # Use psycopg 3 everywhere (it has ARM wheels for Oracle's free tier).
        if value.startswith("postgresql://"):
            return "postgresql+psycopg://" + value[len("postgresql://") :]
        return value


settings = Settings()
