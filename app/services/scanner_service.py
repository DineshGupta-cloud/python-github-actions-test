from __future__ import annotations

from dataclasses import dataclass

from app.config import get_settings
from app.services.market_data_service import MarketDataService
from app.services.technical_analysis_service import TechnicalAnalysisService


@dataclass(frozen=True)
class ScanResult:
    status: str
    message: str


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


def run_scan() -> ScanResult:
    """Health-check entry point; stock universe scanning is added next."""
    return ScanResult(status="SUCCESS", message="Scanner service ready")
