"""Tests for quickstart test-mode behavior."""

from src.mist.intelligence.reports.org_security_posture.runner import OrgSecurityPostureChecklist


def test_test_mode_uses_fixture_data_without_api_context() -> None:
    captured_rows: list[dict[str, str]] = []  # Capture rows to prove output generation.

    def write_fn(rows: list[dict[str, str]], filename: str, **kwargs: object) -> bool:
        captured_rows.extend(rows)  # Store fixture-mode rows.
        return True  # Simulate successful export.

    summary = OrgSecurityPostureChecklist.run(test_mode=True, write_fn=write_fn)  # Run with no API session or org ID.
    assert len(captured_rows) == 19  # Test mode must produce one row for each registered check.
    assert summary["pass"] == len(captured_rows)  # The built-in fixture is fully passing.
