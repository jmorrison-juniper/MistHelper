"""Tests for organization security posture output contract."""

from src.mist.intelligence.reports.org_security_posture.runner import OrgSecurityPostureChecklist
from tests.unit.reports.org_security_posture.fixtures.representative_org_security_posture import (
    RepresentativeOrgSecurityPostureFixture,
)


def test_runner_exports_required_columns_and_minimum_rows() -> None:
    captured_rows: list[dict[str, str]] = []  # Capture rows without writing a file.

    def write_fn(rows: list[dict[str, str]], filename: str, **kwargs: object) -> bool:
        captured_rows.extend(rows)  # Store rows for assertions.
        assert filename == "OrgSecurityPosture.csv"  # The output file name is fixed by the contract.
        assert kwargs["output_format"] == "csv"  # The branch stays CSV-only until integration applies the PK.
        assert kwargs["api_function_name"] == "orgSecurityPostureChecklist"  # Use the registered primary key strategy.
        assert kwargs["fieldnames"] == [
            "check_id",
            "area",
            "setting_path",
            "current_value",
            "recommended_value",
            "verdict",
            "reason",
        ]
        return True  # Simulate a successful DataExporter write.

    source_data = RepresentativeOrgSecurityPostureFixture.source_data()  # Use representative fixture data.
    OrgSecurityPostureChecklist.run(test_mode=True, source_data=source_data, write_fn=write_fn)  # Run without network.
    assert len(captured_rows) >= 12  # The output must include at least twelve checks.
    assert set(captured_rows[0]) == {
        "check_id",
        "area",
        "setting_path",
        "current_value",
        "recommended_value",
        "verdict",
        "reason",
    }
