import numpy as np
import pandas as pd

from app.services.scanner_service import StockScanner


class FakeMarketData:
    def fetch_daily(self, symbol: str, period: str = "1y"):
        # Build a deterministic setup where BOTH genuine bullish crossovers
        # happen within the last 10 trading sessions and the final order is:
        # EMA9 > EMA25 > EMA99.
        # 100 -> 90 creates the temporary bearish separation, then 130 creates
        # the bullish reversal. The final price is within 10% of EMA99.
        close = np.concatenate([
            np.full(100, 100.0),
            np.full(5, 90.0),
            np.full(15, 130.0),
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
    assert candidate.price == 130.0
    assert candidate.ema9 > candidate.ema25 > candidate.ema99
    assert candidate.ema9_above_25 is True
    assert candidate.ema25_above_99 is True
    assert candidate.ema9_25_cross is True
    assert candidate.ema25_99_cross is True
    assert candidate.ema99_distance_pct <= 10.0
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
