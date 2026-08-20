import numpy as np
import pandas as pd

from app.services.scanner_service import StockScanner


class FakeMarketData:
    def fetch_daily(self, symbol: str, period: str = "1y"):
        # Deterministic data that satisfies the production scanner rules:
        # 1) EMA9 > EMA25 > EMA99 at the end.
        # 2) Genuine 9/25 bullish crossover within the last 10 sessions.
        # 3) Genuine 25/99 bullish crossover within the last 10 sessions.
        # 4) Spot price is within 10% of EMA99.
        #
        # The final move is intentionally close to EMA99 so the test does not
        # accidentally depend on the old 52-week-fall/reversal condition.
        close = np.array(
            [100.0] * 106
            + [80.0] * 5
            + [110.0] * 9,
            dtype=float,
        )
        high = close + 2.0
        low = close - 2.0
        volume = np.full(len(close), 200_000.0)

        return pd.DataFrame(
            {
                "Close": close,
                "High": high,
                "Low": low,
                "Volume": volume,
            }
        )


def test_scan_symbol_returns_ema_alignment_candidate():
    scanner = StockScanner(market_data=FakeMarketData())
    candidate = scanner.scan_symbol("TEST")

    assert candidate is not None
    assert candidate.symbol == "TEST"
    assert candidate.price == 110.0
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
