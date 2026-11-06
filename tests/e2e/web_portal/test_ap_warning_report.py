"""Verify that the portal exposes the read-only AP warning export."""

from flask.testing import FlaskClient


def test_ap_warning_report_is_listed_in_a_named_group(client: FlaskClient) -> None:
    """The fallback portal must expose menu 307 without a cloud session."""
    response = client.get("/api/operations/list")
    assert response.status_code == 200
    groups = response.get_json()["categories"]
    reports = next(group for group in groups if group["name"] == "AP Warning Reports")
    assert [operation["menu_number"] for operation in reports["operations"]] == ["307"]
    assert reports["operations"][0]["description"] == "Export AP warning and error codes across all sites"


def test_ap_warning_report_needs_no_additional_controls(client: FlaskClient) -> None:
    """The report uses the selected organization and standard export controls."""
    response = client.get("/api/operations/parameters/307")
    assert response.status_code == 200
    assert response.get_json()["parameters"] == []
