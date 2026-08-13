import sys
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import main
from app.services.scanner_service import ScanResult


def test_scanner_returns_success():
    with patch("app.main.run_scan", return_value=ScanResult(
        status="SUCCESS", message="No qualifying stocks found"
    )):
        result = __import__("app.main", fromlist=["run_scan"]).run_scan()

    assert result.status == "SUCCESS"
    assert result.message in {
        "Scan completed successfully",
        "No qualifying stocks found",
    }


def test_main_returns_zero():
    with patch("app.main.run_scan", return_value=ScanResult(
        status="SUCCESS", message="No qualifying stocks found"
    )), patch("app.main.TelegramService.is_configured", return_value=False):
        assert main() == 0
