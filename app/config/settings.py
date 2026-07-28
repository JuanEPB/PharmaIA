from pathlib import Path
import os

from dotenv import load_dotenv


PROJECT_DIR = Path(__file__).resolve().parents[2]

load_dotenv(PROJECT_DIR / ".env")


class Settings:

    DB_HOST = os.getenv(
        "DB_HOST",
        "127.0.0.1",
    )

    DB_PORT = int(
        os.getenv(
            "DB_PORT",
            "3306",
        )
    )

    DB_NAME = os.getenv(
        "DB_NAME",
        "pharmacontrol",
    )

    DB_USER = os.getenv(
        "DB_USER",
        "root",
    )

    DB_PASSWORD = os.getenv(
        "DB_PASSWORD",
        "",
    )

    DEBUG = (
        os.getenv(
            "DEBUG",
            "True",
        ).lower()
        == "true"
    )

    CORS_ALLOW_ORIGINS = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ALLOW_ORIGINS",
            "*",
        ).split(",")
        if origin.strip()
    ]

    ENVIRONMENT = os.getenv(
        "ENVIRONMENT",
        "development",
    ).strip().lower()

    API_KEYS = {
        api_key.strip()
        for api_key in os.getenv(
            "API_KEYS",
            "",
        ).split(",")
        if api_key.strip()
    }

    PUBLIC_PATHS = {
        "/",
        "/auth/login",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
    }

    @property
    def AUTH_ENABLED(self) -> bool:
        return self.ENVIRONMENT in {
            "production",
            "prod",
        } or bool(self.API_KEYS)


settings = Settings()
