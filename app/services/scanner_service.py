from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.config import get_settings
from app.services.market_data_service import MarketDataService
from app.services.nse_universe import NSE_FNO_SYMBOLS


@dataclass(frozen=True)
class ScanResult:
    status: str
    message: str
    candidates: tuple["ScanCandidate", ...] = ()


@dataclass(frozen=True)
class ScanCandidate:
    symbol: str
    price: float
    high_52w: float
    fall_pct: float
    ema9: float
    ema25: float
    ema99: float
    rsi: float
    volume: int
    avg_volume20: int
    volume_ratio: float
    ema99_distance_pct: float
    ema9_25_cross: bool
    ema25_99_cross: bool
    ema9_above_25: bool
    ema25_above_99: bool
    higher_low: bool
    ema25_rising: bool
    ema99_rising: bool
    score: int
    signal: str


class StockScanner:
    """NSE F&O scanner requiring bullish 9/25 and 25/99 crossover conditions."""

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

    def scan_symbol(self, symbol: str) -> ScanCandidate | None:
        data = self.market_data.fetch_daily(symbol, period=self.settings.period)
        df = data.copy()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        required = {"Close", "High", "Low", "Volume"}
        if not required.issubset(df.columns):
            return None

        df = df.dropna(subset=["Close", "High", "Low", "Volume"])
        if len(df) < self.settings.ema_slow + 20:
            return None

        close = df["Close"]
        df["EMA9"] = close.ewm(span=9, adjust=False).mean()
        df["EMA25"] = close.ewm(span=25, adjust=False).mean()
        df["EMA99"] = close.ewm(span=99, adjust=False).mean()
        df["RSI"] = self._rsi(close, self.settings.rsi_period)
        df["AvgVolume20"] = df["Volume"].rolling(20).mean()

        latest = df.iloc[-1]
        previous = df.iloc[-2]

        price = float(latest["Close"])
        ema9 = float(latest["EMA9"])
        ema25 = float(latest["EMA25"])
        ema99 = float(latest["EMA99"])
        rsi = float(latest["RSI"])
        volume = float(latest["Volume"])
        avg_volume = float(latest["AvgVolume20"])

        high_52w = float(df["High"].max())
        fall_pct = ((high_52w - price) / high_52w) * 100

        # Both bullish crossovers are required.
        bullish_9_25_cross = bool(
            previous["EMA9"] <= previous["EMA25"]
            and latest["EMA9"] > latest["EMA25"]
        )
        bullish_25_99_cross = bool(
            previous["EMA25"] <= previous["EMA99"]
            and latest["EMA25"] > latest["EMA99"]
        )

        ema9_above_25 = ema9 > ema25
        ema25_above_99 = ema25 > ema99
        ema99_distance = abs(price - ema99) / ema99 * 100
        near_ema99 = ema99_distance <= self.settings.ema99_distance_percent

        volume_ratio = volume / avg_volume if avg_volume > 0 else 0
        volume_confirmation = volume_ratio >= 1.2
        rsi_ok = self.settings.rsi_min <= rsi <= self.settings.rsi_max

        recent_low = float(df["Low"].tail(20).min())
        previous_20_low = float(df["Low"].iloc[-40:-20].min())
        higher_low = recent_low > previous_20_low
        ema25_rising = bool(latest["EMA25"] > df["EMA25"].iloc[-6])
        ema99_rising = bool(latest["EMA99"] > df["EMA99"].iloc[-10])

        score = 0
        if fall_pct >= 25: score += 20
        if fall_pct >= 35: score += 5
        if fall_pct >= 50: score += 5
        if ema9_above_25: score += 15
        if bullish_9_25_cross: score += 15
        if ema25_above_99: score += 10
        if bullish_25_99_cross: score += 15
        if near_ema99: score += 5
        if volume_confirmation: score += 5
        if rsi_ok: score += 5
        if higher_low: score += 5
        if ema25_rising: score += 5

        # Only stocks with BOTH bullish crossovers are candidates.
        if not (bullish_9_25_cross and bullish_25_99_cross):
            return None
        if price < self.settings.min_price:
            return None
        if avg_volume < self.settings.min_avg_volume:
            return None
        if fall_pct < self.settings.min_fall_percent:
            return None

        return ScanCandidate(
            symbol=symbol.upper().replace(".NS", ""),
            price=round(price, 2),
            high_52w=round(high_52w, 2),
            fall_pct=round(fall_pct, 2),
            ema9=round(ema9, 2),
            ema25=round(ema25, 2),
            ema99=round(ema99, 2),
            rsi=round(rsi, 2),
            volume=int(volume),
            avg_volume20=int(avg_volume),
            volume_ratio=round(volume_ratio, 2),
            ema99_distance_pct=round(ema99_distance, 2),
            ema9_25_cross=bullish_9_25_cross,
            ema25_99_cross=bullish_25_99_cross,
            ema9_above_25=ema9_above_25,
            ema25_above_99=ema25_above_99,
            higher_low=higher_low,
            ema25_rising=ema25_rising,
            ema99_rising=ema99_rising,
            score=score,
            signal="🔥 9/25/99 BULLISH CROSSOVER",
        )

    def qualifies(self, candidate: ScanCandidate | None) -> bool:
        return candidate is not None

    def scan_universe(self, symbols: list[str] | None = None) -> tuple[ScanCandidate, ...]:
        candidates: list[ScanCandidate] = []
        for symbol in symbols or NSE_FNO_SYMBOLS:
            try:
                candidate = self.scan_symbol(symbol)
                if self.qualifies(candidate):
                    candidates.append(candidate)
            except Exception:
                continue

        candidates.sort(key=lambda item: (item.score, item.fall_pct), reverse=True)
        return tuple(candidates[: self.settings.top_results])


def run_scan() -> ScanResult:
    scanner = StockScanner()
    candidates = scanner.scan_universe()
    if not candidates:
        return ScanResult(status="SUCCESS", message="No stocks matched the 9/25/99 crossover criteria")

    symbols = ", ".join(candidate.symbol for candidate in candidates)
    return ScanResult(
        status="SUCCESS",
        message=f"Found {len(candidates)} stocks with bullish 9/25/99 crossovers: {symbols}",
        candidates=candidates,
    )
