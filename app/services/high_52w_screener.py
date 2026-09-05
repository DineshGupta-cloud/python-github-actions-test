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
    ema9: float
    ema25: float
    ema99: float
    rsi: float
    volume: int
    avg_volume20: int
    volume_ratio: float
    ema9_above_25: bool
    ema25_above_99: bool
    ema9_25_cross: bool
    ema25_99_cross: bool
    ema25_rising: bool
    ema99_rising: bool
    score: int
    signal: str


@dataclass(frozen=True)
class High52WScanResult:
    status: str
    message: str
    candidates: tuple[High52WCandidate, ...] = ()


class High52WScreener:
    """Independent screener for stocks trading within 15% of their 52-week high."""

    LOOKBACK_DAYS = 10
    MAX_BELOW_HIGH_PCT = 15.0

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

    @staticmethod
    def _recent_bullish_cross(
        df: pd.DataFrame, fast: str, slow: str, lookback: int = 10
    ) -> bool:
        start = max(1, len(df) - lookback)
        for i in range(start, len(df)):
            if (
                float(df[fast].iloc[i - 1]) <= float(df[slow].iloc[i - 1])
                and float(df[fast].iloc[i]) > float(df[slow].iloc[i])
            ):
                return True
        return False

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
        df["EMA9"] = close.ewm(span=9, adjust=False).mean()
        df["EMA25"] = close.ewm(span=25, adjust=False).mean()
        df["EMA99"] = close.ewm(span=99, adjust=False).mean()
        df["RSI"] = self._rsi(close, self.settings.rsi_period)
        df["AvgVolume20"] = df["Volume"].rolling(20).mean()

        latest = df.iloc[-1]
        price = float(latest["Close"])
        ema9 = float(latest["EMA9"])
        ema25 = float(latest["EMA25"])
        ema99 = float(latest["EMA99"])
        rsi = float(latest["RSI"])
        volume = int(float(latest["Volume"]))
        avg_volume = float(latest["AvgVolume20"])

        # Use the highest daily high in the available one-year dataset as the 52W high.
        high_52w = float(df["High"].tail(252).max())
        if high_52w <= 0 or price <= 0:
            return None

        below_high_pct = ((high_52w - price) / high_52w) * 100

        # Main screener condition: price is at or above 85% of the 52W high.
        if below_high_pct < 0 or below_high_pct > self.MAX_BELOW_HIGH_PCT:
            return None

        ema9_above_25 = ema9 > ema25
        ema25_above_99 = ema25 > ema99
        ema9_25_cross = self._recent_bullish_cross(df, "EMA9", "EMA25", self.LOOKBACK_DAYS)
        ema25_99_cross = self._recent_bullish_cross(df, "EMA25", "EMA99", self.LOOKBACK_DAYS)
        ema25_rising = bool(ema25 > float(df["EMA25"].iloc[-6]))
        ema99_rising = bool(ema99 > float(df["EMA99"].iloc[-10]))
        volume_ratio = volume / avg_volume if avg_volume > 0 else 0.0

        # Momentum score, while the 15% distance filter remains mandatory.
        score = 0
        if below_high_pct <= 5:
            score += 30
        elif below_high_pct <= 10:
            score += 20
        else:
            score += 10
        if ema9_above_25:
            score += 10
        if ema25_above_99:
            score += 10
        if ema9_25_cross:
            score += 10
        if ema25_99_cross:
            score += 10
        if ema25_rising:
            score += 5
        if ema99_rising:
            score += 5
        if volume_ratio >= 1.2:
            score += 5
        if self.settings.rsi_min <= rsi <= self.settings.rsi_max:
            score += 5

        if price < self.settings.min_price or avg_volume < self.settings.min_avg_volume:
            return None

        signal = "🚀 NEAR 52W HIGH"
        if below_high_pct <= 5 and ema9_above_25 and ema25_above_99:
            signal = "🔥 STRONG 52W HIGH BREAKOUT SETUP"
        elif ema9_above_25 and ema25_above_99:
            signal = "📈 52W HIGH BULLISH TREND"

        return High52WCandidate(
            symbol=symbol.upper().replace(".NS", ""),
            price=round(price, 2),
            high_52w=round(high_52w, 2),
            below_high_pct=round(below_high_pct, 2),
            ema9=round(ema9, 2),
            ema25=round(ema25, 2),
            ema99=round(ema99, 2),
            rsi=round(rsi, 2),
            volume=volume,
            avg_volume20=int(avg_volume),
            volume_ratio=round(volume_ratio, 2),
            ema9_above_25=ema9_above_25,
            ema25_above_99=ema25_above_99,
            ema9_25_cross=ema9_25_cross,
            ema25_99_cross=ema25_99_cross,
            ema25_rising=ema25_rising,
            ema99_rising=ema99_rising,
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

        # Closest to 52W high first, then stronger technical score.
        candidates.sort(key=lambda item: (item.below_high_pct, -item.score, -item.volume_ratio))
        return tuple(candidates[: self.settings.top_results])


def run_high_52w_scan() -> High52WScanResult:
    screener = High52WScreener()
    candidates = screener.scan_universe()

    if not candidates:
        return High52WScanResult(
            status="SUCCESS",
            message="No F&O stocks are currently within 15% of their 52-week high.",
        )

    symbols = ", ".join(candidate.symbol for candidate in candidates)
    return High52WScanResult(
        status="SUCCESS",
        message=f"Found {len(candidates)} stocks within 15% of their 52-week high: {symbols}",
        candidates=candidates,
    )
