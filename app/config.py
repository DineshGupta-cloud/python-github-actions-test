import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Python GitHub Actions App"
    environment: str = os.getenv("APP_ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    min_fall_from_ath: float = float(os.getenv("MIN_FALL_FROM_ATH", "50"))
    max_fall_from_ath: float = float(os.getenv("MAX_FALL_FROM_ATH", "80"))
    top_results: int = int(os.getenv("TOP_RESULTS", "10"))
    ema_fast: int = 9
    ema_medium: int = 25
    ema_slow: int = 99


def get_settings() -> Settings:
    return Settings()
