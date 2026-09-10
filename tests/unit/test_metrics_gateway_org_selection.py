"""Test metrics gateway organization selection at the process boundary."""

from __future__ import annotations

import logging
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import MistHelper


class _Terminal:
    """Provide the small terminal interface used by the gateway guard."""

    def __init__(self, interactive: bool) -> None:
        """Store the terminal state that the test needs."""
        self._interactive = interactive  # Keep the terminal result deterministic for the test

    def isatty(self) -> bool:
        """Return the configured terminal state."""
        return self._interactive  # Report whether the test represents a terminal


def test_metrics_gateway_rejects_missing_org_without_tty(monkeypatch, caplog) -> None:
    """A service start must fail before it asks Mist Cloud to list organizations."""
    monkeypatch.setattr(sys, "stdin", _Terminal(False))  # Simulate a service manager without a terminal
    monkeypatch.setattr(sys, "stdout", _Terminal(False))  # Simulate redirected service output
    picker = Mock()  # Track calls to the interactive organization picker
    monkeypatch.setattr(MistHelper, "_select_org_from_session", picker)  # Prevent a network-backed prompt
    settings = SimpleNamespace(org_id="")  # Provide the missing organization setting

    with caplog.at_level(logging.ERROR):  # Capture the operator-facing failure message
        result = MistHelper._metrics_gateway_org_id(settings)  # Resolve the organization without a terminal

    assert result == ""  # The caller must reject the unresolved organization
    picker.assert_not_called()  # The noninteractive path must never enter the picker
    assert "no terminal" in caplog.text  # Explain why the prompt did not run
    assert "METRICS_ORG_ID or MIST_ORG_ID" in caplog.text  # Name the supported configuration


def test_metrics_gateway_keeps_picker_with_tty(monkeypatch) -> None:
    """An operator with a terminal must keep the existing organization picker."""
    monkeypatch.setattr(sys, "stdin", _Terminal(True))  # Simulate an interactive input terminal
    monkeypatch.setattr(sys, "stdout", _Terminal(True))  # Simulate an interactive output terminal
    monkeypatch.setattr(MistHelper, "org_id", "")  # Clear the session selection before the picker

    def select_org() -> None:
        """Supply the organization that the interactive picker would return."""
        MistHelper.org_id = "org-picked"  # Model the picker updating the active session

    monkeypatch.setattr(MistHelper, "_select_org_from_session", select_org)  # Supply the operator choice
    settings = SimpleNamespace(org_id="")  # Force the picker path

    assert MistHelper._metrics_gateway_org_id(settings) == "org-picked"  # Preserve interactive selection behavior


def test_metrics_gateway_launch_exits_nonzero_without_org(monkeypatch) -> None:
    """A missing organization must produce a failed process status."""
    monkeypatch.setattr(MistHelper, "_metrics_gateway_org_id", lambda _settings: "")  # Force the unresolved path
    monkeypatch.setattr(MistHelper.EnvironmentUtils, "is_running_in_container", lambda: False)  # Use host settings
    monkeypatch.setattr(MistHelper, "echo", lambda *_args, **_kwargs: None)  # Suppress console output

    try:
        MistHelper._launch_metrics_gateway()  # Start the gateway with no organization
    except SystemExit as error:
        assert error.code == 1  # Confirm service managers receive a failure status
    else:
        raise AssertionError("The gateway must exit with status 1.")  # Reject silent success
