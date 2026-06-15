"""Prevent reintroduction of legacy site-insights export shim callsites."""  # Guard migration.

from __future__ import annotations  # Keep annotation behavior consistent across project tests.

from pathlib import Path  # Use pathlib for robust repository traversal in static scan.


def test_no_internal_export_legacy_callsites() -> None:  # Keep canonical callsites in place.
    repository_root = Path(__file__).resolve().parents[2]  # Resolve repo root.
    disallowed_token = "InsightMetricsUtils" + ".export_legacy("  # Build banned token without full literal.
    violations: list[str] = []  # Collect hits for assertion output.

    for python_file in repository_root.rglob("*.py"):  # Scan all Python files.
        path_text = python_file.as_posix()  # Normalize path form.
        if "/specs/" in path_text or "/abandoned-specs/" in path_text or "/finished-specs/" in path_text:  # Skip spec artifacts.
            continue  # Ignore planning files.
        if "/data/" in path_text or "/.venv/" in path_text or "__pycache__" in path_text:  # Skip runtime/cache trees.
            continue  # Ignore non-source trees.
        if python_file.name == "test_no_export_legacy_callsites.py":  # Skip this test file.
            continue  # Avoid self-match.

        content_text = python_file.read_text(encoding="utf-8", errors="ignore")  # Read file text safely.
        if disallowed_token in content_text:  # Flag remaining direct callsites.
            for line_number, line_text in enumerate(content_text.splitlines(), start=1):  # Capture line evidence.
                if disallowed_token in line_text:  # Match banned token in line.
                    violations.append(f"{python_file.relative_to(repository_root)}:{line_number}")  # Record file:line hit.

    assert not violations, f"Legacy export shim callsites found: {violations}"  # Fail if banned callsites remain.
