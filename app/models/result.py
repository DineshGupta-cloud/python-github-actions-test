from dataclasses import dataclass


@dataclass(frozen=True)
class ApplicationResult:
    success: bool
    message: str
