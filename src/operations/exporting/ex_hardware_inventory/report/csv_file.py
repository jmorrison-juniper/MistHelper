"""Render the report rows as CSV bytes and check a written file.

Why:
    Both front ends need the same file format: UTF-8 text, one header row, and
    standard quoting. The check exists because the standard exporter does not
    write atomically. After a write, the check proves that the header and the row
    count match what the run produced, so a partial file never passes as a report.
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
