"""Wave 11 P2 coverage for src/auth/interactive/login_orchestrator.py (initiative #1018).

Covers every branch of ``LoginOrchestrator`` including:
- ``execute`` early-abort paths (mistapi missing, cloud cancelled, credentials cancelled) + success.
- ``_resolve_mistapi`` state cache hit, fallback import success, and ImportError.
- ``_collect_credentials`` email-None and password-None short-circuits.
- ``_authenticate`` exception dispatch to Connection / Value / generic handlers + happy path.
- ``_run_login_pipeline`` full sequence, apisession-None guard, 2FA prompt-cancel, auth-fail.
- ``_log_login_inputs``, ``_create_api_session`` (with None guard), ``_clear_pre_existing_token``.
- ``_initial_login``, ``_needs_two_factor`` (all 3 shapes), ``_handle_two_factor`` (None + success).
- ``_is_authenticated``, ``_report_auth_failure`` (dict error + string error + None response).
- ``_finalize_session``, ``_configure_session_timeout`` (success + swallowed error).
- ``_announce_msp_privileges`` (with grants + without grants).
- ``_handle_connection_error``, ``_handle_value_error`` (token+401 branch + generic branch).
- ``_handle_generic_error``, ``_print_generic_error_message`` (credential/2FA/401/fallback branches).
- ``_is_credential_error``, ``_is_two_factor_error`` substring guards.

No live network, no MistHelper import touched. MagicMock(spec=...) mandatory on stubs.
"""

from __future__ import annotations  # WHY: PEP 604 unions in test type hints.

import logging  # WHY: caplog verification of structured warning/info/debug lines.
from collections.abc import Callable  # WHY: Callable typing for injected fake callbacks.
from typing import Any, cast  # WHY: dict[str, Any] annotations + cast(Any, x) for dynamic attr writes.
from unittest.mock import MagicMock, patch  # WHY: mandatory spec= mocks + patch decorators.

import pytest  # WHY: fixtures + parametrize.

from src.auth.interactive.clouds import CloudSelector  # WHY: shared class object for patch.object.
from src.auth.interactive.credential_prompter import CredentialPrompter  # WHY: shared class for patch.object.
from src.auth.interactive.login_orchestrator import LoginOrchestrator  # WHY: SUT direct import.


def _make_orchestrator(
    state: dict[str, Any] | None = None,
    safe_input: Callable[..., str] | None = None,
    detect_msp_privileges: Callable[[], list[dict[str, Any]]] | None = None,
) -> LoginOrchestrator:
    """Build a LoginOrchestrator with minimal stub collaborators for unit tests."""
    return LoginOrchestrator(
        state=state if state is not None else {},  # WHY: fresh mutable state per test.
        safe_input=safe_input or MagicMock(spec=Callable, return_value=""),  # WHY: default no-op input.
        detect_msp_privileges=detect_msp_privileges or MagicMock(spec=Callable, return_value=[]),
    )


class TestExecute:
    """``execute`` orchestrates the full login flow with 3 early-exit branches."""

    def test_returns_false_when_mistapi_unavailable(self, caplog: pytest.LogCaptureFixture) -> None:
        """When _resolve_mistapi returns None, execute short-circuits with False."""
        orch = _make_orchestrator()  # WHY: default orchestrator with empty state.
        with (
            patch.object(LoginOrchestrator, "_resolve_mistapi", return_value=None),
            caplog.at_level(logging.DEBUG),
        ):
            assert orch.execute() is False  # WHY: SUT contract: propagate failure.
        assert "aborted: mistapi unavailable" in caplog.text  # WHY: legacy debug log.

    def test_returns_false_when_cloud_cancelled(self, caplog: pytest.LogCaptureFixture) -> None:
        """When CloudSelector.prompt returns None, execute short-circuits with False."""
        orch = _make_orchestrator()  # WHY: default orchestrator with empty state.
        with (
            patch.object(LoginOrchestrator, "_resolve_mistapi", return_value=MagicMock(spec=object)),
            patch.object(CloudSelector, "prompt", return_value=None),
            caplog.at_level(logging.DEBUG),
        ):
            assert orch.execute() is False  # WHY: SUT contract: propagate failure.
        assert "cloud selection cancelled" in caplog.text  # WHY: legacy debug log.

    def test_returns_false_when_credentials_cancelled(self, caplog: pytest.LogCaptureFixture) -> None:
        """When _collect_credentials returns None, execute short-circuits with False."""
        orch = _make_orchestrator()  # WHY: default orchestrator with empty state.
        with (
            patch.object(LoginOrchestrator, "_resolve_mistapi", return_value=MagicMock(spec=object)),
            patch.object(CloudSelector, "prompt", return_value=("Global 01", "api.mist.com")),
            patch.object(LoginOrchestrator, "_collect_credentials", return_value=None),
            caplog.at_level(logging.DEBUG),
        ):
            assert orch.execute() is False  # WHY: SUT contract: propagate failure.
        assert "credential collection cancelled" in caplog.text  # WHY: legacy debug log.

    def test_success_delegates_to_authenticate(self) -> None:
        """Happy path: unpacks cloud + credentials and calls _authenticate with them."""
        fake_sdk = MagicMock(spec=object)  # WHY: opaque SDK reference passed through.
        orch = _make_orchestrator()  # WHY: default orchestrator with empty state.
        with (
            patch.object(LoginOrchestrator, "_resolve_mistapi", return_value=fake_sdk),
            patch.object(CloudSelector, "prompt", return_value=("Global 02", "api.gc1.mist.com")),
            patch.object(LoginOrchestrator, "_collect_credentials", return_value=("u@e.com", "pw")),
            patch.object(LoginOrchestrator, "_authenticate", return_value=True) as fake_auth,
        ):
            assert orch.execute() is True  # WHY: SUT returns _authenticate's return.
        fake_auth.assert_called_once_with(fake_sdk, "Global 02", "api.gc1.mist.com", "u@e.com", "pw")


class TestResolveMistapi:
    """``_resolve_mistapi`` prefers state, else fallback-imports, and handles ImportError."""

    def test_returns_state_reference_when_present(self) -> None:
        """State already has mistapi → use it and skip the import."""
        stub_sdk = MagicMock(spec=object)  # WHY: opaque SDK reference sitting in state.
        orch = _make_orchestrator(state={"mistapi": stub_sdk})
        assert orch._resolve_mistapi() is stub_sdk  # WHY: fast-path returns state value.

    def test_fallback_import_succeeds_and_caches_in_state(self, caplog: pytest.LogCaptureFixture) -> None:
        """When state has no mistapi, the fallback import path caches the SDK in state."""
        orch = _make_orchestrator()  # WHY: empty state triggers fallback branch.
        with caplog.at_level(logging.DEBUG):
            resolved = orch._resolve_mistapi()
        # We do not assert the exact module identity (fallback imports the real mistapi package)
        # but we assert it is not None and was cached back to state.
        assert resolved is not None  # WHY: SUT returned the SDK reference.
        assert orch.state["mistapi"] is resolved  # WHY: cache-back contract.
        assert "Resolving mistapi SDK via fallback import" in caplog.text  # WHY: pre-action info log.

    def test_fallback_import_error_returns_none(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
    ) -> None:
        """When mistapi cannot be imported, log error, print banner, return None."""
        import builtins  # WHY: patch built-in __import__ to inject the ImportError.

        real_import = builtins.__import__  # WHY: cache real import to preserve unrelated imports.

        def _fail_only_mistapi(
            name: str, globals: Any = None, locals: Any = None, fromlist: Any = (), level: int = 0
        ) -> Any:
            if name == "mistapi":  # WHY: narrow the failure to the SUT's target.
                raise ImportError("boom")
            return real_import(name, globals, locals, fromlist, level)

        monkeypatch.setattr(builtins, "__import__", _fail_only_mistapi)
        orch = _make_orchestrator()  # WHY: empty state triggers fallback branch.
        with caplog.at_level(logging.ERROR):
            assert orch._resolve_mistapi() is None  # WHY: SUT returns None on ImportError.
        captured = capsys.readouterr()
        assert "X Failed to import mistapi library" in captured.out  # WHY: legacy console message.
        assert "Cannot import mistapi: boom" in caplog.text  # WHY: legacy error log preserved.


class TestCollectCredentials:
    """``_collect_credentials`` short-circuits on email None or password None."""

    def test_returns_none_when_email_none(self) -> None:
        """Email None → return None without prompting for password."""
        orch = _make_orchestrator()  # WHY: default orchestrator with empty state.
        with patch.object(CredentialPrompter, "prompt_email", return_value=None):
            with patch.object(CredentialPrompter, "prompt_password") as fake_pw:
                assert orch._collect_credentials() is None  # WHY: SUT contract.
                fake_pw.assert_not_called()  # WHY: guard clause skips password prompt.

    def test_returns_none_when_password_none(self) -> None:
        """Password None → return None even though email was captured."""
        orch = _make_orchestrator()  # WHY: default orchestrator with empty state.
        with (
            patch.object(CredentialPrompter, "prompt_email", return_value="u@e.com"),
            patch.object(CredentialPrompter, "prompt_password", return_value=None),
        ):
            assert orch._collect_credentials() is None  # WHY: SUT contract.

    def test_returns_credentials_tuple_on_success(self) -> None:
        """Both prompts succeed → tuple returned."""
        orch = _make_orchestrator()  # WHY: default orchestrator with empty state.
        with (
            patch.object(CredentialPrompter, "prompt_email", return_value="u@e.com"),
            patch.object(CredentialPrompter, "prompt_password", return_value="pw"),
        ):
            assert orch._collect_credentials() == ("u@e.com", "pw")  # WHY: SUT contract.


class TestAuthenticate:
    """``_authenticate`` dispatches exceptions to the matching handler."""

    def test_happy_path_delegates_to_pipeline(self, capsys: pytest.CaptureFixture[str]) -> None:
        """No exception → returns whatever _run_login_pipeline returned."""
        orch = _make_orchestrator()  # WHY: default orchestrator with empty state.
        with patch.object(LoginOrchestrator, "_run_login_pipeline", return_value=True) as fake_pipe:
            result = orch._authenticate(MagicMock(spec=object), "Global 01", "api.mist.com", "u@e.com", "pw")
        assert result is True  # WHY: SUT contract.
        fake_pipe.assert_called_once()  # WHY: exactly one delegation call.
        assert "Authenticating..." in capsys.readouterr().out  # WHY: legacy console banner.

    def test_connection_error_dispatched(self) -> None:
        """ConnectionError → routed to _handle_connection_error and returns False."""
        exc = ConnectionError("no route")  # WHY: reference kept to assert delegation arg.
        orch = _make_orchestrator()  # WHY: default orchestrator with empty state.
        with (
            patch.object(LoginOrchestrator, "_run_login_pipeline", side_effect=exc),
            patch.object(LoginOrchestrator, "_handle_connection_error", return_value=False) as fake_conn,
        ):
            assert orch._authenticate(MagicMock(spec=object), "c", "h", "e", "p") is False
        fake_conn.assert_called_once_with(exc)  # WHY: dispatch preserves the exception object.

    def test_value_error_dispatched(self) -> None:
        """ValueError → routed to _handle_value_error and returns False."""
        exc = ValueError("bad token")
        orch = _make_orchestrator()
        with (
            patch.object(LoginOrchestrator, "_run_login_pipeline", side_effect=exc),
            patch.object(LoginOrchestrator, "_handle_value_error", return_value=False) as fake_ve,
        ):
            assert orch._authenticate(MagicMock(spec=object), "c", "h", "e", "p") is False
        fake_ve.assert_called_once_with(exc)  # WHY: dispatch preserves the exception object.

    def test_generic_error_dispatched(self) -> None:
        """Any other Exception → routed to _handle_generic_error and returns False."""
        exc = RuntimeError("boom")
        orch = _make_orchestrator()
        with (
            patch.object(LoginOrchestrator, "_run_login_pipeline", side_effect=exc),
            patch.object(LoginOrchestrator, "_handle_generic_error", return_value=False) as fake_gen,
        ):
            assert orch._authenticate(MagicMock(spec=object), "c", "h", "e", "p") is False
        fake_gen.assert_called_once_with(exc)  # WHY: dispatch preserves the exception object.


class TestRunLoginPipeline:
    """``_run_login_pipeline`` walks create-session / login / 2FA / finalize sequence."""

    def test_returns_false_when_apisession_is_none(self) -> None:
        """APISession constructor returned None → propagate False without touching login."""
        orch = _make_orchestrator()
        with (
            patch.object(LoginOrchestrator, "_log_login_inputs"),
            patch.object(LoginOrchestrator, "_create_api_session", return_value=None),
            patch.object(LoginOrchestrator, "_initial_login") as fake_initial,
        ):
            assert orch._run_login_pipeline(MagicMock(spec=object), "h", "e", "p") is False
        fake_initial.assert_not_called()  # WHY: guard skips downstream calls.

    def test_returns_false_when_two_factor_cancelled(self) -> None:
        """2FA prompt cancelled → _handle_two_factor returned None → False."""
        orch = _make_orchestrator()
        fake_session = MagicMock(spec=object)
        with (
            patch.object(LoginOrchestrator, "_log_login_inputs"),
            patch.object(LoginOrchestrator, "_create_api_session", return_value=fake_session),
            patch.object(LoginOrchestrator, "_initial_login", return_value={"error": {"two_factor_required": True}}),
            patch.object(LoginOrchestrator, "_handle_two_factor", return_value=None),
            patch.object(LoginOrchestrator, "_finalize_session") as fake_final,
        ):
            assert orch._run_login_pipeline(MagicMock(spec=object), "h", "e", "p") is False
        fake_final.assert_not_called()  # WHY: 2FA cancellation skips finalize.

    def test_returns_false_when_not_authenticated(self) -> None:
        """Login result not authenticated → _report_auth_failure invoked and False returned."""
        orch = _make_orchestrator()
        fake_session = MagicMock(spec=object)
        login_result = {"authenticated": False, "error": "bad creds"}  # WHY: post-2FA failure surface.
        with (
            patch.object(LoginOrchestrator, "_log_login_inputs"),
            patch.object(LoginOrchestrator, "_create_api_session", return_value=fake_session),
            patch.object(LoginOrchestrator, "_initial_login", return_value=login_result),
            patch.object(LoginOrchestrator, "_report_auth_failure") as fake_report,
            patch.object(LoginOrchestrator, "_finalize_session") as fake_final,
        ):
            assert orch._run_login_pipeline(MagicMock(spec=object), "h", "e", "p") is False
        fake_report.assert_called_once_with(login_result)  # WHY: legacy contract.
        fake_final.assert_not_called()  # WHY: no finalize on auth failure.

    def test_returns_true_on_full_happy_path(self) -> None:
        """Login authenticated → _finalize_session invoked and True returned."""
        orch = _make_orchestrator()
        fake_session = MagicMock(spec=object)
        login_result = {"authenticated": True}
        with (
            patch.object(LoginOrchestrator, "_log_login_inputs"),
            patch.object(LoginOrchestrator, "_create_api_session", return_value=fake_session),
            patch.object(LoginOrchestrator, "_initial_login", return_value=login_result),
            patch.object(LoginOrchestrator, "_finalize_session") as fake_final,
        ):
            assert orch._run_login_pipeline(MagicMock(spec=object), "h", "e-mail", "p") is True
        fake_final.assert_called_once_with(fake_session, "e-mail", "h")  # WHY: legacy contract.


class TestLogLoginInputs:
    """``_log_login_inputs`` emits three legacy debug lines."""

    def test_emits_three_debug_lines(self, caplog: pytest.LogCaptureFixture) -> None:
        """host, email and password length are debug-logged separately."""
        with caplog.at_level(logging.DEBUG):
            LoginOrchestrator._log_login_inputs("api.mist.com", "u@e.com", "hunter2")
        assert "host: api.mist.com" in caplog.text  # WHY: legacy line 1.
        assert "email: u@e.com" in caplog.text  # WHY: legacy line 2.
        assert "password length: 7" in caplog.text  # WHY: legacy line 3.

    def test_empty_password_logs_length_zero(self, caplog: pytest.LogCaptureFixture) -> None:
        """Empty password logs length 0 (short-circuit protects len())."""
        with caplog.at_level(logging.DEBUG):
            LoginOrchestrator._log_login_inputs("h", "e", "")
        assert "password length: 0" in caplog.text  # WHY: SUT ternary contract.


class TestCreateApiSession:
    """``_create_api_session`` constructs SDK session and clears the pre-existing token."""

    def test_none_session_returns_none_and_warns(
        self, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
    ) -> None:
        """When APISession returns None, log error, print banner, return None."""
        fake_sdk = MagicMock()  # WHY: unspec'd because we swap the constructor attribute.
        fake_sdk.APISession = MagicMock(return_value=None)  # WHY: soft-failure surface.
        with caplog.at_level(logging.ERROR):
            result = LoginOrchestrator._create_api_session(fake_sdk, "h", "e", "p")
        assert result is None  # WHY: SUT contract.
        assert "X Failed to create API session" in capsys.readouterr().out  # WHY: legacy console.
        assert "APISession constructor returned None" in caplog.text  # WHY: legacy error log.

    def test_returns_session_and_clears_token(self) -> None:
        """Successful construction returns the session and clears any cached token."""
        fake_session = MagicMock()  # WHY: attributes _apitoken + _apitoken_index accessed in helper.
        fake_session._apitoken = ["tok1"]  # WHY: force the clear branch in _clear_pre_existing_token.
        fake_session._apitoken_index = 0
        fake_sdk = MagicMock()
        fake_sdk.APISession = MagicMock(return_value=fake_session)
        with patch.object(LoginOrchestrator, "_clear_pre_existing_token") as fake_clear:
            result = LoginOrchestrator._create_api_session(fake_sdk, "h", "e", "p")
        assert result is fake_session  # WHY: session handed back to caller.
        fake_clear.assert_called_once_with(fake_session)  # WHY: token clear helper invoked.
        fake_sdk.APISession.assert_called_once_with(
            email="e", password="p", host="h", console_log_level=20, show_cli_notif=False
        )  # WHY: SUT kwargs must match legacy signature verbatim.


class TestClearPreExistingToken:
    """``_clear_pre_existing_token`` fast-exits on empty token, clears otherwise."""

    def test_no_token_is_noop(self) -> None:
        """Empty apisession._apitoken skips the clear branch."""
        fake_session = MagicMock()  # WHY: unspec'd to allow arbitrary attribute reads.
        fake_session._apitoken = []  # WHY: empty list means no token to clear.
        LoginOrchestrator._clear_pre_existing_token(fake_session)  # SUT should return without touching state.
        assert fake_session._apitoken == []  # WHY: unchanged.

    def test_clears_token_and_resets_index(self, caplog: pytest.LogCaptureFixture) -> None:
        """Non-empty token → cleared to [] and index reset to -1."""
        fake_session = MagicMock()
        fake_session._apitoken = ["tok1", "tok2"]  # WHY: two tokens forces len()==2 in the log line.
        fake_session._apitoken_index = 1
        with caplog.at_level(logging.DEBUG):
            LoginOrchestrator._clear_pre_existing_token(fake_session)
        assert fake_session._apitoken == []  # WHY: SUT resets token cache.
        assert fake_session._apitoken_index == -1  # WHY: SUT resets cursor.
        assert "Clearing API token to force email/password login (had 2 token(s))" in caplog.text


class TestInitialLogin:
    """``_initial_login`` invokes login_with_return() and returns the raw result."""

    def test_returns_apisession_result(self, caplog: pytest.LogCaptureFixture) -> None:
        """SDK response flows back verbatim; debug log records authentication flag."""
        fake_session = MagicMock()
        fake_session.login_with_return = MagicMock(return_value={"authenticated": True})
        with caplog.at_level(logging.DEBUG):
            result = LoginOrchestrator._initial_login(fake_session)
        assert result == {"authenticated": True}  # WHY: verbatim passthrough.
        assert "Initial login returned authenticated=True" in caplog.text  # WHY: legacy debug log.


class TestNeedsTwoFactor:
    """``_needs_two_factor`` handles three shapes: standard dict, legacy top-level, None."""

    def test_none_result_returns_false(self) -> None:
        """None login result → not required."""
        assert LoginOrchestrator._needs_two_factor(None) is False

    def test_empty_dict_returns_false(self) -> None:
        """Empty dict → not required."""
        assert LoginOrchestrator._needs_two_factor({}) is False

    def test_standard_shape_error_dict_returns_true(self) -> None:
        """{'error': {'two_factor_required': True}} → True."""
        assert LoginOrchestrator._needs_two_factor({"error": {"two_factor_required": True}}) is True

    def test_legacy_top_level_shape_returns_true(self) -> None:
        """{'two_factor_required': True} → True (legacy fallback)."""
        assert LoginOrchestrator._needs_two_factor({"two_factor_required": True}) is True

    def test_non_dict_error_field_falls_through_to_top_level(self) -> None:
        """error field that is not a dict falls through to the top-level check."""
        assert LoginOrchestrator._needs_two_factor({"error": "some string", "two_factor_required": True}) is True


class TestHandleTwoFactor:
    """``_handle_two_factor`` prompts for 2FA and replays the login."""

    def test_none_when_user_aborts(self, capsys: pytest.CaptureFixture[str]) -> None:
        """CredentialPrompter returns None → state cleared and None propagated."""
        orch = _make_orchestrator()
        orch.state["apisession"] = "stale"  # WHY: pre-existing partial session must be cleared.
        fake_session = MagicMock()
        with patch.object(CredentialPrompter, "prompt_two_factor", return_value=None):
            result = orch._handle_two_factor(fake_session)
        assert result is None  # WHY: SUT contract.
        assert orch.state["apisession"] is None  # WHY: partial session cleared.
        assert "Two-factor authentication required." in capsys.readouterr().out  # WHY: legacy banner.

    def test_success_calls_login_with_return_with_two_factor(self, caplog: pytest.LogCaptureFixture) -> None:
        """Prompt returns a code → login_with_return replayed with two_factor kwarg."""
        orch = _make_orchestrator()
        fake_session = MagicMock()
        fake_session.login_with_return = MagicMock(return_value={"authenticated": True})
        with patch.object(CredentialPrompter, "prompt_two_factor", return_value="123456"):
            with caplog.at_level(logging.DEBUG):
                result = orch._handle_two_factor(fake_session)
        assert result == {"authenticated": True}  # WHY: SUT contract.
        fake_session.login_with_return.assert_called_once_with(two_factor="123456")  # WHY: kwargs shape.
        assert "2FA login returned authenticated=True" in caplog.text  # WHY: legacy debug log.


class TestIsAuthenticated:
    """``_is_authenticated`` returns bool based on 'authenticated' key."""

    @pytest.mark.parametrize(
        ("payload", "expected"),
        [
            (None, False),  # WHY: None response → False.
            ({}, False),  # WHY: missing key → False.
            ({"authenticated": False}, False),  # WHY: explicit False → False.
            ({"authenticated": True}, True),  # WHY: explicit True → True.
        ],
    )
    def test_authenticated_branch(self, payload: dict[str, Any] | None, expected: bool) -> None:
        """The 4-way truth table for the SUT contract."""
        assert LoginOrchestrator._is_authenticated(payload) is expected


class TestReportAuthFailure:
    """``_report_auth_failure`` prints legacy message and clears state."""

    def test_none_response_uses_no_response_default(
        self, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
    ) -> None:
        """None login result → 'No response' is printed and logged."""
        orch = _make_orchestrator()
        with caplog.at_level(logging.ERROR):
            orch._report_auth_failure(None)
        assert "X Authentication failed: No response" in capsys.readouterr().out  # WHY: legacy.
        assert "Interactive login failed: No response" in caplog.text  # WHY: legacy.
        assert orch.state["apisession"] is None  # WHY: state cleanup.

    def test_dict_error_uses_detail_field(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Error dict → the 'detail' field is preferred."""
        orch = _make_orchestrator()
        orch._report_auth_failure({"error": {"detail": "bad token"}})
        assert "X Authentication failed: bad token" in capsys.readouterr().out  # WHY: detail wins.

    def test_dict_error_without_detail_uses_string(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Error dict without 'detail' → falls back to str(dict)."""
        orch = _make_orchestrator()
        orch._report_auth_failure({"error": {"code": 401}})
        out = capsys.readouterr().out
        assert "X Authentication failed:" in out  # WHY: prefix preserved.
        assert "401" in out  # WHY: dict-string contains the code.

    def test_string_error_used_verbatim(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Non-dict error field is used verbatim (coerced to str)."""
        orch = _make_orchestrator()
        orch._report_auth_failure({"error": "bad creds"})
        assert "X Authentication failed: bad creds" in capsys.readouterr().out  # WHY: verbatim.

    def test_missing_error_field_uses_unknown_default(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Missing 'error' key → 'Unknown error' default."""
        orch = _make_orchestrator()
        orch._report_auth_failure({"authenticated": False})
        assert "X Authentication failed: Unknown error" in capsys.readouterr().out  # WHY: legacy default.


class TestFinalizeSession:
    """``_finalize_session`` caches session, configures timeout, announces MSPs."""

    def test_full_finalize_sequence(self, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture) -> None:
        """State cached, timeout configured, MSP privileges announced."""
        orch = _make_orchestrator()
        fake_session = MagicMock(spec=object)
        with (
            patch.object(LoginOrchestrator, "_configure_session_timeout") as fake_timeout,
            patch.object(LoginOrchestrator, "_announce_msp_privileges") as fake_msp,
            caplog.at_level(logging.INFO),
        ):
            orch._finalize_session(fake_session, "u@e.com", "api.mist.com")
        assert orch.state["apisession"] is fake_session  # WHY: state cache-back.
        fake_timeout.assert_called_once_with(fake_session)  # WHY: timeout helper invoked.
        fake_msp.assert_called_once()  # WHY: MSP announcement invoked.
        assert "+ Login successful!" in capsys.readouterr().out  # WHY: legacy console.
        assert "Interactive login successful for u@e.com to api.mist.com" in caplog.text  # WHY: legacy log.


class TestConfigureSessionTimeout:
    """``_configure_session_timeout`` best-effort delegation to session_timeout helper."""

    def test_success_delegates_to_helper(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Import succeeds → helper called with the session."""
        import sys  # WHY: inject a fake module into sys.modules for deferred import.
        import types  # WHY: build a ModuleType stub for the deferred import target.

        fake_module = types.ModuleType("src.auth.session_timeout")  # WHY: real module type for import machinery.
        fake_helper = MagicMock()  # WHY: replaced helper we can assert on.
        cast(Any, fake_module).configure_session_timeout = fake_helper  # WHY: cast(Any) satisfies mypy + ruff.
        monkeypatch.setitem(sys.modules, "src.auth.session_timeout", fake_module)
        fake_session = MagicMock(spec=object)
        LoginOrchestrator._configure_session_timeout(fake_session)
        fake_helper.assert_called_once_with(fake_session)  # WHY: delegation contract.

    def test_swallowed_exception_does_not_propagate(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Helper raises → SUT swallows silently (legacy contract)."""
        import sys  # WHY: inject fake module for the deferred import.
        import types  # WHY: build a ModuleType stub.

        fake_module = types.ModuleType("src.auth.session_timeout")

        def _boom(_session: Any) -> None:
            raise RuntimeError("timeout wiring broken")  # WHY: reach the except Exception branch.

        cast(Any, fake_module).configure_session_timeout = _boom  # WHY: cast(Any) satisfies mypy + ruff.
        monkeypatch.setitem(sys.modules, "src.auth.session_timeout", fake_module)
        LoginOrchestrator._configure_session_timeout(MagicMock(spec=object))  # SUT should not raise.

    def test_missing_module_swallowed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When the deferred import fails, the SUT swallows the ImportError silently."""
        import sys  # WHY: force ImportError by ensuring the target key is not in sys.modules.

        monkeypatch.delitem(sys.modules, "src.auth.session_timeout", raising=False)
        LoginOrchestrator._configure_session_timeout(MagicMock(spec=object))  # SUT should not raise.


class TestAnnounceMspPrivileges:
    """``_announce_msp_privileges`` echoes MSP grants or the empty-list banner."""

    def test_with_grants_populates_state_and_echoes_each(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Non-empty grants → state cached and each grant printed."""
        grants = [
            {"msp_name": "MSP-A", "role": "admin"},  # WHY: two grants exercises the loop.
            {"msp_name": "MSP-B", "role": "viewer"},
        ]
        detect_fn = MagicMock(spec=Callable, return_value=grants)
        orch = _make_orchestrator(detect_msp_privileges=detect_fn)
        orch._announce_msp_privileges()
        out = capsys.readouterr().out
        assert orch.state["msp_privileges"] == grants  # WHY: cache-back.
        assert "MSP access detected: 2 MSP(s) available" in out  # WHY: legacy banner.
        assert "- MSP-A (role: admin)" in out  # WHY: per-grant line.
        assert "- MSP-B (role: viewer)" in out  # WHY: per-grant line.

    def test_no_grants_prints_org_level_message(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Empty grants list → org-level banner printed and state untouched."""
        detect_fn = MagicMock(spec=Callable, return_value=[])
        orch = _make_orchestrator(detect_msp_privileges=detect_fn)
        orch._announce_msp_privileges()
        out = capsys.readouterr().out
        assert "No MSP privileges detected (org-level access only)" in out  # WHY: legacy banner.
        assert "msp_privileges" not in orch.state  # WHY: state left untouched.


class TestHandleConnectionError:
    """``_handle_connection_error`` prints legacy line + logs + clears state."""

    def test_prints_and_logs_and_clears_state(
        self, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
    ) -> None:
        orch = _make_orchestrator()
        orch.state["apisession"] = "partial"  # WHY: verify cleanup runs.
        exc = ConnectionError("network down")
        with caplog.at_level(logging.ERROR):
            assert orch._handle_connection_error(exc) is False  # WHY: contract.
        assert "X Connection failed: network down" in capsys.readouterr().out  # WHY: legacy console.
        assert "Interactive login connection error: network down" in caplog.text  # WHY: legacy log.
        assert orch.state["apisession"] is None  # WHY: state cleared.


class TestHandleValueError:
    """``_handle_value_error`` branches on 'token'/'401' substrings."""

    def test_token_branch_uses_generic_line(
        self, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
    ) -> None:
        """'token' substring → 'Invalid API token or credentials' line."""
        orch = _make_orchestrator()
        exc = ValueError("bad token payload")
        with caplog.at_level(logging.ERROR):
            assert orch._handle_value_error(exc) is False
        assert "X Invalid API token or credentials" in capsys.readouterr().out  # WHY: specific branch.
        assert "Interactive login value error: bad token payload" in caplog.text  # WHY: legacy log.
        assert orch.state["apisession"] is None  # WHY: state cleared.

    def test_401_branch_uses_generic_line(self, capsys: pytest.CaptureFixture[str]) -> None:
        """'401' substring → same 'Invalid API token or credentials' line."""
        orch = _make_orchestrator()
        exc = ValueError("HTTP 401 returned")
        orch._handle_value_error(exc)
        assert "X Invalid API token or credentials" in capsys.readouterr().out  # WHY: specific branch.

    def test_generic_branch_uses_error_verbatim(self, capsys: pytest.CaptureFixture[str]) -> None:
        """No token / 401 substring → verbatim 'Authentication error: ...' line."""
        orch = _make_orchestrator()
        exc = ValueError("some random validation")
        orch._handle_value_error(exc)
        assert "X Authentication error: some random validation" in capsys.readouterr().out


class TestHandleGenericError:
    """``_handle_generic_error`` prints via helper + logs + clears state."""

    def test_delegates_and_clears_state(self, caplog: pytest.LogCaptureFixture) -> None:
        orch = _make_orchestrator()
        orch.state["apisession"] = "partial"
        exc = RuntimeError("kaboom")
        with (
            patch.object(LoginOrchestrator, "_print_generic_error_message") as fake_print,
            caplog.at_level(logging.ERROR),
        ):
            assert orch._handle_generic_error(exc) is False  # WHY: contract.
        fake_print.assert_called_once_with(exc, "kaboom", "kaboom")  # WHY: helper receives 3 args.
        assert "Interactive login failed: kaboom" in caplog.text  # WHY: legacy log.
        assert orch.state["apisession"] is None  # WHY: state cleared.


class TestPrintGenericErrorMessage:
    """``_print_generic_error_message`` branches: credential / 2FA / 401 / fallback."""

    def test_credential_branch(self, capsys: pytest.CaptureFixture[str]) -> None:
        """'invalid' substring → credential message."""
        LoginOrchestrator._print_generic_error_message(RuntimeError("x"), "invalid whatever", "invalid whatever")
        assert "X Invalid email or password" in capsys.readouterr().out

    def test_two_factor_branch(self, capsys: pytest.CaptureFixture[str]) -> None:
        """'2fa' substring → 2FA message."""
        LoginOrchestrator._print_generic_error_message(RuntimeError("x"), "2fa broken", "2fa broken")
        assert "X Two-factor authentication failed" in capsys.readouterr().out

    def test_401_branch(self, capsys: pytest.CaptureFixture[str]) -> None:
        """'401' substring in the original error message → auth-failure message."""
        LoginOrchestrator._print_generic_error_message(RuntimeError("x"), "HTTP 401", "http 401")
        assert "X Invalid email or password (authentication failed)" in capsys.readouterr().out

    def test_fallback_branch(self, capsys: pytest.CaptureFixture[str]) -> None:
        """No matching substring → generic 'X Login failed: <exc>' line."""
        exc = RuntimeError("mystery")  # WHY: __str__ used in the fallback line.
        LoginOrchestrator._print_generic_error_message(exc, "mystery", "mystery")
        assert "X Login failed: mystery" in capsys.readouterr().out


class TestIsCredentialError:
    """``_is_credential_error`` short substring guard."""

    @pytest.mark.parametrize(
        ("lower_message", "expected"),
        [
            ("invalid credentials", True),  # WHY: both substrings.
            ("invalid input", True),  # WHY: 'invalid' only.
            ("bad credential value", True),  # WHY: 'credential' only.
            ("unrelated", False),  # WHY: neither.
        ],
    )
    def test_substring_guard(self, lower_message: str, expected: bool) -> None:
        assert LoginOrchestrator._is_credential_error(lower_message) is expected


class TestIsTwoFactorError:
    """``_is_two_factor_error`` short substring guard."""

    @pytest.mark.parametrize(
        ("lower_message", "expected"),
        [
            ("two_factor required", True),  # WHY: 'two_factor' snake form.
            ("2fa code", True),  # WHY: '2fa' short form.
            ("unrelated failure", False),  # WHY: neither.
        ],
    )
    def test_substring_guard(self, lower_message: str, expected: bool) -> None:
        assert LoginOrchestrator._is_two_factor_error(lower_message) is expected
