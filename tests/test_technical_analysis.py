import pandas as pd

from app.services.technical_analysis_service import TechnicalAnalysisService


def sample_data():
    return pd.DataFrame(
        {
            "Close": [100, 102, 98, 105, 110, 108, 115, 120, 118, 125],
            "High": [101, 103, 100, 106, 111, 109, 116, 121, 119, 126],
            "Volume": [1000] * 10,
        }
    )


def test_calculate_adds_ema_and_drawdown_columns():
    result = TechnicalAnalysisService.calculate(sample_data())

    assert {"EMA9", "EMA25", "EMA99", "ATH", "FallPct"}.issubset(result.columns)
    assert result["EMA9"].notna().all()
    assert result["EMA25"].notna().all()
    assert result["EMA99"].notna().all()
    assert result["ATH"].iloc[-1] == 126


def test_latest_signal_contains_expected_values():
    result = TechnicalAnalysisService.calculate(sample_data())
    signal = TechnicalAnalysisService.latest_signal(result)

    assert signal["close"] == 125.0
    assert signal["ath"] == 126.0
    assert signal["fall_pct"] < 0
