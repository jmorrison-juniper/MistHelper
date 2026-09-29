"""Tests for the client fingerprint census model."""

from __future__ import annotations  # WHY: keep annotations consistent with the package.

import json  # WHY: read the OpenAPI enum that defines valid distinct fields.
from pathlib import Path  # WHY: build repository-relative paths without separators.

import pytest  # WHY: assert validation failures clearly.

from src.reports.client_fingerprint_census.model import (
    DISPLAY_LIMIT,
    DISTINCT_FIELDS,
    UNKNOWN_VALUE,
    FingerprintCensusModel,
)


def test_distinct_fields_match_openapi_enum() -> None:
    """Assert that the model uses the OpenAPI distinct enum."""
    repo_root = Path(__file__).resolve().parents[4]  # WHY: pytest can run from a changed current directory.
    spec_path = repo_root / "documentation" / "mist-api-openapi3json.json"  # WHY: local API contract source.
    payload = json.loads(spec_path.read_text(encoding="utf-8"))  # WHY: inspect the checked-in OpenAPI file.
    schema = payload["components"]["schemas"]["fingerprints_count_distinct"]  # WHY: enum lives in this schema.
    assert tuple(schema["enum"]) == DISTINCT_FIELDS  # WHY: acceptance requires the OpenAPI enum list.


def test_validate_distinct_rejects_unknown_field() -> None:
    """Assert that unsupported distinct fields fail before the API call."""
    with pytest.raises(ValueError, match="Unsupported distinct field"):  # WHY: callers need a clear failure.
        FingerprintCensusModel.validate_distinct("mfg")  # WHY: `mfg` is not in the count endpoint enum.


def test_normalize_rows_sorts_and_sanitizes_values() -> None:
    """Assert that raw count rows become sorted export rows."""
    raw_rows = [  # WHY: cover normal, missing, and string count values.
        {"property": "Windows", "count": 3},
        {"property": None, "count": "4"},
        {"property": "Android", "count": True},
    ]
    rows = FingerprintCensusModel.normalize_rows(raw_rows, "site-1", "HQ", "os_type")  # WHY: run transform.
    assert [row.value for row in rows] == [UNKNOWN_VALUE, "Windows", "Android"]  # WHY: sort by count first.
    assert [row.count for row in rows] == [4, 3, 0]  # WHY: counts are safe integers.
    assert rows[0].site_name == "HQ"  # WHY: site context must be present in every export row.


def test_top_rows_limits_console_output() -> None:
    """Assert that the console table never exceeds the display limit."""
    raw_rows = [{"property": f"value-{index}", "count": index} for index in range(30)]  # WHY: exceed limit.
    rows = FingerprintCensusModel.normalize_rows(raw_rows, "site-1", "HQ", "family")  # WHY: get sorted rows.
    top_rows = FingerprintCensusModel.top_rows(rows)  # WHY: apply console display contract.
    assert len(top_rows) == DISPLAY_LIMIT  # WHY: top rows must cap console output.
    assert top_rows[0].count == 29  # WHY: highest counts appear first.
