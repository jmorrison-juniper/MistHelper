"""Wave 8 P2 coverage — CommandCsvLoader (SSH config CSV fallback)."""

from __future__ import annotations

import os  # WHY: filesystem probes for legacy-fallback branch coverage
from pathlib import Path  # WHY: cross-platform tmp path helper

import pytest  # WHY: fixtures (tmp_path, capsys, monkeypatch) drive the loader tests

from src.ssh.config.csv_loader import CommandCsvLoader  # WHY: SUT under test


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
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """When data/<name>.csv is missing but <name>.csv exists at root, loader uses fallback."""
    monkeypatch.chdir(tmp_path)  # WHY: root of the legacy search is CWD
    legacy = tmp_path / "SSH.CSV"  # WHY: legacy-style file at root
    _write_csv(legacy, ["show version"])  # WHY: one valid command
    result = CommandCsvLoader().load("data/SSH.CSV")  # WHY: exercise the fallback branch
    assert result == ["show version"]  # WHY: legacy content is returned
    assert "legacy SSH commands file" in capsys.readouterr().out  # WHY: user-facing warning fired


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


def test_load_flags_invalid_commands(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Invalid commands (e.g. NUL char) emit a warning summary and are dropped."""
    csv_path = _write_csv(
        tmp_path / "mix.csv",
        [
            "show version",  # WHY: valid
            "bad\x00cmd",  # WHY: invalid (NUL disallowed by validator)
            "show foo",  # WHY: valid
        ],
    )
    result = CommandCsvLoader().load(csv_path)  # WHY: run through the parser
    out = capsys.readouterr().out  # WHY: capture invalid summary
    assert "Skipping 1 invalid commands" in out  # WHY: warning header present
    assert result == ["show version", "show foo"]  # WHY: invalid row is dropped


def test_load_warning_truncates_to_three(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """When more than 3 invalid rows exist, only the first 3 are printed + 'and N more' summary."""
    rows = [f"bad\x00row{index}" for index in range(6)]  # WHY: 6 invalid rows exceed the 3-line cap
    csv_path = _write_csv(tmp_path / "many_bad.csv", rows)  # WHY: all rows are invalid
    result = CommandCsvLoader().load(csv_path)  # WHY: run through the parser
    out = capsys.readouterr().out  # WHY: capture the truncation summary
    assert result == []  # WHY: no valid commands present
    assert "Skipping 6 invalid commands" in out  # WHY: count in warning
    assert "and 3 more" in out  # WHY: truncation notice printed (6 - 3 = 3 more)


def test_load_truncates_long_invalid_command_display(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Invalid commands longer than 50 chars are truncated with an ellipsis in the warning."""
    long_bad = "\x00" + ("a" * 60)  # WHY: >50-char command with a leading NUL to fail validation
    csv_path = _write_csv(tmp_path / "long.csv", [long_bad])  # WHY: single overlong invalid row
    CommandCsvLoader().load(csv_path)  # WHY: run to trigger truncation
    out = capsys.readouterr().out  # WHY: capture warning line
    assert "..." in out  # WHY: truncation ellipsis was applied


def test_load_enforces_command_cap(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """More than 50 commands triggers a truncation warning and returns the first 50."""
    rows = [f"show item {index}" for index in range(75)]  # WHY: 75 valid rows exceed the 50 cap
    csv_path = _write_csv(tmp_path / "big.csv", rows)  # WHY: over-capacity file
    result = CommandCsvLoader().load(csv_path)  # WHY: run through the parser
    out = capsys.readouterr().out  # WHY: capture the cap warning
    assert len(result) == 50  # WHY: capped at _MAX_COMMANDS
    assert "Too many commands" in out  # WHY: user-facing message preserved


def test_load_handles_read_exception(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A file-read failure returns [] and prints a warning."""
    import builtins  # WHY: patch the true builtin open() since csv_loader does not module-scope it
    from typing import Any, cast  # WHY: cast preserves builtin.open signature without ignore markers

    csv_path = tmp_path / "cmds.csv"  # WHY: path that exists on disk
    csv_path.write_text("show version\n", encoding="utf-8")  # WHY: file present for os.path.exists
    target = str(csv_path)  # WHY: pin target so we only fail the SUT's open call
    real_open = builtins.open  # WHY: preserve original open for pass-through of unrelated paths

    def _selective_open(*args: Any, **kwargs: Any) -> Any:  # WHY: match open() variadic signature
        file = args[0] if args else kwargs.get("file")  # WHY: first positional arg is the file target
        if isinstance(file, (str, bytes, os.PathLike)) and os.fspath(file) == target:  # WHY: match the SUT path
            raise OSError("boom")  # WHY: force the broad-except branch inside CommandCsvLoader.load
        return real_open(*args, **kwargs)  # WHY: delegate for unrelated opens

    monkeypatch.setattr(builtins, "open", cast(Any, _selective_open))  # WHY: cast satisfies mypy strict mode
    result = CommandCsvLoader().load(str(csv_path))  # WHY: run through the failing read path
    out = capsys.readouterr().out  # WHY: warning message should be printed
    assert result == []  # WHY: broad-except returns empty list
    assert "Could not read" in out  # WHY: warning surfaced to operator


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
