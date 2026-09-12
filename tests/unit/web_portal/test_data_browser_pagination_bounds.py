"""Bound the page size of the data browser preview on both ends.

The routes clamped the page size at the top only. A negative value therefore
reached SQLite, which reads a negative `LIMIT` as no limit at all. One request
then returned every row of the table. A zero value divided by zero.

These tests prove that the service clamps the page size and the page number.
See issue #1946.
"""

from __future__ import annotations

import logging
import sqlite3

import pytest

from web_portal.services.data_browser import (
    MAX_PAGE_SIZE,
    MIN_PAGE_SIZE,
    DataBrowserService,
)

# The row count of each fixture. The count sits above MAX_PAGE_SIZE so that a
# bypass returns visibly more rows than the cap allows.
TOTAL_ROWS = 1000

# The page size values that a caller can send to defeat a one sided clamp.
OUT_OF_RANGE_SIZES = (-1, 0, -1000, MAX_PAGE_SIZE + 1, 10**9)


@pytest.fixture
def browser(tmp_path):
    """Build a data directory that holds a large CSV, JSON, log, and database."""
    logging.info("Building the data browser fixtures in %s", tmp_path)
    # Write a CSV that holds more rows than the cap allows.
    csv_path = tmp_path / "big.csv"
    # Build the whole body in memory first, because one write is faster than
    # a thousand writes and the fixture runs for every test.
    csv_lines = ["col_a,col_b"]
    csv_lines.extend(f"value_{index},payload_{index}" for index in range(TOTAL_ROWS))
    csv_path.write_text("\n".join(csv_lines) + "\n", encoding="utf-8")

    # Write a JSON array that holds the same number of records.
    json_rows = ",".join(f'{{"id": {index}, "token": "t_{index}"}}' for index in range(TOTAL_ROWS))
    (tmp_path / "big.json").write_text(f"[{json_rows}]", encoding="utf-8")

    # Write a log file, because the log preview shares the same paginator.
    log_lines = "\n".join(f"line {index}" for index in range(TOTAL_ROWS))
    (tmp_path / "big.log").write_text(log_lines + "\n", encoding="utf-8")

    # Write a database that holds a table an attacker would want to read.
    db_path = tmp_path / "big.db"
    # Use a context manager so that the handle closes on the error path too.
    with sqlite3.connect(db_path) as conn:
        conn.execute("CREATE TABLE secrets (id INTEGER, token TEXT)")
        conn.executemany(
            "INSERT INTO secrets VALUES (?, ?)",
            [(index, f"token_{index}") for index in range(TOTAL_ROWS)],
        )
    logging.debug("Built four fixtures that each hold %d rows", TOTAL_ROWS)
    return DataBrowserService(str(tmp_path))


class TestSqlitePageSizeIsBounded:
    """The SQLite preview must never return more rows than the cap allows."""

    @pytest.mark.parametrize("per_page", OUT_OF_RANGE_SIZES)
    def test_out_of_range_size_returns_at_most_the_cap(self, browser, per_page) -> None:
        """An out of range page size returns the cap and not the whole table."""
        logging.info("Requesting the SQLite preview with per_page=%d", per_page)
        # Call the service the same way the route calls it.
        result = browser.preview_sqlite_table("big.db", "secrets", 1, per_page, "")
        # A raised error would surface as an error dict, so check for one first.
        assert "error" not in result, f"per_page={per_page} produced {result.get('error')!r}."
        # The cap is the whole point of the defect, so assert it directly.
        assert len(result["rows"]) <= MAX_PAGE_SIZE, (
            f"per_page={per_page} returned {len(result['rows'])} rows. " f"The cap is {MAX_PAGE_SIZE}."
        )
        logging.debug("per_page=%d returned %d rows", per_page, len(result["rows"]))

    @pytest.mark.parametrize("per_page", OUT_OF_RANGE_SIZES)
    def test_out_of_range_size_with_a_search_returns_at_most_the_cap(self, browser, per_page) -> None:
        """The search branch shares the cap with the plain branch."""
        logging.info("Requesting the SQLite search preview with per_page=%d", per_page)
        # The search branch runs a different query, so it needs its own test.
        result = browser.preview_sqlite_table("big.db", "secrets", 1, per_page, "token")
        # The search must match every row, which makes a bypass visible.
        assert "error" not in result, f"per_page={per_page} produced {result.get('error')!r}."
        assert (
            len(result["rows"]) <= MAX_PAGE_SIZE
        ), f"per_page={per_page} with a search returned {len(result['rows'])} rows."
        logging.debug("The search branch returned %d rows", len(result["rows"]))


class TestFilePageSizeIsBounded:
    """The CSV, JSON, and log previews must share the same cap."""

    @pytest.mark.parametrize("name", ["big.csv", "big.json", "big.log"])
    @pytest.mark.parametrize("per_page", OUT_OF_RANGE_SIZES)
    def test_out_of_range_size_returns_at_most_the_cap(self, browser, name, per_page) -> None:
        """An out of range page size never raises and never exceeds the cap."""
        logging.info("Requesting the preview of %s with per_page=%d", name, per_page)
        # A zero page size raised ZeroDivisionError before the fix. The call
        # sits outside a try block, so Flask returned 500 and a stack trace.
        result = browser.preview_file(name, 1, per_page, "")
        # Confirm that the call produced data and not an internal error text.
        assert "error" not in result, f"{name} per_page={per_page} produced {result.get('error')!r}."
        assert len(result["rows"]) <= MAX_PAGE_SIZE, f"{name} per_page={per_page} returned {len(result['rows'])} rows."
        logging.debug("%s returned %d rows", name, len(result["rows"]))


class TestPageNumberIsBounded:
    """The page number must never produce a negative slice offset."""

    @pytest.mark.parametrize("page", [0, -1, -1000])
    def test_a_low_page_number_returns_the_first_page(self, browser, page) -> None:
        """A page number below one reads the first page."""
        logging.info("Requesting the SQLite preview with page=%d", page)
        # A negative page produced a negative offset, which SQLite rejects and
        # which Python reads as a slice from the end of the list.
        result = browser.preview_sqlite_table("big.db", "secrets", page, 50, "")
        assert "error" not in result, f"page={page} produced {result.get('error')!r}."
        # The reported page must sit inside the valid range.
        assert result["page"] >= 1, f"page={page} reported page {result['page']}."
        # The first row of the first page is the first row of the table.
        assert result["rows"][0][0] == 0, f"page={page} did not return the first page."
        logging.debug("page=%d reported page %d", page, result["page"])


class TestNormalRequestsStillWork:
    """The clamp must not change a request that already sits in range."""

    def test_a_normal_page_size_is_unchanged(self, browser) -> None:
        """A page size inside the range returns exactly that many rows."""
        logging.info("Requesting the SQLite preview with a normal page size")
        # Guard against a clamp that always returns the cap.
        result = browser.preview_sqlite_table("big.db", "secrets", 1, 50, "")
        assert len(result["rows"]) == 50, "A normal page size must not change."
        logging.debug("A normal page size returned %d rows", len(result["rows"]))

    def test_the_second_page_follows_the_first(self, browser) -> None:
        """Paging still walks through the table in order."""
        logging.info("Requesting the second page of the SQLite preview")
        # A clamp that pins the page number to 1 would break paging, so prove
        # that the second page still returns the second block of rows.
        result = browser.preview_sqlite_table("big.db", "secrets", 2, 50, "")
        assert result["rows"][0][0] == 50, "The second page must start at row 50."
        logging.debug("The second page starts at row %d", result["rows"][0][0])

    def test_the_minimum_page_size_returns_one_row(self, browser) -> None:
        """The lower bound is a single row and not an empty page."""
        logging.info("Requesting the SQLite preview with the minimum page size")
        # MIN_PAGE_SIZE names the lower bound, so a caller can read it.
        result = browser.preview_sqlite_table("big.db", "secrets", 1, MIN_PAGE_SIZE, "")
        assert len(result["rows"]) == MIN_PAGE_SIZE, "The minimum page size must return one row."
        logging.debug("The minimum page size returned %d rows", len(result["rows"]))


class TestTheBoundsAreNamed:
    """The bounds must be module constants so that a route can reuse them."""

    def test_the_bounds_hold_sane_values(self) -> None:
        """The lower bound is one row and the upper bound is above it."""
        logging.info("Checking the page size bounds")
        # A lower bound of zero would reintroduce the divide by zero.
        assert MIN_PAGE_SIZE >= 1, "The lower bound must be at least one row."
        # An upper bound below the lower bound would make every clamp empty.
        assert MAX_PAGE_SIZE > MIN_PAGE_SIZE, "The upper bound must sit above the lower bound."
        logging.debug("The bounds are %d and %d", MIN_PAGE_SIZE, MAX_PAGE_SIZE)
