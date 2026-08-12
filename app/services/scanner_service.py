from dataclasses import dataclass


@dataclass(frozen=True)
class ScanResult:
    status: str
    message: str


def run_scan() -> ScanResult:
    """Placeholder service for the future NSE scanner."""
    return ScanResult(status="SUCCESS", message="Scan completed successfully")
