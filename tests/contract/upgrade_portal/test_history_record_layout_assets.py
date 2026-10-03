"""Require native history component delivery and unchanged presentation inputs."""

from __future__ import annotations

import html
import logging
import re
import tomllib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from flask import Flask, render_template

from src.upgrade_portal.app.routes import review

logger = logging.getLogger(__name__)


class RecordAssetGuard:
    """Read and check only the page-owned history component."""

    ROOT = Path(__file__).resolve().parents[3]
    ASSET = "src/upgrade_portal/app/assets/static/css/history_records.css"
    TEMPLATE = "src/upgrade_portal/app/assets/templates/review/history.html"

    @classmethod
    def read(cls, path: Path) -> str:
        """Fail unreadable input rather than accepting an empty measurement."""
        logger.info("Read one required history component")
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            logger.exception("Checked 0 history components. The required input cannot be read.")
            raise
        assert source.strip(), "Checked 1 history component. The input is empty."
        logger.debug("Read one history component with %s characters", len(source))
        return source

    class Rules:
        """Check selector boundaries and complete width budgets."""

        @staticmethod
        def require(source: str) -> None:
            """Require actual scoped rules without a font or theme shortcut."""
            clean = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)
            rules = re.findall(r"([^{}]+)\{([^{}]+)\}", clean)
            assert rules, "Checked 1 stylesheet and 0 rules. The component has no readable rules."
            print(f"Checked 1 history stylesheet, {len(rules)} rules, and 24 column shares.")
            for selectors, declarations in rules:
                assert all(selector.strip().startswith(".history-records-") for selector in selectors.split(","))
                assert not re.search(r"font(?:-size|-family)?\s*:", declarations)
                assert "!important" not in declarations and "url(" not in declarations
            assert "background-color: var(--portal-surface)" in clean
            assert "background-color: var(--portal-table-row-hover)" in clean
            assert "table-layout: fixed" in clean and "text-overflow: ellipsis" in clean
            RecordAssetGuard.Rules.budgets(clean)

        @staticmethod
        def budgets(source: str) -> None:
            """Require all existing columns and a total share of 100 percent."""
            for kind, count in (("runs", 11), ("operations", 8), ("audit", 5)):
                shares = re.findall(
                    rf"\.history-records-{kind} thead th:nth-child\((\d+)\)\s*\{{\s*width:\s*(\d+)%;\s*\}}",
                    source,
                )
                assert [int(index) for index, _share in shares] == list(range(1, count + 1))
                assert sum(int(share) for _index, share in shares) == 100
            logger.debug("Verified 24 column shares across three complete tables")


class TestHistoryRecordAssets:
    """Verify the shipped asset route and actual template escaping."""

    def test_native_asset_and_package_boundary(self, portal_app: Flask) -> None:
        """The exact native static route returns the required component bytes."""
        logger.info("Request one native history stylesheet")
        response = portal_app.test_client().get("/static/css/history_records.css")
        source = RecordAssetGuard.read(RecordAssetGuard.ROOT / RecordAssetGuard.ASSET)
        assert response.status_code == 200 and response.mimetype == "text/css"
        assert response.get_data(as_text=True) == source
        RecordAssetGuard.Rules.require(source)
        configuration = tomllib.loads((RecordAssetGuard.ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        assert "src" in configuration["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"]
        logger.debug("Verified one native CSS response and its existing package inclusion boundary")

    def test_asset_refusals_are_not_successful_css(self, portal_app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
        """Actual HTTP 4xx and 5xx responses must not resemble a delivered component."""
        logger.info("Request missing and unreadable native asset responses")
        client = portal_app.test_client()
        missing = client.get("/static/css/history_records_missing.css")
        assert missing.status_code == 404 and missing.mimetype != "text/css"
        monkeypatch.setitem(portal_app.config, "TESTING", False)
        failure = Mock(side_effect=OSError("The controlled asset read failed."))
        monkeypatch.setattr(portal_app, "send_static_file", failure)
        unreadable = client.get("/static/css/history_records.css", headers={"Accept": "application/json"})
        assert unreadable.status_code == 500 and unreadable.mimetype != "text/css"
        assert unreadable.get_json()["error"]["code"] == "server_error"
        assert failure.call_count == 1
        logger.debug("Verified one 404 and one 500 native asset refusal")

    def test_actual_template_load_order_titles_and_escaping(self, portal_app: Flask) -> None:
        """The native renderer retains complete escaped values and stored moment titles."""
        logger.info("Render one native history template with controlled quoted values")
        page, value = self.Template.render(portal_app)
        self.Template.require(page, value)
        assert page.count("css/history_records.css") == 1
        assert html.escape(value, quote=False) in page.replace("&#34;", '"')
        logger.debug("Verified four ordered stylesheets and complete escaped titles")

    class Template:
        """Separate controlled template input from independent output requirements."""

        @staticmethod
        def render(portal_app: Flask) -> tuple[str, str]:
            """Use the actual renderer and run shaper with a quoted stored value."""
            value = 'Site <b>A & "North"</b>'
            run = review.run_history_row(
                {
                    "run_id": "run-3491",
                    "site_name": value,
                    "actor_email": "controlled.operator@example.invalid",
                    "cloud_account": value,
                    "created_at": "2026-09-02T23:01:00-05:00",
                }
            )
            operations = SimpleNamespace(org_selected=True, database_available=True, rows=[])
            with portal_app.test_request_context("/history"):
                page = render_template(
                    "review/history.html", run_rows=[run], operation_section=operations, signed_in=True
                )
            return page, value

        @staticmethod
        def require(page: str, value: str) -> None:
            """Require the exact asset order and original stored title without raw markup."""
            links = re.findall(r'<link rel="stylesheet"\s+[^>]*href="([^"]+)"', page)
            assert links == [
                "/static/vendor/bootstrap/bootstrap.min.css",
                "/static/css/themes/magenta.css",
                "/static/css/portal.css",
                "/static/css/history_records.css",
            ]
            assert value not in page
            titles = [html.unescape(title) for title in re.findall(r'title="([^"]*)"', page)]
            assert titles.count(value) == 2
            assert "2026-09-02T23:01:00-05:00" in titles and "2026-09-03 04:01 UTC" in page
            assert '<a class="history-record-value" title="run-3491" href="/runs/run-3491">run-3491</a>' in page
            assert re.search(r'data-testid="history-table"[^>]*', page)
            assert "history-records-table history-table" not in page

    class TestNegativeInputs:
        """Exercise unreadable inputs and bounded component faults without a browser skip."""

        @pytest.mark.parametrize("kind", ("unscoped", "font", "budget", "ellipsis"))
        def test_component_guard_rejects_a_real_fault(self, kind: str) -> None:
            """The same source decision rejects four bounded faults in actual component text."""
            source = RecordAssetGuard.read(RecordAssetGuard.ROOT / RecordAssetGuard.ASSET)
            changes = {
                "unscoped": (".history-records-table {", ".portal-table {"),
                "font": ("table-layout: fixed;", "table-layout: fixed; font-size: 8px;"),
                "budget": ("width: 3%;", "width: 4%;"),
                "ellipsis": ("text-overflow: ellipsis", "text-overflow: clip"),
            }
            before, after = changes[kind]
            assert before in source
            with pytest.raises(AssertionError):
                RecordAssetGuard.Rules.require(source.replace(before, after))

        def test_required_guard_fails_unreadable_input(self, tmp_path: Path) -> None:
            """A missing required asset must fail with a zero-input count."""
            with pytest.raises(FileNotFoundError):
                RecordAssetGuard.read(tmp_path / "unreadable-history.css")
