import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Python GitHub Actions App"
    environment: str = os.getenv("APP_ENV", "development")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    period: str = os.getenv("SCAN_PERIOD", "1y")
    interval: str = os.getenv("SCAN_INTERVAL", "1d")
    ema_fast: int = int(os.getenv("EMA_FAST", "9"))
    ema_medium: int = int(os.getenv("EMA_MEDIUM", "25"))
    ema_slow: int = int(os.getenv("EMA_SLOW", "99"))
    rsi_period: int = int(os.getenv("RSI_PERIOD", "14"))
    volume_period: int = int(os.getenv("VOLUME_PERIOD", "20"))
    min_fall_percent: float = float(os.getenv("MIN_FALL_PERCENT", "25"))
    min_price: float = float(os.getenv("MIN_PRICE", "20"))
    min_avg_volume: int = int(os.getenv("MIN_AVG_VOLUME", "100000"))
    ema99_distance_percent: float = float(os.getenv("EMA99_DISTANCE_PERCENT", "15"))
    rsi_min: float = float(os.getenv("RSI_MIN", "35"))
    rsi_max: float = float(os.getenv("RSI_MAX", "70"))
    top_results: int = int(os.getenv("TOP_RESULTS", "50"))


def get_settings() -> Settings:
    return Settings()
