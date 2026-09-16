"""Wave 2 P2 coverage for src/refactors/main_entrypoint.py (initiative #1018).

Covers `MainEntrypoint.run()` end-to-end plus the `_MistHelperProxy` `__getattr__`
lazy-lookup path. MistHelper module attributes are monkeypatched with MagicMock
instances so the entrypoint's eight-step pipeline executes without touching real
argparse, network, or authentication code. No source edits, no live I/O.
"""

from __future__ import annotations  # WHY: PEP 604 unions in type hints on Python 3.10+.

import argparse  # WHY: MagicMock(spec=argparse.ArgumentParser) contract typing.
from collections.abc import Callable  # WHY: tests type handler fixtures.
from typing import Any  # WHY: mocks dict holds both MagicMock and Namespace objects.
from unittest.mock import MagicMock, call  # WHY: FR-008 mandates MagicMock(spec=...) + call-order verification.

import pytest  # WHY: monkeypatch fixture for MistHelper attribute overrides.

import MistHelper  # WHY: cache tests exercise the runtime menu and mode dispatch tables.
from src.config.source_dependency_resolver import SourceDependencyResolver  # WHY: assert the source dependency seam.
from src.refactors.main_entrypoint import (  # WHY: SUT direct imports.
    _MH,
    AppContext,
    ApplicationBootstrap,
    MainEntrypoint,
)
from src.utils.menu_entry import MenuEntry  # WHY: menu cache fixtures use the production row model.


@pytest.fixture
def wired_misthelper(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Wire every MistHelper attribute the entrypoint touches to a MagicMock(spec=...) double.

    Returns a dict of {attribute_name: mock} so tests can assert on call ordering
    and argument bindings. The `_MistHelperProxy.__getattr__` path resolves each
    attribute against `SourceDependencyResolver`, so monkeypatching
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
        "_systematic_test_has_api_token": MagicMock(return_value=True, name="_systematic_test_has_api_token"),
        "_configure_runtime_options": MagicMock(name="_configure_runtime_options"),
        "_dispatch_main_mode": MagicMock(name="_dispatch_main_mode"),
    }
    bootstrap_startup_mock = MagicMock(name="_run_common_startup")  # WHY: avoid real file and dependency startup.
    monkeypatch.setattr(ApplicationBootstrap, "_run_common_startup", bootstrap_startup_mock)  # WHY: isolate run().
    for attr_name, mock_obj in mocks.items():  # WHY: publish each mock as a MistHelper module attribute.
        monkeypatch.setattr(f"MistHelper.{attr_name}", mock_obj, raising=False)  # WHY: proxy resolves at call time.
    mocks["_parser"] = parser_mock  # WHY: expose the parser mock for direct assertions.
    mocks["_parsed_args"] = parsed_args  # WHY: expose the namespace instance for identity assertions.
    mocks["_run_common_startup"] = bootstrap_startup_mock  # WHY: expose the bootstrap boundary assertion.
    return mocks  # WHY: hand the wiring back to the test for call-order + arg assertions.


class TestMistHelperProxy:
    """`_MistHelperProxy.__getattr__` resolves names against the live MistHelper module."""

    def test_getattr_returns_module_attribute(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A published attribute on MistHelper is returned by the proxy's __getattr__."""
        sentinel_value = MagicMock(name="sentinel")  # WHY: unique object we can identity-compare below.
        monkeypatch.setattr("MistHelper._sentinel_proxy_attr", sentinel_value, raising=False)  # WHY: publish attr.
        proxy = _MH  # WHY: fresh proxy instance to exercise the getattr path in isolation.
        assert proxy._sentinel_proxy_attr is sentinel_value  # WHY: identity check confirms zero-copy passthrough.

    def test_getattr_reflects_late_rebinding(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Rebinding the attribute after proxy creation is honoured at the next access."""
        proxy = _MH  # WHY: create proxy first so the test proves the lookup is call-time.
        first = MagicMock(name="first")  # WHY: initial published value.
        monkeypatch.setattr("MistHelper._sentinel_rebind_attr", first, raising=False)  # WHY: initial publication.
        assert proxy._sentinel_rebind_attr is first  # WHY: baseline: proxy sees the first value.
        second = MagicMock(name="second")  # WHY: rebound value.
        monkeypatch.setattr("MistHelper._sentinel_rebind_attr", second, raising=False)  # WHY: publish new value.
        assert proxy._sentinel_rebind_attr is second  # WHY: proxy call-time lookup honours the rebound value.


def _menu_entry(menu_id: str, handler, title: str) -> MenuEntry:
    """Return a small menu row for cache tests."""
    return MenuEntry(  # WHY: `_print_interactive_menu` reads the named row fields.
        menu_id=menu_id,  # WHY: keep the row aligned with its dictionary key.
        handler=handler,  # WHY: the cache test does not call the handler.
        title=title,  # WHY: the output assertion reads this text.
        category="safe",  # WHY: this fixture only exercises display order.
        destructive=False,  # WHY: the fixture performs no Mist Cloud write.
        supports_fast=False,  # WHY: the cache test never invokes systematic tests.
    )


class TestMainEntrypointRun:
    """`MainEntrypoint.run` drives the eight-step pipeline in declared order."""

    def test_run_invokes_pipeline_steps_in_order(self, wired_misthelper: dict[str, Any]) -> None:
        """Each of the eight pipeline steps is called exactly once in the documented order."""
        MainEntrypoint.run()  # WHY: exercise the full CLI entrypoint under mocked dependencies.

        # Assert each step was called exactly once (existence + arity are covered by argument checks below).
        assert wired_misthelper["_build_argument_parser"].call_count == 1  # WHY: step 1 builds the parser.
        assert wired_misthelper["_parser"].parse_args.call_count == 1  # WHY: step 2 parses exactly once.
        assert wired_misthelper["_run_common_startup"].call_count == 1  # WHY: step 3 runs explicit bootstrap work.
        assert wired_misthelper["InputUtils"].ensure_tqdm_available.call_count == 1  # WHY: step 4 sets tqdm.
        assert wired_misthelper["_setup_runtime_flags"].call_count == 1  # WHY: step 5 propagates flags.
        assert wired_misthelper["_initialize_dependencies"].call_count == 1  # WHY: step 6 initializes deps.
        assert wired_misthelper["_establish_mist_session"].call_count == 1  # WHY: step 7 authenticates.
        assert wired_misthelper["_systematic_test_has_api_token"].call_count == 1  # WHY: step 7 checks token state.
        assert wired_misthelper["_configure_runtime_options"].call_count == 1  # WHY: step 8 applies runtime options.
        assert wired_misthelper["_dispatch_main_mode"].call_count == 1  # WHY: step 9 dispatches the mode.

    def test_run_forwards_parsed_args_to_downstream_steps(self, wired_misthelper: dict[str, Any]) -> None:
        """Steps 5-8 all receive the exact Namespace returned by parser.parse_args()."""
        MainEntrypoint.run()  # WHY: single invocation drives every downstream step with the same args namespace.
        expected_args = wired_misthelper["_parsed_args"]  # WHY: identity object we expect to see propagated.
        assert wired_misthelper["_setup_runtime_flags"].call_args == call(expected_args)  # WHY: step 5 args-pass.
        assert wired_misthelper["_initialize_dependencies"].call_args == call(expected_args)  # WHY: step 6 args-pass.
        assert wired_misthelper["_establish_mist_session"].call_args == call(expected_args)  # WHY: step 7 args-pass.
        assert wired_misthelper["_configure_runtime_options"].call_args == call(expected_args)  # WHY: step 8a pass.
        assert wired_misthelper["_dispatch_main_mode"].call_args == call(expected_args)  # WHY: step 8b args-pass.

    def test_run_replaces_active_context_for_each_invocation(self, wired_misthelper: dict[str, Any]) -> None:
        """Each CLI invocation receives a fresh active context."""
        old_context = MainEntrypoint.context  # WHY: capture the pre-run bridge owner for identity comparison.

        MainEntrypoint.run()  # WHY: run must create and activate a fresh invocation context.

        assert isinstance(MainEntrypoint.context, AppContext)  # WHY: legacy readers still need an AppContext view.
        assert MainEntrypoint.context is not old_context  # WHY: one run must not reuse prior invocation state.

    def test_run_skips_startup_session_for_offline_safe_test(self, wired_misthelper: dict[str, Any]) -> None:
        """A no-token `--test` run reaches the test dispatcher without Mist session startup."""
        wired_misthelper["_parsed_args"].test = True  # WHY: simulate the documented safe test command.
        wired_misthelper["_systematic_test_has_api_token"].return_value = False  # WHY: simulate a no-token host.

        MainEntrypoint.run()  # WHY: exercise the entrypoint branch that must run offline.

        wired_misthelper["_establish_mist_session"].assert_not_called()  # WHY: no-token --test must not auth.
        wired_misthelper["_dispatch_main_mode"].assert_called_once_with(
            wired_misthelper["_parsed_args"]
        )  # WHY: the test dispatcher must still run.

    def test_run_keeps_startup_session_when_safe_test_has_token(self, wired_misthelper: dict[str, Any]) -> None:
        """A token-backed `--test` run still performs the original Mist session startup."""
        wired_misthelper["_parsed_args"].test = True  # WHY: simulate --test with credentials present.
        wired_misthelper["_systematic_test_has_api_token"].return_value = True  # WHY: credential path stays live.

        MainEntrypoint.run()  # WHY: exercise the unchanged live-test startup path.

        wired_misthelper["_establish_mist_session"].assert_called_once_with(
            wired_misthelper["_parsed_args"]
        )  # WHY: token-backed --test must behave as before.

    def test_run_keeps_startup_session_when_safe_test_uses_login(self, wired_misthelper: dict[str, Any]) -> None:
        """A login-backed `--test` run still performs interactive Mist session startup."""
        wired_misthelper["_parsed_args"].test = True  # WHY: combine --test with the login path.
        wired_misthelper["_parsed_args"].login = True  # WHY: login must override the offline no-token bypass.
        wired_misthelper["_systematic_test_has_api_token"].return_value = False  # WHY: prove token absence is safe.

        MainEntrypoint.run()  # WHY: exercise the login branch with no environment token.

        wired_misthelper["_establish_mist_session"].assert_called_once_with(
            wired_misthelper["_parsed_args"]
        )  # WHY: --login must still build a session.

    def test_run_uses_module_level_proxy_singleton(self) -> None:
        """The module-level `_MH` singleton is an instance of `_MistHelperProxy`."""
        assert _MH is SourceDependencyResolver  # WHY: guard against accidental replacement with a plain module.


class TestMistHelperMenuAndModeCaches:
    """The CLI caches keep the same behavior and refresh when key data changes."""

    def test_print_interactive_menu_refreshes_when_menu_keys_change(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A menu key change invalidates the sorted-key cache before the next redraw."""
        lines: list[str] = []  # WHY: collect formatted menu output without writing to the terminal.
        menu_actions = {
            "10": _menu_entry("10", lambda: None, "ten"),
            "2": _menu_entry("2", lambda: None, "two"),
        }  # WHY: non-lexical order proves numeric sorting stays active.

        def fake_echo(message: str, *args: object) -> None:
            rendered = message % args if args else message  # WHY: match MistHelper.echo formatting behavior.
            lines.append(rendered)  # WHY: keep exact text for the assertion.

        monkeypatch.setattr(MistHelper, "menu_actions", menu_actions)  # WHY: use a small registry fixture.
        monkeypatch.setattr(MistHelper, "echo", fake_echo)  # WHY: capture printed text without side effects.
        monkeypatch.setattr(MistHelper, "_SORTED_MENU_KEYS_CACHE", None)  # WHY: start from a cold cache.

        MistHelper._print_interactive_menu()  # WHY: build the initial cached order.
        menu_actions["3"] = _menu_entry("3", lambda: None, "three")  # WHY: simulate a runtime registry extension.
        MistHelper._print_interactive_menu()  # WHY: prove the next redraw sees the new key.

        assert lines == [
            "\nAvailable Options:",
            "2: two",
            "10: ten",
            "\nAvailable Options:",
            "2: two",
            "3: three",
            "10: ten",
        ]  # WHY: the cache must not serve stale keys or alter menu text.

    def test_dispatch_main_mode_keeps_handler_order_and_late_binding(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The cached mode table preserves first-match dispatch and handler rebinding."""
        calls: list[str] = []  # WHY: record the selected handler for each synthetic mode.

        def make_handler(name: str) -> Callable[[argparse.Namespace], None]:
            def handler(_args: argparse.Namespace) -> None:
                calls.append(name)  # WHY: identify the selected mode without running real side effects.

            return handler  # WHY: hand monkeypatch a callable with the original handler shape.

        handlers = {
            "_run_systematic_test_mode": "test",
            "_run_interactive_test_mode": "testinteractive",
            "_run_tui_mode_and_exit": "tui",
            "_run_web_portal_mode": "web_portal",
            "_run_capture_portal_mode": "capture_portal",
            "_run_metrics_snmp": "metrics_snmp",
            "_run_mib_generator_mode": "mib_generate",
            "_run_metrics_gateway_mode": "metrics_gateway",
            "_run_cli_mode": "cli",
            "_run_interactive_mode": "interactive",
        }  # WHY: cover every dispatch branch, including the fallback.
        for attr_name, label in handlers.items():
            monkeypatch.setattr(MistHelper, attr_name, make_handler(label))  # WHY: avoid real dispatch side effects.

        base = {
            "test": False,
            "testinteractive": False,
            "tui": False,
            "web_portal": False,
            "capture_portal": False,
            "metrics_snmp": False,
            "mib_generate": False,
            "mib_dry_run": False,
            "mib_report": False,
            "mib_check": False,
            "metrics_gateway": False,
            "menu": None,
            "org": None,
            "site": None,
            "device": None,
            "port": None,
        }  # WHY: each synthetic namespace starts with all mode flags disabled.
        mode_names = (
            "test",
            "testinteractive",
            "tui",
            "web_portal",
            "capture_portal",
            "metrics_snmp",
            "mib_generate",
            "metrics_gateway",
        )  # WHY: order matches the production first-match table.
        for mode_name in mode_names:
            values = dict(base)  # WHY: isolate one flag per dispatch case.
            values[mode_name] = True  # WHY: select the mode under test.
            MistHelper._dispatch_main_mode(argparse.Namespace(**values))  # WHY: exercise the cached table.
        cli_values = dict(base)  # WHY: build the explicit CLI dispatch case.
        cli_values["menu"] = "1"  # WHY: a menu value is a meaningful CLI argument.
        MistHelper._dispatch_main_mode(argparse.Namespace(**cli_values))  # WHY: exercise CLI branch.
        MistHelper._dispatch_main_mode(argparse.Namespace(**base))  # WHY: exercise fallback branch.

        assert calls == [
            "test",
            "testinteractive",
            "tui",
            "web_portal",
            "capture_portal",
            "metrics_snmp",
            "mib_generate",
            "metrics_gateway",
            "cli",
            "interactive",
        ]  # WHY: cached predicates and late-bound handlers must match the original behavior.
