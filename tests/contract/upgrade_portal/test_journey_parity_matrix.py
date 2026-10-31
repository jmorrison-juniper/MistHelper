"""Check that the journey matrix follows the feature capability inventory."""

from __future__ import annotations

import json  # Read the durable parity rows.
import re  # Read the inventory rows and the matching Markdown table.
from pathlib import Path  # Resolve files from this test module.
from typing import Any  # Type decoded JSON records.

REPOSITORY_ROOT = Path(__file__).parents[3]  # The test tree starts below the repository root.
SPEC_PATH = REPOSITORY_ROOT / "specs/3200-upgrade-portal-journeys/spec.md"  # The capability source.
JSON_PATH = REPOSITORY_ROOT / "tests/e2e/upgrade_portal/journeys/parity_matrix.json"  # The durable rows.
MARKDOWN_PATH = REPOSITORY_ROOT / "specs/3200-upgrade-portal-journeys/parity-matrix.md"  # The readable rows.
INVENTORY_PATTERN = re.compile(r"^\| (C\d{2}) \| (.*?) \| `(present|partial|missing)` \|", re.MULTILINE)
MARKDOWN_PATTERN = re.compile(r"^\| (C\d{2}) \| (.*?) \| `([^`]+)` \| `([^`]+)` \|", re.MULTILINE)
ALLOWED_STATUSES = {"proven", "partial", "missing", "defect"}


def test_parity_matrix_matches_inventory_and_report_contract() -> None:
    """Keep both matrix files aligned with all 54 capability rows."""
    spec_text = SPEC_PATH.read_text(encoding="utf-8")  # Read the source inventory.
    expected = INVENTORY_PATTERN.findall(spec_text)  # Keep the identifier and exact capability name.
    rows: list[dict[str, Any]] = json.loads(JSON_PATH.read_text(encoding="utf-8"))  # Read the durable matrix.
    actual = [(row["id"], row["capability"]) for row in rows]  # Keep the same identity fields.
    expected_identity = [(identifier, name) for identifier, name, _status in expected]  # Drop baseline status.
    assert len(expected_identity) == 54  # The inventory must retain every specified capability.
    assert actual == expected_identity  # The JSON order and names must match the source inventory.
    for row in rows:  # Check every per-mode status and issue link.
        assert row["single"] in ALLOWED_STATUSES  # Use only the report vocabulary.
        assert row["multi"] in ALLOWED_STATUSES  # Use only the report vocabulary.
        assert row["verdict"] == ("parity" if row["single"] == row["multi"] == "proven" else "gap")
        assert row["out_of_date"] is False  # This static matrix has no stale passing gap case.
        assert isinstance(row["families"], list) and row["families"]  # Name the applicable device families.
        assert isinstance(row["journeys"], dict) and row["journeys"]  # Link the journey evidence by mode.
        assert isinstance(row["issue"], int) if row["verdict"] == "gap" else row["issue"] is None
        if "defect" in (row["single"], row["multi"]):  # Every confirmed defect needs its own issue.
            assert row["issue"] != 3200
    markdown_text = MARKDOWN_PATH.read_text(encoding="utf-8")  # Read the operator-facing matrix.
    markdown_rows = MARKDOWN_PATTERN.findall(markdown_text)  # Keep identities and mode statuses.
    expected_markdown = [
        (row["id"], row["capability"], row["single"], row["multi"]) for row in rows
    ]  # Use the JSON as the rendering source.
    assert markdown_rows == expected_markdown  # The readable matrix must not drift from JSON.
