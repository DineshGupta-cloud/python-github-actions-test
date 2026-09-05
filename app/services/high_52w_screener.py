from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.config import get_settings
from app.services.market_data_service import MarketDataService
from app.services.nse_universe import NSE_FNO_SYMBOLS


@dataclass(frozen=True)
class High52WCandidate:
    symbol: str
    price: float
    high_52w: float
    below_high_pct: float
    ema20: float
    ema50: float
    rsi: float
    volume: int
    avg_volume20: int
    volume_ratio: float
    score: int
    signal: str


@dataclass(frozen=True)
class High52WScanResult:
    status: str
    message: str
    candidates: tuple[High52WCandidate, ...] = ()


class High52WScreener:
    """52W High momentum screener using the requested strict filters."""

    MAX_BELOW_HIGH_PCT = 15.0
    RSI_MIN = 55.0
    MIN_VOLUME_RATIO = 1.2

    def __init__(self, market_data: MarketDataService | None = None):
        self.market_data = market_data or MarketDataService()
        self.settings = get_settings()

    @staticmethod
    def _rsi(series: pd.Series, period: int) -> pd.Series:
        delta = series.diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, pd.NA)
        return 100 - (100 / (1 + rs))

    def scan_symbol(self, symbol: str) -> High52WCandidate | None:
        data = self.market_data.fetch_daily(symbol, period=self.settings.period)
        df = data.copy()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        required = {"Close", "High", "Volume"}
        if not required.issubset(df.columns):
            return None

        df = df.dropna(subset=["Close", "High", "Volume"])
        if len(df) < 120:
            return None

        close = df["Close"]
        df["EMA20"] = close.ewm(span=20, adjust=False).mean()
        df["EMA50"] = close.ewm(span=50, adjust=False).mean()
        df["RSI"] = self._rsi(close, self.settings.rsi_period)
        df["AvgVolume20"] = df["Volume"].rolling(20).mean()

        latest = df.iloc[-1]
        price = float(latest["Close"])
        ema20 = float(latest["EMA20"])
        ema50 = float(latest["EMA50"])
        rsi = float(latest["RSI"])
        volume = int(float(latest["Volume"]))
        avg_volume = float(latest["AvgVolume20"])

        high_52w = float(df["High"].tail(252).max())
        if high_52w <= 0 or price <= 0 or avg_volume <= 0:
            return None

        below_high_pct = ((high_52w - price) / high_52w) * 100
        volume_ratio = volume / avg_volume

        # EXACT requested screener conditions:
        # Distance from 52W High <= 15%
        # AND Price > EMA20
        # AND Price > EMA50
        # AND EMA20 > EMA50
        # AND RSI > 55
        # AND Volume Ratio > 1.2
        if below_high_pct < 0 or below_high_pct > self.MAX_BELOW_HIGH_PCT:
            return None
        if price <= ema20:
            return None
        if price <= ema50:
            return None
        if ema20 <= ema50:
            return None
        if rsi <= self.RSI_MIN:
            return None
        if volume_ratio <= self.MIN_VOLUME_RATIO:
            return None
        if price < self.settings.min_price or avg_volume < self.settings.min_avg_volume:
            return None

        # Ranking score is secondary; all returned stocks already pass every filter.
        score = 0
        if below_high_pct <= 5:
            score += 30
        elif below_high_pct <= 10:
            score += 20
        else:
            score += 10

        if price > ema20:
            score += 15
        if price > ema50:
            score += 15
        if ema20 > ema50:
            score += 15
        if rsi > 60:
            score += 10
        if volume_ratio > 1.5:
            score += 10
        else:
            score += 5

        signal = "🔥 STRONG 52W HIGH MOMENTUM"
        if below_high_pct <= 5 and rsi > 60 and volume_ratio > 1.5:
            signal = "🚀 52W HIGH BREAKOUT WATCH"

        return High52WCandidate(
            symbol=symbol.upper().replace(".NS", ""),
            price=round(price, 2),
            high_52w=round(high_52w, 2),
            below_high_pct=round(below_high_pct, 2),
            ema20=round(ema20, 2),
            ema50=round(ema50, 2),
            rsi=round(rsi, 2),
            volume=volume,
            avg_volume20=int(avg_volume),
            volume_ratio=round(volume_ratio, 2),
            score=score,
            signal=signal,
        )

    def scan_universe(self, symbols: list[str] | None = None) -> tuple[High52WCandidate, ...]:
        candidates: list[High52WCandidate] = []
        for symbol in symbols or NSE_FNO_SYMBOLS:
            try:
                candidate = self.scan_symbol(symbol)
                if candidate is not None:
                    candidates.append(candidate)
            except Exception:
                continue

        # Closest to 52W high first, then stronger momentum.
        candidates.sort(key=lambda item: (item.below_high_pct, -item.score, -item.volume_ratio))
        return tuple(candidates[: self.settings.top_results])


def run_high_52w_scan() -> High52WScanResult:
    screener = High52WScreener()
    candidates = screener.scan_universe()

    if not candidates:
        return High52WScanResult(
            status="SUCCESS",
            message="No F&O stocks matched all 52W High momentum filters.",
        )

    symbols = ", ".join(candidate.symbol for candidate in candidates)
    return High52WScanResult(
        status="SUCCESS",
        message=f"Found {len(candidates)} stocks matching all 52W High momentum filters: {symbols}",
        candidates=candidates,
    )
