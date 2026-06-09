"""Unit tests for src/ui/runtime/dotenv_loader.py."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from src.ui.runtime.dotenv_loader import DotenvLoader, _strip_surrounding_quotes


@pytest.fixture(autouse=True)
def _cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Run every test in an isolated tmp dir so .env reads/writes are sandboxed."""
    monkeypatch.chdir(tmp_path)  # Each test gets a private working directory
    return tmp_path


def test_load_returns_empty_when_no_file(tui_stub) -> None:
    """No .env file -> empty dict, no exception."""
    loader = DotenvLoader(tui_stub)  # Construct collaborator
    assert loader.load() == {}  # Empty dict expected


def test_load_parses_simple_pairs(tui_stub, _cwd: Path) -> None:
    """Simple KEY=VALUE pairs are parsed verbatim."""
    (_cwd / ".env").write_text("API=abc\nORG=xyz\n", encoding="utf-8")  # Write minimal .env
    loader = DotenvLoader(tui_stub)  # Construct collaborator
    result = loader.load()  # Parse the file
    assert result == {"API": "abc", "ORG": "xyz"}  # Both pairs captured


def test_load_skips_blank_and_comment_lines(tui_stub, _cwd: Path) -> None:
    """Blank and comment lines are ignored."""
    (_cwd / ".env").write_text("\n# comment\nKEY=val\n", encoding="utf-8")  # Mixed content
    assert DotenvLoader(tui_stub).load() == {"KEY": "val"}  # Only KEY=val survives


def test_load_skips_malformed_lines(tui_stub, _cwd: Path) -> None:
    """Lines without '=' are silently dropped."""
    (_cwd / ".env").write_text("VALID=ok\nno_equals_here\nALSO=fine\n", encoding="utf-8")
    assert DotenvLoader(tui_stub).load() == {"VALID": "ok", "ALSO": "fine"}


def test_load_strips_surrounding_quotes(tui_stub, _cwd: Path) -> None:
    """Matching pairs of single or double quotes are stripped."""
    (_cwd / ".env").write_text("A=\"quoted\"\nB='single'\nC=raw\n", encoding="utf-8")
    assert DotenvLoader(tui_stub).load() == {"A": "quoted", "B": "single", "C": "raw"}


def test_load_handles_value_with_equals_sign(tui_stub, _cwd: Path) -> None:
    """An '=' inside the value is preserved (split-on-first only)."""
    (_cwd / ".env").write_text("URL=https://x.y?a=b&c=d\n", encoding="utf-8")
    assert DotenvLoader(tui_stub).load() == {"URL": "https://x.y?a=b&c=d"}


def test_load_debug_mode_logs_keys(tui_stub, _cwd: Path, caplog: pytest.LogCaptureFixture) -> None:
    """When ``tui.debug_mode`` is True the loader emits a TUI_DEBUG line."""
    tui_stub.debug_mode = True  # Enable debug branch
    (_cwd / ".env").write_text("X=1\n", encoding="utf-8")  # Tiny .env
    with caplog.at_level("DEBUG"):  # Capture debug records
        DotenvLoader(tui_stub).load()  # Trigger load
    assert any("TUI_DEBUG: Loaded" in r.message for r in caplog.records)


def test_load_swallows_read_errors(tui_stub, _cwd: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Read errors must not propagate; loader returns empty dict instead."""
    (_cwd / ".env").write_text("X=1\n", encoding="utf-8")  # File exists -> open() runs

    def _boom(*_a, **_k):  # noqa: ANN001 — pytest test helper
        raise OSError("simulated")  # Force the read path to raise

    monkeypatch.setattr("builtins.open", _boom)  # Patch the global open()
    assert DotenvLoader(tui_stub).load() == {}  # Still returns empty dict


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('"hello"', "hello"),  # Double-quote pair stripped
        ("'world'", "world"),  # Single-quote pair stripped
        ("plain", "plain"),  # Unquoted passes through
        ("\"mismatched'", "\"mismatched'"),  # Mismatched quotes preserved
        ("'", "'"),  # Single char is left alone
        ("", ""),  # Empty string is preserved
    ],
)
def test_strip_surrounding_quotes(raw: str, expected: str) -> None:
    """``_strip_surrounding_quotes`` handles all quoting edge cases."""
    assert _strip_surrounding_quotes(raw) == expected


def test_load_uses_existing_file_only(tui_stub, _cwd: Path) -> None:
    """Loader checks os.path.exists -> only reads when present."""
    assert not os.path.exists(_cwd / ".env")  # Sanity: no file
    assert DotenvLoader(tui_stub).load() == {}  # Empty dict, no IO error
