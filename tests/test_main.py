import sys
from pathlib import Path

# Make the repository root importable in every environment.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import add


def test_add():
    assert add(2, 3) == 5


def test_add_negative():
    assert add(-2, 3) == 1
