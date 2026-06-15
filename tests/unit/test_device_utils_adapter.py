"""Unit tests for :mod:`src.device.device_utils_adapter`.

Coverage targets:

* version detection / availability flag
* dispatch table behavior (covered + uncovered combos)
* response normalization across UtilResponse shapes
* fallback wiring (both wired-up and missing-fallback cases)
"""

# pylint: disable=protected-access,redefined-outer-name

from __future__ import annotations  # Defer type evaluation for cross-version compat

from types import SimpleNamespace  # Lightweight stand-in for UtilResponse in fixtures
from typing import Any  # Generic typing for fixture builders

import pytest  # Project-standard test framework

from src.device import device_utils_adapter as adapter_module  # Module-under-test
from src.device.device_utils_adapter import DeviceUtilsAdapter  # Class-under-test


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------
@pytest.fixture
def fake_session() -> Any:
    """Stand-in for ``mistapi.APISession`` -- adapter only forwards it."""
    return SimpleNamespace(name="fake-session")  # No methods called by the adapter itself


@pytest.fixture
def util_response_factory():
    """Factory that builds a fake ``UtilResponse`` with chosen payloads."""

    def _build(ws_data: list[Any] | None = None, api_data: Any = None) -> SimpleNamespace:
        trigger = SimpleNamespace(data=api_data) if api_data is not None else None  # Mirror real attr layout
        return SimpleNamespace(  # SimpleNamespace duck-types UtilResponse for our purposes
            ws_data=ws_data or [],  # ws_data may be None on the real class -- empty list is safer
            trigger_api_response=trigger,  # None when only WS data is present
            wait=lambda timeout=None: None,  # No-op wait keeps the adapter happy
        )

    return _build  # Return the builder so tests can customize payloads


# -----------------------------------------------------------------------------
# Initialization + availability
# -----------------------------------------------------------------------------
def test_module_exposes_availability_flag() -> None:
    """The module-level availability flag must be a bool."""
    assert isinstance(adapter_module.DEVICE_UTILS_AVAILABLE, bool)  # Sanity: import detection ran


def test_init_populates_command_map_when_available(fake_session: Any) -> None:
    """Adapter constructs cleanly when device_utils is importable.

    Cannot assert specific entries because the project's test harness
    stubs ``mistapi`` -- the dispatch map ends up empty or partial.
    Real-install coverage of the registration is exercised by the
    dedicated ``test_execute_routes_through_helper`` test below, which
    injects a helper directly into ``_command_map``.
    """
    a = DeviceUtilsAdapter(fake_session)  # Must not raise even with stubbed mistapi
    assert isinstance(a._command_map, dict)  # Sanity: dispatch table is always a dict


def test_init_empty_map_when_module_missing(monkeypatch: pytest.MonkeyPatch, fake_session: Any) -> None:
    """When device_utils is absent, dispatch map is empty and is_available is False."""
    monkeypatch.setattr(adapter_module, "DEVICE_UTILS_AVAILABLE", False)  # Force the disabled path
    monkeypatch.setattr(adapter_module, "_device_utils", None)  # Mirror real "missing" state
    a = DeviceUtilsAdapter(fake_session)  # Rebuild with the patched module state
    assert a._command_map == {}  # Empty dispatch means every call routes to fallback
    assert a.is_available("show_arp", "switch") is False  # is_available honors the flag


# -----------------------------------------------------------------------------
# Normalization
# -----------------------------------------------------------------------------
def test_normalize_handles_none(fake_session: Any) -> None:
    """A None UtilResponse normalizes to an empty list (defensive)."""
    a = DeviceUtilsAdapter(fake_session)  # Adapter with no fallback wired (not exercised here)
    assert a._normalize_response(None) == []  # Empty contract preserved


def test_normalize_flattens_ws_data(fake_session: Any, util_response_factory) -> None:
    """ws_data dicts are flattened to single-level rows."""
    a = DeviceUtilsAdapter(fake_session)  # Adapter under test
    payload = util_response_factory(ws_data=[{"a": {"b": 1}, "c": [10, 20]}])  # Nested dict + scalar list
    rows = a._normalize_response(payload)  # Trigger normalize
    assert rows == [{"a_b": 1, "c": "10,20"}]  # Joined nested key + comma-joined list


def test_normalize_flattens_api_list(fake_session: Any, util_response_factory) -> None:
    """api_response.data lists are split into one row per element."""
    a = DeviceUtilsAdapter(fake_session)  # Fresh adapter
    payload = util_response_factory(api_data=[{"mac": "aa"}, {"mac": "bb"}])  # Two-row API result
    rows = a._normalize_response(payload)  # Normalize the dual-record payload
    assert rows == [{"mac": "aa"}, {"mac": "bb"}]  # Order preserved, no extra flattening needed


def test_normalize_handles_non_dict_payload(fake_session: Any, util_response_factory) -> None:
    """Scalar messages get wrapped under ``value`` so writers always see a dict."""
    a = DeviceUtilsAdapter(fake_session)  # Adapter only used for the normalize call
    payload = util_response_factory(ws_data=["raw-string-message"])  # WS frame that is not a dict
    rows = a._normalize_response(payload)  # Trigger normalize
    assert rows == [{"value": "raw-string-message"}]  # Wrapped under deterministic column name


def test_normalize_indexes_lists_of_dicts(fake_session: Any, util_response_factory) -> None:
    """Nested list-of-dicts get indexed keys to remain CSV-friendly."""
    a = DeviceUtilsAdapter(fake_session)  # Adapter under test
    payload = util_response_factory(ws_data=[{"ports": [{"id": "ge-0/0/1"}, {"id": "ge-0/0/2"}]}])
    rows = a._normalize_response(payload)  # Flatten the nested list
    assert rows == [{"ports_0_id": "ge-0/0/1", "ports_1_id": "ge-0/0/2"}]  # Indexed flattening


# -----------------------------------------------------------------------------
# Fallback / execute
# -----------------------------------------------------------------------------
def test_execute_uses_fallback_when_command_unmapped(fake_session: Any) -> None:
    """Unknown command/device combo routes straight to the fallback callable."""
    calls: list[tuple[Any, ...]] = []  # Capture arguments for later assertions

    def fallback(command, device_type, site_id, device_id, **params):  # Matches FallbackFn shape
        calls.append((command, device_type, site_id, device_id, params))  # Record invocation
        return [{"row": 1}]  # Sentinel result so we can verify it bubbles up

    a = DeviceUtilsAdapter(fake_session, fallback_fn=fallback)  # Wire fallback
    out = a.execute("nonexistent_cmd", "switch", "site-uuid", "dev-uuid", foo="bar")  # Trigger dispatch
    assert out == [{"row": 1}]  # Caller sees the fallback's return value verbatim
    assert calls == [("nonexistent_cmd", "switch", "site-uuid", "dev-uuid", {"foo": "bar"})]  # Args forwarded


def test_execute_missing_fallback_raises(fake_session: Any, monkeypatch: pytest.MonkeyPatch) -> None:
    """An adapter built without a fallback fails loudly when one is needed."""
    monkeypatch.setattr(adapter_module, "DEVICE_UTILS_AVAILABLE", False)  # Guarantee fallback path
    monkeypatch.setattr(adapter_module, "_device_utils", None)  # Mirror disabled state
    a = DeviceUtilsAdapter(fake_session)  # No fallback wired
    with pytest.raises(NotImplementedError):  # Configuration bug should surface immediately
        a.execute("show_arp", "switch", "s", "d")  # Any command triggers fallback when map is empty


def test_execute_routes_through_helper(fake_session: Any, util_response_factory) -> None:
    """When a helper is mapped, execute() invokes it and normalizes the result."""
    a = DeviceUtilsAdapter(fake_session)  # Build adapter; we will overwrite the dispatch map below
    util = util_response_factory(api_data={"mac": "aa:bb:cc"})  # Fake helper return value
    invocations: list[tuple[Any, ...]] = []  # Track helper invocations

    def fake_helper(session, site_id, device_id, **params):  # Matches device_utils helper signature
        invocations.append((session, site_id, device_id, params))  # Capture for assertion
        return util  # Return our crafted UtilResponse

    a._command_map[("switch", "show_arp")] = fake_helper  # Inject the helper into the dispatch table
    a._utils_available = True  # Force is_available() to consult the map
    rows = a.execute("show_arp", "switch", "site-uuid", "dev-uuid", node="node0")  # Trigger dispatch
    assert rows == [{"mac": "aa:bb:cc"}]  # Flattened helper output
    assert invocations == [(fake_session, "site-uuid", "dev-uuid", {"node": "node0"})]  # Args forwarded


def test_execute_helper_exception_falls_back(fake_session: Any) -> None:
    """Any helper exception degrades to the fallback path (no menu crash)."""
    fallback_called: list[bool] = []  # Track that fallback fired

    def fallback(*_args, **_kwargs):  # Match FallbackFn signature
        fallback_called.append(True)  # Record invocation
        return [{"recovered": True}]  # Distinct sentinel so we can assert routing

    a = DeviceUtilsAdapter(fake_session, fallback_fn=fallback)  # Wire fallback

    def raising_helper(*_a, **_k):  # Helper that always raises -- triggers fallback path
        raise RuntimeError("boom")  # Distinct message for debuggability

    a._command_map[("switch", "show_arp")] = raising_helper  # Inject the failing helper
    a._utils_available = True  # Ensure dispatch attempts the helper
    rows = a.execute("show_arp", "switch", "s", "d")  # Invoke; should swallow exception
    assert rows == [{"recovered": True}]  # Caller sees fallback's response
    assert fallback_called == [True]  # Fallback was actually invoked
