from __future__ import annotations

from dataclasses import dataclass

from app.config import get_settings
from app.services.market_data_service import MarketDataService
from app.services.nse_universe import NSE_FNO_SYMBOLS
from app.services.technical_analysis_service import TechnicalAnalysisService


@dataclass(frozen=True)
class ScanResult:
    status: str
    message: str
    candidates: tuple["ScanCandidate", ...] = ()


@dataclass(frozen=True)
class ScanCandidate:
    symbol: str
    close: float
    ema9: float
    ema25: float
    ema99: float
    sma25: float | None
    sma99: float | None
    ath: float
    fall_pct: float
    bullish_structure: bool
    sma25_cross_99: bool
    crossover_price: float | None
    price_above_crossover_pct: float | None


class StockScanner:
    def __init__(self, market_data: MarketDataService | None = None):
        self.market_data = market_data or MarketDataService()
        self.analysis = TechnicalAnalysisService()
        self.settings = get_settings()

    def scan_symbol(self, symbol: str) -> ScanCandidate:
        data = self.market_data.fetch_daily(symbol)
        analyzed = self.analysis.calculate(data)
        signal = self.analysis.latest_signal(analyzed)

        bullish_structure = signal["ema9"] > signal["ema25"] > signal["ema99"]

        crossover_rows = analyzed.loc[analyzed["SMA25Cross99"] == True]
        crossover_price = None
        price_above_crossover_pct = None

        if not crossover_rows.empty:
            crossover = crossover_rows.iloc[-1]
            crossover_price = float(crossover["Close"])
            price_above_crossover_pct = (
                (signal["close"] - crossover_price) / crossover_price * 100
            )

        return ScanCandidate(
            symbol=symbol.upper().replace(".NS", ""),
            bullish_structure=bullish_structure,
            sma25_cross_99=signal["sma25_cross_99"],
            crossover_price=crossover_price,
            price_above_crossover_pct=price_above_crossover_pct,
            **signal,
        )

    def qualifies(self, candidate: ScanCandidate) -> bool:
        # Primary scanner condition:
        # SMA 25 crosses above SMA 99 and current price is not more
        # than 10% above the price on the most recent crossover candle.
        if candidate.crossover_price is None:
            return False

        if candidate.price_above_crossover_pct is None:
            return False

        return (
            candidate.sma25_cross_99
            and 0 <= candidate.price_above_crossover_pct <= 10
        )

    def scan_universe(self, symbols: list[str] | None = None) -> tuple[ScanCandidate, ...]:
        candidates: list[ScanCandidate] = []
        for symbol in symbols or NSE_FNO_SYMBOLS:
            try:
                candidate = self.scan_symbol(symbol)
                if self.qualifies(candidate):
                    candidates.append(candidate)
            except Exception:
                # One bad ticker/data response must not stop the entire scan.
                continue

        candidates.sort(
            key=lambda item: item.price_above_crossover_pct
            if item.price_above_crossover_pct is not None
            else 999
        )
        return tuple(candidates[: self.settings.top_results])


def run_scan() -> ScanResult:
    scanner = StockScanner()
    candidates = scanner.scan_universe()
    if not candidates:
        return ScanResult(status="SUCCESS", message="No SMA25/SMA99 crossover stocks found")

    symbols = ", ".join(candidate.symbol for candidate in candidates)
    return ScanResult(
        status="SUCCESS",
        message=f"Found {len(candidates)} SMA25/SMA99 crossover stocks: {symbols}",
        candidates=candidates,
    )
