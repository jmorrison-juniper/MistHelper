"""Verify code matching without inventing definitions or observation times."""

import pytest

from src.operations.exporting.ap_warning_report.codes import CodeDefinitions, TroubleCode


@pytest.mark.parametrize("value", [None, "", "  ", 0, "0", "00", "000"])
def test_absent_and_zero_codes_are_not_trouble(value: object) -> None:
    """Zero and absent values must not produce report rows."""
    assert TroubleCode.normalize(value) == ""


@pytest.mark.parametrize("value", [3, "3", "03", "003", " 03 "])
def test_numeric_codes_match_with_leading_zero(value: object) -> None:
    """String and integer representations identify the same dictionary code."""
    assert TroubleCode.normalize(value) == "03"


@pytest.mark.parametrize("value", [True, False, -1, 3.5, {}, [], "bad", "０３"])
def test_invalid_code_fails_explicitly(value: object) -> None:
    """Malformed evidence must not silently disappear."""
    with pytest.raises(ValueError, match="trouble code"):
        TroubleCode.normalize(value)


def test_known_and_unknown_definitions() -> None:
    """The dictionary resolves known codes and preserves unknown evidence."""
    definitions = CodeDefinitions(
        [{"code": "03", "key": "DHCP_TIMEOUT", "name": "DHCP timeout", "description": "No DHCP response"}]
    )
    assert definitions.describe("03") == {
        "code": "03",
        "definition_status": "known",
        "code_key": "DHCP_TIMEOUT",
        "code_name": "DHCP timeout",
        "code_description": "No DHCP response",
    }
    assert definitions.describe("99") == {
        "code": "99",
        "definition_status": "unknown",
        "code_key": "",
        "code_name": "",
        "code_description": "No definition returned by Mist",
    }


@pytest.mark.parametrize(
    "rows",
    [
        [],
        [{"code": "03"}],
        [{"key": "DHCP", "name": "DHCP error", "description": "No DHCP response"}],
        [{"code": "03", "key": None, "name": "Name", "description": "Description"}],
        [{"code": "03", "key": "A", "name": "A", "description": "A"}] * 2,
    ],
)
def test_invalid_or_duplicate_definitions_fail(rows: list[dict[str, object]]) -> None:
    """A broken dictionary must not appear as successful enrichment."""
    with pytest.raises(ValueError, match="definition"):
        CodeDefinitions(rows)


def test_observation_time_uses_utc_without_inventing_missing_time() -> None:
    """Epoch timestamps become UTC ISO 8601 and missing times remain empty."""
    assert TroubleCode.timestamp(0) == "1970-01-01T00:00:00+00:00"
    assert TroubleCode.timestamp(None) == ""


@pytest.mark.parametrize("value", [True, -1, "yesterday", float("nan"), float("inf"), 10**30])
def test_invalid_observation_time_fails(value: object) -> None:
    """Invalid observation times cannot become an apparent current observation."""
    with pytest.raises(ValueError, match="timestamp"):
        TroubleCode.timestamp(value)
