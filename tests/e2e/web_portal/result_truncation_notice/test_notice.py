"""Measure real cell geometry and complete-value access for issue 3161."""

import csv
import io
from urllib.parse import urljoin

from playwright.sync_api import Page, expect


class TestResultClippingNotice:
    """Exercise the current template, stylesheet, JavaScript, and preview route."""

    def test_clipped_cell_announces_complete_value_access(self, notice_page: Page) -> None:
        """A real clipped cell must not depend on the unrelated sort-limit flag."""
        measured = (
            notice_page.locator("#resultsBody tr")
            .first.locator("td")
            .nth(1)
            .evaluate("cell => ({visible: cell.clientWidth, content: cell.scrollWidth, text: cell.textContent})")
        )
        print(f"Current cell measurement: {measured}")
        assert measured["content"] > measured["visible"] > 0
        assert len(measured["text"]) == 246
        expect(notice_page.get_by_test_id("results-truncated")).to_be_visible(timeout=1000)
        expect(notice_page.get_by_role("status")).to_contain_text("Some cell text is clipped")
        notice_page.get_by_test_id("results-clipped-row").click()
        expect(notice_page.get_by_test_id("results-row-detail")).to_contain_text(measured["text"])
        expect(notice_page.locator("#resultsSummary")).to_contain_text("1 to 25 of 30")

    def test_short_values_need_no_notice(self, notice_page: Page) -> None:
        """The short control has positive geometry but no hidden content."""
        notice_page.evaluate("OperationResults.selectFile('Short.csv')")
        expect(notice_page.locator("#resultsBody tr").first).to_contain_text("up")
        assert notice_page.locator("#resultsBody td").evaluate_all(
            "cells => cells.every(cell => cell.clientWidth > 0 && cell.scrollWidth <= cell.clientWidth)"
        )
        expect(notice_page.get_by_test_id("results-truncated")).to_be_hidden()

    def test_output_link_preserves_the_complete_download(self, notice_page: Page) -> None:
        """Use the existing output destination and unmodified native download route."""
        notice_page.evaluate("""() => {
                document.getElementById('executionPanel').classList.remove('d-none');
                document.getElementById('outputFiles').classList.remove('d-none');
                document.getElementById('outputFileList').innerHTML =
                    '<li><a href="/api/data/download/Adjacency.csv">Adjacency.csv</a></li>';
            }""")
        notice_page.get_by_test_id("results-complete-output").click()
        expect(notice_page.locator("#outputFiles")).to_be_focused()
        response = notice_page.request.get(urljoin(notice_page.url, "/api/data/download/Adjacency.csv"))
        assert response.status == 200
        records = list(csv.reader(io.StringIO(response.text())))
        assert len(records) == 31
        assert len(records[1][1]) == 246
        assert records[-1] == ["switch-29", "up"]

    def test_pages_and_sorting_update_the_notice(self, notice_page: Page) -> None:
        """The short second page removes clipping without changing the row count."""
        notice_page.get_by_test_id("results-next").click()
        expect(notice_page.locator("#resultsSummary")).to_contain_text("26 to 30 of 30")
        expect(notice_page.locator("#resultsBody tr")).to_have_count(5)
        expect(notice_page.get_by_test_id("results-truncated")).to_be_hidden()
        notice_page.get_by_test_id("results-prev").click()
        expect(notice_page.get_by_test_id("results-truncated")).to_be_visible()
        notice_page.locator("#resultsHead th").first.click()
        expect(notice_page.locator("#resultsHead th.sort-asc")).to_have_text("device_name")
        expect(notice_page.locator("#resultsBody tr").first).to_contain_text("switch-00")
        expect(notice_page.get_by_test_id("results-clipped-row")).to_have_count(1)
        assert notice_page.locator("#resultsBody tr").count() == 25


class TestResultNoticeUpdates:
    """Keep layout, data changes, and existing sorting warnings consistent."""

    def test_layout_changes_remeasure_actual_clipping(self, notice_page: Page) -> None:
        """A layout without hidden text must clear the notice and retain all values."""
        notice_page.add_style_tag(content="#resultsTable td {max-width:none; overflow:visible}")
        expect(notice_page.get_by_test_id("results-truncated")).to_be_hidden(timeout=1000)
        assert notice_page.locator("#resultsBody td").evaluate_all(
            "cells => cells.every(cell => cell.scrollWidth <= cell.clientWidth)"
        )
        notice_page.set_viewport_size({"width": 600, "height": 800})
        notice_page.locator("style").last.evaluate("style => style.remove()")
        expect(notice_page.get_by_test_id("results-truncated")).to_be_visible(timeout=1000)
        notice_page.get_by_test_id("results-clipped-row").press("Enter")
        expect(notice_page.locator(".result-detail-inner")).to_be_focused()
        expect(notice_page.get_by_test_id("results-row-detail")).to_contain_text("neighbor reachable")

    def test_sort_warning_coexists_with_clipping(self, notice_page: Page) -> None:
        """A controlled native preview response can report both presentation limits."""
        response = notice_page.request.get(urljoin(notice_page.url, "/api/data/preview/Adjacency.csv?per_page=25"))
        assert response.status == 200
        data = response.json()
        data.update(sort_truncated=True, sort_limit=50000)
        notice_page.route("**/api/data/preview/**", lambda route: route.fulfill(json=data))
        notice_page.evaluate("OperationResults.sortBy(0)")
        expect(notice_page.get_by_test_id("results-truncated")).to_contain_text("50000 rows only")
        expect(notice_page.get_by_test_id("results-truncated")).to_contain_text("Some cell text is clipped")
        notice_page.add_style_tag(content="#resultsTable td {max-width:none; overflow:visible}")
        expect(notice_page.get_by_test_id("results-clipped-row")).to_have_count(0)
        expect(notice_page.get_by_test_id("results-truncated")).to_contain_text("50000 rows only")

    def test_filter_empty_error_and_reset_clear_old_notice(self, notice_page: Page) -> None:
        """No previous warning survives a different result, error, or cleared run."""
        notice_page.get_by_test_id("results-search").fill("switch-29")
        expect(notice_page.locator("#resultsSummary")).to_contain_text("1 to 1 of 1")
        expect(notice_page.get_by_test_id("results-truncated")).to_be_hidden()
        notice_page.get_by_test_id("results-search").fill("absent-neighbor")
        expect(notice_page.locator("#resultsBody")).to_contain_text("No row matches")
        expect(notice_page.get_by_test_id("results-truncated")).to_be_hidden()
        notice_page.evaluate("OperationResults.selectFile('Adjacency.csv')")
        expect(notice_page.get_by_test_id("results-truncated")).to_be_visible()
        notice_page.route(
            "**/api/data/preview/**", lambda route: route.fulfill(status=500, json={"error": "Read failed"})
        )
        notice_page.evaluate("OperationResults.nextPage()")
        expect(notice_page.locator("#resultsBody")).to_contain_text("Could not read the results")
        expect(notice_page.get_by_test_id("results-truncated")).to_be_hidden()
        notice_page.evaluate("OperationResults.reset()")
        expect(notice_page.get_by_test_id("results-panel")).to_be_hidden()
        assert notice_page.get_by_test_id("results-truncated").inner_text() == ""
