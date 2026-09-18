"""Tests for the rogue DHCP menu operation and its export call.

The operation is the entry point that the menu row, the command line, and the
operations web dashboard all call. These tests prove that it writes through the
shared export path, that it writes nothing when it found nothing, and that it
never reports success after a failed write.
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.security.rogue_dhcp.operation import (
    EXPORT_ENDPOINT_NAME,
    EXPORT_FILENAME,
    RogueDhcpScanOperation,
)
from src.security.rogue_dhcp.records import SOURCE_ORG_ALARM, RogueDhcpFinding, RogueDhcpRecordNormalizer
from src.security.rogue_dhcp.scanner import RogueDhcpScanResult

ALARM_RECORD = {
    "type": "sw_rogue_dhcp_server_detected",
    "site_id": "site-a",
    "switches": ["544b8c167179"],
    "hostnames": ["SW-EDGE-01"],
    "port_id": "ge-0/0/9.0",
    "timestamp": 1_700_000_000,
    "last_seen": 1_700_000_000,
}


def build_finding() -> RogueDhcpFinding:
    """Return one realistic finding for the export assertions."""
    normalizer = RogueDhcpRecordNormalizer("org-1", "2026-09-18T00:00:00+00:00", 1_700_000_000.0)
    return normalizer.from_alarm(ALARM_RECORD, SOURCE_ORG_ALARM)


def build_result(
    findings: list[RogueDhcpFinding] | None = None, failed: list[str] | None = None
) -> RogueDhcpScanResult:
    """Return a scan result with the supplied findings."""
    return RogueDhcpScanResult(
        findings=findings if findings is not None else [],
        window_start=1_700_000_000.0 - 86400,
        window_end=1_700_000_000.0,
        sites_queried=["site-a"],
        sites_failed=failed or [],
        source_counts={SOURCE_ORG_ALARM: len(findings or [])},
    )


@pytest.fixture
def stub_resolver() -> Any:
    """Patch the shared dependency resolver so no test touches a live session."""
    with patch("src.security.rogue_dhcp.operation.SourceDependencyResolver") as resolver:
        resolver.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org-1"
        resolver.apisession = object()
        resolver.DataExporter.write_with_format_selection.return_value = True
        yield resolver


def run_with_result(resolver: Any, result: RogueDhcpScanResult) -> None:
    """Run the operation against a scanner that returns the supplied result."""
    scanner = MagicMock()
    scanner.scan.return_value = result
    with patch("src.security.rogue_dhcp.operation.RogueDhcpScanner", return_value=scanner):
        RogueDhcpScanOperation.run()


def test_the_export_receives_the_registered_endpoint_name(stub_resolver: Any) -> None:
    """FR-023. The primary key strategy registers under this exact name."""
    run_with_result(stub_resolver, build_result([build_finding()]))
    _, kwargs = stub_resolver.DataExporter.write_with_format_selection.call_args
    assert kwargs["api_function_name"] == EXPORT_ENDPOINT_NAME


def test_the_export_writes_to_the_named_file(stub_resolver: Any) -> None:
    """FR-022. The data directory must hold one named file for this operation."""
    run_with_result(stub_resolver, build_result([build_finding()]))
    args, _ = stub_resolver.DataExporter.write_with_format_selection.call_args
    assert args[1] == EXPORT_FILENAME


def test_the_export_sends_the_declared_column_set(stub_resolver: Any) -> None:
    """FR-018. The CSV header must follow the dataclass declaration."""
    run_with_result(stub_resolver, build_result([build_finding()]))
    _, kwargs = stub_resolver.DataExporter.write_with_format_selection.call_args
    assert kwargs["fieldnames"] == RogueDhcpFinding.column_names()


def test_the_export_sends_flat_rows(stub_resolver: Any) -> None:
    """The writer takes flat dicts, not frozen dataclass instances."""
    run_with_result(stub_resolver, build_result([build_finding()]))
    args, _ = stub_resolver.DataExporter.write_with_format_selection.call_args
    assert isinstance(args[0][0], dict)


def test_an_empty_result_writes_nothing(stub_resolver: Any) -> None:
    """FR-024. A clean organization must not leave an empty file behind."""
    run_with_result(stub_resolver, build_result([]))
    stub_resolver.DataExporter.write_with_format_selection.assert_not_called()


def test_an_empty_result_states_the_clean_outcome(stub_resolver: Any, caplog: Any) -> None:
    """A clean organization must read as a clear result, not as a silent run."""
    with caplog.at_level(logging.INFO):
        run_with_result(stub_resolver, build_result([]))
    assert "No rogue DHCP server signal was found" in caplog.text


def test_a_failed_write_is_reported(stub_resolver: Any, caplog: Any) -> None:
    """The operation must never report success after a failed write."""
    stub_resolver.DataExporter.write_with_format_selection.return_value = False
    with caplog.at_level(logging.ERROR):
        run_with_result(stub_resolver, build_result([build_finding()]))
    assert "could not write" in caplog.text


def test_a_successful_write_reports_the_file(stub_resolver: Any, caplog: Any) -> None:
    """An operator must learn where the result landed."""
    with caplog.at_level(logging.INFO):
        run_with_result(stub_resolver, build_result([build_finding()]))
    assert EXPORT_FILENAME in caplog.text


def test_the_report_names_a_failed_site(stub_resolver: Any, caplog: Any) -> None:
    """FR-026. An incomplete result must say which site it could not read."""
    with caplog.at_level(logging.WARNING):
        run_with_result(stub_resolver, build_result([build_finding()], failed=["site-x"]))
    assert "site-x" in caplog.text


def test_the_report_states_the_marvis_scope_limit(stub_resolver: Any, caplog: Any) -> None:
    """Every run must state that the Marvis search covered the named sites only."""
    with caplog.at_level(logging.INFO):
        run_with_result(stub_resolver, build_result([build_finding()]))
    assert "Marvis config action search" in caplog.text


def test_the_report_prints_one_line_for_each_finding(stub_resolver: Any, caplog: Any) -> None:
    """FR-021. The console table is the first result an operator reads."""
    with caplog.at_level(logging.INFO):
        run_with_result(stub_resolver, build_result([build_finding()]))
    assert "544b8c167179" in caplog.text


def test_the_scanner_receives_the_resolved_organization(stub_resolver: Any) -> None:
    """The scan must cover the organization the shared helper resolved."""
    scanner = MagicMock()
    scanner.scan.return_value = build_result([])
    with patch("src.security.rogue_dhcp.operation.RogueDhcpScanner", return_value=scanner) as factory:
        RogueDhcpScanOperation.run()
    assert factory.call_args[0][1] == "org-1"


def test_the_window_length_reaches_the_scanner(stub_resolver: Any) -> None:
    """FR-003. The caller must be able to shorten the window."""
    scanner = MagicMock()
    scanner.scan.return_value = build_result([])
    with patch("src.security.rogue_dhcp.operation.RogueDhcpScanner", return_value=scanner) as factory:
        RogueDhcpScanOperation.run(window_days=7)
    assert factory.call_args[1]["window_days"] == 7
