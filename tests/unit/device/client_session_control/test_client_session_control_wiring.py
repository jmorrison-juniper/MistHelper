"""Tests for deferred destructive menu wiring proof."""

from pathlib import Path  # WHY: read the owned wiring manifest without importing MistHelper.py.


def test_wiring_manifest_defers_registration_and_marks_destructive() -> None:  # WHY: wiring stays out of this PR.
    wiring_path = Path("specs/3566-client-coa-disconnect/wiring.md")  # WHY: owned manifest records the contract.
    wiring_text = wiring_path.read_text(encoding="utf-8")  # WHY: inspect the exact handoff text.
    assert "Menu number: 286" in wiring_text  # WHY: menu number must be explicit.
    assert "Category: `destructive`" in wiring_text  # WHY: automated safe tests must exclude it.
    assert "Destructive flag: `true`" in wiring_text  # WHY: destructive metadata must be explicit.
    assert "Supports fast: `false`" in wiring_text  # WHY: fast tests must skip the operation.
    assert "Registration is deferred to the integration pull request" in wiring_text  # WHY: no hot-file edit here.
