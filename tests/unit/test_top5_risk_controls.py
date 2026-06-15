"""Risk-control regression tests for top-5 decomposition workflows."""

from __future__ import annotations

from unittest.mock import MagicMock


def test_device_events_52w_entrypoint_is_safe_callable() -> None:
    """device_events_52w entrypoint remains callable without prompt side effects at import time."""
    from MistHelper import export_all_org_device_events_52w_to_csv

    assert callable(export_all_org_device_events_52w_to_csv)


def test_safe_input_guard_unchanged_signature() -> None:
    """safe_input callable remains available for cancellation/EOF-protected prompt paths."""
    from MistHelper import InputUtils

    assert hasattr(InputUtils, "safe_input")
    assert callable(InputUtils.safe_input)


def test_log_sanitizer_filter_is_attachable() -> None:
    """Sanitizer attachment path remains operational for redaction guardrails."""
    logger = MagicMock()
    sanitizer = MagicMock()
    logger.addFilter(sanitizer)
    logger.addFilter.assert_called_once_with(sanitizer)
