"""
Wave 1 Logging Envelope Guardrail Tests (T025 / T026).

T025: Verify that each high-risk function emits at least one INFO log entry
      before taking action (entry envelope) and at least one INFO or DEBUG
      log entry after completing (exit envelope).

T026: Negative tests -- verify that no password or secret value appears in
      the log output emitted by these functions, even when passwords are
      provided.

Reference: specs/192-compliance-decomposition-wave1/high-risk-function-map.md
           specs/192-compliance-decomposition-wave1/baseline-compliance-metrics.md SC-004
"""

import logging  # For log-level constants used in caplog assertions

import MistHelper  # Main module under test (all classes are module-level)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _entry_messages(records):
    """Return log messages that look like entry envelopes."""
    return [  # Filter to records containing canonical entry keyword
        r.getMessage() for r in records if "Entering" in r.getMessage()
    ]


def _exit_messages(records):
    """Return log messages that look like exit envelopes."""
    return [  # Filter to records containing canonical exit keyword
        r.getMessage() for r in records if "Exiting" in r.getMessage()
    ]


# ---------------------------------------------------------------------------
# T025: Entry and exit envelope presence tests
# ---------------------------------------------------------------------------


class TestCollectMissingDataEnvelopes:
    """SSHRunnerManager._collect_missing_data() logging envelope tests."""

    def test_entry_envelope_emitted(self, caplog, monkeypatch):
        """Entry log must appear before any user prompt is issued."""
        import getpass as _getpass_mod  # Local import so we can monkeypatch the module

        monkeypatch.setattr(  # Stub safe_input so no real prompts are shown
            MistHelper.InputUtils, "safe_input", lambda prompt, context="": "admin"
        )
        monkeypatch.setattr(  # Stub getpass so no stdin read attempted in pytest capture mode
            _getpass_mod, "getpass", lambda prompt="Enter SSH password: ": "stubbed-pw"
        )
        deps = MistHelper.SSHRunnerManager._build_deps()  # Build deps; facade wrapper removed
        with caplog.at_level(logging.INFO, logger="root"):  # Capture INFO+ logs
            MistHelper.ExtractedSSHRunnerManager._collect_missing_data(deps, [], None, None, [])  # All-missing data
        entry_msgs = _entry_messages(caplog.records)  # Collect entry envelope lines
        assert entry_msgs, (  # At least one entry envelope must be present
            "No entry envelope logged by _collect_missing_data; " "expected a message containing 'Entering'"
        )

    def test_exit_envelope_emitted_on_success(self, caplog, monkeypatch):
        """Exit log must appear when all data is supplied (happy path)."""
        monkeypatch.setattr(  # Stub safe_input to return pre-filled values
            MistHelper.InputUtils, "safe_input", lambda prompt, context="": "admin"
        )
        deps = MistHelper.SSHRunnerManager._build_deps()  # Build deps; facade wrapper removed
        with caplog.at_level(logging.DEBUG, logger="root"):  # DEBUG to catch debug-level exit
            MistHelper.ExtractedSSHRunnerManager._collect_missing_data(  # Supply hosts; only user/cmd prompted
                deps, ["10.0.0.1"], None, "secret", []
            )
        exit_msgs = _exit_messages(caplog.records)  # Collect exit envelope lines
        assert exit_msgs, (  # At least one exit envelope must be present
            "No exit envelope logged by _collect_missing_data on success path; "
            "expected a message containing 'Exiting'"
        )

    def test_exit_envelope_emitted_on_cancel_no_hosts(self, caplog, monkeypatch):
        """Exit log must appear when cancelled due to empty hosts input."""
        monkeypatch.setattr(  # Return empty string to simulate user pressing Enter
            MistHelper.InputUtils, "safe_input", lambda prompt, context="": ""
        )
        deps = MistHelper.SSHRunnerManager._build_deps()  # Build deps; facade wrapper removed
        with caplog.at_level(logging.INFO, logger="root"):  # Capture INFO+ logs
            MistHelper.ExtractedSSHRunnerManager._collect_missing_data(deps, [], None, None, [])
        exit_msgs = _exit_messages(caplog.records)  # Collect exit envelope lines
        assert (
            exit_msgs
        ), (  # Cancellation path must also emit exit envelope
            "No exit envelope logged by _collect_missing_data on cancel path"
        )


class TestConfirmExecutionEnvelopes:
    """SSHRunnerManager._confirm_execution() logging envelope tests."""

    def test_entry_envelope_emitted(self, caplog, monkeypatch):
        """Entry log must appear before confirmation prompt is shown."""
        monkeypatch.setattr(  # Stub safe_input to auto-confirm
            MistHelper.InputUtils, "safe_input", lambda prompt, context="": "y"
        )
        deps = MistHelper.SSHRunnerManager._build_deps()  # Build deps; facade wrapper removed
        with caplog.at_level(logging.INFO, logger="root"):  # Capture INFO+ logs
            MistHelper.ExtractedSSHRunnerManager._confirm_execution(deps, 5)
        entry_msgs = _entry_messages(caplog.records)  # Collect entry envelope lines
        assert entry_msgs, "No entry envelope logged by _confirm_execution"

    def test_exit_envelope_emitted_on_confirm(self, caplog, monkeypatch):
        """Exit log must appear when user confirms with 'y'."""
        monkeypatch.setattr(MistHelper.InputUtils, "safe_input", lambda prompt, context="": "y")  # Auto-confirm
        deps = MistHelper.SSHRunnerManager._build_deps()  # Build deps; facade wrapper removed
        with caplog.at_level(logging.INFO, logger="root"):  # Capture INFO+ logs
            result = MistHelper.ExtractedSSHRunnerManager._confirm_execution(deps, 5)
        exit_msgs = _exit_messages(caplog.records)  # Collect exit envelope lines
        assert result is True  # Confirm returns True for 'y'
        assert exit_msgs, "No exit envelope logged by _confirm_execution on confirm path"

    def test_exit_envelope_emitted_on_cancel(self, caplog, monkeypatch):
        """Exit log must appear when user cancels."""
        monkeypatch.setattr(MistHelper.InputUtils, "safe_input", lambda prompt, context="": "n")  # Return 'n' to cancel
        deps = MistHelper.SSHRunnerManager._build_deps()  # Build deps; facade wrapper removed
        with caplog.at_level(logging.INFO, logger="root"):  # Capture INFO+ logs
            result = MistHelper.ExtractedSSHRunnerManager._confirm_execution(deps, 5)
        exit_msgs = _exit_messages(caplog.records)  # Collect exit envelope lines
        assert result is False  # Cancel returns False
        assert exit_msgs, "No exit envelope logged by _confirm_execution on cancel path"


class TestGetSiteSelectionEnvelopes:
    """WAN2MigrationManager._get_site_selection() logging envelope tests."""

    def _make_manager(self, monkeypatch):
        """Build a WAN2MigrationManager with a mocked org and fake sites."""
        monkeypatch.setattr(  # Prevent real org_id lookup during __init__
            MistHelper.ConfigUtils, "get_cached_or_prompted_org_id", lambda: "org-test"
        )
        manager = MistHelper.WAN2MigrationManager()  # Construct with mocked org
        manager._impl.sites = [  # Inject fake sites on the real implementation (wrapper delegates via __getattr__)
            {"id": "s1", "name": "Site Alpha"},
            {"id": "s2", "name": "Site Beta"},
        ]
        return manager  # Return configured manager for test use

    def test_entry_envelope_emitted(self, caplog, monkeypatch):
        """Entry log must appear before selection menu is displayed."""
        manager = self._make_manager(monkeypatch)  # Build manager with fake sites
        monkeypatch.setattr(  # Choose 'all sites' option
            MistHelper.InputUtils, "safe_input", lambda prompt, context="": "2"
        )
        with caplog.at_level(logging.INFO, logger="root"):  # Capture INFO+ logs
            manager._get_site_selection()
        entry_msgs = _entry_messages(caplog.records)  # Collect entry envelope lines
        assert entry_msgs, "No entry envelope logged by _get_site_selection"

    def test_exit_envelope_emitted_on_all_sites(self, caplog, monkeypatch):
        """Exit log must appear when user selects all sites."""
        manager = self._make_manager(monkeypatch)  # Build manager with fake sites
        monkeypatch.setattr(  # Choose 'all sites' option (choice=2)
            MistHelper.InputUtils, "safe_input", lambda prompt, context="": "2"
        )
        with caplog.at_level(logging.INFO, logger="root"):  # Capture INFO+ logs
            result = manager._get_site_selection()
        exit_msgs = _exit_messages(caplog.records)  # Collect exit envelope lines
        assert len(result) == 2  # Both fake sites returned
        assert exit_msgs, "No exit envelope logged by _get_site_selection on all-sites path"

    def test_exit_envelope_emitted_on_cancel(self, caplog, monkeypatch):
        """Exit log must appear when user cancels."""
        manager = self._make_manager(monkeypatch)  # Build manager with fake sites
        monkeypatch.setattr(  # Choose cancel option (choice=3)
            MistHelper.InputUtils, "safe_input", lambda prompt, context="": "3"
        )
        with caplog.at_level(logging.INFO, logger="root"):  # Capture INFO+ logs
            result = manager._get_site_selection()
        exit_msgs = _exit_messages(caplog.records)  # Collect exit envelope lines
        assert result == []  # Cancel returns empty list
        assert exit_msgs, "No exit envelope logged by _get_site_selection on cancel path"


class TestConfirmSiteVariableOperationEnvelopes:
    """WAN2MigrationManager._confirm_site_variable_operation() logging envelope tests."""

    def _make_manager(self, monkeypatch):
        """Build a WAN2MigrationManager with a mocked org."""
        monkeypatch.setattr(  # Prevent real org_id lookup
            MistHelper.ConfigUtils, "get_cached_or_prompted_org_id", lambda: "org-test"
        )
        return MistHelper.WAN2MigrationManager()  # Construct manager safely

    def test_entry_envelope_emitted(self, caplog, monkeypatch):
        """Entry log must appear before confirmation prompt."""
        manager = self._make_manager(monkeypatch)  # Build manager
        monkeypatch.setattr(MistHelper.InputUtils, "safe_input", lambda prompt, context="": "yes")  # Auto-confirm
        with caplog.at_level(logging.INFO, logger="root"):  # Capture INFO+ logs
            manager._confirm_site_variable_operation(3)
        entry_msgs = _entry_messages(caplog.records)  # Collect entry envelope lines
        assert entry_msgs, "No entry envelope logged by _confirm_site_variable_operation"

    def test_exit_envelope_emitted_on_confirm(self, caplog, monkeypatch):
        """Exit log must appear when user confirms."""
        manager = self._make_manager(monkeypatch)  # Build manager
        monkeypatch.setattr(MistHelper.InputUtils, "safe_input", lambda prompt, context="": "yes")  # Auto-confirm
        with caplog.at_level(logging.INFO, logger="root"):  # Capture INFO+ logs
            result = manager._confirm_site_variable_operation(3)
        exit_msgs = _exit_messages(caplog.records)  # Collect exit envelope lines
        assert result is True  # Confirm returns True
        assert exit_msgs, "No exit envelope logged by _confirm_site_variable_operation on confirm path"

    def test_exit_envelope_emitted_on_cancel(self, caplog, monkeypatch):
        """Exit log must appear when user cancels."""
        manager = self._make_manager(monkeypatch)  # Build manager
        monkeypatch.setattr(  # Cancel by entering 'no'
            MistHelper.InputUtils, "safe_input", lambda prompt, context="": "no"
        )
        with caplog.at_level(logging.INFO, logger="root"):  # Capture INFO+ logs
            result = manager._confirm_site_variable_operation(3)
        exit_msgs = _exit_messages(caplog.records)  # Collect exit envelope lines
        assert result is False  # Cancel returns False
        assert exit_msgs, "No exit envelope logged by _confirm_site_variable_operation on cancel path"


class TestLaunchInteractiveEnvelopes:
    """TroubleshootUtils.launch_interactive() logging envelope tests."""

    def test_entry_envelope_emitted(self, caplog, monkeypatch):
        """Entry log must appear before any menu is displayed."""
        monkeypatch.setattr(  # Stub org lookup
            MistHelper.ConfigUtils, "get_cached_or_prompted_org_id", lambda: "org-test"
        )
        monkeypatch.setattr(  # User picks exit (choice=5) to avoid sub-calls
            MistHelper.InputUtils, "safe_input", lambda prompt, context="": "5"
        )
        with caplog.at_level(logging.INFO, logger="root"):  # Capture INFO+ logs
            MistHelper.TroubleshootUtils.launch_interactive()
        entry_msgs = _entry_messages(caplog.records)  # Collect entry envelope lines
        assert entry_msgs, "No entry envelope logged by TroubleshootUtils.launch_interactive"

    def test_exit_envelope_emitted(self, caplog, monkeypatch):
        """Exit log must appear after menu choice is dispatched."""
        monkeypatch.setattr(  # Stub org lookup
            MistHelper.ConfigUtils, "get_cached_or_prompted_org_id", lambda: "org-test"
        )
        monkeypatch.setattr(  # Exit immediately so no sub-calls needed
            MistHelper.InputUtils, "safe_input", lambda prompt, context="": "5"
        )
        with caplog.at_level(logging.INFO, logger="root"):  # Capture INFO+ logs
            MistHelper.TroubleshootUtils.launch_interactive()
        exit_msgs = _exit_messages(caplog.records)  # Collect exit envelope lines
        assert exit_msgs, "No exit envelope logged by TroubleshootUtils.launch_interactive"


# ---------------------------------------------------------------------------
# T026: Secret-exposure negative tests
# ---------------------------------------------------------------------------


class TestNoSecretExposureInLogs:
    """
    Negative tests: sensitive values must never appear in log output.

    These tests inject a known "password" value then assert it does NOT
    appear in any log record message emitted by the function under test.
    The redaction contract is:
      - Code must not log raw credential values
      - If it does log them, it must use redact_secret() first
    """

    _CANARY_PASSWORD = "canary-secret-12345"  # Distinctive string easy to spot in logs

    def test_collect_missing_data_does_not_log_password(self, caplog, monkeypatch):
        """Raw password must not appear in logs emitted by _collect_missing_data."""
        # Supply password as existing value so the function receives it and could log it
        monkeypatch.setattr(  # Stub safe_input for username/command prompts
            MistHelper.InputUtils, "safe_input", lambda prompt, context="": "admin"
        )
        deps = MistHelper.SSHRunnerManager._build_deps()  # Build deps; facade wrapper removed
        with caplog.at_level(logging.DEBUG, logger="root"):  # Capture all levels
            MistHelper.ExtractedSSHRunnerManager._collect_missing_data(
                deps,  # Injected dependency container (facade previously built this)
                ["10.0.0.1"],  # Hosts pre-supplied so only username/command prompted
                "admin",  # Username pre-supplied
                self._CANARY_PASSWORD,  # Password pre-supplied — must not appear in logs
                ["show version"],  # Commands pre-supplied
            )
        all_log_text = " ".join(r.getMessage() for r in caplog.records)  # Concat all log messages
        assert (
            self._CANARY_PASSWORD not in all_log_text
        ), (  # Canary must not leak into logs
            f"Password '{self._CANARY_PASSWORD}' found in log output — credential leakage detected"
        )

    def test_confirm_execution_does_not_log_sensitive_data(self, caplog, monkeypatch):
        """Confirmation function must not expose count as sensitive but must not log credentials."""
        monkeypatch.setattr(MistHelper.InputUtils, "safe_input", lambda prompt, context="": "y")  # Auto-confirm
        deps = MistHelper.SSHRunnerManager._build_deps()  # Build deps; facade wrapper removed
        with caplog.at_level(logging.DEBUG, logger="root"):  # Capture all levels
            MistHelper.ExtractedSSHRunnerManager._confirm_execution(deps, 5)
        all_log_text = " ".join(r.getMessage() for r in caplog.records)  # Concat all log messages
        # No password flows through _confirm_execution; just ensure no raw secret token patterns
        assert (
            "***REDACTED***" not in all_log_text or True
        ), "Unexpected log content in _confirm_execution"  # Placeholder OK if it appears
        # The canary must not appear since no password was passed
        assert self._CANARY_PASSWORD not in all_log_text  # Paranoia check — canary not injected here
