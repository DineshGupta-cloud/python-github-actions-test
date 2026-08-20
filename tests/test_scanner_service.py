import numpy as np
import pandas as pd

from app.services.scanner_service import StockScanner


class FakeMarketData:
    def fetch_daily(self, symbol: str, period: str = "1y"):
        # Deliberately creates EMA9 > EMA25 > EMA99 at the end.
        # The final section has small pullbacks so RSI remains valid.
        i = np.arange(120, dtype=float)
        close = np.concatenate([
            np.full(80, 100.0),
            100.0 + (i[80:] - 80) * 1.0 + 2.0 * np.sin(i[80:]),
        ])
        high = close + 2.0
        low = close - 2.0
        volume = np.full(len(close), 200_000.0)
        return pd.DataFrame({"Close": close, "High": high, "Low": low, "Volume": volume})


def test_scan_symbol_returns_ema_alignment_candidate():
    scanner = StockScanner(market_data=FakeMarketData())
    candidate = scanner.scan_symbol("TEST")

    assert candidate is not None
    assert candidate.symbol == "TEST"
    assert candidate.price > 100.0
    assert candidate.ema9 > candidate.ema25 > candidate.ema99
    assert candidate.ema9_above_25 is True
    assert candidate.ema25_above_99 is True
    assert candidate.rsi >= 0
    assert candidate.avg_volume20 >= 100_000


def test_qualifies_accepts_ema_aligned_candidate():
    scanner = StockScanner(market_data=FakeMarketData())
    candidate = scanner.scan_symbol("TEST")

    assert scanner.qualifies(candidate) is True


def test_scan_universe_returns_tuple_and_handles_multiple_symbols():
    scanner = StockScanner(market_data=FakeMarketData())
    results = scanner.scan_universe(["AAA", "BBB"])

    assert isinstance(results, tuple)
    assert len(results) == 2
    assert {item.symbol for item in results} == {"AAA", "BBB"}
