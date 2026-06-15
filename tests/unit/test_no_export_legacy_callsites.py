"""Prevent reintroduction of legacy site-insights export shim callsites."""  # Explain this guard test's migration intent.

from __future__ import annotations  # Keep annotation behavior consistent across project tests.

from pathlib import Path  # Use pathlib for robust repository traversal in static scan.


def test_no_internal_export_legacy_callsites() -> None:  # Ensure canonical callsites remain in place post-migration.
    repository_root = Path(__file__).resolve().parents[2]  # Resolve repository root from test file location.
    disallowed_token = "InsightMetricsUtils" + ".export_legacy("  # Build banned call token without retired literal in source.
    violations: list[str] = []  # Capture violating locations so assertion message is actionable.

    for python_file in repository_root.rglob("*.py"):  # Traverse python files to catch regressions in any module.
        path_text = python_file.as_posix()  # Normalize path representation for portable skip filtering.
        if "/specs/" in path_text or "/abandoned-specs/" in path_text or "/finished-specs/" in path_text:  # Skip generated/planning artifacts.
            continue  # Continue scanning runtime source files only.
        if "/data/" in path_text or "/.venv/" in path_text or "__pycache__" in path_text:  # Skip non-source runtime/cache trees.
            continue  # Ignore irrelevant files that should not affect migration policy.
        if python_file.name == "test_no_export_legacy_callsites.py":  # Skip scanning this guard test's own token literal.
            continue  # Avoid self-matching false positive.

        content_text = python_file.read_text(encoding="utf-8", errors="ignore")  # Read file content safely for textual token scan.
        if disallowed_token in content_text:  # Flag any remaining direct callsite usage.
            for line_number, line_text in enumerate(content_text.splitlines(), start=1):  # Collect precise line-level evidence.
                if disallowed_token in line_text:  # Match call expression at line granularity for actionable output.
                    violations.append(f"{python_file.relative_to(repository_root)}:{line_number}")  # Store file+line for assertion diagnostics.

    assert not violations, f"Legacy export shim callsites found: {violations}"  # Fail test when banned callsites remain or reappear.
