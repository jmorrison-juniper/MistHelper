"""Browser tests for the operation results table (issue #3048).

Why:
    An operation used to report its result as a log. A log cannot be sorted, it
    cannot be filtered, and a row cannot be opened. The rogue DHCP scan of menu
    269 writes 20 columns for each finding, and a log line cannot carry that.

    These tests drive the table the way an engineer does. They read the rendered
    geometry as well, because two layout defects appeared during the work and
    neither one changes the document.

Layout history:
    The shared table rule carries ``word-break: break-word``. With 27 narrow
    columns it broke "Louisburg" into three stacked lines and made one row 880
    pixels tall. The detail block also inherited the full 2210 pixel table
    width, so a reader had to scroll sideways to read it.
"""

from __future__ import annotations

import csv
import logging
import socket
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

logger = logging.getLogger(__name__)

pytest.importorskip("playwright", reason="playwright is absent, so no browser test can run")

READY_TIMEOUT_MS = 15000  # One page load must not block the suite.
SETTLE_MS = 700  # The table asks the server after each control, so allow one round trip.
MAX_DATA_ROW_HEIGHT = 120  # One row of one line stays near 42 pixels on this layout.

COLUMNS = ["site_name", "device_name", "port_id", "state", "count", "details"]
ROWS = [
    ["Denver Branch", "SW-EDGE-01", "ge-0/0/9", "active", "9", "A long detail line " * 6],
    ["Austin Campus", "SW-CORE-02", "ge-0/0/3", "historical", "10", "Another long detail line"],
    ["Boston Lab", "SW-LAB-07", "ge-0/0/1", "active", "2", "Louisburg mixed with other text"],
]


def free_port() -> int:
    """Return a port that no other process holds right now."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))  # Port zero asks the operating system for a free port.
        return int(probe.getsockname()[1])


@pytest.fixture(scope="module")
def results_portal(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    """Serve a portal whose data directory holds one result file."""
    from werkzeug.serving import make_server

    from web_portal.app import WebPortalApp
    from web_portal.menu_registry import build_static_menu_actions

    data_dir: Path = tmp_path_factory.mktemp("results_data")
    with open(data_dir / "Findings.csv", "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS)
        writer.writerows(ROWS)

    app = WebPortalApp.create_app(apisession=None, menu_actions=build_static_menu_actions(), org_id="test-org")
    app.config["TESTING"] = True
    app.config["DATA_DIR"] = str(data_dir)

    port = free_port()  # Never take a fixed port, because a developer may hold it.
    server = make_server("127.0.0.1", port, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    logger.info("Starting the results portal on port %d", port)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=10)
        WebPortalApp.shutdown_app(app)


@pytest.fixture
def results_page(page: Any, results_portal: str) -> Any:
    """Open the operations page and render the result file in the table."""
    page.goto(f"{results_portal}/operations", wait_until="networkidle", timeout=READY_TIMEOUT_MS)
    page.wait_for_selector(".op-item", state="attached", timeout=READY_TIMEOUT_MS)
    # Render the file directly. A real run needs Mist credentials, and the table
    # reads the same endpoint either way.
    page.evaluate("() => OperationResults.showForRun(['Findings.csv'])")
    page.wait_for_selector("#resultsBody tr", timeout=READY_TIMEOUT_MS)
    return page


def column_values(page: Any, index: int) -> list[str]:
    """Return one column of the rendered rows, skipping any open detail."""
    return page.evaluate(
        "idx => Array.from(document.querySelectorAll('#resultsBody tr:not(.result-detail)'))"
        ".map(tr => (tr.querySelectorAll('td')[idx] || {}).textContent || '')",
        index,
    )


class TestTheResultsTableReplacesTheLog:
    """Prove the table answers the questions a log cannot."""

    def test_the_table_paints_every_row(self, results_page: Any) -> None:
        """A table with no row proves nothing below, so measure it first."""
        rows = len(column_values(results_page, 0))
        print(f"The results table painted {rows} rows and {len(COLUMNS)} columns.")
        assert rows == len(ROWS), "The table did not paint one row for each record."

    def test_the_panel_is_visible_without_an_extra_click(self, results_page: Any) -> None:
        """Issue #3048. The result used to sit two clicks away, behind a modal."""
        assert results_page.locator('[data-testid="results-panel"]').is_visible()

    def test_a_heading_sorts_the_rows(self, results_page: Any) -> None:
        """Issue #3047 made this possible, and the table depends on it."""
        before = column_values(results_page, 0)
        results_page.evaluate("() => OperationResults.sortBy(0)")
        results_page.wait_for_timeout(SETTLE_MS)
        ascending = column_values(results_page, 0)
        assert ascending == sorted(before, key=str.casefold), "The heading did not order the rows."

    def test_a_second_click_reverses_the_order(self, results_page: Any) -> None:
        """A reader flips the order to see the other end of the result."""
        results_page.evaluate("() => OperationResults.sortBy(0)")
        results_page.wait_for_timeout(SETTLE_MS)
        ascending = column_values(results_page, 0)
        results_page.evaluate("() => OperationResults.sortBy(0)")
        results_page.wait_for_timeout(SETTLE_MS)
        assert column_values(results_page, 0) == list(reversed(ascending))

    def test_a_count_column_sorts_by_value(self, results_page: Any) -> None:
        """A text order would put 10 before 9, which reads as wrong to an operator."""
        results_page.evaluate("() => OperationResults.sortBy(4)")
        results_page.wait_for_timeout(SETTLE_MS)
        assert column_values(results_page, 4) == ["2", "9", "10"]

    def test_the_filter_narrows_the_result(self, results_page: Any) -> None:
        """An engineer asks whether one site appears at all."""
        results_page.fill('[data-testid="results-search"]', "Denver")
        results_page.wait_for_timeout(SETTLE_MS + 400)  # The filter waits for a pause in typing.
        assert column_values(results_page, 0) == ["Denver Branch"]

    def test_a_row_opens_every_field(self, results_page: Any) -> None:
        """A 6-column record already crowds a screen, and a 27-column record cannot fit."""
        results_page.evaluate("() => OperationResults.toggleRow(0)")
        results_page.wait_for_timeout(300)
        detail = results_page.locator('[data-testid="results-row-detail"]')
        assert detail.count() == 1, "Selecting a row opened no detail."
        assert detail.locator("dt").count() == len(COLUMNS), "The detail names fewer fields than the file holds."

    def test_a_second_click_closes_the_detail(self, results_page: Any) -> None:
        """An open detail must not trap the reader."""
        results_page.evaluate("() => OperationResults.toggleRow(0)")
        results_page.wait_for_timeout(250)
        results_page.evaluate("() => OperationResults.toggleRow(0)")
        results_page.wait_for_timeout(250)
        assert results_page.locator('[data-testid="results-row-detail"]').count() == 0

    def test_the_summary_states_the_row_count(self, results_page: Any) -> None:
        """A reader must know whether the page shows the whole result."""
        summary = results_page.locator('[data-testid="results-summary"]').inner_text()
        assert str(len(ROWS)) in summary

    def test_a_sorted_heading_shows_one_arrow(self, results_page: Any) -> None:
        """The arrow comes from the stylesheet, so the heading text must hold none.

        ``portal.css`` adds the arrow through the ``sort-asc`` and ``sort-desc``
        rules with an ``::after`` rule. A second arrow inside the heading text
        renders twice, and the heading then reads "country down down".
        """
        results_page.evaluate("() => OperationResults.sortBy(0)")
        results_page.wait_for_timeout(SETTLE_MS)
        heading = results_page.evaluate(
            "() => { const th = document.querySelector('#resultsHead th.sort-asc, #resultsHead th.sort-desc');"
            " return th ? { text: th.textContent, cls: th.className } : null; }"
        )
        assert isinstance(heading, dict), "No heading carries a sort class, so the order is not visible."
        for arrow in ("\u25b2", "\u25bc", "\u2191", "\u2193"):
            assert arrow not in heading["text"], (
                f"The heading text holds the arrow {arrow!r} and the stylesheet adds another one, "
                f"so the reader sees two. Heading: {heading['text']!r}."
            )


class TestTheLayoutStaysReadable:
    """Guard the two defects that the document alone cannot show."""

    def test_a_data_row_stays_on_one_line(self, results_page: Any) -> None:
        """The shared break-word rule made one row 880 pixels tall."""
        heights = results_page.evaluate(
            "() => Array.from(document.querySelectorAll('#resultsBody tr:not(.result-detail)'))"
            ".map(tr => tr.getBoundingClientRect().height)"
        )
        tallest = max(heights)
        assert tallest < MAX_DATA_ROW_HEIGHT, (
            f"One result row is {tallest:.0f} pixels tall. A narrow column is breaking words, "
            "which stacks a single value over several lines. Issue #3048."
        )

    def test_the_row_detail_needs_no_sideways_scroll(self, results_page: Any) -> None:
        """A detail that inherits the full table width is unreadable."""
        results_page.evaluate("() => OperationResults.toggleRow(0)")
        results_page.wait_for_timeout(300)
        measured = results_page.evaluate(
            "() => { const wrap = document.getElementById('resultsTableWrap');"
            " const inner = document.querySelector('.result-detail-inner');"
            " return inner ? { inner: inner.getBoundingClientRect().width,"
            " visible: wrap.getBoundingClientRect().width } : null; }"
        )
        assert isinstance(measured, dict), "The detail block did not render, so no width could be read."
        assert measured["inner"] <= measured["visible"] + 2, (
            f"The row detail is {measured['inner']:.0f} pixels wide inside a "
            f"{measured['visible']:.0f} pixel panel, so a reader must scroll sideways. Issue #3048."
        )
