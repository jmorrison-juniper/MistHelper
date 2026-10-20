"""Tests for the typed outcome of the organization security posture checklist."""

import pytest

from src.foundation.models.operation_outcome import OperationOutcome
from src.foundation.runtime.config.source_dependency_resolver import SourceDependencyResolver
from src.mist.intelligence.reports.org_security_posture.models import OrganizationSecuritySourceData
from src.mist.intelligence.reports.org_security_posture.runner import OrgSecurityPostureChecklist
from tests.unit.reports.org_security_posture.fixtures.representative_org_security_posture import (
    RepresentativeOrgSecurityPostureFixture,
)


class CountingWriter:
    """Record each write attempt and return a chosen result."""

    def __init__(self, result: bool) -> None:
        self.result = result  # Chosen write result.
        self.calls = 0  # Count each write attempt.

    def __call__(self, rows: list[dict[str, str]], filename: str, **kwargs: object) -> bool:
        self.calls += 1  # Record the attempt.
        return self.result  # Return the chosen result.


def test_rejected_write_returns_failed_without_summary(capsys: pytest.CaptureFixture[str]) -> None:
    writer = CountingWriter(False)  # Simulate a rejected export.
    source_data = RepresentativeOrgSecurityPostureFixture.source_data()  # Use offline fixture data.
    outcome = OrgSecurityPostureChecklist.run(test_mode=True, source_data=source_data, write_fn=writer)
    assert outcome.state == "failed"  # A rejected write is a failure.
    assert outcome.message == "The organization security posture checklist could not write its output."  # Exact text.
    assert writer.calls == 1  # The write was attempted once.
    assert "pass:" not in capsys.readouterr().out  # No summary after a rejected write.


def test_missing_context_returns_missing_input_without_write(monkeypatch: pytest.MonkeyPatch) -> None:
    writer = CountingWriter(True)  # Any write would be a defect.
    monkeypatch.setattr(SourceDependencyResolver, "apisession", None, raising=False)  # No shared session.
    outcome = OrgSecurityPostureChecklist.run(org_id="org-1", write_fn=writer)  # Normal mode, no session.
    assert outcome.state == "missing_input"  # Missing context maps to missing_input.
    assert writer.calls == 0  # Nothing is written.


def test_source_collection_error_propagates() -> None:
    class BrokenSession:
        """Fail every API read."""

        def mist_get(self, *args: object, **kwargs: object) -> None:
            raise RuntimeError("simulated Mist failure")  # Simulate an SDK failure.

    writer = CountingWriter(True)  # Any write would be a defect.
    with pytest.raises(RuntimeError, match="simulated Mist failure"):  # Fetch errors keep propagating.
        OrgSecurityPostureChecklist.run(api_session=BrokenSession(), org_id="org-1", write_fn=writer)
    assert writer.calls == 0  # Nothing is written after a collection error.


def test_empty_source_payloads_still_return_completed_outcome_with_check_rows() -> None:
    captured_rows: list[dict[str, str]] = []  # Keep the attempted output available for assertions.

    def write_fn(rows: list[dict[str, str]], filename: str, **kwargs: object) -> bool:
        captured_rows.extend(rows)  # Retain every checklist row sent to the exporter.
        return True  # Simulate a successful local output write.

    source_data = OrganizationSecuritySourceData({}, [], [], [], [])  # Supply empty API collections.
    outcome = OrgSecurityPostureChecklist.run(
        test_mode=True, source_data=source_data, write_fn=write_fn
    )  # Run every registered check without API access.

    assert isinstance(outcome, OperationOutcome)  # Keep menu 276 on the typed outcome contract.
    assert outcome.state == "completed"  # Empty source collections still produce checklist results.
    assert outcome.message == "The organization security posture checklist completed."  # Preserve operator text.
    assert outcome.detail is not None  # The completed result carries the verdict summary.
    assert len(captured_rows) > 0  # The registered checklist emits rows even when its source collections are empty.
