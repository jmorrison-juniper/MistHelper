"""Guard against adding new tests that import deprecated top-level facade names."""  # Explain intent of static guard.

from __future__ import annotations  # Keep annotation style consistent with project tests.

from pathlib import Path  # Use pathlib for reliable repository scanning.


def test_no_new_test_imports_of_selected_legacy_facades() -> None:  # Enforce migration away from legacy package facades.
    repository_root = Path(__file__).resolve().parents[2]  # Resolve project root from current test file path.
    allowed_existing_references = {  # Baseline exceptions tracked until corresponding canonical ports are complete.
        "tests/unit/test_exports.py",
        "tests/unit/test_menu_13_device_stats.py",
        "tests/integration/test_mistapi_sdk_compatibility.py",
        "tests/guardrails/test_wave1_safety_classification_guardrails.py",
        "tests/guardrails/test_wave1_entry_routing_guardrails.py",
    }
    banned_tokens = [  # Focus on most problematic facade symbols targeted for retirement.
        "MistHelper.SiteExportUtils",
        "MistHelper.InsightMetricsUtils",
        "MistHelper.OperationRegistry",
        "MistHelper.TimeUtils",
    ]
    violations: list[str] = []  # Collect violations for an actionable assertion message.

    for python_file in (repository_root / "tests").rglob("*.py"):  # Scan only tests to control US3 migration drift.
        relative_path = python_file.relative_to(repository_root).as_posix()  # Build normalized path for comparisons.
        if relative_path in allowed_existing_references:  # Skip known legacy-dependent tests while migration is in progress.
            continue
        content_text = python_file.read_text(encoding="utf-8", errors="ignore")  # Read safely to avoid encoding failures.
        for banned_token in banned_tokens:  # Check each banned facade token in scanned test file content.
            if banned_token in content_text:  # Flag direct references that would increase migration debt.
                violations.append(f"{relative_path}: contains {banned_token}")  # Record precise violation info.

    assert not violations, f"New legacy facade test references detected: {violations}"  # Fail if new legacy references were introduced.
