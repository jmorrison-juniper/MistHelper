"""Unit tests for src.refactors.marvis_data_utils.

Wave 13 P2 coverage lift — MarvisDataUtilsFactory.instance() is a
lazy singleton that wires escape/flatten callables from MistHelper's
DataProcessingUtils. Cover cold construction, warm cache-hit, and
attribute wiring to close the 65% gap in one file.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on older type checkers

import sys  # WHY: patch.dict(sys.modules) to inject a fake MistHelper module
from unittest.mock import MagicMock, patch  # WHY: MagicMock stubs + patch for module swap

import src.refactors.marvis_data_utils as marvis_module  # WHY: reset _instance between test cases


def _install_fake_misthelper() -> MagicMock:
    """Return a MagicMock stand-in for MistHelper with DataProcessingUtils wired."""
    fake = MagicMock()  # WHY: MagicMock accepts arbitrary attribute lookups
    fake.DataProcessingUtils = MagicMock()  # WHY: DataProcessingUtils exposes the two callables
    fake.DataProcessingUtils.escape_multiline = MagicMock()  # WHY: escape_fn argument
    fake.DataProcessingUtils.flatten_nested_fields = MagicMock()  # WHY: flatten_fn argument
    return fake  # WHY: caller patches sys.modules["MistHelper"] with this handle


def _reset_singleton() -> None:
    """Reset the module-level singleton cache so tests remain independent."""
    marvis_module.MarvisDataUtilsFactory._instance = None  # WHY: force a cold construction path


def test_instance_returns_wired_marvis_data_utils() -> None:
    """First instance() call constructs a MarvisDataUtils with escape/flatten wired from MistHelper."""
    _reset_singleton()  # WHY: start from a cold cache
    fake_mh = _install_fake_misthelper()
    with patch.dict(sys.modules, {"MistHelper": fake_mh}):
        with patch("src.refactors.marvis_data_utils.MarvisDataUtils") as marvis_cls:
            marvis_cls.return_value = MagicMock(name="wired_marvis_instance")  # WHY: return distinctive instance
            result = marvis_module.MarvisDataUtilsFactory.instance()  # WHY: cold path builds the instance
    assert result is marvis_cls.return_value  # WHY: factory returns the constructed instance
    marvis_cls.assert_called_once()  # WHY: cold path constructs exactly once
    kwargs = marvis_cls.call_args.kwargs
    assert kwargs["escape_fn"] is fake_mh.DataProcessingUtils.escape_multiline  # WHY: escape callable wired
    assert kwargs["flatten_fn"] is fake_mh.DataProcessingUtils.flatten_nested_fields  # WHY: flatten wired


def test_instance_returns_cached_singleton_on_second_call() -> None:
    """Subsequent instance() calls return the cached singleton without re-wiring MistHelper."""
    _reset_singleton()  # WHY: start from a cold cache so first call builds fresh
    fake_mh = _install_fake_misthelper()
    with patch.dict(sys.modules, {"MistHelper": fake_mh}):
        with patch("src.refactors.marvis_data_utils.MarvisDataUtils") as marvis_cls:
            first = marvis_module.MarvisDataUtilsFactory.instance()  # WHY: cold construction
            second = marvis_module.MarvisDataUtilsFactory.instance()  # WHY: warm cache-hit
    assert first is second  # WHY: singleton identity preserved
    marvis_cls.assert_called_once()  # WHY: cached path skips re-construction
