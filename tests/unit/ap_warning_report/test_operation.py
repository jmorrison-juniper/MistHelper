"""Verify export orchestration without real credentials or cloud requests."""

import logging
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock, patch

import pytest
from requests import ConnectionError, RequestException, Timeout

from src.operations.exporting.ap_warning_report.operation import ApWarningReport

ORG_ID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def runtime() -> SimpleNamespace:
    """Provide one selected organization and a tracked output writer."""
    return SimpleNamespace(
        ConfigUtils=SimpleNamespace(get_cached_or_prompted_org_id=Mock(return_value=ORG_ID)),
        apisession=Mock(),
        DataExporter=SimpleNamespace(write_with_format_selection=Mock(return_value=True)),
    )


@pytest.fixture
def report_sources() -> dict[str, list[dict[str, Any]]]:
    """Provide one inventory AP with documented trouble evidence."""
    return {
        "definitions": [{"code": "03", "key": "DHCP", "name": "DHCP error", "description": "No DHCP response"}],
        "sites": [{"id": "site-one", "name": "First site"}],
        "inventory": [{"mac": "000000000001", "type": "ap", "site_id": "site-one", "connected": True}],
        "stats": [{"mac": "000000000001", "last_trouble": {"code": "03"}}],
    }


def test_export_uses_standard_writer_and_truthful_count(
    runtime: SimpleNamespace, report_sources: dict[str, Any]
) -> None:
    """The standard writer receives flat rows and the feature strategy name."""
    with (
        patch("src.operations.exporting.ap_warning_report.operation.SourceDependencyResolver", runtime),
        patch("src.operations.exporting.ap_warning_report.operation.ApWarningClient") as client,
    ):
        client.return_value.read.return_value = report_sources
        assert ApWarningReport.run() == 1
    arguments = runtime.DataExporter.write_with_format_selection.call_args
    assert arguments.args[1] == f"ApWarningReport_{ORG_ID}.csv"
    assert arguments.kwargs["api_function_name"] == "ap_warning_report"
    assert set(arguments.args[0][0]) == set(arguments.kwargs["fieldnames"])
    assert arguments.args[0][0]["reported_at"].endswith("+00:00")
    assert arguments.args[0][0]["code"] == "03"


def test_canceled_org_selection_makes_no_cloud_requests(runtime: SimpleNamespace) -> None:
    """A canceled selection returns safely without constructing a client."""
    runtime.ConfigUtils.get_cached_or_prompted_org_id.return_value = None
    with (
        patch("src.operations.exporting.ap_warning_report.operation.SourceDependencyResolver", runtime),
        patch("src.operations.exporting.ap_warning_report.operation.ApWarningClient") as client,
    ):
        assert ApWarningReport.run() == 0
    client.assert_not_called()
    runtime.DataExporter.write_with_format_selection.assert_not_called()


def test_no_matches_does_not_write_or_claim_health(
    runtime: SimpleNamespace, report_sources: dict[str, Any], caplog: pytest.LogCaptureFixture
) -> None:
    """Missing trouble evidence is not proof that the AP is healthy."""
    report_sources["stats"] = []
    with (
        patch("src.operations.exporting.ap_warning_report.operation.SourceDependencyResolver", runtime),
        patch("src.operations.exporting.ap_warning_report.operation.ApWarningClient") as client,
        caplog.at_level(logging.INFO),
    ):
        client.return_value.read.return_value = report_sources
        assert ApWarningReport.run() == 0
    runtime.DataExporter.write_with_format_selection.assert_not_called()
    assert "missing trouble evidence=1" in caplog.text
    assert "No report was written" in caplog.text
    assert "healthy" not in caplog.text


def test_output_failure_never_reports_success(
    runtime: SimpleNamespace, report_sources: dict[str, Any], caplog: pytest.LogCaptureFixture
) -> None:
    """A false writer result must become an explicit failure."""
    runtime.DataExporter.write_with_format_selection.return_value = False
    with (
        patch("src.operations.exporting.ap_warning_report.operation.SourceDependencyResolver", runtime),
        patch("src.operations.exporting.ap_warning_report.operation.ApWarningClient") as client,
        caplog.at_level(logging.INFO),
    ):
        client.return_value.read.return_value = report_sources
        with pytest.raises(RuntimeError, match="write"):
            ApWarningReport.run()
    assert "Exported" not in caplog.text


def test_transport_exception_does_not_expose_credential(
    runtime: SimpleNamespace, caplog: pytest.LogCaptureFixture
) -> None:
    """Only the failure type, not a transport message, reaches operator output."""
    marker = "SYNTHETIC_PRIVATE_MARKER"
    with (
        patch("src.operations.exporting.ap_warning_report.operation.SourceDependencyResolver", runtime),
        patch("src.operations.exporting.ap_warning_report.operation.ApWarningClient") as client,
        caplog.at_level(logging.INFO),
    ):
        client.return_value.read.side_effect = RequestException(marker)
        with pytest.raises(RuntimeError) as failure:
            ApWarningReport.run()
    assert marker not in str(failure.value)
    assert marker not in caplog.text
    runtime.DataExporter.write_with_format_selection.assert_not_called()


def test_organization_is_canonical_before_filename_construction(
    runtime: SimpleNamespace, report_sources: dict[str, Any]
) -> None:
    """Accepted UUID spellings must not introduce path punctuation."""
    runtime.ConfigUtils.get_cached_or_prompted_org_id.return_value = f"urn:uuid:{ORG_ID}"
    with (
        patch("src.operations.exporting.ap_warning_report.operation.SourceDependencyResolver", runtime),
        patch("src.operations.exporting.ap_warning_report.operation.ApWarningClient") as client,
    ):
        client.return_value.read.return_value = report_sources
        assert ApWarningReport.run() == 1
    assert runtime.DataExporter.write_with_format_selection.call_args.args[1] == f"ApWarningReport_{ORG_ID}.csv"


@pytest.mark.parametrize("error_type", [Timeout, ConnectionError])
def test_timeout_and_connection_error_prevent_output(
    runtime: SimpleNamespace, error_type: type[RequestException]
) -> None:
    """A network failure must stop the callable before its writer runs."""
    with (
        patch("src.operations.exporting.ap_warning_report.operation.SourceDependencyResolver", runtime),
        patch("src.operations.exporting.ap_warning_report.operation.ApWarningClient") as client,
    ):
        client.return_value.read.side_effect = error_type
        with pytest.raises(RuntimeError, match="failed"):
            ApWarningReport.run()
    runtime.DataExporter.write_with_format_selection.assert_not_called()
