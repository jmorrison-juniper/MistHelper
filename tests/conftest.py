"""Pytest configuration for MistHelper test suite.

Provides test isolation: temp directories, no network, no .env loading.
Unit tests must run offline with zero API credentials in under 30 seconds.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

# Pre-load MistHelper.py (the script) into sys.modules as "MistHelper".
# The project root has an __init__.py which makes the root directory a Python
# package — so `import MistHelper` would normally resolve to __init__.py (empty).
# We force-replace the module in sys.modules with the actual MistHelper.py script.
_mh_path = Path(__file__).parents[1] / "MistHelper.py"
_existing = sys.modules.get("MistHelper")
_is_init = _existing is not None and getattr(_existing, "__file__", "").endswith("__init__.py")
if _mh_path.exists() and (_existing is None or _is_init):
    _spec = importlib.util.spec_from_file_location("MistHelper", _mh_path)
    _mod = importlib.util.module_from_spec(_spec)  # type: ignore[assignment]
    sys.modules["MistHelper"] = _mod
    try:
        _spec.loader.exec_module(_mod)  # type: ignore[union-attr]
    except SystemExit:
        pass  # MistHelper.py calls sys.exit(); ignore during import
    except (ImportError, ModuleNotFoundError):
        pass  # Missing dependencies (e.g., mistapi); tests for src/ still work


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Provide a temporary data directory for test file output."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def tmp_jsonl_file(tmp_data_dir):
    """Provide a temporary JSONL file path for telemetry tests."""
    return str(tmp_data_dir / "test_events.jsonl")


@pytest.fixture(autouse=True)
def isolate_working_directory(tmp_path, monkeypatch):
    """Ensure tests never write to the real data/ directory."""
    monkeypatch.chdir(tmp_path)
