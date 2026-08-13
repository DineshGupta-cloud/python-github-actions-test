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
    ath: float
    fall_pct: float
    bullish_structure: bool


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
        return ScanCandidate(
            symbol=symbol.upper().replace(".NS", ""),
            bullish_structure=bullish_structure,
            **signal,
        )

    def qualifies(self, candidate: ScanCandidate) -> bool:
        fall = abs(candidate.fall_pct)
        return (
            self.settings.min_fall_from_ath <= fall <= self.settings.max_fall_from_ath
            and candidate.bullish_structure
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

        candidates.sort(key=lambda item: abs(item.fall_pct), reverse=True)
        return tuple(candidates[: self.settings.top_results])


def run_scan() -> ScanResult:
    scanner = StockScanner()
    candidates = scanner.scan_universe()
    if not candidates:
        return ScanResult(status="SUCCESS", message="No qualifying stocks found")

    symbols = ", ".join(candidate.symbol for candidate in candidates)
    return ScanResult(
        status="SUCCESS",
        message=f"Found {len(candidates)} qualifying stocks: {symbols}",
        candidates=candidates,
    )
