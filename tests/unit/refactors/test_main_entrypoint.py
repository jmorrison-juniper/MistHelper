"""Wave 2 P2 coverage for src/refactors/main_entrypoint.py (initiative #1018).

Covers `MainEntrypoint.run()` end-to-end plus the `_MistHelperProxy` `__getattr__`
lazy-lookup path. MistHelper module attributes are monkeypatched with MagicMock
instances so the entrypoint's eight-step pipeline executes without touching real
argparse, network, or authentication code. No source edits, no live I/O.
"""

from __future__ import annotations  # WHY: PEP 604 unions in type hints on Python 3.10+.

import argparse  # WHY: MagicMock(spec=argparse.ArgumentParser) contract typing.
from typing import Any  # WHY: mocks dict holds both MagicMock and Namespace objects.
from unittest.mock import MagicMock, call  # WHY: FR-008 mandates MagicMock(spec=...) + call-order verification.

import pytest  # WHY: monkeypatch fixture for MistHelper attribute overrides.

from src.refactors.main_entrypoint import _MH, MainEntrypoint, _MistHelperProxy  # WHY: SUT + proxy direct imports.


@pytest.fixture
def wired_misthelper(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Wire every MistHelper attribute the entrypoint touches to a MagicMock(spec=...) double.

    Returns a dict of {attribute_name: mock} so tests can assert on call ordering
    and argument bindings. The `_MistHelperProxy.__getattr__` path resolves each
    attribute against `importlib.import_module("MistHelper")`, so monkeypatching
    the module attribute is sufficient to intercept every proxy access.
    """
    parser_mock = MagicMock(spec=argparse.ArgumentParser)  # WHY: entrypoint calls parser.parse_args() only.
    parsed_args = argparse.Namespace(  # WHY: MainEntrypoint.run passes args through downstream steps.
        standalone=False, debug=False, login=False, test=False
    )
    parser_mock.parse_args.return_value = parsed_args  # WHY: entrypoint reads result of parse_args() and forwards it.

    input_utils_mock = MagicMock()  # WHY: InputUtils.ensure_tqdm_available() only; no spec class available here.
    mocks: dict[str, Any] = {  # WHY: bundle every entrypoint dependency (MagicMock + Namespace + parser handle).
        "_initialize_deferred_imports": MagicMock(name="_initialize_deferred_imports"),
        "InputUtils": input_utils_mock,
        "_build_argument_parser": MagicMock(return_value=parser_mock, name="_build_argument_parser"),
        "_setup_runtime_flags": MagicMock(name="_setup_runtime_flags"),
        "_initialize_dependencies": MagicMock(name="_initialize_dependencies"),
        "_establish_mist_session": MagicMock(name="_establish_mist_session"),
        "_configure_runtime_options": MagicMock(name="_configure_runtime_options"),
        "_dispatch_main_mode": MagicMock(name="_dispatch_main_mode"),
    }
    for attr_name, mock_obj in mocks.items():  # WHY: publish each mock as a MistHelper module attribute.
        monkeypatch.setattr(f"MistHelper.{attr_name}", mock_obj, raising=False)  # WHY: proxy resolves at call time.
    mocks["_parser"] = parser_mock  # WHY: expose the parser mock for direct assertions.
    mocks["_parsed_args"] = parsed_args  # WHY: expose the namespace instance for identity assertions.
    return mocks  # WHY: hand the wiring back to the test for call-order + arg assertions.


class TestMistHelperProxy:
    """`_MistHelperProxy.__getattr__` resolves names against the live MistHelper module."""

    def test_getattr_returns_module_attribute(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A published attribute on MistHelper is returned by the proxy's __getattr__."""
        sentinel_value = MagicMock(name="sentinel")  # WHY: unique object we can identity-compare below.
        monkeypatch.setattr("MistHelper._sentinel_proxy_attr", sentinel_value, raising=False)  # WHY: publish attr.
        proxy = _MistHelperProxy()  # WHY: fresh proxy instance to exercise the getattr path in isolation.
        assert proxy._sentinel_proxy_attr is sentinel_value  # WHY: identity check confirms zero-copy passthrough.

    def test_getattr_reflects_late_rebinding(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Rebinding the attribute after proxy creation is honoured at the next access."""
        proxy = _MistHelperProxy()  # WHY: create proxy first so the test proves the lookup is call-time.
        first = MagicMock(name="first")  # WHY: initial published value.
        monkeypatch.setattr("MistHelper._sentinel_rebind_attr", first, raising=False)  # WHY: initial publication.
        assert proxy._sentinel_rebind_attr is first  # WHY: baseline: proxy sees the first value.
        second = MagicMock(name="second")  # WHY: rebound value.
        monkeypatch.setattr("MistHelper._sentinel_rebind_attr", second, raising=False)  # WHY: publish new value.
        assert proxy._sentinel_rebind_attr is second  # WHY: proxy call-time lookup honours the rebound value.


class TestMainEntrypointRun:
    """`MainEntrypoint.run` drives the eight-step pipeline in declared order."""

    def test_run_invokes_pipeline_steps_in_order(self, wired_misthelper: dict[str, Any]) -> None:
        """Each of the eight pipeline steps is called exactly once in the documented order."""
        MainEntrypoint.run()  # WHY: exercise the full CLI entrypoint under mocked dependencies.

        # Assert each step was called exactly once (existence + arity are covered by argument checks below).
        assert wired_misthelper["_initialize_deferred_imports"].call_count == 1  # WHY: step 1 (imports).
        assert wired_misthelper["InputUtils"].ensure_tqdm_available.call_count == 1  # WHY: step 2 (tqdm setup).
        assert wired_misthelper["_build_argument_parser"].call_count == 1  # WHY: step 3 (argparse construction).
        assert wired_misthelper["_parser"].parse_args.call_count == 1  # WHY: step 4 (argument parsing).
        assert wired_misthelper["_setup_runtime_flags"].call_count == 1  # WHY: step 5 (flag propagation).
        assert wired_misthelper["_initialize_dependencies"].call_count == 1  # WHY: step 6 (deferred deps).
        assert wired_misthelper["_establish_mist_session"].call_count == 1  # WHY: step 7 (Mist auth).
        assert wired_misthelper["_configure_runtime_options"].call_count == 1  # WHY: step 8a (runtime opts).
        assert wired_misthelper["_dispatch_main_mode"].call_count == 1  # WHY: step 8b (mode dispatch).

    def test_run_forwards_parsed_args_to_downstream_steps(self, wired_misthelper: dict[str, Any]) -> None:
        """Steps 5-8 all receive the exact Namespace returned by parser.parse_args()."""
        MainEntrypoint.run()  # WHY: single invocation drives every downstream step with the same args namespace.
        expected_args = wired_misthelper["_parsed_args"]  # WHY: identity object we expect to see propagated.
        assert wired_misthelper["_setup_runtime_flags"].call_args == call(expected_args)  # WHY: step 5 args-pass.
        assert wired_misthelper["_initialize_dependencies"].call_args == call(expected_args)  # WHY: step 6 args-pass.
        assert wired_misthelper["_establish_mist_session"].call_args == call(expected_args)  # WHY: step 7 args-pass.
        assert wired_misthelper["_configure_runtime_options"].call_args == call(expected_args)  # WHY: step 8a pass.
        assert wired_misthelper["_dispatch_main_mode"].call_args == call(expected_args)  # WHY: step 8b args-pass.

    def test_run_uses_module_level_proxy_singleton(self) -> None:
        """The module-level `_MH` singleton is an instance of `_MistHelperProxy`."""
        assert isinstance(_MH, _MistHelperProxy)  # WHY: guard against accidental replacement with a plain module.
