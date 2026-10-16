"""Test licensing comparison CSV rows and validation."""

from src.interfaces.portals.licensing_comparison.service import LicensingComparisonService


def test_export_preserves_unavailable_data_and_license_attribution() -> None:
    """Keep failed reads explicit in exported rows rather than writing false zeros."""
    payload = {
        "results": [
            {
                "name": "Manual office",
                "org_id": "manual-one",
                "source": "manual",
                "request_status": "partial",
                "license_summary": {"status_code": 503, "data": None, "error": "unavailable"},
                "license_use_by_site": {"status_code": 200, "data": []},
                "inventory": {"status_code": 503, "data": None, "error": "unavailable"},
                "balances": [],
            }
        ]
    }  # Use only synthetic comparison values.
    rows, error = LicensingComparisonService.export_rows(payload)  # Build output with the production serializer.
    assert error is None  # A named comparison row is exportable.
    assert '"data": null' in rows[0]["inventory"]  # Keep unavailable inventory distinct from zero.
    assert '"status_code": 503' in rows[0]["license_summary"]  # Preserve the failed HTTP status.
    assert "CC BY-NC-SA 4.0" in rows[0]["source_attribution"]  # Keep license attribution in each report row.


def test_export_rejects_missing_and_malformed_rows() -> None:
    """Reject empty reports and rows without an organization name."""
    empty_rows, empty_error = LicensingComparisonService.export_rows({"results": []})  # Submit no report rows.
    invalid_rows, invalid_error = LicensingComparisonService.export_rows({"results": [{}]})  # Omit the row name.
    assert empty_rows == []  # Do not create a blank export.
    assert empty_error == "The comparison has no exportable rows."  # Name the empty report error.
    assert invalid_rows == []  # Do not export malformed rows.
    assert invalid_error == "Each comparison row must include an organization name."  # Name the row error.
