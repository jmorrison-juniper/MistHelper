"""Wave 7 P2 coverage for src/refactors/switch_to_interactive_login.py (initiative #1018).

Covers every branch of ``SwitchToInteractiveLoginManager`` plus the module-level
``_resolve_runtime_dependencies`` helper:

- ``_resolve_runtime_dependencies``: returns a SimpleNamespace whose
  ``misthelper_module`` attribute is the current MistHelper module; emits both
  info + debug log records.
- ``__init__``: stashes the SimpleNamespace on ``self._deps``.
- ``_misthelper``: call-time lookup returns the module handle bound at
  construction time.
- ``run``: three branches -- (a) user declines the confirmation prompt, (b)
  interactive login fails and is rolled back, (c) interactive login succeeds
  and finalization runs.
- ``_attempt_login_and_finalize``: reads old_session + old_org_id, forwards to
  the rollback helper, and invokes ``_handle_interactive_login_success`` on
  success only.

Every MistHelper attribute the manager touches is monkeypatched onto the
``MistHelper`` module; no live network and no MistHelper source imports.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.10+.

import logging  # WHY: caplog verification of the trace breadcrumbs.
from types import SimpleNamespace  # WHY: assert on the returned SimpleNamespace type.
from typing import Any  # WHY: monkeypatched fakes have loose typing.
from unittest.mock import MagicMock, call  # WHY: FR-008 collaborator doubles + call-order assertions.

import pytest  # WHY: fixture + monkeypatch + caplog fixtures.

from src.refactors.switch_to_interactive_login import (  # WHY: direct SUT imports.
    SwitchToInteractiveLoginManager,
    _resolve_runtime_dependencies,
)


@pytest.fixture
def wired_misthelper(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Publish every helper the manager reaches through onto MistHelper.

    Returns a dict so tests can drive per-call behavior and assert argument
    binding + call ordering. Each helper is a ``MagicMock`` (no ``spec=`` here
    because the underlying targets are free functions rather than a class).
    """
    print_header = MagicMock(name="_print_switch_login_header")  # WHY: banner helper.
    confirm = MagicMock(name="_prompt_switch_login_confirmation")  # WHY: user Y/N prompt.
    attempt_login = MagicMock(name="_attempt_interactive_login_with_rollback")  # WHY: rollback-guarded login.
    handle_success = MagicMock(name="_handle_interactive_login_success")  # WHY: post-login finalization.

    monkeypatch.setattr("MistHelper._print_switch_login_header", print_header, raising=False)  # WHY: proxy lookup.
    monkeypatch.setattr("MistHelper._prompt_switch_login_confirmation", confirm, raising=False)  # WHY: proxy lookup.
    monkeypatch.setattr(  # WHY: proxy lookup.
        "MistHelper._attempt_interactive_login_with_rollback", attempt_login, raising=False
    )
    monkeypatch.setattr(  # WHY: proxy lookup.
        "MistHelper._handle_interactive_login_success", handle_success, raising=False
    )

    # WHY: preserve old session/org_id sentinels so we can assert they get forwarded to rollback.
    old_session = MagicMock(name="old_apisession")
    old_org = "old-org-id"
    monkeypatch.setattr(
        "MistHelper.apisession", old_session, raising=False
    )  # WHY: read by _attempt_login_and_finalize.
    monkeypatch.setattr("MistHelper.org_id", old_org, raising=False)  # WHY: read by _attempt_login_and_finalize.

    return {
        "_print_switch_login_header": print_header,
        "_prompt_switch_login_confirmation": confirm,
        "_attempt_interactive_login_with_rollback": attempt_login,
        "_handle_interactive_login_success": handle_success,
        "old_session": old_session,
        "old_org_id": old_org,
    }


class TestResolveRuntimeDependencies:
    """The helper returns a SimpleNamespace + emits info/debug breadcrumbs."""

    def test_returns_namespace_with_misthelper_module(self) -> None:
        """The returned SimpleNamespace exposes the imported MistHelper module."""
        deps = _resolve_runtime_dependencies()  # WHY: exercise the helper end-to-end.
        assert isinstance(deps, SimpleNamespace)  # WHY: type contract.
        assert deps.misthelper_module.__name__ == "MistHelper"  # WHY: attribute is the real module.

    def test_emits_info_and_debug_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        """Before-import info log + after-import debug log both fire."""
        with caplog.at_level(logging.DEBUG, logger="root"):  # WHY: both levels visible.
            _resolve_runtime_dependencies()  # WHY: exercise the helper.
        messages = [rec.message for rec in caplog.records]  # WHY: aggregate for substring checks.
        assert any("Resolving SwitchToInteractiveLoginManager runtime" in m for m in messages)  # WHY: info log.
        assert any(
            "SwitchToInteractiveLoginManager runtime dependencies resolved" in m for m in messages
        )  # WHY: debug log.


class TestSwitchToInteractiveLoginManagerInit:
    """Constructor stashes the SimpleNamespace and emits init logs."""

    def test_init_populates_deps_namespace(self) -> None:
        """`self._deps` is a SimpleNamespace whose misthelper_module is the real module."""
        manager = SwitchToInteractiveLoginManager()  # WHY: exercise constructor.
        assert isinstance(manager._deps, SimpleNamespace)  # WHY: type contract.
        assert manager._deps.misthelper_module.__name__ == "MistHelper"  # WHY: module reference lives on the ns.

    def test_misthelper_returns_the_bound_module(self) -> None:
        """`_misthelper()` returns the same module referenced by `self._deps.misthelper_module`."""
        manager = SwitchToInteractiveLoginManager()  # WHY: baseline manager.
        assert manager._misthelper() is manager._deps.misthelper_module  # WHY: call-time identity check.


class TestSwitchToInteractiveLoginManagerRun:
    """`run()` orchestration: three branches (declined / failed / success)."""

    def test_run_declined_returns_true_and_skips_login(self, wired_misthelper: dict[str, Any]) -> None:
        """When the confirmation prompt returns False, no login attempt is made."""
        wired_misthelper["_prompt_switch_login_confirmation"].return_value = False  # WHY: user cancelled.
        manager = SwitchToInteractiveLoginManager()  # WHY: fresh manager under monkeypatched module.

        result = manager.run()  # WHY: exercise the decline branch.

        assert result is True  # WHY: always True so menu loop continues.
        wired_misthelper["_print_switch_login_header"].assert_called_once_with()  # WHY: banner shown first.
        wired_misthelper["_prompt_switch_login_confirmation"].assert_called_once_with()  # WHY: prompt fired.
        # WHY: no downstream login attempt or finalization on decline.
        wired_misthelper["_attempt_interactive_login_with_rollback"].assert_not_called()
        wired_misthelper["_handle_interactive_login_success"].assert_not_called()

    def test_run_login_failed_rolls_back_and_returns_true(self, wired_misthelper: dict[str, Any]) -> None:
        """When rollback-guarded login returns False, finalization is skipped."""
        wired_misthelper["_prompt_switch_login_confirmation"].return_value = True  # WHY: user consented.
        wired_misthelper["_attempt_interactive_login_with_rollback"].return_value = False  # WHY: login failed.
        manager = SwitchToInteractiveLoginManager()  # WHY: fresh manager.

        result = manager.run()  # WHY: exercise the failure branch.

        assert result is True  # WHY: run always returns True.
        # WHY: rollback helper called with the stashed old session + org id.
        wired_misthelper["_attempt_interactive_login_with_rollback"].assert_called_once_with(
            wired_misthelper["old_session"], wired_misthelper["old_org_id"]
        )
        # WHY: finalization skipped on failure.
        wired_misthelper["_handle_interactive_login_success"].assert_not_called()

    def test_run_login_succeeded_invokes_finalization(self, wired_misthelper: dict[str, Any]) -> None:
        """When rollback-guarded login returns True, finalization runs exactly once."""
        wired_misthelper["_prompt_switch_login_confirmation"].return_value = True  # WHY: user consented.
        wired_misthelper["_attempt_interactive_login_with_rollback"].return_value = True  # WHY: login succeeded.
        manager = SwitchToInteractiveLoginManager()  # WHY: fresh manager.

        result = manager.run()  # WHY: exercise the success branch.

        assert result is True  # WHY: run always returns True.
        wired_misthelper["_handle_interactive_login_success"].assert_called_once_with()  # WHY: finalization ran.

    def test_run_calls_ordered_pipeline(self, wired_misthelper: dict[str, Any]) -> None:
        """Pipeline order: banner -> confirm -> attempt -> handle_success on happy path."""
        wired_misthelper["_prompt_switch_login_confirmation"].return_value = True  # WHY: happy path.
        wired_misthelper["_attempt_interactive_login_with_rollback"].return_value = True  # WHY: happy path.
        manager = SwitchToInteractiveLoginManager()  # WHY: fresh manager.

        # WHY: use a call-order manager so we can assert relative ordering across mocks.
        order_manager = MagicMock()  # WHY: attach child mocks + inspect call order.
        order_manager.attach_mock(wired_misthelper["_print_switch_login_header"], "banner")
        order_manager.attach_mock(wired_misthelper["_prompt_switch_login_confirmation"], "confirm")
        order_manager.attach_mock(wired_misthelper["_attempt_interactive_login_with_rollback"], "attempt")
        order_manager.attach_mock(wired_misthelper["_handle_interactive_login_success"], "finalize")

        manager.run()  # WHY: exercise the full pipeline.

        assert order_manager.mock_calls == [  # WHY: exact ordering contract.
            call.banner(),
            call.confirm(),
            call.attempt(wired_misthelper["old_session"], wired_misthelper["old_org_id"]),
            call.finalize(),
        ]

    def test_run_reads_apisession_and_org_id_at_call_time(
        self, wired_misthelper: dict[str, Any], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """apisession + org_id are read at call time, honoring late rebinding after construction."""
        wired_misthelper["_prompt_switch_login_confirmation"].return_value = True  # WHY: reach rollback branch.
        wired_misthelper["_attempt_interactive_login_with_rollback"].return_value = False  # WHY: keeps test minimal.
        manager = SwitchToInteractiveLoginManager()  # WHY: construct before rebinding.
        # WHY: rebind the module attributes AFTER construction.
        new_session = MagicMock(name="new_apisession")
        monkeypatch.setattr("MistHelper.apisession", new_session, raising=False)
        monkeypatch.setattr("MistHelper.org_id", "new-org-id", raising=False)

        manager.run()  # WHY: exercise call-time attribute lookup.

        wired_misthelper["_attempt_interactive_login_with_rollback"].assert_called_once_with(
            new_session, "new-org-id"
        )  # WHY: rebound values are picked up at call time (getattr fallback).
