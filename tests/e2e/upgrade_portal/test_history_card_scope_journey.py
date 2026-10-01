"""Verify site and organization history descriptions in isolated Chromium journeys."""

from __future__ import annotations

import logging
from pathlib import Path
from urllib.parse import urlencode

from playwright.sync_api import Page, expect

from tests.contract.upgrade_portal.test_history_card_scope_routes import CardEvidence
from tests.e2e.upgrade_portal.conftest import STORED_POLL_CAPTURE_ID, STORED_POLL_SITE_ID, STORED_POLL_SITE_NAME

logger = logging.getLogger(__name__)


class ScopeJourney:
    """Read the existing isolated browser records without starting an upgrade."""

    @staticmethod
    def open(page: Page, path: str) -> None:
        """Open the actual history route after the current asynchronous seeds finish."""
        logger.info("Open one isolated history scope page")
        if path == "/history":
            page.wait_for_function(
                """async () => {
                    const response = await fetch('/history');
                    if (response.status !== 200) {
                        throw new Error('The isolated history request did not succeed.');
                    }
                    return (await response.text()).includes(
                        'data-testid="history-operation-row-org-run-e2e-mixed-0001"');
                }""",
                timeout=10_000,
            )
        response = page.goto(path, wait_until="domcontentloaded")
        assert response is not None
        assert response.status == 200
        logger.debug("Opened one isolated history scope page with status 200")

    @staticmethod
    def descriptions(page: Page, subject: str, one_site: bool) -> None:
        """Pin complete notes, captions, and computed accessible table names."""
        expected = CardEvidence.Expected.all(subject, one_site)
        logger.info("Read six isolated history descriptions")
        for kind, note, caption in zip(
            ("run", "operation", "audit"), expected["notes"], expected["captions"], strict=True
        ):
            expect(page.get_by_test_id(f"history-{kind}-note")).to_have_text(note)
            table = page.get_by_test_id(f"history-{kind}-table")
            expect(table.locator("caption")).to_have_text(caption)
            expect(table).to_have_accessible_name(caption)
        logger.debug("Verified six descriptions and three accessible table names")

    @staticmethod
    def empty_rows(page: Page, subject: str, one_site: bool) -> None:
        """Pin every empty statement instead of accepting a successful empty page alone."""
        logger.info("Read three isolated history empty statements")
        expected = CardEvidence.Expected.empty(subject, one_site)
        for kind, text in zip(("run", "operation", "audit"), expected, strict=True):
            expect(page.get_by_test_id(f"history-{kind}-empty")).to_have_text(text)
        logger.debug("Verified three isolated history empty statements")

    @staticmethod
    def identifiers(page: Page, kind: str) -> list[str]:
        """Read exact rendered identifiers using the existing row contracts."""
        logger.info("Read isolated history row identifiers")
        prefix = {"capture": "history-row-", "run": "history-run-row-", "operation": "history-operation-row-"}[kind]
        identifiers = []
        for row in page.locator(f'[data-testid^="{prefix}"]').all():
            marker = row.get_attribute("data-testid")
            assert marker is not None
            identifiers.append(marker.removeprefix(prefix))
        logger.debug("Read %s isolated history row identifiers", len(identifiers))
        return identifiers

    @staticmethod
    def api_page(page: Page, kind: str, site_id: str, expected: tuple[int, list[str]]) -> None:
        """Verify the real API envelope, total, and identifiers for the same site."""
        logger.info("Read one isolated history API page")
        suffix = "runs/history" if kind == "run" else "history"
        response = page.request.get(f"/api/sites/{site_id}/{suffix}")
        assert response.status == 200
        body = response.json()
        assert isinstance(body, dict) and set(body) == {kind + "s", "total"}
        rows = body[kind + "s"]
        assert isinstance(rows, list) and type(body["total"]) is int
        assert (body["total"], [row[kind + "_id"] for row in rows]) == expected
        logger.debug("Verified %s isolated API rows of %s", len(rows), body["total"])


class HistoryEvidence:
    """Preserve exact seeded runs and save the complete rendered page."""

    @staticmethod
    def single_site_runs(page: Page) -> None:
        """Require the same eight run identifiers, not only eight arbitrary rows."""
        first_identifiers = [
            "e2e-bulk-retry-run-0001",
            "e2e-failed-run-0001",
            "e2e-lifecycle-run-0001",
            "e2e-prepared-run-0001",
        ]
        last_identifiers = [
            "e2e-stale-precloud-0001",
            "e2e-stale-stopping-0001",
            "e2e-start-ready-run-0001",
            "e2e-stopped-run-0001",
        ]
        assert sorted(ScopeJourney.identifiers(page, "run")) == first_identifiers + last_identifiers

    @staticmethod
    def screenshot(page: Page, path: Path) -> None:
        """Save visual evidence inside the test's temporary directory."""
        logger.info("Save the isolated history scope screenshot")
        page.screenshot(path=str(path), full_page=True)
        assert path.is_file()
        logger.debug("Saved one isolated history scope screenshot")


class TestHistoryCardScopeJourney:
    """Require real browser evidence without a skip or production source."""

    def test_named_site_empty_cards_with_populated_organization(self, page: Page, tmp_path: Path) -> None:
        """The named site has one capture while other sites supply runs and multi-site upgrades."""
        ScopeJourney.open(page, "/history")
        HistoryEvidence.single_site_runs(page)
        assert len(ScopeJourney.identifiers(page, "operation")) == 5
        ScopeJourney.open(page, "/history?" + urlencode({"site_id": STORED_POLL_SITE_ID}))
        ScopeJourney.descriptions(page, STORED_POLL_SITE_NAME, True)
        ScopeJourney.empty_rows(page, STORED_POLL_SITE_NAME, True)
        assert ScopeJourney.identifiers(page, "capture") == [STORED_POLL_CAPTURE_ID]
        assert ScopeJourney.identifiers(page, "run") == []
        assert ScopeJourney.identifiers(page, "operation") == []
        ScopeJourney.api_page(page, "capture", STORED_POLL_SITE_ID, (1, [STORED_POLL_CAPTURE_ID]))
        ScopeJourney.api_page(page, "run", STORED_POLL_SITE_ID, (0, []))
        HistoryEvidence.screenshot(page, tmp_path / "history-named-site.png")

    def test_populated_organization_descriptions_and_exact_identifiers(self, page: Page, tmp_path: Path) -> None:
        """The no-site route names the organization and preserves all current seeded records."""
        ScopeJourney.open(page, "/history")
        ScopeJourney.descriptions(page, "the selected organization", False)
        assert sorted(ScopeJourney.identifiers(page, "capture")) == [
            "e2e-capture-post-0001",
            "e2e-capture-pre-0001",
            "e2e-capture-standalone-0001",
            "e2e-capture-stored-poll-0001",
            "e2e-capture-tier3-0001",
        ]
        HistoryEvidence.single_site_runs(page)
        assert sorted(ScopeJourney.identifiers(page, "operation")) == [
            "org-run-e2e-cancel-0001",
            "org-run-e2e-ended-0001",
            "org-run-e2e-mixed-0001",
            "org-run-e2e-reconcile-0001",
            "org-run-e2e-retry-0001",
        ]
        expect(page.get_by_test_id("history-audit-empty")).to_have_text(
            "This page shows no site lock action for the selected organization."
        )
        HistoryEvidence.screenshot(page, tmp_path / "history-selected-organization.png")

    def test_unnamed_empty_site_ignores_a_query_display_name(self, page: Page) -> None:
        """An unmatched site names the selected-site scope rather than a caller-supplied name."""
        path = "/history?" + urlencode({"site_id": "issue-3485-empty-site", "site_name": "<b>UNTRUSTED name</b>"})
        ScopeJourney.open(page, path)
        ScopeJourney.descriptions(page, "the selected site", True)
        ScopeJourney.empty_rows(page, "the selected site", True)
        assert [ScopeJourney.identifiers(page, kind) for kind in ("capture", "run", "operation")] == [[], [], []]
        expect(page.get_by_test_id("history-run-note").locator("*")).to_have_count(0)
        ScopeJourney.api_page(page, "capture", "issue-3485-empty-site", (0, []))
        ScopeJourney.api_page(page, "run", "issue-3485-empty-site", (0, []))
