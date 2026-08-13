from __future__ import annotations

import pandas as pd


class TechnicalAnalysisService:
    """Calculate EMA and drawdown metrics for scanner candidates."""

    @staticmethod
    def calculate(data: pd.DataFrame) -> pd.DataFrame:
        result = data.copy()
        result["EMA9"] = result["Close"].ewm(span=9, adjust=False).mean()
        result["EMA25"] = result["Close"].ewm(span=25, adjust=False).mean()
        result["EMA99"] = result["Close"].ewm(span=99, adjust=False).mean()
        result["ATH"] = result["High"].cummax()
        result["FallPct"] = ((result["Close"] - result["ATH"]) / result["ATH"]) * 100
        return result

    @staticmethod
    def latest_signal(data: pd.DataFrame) -> dict:
        latest = data.iloc[-1]
        return {
            "close": float(latest["Close"]),
            "ema9": float(latest["EMA9"]),
            "ema25": float(latest["EMA25"]),
            "ema99": float(latest["EMA99"]),
            "ath": float(latest["ATH"]),
            "fall_pct": float(latest["FallPct"]),
        }
