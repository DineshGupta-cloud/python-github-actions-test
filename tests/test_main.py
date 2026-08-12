from pathlib import Path
import importlib.util


# Load app/main.py directly so tests work consistently on Windows, Linux,
# local machines, and GitHub-hosted runners without relying on PYTHONPATH.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAIN_FILE = PROJECT_ROOT / "app" / "main.py"

spec = importlib.util.spec_from_file_location("app_main", MAIN_FILE)
if spec is None or spec.loader is None:
    raise ImportError(f"Unable to load application module: {MAIN_FILE}")

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
add = module.add


def test_add():
    assert add(2, 3) == 5


def test_add_negative():
    assert add(-2, 3) == 1
