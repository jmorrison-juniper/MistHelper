"""Unit tests for src.auth.interactive.credential_prompter.

Wave 13 P2 coverage lift — CredentialPrompter is a thin wrapper over
safe_input/getpass that returns Optional[str]. Cover every branch
(success, EOF/SystemExit, blank input, getpass failure) to close the
50% gap in one file.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions on older type checkers

import logging  # WHY: caplog level control for legacy warning-level messages
from unittest.mock import MagicMock  # WHY: MagicMock spec + patch for getpass

import pytest  # WHY: LogCaptureFixture type for caplog assertions

from src.auth.interactive.credential_prompter import CredentialPrompter  # WHY: subject under test


class _SafeInputStub:
    """Callable stub with configurable return value or exception (spec=safe_input)."""

    def __init__(self, return_value: str = "", raises: BaseException | None = None) -> None:
        self.return_value = return_value  # WHY: value returned on successful call
        self.raises = raises  # WHY: exception raised instead of returning
        self.calls: list[tuple[tuple, dict]] = []  # WHY: record calls for assertions

    def __call__(self, *args, **kwargs) -> str:
        self.calls.append((args, kwargs))  # WHY: record for behavioural assertions
        if self.raises is not None:
            raise self.raises  # WHY: simulate EOF path
        return self.return_value  # WHY: simulate operator input


def test_prompt_email_returns_trimmed_value() -> None:
    """Successful prompt returns the trimmed email string."""
    stub = _SafeInputStub(return_value="  operator@example.com  ")  # WHY: whitespace confirms trim
    prompter = CredentialPrompter(safe_input=stub)  # WHY: inject stub as safe_input
    assert prompter.prompt_email() == "operator@example.com"  # WHY: whitespace stripped
    assert stub.calls[0][0][0] == "  Email: "  # WHY: legacy prompt text preserved


def test_prompt_email_returns_none_on_eof() -> None:
    """SystemExit raised by safe_input surfaces as None."""
    stub = _SafeInputStub(raises=SystemExit())  # WHY: safe_input escalates EOF via SystemExit
    prompter = CredentialPrompter(safe_input=stub)
    assert prompter.prompt_email() is None  # WHY: EOF must cancel the flow


def test_prompt_email_returns_none_on_blank(caplog: pytest.LogCaptureFixture) -> None:
    """Blank email prints the legacy validation banner and returns None."""
    stub = _SafeInputStub(return_value="")  # WHY: blank input is a hard validation failure
    prompter = CredentialPrompter(safe_input=stub)
    with caplog.at_level(logging.WARNING):
        assert prompter.prompt_email() is None
    assert "X Email is required" in caplog.text  # WHY: legacy console message preserved


def test_prompt_password_returns_value(monkeypatch) -> None:
    """Successful getpass returns the raw password (no trimming)."""
    monkeypatch.setattr(  # WHY: patch getpass in the target module namespace
        "src.auth.interactive.credential_prompter.getpass.getpass",
        MagicMock(return_value="hunter2"),
    )
    prompter = CredentialPrompter(safe_input=_SafeInputStub())
    assert prompter.prompt_password() == "hunter2"


def test_prompt_password_returns_none_on_eof(monkeypatch) -> None:
    """EOFError from getpass returns None (SSH disconnect path)."""
    monkeypatch.setattr(
        "src.auth.interactive.credential_prompter.getpass.getpass",
        MagicMock(side_effect=EOFError()),
    )
    prompter = CredentialPrompter(safe_input=_SafeInputStub())
    assert prompter.prompt_password() is None


def test_prompt_password_returns_none_on_terminal_error(monkeypatch, caplog: pytest.LogCaptureFixture) -> None:
    """Non-EOF exceptions from getpass are logged and returned as None."""
    monkeypatch.setattr(
        "src.auth.interactive.credential_prompter.getpass.getpass",
        MagicMock(side_effect=OSError("closed stdin")),
    )
    prompter = CredentialPrompter(safe_input=_SafeInputStub())
    with caplog.at_level(logging.WARNING):
        assert prompter.prompt_password() is None
    assert "Failed to read password" in caplog.text  # WHY: legacy console banner


def test_prompt_password_returns_none_on_blank(monkeypatch, caplog: pytest.LogCaptureFixture) -> None:
    """Blank password prints validation banner and returns None."""
    monkeypatch.setattr(
        "src.auth.interactive.credential_prompter.getpass.getpass",
        MagicMock(return_value=""),
    )
    prompter = CredentialPrompter(safe_input=_SafeInputStub())
    with caplog.at_level(logging.WARNING):
        assert prompter.prompt_password() is None
    assert "X Password is required" in caplog.text


def test_prompt_two_factor_returns_trimmed_value() -> None:
    """Successful 2FA prompt returns the trimmed code."""
    stub = _SafeInputStub(return_value=" 123456 ")  # WHY: verify trim of whitespace
    prompter = CredentialPrompter(safe_input=stub)
    assert prompter.prompt_two_factor() == "123456"
    assert stub.calls[0][0][0] == "  Enter 2FA code: "  # WHY: legacy prompt text


def test_prompt_two_factor_returns_none_on_eof() -> None:
    """SystemExit from safe_input surfaces as None from prompt_two_factor."""
    stub = _SafeInputStub(raises=SystemExit())
    prompter = CredentialPrompter(safe_input=stub)
    assert prompter.prompt_two_factor() is None


def test_prompt_two_factor_returns_none_on_blank(caplog: pytest.LogCaptureFixture) -> None:
    """Blank 2FA prints legacy banner and returns None."""
    stub = _SafeInputStub(return_value="   ")  # WHY: whitespace-only trims to empty
    prompter = CredentialPrompter(safe_input=stub)
    with caplog.at_level(logging.WARNING):
        assert prompter.prompt_two_factor() is None
    assert "X 2FA code is required" in caplog.text
