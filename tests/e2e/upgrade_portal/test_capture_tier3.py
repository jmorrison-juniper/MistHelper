"""Browser proof for the stored Tier 3 capture journey.

Why:
    Contract tests cannot prove that a browser shows the stored rows. These
    tests open the real page and compare both downloads with the shown data.
"""

from __future__ import annotations

import csv
import io
from typing import Any

import pytest

sync_api = pytest.importorskip("playwright.sync_api", reason="The Playwright package is not installed.")

from tests.e2e.upgrade_portal.conftest import TIER3_CAPTURE_ID  # noqa: E402

CAPTURE_PATH = f"/captures/{TIER3_CAPTURE_ID}"
EXPORT_PATH = f"/api/captures/{TIER3_CAPTURE_ID}/export"
EXPECTED_KINDS = {"client_guest", "switch_port", "poe", "radio"}
EMPTY_KINDS = {"tunnel", "bgp_peer", "alarm"}


@pytest.fixture
def tier3_page(page: Any, capture_portal_server: str) -> Any:
    """Open the stored Tier 3 capture page.

    Args:
        page: The signed browser page.
        capture_portal_server: The isolated portal address.

    Returns:
        The opened browser page.
    """
    del capture_portal_server
    answer = page.goto(CAPTURE_PATH, wait_until="domcontentloaded")
    assert answer is not None
    assert answer.status == 200
    return page


def test_the_browser_shows_tier3_rows_and_section_states(tier3_page: Any) -> None:
    """The page shows stored rows and distinguishes empty and failed reads."""
    sync_api.expect(tier3_page.get_by_test_id("capture-client-row-aabbcc000099")).to_be_visible()
    sync_api.expect(tier3_page.get_by_test_id("capture-switch-ports-card")).to_have_attribute("data-state", "ok")
    sync_api.expect(tier3_page.get_by_test_id("capture-poe-card")).to_have_attribute("data-state", "ok")
    sync_api.expect(tier3_page.get_by_test_id("capture-radios-card")).to_have_attribute("data-state", "ok")
    sync_api.expect(tier3_page.get_by_test_id("capture-tunnels-card")).to_have_attribute("data-state", "no_rows")
    sync_api.expect(tier3_page.get_by_test_id("capture-bgp-peers-card")).to_have_attribute(
        "data-state", "unavailable"
    )
    sync_api.expect(tier3_page.get_by_text("ge-0/0/1", exact=True).first).to_be_visible()
    sync_api.expect(tier3_page.get_by_text("4.5", exact=True)).to_be_visible()


def test_the_csv_and_json_downloads_hold_the_same_tier3_kinds(tier3_page: Any) -> None:
    """The two downloads hold each stored Tier 3 row kind."""
    csv_answer = tier3_page.request.get(f"{EXPORT_PATH}?format=csv")
    json_answer = tier3_page.request.get(f"{EXPORT_PATH}?format=json")
    assert csv_answer.status == 200
    assert json_answer.status == 200

    csv_rows = list(csv.DictReader(io.StringIO(csv_answer.text())))
    json_rows = json_answer.json()["rows"]
    csv_kinds = {row["kind"] for row in csv_rows}
    json_kinds = {row["kind"] for row in json_rows}

    assert EXPECTED_KINDS <= csv_kinds
    assert csv_kinds == json_kinds
    assert not csv_kinds & EMPTY_KINDS
