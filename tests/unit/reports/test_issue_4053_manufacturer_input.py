"""Regression tests for menu 91 browser manufacturer input."""

from __future__ import annotations

from src.mist.intelligence.reports.wired_client_manufacturer_report_generator import (
    WiredClientManufacturerReportGenerator as ReportGenerator,
)


def test_menu_91_accepts_a_manufacturer_name() -> None:
    """A browser can submit the displayed name instead of a numeric row."""
    manufacturers = [("Arista", 12), ("Juniper", 5)]

    selected = ReportGenerator._parse_manufacturer_choice("Arista", manufacturers)

    assert selected == "Arista"


def test_menu_91_keeps_numeric_and_empty_choices() -> None:
    """The existing CLI index and empty answers keep their current meaning."""
    manufacturers = [("Arista", 12), ("Juniper", 5)]

    assert ReportGenerator._parse_manufacturer_choice("2", manufacturers) == "Juniper"
    assert ReportGenerator._parse_manufacturer_choice("", manufacturers) is None


def test_menu_91_keeps_numeric_meaning_when_a_name_is_numeric() -> None:
    """A numeric CLI answer remains an index even when a displayed name is numeric."""
    manufacturers = [("Arista", 12), ("2", 5)]

    assert ReportGenerator._parse_manufacturer_choice("2", manufacturers) == "2"


def test_menu_91_rejects_an_out_of_range_number_before_matching_a_name() -> None:
    """An invalid numeric CLI index does not become a manufacturer-name answer."""
    manufacturers = [("Arista", 12), ("99", 5)]

    assert ReportGenerator._parse_manufacturer_choice("99", manufacturers) is None


def test_menu_91_rejects_an_unknown_name() -> None:
    """An unknown name keeps the existing no-filter result."""
    manufacturers = [("Arista", 12), ("Juniper", 5)]

    assert ReportGenerator._parse_manufacturer_choice("Unknown", manufacturers) is None
