import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Python GitHub Actions App"
    environment: str = os.getenv("APP_ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")


def get_settings() -> Settings:
    return Settings()
