"""Test tracked-source discovery and stable candidate identities."""

import json
import subprocess
from pathlib import Path

import pytest

from src.foundation.support.code_defaults.__main__ import main
from src.foundation.support.code_defaults.inventory import InventoryScanner


def _repository(tmp_path: Path, source: str) -> Path:
    """Create a local tracked repository with one Python source file."""
    root = tmp_path / "repository"
    root.mkdir()
    subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
    (root / "example.py").write_text(source, encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "example.py"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-m", "test fixture"], check=True, capture_output=True)
    return root


def test_discovers_five_empty_shapes_and_ignores_untracked_and_tests(tmp_path: Path) -> None:
    """Find only tracked non-test Python inputs with empty defaults."""
    source = (
        "import os\n"
        "def choose(mapping, client):\n"
        "    mapping.get('first', '')\n"
        "    mapping.pop('second', [])\n"
        "    os.getenv('THIRD', '')\n"
        "    getattr(client, 'fourth', {})\n"
        "    mapping.get('safe', [1])\n"
        "    def nested(value=(), *, extra=set()):\n"
        "        return value\n"
        "    def positional_only(value=(), /):\n"
        "        return value\n"
        "    return nested\n"
    )
    root = _repository(tmp_path, source)
    (root / "untracked.py").write_text("value.get('ignored', '')\n", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_hidden.py").write_text("value.get('ignored', '')\n", encoding="utf-8")
    (root / "example_test.py").write_text("value.get('ignored', '')\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(root), "add", "tests/test_hidden.py", "example_test.py"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-m", "add tracked test files"], check=True, capture_output=True)

    result = InventoryScanner(root).scan()

    assert result.discovered_files == 1
    assert result.parsed_files == 1
    assert result.parse_failures == ()
    assert len(result.candidates) == 7
    assert {candidate.path for candidate in result.candidates} == {"example.py"}
    assert {candidate.shape for candidate in result.candidates} == {
        "mapping_get",
        "mapping_pop",
        "environment",
        "attribute",
        "parameter",
    }
    assert [candidate.identity for candidate in result.candidates] == [
        candidate.identity for candidate in InventoryScanner(root).scan().candidates
    ]


def test_line_movement_does_not_change_candidate_identity(tmp_path: Path) -> None:
    """Keep identities stable when source lines move without code changes."""
    root = _repository(tmp_path, "def choose(record):\n    return record.get('id', '')\n")
    before = InventoryScanner(root).scan()
    (root / "example.py").write_text(
        "\n\n# line movement only\n\ndef choose(record):\n    return record.get('id', '')\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "-C", str(root), "add", "example.py"], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-m", "move source lines"], check=True, capture_output=True)

    after = InventoryScanner(root).scan()

    assert [candidate.identity for candidate in before.candidates] == [
        candidate.identity for candidate in after.candidates
    ]
    assert before.candidates[0].line != after.candidates[0].line


def test_parse_errors_are_reported_and_unknown_roots_fail(tmp_path: Path) -> None:
    """Report parse failures and refuse a root that is not a Git worktree."""
    root = _repository(tmp_path, "def broken(:\n")

    result = InventoryScanner(root).scan()

    assert result.parsed_files == 0
    assert len(result.parse_failures) == 1
    assert "example.py" in result.parse_failures[0]
    try:
        InventoryScanner(tmp_path / "missing").scan()
    except ValueError as error:
        assert "Git worktree" in str(error)
    else:
        raise AssertionError("a missing Git worktree must fail")


def test_scan_reports_counts_and_separate_classification_totals(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Emit parse and severity counts with reversible deterministic JSON."""
    root = _repository(tmp_path, "def choose(record):\n    return record.get('id', '')\n")

    status = main(["scan", "--root", str(root)])
    output = json.loads(capsys.readouterr().out)

    assert status == 0
    assert output["status"] == "completed"
    assert output["discovered_files"] == 1
    assert output["parsed_files"] == 1
    assert output["classification_totals"] == {"outside_batch": 1}
    assert output["severity_totals"] == {"outside_batch": 1}
