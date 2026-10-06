"""Test the SSR command reference guard."""

from pathlib import Path

import pytest

from scripts.verify_ssr_commands import CommandVerifier


def write_inputs(tmp_path: Path, runbook: str, reference: str) -> CommandVerifier:
    """Create isolated verifier inputs for one test."""
    runbook_path = tmp_path / "runbook.md"
    reference_path = tmp_path / "reference.md"
    runbook_path.write_text(runbook, encoding="utf-8")
    reference_path.write_text(reference, encoding="utf-8")
    return CommandVerifier(runbook_path, reference_path)


def test_extract_ignores_fenced_backticks_and_keeps_inline_commands(tmp_path: Path) -> None:
    """Keep inline commands after a fenced example."""
    verifier = write_inputs(
        tmp_path,
        "```text\n`show hidden`\n```\nUse `show status` after the check.",
        "`show status`",
    )

    assert verifier.run() == []
    assert verifier.checked_count == 1


def test_run_rejects_a_runbook_with_no_commands(tmp_path: Path) -> None:
    """Reject a false pass when extraction finds no command."""
    verifier = write_inputs(tmp_path, "No command appears here.", "`show status`")

    with pytest.raises(ValueError, match="No PCLI commands found"):
        verifier.run()


def test_run_reports_unverified_commands(tmp_path: Path) -> None:
    """Return commands that the reference does not define."""
    verifier = write_inputs(tmp_path, "Use `show missing`.", "`show status`")

    assert verifier.run() == ["show missing"]
    assert verifier.checked_count == 1


@pytest.mark.parametrize("missing_input", ["runbook", "reference"])
def test_run_rejects_a_missing_input(tmp_path: Path, missing_input: str) -> None:
    """Reject a false pass when one required input is absent."""
    verifier = write_inputs(tmp_path, "Use `show status`.", "`show status`")
    getattr(verifier, missing_input).unlink()

    with pytest.raises(FileNotFoundError):
        verifier.run()
