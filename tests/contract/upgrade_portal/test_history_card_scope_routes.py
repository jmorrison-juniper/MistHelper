"""Prove history card scope on real routes with actual scoped source queries."""

from __future__ import annotations

import html
import json
import logging
import re
from unittest.mock import create_autospec
from urllib.parse import parse_qs, urlsplit

import pytest

from src.interfaces.portals.upgrade_portal.app.routes import review
from src.interfaces.portals.upgrade_portal.runtime import identity
from tests.contract.upgrade_portal.test_issue_3484_history_org_isolation import HistoryCase, SyntheticStore

logger = logging.getLogger(__name__)


class CardEvidence:
    """Read complete card descriptions independently from the production view model."""

    @staticmethod
    def text(page: str, pattern: str) -> str:
        """Read one complete element and retain its decoded text."""
        match = re.search(pattern, page, re.DOTALL)
        assert match is not None, "The rendered history page lacks the required description."
        return " ".join(html.unescape(match.group(1)).split())

    @classmethod
    def notes(cls, page: str) -> tuple[str, ...]:
        """Read the three notes using their existing card headings."""
        return tuple(
            cls.text(page, rf"<h2[^>]*>{re.escape(title)}</h2>\s*<p[^>]*>(.*?)</p>")
            for title in ("Runs", "Multi-site upgrades", "Audit log")
        )

    @classmethod
    def captions(cls, page: str) -> tuple[str, ...]:
        """Read the accessible caption of each actual history table."""
        return tuple(
            cls.text(
                page,
                rf'<table[^>]*data-testid="history-{kind}-table"[^>]*>\s*<caption[^>]*>(.*?)</caption>',
            )
            for kind in ("run", "operation", "audit")
        )

    @classmethod
    def empty_rows(cls, page: str) -> tuple[str, ...]:
        """Read the existing empty-row identifiers without changing the template."""
        return tuple(
            cls.text(page, rf'<td[^>]*data-testid="history-{kind}-empty"[^>]*>(.*?)</td>')
            for kind in ("run", "operation", "audit")
        )

    class Expected:
        """State complete expected descriptions without reading production properties."""

        @staticmethod
        def operation(subject: str, one_site: bool) -> str:
            """Distinguish site membership from organization ownership."""
            return (
                f"The multi-site upgrades that include {subject}"
                if one_site
                else f"The multi-site upgrades of {subject}"
            )

        @classmethod
        def notes(cls, subject: str, one_site: bool) -> tuple[str, ...]:
            """Keep all existing explanatory sentences after the new scope lead."""
            operation = cls.operation(subject, one_site)
            return (
                f"The single-site upgrade runs of {subject}, newest first. "
                "Each row links to the capture from before the upgrade and to the capture from after it. "
                "Every moment reads as UTC.",
                f"{operation}, newest first. The upgrade identifier links to the progress page when this "
                "browser session started the upgrade. Every moment reads as UTC.",
                f"The site lock actions of {subject}, newest first. Each row names the moment in UTC, "
                "the site, the action, and the operator. The portal shows a one-way digest of the address "
                "of the operator and never the address itself.",
            )

        @classmethod
        def captions(cls, subject: str, one_site: bool) -> tuple[str, ...]:
            """Pin the full accessible caption rather than a prefix."""
            operation = cls.operation(subject, one_site)
            return (
                f"The single-site upgrade runs of {subject}. Each row holds the site, the state, the device "
                "count, the start moment, the end moment, and a link to each capture.",
                f"{operation}. Each row holds the sites, the device types, the operator, the Mist account, "
                "and the state. It also holds the start moment and the moment of the last update.",
                f"The site lock actions of {subject}. Each row shows a take, release, takeover, or expiry.",
            )

        @staticmethod
        def empty(subject: str, one_site: bool) -> tuple[str, ...]:
            """Describe the visible page without claiming that earlier records do not exist."""
            return (
                f"This page shows no single-site upgrade run for {subject}.",
                (
                    f"This page shows no multi-site upgrade that includes {subject}."
                    if one_site
                    else f"This page shows no multi-site upgrade for {subject}."
                ),
                f"This page shows no site lock action for {subject}.",
            )

        @classmethod
        def all(cls, subject: str, one_site: bool) -> dict[str, tuple[str, ...]]:
            """Group all nine independently stated descriptions."""
            return {
                "notes": cls.notes(subject, one_site),
                "captions": cls.captions(subject, one_site),
                "empty": cls.empty(subject, one_site),
            }


class TestSiteCardScope(HistoryCase):
    """Describe only the requested site inside the validated organization."""

    class Inputs:
        """Prepare source records without replacing a real reader or scope property."""

        @staticmethod
        def named_empty_site(history_case: HistoryCase, name: str) -> None:
            """Retain named captures while leaving the other site cards empty."""
            logger.info("Prepare named synthetic captures and empty site history cards")
            for row in history_case.database.aql.records["upgrade_captures"]:
                if row.get("org_id") == "org-3484-a" and row.get("site_id") == "site-3484-a1":
                    row["site_name"] = name
            history_case.database.aql.records["upgrade_runs"] = [
                row for row in history_case.database.aql.records["upgrade_runs"] if row.get("site_id") != "site-3484-a1"
            ]
            history_case.database.trail.write_text(
                json.dumps(SyntheticStore.Rows.audit("org-3484-a", "site-3484-a2", "take", "2026-09-03T10:00:00Z")),
                encoding="utf-8",
            )
            logger.debug("Prepared three named captures and three empty site cards")

    @pytest.mark.parametrize("site_id", ["site-3484-empty", "site-3484-b1", "unknown-site"])
    @pytest.mark.parametrize("part", ["notes", "captions", "empty"])
    @pytest.mark.parametrize("card_index", [0, 1, 2])
    def test_empty_site_with_populated_other_sites(
        self, history_case: HistoryCase, site_id: str, part: str, card_index: int
    ) -> None:
        """Prove the original false descriptions on the actual empty-site response."""
        response = history_case.get("/history?site_id=" + site_id)
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        expected = CardEvidence.Expected.all("the selected site", True)
        actual = {
            "notes": CardEvidence.notes(page),
            "captions": CardEvidence.captions(page),
            "empty": CardEvidence.empty_rows(page),
        }
        assert actual[part][card_index] == expected[part][card_index]
        assert [self.Evidence.html_rows(page, kind) for kind in ("capture", "run", "operation")] == [[], [], []]
        assert "0 captures." in page
        self.Evidence.clean(page)
        self.Evidence.queries(history_case.database, site_id)

    def test_populated_site_keeps_exact_records(self, history_case: HistoryCase) -> None:
        """Use the existing capture name without changing source order, links, or attribution."""
        response = history_case.get("/history?site_id=site-3484-a1&org_id=org-3484-b")
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        expected = CardEvidence.Expected.all("Selected Alpha", True)
        assert CardEvidence.notes(page) == expected["notes"]
        assert CardEvidence.captions(page) == expected["captions"]
        assert self.Evidence.html_rows(page, "capture") == ["cap-a-5", "cap-a-3", "cap-a-1"]
        assert self.Evidence.html_rows(page, "run") == ["run-a-5", "run-a-3", "run-a-1"]
        assert self.Evidence.html_rows(page, "operation") == ["op-a-2"]
        assert re.findall(r'data-testid="history-audit-row-(\d+)"', page) == ["1", "2", "3"]
        assert "3 captures." in page and 'data-history-scope="site:site-3484-a1"' in page
        assert 'href="/upgrade/org/jobs/op-a-2"' in page
        assert history_case.record.owner.key not in page
        self.Evidence.clean(page)
        self.Evidence.queries(history_case.database, "site-3484-a1")

    def test_named_site_empty_cards_escape_stored_names(self, history_case: HistoryCase) -> None:
        """Pin all nine descriptions when captures provide a name but the other cards are empty."""
        name = 'Site <b>A & "North"</b>'
        self.Inputs.named_empty_site(history_case, name)
        response = history_case.get("/history?site_id=site-3484-a1&site_name=UNTRUSTED-query-name")
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        expected = CardEvidence.Expected.all(name, True)
        assert CardEvidence.notes(page) == expected["notes"]
        assert CardEvidence.captions(page) == expected["captions"]
        assert CardEvidence.empty_rows(page) == expected["empty"]
        assert "Site &lt;b&gt;A &amp; &#34;North&#34;&lt;/b&gt;" in page
        assert name not in page
        assert "UNTRUSTED-query-name" not in " ".join(CardEvidence.notes(page) + CardEvidence.captions(page))
        assert self.Evidence.html_rows(page, "capture") == ["cap-a-5", "cap-a-3", "cap-a-1"]
        self.Evidence.queries(history_case.database, "site-3484-a1")

    def test_later_empty_page_does_not_claim_the_site_has_no_records(self, history_case: HistoryCase) -> None:
        """The empty run statement describes this page even when the site has three earlier runs."""
        response = history_case.get("/history?site_id=site-3484-a1&limit=1&offset=20")
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        expected = CardEvidence.Expected.all("the selected site", True)
        assert CardEvidence.notes(page) == expected["notes"]
        assert CardEvidence.captions(page) == expected["captions"]
        assert self.Evidence.html_rows(page, "capture") == [] and self.Evidence.html_rows(page, "run") == []
        assert self.Evidence.html_rows(page, "operation") == ["op-a-2"]
        assert "3 captures." in page and "20 captures" in page
        previous = CardEvidence.text(page, r'<a(?=[^>]*data-testid="history-page-previous")[^>]*href="([^"]+)"')
        assert parse_qs(urlsplit(previous).query) == {"site_id": ["site-3484-a1"], "limit": ["1"], "offset": ["19"]}
        assert (
            CardEvidence.text(page, r'<td[^>]*data-testid="history-run-empty"[^>]*>(.*?)</td>') == expected["empty"][0]
        )
        self.Evidence.queries(history_case.database, "site-3484-a1")


class TestOrganizationCardScope(HistoryCase):
    """Describe only the selected organization on history without a site filter."""

    def test_populated_organization_keeps_exact_records(self, history_case: HistoryCase) -> None:
        """Pin descriptions, both sites, exact counts, and owner-only links."""
        response = history_case.get("/history?org_id=org-3484-b&site_name=UNTRUSTED-query-name")
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        expected = CardEvidence.Expected.all("the selected organization", False)
        assert CardEvidence.notes(page) == expected["notes"]
        assert CardEvidence.captions(page) == expected["captions"]
        assert self.Evidence.html_rows(page, "capture") == "cap-a-6 cap-a-5 cap-a-4 cap-a-3 cap-a-2 cap-a-1".split()
        assert self.Evidence.html_rows(page, "run") == "run-a-6 run-a-5 run-a-4 run-a-3 run-a-2 run-a-1".split()
        assert self.Evidence.html_rows(page, "operation") == ["op-a-2", "op-a-1"]
        assert re.findall(r'data-testid="history-audit-row-(\d+)"', page) == ["1", "2", "3", "4", "5"]
        assert "6 captures." in page and 'data-history-scope="all-sites"' in page
        assert "UNTRUSTED-query-name" not in " ".join(CardEvidence.notes(page) + CardEvidence.captions(page))
        self.Evidence.clean(page)
        self.Evidence.queries(history_case.database)

    def test_empty_selected_organization_with_foreign_records(self, history_case: HistoryCase) -> None:
        """Pin all nine organization descriptions without a foreign-record fallback."""
        logger.info("Remove only selected synthetic organization records")
        history_case.database.aql.records = {
            collection: [row for row in rows if row.get("org_id") != "org-3484-a"]
            for collection, rows in history_case.database.aql.records.items()
        }
        history_case.database.trail.write_text(
            json.dumps(SyntheticStore.Rows.audit("org-3484-b", "site-3484-b1", "take", "2099-11-06T17:43:31Z")),
            encoding="utf-8",
        )
        logger.debug("The selected synthetic organization has four empty history sources")
        response = history_case.get("/history")
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        expected = CardEvidence.Expected.all("the selected organization", False)
        assert CardEvidence.notes(page) == expected["notes"]
        assert CardEvidence.captions(page) == expected["captions"]
        assert CardEvidence.empty_rows(page) == expected["empty"]
        assert [self.Evidence.html_rows(page, kind) for kind in ("capture", "run", "operation")] == [[], [], []]
        assert "0 captures." in page
        self.Evidence.clean(page)
        self.Evidence.queries(history_case.database)

    @pytest.mark.parametrize(
        "path,kind,identifiers",
        [
            ("/api/sites/site-3484-a1/history?limit=1&offset=1", "capture", ["cap-a-3"]),
            ("/api/sites/site-3484-a1/runs/history?limit=1&offset=1", "run", ["run-a-3"]),
        ],
    )
    def test_api_totals_and_page_windows(
        self, history_case: HistoryCase, path: str, kind: str, identifiers: list[str]
    ) -> None:
        """Keep exact API envelopes, total counts, identifiers, and source window binds."""
        response = history_case.get(path + "&org_id=org-3484-b")
        assert response.status_code == 200
        assert self.Evidence.json_rows(response, kind) == (3, identifiers)
        self.Evidence.queries(history_case.database, "site-3484-a1")
        SyntheticStore.Aql.Input.windows(history_case.database.aql.calls, (1, 1), 1)
        self.Evidence.clean(response.get_data(as_text=True))

    def test_unavailable_operation_store_keeps_its_existing_message(self, history_case: HistoryCase) -> None:
        """An unavailable operation source must not become an empty organization claim."""
        history_case.database.available = False
        response = history_case.get("/history")
        assert response.status_code == 200
        page = response.get_data(as_text=True)
        assert CardEvidence.notes(page) == CardEvidence.Expected.notes("the selected organization", False)
        assert "The portal cannot read the multi-site upgrades, because the database does not answer." in page
        assert 'data-testid="history-operation-table"' not in page
        assert 'data-testid="history-operation-empty"' not in page


class TestHistoryScopeAccess(HistoryCase):
    """Keep existing refusals and explicit failures before scope descriptions."""

    @pytest.mark.parametrize("site_query", ["", "?site_id=site-3484-a1"])
    @pytest.mark.parametrize("selection", ["missing-selection", "org-not-permitted"])
    def test_selection_refusals(self, history_case: HistoryCase, site_query: str, selection: str) -> None:
        """A description change must not resolve any source after an organization refusal."""
        history_case.scope(selection, ("org-3484-a",))
        response = history_case.get("/history" + site_query)
        expected = (400, "org_not_chosen") if selection == "missing-selection" else (403, "org_not_permitted")
        assert (response.status_code, response.get_json()["error"]["code"]) == expected
        self.Evidence.no_reads(history_case.database)

    @pytest.mark.parametrize("change", ["absent-session", "mismatched-browser"])
    def test_sign_in_refusals(self, history_case: HistoryCase, change: str) -> None:
        """Neither an absent record nor a mismatched browser cookie can read history."""
        if change == "absent-session":
            identity.SESSION_REGISTRY.drop(history_case.record.owner.key)
        else:
            history_case.client.set_cookie(identity.BROWSER_ID_COOKIE, identity.issue_browser_id())
        response = history_case.get("/history?site_id=site-3484-a1")
        assert response.status_code == 401
        assert response.get_json() == {
            "error": {"code": "not_authenticated", "message": "Sign in before you continue."}
        }
        self.Evidence.no_reads(history_case.database)

    def test_scope_read_failure_remains_an_explicit_server_error(
        self, history_case: HistoryCase, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A failed name read must not produce a successful page with false default descriptions."""
        reader = create_autospec(review.read_site_name, side_effect=RuntimeError("Synthetic scope read failed."))
        monkeypatch.setattr(review, "read_site_name", reader)
        history_case.app.config["PROPAGATE_EXCEPTIONS"] = False
        response = history_case.get("/history?site_id=site-3484-a1")
        assert response.status_code == 500
        assert 'data-testid="history-run-table"' not in response.get_data(as_text=True)
        assert any(record.levelno == logging.ERROR and record.exc_info is not None for record in caplog.records)
        reader.assert_called_once()
