import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "INQ - Campus Queue Management System"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"

    # Database Configuration (Defaults to SQLite; supports PostgreSQL via DATABASE_URL)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./inq.db")

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
