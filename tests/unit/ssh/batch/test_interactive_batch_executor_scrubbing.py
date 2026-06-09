"""Unit tests locking the password-redaction contract of InteractiveBatchExecutor.

Regression coverage for the CodeQL clear-text-storage finding: every message
written through the wrapped writer MUST have any literal occurrence of the
password replaced with ``***REDACTED***`` before reaching the inner writer.
"""

from __future__ import annotations

from src.ssh.batch.interactive_batch_executor import InteractiveBatchExecutor


def test_build_scrubbing_writer_replaces_password_literal() -> None:
    """Literal password substring must be replaced with REDACTED marker."""
    captured: list[str] = []  # Collect what reaches the inner writer
    wrapped = InteractiveBatchExecutor._build_scrubbing_writer(captured.append, "s3cret!")

    wrapped("user typed s3cret! into the prompt")  # Trigger scrub via real call

    assert captured == ["user typed ***REDACTED*** into the prompt"]  # Sole captured message


def test_build_scrubbing_writer_with_none_password_returns_inner_unchanged() -> None:
    """When no password is provided, the wrapper must short-circuit to the raw writer."""
    captured: list[str] = []  # Capture target
    raw = captured.append  # Reference to the raw writer
    wrapped = InteractiveBatchExecutor._build_scrubbing_writer(raw, None)

    assert wrapped is raw  # Same object \u2014 no wrapping overhead when nothing to scrub


def test_build_scrubbing_writer_with_empty_password_returns_inner_unchanged() -> None:
    """An empty-string password is treated identically to None (no scrubbing needed)."""
    captured: list[str] = []
    raw = captured.append
    wrapped = InteractiveBatchExecutor._build_scrubbing_writer(raw, "")

    assert wrapped is raw  # str.replace with empty would be a no-op anyway


def test_build_scrubbing_writer_handles_multiple_occurrences() -> None:
    """Every occurrence of the password literal in one message must be redacted."""
    captured: list[str] = []
    wrapped = InteractiveBatchExecutor._build_scrubbing_writer(captured.append, "pw")

    wrapped("pw appears pw twice pw")  # Three occurrences in one message

    assert captured == ["***REDACTED*** appears ***REDACTED*** twice ***REDACTED***"]


def test_build_scrubbing_writer_leaves_clean_messages_unchanged() -> None:
    """Messages that do not contain the password must pass through verbatim."""
    captured: list[str] = []
    wrapped = InteractiveBatchExecutor._build_scrubbing_writer(captured.append, "topsecret")

    wrapped("show version output")  # No credential anywhere in the line

    assert captured == ["show version output"]  # Byte-identical pass-through
