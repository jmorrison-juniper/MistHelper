"""Verify site and organization history descriptions in isolated Chromium journeys."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import urlencode

import pytest

from tests.contract.upgrade_portal.test_history_card_scope_routes import CardEvidence
from tests.support.upgrade_portal_e2e.owner import RunOwnerHeaderCheck

if TYPE_CHECKING:
    from playwright.sync_api import Page

sync_api = pytest.importorskip("playwright.sync_api", reason="Playwright is not installed.")

logger = logging.getLogger(__name__)


class ScopeJourney:
    """Read the existing isolated browser records without starting an upgrade."""

    @staticmethod
    def open(page: Page, path: str, test_run_id: str) -> None:
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
        assert RunOwnerHeaderCheck(test_run_id).require(response.headers) == test_run_id
        logger.debug("Opened one isolated history scope page with status 200")

    @staticmethod
    def descriptions(page: Page, subject: str, one_site: bool) -> None:
        """Pin complete notes, captions, and computed accessible table names."""
        expected = CardEvidence.Expected.all(subject, one_site)
        logger.info("Read six isolated history descriptions")
        for kind, note, caption in zip(
            ("run", "operation", "audit"), expected["notes"], expected["captions"], strict=True
        ):
            sync_api.expect(page.get_by_test_id(f"history-{kind}-note")).to_have_text(note)
            table = page.get_by_test_id(f"history-{kind}-table")
            sync_api.expect(table.locator("caption")).to_have_text(caption)
            sync_api.expect(table).to_have_accessible_name(caption)
        logger.debug("Verified six descriptions and three accessible table names")

    @staticmethod
    def empty_rows(page: Page, subject: str, one_site: bool) -> None:
        """Pin every empty statement instead of accepting a successful empty page alone."""
        logger.info("Read three isolated history empty statements")
        expected = CardEvidence.Expected.empty(subject, one_site)
        for kind, text in zip(("run", "operation", "audit"), expected, strict=True):
            sync_api.expect(page.get_by_test_id(f"history-{kind}-empty")).to_have_text(text)
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
    """Preserve the independent expected identifiers of the existing shipped records."""

    class StoredSite:
        """Name the existing stored-poll seed without importing a second fixture module."""

        ID = "e2e-stored-poll-site"
        NAME = "E2E Stored Poll Site"
        CAPTURE_ID = "e2e-capture-stored-poll-0001"

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


class TestHistoryCardScopeJourney:
    """Require real browser evidence without a skip or production source."""

    def test_named_site_empty_cards_with_populated_organization(self, page: Page, e2e_test_run_id: str) -> None:
        """The named site has one capture while other sites supply runs and multi-site upgrades."""
        ScopeJourney.open(page, "/history", e2e_test_run_id)
        HistoryEvidence.single_site_runs(page)
        assert len(ScopeJourney.identifiers(page, "operation")) == 5
        site = HistoryEvidence.StoredSite
        ScopeJourney.open(page, "/history?" + urlencode({"site_id": site.ID}), e2e_test_run_id)
        ScopeJourney.descriptions(page, site.NAME, True)
        ScopeJourney.empty_rows(page, site.NAME, True)
        assert ScopeJourney.identifiers(page, "capture") == [site.CAPTURE_ID]
        assert ScopeJourney.identifiers(page, "run") == []
        assert ScopeJourney.identifiers(page, "operation") == []
        ScopeJourney.api_page(page, "capture", site.ID, (1, [site.CAPTURE_ID]))
        ScopeJourney.api_page(page, "run", site.ID, (0, []))

    def test_populated_organization_descriptions_and_exact_identifiers(self, page: Page, e2e_test_run_id: str) -> None:
        """The no-site route names the organization and preserves all current seeded records."""
        ScopeJourney.open(page, "/history", e2e_test_run_id)
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
        sync_api.expect(page.get_by_test_id("history-audit-empty")).to_have_text(
            "This page shows no site lock action for the selected organization."
        )

    def test_unnamed_empty_site_ignores_a_query_display_name(self, page: Page, e2e_test_run_id: str) -> None:
        """An unmatched site names the selected-site scope rather than a caller-supplied name."""
        path = "/history?" + urlencode({"site_id": "issue-3485-empty-site", "site_name": "<b>UNTRUSTED name</b>"})
        ScopeJourney.open(page, path, e2e_test_run_id)
        ScopeJourney.descriptions(page, "the selected site", True)
        ScopeJourney.empty_rows(page, "the selected site", True)
        assert [ScopeJourney.identifiers(page, kind) for kind in ("capture", "run", "operation")] == [[], [], []]
        sync_api.expect(page.get_by_test_id("history-run-note").locator("*")).to_have_count(0)
        ScopeJourney.api_page(page, "capture", "issue-3485-empty-site", (0, []))
        ScopeJourney.api_page(page, "run", "issue-3485-empty-site", (0, []))
