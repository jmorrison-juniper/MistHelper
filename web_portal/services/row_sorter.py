"""Order the rows of a data preview page.

Why:
    The preview table let a user click a column header, and the click changed
    only the arrow. ``web_portal/static/js/data_preview.js`` held the sort state
    and never sent it, and the preview route never read one. Issue #3047 records
    the defect.

    Warning: a table that looks sorted and is not is worse than a table with no
    sort at all. An engineer who sorts a rogue DHCP result by the last time seen
    believes the newest finding sits at the top, and then works the wrong row
    first.

Memory:
    The preview paginator streams rows, so it never holds a whole file. A sort
    cannot stream, because the last row of a file can belong on the first page.
    This module therefore reads rows into memory only when a caller asks for a
    sort, and it stops at ``MAX_SORT_ROWS``.

    A file larger than that cap reports ``sort_truncated``. The caller must tell
    the operator, because a silent partial sort is the same lie the defect told.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)  # Use a module logger so records name this module.

# WHY: one sort holds this many rows in memory at most. 50,000 rows of 20 short
# columns stay near 40 MB, which one portal worker can hold. A larger file keeps
# its first rows and reports the cut.
MAX_SORT_ROWS = 50_000

ASCENDING = "asc"  # The direction value that the browser sends for a first click.
DESCENDING = "desc"  # The direction value that the browser sends for a second click.


@dataclass(frozen=True)
class SortSpec:
    """One column order request.

    Attributes:
        column: The zero-based index of the column to order by.
        descending: True to place the largest value first.
    """

    column: int
    descending: bool

    @classmethod
    def from_request(cls, column: Any, direction: Any, column_count: int) -> SortSpec | None:
        """Build a sort request from raw query values.

        The method refuses a column that the table does not hold, so a crafted
        request cannot reach the row reader with a bad index.

        Args:
            column: The requested column index, as text or as a number.
            direction: The requested direction, ``asc`` or ``desc``.
            column_count: The number of columns the file holds.

        Returns:
            The request, or None when the caller asked for no valid sort.
        """
        if column is None or column == "":  # No column means the caller wants the stream order.
            return None
        try:  # A non-numeric index is a bad request, not a server fault.
            index = int(column)
        except (TypeError, ValueError):
            logger.debug("Ignoring a sort column that is not a number: %r", column)
            return None
        if index < 0 or index >= column_count:  # An out-of-range index would raise on every row.
            logger.debug("Ignoring a sort column outside the table: %d of %d", index, column_count)
            return None
        return cls(column=index, descending=str(direction).lower() == DESCENDING)


class RowSorter:
    """Order preview rows by one column, with a bound on the rows it holds.

    Why:
        One class owns the order rule, so the CSV path, the JSON path, and the
        SQLite path cannot disagree about what "sorted" means.
    """

    def __init__(self, max_rows: int = MAX_SORT_ROWS) -> None:
        """Store the row cap.

        Args:
            max_rows: The largest number of rows this sorter holds in memory.
        """
        self._max_rows = max(1, int(max_rows))  # A cap below one would drop every row.

    @property
    def max_rows(self) -> int:
        """Return the largest number of rows this sorter holds.

        The caller reports this number to the operator when the cap cuts a read,
        so the operator learns how much of the file the order covered.
        """
        return self._max_rows

    @staticmethod
    def sort_key(value: Any) -> tuple[int, float, str]:
        """Return a key that orders a cell by value and not by text.

        The key holds three parts. The first part groups empty cells last, so a
        missing value never hides a real one. The second part orders a number by
        its value, so 10 follows 9. The third part orders text without regard to
        case.

        Args:
            value: One cell of a row.

        Returns:
            A tuple that Python can compare against the key of any other cell.
        """
        text = "" if value is None else str(value).strip()
        if not text:  # An empty cell carries no information, so it sorts last.
            return (1, 0.0, "")
        try:  # A numeric cell must order by value, or 10 would sort before 9.
            return (0, float(text), "")
        except ValueError:
            return (0, float("inf"), text.casefold())

    def collect(self, rows: Any) -> tuple[list[Any], bool]:
        """Read rows into memory, up to the cap.

        Args:
            rows: Any iterable of rows.

        Returns:
            The rows that fit, and True when the cap cut the read.
        """
        held: list[Any] = []
        for row in rows:  # Stop at the cap, so one huge file cannot exhaust the worker.
            if len(held) >= self._max_rows:
                logger.warning("The sort reached its %d row cap, so it covers a part of the file", self._max_rows)
                return held, True
            held.append(row)
        return held, False

    def sort(self, rows: list[Any], spec: SortSpec) -> list[Any]:
        """Return the rows in the requested order.

        Args:
            rows: The rows to order.
            spec: The requested column and direction.

        Returns:
            A new list in the requested order.
        """
        logger.info("Sorting %d preview rows on column %d", len(rows), spec.column)  # Action log.

        def key_of(row: Any) -> tuple[int, float, str]:
            """Return the sort key of one row, tolerating a short row."""
            if spec.column >= len(row):  # A ragged file can hold a row with fewer cells.
                return self.sort_key(None)
            return self.sort_key(row[spec.column])

        ordered = sorted(rows, key=key_of, reverse=spec.descending)
        logger.debug("Sorted %d preview rows, descending=%s", len(ordered), spec.descending)  # Result summary.
        return ordered
