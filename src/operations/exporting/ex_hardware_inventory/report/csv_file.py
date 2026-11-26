"""Render the report rows as CSV bytes, check a written file, and read a page of it.

Why:
    Both front ends need the same file format: UTF-8 text, one header row, and
    standard quoting. The check exists because the standard exporter does not
    write atomically. After a write, the check proves that the header and the row
    count match what the run produced, so a partial file never passes as a report.
    The page reader exists because the portal shows the report as a table. It reads
    the same bytes as the download, so the table and the file never differ.
"""

from __future__ import annotations

import csv  # Write and read standard CSV.
import io  # Hold the text in memory before it becomes bytes.
import logging  # Record each render and each check for the operator trace.
from collections.abc import Mapping, Sequence  # Accept any rows and any column list.

logger = logging.getLogger(__name__)  # Name the logger after this module so log lines carry their source.


class ReportTooLarge(ValueError):
    """Report that a rendered file would pass the byte limit."""


class ReportCheckError(ValueError):
    """Report that a file does not match the rows that it should hold."""


class CsvRenderer:
    """Turn rows into UTF-8 CSV bytes."""

    @staticmethod
    def render(rows: Sequence[Mapping[str, str]], fieldnames: Sequence[str], limit_bytes: int) -> bytes:
        """Render the rows with one header row.

        Args:
            rows: The report rows. A missing key gives an empty cell.
            fieldnames: The column list and order.
            limit_bytes: The most bytes that the file may hold.

        Returns:
            The file bytes, UTF-8 text with CRLF line ends and no byte order mark.

        Raises:
            ReportTooLarge: When the file would pass the limit.
        """
        logger.info("Rendering %d report rows as CSV", len(rows))  # Log before the transform.
        buffer = io.StringIO(newline="")  # The CSV writer manages its own line ends.
        writer = csv.DictWriter(
            buffer, fieldnames=list(fieldnames), lineterminator="\r\n", extrasaction="ignore"
        )  # Standard quoting with CRLF line ends.
        writer.writeheader()  # The first line names the columns.
        writer.writerows(rows)  # Standard quoting keeps awkward values intact.
        data = buffer.getvalue().encode("utf-8")  # The bytes that a writer stores.
        if len(data) > limit_bytes:  # A report over the limit must not be published.
            raise ReportTooLarge(
                f"The report would hold {len(data)} bytes. The limit is {limit_bytes} bytes."
            )  # Never publish a report over the limit.
        logger.debug("Rendered %d bytes of CSV", len(data))  # Log the result size.
        return data  # Hand back the file bytes.


class CsvVerifier:
    """Prove that CSV bytes match the expected columns and row count."""

    @staticmethod
    def verify(data: bytes, fieldnames: Sequence[str], row_count: int) -> None:
        """Check the header, the row count, and the width of every row.

        Args:
            data: The file bytes.
            fieldnames: The expected column list.
            row_count: The expected number of data rows.

        Raises:
            ReportCheckError: When the file does not match.
        """
        logger.info("Checking a report file of %d bytes", len(data))  # Log before the read.
        try:  # A broken file must give one documented error.
            parsed = list(csv.reader(io.StringIO(data.decode("utf-8"), newline="")))  # Read with the same rules.
        except (UnicodeDecodeError, csv.Error) as error:  # The bytes are not valid UTF-8 CSV.
            raise ReportCheckError("The report file is not valid UTF-8 CSV.") from error  # Name the cause once.
        if not parsed or parsed[0] != list(fieldnames):  # The first line must name every column in order.
            raise ReportCheckError("The report header does not match its columns.")  # Refuse the file.
        body = parsed[1:]  # Every line after the header is a data row.
        if len(body) != row_count:  # A short file means a lost row.
            raise ReportCheckError(
                f"The report holds {len(body)} rows. It should hold {row_count} rows."
            )  # A short file means a lost row.
        if any(len(row) != len(fieldnames) for row in body):  # A ragged row means a damaged file.
            raise ReportCheckError("A report row has the wrong number of cells.")  # Refuse the file.
        logger.debug("The report file passed its check with %d rows", len(body))  # Log the result.


class CsvPreviewer:
    """Read one page of rows from CSV bytes for a table view."""

    CELL_LIMIT = 1000  # The most characters that one cell keeps in a preview.

    @classmethod
    def page(cls, data: bytes, offset: int, limit: int, text: str = "") -> dict[str, object]:
        """Return the columns and one page of the rows that hold a filter text.

        Why:
            The portal shows the report as a table. A filter over the whole file,
            and not over one page, keeps the row counts true.

        Args:
            data: The file bytes.
            offset: The number of matching rows to skip.
            limit: The most rows in the page.
            text: A plain text that one cell must hold, with case ignored. Empty text matches each row.

        Returns:
            The columns, the page of rows, the data row count, the matching row count, and the cut cell count.

        Raises:
            ValueError: When the offset is below 0 or the limit is below 1.
            ReportCheckError: When the file is not valid UTF-8 CSV, is empty, or has a row of the wrong width.
        """
        if offset < 0 or limit < 1:  # A negative slice would read from the end of the list.
            raise ValueError("The page offset must be 0 or more, and the page limit must be 1 or more.")
        logger.info("Reading a page of up to %d rows at offset %d from %d bytes", limit, offset, len(data))
        columns, rows = cls._read(data)  # One parse gives the header and the data rows.
        needle = text.strip().casefold()  # A plain, case-insensitive match never builds a pattern from the text.
        matched = [row for row in rows if cls._holds(row, needle)]  # The filter runs over the whole report.
        shown, cut = cls._cut(matched[offset : offset + limit])  # Only the rows of this page leave the server.
        logger.debug("Read %d of %d matching rows from %d data rows", len(shown), len(matched), len(rows))
        return {
            "columns": columns,
            "rows": shown,
            "offset": offset,
            "limit": limit,
            "total": len(rows),
            "matched": len(matched),
            "cut_cells": cut,
        }  # The portal sends this answer as JSON.

    @classmethod
    def _cut(cls, window: list[list[str]]) -> tuple[list[list[str]], int]:
        """Return the rows with each cell cut at the limit, and the number of cells that lost text."""
        cut = sum(len(cell) > cls.CELL_LIMIT for row in window for cell in row)  # Count the cells that lose text.
        return [
            [cell[: cls.CELL_LIMIT] for cell in row] for row in window
        ], cut  # A huge cell never makes a huge answer.

    @staticmethod
    def _read(data: bytes) -> tuple[list[str], list[list[str]]]:
        """Return the header and the data rows, or raise when the bytes are not a report."""
        try:  # A broken file must give one documented error.
            parsed = list(csv.reader(io.StringIO(data.decode("utf-8"), newline="")))  # Read with the same rules.
        except (UnicodeDecodeError, csv.Error) as error:  # The bytes are not valid UTF-8 CSV.
            raise ReportCheckError("The report file is not valid UTF-8 CSV.") from error  # Name the cause once.
        if not parsed:  # An empty file has no header, so it is no report.
            raise ReportCheckError("The report file is empty.")  # Refuse the file.
        columns, rows = parsed[0], parsed[1:]  # The first line names the columns.
        if any(len(row) != len(columns) for row in rows):  # A ragged row means a damaged file.
            raise ReportCheckError("A report row has the wrong number of cells.")  # Refuse the file.
        return columns, rows  # The caller filters and pages these rows.

    @staticmethod
    def _holds(row: Sequence[str], needle: str) -> bool:
        """Return true when there is no filter, or when one cell holds the filter text."""
        return not needle or any(needle in cell.casefold() for cell in row)  # A plain text search, never a pattern.
