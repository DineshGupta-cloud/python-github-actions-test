from __future__ import annotations

import pandas as pd


class TechnicalAnalysisService:
    """Calculate EMA/SMA crossover and drawdown metrics."""

    @staticmethod
    def calculate(data: pd.DataFrame) -> pd.DataFrame:
        result = data.copy()
        result["EMA9"] = result["Close"].ewm(span=9, adjust=False).mean()
        result["EMA25"] = result["Close"].ewm(span=25, adjust=False).mean()
        result["EMA99"] = result["Close"].ewm(span=99, adjust=False).mean()
        result["SMA25"] = result["Close"].rolling(25).mean()
        result["SMA99"] = result["Close"].rolling(99).mean()
        result["ATH"] = result["High"].cummax()
        result["FallPct"] = ((result["Close"] - result["ATH"]) / result["ATH"]) * 100

        result["EMA9Cross25"] = (
            (result["EMA9"] > result["EMA25"])
            & (result["EMA9"].shift(1) <= result["EMA25"].shift(1))
        )
        result["SMA25Cross99"] = (
            (result["SMA25"] > result["SMA99"])
            & (result["SMA25"].shift(1) <= result["SMA99"].shift(1))
        )
        return result

    @staticmethod
    def latest_signal(data: pd.DataFrame) -> dict:
        latest = data.iloc[-1]
        return {
            "close": float(latest["Close"]),
            "ema9": float(latest["EMA9"]),
            "ema25": float(latest["EMA25"]),
            "ema99": float(latest["EMA99"]),
            "sma25": float(latest["SMA25"]) if pd.notna(latest["SMA25"]) else None,
            "sma99": float(latest["SMA99"]) if pd.notna(latest["SMA99"]) else None,
            "ath": float(latest["ATH"]),
            "fall_pct": float(latest["FallPct"]),
            "ema9_cross_25": bool(latest["EMA9Cross25"]),
            "sma25_cross_99": bool(latest["SMA25Cross99"]),
        }
