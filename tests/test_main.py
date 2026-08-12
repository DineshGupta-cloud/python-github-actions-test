import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.main import main
from app.services.scanner_service import run_scan


def test_scanner_returns_success():
    result = run_scan()
    assert result.status == "SUCCESS"
    assert result.message == "Scan completed successfully"


def test_main_returns_zero():
    assert main() == 0
