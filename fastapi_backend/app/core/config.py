from typing import Set

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # OpenAPI docs
    OPENAPI_URL: str = "/openapi.json"

    # Database
    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None
    EXPIRE_ON_COMMIT: bool = False

    # User
    ACCESS_SECRET_KEY: str
    RESET_PASSWORD_SECRET_KEY: str
    VERIFICATION_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 3600

    #SuperUser
    SUPERUSER_EMAIL: str
    SUPERUSER_PASSWORD: str
    SUPERUSER_FULL_NAME: str = "Super Admin"

    SUPERADMINS: set[str] = set()

    # Clerk
    CLERK_ISSUER: str
    CLERK_EXPECTED_AUD: str
    CLERK_PERMITTED_AZP: str
    CLERK_SECRET_KEY: str
    CLERK_JWKS_URL: str

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # CORS
    # CORS_ORIGINS: Set[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
