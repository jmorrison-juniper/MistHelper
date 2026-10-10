"""Registered-path precedence tests for the menu 291 RRM dry-run policy (issue #4051)."""

from __future__ import annotations  # WHY: keep annotations lightweight in tests.

import argparse  # WHY: the CLI tri-state tests build real namespaces.
from types import SimpleNamespace  # WHY: a stand-in root module carries only the args attribute.
from typing import Any  # WHY: monkeypatch is dynamically typed.

import pytest  # WHY: table-driven cases use parametrize.

import MistHelper  # WHY: menu_actions is the authoritative registered menu mapping.
from src.foundation.runtime.config.source_dependency_resolver import SourceDependencyResolver
from src.mist.resources.site.rrm_reset.operation import RrmResetOperation
from tests.integration.rrm_dry_run.rrm_fakes import RecordingClient, build_dependencies

MENU_ID = "291"  # WHY: one constant names the destructive RRM menu under test.


def _install(monkeypatch: Any, answers: list[str], cli_dry_run: bool | None) -> tuple[list[str], RecordingClient]:
    """Bind recording dependencies and a root module that reports the given CLI mode."""
    monkeypatch.setenv("RRM_SETTLE_SECONDS", "0")  # WHY: tests must not wait for the RRM settle period.
    events: list[str] = []  # WHY: the event log records reads, writes, and requests.
    deps, client = build_dependencies(events, answers)  # WHY: no real Mist session may be reached.
    monkeypatch.setattr(RrmResetOperation, "_build_dependencies", staticmethod(lambda: deps))  # WHY: inject fakes.
    root = SimpleNamespace(args=argparse.Namespace(dry_run=cli_dry_run))  # WHY: model the parsed root CLI state.
    monkeypatch.setattr(SourceDependencyResolver, "_root_module", root)  # WHY: bind the root args seam.
    return events, client  # WHY: assertions read both the order and the requests.


def _handler() -> Any:
    """Return the registered menu 291 handler."""
    return MistHelper.menu_actions[MENU_ID].handler  # WHY: the test must exercise the registered callable.


@pytest.mark.parametrize(
    ("env_value", "reason"),
    [
        ("true", "a truthy environment value forces dry-run mode"),
        ("1", "the numeric truthy value forces dry-run mode"),
        ("false", "a false environment value must not authorize live mode"),
        ("banana", "an invalid environment value must not authorize live mode"),
        ("", "an empty environment value must not authorize live mode"),
    ],
)
def test_menu_291_interactive_dispatch_never_runs_live_from_environment(
    monkeypatch: Any, env_value: str, reason: str
) -> None:
    """Interactive dispatch with no explicit mode must never send a destructive request."""
    monkeypatch.setenv("RRM_DRY_RUN", env_value)  # WHY: the environment is the only supplied signal.
    events, client = _install(monkeypatch, ["OPTIMIZE", "OPTIMIZE"], None)  # WHY: answers would allow a live run.
    _handler()()  # WHY: interactive dispatch calls the handler with no argument.
    assert client.requests == [], reason  # WHY: silence must never authorize a production radio change.
    assert events == ["read:site-1", "before:1"], "the dry-run path still writes the durable before capture"


def test_menu_291_interactive_dispatch_absent_environment_forces_dry_run(monkeypatch: Any) -> None:
    """A fully absent environment value resolves to dry-run mode."""
    monkeypatch.delenv("RRM_DRY_RUN", raising=False)  # WHY: prove the absent case, not a falsy case.
    events, client = _install(monkeypatch, ["OPTIMIZE", "OPTIMIZE"], None)  # WHY: no explicit mode is supplied.
    _handler()()  # WHY: interactive dispatch supplies no mode.
    assert client.requests == [], "absence must resolve to forced dry-run mode"
    assert events == ["read:site-1", "before:1"], "the dry-run path writes the before capture and nothing else"


def test_menu_291_explicit_live_argument_runs_live_after_typed_confirmation(monkeypatch: Any) -> None:
    """An explicit live argument beats a truthy environment value and still requires the action word."""
    monkeypatch.setenv("RRM_DRY_RUN", "true")  # WHY: the explicit argument must win over the environment.
    events, client = _install(monkeypatch, ["OPTIMIZE", "OPTIMIZE"], None)  # WHY: supply the confirmation word.
    _handler()(dry_run=False)  # WHY: an explicit live choice is the only way to reach the request.
    assert [name for name, _site, _body in client.requests] == ["optimize"], "explicit live mode sends one request"
    assert events[:3] == ["read:site-1", "before:1", "optimize"], "the before capture still precedes the request"


def test_menu_291_explicit_live_argument_still_refuses_a_wrong_confirmation(monkeypatch: Any) -> None:
    """An explicit live argument with a wrong confirmation word sends no request."""
    monkeypatch.delenv("RRM_DRY_RUN", raising=False)  # WHY: isolate the confirmation control.
    events, client = _install(monkeypatch, ["RESET", "OPTIMIZE"], None)  # WHY: the confirmation does not match.
    _handler()(dry_run=False)  # WHY: explicit live mode reaches the typed confirmation.
    assert client.requests == [], "a wrong confirmation word must stop the destructive request"
    assert events == ["read:site-1", "before:1"], "only the before evidence is written"


def test_menu_291_explicit_dry_run_argument_wins_over_false_environment(monkeypatch: Any) -> None:
    """An explicit dry-run argument beats a false environment value."""
    monkeypatch.setenv("RRM_DRY_RUN", "false")  # WHY: the false value must not authorize live mode.
    _events, client = _install(monkeypatch, ["OPTIMIZE", "OPTIMIZE"], None)  # WHY: answers would allow a live run.
    _handler()(dry_run=True)  # WHY: the caller asks for a preview.
    assert client.requests == [], "an explicit dry-run argument sends no destructive request"


def test_menu_291_cli_dry_run_flag_forces_dry_run(monkeypatch: Any) -> None:
    """The root CLI dry-run mode resolves to dry-run mode when no argument is supplied."""
    monkeypatch.delenv("RRM_DRY_RUN", raising=False)  # WHY: the CLI mode is the only supplied signal.
    _events, client = _install(monkeypatch, ["OPTIMIZE", "OPTIMIZE"], True)  # WHY: model `--dry-run`.
    _handler()()  # WHY: the handler falls back to the root CLI mode.
    assert client.requests == [], "the CLI dry-run mode sends no destructive request"


def test_menu_291_cli_live_run_flag_beats_truthy_environment(monkeypatch: Any) -> None:
    """An explicit CLI live mode beats a truthy environment value."""
    monkeypatch.setenv("RRM_DRY_RUN", "true")  # WHY: the explicit CLI mode must win over the environment.
    _events, client = _install(monkeypatch, ["RESET", "RESET"], False)  # WHY: model `--live-run`.
    _handler()()  # WHY: the handler falls back to the explicit root CLI mode.
    assert [name for name, _site, _body in client.requests] == ["reset"], "explicit CLI live mode sends one request"


def test_menu_291_handler_default_is_the_absent_marker() -> None:
    """The registered handler must default to the absent marker, not to live mode."""
    defaults = _handler().__defaults__  # WHY: the lambda default decides the interactive dispatch value.
    assert defaults == (None,), f"menu {MENU_ID} must default dry_run to None, observed {defaults!r}"


@pytest.mark.parametrize(
    ("arguments", "expected"),
    [
        ([], None),
        (["--dry-run"], True),
        (["--live-run"], False),
    ],
)
def test_cli_kwargs_carry_the_tri_state_mode(arguments: list[str], expected: bool | None) -> None:
    """CLI dispatch must pass None when neither an explicit dry-run nor an explicit live mode is present."""
    args = MistHelper._build_argument_parser().parse_args(arguments)  # WHY: exercise the actual root parser.
    kwargs = MistHelper._build_cli_func_kwargs(args, None, None)  # WHY: this builder feeds every CLI menu call.
    assert kwargs["dry_run"] is expected, f"arguments {arguments!r} must map to {expected}"


def test_cli_rejects_both_destructive_modes() -> None:
    """The parser must reject contradictory dry-run and live-run flags."""
    parser = MistHelper._build_argument_parser()  # WHY: the mutual exclusion belongs to the registered parser.
    with pytest.raises(SystemExit) as error:  # WHY: argparse reports invalid flag combinations with SystemExit.
        parser.parse_args(["--dry-run", "--live-run"])  # WHY: no run may carry two destructive modes.
    assert error.value.code == 2, "argparse must reject contradictory destructive modes"
