import numpy as np
import pandas as pd

from app.services.scanner_service import StockScanner


class FakeMarketData:
    def fetch_daily(self, symbol: str, period: str = "1y"):
        close = np.array([100.0] * 60 + [200.0] * 20 + [140.0] * 40)
        high = np.maximum(close + 2, 200.0)
        low = close - 2
        volume = np.array([200_000.0] * len(close))
        return pd.DataFrame({"Close": close, "High": high, "Low": low, "Volume": volume})


def test_scan_symbol_returns_reversal_candidate():
    scanner = StockScanner(market_data=FakeMarketData())
    candidate = scanner.scan_symbol("TEST")

    assert candidate is not None
    assert candidate.symbol == "TEST"
    assert candidate.price == 140.0
    assert candidate.high_52w == 202.0
    assert candidate.fall_pct > 25
    assert candidate.ema9 > 0
    assert candidate.ema25 > 0
    assert candidate.ema99 > 0
    assert candidate.rsi >= 0
    assert candidate.avg_volume20 >= 100_000
    assert candidate.score >= 20


def test_qualifies_accepts_filtered_candidate():
    scanner = StockScanner(market_data=FakeMarketData())
    candidate = scanner.scan_symbol("TEST")

    assert scanner.qualifies(candidate) is True


def test_scan_universe_returns_tuple_and_handles_multiple_symbols():
    scanner = StockScanner(market_data=FakeMarketData())
    results = scanner.scan_universe(["AAA", "BBB"])

    assert isinstance(results, tuple)
    assert len(results) == 2
    assert {item.symbol for item in results} == {"AAA", "BBB"}
