"""Test route rendering and CSV export without a live Mist session."""

import csv
from io import StringIO
from pathlib import Path

import pytest
from flask.testing import FlaskClient

import src.interfaces.portals.licensing_comparison.export as licensing_export


def test_dashboard_renders_source_attribution(licensing_client: FlaskClient) -> None:
    """Render the feature page and retain the source license attribution."""
    response = licensing_client.get("/license-comparison")  # Request the dashboard without network access.
    page = response.get_data(as_text=True)  # Read only the rendered HTML response.
    assert response.status_code == 200  # The configured shared-session marker allows page rendering.
    assert "MistOrgLicensingComparison" in page  # Preserve the source project attribution.
    assert "CC BY-NC-SA 4.0" in page  # Keep the source license visible to operators.


def test_csv_export_uses_shared_exporter_and_neutralizes_formulas(
    licensing_client: FlaskClient,
) -> None:
    """Export comparison data to the existing data directory with safe cells."""
    response = licensing_client.post(
        "/api/license-comparison/export",
        json={
            "results": [
                {
                    "name": "=1+2",
                    "org_id": "org-1",
                    "source": "direct",
                    "request_status": "success",
                    "license_summary": {"status_code": 200, "data": {"summary": {}}},
                    "license_use_by_site": {"status_code": 200, "data": []},
                    "inventory": {"status_code": 200, "data": []},
                    "balances": [],
                }
            ]
        },
    )  # Write one synthetic comparison through the production exporter.
    rows = list(csv.DictReader(StringIO(response.get_data(as_text=True))))  # Parse the CSV response.
    data_dir = Path(licensing_client.application.config["DATA_DIR"])  # Inspect only the temporary export folder.
    csv_files = list(data_dir.rglob("*.csv"))  # Count CSV output in the temporary directory.
    database_files = list(data_dir.rglob("*.db"))  # Check for forbidden database output.
    assert response.status_code == 200  # The shared exporter completed the download.
    assert rows[0]["organization"] == "'=1+2"  # Prevent spreadsheet formula execution.
    assert rows[0]["organization_id"] == "org-1"  # Preserve the source organization identifier.
    assert "CC BY-NC-SA 4.0" in rows[0]["source_attribution"]  # Preserve license attribution in the report.
    assert len(csv_files) == 1  # Write exactly one requested CSV report.
    assert database_files == []  # Do not create a database for comparison input.


def test_csv_export_reports_a_shared_writer_failure(
    licensing_client: FlaskClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Return an explicit server error when the shared exporter fails."""
    monkeypatch.setattr(
        licensing_export.CsvExportService,
        "_persist",
        lambda *_arguments, **_keywords: False,
    )  # Force a controlled exporter failure.
    response = licensing_client.post(
        "/api/license-comparison/export", json={"results": [{"name": "Primary"}]}
    )  # Request an export with one valid synthetic row.
    assert response.status_code == 500  # Do not report a failed write as success.
    assert response.get_json() == {"error": "The CSV export failed. Try again."}  # Explain the export failure.
