"""Wave 9 P2 coverage for src/refactors/initialize_mist_session_interactive.py (initiative #1018).

Covers `_MistHelperProxy.__getattr__` and `MistSessionInteractiveInitializer.initialize`:
- Proxy attribute lookup resolves to live MistHelper module attributes.
- `initialize()` snapshots globals, constructs the LoginOrchestrator with injected
  deps (safe_input, MSP detector), calls execute(), restores globals, and returns
  the coerced boolean outcome (True / False / falsy → False).

Both interactive login success and failure are exercised, along with the
inner `_detect_msp_for_login` adapter which forwards to `detect_msp_privileges`.

All MistHelper helper functions are published on the MistHelper module via
`monkeypatch.setattr("MistHelper.<attr>", ..., raising=False)` so the `_MH`
proxy resolves to our doubles at call time. No source edits, no live I/O.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.10+.

import logging  # WHY: logging.info/debug for action-log traceability required by constitution.
from typing import Any  # WHY: heterogeneous state bag typing.
from unittest.mock import MagicMock  # WHY: FR-008 mandates MagicMock doubles.

import pytest  # WHY: monkeypatch fixture.

from src.refactors.initialize_mist_session_interactive import (  # WHY: SUT direct imports.
    _MH,
    MistSessionInteractiveInitializer,
    _MistHelperProxy,
)


class TestMistHelperProxy:
    """`_MistHelperProxy.__getattr__` resolves names against the live MistHelper module."""

    def test_getattr_returns_module_attribute(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A published attribute on MistHelper is returned by the proxy's __getattr__."""
        logging.info("test: publishing sentinel attribute on MistHelper module")  # WHY: pre-action log.
        sentinel = MagicMock(name="interactive_sentinel")  # WHY: unique identity for equality check.
        monkeypatch.setattr("MistHelper._interactive_sentinel_attr", sentinel, raising=False)  # WHY: publish for proxy.
        proxy = _MistHelperProxy()  # WHY: fresh proxy instance to exercise __getattr__ in isolation.
        result = proxy._interactive_sentinel_attr  # WHY: exercise __getattr__ on unpublished attribute name.
        logging.debug("test: proxy returned attribute; identity=%s", id(result))  # WHY: post-action log.
        assert result is sentinel  # WHY: identity match confirms lazy resolution against live module.

    def test_module_level_singleton_is_proxy(self) -> None:
        """`_MH` module-level singleton is an instance of `_MistHelperProxy`."""
        logging.info("test: asserting module-level _MH is a proxy instance")  # WHY: pre-action log.
        assert isinstance(_MH, _MistHelperProxy)  # WHY: guard against accidental rebinding.
        logging.debug("test: module-level _MH proxy identity confirmed")  # WHY: post-action log.


def _publish_interactive_helpers(
    monkeypatch: pytest.MonkeyPatch, *, execute_returns: Any = True
) -> dict[str, MagicMock]:
    """Publish MistHelper helper functions used by MistSessionInteractiveInitializer.initialize.

    Each helper is stubbed with a MagicMock; ``execute_returns`` controls the
    orchestrator's ``execute()`` return value. Returns a dict of mocks so
    individual tests can assert wiring or override behaviour.
    """
    logging.info(  # WHY: pre-action log — publishing helper stubs.
        "test-helpers: publishing MistHelper helper doubles (execute_returns=%s)",
        execute_returns,
    )
    snapshot = MagicMock(name="snapshot_globals")  # WHY: state-bag snapshotter stub.
    state_bag: dict[str, Any] = {"apisession": MagicMock(name="apisession_in_state")}  # WHY: default state.
    snapshot.return_value = state_bag  # WHY: initialize() reads state from this bag.
    restore = MagicMock(name="restore_globals")  # WHY: state-bag restorer stub.
    orch_class = MagicMock(name="LoginOrchestrator_class")  # WHY: class-level stub for constructor.
    orch_instance = MagicMock(name="LoginOrchestrator_instance")  # WHY: instance returned by constructor.
    orch_instance.execute.return_value = execute_returns  # WHY: parameterize execute() outcome.
    orch_class.return_value = orch_instance  # WHY: calling LoginOrchestrator(...) returns instance.
    input_utils = MagicMock(name="InputUtils")  # WHY: InputUtils namespace stub.
    input_utils.safe_input = MagicMock(name="safe_input")  # WHY: attribute accessed by initialize().

    monkeypatch.setattr(
        "MistHelper._snapshot_session_globals_to_state", snapshot, raising=False
    )  # WHY: publish snapshotter.
    monkeypatch.setattr(
        "MistHelper._restore_session_globals_from_state", restore, raising=False
    )  # WHY: publish restorer.
    monkeypatch.setattr("MistHelper.LoginOrchestrator", orch_class, raising=False)  # WHY: publish orchestrator class.
    monkeypatch.setattr("MistHelper.InputUtils", input_utils, raising=False)  # WHY: publish InputUtils.

    logging.debug(  # WHY: post-action log — helpers published.
        "test-helpers: helpers published (snapshot,restore,orch,input_utils)"
    )
    return {
        "snapshot": snapshot,  # WHY: expose to tests for assertion.
        "state_bag": state_bag,  # type: ignore[dict-item]  # WHY: state bag is a dict; MagicMock hint is broad.
        "restore": restore,  # WHY: expose restore mock.
        "orch_class": orch_class,  # WHY: expose class mock for constructor-arg assertions.
        "orch_instance": orch_instance,  # WHY: expose instance mock for execute() assertions.
        "input_utils": input_utils,  # WHY: expose InputUtils mock.
    }


class TestInitializeInteractive:
    """`MistSessionInteractiveInitializer.initialize` — full behaviour matrix."""

    def test_happy_path_returns_true(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Successful login: initialize() returns True and restores state."""
        logging.info("test: happy-path initialize() expecting True")  # WHY: pre-action log.
        mocks = _publish_interactive_helpers(monkeypatch, execute_returns=True)  # WHY: wire helpers.
        result = MistSessionInteractiveInitializer.initialize()  # WHY: SUT invocation.
        logging.debug("test: initialize() returned %s", result)  # WHY: post-action log.
        assert result is True  # WHY: bool(True) == True.
        mocks["snapshot"].assert_called_once_with()  # WHY: state was snapshotted.
        mocks["orch_class"].assert_called_once()  # WHY: orchestrator was constructed.
        mocks["orch_instance"].execute.assert_called_once_with()  # WHY: execute() invoked.
        mocks["restore"].assert_called_once_with(mocks["state_bag"])  # WHY: state restored post-login.

    def test_failed_login_returns_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Failed login (execute returns False): initialize() returns False."""
        logging.info("test: failed-login initialize() expecting False")  # WHY: pre-action log.
        mocks = _publish_interactive_helpers(monkeypatch, execute_returns=False)  # WHY: wire helpers.
        result = MistSessionInteractiveInitializer.initialize()  # WHY: SUT invocation.
        logging.debug("test: initialize() returned %s", result)  # WHY: post-action log.
        assert result is False  # WHY: bool(False) == False.
        mocks["restore"].assert_called_once_with(mocks["state_bag"])  # WHY: restore still runs.

    def test_falsy_execute_result_coerces_to_false(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Falsy but non-False execute() (e.g. None): bool() coerces to False."""
        logging.info("test: falsy-return initialize() expecting False via bool() coercion")  # pre-action.
        mocks = _publish_interactive_helpers(monkeypatch, execute_returns=None)  # WHY: None is falsy.
        result = MistSessionInteractiveInitializer.initialize()  # WHY: SUT invocation.
        logging.debug("test: initialize() returned %s (coerced from None)", result)  # post-action.
        assert result is False  # WHY: bool(None) → False.
        mocks["restore"].assert_called_once()  # WHY: restore path still executed on falsy result.

    def test_orchestrator_receives_injected_deps(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """LoginOrchestrator constructor receives state, safe_input, and detect_msp_privileges."""
        logging.info("test: verifying orchestrator constructor kwargs wiring")  # pre-action.
        mocks = _publish_interactive_helpers(monkeypatch, execute_returns=True)  # WHY: wire helpers.
        MistSessionInteractiveInitializer.initialize()  # WHY: trigger orchestrator construction.
        call_kwargs = mocks["orch_class"].call_args.kwargs  # WHY: inspect constructor kwargs.
        logging.debug("test: orchestrator kwargs=%s", sorted(call_kwargs.keys()))  # post-action.
        assert call_kwargs["state"] is mocks["state_bag"]  # WHY: state bag passed through.
        assert call_kwargs["safe_input"] is mocks["input_utils"].safe_input  # WHY: safe_input injected.
        assert callable(call_kwargs["detect_msp_privileges"])  # WHY: DI adapter is a callable.

    def test_detect_msp_adapter_calls_extracted_detector(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Inner `_detect_msp_for_login` adapter delegates to `detect_msp_privileges`."""
        logging.info("test: exercising _detect_msp_for_login DI adapter")  # pre-action.
        mocks = _publish_interactive_helpers(monkeypatch, execute_returns=True)  # WHY: wire helpers.
        fake_detector_return = MagicMock(name="msp_detection_result")  # WHY: sentinel return value.
        detector_stub = MagicMock(  # WHY: replacement for extracted detect_msp_privileges.
            name="detect_msp_privileges_stub", return_value=fake_detector_return
        )
        monkeypatch.setattr(  # WHY: patch the imported symbol in the SUT module namespace.
            "src.refactors.initialize_mist_session_interactive.detect_msp_privileges",
            detector_stub,
        )
        MistSessionInteractiveInitializer.initialize()  # WHY: build the adapter closure.
        adapter = mocks["orch_class"].call_args.kwargs["detect_msp_privileges"]  # WHY: extract adapter.
        result = adapter()  # WHY: invoke the adapter (simulates orchestrator calling it).
        logging.debug("test: adapter returned %s", result)  # post-action.
        assert result is fake_detector_return  # WHY: adapter forwards detector return value.
        detector_stub.assert_called_once_with(mocks["state_bag"]["apisession"])  # WHY: called with state.get.
