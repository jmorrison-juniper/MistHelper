"""Tests for organization security posture console summary."""

from src.mist.intelligence.reports.org_security_posture.models import OrganizationSecuritySourceData
from src.mist.intelligence.reports.org_security_posture.runner import OrgSecurityPostureChecklist
from tests.unit.marvis.mist.intelligence.reports.audits.posture.org_security_posture.fixtures.representative import (
    RepresentativeOrgSecurityPostureFixture,
)


def test_console_summary_counts_match_exported_rows(capsys) -> None:
    captured_rows: list[dict[str, str]] = []  # Capture rows for summary comparison.

    def write_fn(rows: list[dict[str, str]], filename: str, **kwargs: object) -> bool:
        captured_rows.extend(rows)  # Store the exact exported rows.
        return True  # Simulate successful export.

    source_data = RepresentativeOrgSecurityPostureFixture.source_data()  # Use fixture data with mixed verdicts.
    outcome = OrgSecurityPostureChecklist.run(
        test_mode=True, source_data=source_data, write_fn=write_fn
    )  # Run checklist.
    output = capsys.readouterr().out  # Capture printed summary text.
    verdicts = [row["verdict"] for row in captured_rows]  # Read each exported verdict.
    counts = {v: verdicts.count(v) for v in ("pass", "fail", "review")}  # Count each verdict.
    assert outcome.state == "completed"  # A successful export completes the run.
    assert outcome.detail == f"pass: {counts['pass']}, fail: {counts['fail']}, review: {counts['review']}"  # Match CSV.
    assert f"pass: {counts['pass']}" in output  # Console pass count must match exported rows.
    assert f"fail: {counts['fail']}" in output  # Console fail count must match exported rows.


def test_all_pass_summary_prints_zero_fail_and_review(capsys) -> None:
    captured_rows: list[dict[str, str]] = []  # Capture rows without writing a file.

    def write_fn(rows: list[dict[str, str]], filename: str, **kwargs: object) -> bool:
        captured_rows.extend(rows)  # Store rows so the fake writer behaves like a sink.
        return True  # Simulate successful export.

    settings = {  # Build a fixture where every setting meets the recommendation.
        "password_policy": {
            "enabled": True,
            "min_length": 12,
            "requires_uppercase": True,
            "requires_lowercase": True,
            "requires_number": True,
            "requires_special_char": True,
            "requires_two_factor_auth": True,
            "reuse_history": 5,
            "expiry_in_days": 90,
        },
        "ui_idle_timeout": 30,
        "session_policy": {"max_lifetime_hours": 12},
        "api_policy": {"access": "restricted"},
        "disable_remote_shell": True,
        "disable_pcap": True,
        "junos_shell_access": {"admin": "none", "helpdesk": "none", "read": "none", "write": "none"},
        "pcap_bucket_verified": True,
        "switch_mgmt": {"remove_existing_configs": True},
    }
    tokens = [{"created_time": 1_700_000_000, "expire_time": 1_731_536_000}]  # Keep token lifetime within limit.
    source_data = OrganizationSecuritySourceData(settings, [], [], tokens, [{"url": "https://example.invalid/hook"}])
    outcome = OrgSecurityPostureChecklist.run(
        test_mode=True, source_data=source_data, write_fn=write_fn
    )  # Run checklist.
    output = capsys.readouterr().out  # Capture printed summary text.
    assert outcome.state == "completed"  # A successful export completes the run.
    assert outcome.detail is not None and "fail: 0, review: 0" in outcome.detail  # Complete data has no fail or review.
    assert "fail: 0" in output  # Console summary must show zero failures.
    assert "review: 0" in output  # Console summary must show zero review rows.
