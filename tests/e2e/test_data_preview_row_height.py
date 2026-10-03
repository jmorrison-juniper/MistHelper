"""Prove compact rows with the actual preview renderer for issue #3311."""

from __future__ import annotations

import csv
import logging
from collections.abc import Iterator
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import pytest
from playwright.sync_api import Page, expect

from tests.support.data_preview_harness import (
    DataPreviewHarness,
    LoopbackPreviewServer,
    PreviewBrowser,
    PreviewRowBudget,
)

pytest_plugins = [__name__]  # Register the already rewritten module before any required case can receive a skip.


@pytest.fixture
def compact_portal(tmp_path: Path) -> Iterator[DataPreviewHarness]:
    """Serve only temporary data and actual portal templates."""
    harness = DataPreviewHarness(tmp_path)
    with LoopbackPreviewServer(harness.app).serve() as url:
        harness.url = url
        yield harness


@pytest.fixture
def preview_browser(
    page: Page, compact_portal: DataPreviewHarness, pytestconfig: pytest.Config
) -> Iterator[PreviewBrowser]:
    """Keep every console error visible to the test result."""
    browser = PreviewBrowser(page, compact_portal, screenshots=pytestconfig.getoption("screenshot") == "on")
    browser.open(compact_portal.url, compact_portal.fixture.filename)
    yield browser
    browser.verify()


class TestCompactPreviewRows:
    """Measure every rendered row at each required width and theme."""

    @pytest.mark.parametrize(
        ("width", "theme"),
        [
            (width, theme)
            for theme in ("dark", "light", "magenta", "high-contrast")
            for width in (1024, 1280, 1440, 1600)
        ],
        ids=[
            f"{theme}-{width}"
            for theme in ("dark", "light", "magenta", "high-contrast")
            for width in (1024, 1280, 1440, 1600)
        ],
    )
    def test_every_row_stays_within_budget(
        self, preview_browser: PreviewBrowser, tmp_path: Path, width: int, theme: str
    ) -> None:
        """A computed style alone cannot prove that long rows remain compact."""
        page = preview_browser.page
        page.set_viewport_size({"width": width, "height": 1000})
        page.evaluate("theme => applyTheme(theme)", theme)
        page.wait_for_function(
            "theme => document.getElementById('theme-css').sheet?.href.endsWith('/' + theme + '.css')",
            arg=theme,
        )
        expect(page.locator("#dataPreviewPageInfo")).to_have_text("Page 1 of 3 (112 rows)")
        measured = PreviewRowBudget.capture(page, tmp_path / f"preview-{theme}-{width}", preview_browser.screenshots)
        assert PreviewRowBudget.check(measured["heights"]) == 50
        assert PreviewRowBudget.check(measured["headerHeights"]) == 1
        assert measured["columnCount"] == 43
        assert measured["cellCounts"] == [43] * 50
        assert all(
            abs(left - cell_left) <= 1 and abs(right - cell_right) <= 1
            for left, cell_left, right, cell_right in measured["alignment"]
        )
        self._assert_real_scroll(page)

    def _assert_real_scroll(self, page: Page) -> None:
        """Use a real wheel event to reach the last record and the last column."""
        wrapper = page.locator("#dataPreviewModal .modal-body")
        wrapper.hover(position={"x": 50, "y": 100})
        page.mouse.wheel(10000, 10000)
        last_cell = page.locator("#modalPreviewTable tbody tr").last.locator("td").last
        expect(last_cell.get_by_role("button")).to_be_in_viewport(ratio=1)
        position = wrapper.evaluate("wrap => ({left: wrap.scrollLeft, top: wrap.scrollTop})")
        assert position["left"] > 0
        assert position["top"] > 0
        heading_left = page.locator("#modalPreviewTable th").last.evaluate("cell => cell.getBoundingClientRect().left")
        cell_left = last_cell.evaluate("cell => cell.getBoundingClientRect().left")
        assert abs(heading_left - cell_left) <= 1

    @pytest.mark.parametrize(
        "failure",
        [
            (404, '{"error":"The fixture file is missing."}', "The fixture file is missing."),
            (500, "<h1>Server error</h1>", "The portal failed to answer. Read data/script.log for the cause."),
            (200, "", "The portal answered with status 200."),
            (200, "{invalid JSON", "The portal answered with status 200."),
        ],
        ids=["http-4xx", "http-5xx", "empty-body", "malformed-json"],
    )
    def test_preview_errors_show_no_success_table(
        self, preview_browser: PreviewBrowser, failure: tuple[int, str, str]
    ) -> None:
        """Count deliberate HTTP errors and reject a success display after a failure."""
        page = preview_browser.page
        status, body, message = failure
        preview_browser.expected_http_errors = (status,) if status >= 400 else ()
        page.route(
            "**/api/data/preview/OrgMarvisActions.csv?**",
            lambda route: route.fulfill(
                status=status, body=body, content_type="application/json", headers=preview_browser.owner_headers
            ),
        )
        page.evaluate("() => DataPreviewModal.openPreview('OrgMarvisActions.csv')")
        expect(page.locator("#dataPreviewBody .text-danger")).to_have_text(message)
        assert page.locator("#modalPreviewTable").count() == 0
        assert page.locator("#dataPreviewBody img, #dataPreviewBody script").count() == 0

    def test_a_missing_preview_body_reports_the_failure(self, preview_browser: PreviewBrowser) -> None:
        """A missing render target must report the cause rather than fail silently."""
        page = preview_browser.page
        page.locator("#dataPreviewBody").evaluate("body => body.remove()")
        with page.expect_event("console", predicate=lambda message: message.type == "warning") as warned:
            page.evaluate("() => DataPreviewModal.openPreview('OrgMarvisActions.csv')")
        assert warned.value.text == "Caution: the preview body is missing. The portal cannot display the table."
        assert page.locator("#modalPreviewTable").count() == 0


class TestFullPreviewCellValues:
    """Keep complete values readable without enlarging a table row."""

    @pytest.mark.parametrize(
        "selection",
        [(0, 1), (1, 1), (0, 2), (0, 3), (0, 4), (0, 5)],
        ids=["long-json", "longer-json", "quotes", "markup", "unicode", "newlines"],
    )
    def test_exact_values_are_keyboard_readable(
        self, preview_browser: PreviewBrowser, compact_portal: DataPreviewHarness, selection: tuple[int, int]
    ) -> None:
        """Enter opens exact text and Escape returns focus without closing the preview."""
        page = preview_browser.page
        cell = page.locator("#modalPreviewTable tbody tr").nth(selection[0]).locator("td").nth(selection[1])
        button = cell.get_by_role("button")
        value = compact_portal.fixture.rows[selection[0]][selection[1]]
        assert cell.get_attribute("title") == value
        assert button.text_content() == value
        button.press("Enter")
        dialog = page.get_by_role("dialog", name="Full cell value", exact=True)
        expect(dialog).to_be_visible()
        assert dialog.locator("#dataPreviewCellText").text_content() == value
        assert dialog.locator("img, script").count() == 0
        assert page.evaluate("() => typeof window.previewInjection") == "undefined"
        heights = page.locator("#modalPreviewTable tbody tr").evaluate_all(
            "rows => rows.map(row => row.getBoundingClientRect().height)"
        )
        assert PreviewRowBudget.check(heights) == 50
        page.keyboard.press("Escape")
        expect(dialog).not_to_be_visible()
        expect(page.locator("#dataPreviewModal")).to_be_visible()
        expect(button).to_be_focused()

    def test_space_and_close_return_focus(self, preview_browser: PreviewBrowser) -> None:
        """Space, Tab, and Enter keep focus in the dialog and return it to the cell."""
        page = preview_browser.page
        button = page.locator("#modalPreviewTable tbody tr").first.locator("td").nth(1).get_by_role("button")
        button.press("Space")
        dialog = page.get_by_role("dialog", name="Full cell value", exact=True)
        expect(dialog).to_be_visible()
        assert len(dialog.locator("#dataPreviewCellText").text_content() or "") == 558
        close = dialog.get_by_role("button", name="Close full value", exact=True)
        expect(close).to_be_focused()
        page.keyboard.press("Tab")
        expect(dialog.locator("#dataPreviewCellText")).to_be_focused()
        page.keyboard.press("Shift+Tab")
        expect(close).to_be_focused()
        close.press("Enter")
        expect(dialog).not_to_be_visible()
        expect(button).to_be_focused()

    @pytest.mark.browser_context_args(viewport={"width": 1024, "height": 1000}, has_touch=True)
    def test_touch_reads_the_full_value(
        self, preview_browser: PreviewBrowser, compact_portal: DataPreviewHarness, tmp_path: Path
    ) -> None:
        """Touch targets keep the same row budget and exact full text."""
        page = preview_browser.page
        measured = PreviewRowBudget.capture(page, tmp_path / "preview-touch-1024", preview_browser.screenshots)
        assert PreviewRowBudget.check(measured["heights"]) == 50
        button = page.locator("#modalPreviewTable tbody tr").first.locator("td").nth(1).get_by_role("button")
        bounds = button.bounding_box()
        assert isinstance(bounds, dict)
        assert bounds["height"] >= 44
        button.tap()
        dialog = page.get_by_role("dialog", name="Full cell value", exact=True)
        expect(dialog).to_be_visible()
        assert dialog.locator("#dataPreviewCellText").text_content() == compact_portal.fixture.rows[0][1]
        if preview_browser.screenshots:
            dialog.screenshot(path=str(tmp_path / "preview-touch-full-value.png"))
        dialog.get_by_role("button", name="Close full value", exact=True).tap()
        expect(dialog).not_to_be_visible()
        expect(button).to_be_focused()

    def test_sqlite_value_types_and_headers_remain_text(self, preview_browser: PreviewBrowser) -> None:
        """The shared renderer retains null conversion and never interprets a header as markup."""
        page = preview_browser.page
        header = '<img src=x onerror="window.previewInjection=true">\'" & \u4ea4\u6362'
        special = '"quoted" <script>window.previewInjection=true</script>\ncaf\u00e9'
        answer = dict(
            columns=[header, "empty", "zero", "false", "special"],
            rows=[[None, "", 0, False, special]],
            total_rows=1,
        )
        page.route(
            "**/api/data/preview/Values.db/rows?**",
            lambda route: route.fulfill(json=answer, headers=preview_browser.owner_headers),
        )
        page.evaluate("() => DataPreviewModal.openSqliteTable('Values.db', 'rows')")
        expect(page.locator("#modalPreviewTable tbody tr")).to_have_count(1)
        assert page.locator("#modalPreviewTable th").first.text_content() == header
        assert page.locator("#modalPreviewTable td").all_text_contents() == ["", "", "0", "false", special]
        page.locator("#modalPreviewTable td").first.get_by_role("button").press("Enter")
        dialog = page.get_by_role("dialog", name="Full cell value", exact=True)
        expect(dialog).to_be_visible()
        assert dialog.locator("#dataPreviewCellColumn").text_content() == "Column: " + header
        assert dialog.locator("#dataPreviewCellText").text_content() == ""
        assert page.locator("#modalPreviewTable img, #modalPreviewTable script").count() == 0
        assert page.evaluate("() => typeof window.previewInjection") == "undefined"

    def test_replace_and_hide_close_the_full_value(self, preview_browser: PreviewBrowser) -> None:
        """A replacement preview cannot retain a stale full-value dialog."""
        page = preview_browser.page
        button = page.locator("#modalPreviewTable tbody tr").first.locator("td").nth(1).get_by_role("button")
        button.press("Enter")
        dialog = page.get_by_role("dialog", name="Full cell value", exact=True)
        expect(dialog).to_be_visible()
        page.evaluate("() => DataPreviewModal.openPreview('OrgMarvisActions.csv')")
        expect(dialog).not_to_be_visible()
        expect(page.locator("#modalPreviewTable tbody tr")).to_have_count(50)
        button.press("Enter")
        expect(dialog).to_be_visible()
        page.evaluate("() => DataPreviewModal.hide()")
        expect(dialog).not_to_be_visible()
        expect(page.locator("#dataPreviewModal")).not_to_be_visible()
        assert page.locator("#dataPreviewCellDialog[open]").count() == 0


class TestExistingPreviewControls:
    """Keep actual pagination, sorting, search, and CSV values unchanged."""

    def test_all_three_pages_keep_their_exact_records(
        self, preview_browser: PreviewBrowser, compact_portal: DataPreviewHarness
    ) -> None:
        """Next and Prev retain the 50, 50, and 12 record page boundaries."""
        page = preview_browser.page
        for number, first, count in ((1, 0, 50), (2, 50, 50), (3, 100, 12)):
            expect(page.locator("#dataPreviewPageInfo")).to_have_text(f"Page {number} of 3 (112 rows)")
            records = page.locator("#modalPreviewTable tbody tr").evaluate_all(
                "rows => rows.map(row => Array.from(row.cells, cell => cell.textContent))"
            )
            assert records == compact_portal.fixture.rows[first : first + count]
            if number < 3:
                page.locator("#dataPreviewNext").click()
        expect(page.locator("#dataPreviewNext")).to_be_disabled()
        page.locator("#dataPreviewPrev").click()
        expect(page.locator("#dataPreviewPageInfo")).to_have_text("Page 2 of 3 (112 rows)")
        assert page.locator("#modalPreviewTable tbody tr").count() == 50

    def test_header_sort_keeps_request_parameters(self, preview_browser: PreviewBrowser) -> None:
        """The server still sorts the whole file in both directions."""
        page = preview_browser.page
        for direction, first in (("asc", "Row 001"), ("desc", "Row 112")):
            with page.expect_response("**/api/data/preview/**") as answered:
                page.locator("#modalPreviewTable th").first.click()
            response = answered.value
            parameters = parse_qs(urlsplit(response.url).query)
            assert parameters["sort_column"] == ["0"]
            assert parameters["sort_dir"] == [direction]
            assert parameters["page"] == ["1"]
            assert parameters["per_page"] == ["50"]
            assert response.json()["total_rows"] == 112
            expect(page.locator("#modalPreviewTable tbody tr").first.locator("td").first).to_have_text(first)
            assert page.locator("#modalPreviewTable th").first.get_attribute("class") == "sort-" + direction

    def test_search_keeps_exact_response_values(self, preview_browser: PreviewBrowser) -> None:
        """The existing search control still selects the requested record."""
        page = preview_browser.page
        with page.expect_response("**/api/data/preview/**") as answered:
            page.locator("#dataPreviewSearch").fill("Row 112")
        response = answered.value
        assert parse_qs(urlsplit(response.url).query)["search"] == ["Row 112"]
        assert response.json()["total_rows"] == 1
        expect(page.locator("#modalPreviewTable tbody tr")).to_have_count(1)
        assert page.locator("#modalPreviewTable tbody tr").first.locator("td").first.text_content() == "Row 112"
        expect(page.locator("#dataPreviewPagination")).not_to_be_visible()

    def test_csv_export_keeps_full_values(
        self, preview_browser: PreviewBrowser, compact_portal: DataPreviewHarness
    ) -> None:
        """Cell controls must not add their labels or shorten exported values."""
        page = preview_browser.page
        original = compact_portal.fixture.path.read_bytes()
        with page.expect_download() as downloaded:
            page.locator("#dataPreviewModal").get_by_role("button", name="Export CSV", exact=True).click()
        download = downloaded.value
        assert download.suggested_filename == "preview_export.csv"
        assert download.path().read_bytes() == compact_portal.fixture.export_page_bytes()
        with download.path().open(encoding="utf-8", newline="") as handle:
            exported = list(csv.reader(handle))
        assert exported == [compact_portal.fixture.columns, *compact_portal.fixture.rows[:50]]
        assert compact_portal.fixture.path.read_bytes() == original

    @pytest.mark.parametrize("theme", ["dark", "light", "magenta", "high-contrast"])
    def test_results_dimensions_survive_a_modal_preview(
        self, preview_browser: PreviewBrowser, compact_portal: DataPreviewHarness, theme: str
    ) -> None:
        """The general results table keeps its dimensions and opens its own row detail."""
        page = preview_browser.page
        page.goto(compact_portal.url + "/operations", wait_until="networkidle")
        page.evaluate("theme => applyTheme(theme)", theme)
        page.wait_for_function(
            "theme => document.getElementById('theme-css').sheet?.href.endsWith('/' + theme + '.css')", arg=theme
        )
        page.evaluate("() => OperationResults.showForRun(['OrgMarvisActions.csv'])")
        expect(page.locator("#resultsBody tr")).to_have_count(25)
        before = page.locator("#resultsTable").evaluate(PreviewRowBudget.result_geometry_script)
        page.evaluate("() => DataPreviewModal.openPreview('OrgMarvisActions.csv')")
        expect(page.locator("#modalPreviewTable tbody tr")).to_have_count(50)
        preview_browser.wait_modal_ready()
        page.evaluate("() => DataPreviewModal.hide()")
        expect(page.locator("#dataPreviewModal")).not_to_be_visible()
        assert page.locator("#resultsTable").evaluate(PreviewRowBudget.result_geometry_script) == before
        assert max(before["rows"]) <= 60
        page.locator("#resultsBody tr").first.click()
        expect(page.get_by_test_id("results-row-detail")).to_be_visible()
        assert page.get_by_test_id("results-row-detail").locator("dt").count() == 43


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Fail required preview cases when a test capability is unavailable."""
    checked = sum(item.path.name == "test_data_preview_row_height.py" for item in items)
    if checked == 0:
        return
    logging.info("Checking capabilities for %d required preview browser cases.", checked)
    for plugin, package in (("timeout", "pytest-timeout"), ("playwright", "pytest-playwright")):
        if not config.pluginmanager.hasplugin(plugin):
            raise pytest.UsageError(
                f"Checked {checked} required preview cases. {package} is missing. Required preview cases cannot skip."
            )
    logging.debug("Checked %d required preview cases. All test capabilities are available.", checked)
