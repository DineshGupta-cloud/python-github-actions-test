import pandas as pd

from app.services.scanner_service import ScanCandidate, StockScanner


class FakeMarketData:
    def fetch_daily(self, symbol: str):
        return pd.DataFrame(
            {
                "Close": [100 + i for i in range(120)],
                "High": [101 + i for i in range(120)],
                "Volume": [1000] * 120,
            }
        )


def test_scan_symbol_returns_candidate():
    scanner = StockScanner(market_data=FakeMarketData())
    candidate = scanner.scan_symbol("TEST")

    assert candidate.symbol == "TEST"
    assert candidate.close == 219.0
    assert candidate.ema9 > 0
    assert candidate.ema25 > 0
    assert candidate.ema99 > 0
    assert candidate.ath == 220.0


def test_qualifies_requires_bullish_structure_and_fall_range():
    scanner = StockScanner(market_data=FakeMarketData())
    candidate = ScanCandidate(
        symbol="TEST",
        close=30,
        ema9=32,
        ema25=31,
        ema99=29,
        ath=100,
        fall_pct=-70,
        bullish_structure=True,
    )

    assert scanner.qualifies(candidate) is True
