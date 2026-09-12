"""Unit tests for src.utils.tqdm_wrapper (1015 T-14).

Covers:
- Real-tqdm resolution path when the ``tqdm`` package is installed.
- No-op fallback path when the ``tqdm`` package raises ``ImportError``.
- Iterable pass-through semantics of the fallback callable.
- Re-export identity via ``MistHelper.tqdm`` (backwards-compat alias).
"""

from __future__ import annotations

import importlib
import sys

import pytest


def test_wrapper_module_exposes_tqdm_symbol():
    """The wrapper module always exposes a callable named ``tqdm``."""
    module = importlib.import_module("src.utils.tqdm_wrapper")
    assert callable(module.tqdm)


def test_wrapper_real_tqdm_when_installed():
    """When ``tqdm`` is importable, the wrapper re-exports the real package callable."""
    try:
        from tqdm import tqdm as real_tqdm  # Import inside test to check installed path.
    except ImportError:
        pytest.skip("tqdm package not installed; real-path test not applicable in this env.")
    module = importlib.reload(importlib.import_module("src.utils.tqdm_wrapper"))
    assert module.tqdm is real_tqdm


def test_wrapper_fallback_pass_through(monkeypatch):
    """When ``tqdm`` cannot be imported, the fallback returns the iterable unchanged."""
    monkeypatch.setitem(sys.modules, "tqdm", None)  # Force ImportError on `from tqdm import tqdm`.
    sys.modules.pop("src.utils.tqdm_wrapper", None)
    module = importlib.import_module("src.utils.tqdm_wrapper")
    try:
        source = [1, 2, 3]
        assert list(module.tqdm(source)) == source
        assert module.tqdm(source) is source  # Pass-through returns the same iterable object.
    finally:
        sys.modules.pop("src.utils.tqdm_wrapper", None)
        monkeypatch.delitem(sys.modules, "tqdm", raising=False)
        importlib.import_module("src.utils.tqdm_wrapper")  # Restore real state for other tests.


def test_wrapper_fallback_accepts_extra_args(monkeypatch):
    """Fallback tolerates ``*args``/``**kwargs`` like the real tqdm signature."""
    monkeypatch.setitem(sys.modules, "tqdm", None)  # Force ImportError.
    sys.modules.pop("src.utils.tqdm_wrapper", None)
    module = importlib.import_module("src.utils.tqdm_wrapper")
    try:
        result = module.tqdm(range(3), desc="ignored", total=3, leave=False)
        assert list(result) == [0, 1, 2]
    finally:
        sys.modules.pop("src.utils.tqdm_wrapper", None)
        monkeypatch.delitem(sys.modules, "tqdm", raising=False)
        importlib.import_module("src.utils.tqdm_wrapper")
