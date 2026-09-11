"""Wave 4 P2 coverage for src/refactors/initialize_mist_session.py (initiative #1018).

Covers `_MistHelperProxy.__getattr__`, `_mh_module`, and every branch of
`MistSessionInitializer.initialize`:
- Already-initialized short-circuit (apisession truthy → returns True).
- mistapi load failure → returns False.
- All session strategies fail → logs variants and returns False.
- Happy path → configures timeout + validates session, returns True.
- validate_initialized_session returning falsy → bool() converts to False.

All MistHelper helper functions are published on the MistHelper module via
`monkeypatch.setattr("MistHelper.<attr>", ..., raising=False)` so the `_MH`
proxy resolves to our doubles at call time. No source edits, no live I/O.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.10+.

from typing import Any  # WHY: dict-of-mocks return-type annotation.
from unittest.mock import MagicMock  # WHY: FR-008 mandates MagicMock doubles.

import pytest  # WHY: monkeypatch fixture.

from src.refactors.initialize_mist_session import (  # WHY: SUT + proxy direct imports.
    _MH,
    MistSessionInitializer,
    _mh_module,
    _MistHelperProxy,
)


class TestMistHelperProxy:
    """`_MistHelperProxy.__getattr__` resolves names against the live MistHelper module."""

    def test_getattr_returns_module_attribute(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A published attribute on MistHelper is returned by the proxy's __getattr__."""
        sentinel = MagicMock(name="init_sess_sentinel")  # WHY: unique object we can identity-compare.
        monkeypatch.setattr("MistHelper._init_sess_sentinel_attr", sentinel, raising=False)  # WHY: publish for proxy.
        proxy = _MistHelperProxy()  # WHY: fresh proxy to exercise __getattr__ in isolation.
        assert proxy._init_sess_sentinel_attr is sentinel  # WHY: identity check.

    def test_module_level_singleton_is_proxy(self) -> None:
        """`_MH` module-level singleton is an instance of `_MistHelperProxy`."""
        assert isinstance(_MH, _MistHelperProxy)  # WHY: guard against accidental replacement.


class TestMhModule:
    """`_mh_module` returns the live MistHelper module."""

    def test_returns_misthelper_module(self) -> None:
        """The returned module's __name__ is 'MistHelper'."""
        module = _mh_module()  # WHY: exercise the helper.
        assert module.__name__ == "MistHelper"  # WHY: identity by module name.


def _publish_helpers(monkeypatch: pytest.MonkeyPatch, **overrides: Any) -> dict[str, MagicMock]:
    """Publish MistHelper helper functions used by MistSessionInitializer.initialize.

    Each helper is stubbed with a MagicMock; individual tests can override return_value
    or side_effect via the returned dict.
    """
    helpers = {  # WHY: build the default mock set once, then let tests customize per-need.
        "_load_mistapi_module": MagicMock(name="_load_mistapi_module"),  # WHY: returns loaded mistapi module.
        "_parse_api_tokens": MagicMock(name="_parse_api_tokens"),  # WHY: returns (host, tokens).
        "_introspect_apisession_class": MagicMock(
            name="_introspect_apisession_class"
        ),  # WHY: returns (cls, sig_params).
        "_attempt_all_session_strategies": MagicMock(
            name="_attempt_all_session_strategies"
        ),  # WHY: returns (session, method, tried).
        "_log_failed_session_variants": MagicMock(name="_log_failed_session_variants"),  # WHY: called only on failure.
        "_configure_session_timeout": MagicMock(name="_configure_session_timeout"),  # WHY: called only on success.
        "_validate_initialized_session": MagicMock(name="_validate_initialized_session"),  # WHY: returns truthy/falsy.
    }

    for name, mock in helpers.items():  # WHY: publish each helper on MistHelper so _MH proxy resolves.
        monkeypatch.setattr(f"MistHelper.{name}", mock, raising=False)  # WHY: proxy is call-time.

    return helpers  # WHY: expose mocks so tests can customize + assert.


class TestInitializeShortCircuit:
    """`initialize()` returns True immediately when apisession is truthy."""

    def test_already_initialized_returns_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When _MH.apisession is truthy, initialize() returns True and skips all setup."""
        existing_session = MagicMock(name="existing_apisession")  # WHY: truthy sentinel.
        monkeypatch.setattr("MistHelper.apisession", existing_session, raising=False)  # WHY: publish truthy.
        helpers = _publish_helpers(monkeypatch)  # WHY: publish helpers so short-circuit assertion is provable.

        assert MistSessionInitializer.initialize() is True  # WHY: short-circuit returns True.
        assert helpers["_load_mistapi_module"].call_count == 0  # WHY: setup skipped entirely.


class TestInitializeMistapiLoadFailure:
    """`initialize()` returns False when mistapi cannot be loaded."""

    def test_load_mistapi_returns_none_bails(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When _load_mistapi_module returns None/falsy, initialize() returns False."""
        monkeypatch.setattr("MistHelper.apisession", None, raising=False)  # WHY: not-initialized.
        monkeypatch.setattr("MistHelper.mistapi", None, raising=False)  # WHY: starting state - no mistapi.
        helpers = _publish_helpers(monkeypatch)  # WHY: publish helpers so load returns None.
        helpers["_load_mistapi_module"].return_value = None  # WHY: force loader failure branch.

        assert MistSessionInitializer.initialize() is False  # WHY: mistapi unavailable → False.
        assert helpers["_parse_api_tokens"].call_count == 0  # WHY: never reached parse step.


class TestInitializeStrategiesFail:
    """`initialize()` returns False when no session strategy succeeds."""

    def test_all_strategies_fail_logs_and_returns_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When _attempt_all_session_strategies returns falsy session, log variants + False."""
        monkeypatch.setattr("MistHelper.apisession", None, raising=False)  # WHY: not-initialized.
        monkeypatch.setattr("MistHelper.mistapi", None, raising=False)  # WHY: mistapi placeholder.
        helpers = _publish_helpers(monkeypatch)  # WHY: publish helpers with sensible defaults.

        loaded_mistapi = MagicMock(name="loaded_mistapi")  # WHY: successful loader result.
        helpers["_load_mistapi_module"].return_value = loaded_mistapi  # WHY: loader step succeeds.
        helpers["_parse_api_tokens"].return_value = (
            "https://api.mist.com",
            ["tok1", "tok2"],
        )  # WHY: (host, tokens) tuple.
        apisession_cls = MagicMock(name="APISession_cls")  # WHY: class handle discovered by introspect.
        helpers["_introspect_apisession_class"].return_value = (
            apisession_cls,
            ["host", "token"],
        )  # WHY: (cls, sig_params) tuple.
        tried_variants = ["variant_a", "variant_b"]  # WHY: sentinel list for post-assert.
        helpers["_attempt_all_session_strategies"].return_value = (
            None,
            None,
            tried_variants,
        )  # WHY: all strategies fail → falsy session.

        assert MistSessionInitializer.initialize() is False  # WHY: strategies failed → False.
        assert helpers["_log_failed_session_variants"].call_count == 1  # WHY: failure logged.
        assert helpers["_log_failed_session_variants"].call_args.args == (
            tried_variants,
        )  # WHY: tried variants surfaced.
        assert helpers["_configure_session_timeout"].call_count == 0  # WHY: timeout config skipped.
        assert helpers["_validate_initialized_session"].call_count == 0  # WHY: validation skipped.


class TestInitializeHappyPath:
    """`initialize()` returns True when a session is built and validated."""

    def test_full_happy_path(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Session discovered, timeout configured, validation truthy → returns True; global mirrored."""
        monkeypatch.setattr("MistHelper.apisession", None, raising=False)  # WHY: not-initialized.
        monkeypatch.setattr("MistHelper.mistapi", None, raising=False)  # WHY: mistapi placeholder.
        helpers = _publish_helpers(monkeypatch)  # WHY: publish helpers.

        loaded_mistapi = MagicMock(name="loaded_mistapi")  # WHY: successful loader result.
        helpers["_load_mistapi_module"].return_value = loaded_mistapi  # WHY: loader succeeds.
        helpers["_parse_api_tokens"].return_value = (
            "https://api.mist.com",
            ["tok1"],
        )  # WHY: (host, tokens).
        apisession_cls = MagicMock(name="APISession_cls")  # WHY: class handle from introspect.
        helpers["_introspect_apisession_class"].return_value = (
            apisession_cls,
            ["host", "apitoken"],
        )  # WHY: (cls, params).
        new_session = MagicMock(name="new_apisession")  # WHY: truthy session sentinel.
        helpers["_attempt_all_session_strategies"].return_value = (
            new_session,
            "positional_all_args",
            ["variant_ok"],
        )  # WHY: (session, method, tried).
        helpers["_validate_initialized_session"].return_value = True  # WHY: validation succeeds.

        result = MistSessionInitializer.initialize()  # WHY: exercise full happy path.

        assert result is True  # WHY: validated session → True.
        assert helpers["_configure_session_timeout"].call_count == 1  # WHY: timeout applied.
        assert helpers["_configure_session_timeout"].call_args.args == (new_session,)  # WHY: correct session threaded.
        assert helpers["_validate_initialized_session"].call_count == 1  # WHY: validation invoked.
        assert helpers["_validate_initialized_session"].call_args.args == (
            new_session,
            "positional_all_args",
        )  # WHY: session + method threaded to validator.
        # WHY: assert that global mirror writes actually happened.
        import MistHelper as mh  # WHY: read back the mutated global to confirm assignment mirroring.

        assert mh.apisession is new_session  # WHY: mh_module.apisession = new_apisession happened.
        assert mh.mistapi is loaded_mistapi  # WHY: mh_module.mistapi = loaded_mistapi happened.

    def test_validate_returns_falsy_bool_converts_to_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When _validate_initialized_session returns falsy (e.g., None), bool() → False."""
        monkeypatch.setattr("MistHelper.apisession", None, raising=False)  # WHY: not-initialized.
        monkeypatch.setattr("MistHelper.mistapi", None, raising=False)  # WHY: mistapi placeholder.
        helpers = _publish_helpers(monkeypatch)  # WHY: publish helpers.

        helpers["_load_mistapi_module"].return_value = MagicMock(name="loaded_mistapi")  # WHY: loader succeeds.
        helpers["_parse_api_tokens"].return_value = (
            "https://api.mist.com",
            ["tok1"],
        )  # WHY: (host, tokens).
        helpers["_introspect_apisession_class"].return_value = (
            MagicMock(name="APISession_cls"),
            ["host", "apitoken"],
        )  # WHY: (cls, params).
        helpers["_attempt_all_session_strategies"].return_value = (
            MagicMock(name="new_apisession"),
            "positional_all_args",
            ["variant_ok"],
        )  # WHY: session built successfully.
        helpers["_validate_initialized_session"].return_value = None  # WHY: falsy → bool() → False.

        assert MistSessionInitializer.initialize() is False  # WHY: bool(None) == False.
