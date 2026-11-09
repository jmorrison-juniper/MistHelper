"""Wave 8 P2 coverage — CommandCsvLoader (SSH config CSV fallback)."""

from __future__ import annotations

import csv  # Field limits provide a real parser failure without shared state changes.
import logging  # WHY: caplog assertions verify migrated logger output
from pathlib import Path  # WHY: cross-platform tmp path helper
from unittest.mock import Mock  # Local failures require no host permission changes.

import pytest  # WHY: fixtures (tmp_path, caplog, monkeypatch) drive the loader tests

from src.operations.execution.ssh.config import csv_loader  # Patch only the loader, not global file access.
from src.operations.execution.ssh.config.csv_loader import CommandCsvLoader  # WHY: SUT under test

_LOGGER_NAME = "src.operations.execution.ssh.config.csv_loader"  # WHY: module-scoped logger used by the SUT


def _write_csv(path: Path, rows: list[str]) -> str:  # WHY: helper packs CSV lines into a temp file
    """Write ``rows`` (already CSV-encoded lines) to ``path`` and return the str path."""
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")  # WHY: newline-terminated for csv.reader
    return str(path)  # WHY: loader interface takes a string path


def test_load_returns_empty_when_file_missing(tmp_path: Path) -> None:  # WHY: no-file guard
    """Missing file with non-data/ prefix returns empty list."""
    missing = tmp_path / "does_not_exist.csv"  # WHY: guaranteed-absent path
    result = CommandCsvLoader().load(str(missing))  # WHY: exercise resolve_csv_path=None branch
    assert result == []  # WHY: contract: silent empty on absent file


def test_load_returns_empty_when_data_prefix_and_no_legacy(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Legacy fallback returns None when both data/ and stripped paths are absent."""
    monkeypatch.chdir(tmp_path)  # WHY: ensure legacy path search fails cleanly
    result = CommandCsvLoader().load("data/nowhere.csv")  # WHY: triggers legacy-fallback then miss
    assert result == []  # WHY: neither file exists → returns []


def test_load_uses_legacy_fallback(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """When data/<name>.csv is missing but <name>.csv exists at root, loader uses fallback."""
    monkeypatch.chdir(tmp_path)  # WHY: root of the legacy search is CWD
    legacy = tmp_path / "SSH.CSV"  # WHY: legacy-style file at root
    _write_csv(legacy, ["show version"])  # WHY: one valid command
    with caplog.at_level(logging.INFO, logger=_LOGGER_NAME):  # WHY: capture module-scoped logger output
        result = CommandCsvLoader().load("data/SSH.CSV")  # WHY: exercise the fallback branch
    assert result == ["show version"]  # WHY: legacy content is returned
    out = "\n".join(r.getMessage() for r in caplog.records)  # WHY: aggregate captured log lines
    assert "legacy SSH commands file" in out  # WHY: user-facing warning fired


def test_load_valid_commands(tmp_path: Path) -> None:
    """Valid commands are returned in order; blanks and comments are skipped."""
    csv_path = _write_csv(
        tmp_path / "cmds.csv",
        [
            "show version",  # WHY: valid row
            "",  # WHY: blank row should be skipped
            "# a comment",  # WHY: comment row should be skipped
            "show interfaces",  # WHY: another valid row
        ],
    )
    result = CommandCsvLoader().load(csv_path)  # WHY: run through the parser
    assert result == ["show version", "show interfaces"]  # WHY: skips blank+comment, preserves order


def test_load_flags_invalid_commands(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Invalid commands (e.g. NUL char) emit a warning summary and are dropped."""
    csv_path = _write_csv(
        tmp_path / "mix.csv",
        [
            "show version",  # WHY: valid
            "bad\x00cmd",  # WHY: invalid (NUL disallowed by validator)
            "show foo",  # WHY: valid
        ],
    )
    with caplog.at_level(logging.INFO, logger=_LOGGER_NAME):  # WHY: capture module-scoped logger output
        result = CommandCsvLoader().load(csv_path)  # WHY: run through the parser
    out = "\n".join(r.getMessage() for r in caplog.records)  # WHY: aggregate captured log lines
    assert "Skipping 1 invalid commands" in out  # WHY: warning header present
    assert result == ["show version", "show foo"]  # WHY: invalid row is dropped


def test_load_warning_truncates_to_three(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """When more than 3 invalid rows exist, only the first 3 are printed + 'and N more' summary."""
    rows = [f"bad\x00row{index}" for index in range(6)]  # WHY: 6 invalid rows exceed the 3-line cap
    csv_path = _write_csv(tmp_path / "many_bad.csv", rows)  # WHY: all rows are invalid
    with caplog.at_level(logging.INFO, logger=_LOGGER_NAME):  # WHY: capture module-scoped logger output
        result = CommandCsvLoader().load(csv_path)  # WHY: run through the parser
    out = "\n".join(r.getMessage() for r in caplog.records)  # WHY: aggregate captured log lines
    assert result == []  # WHY: no valid commands present
    assert "Skipping 6 invalid commands" in out  # WHY: count in warning
    assert "and 3 more" in out  # WHY: truncation notice printed (6 - 3 = 3 more)


def test_load_truncates_long_invalid_command_display(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """Invalid commands longer than 50 chars are truncated with an ellipsis in the warning."""
    long_bad = "\x00" + ("a" * 60)  # WHY: >50-char command with a leading NUL to fail validation
    csv_path = _write_csv(tmp_path / "long.csv", [long_bad])  # WHY: single overlong invalid row
    with caplog.at_level(logging.INFO, logger=_LOGGER_NAME):  # WHY: capture module-scoped logger output
        CommandCsvLoader().load(csv_path)  # WHY: run to trigger truncation
    out = "\n".join(r.getMessage() for r in caplog.records)  # WHY: aggregate captured log lines
    assert "..." in out  # WHY: truncation ellipsis was applied


def test_load_enforces_command_cap(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """More than 50 commands triggers a truncation warning and returns the first 50."""
    rows = [f"show item {index}" for index in range(75)]  # WHY: 75 valid rows exceed the 50 cap
    csv_path = _write_csv(tmp_path / "big.csv", rows)  # WHY: over-capacity file
    with caplog.at_level(logging.INFO, logger=_LOGGER_NAME):  # WHY: capture module-scoped logger output
        result = CommandCsvLoader().load(csv_path)  # WHY: run through the parser
    out = "\n".join(r.getMessage() for r in caplog.records)  # WHY: aggregate captured log lines
    assert len(result) == 50  # WHY: capped at _MAX_COMMANDS
    assert "Too many commands" in out  # WHY: user-facing message preserved


@pytest.mark.parametrize("error_type", [OSError, PermissionError, FileNotFoundError, IsADirectoryError])
def test_load_handles_read_exception(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    error_type: type[OSError],
) -> None:
    """Unreadable files preserve the fallback without disclosing exception text."""
    csv_path = _write_csv(tmp_path / "cmds.csv", ["show version"])  # Resolution needs a real local file.
    failure = error_type("private synthetic detail\nsecond line")  # Detect raw and multiline exception disclosure.
    monkeypatch.setattr(csv_loader, "open", Mock(side_effect=failure), raising=False)  # Isolate the failed read.
    with caplog.at_level(logging.INFO, logger=_LOGGER_NAME):  # WHY: capture module-scoped logger output
        result = CommandCsvLoader().load(csv_path)  # Exercise the public fallback contract.
    assert result == []  # Unreadable input must not supply commands.
    assert f"Could not read {csv_path}: {error_type.__name__}" in caplog.text  # Retain safe failure context.
    assert "private synthetic detail" not in caplog.text  # Exception text can contain private data.
    assert "second line" not in caplog.text  # Multiline input must not create log records.
    assert all(record.exc_info is None for record in caplog.records)  # Tracebacks also expose exception text.


@pytest.mark.parametrize("failure_kind", ["encoding", "field-limit"])
def test_load_handles_invalid_csv(tmp_path: Path, caplog: pytest.LogCaptureFixture, failure_kind: str) -> None:
    """Real decoding and parser failures discard every command from the file."""
    csv_path = tmp_path / "invalid.csv"  # Keep malformed input outside product output.
    if failure_kind == "encoding":  # Invalid UTF-8 reaches the text reader failure path.
        csv_path.write_bytes(b"show version\nprivate-synthetic-detail\xff\n")  # Include a valid prefix.
        expected_type = "UnicodeDecodeError"  # Keep only the safe failure category.
    else:  # The default CSV dialect reports oversized fields without strict mode.
        oversized = "private-synthetic-detail" + ("x" * csv.field_size_limit())  # Preserve the global limit.
        _write_csv(csv_path, ["show version", oversized])  # Fail after a valid parsed row.
        expected_type = "Error"  # The standard CSV exception class is csv.Error.
    with caplog.at_level(logging.INFO, logger=_LOGGER_NAME):  # Capture the fallback notice.
        result = CommandCsvLoader().load(str(csv_path))  # Use real file reading and CSV parsing.
    assert result == []  # A failed file must not return a partial command list.
    assert f"Could not read {csv_path}: {expected_type}" in caplog.text  # Name the input failure.
    assert "private-synthetic-detail" not in caplog.text  # Never include failed input in this notice.
    assert all(record.exc_info is None for record in caplog.records)  # Exclude raw exception tracebacks.


@pytest.mark.parametrize("error_type", [TypeError, AttributeError, NameError, ValueError, RuntimeError])
def test_load_propagates_unexpected_validation_errors(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, error_type: type[Exception]
) -> None:
    """Programming defects must not appear as an empty command file."""
    csv_path = _write_csv(tmp_path / "commands.csv", ["show version"])  # Exercise the real parsing path.
    failure = error_type("synthetic validation defect")  # A non-input failure must remain visible.
    monkeypatch.setattr(csv_loader, "validate_command", Mock(side_effect=failure))  # Inject the validation defect.
    with pytest.raises(error_type) as caught:  # An empty fallback would fail this test.
        CommandCsvLoader().load(csv_path)  # Parsing must not execute a command or connect to SSH.
    assert caught.value is failure  # Propagate the original exception without replacement.


def test_load_preserves_csv_dialect(tmp_path: Path) -> None:
    """Quoted commas, ignored columns, and permissive quotes retain their behavior."""
    csv_path = _write_csv(  # Preserve the established parser rather than introduce strict mode.
        tmp_path / "dialect.csv",
        ['"show interfaces, detail",ignored', " show version ,ignored", '"show route'],
    )
    result = CommandCsvLoader().load(csv_path)  # Read synthetic commands without executing them.
    assert result == ["show interfaces, detail", "show version", "show route"]  # Keep first-column parsing.


def test_resolve_csv_path_returns_primary_when_exists(tmp_path: Path) -> None:
    """When the primary path exists, resolution returns it verbatim."""
    csv_path = tmp_path / "primary.csv"  # WHY: file at primary location
    csv_path.write_text("cmd\n", encoding="utf-8")  # WHY: make the file exist
    assert CommandCsvLoader._resolve_csv_path(str(csv_path)) == str(csv_path)  # WHY: identity preserved


def test_truncate_invalid_short_returns_verbatim() -> None:
    """Commands under 50 chars are returned unchanged."""
    short = "show short"  # WHY: input under the truncation threshold
    assert CommandCsvLoader._truncate_invalid(short) == short  # WHY: no ellipsis appended


def test_truncate_invalid_long_appends_ellipsis() -> None:
    """Commands over 50 chars are trimmed with an ellipsis marker."""
    long_cmd = "a" * 60  # WHY: input exceeds the 50-char threshold
    trimmed = CommandCsvLoader._truncate_invalid(long_cmd)  # WHY: exercise the truncation branch
    assert trimmed.endswith("...")  # WHY: marker appended
    assert len(trimmed) == 53  # WHY: 50 chars + "..." suffix
