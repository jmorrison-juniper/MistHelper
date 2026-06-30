"""Unit tests for CSVAddressIngester (1003-site-address-audit)."""

import pytest

from src.site.address_audit.csv_ingester import CSVAddressIngester
from src.site.address_audit.models import AddressRow

_SAMPLE = (
    "2012233588\tSSR130\t5550 N Military Trail Unit 200\tBoca Raton\tFL\t33431\n"
    "2012234081\tSSR130\t6000 Glades Rd Suite 1019A\tBoca Raton\tFL\t33431\n"
    "2017233102\tSSR130\t4103 14th St W Suite 101\tBradenton\tFL\t34205\n"
    "2012233133\tSSR130\t459 Brandon Town Center Mall Suite 330\tBrandon\tFL\t33511\n"
)


def _write(tmp_path, text):
    """Write CSV text to a temp file and return its path."""
    path = tmp_path / "audit.tsv"
    path.write_text(text, encoding="utf-8")
    return str(path)


class TestLoad:
    """CSVAddressIngester.load behavior."""

    def test_parses_four_rows(self, tmp_path):
        """A clean 4-row sample yields four AddressRow objects, zero failures."""
        rows, failures = CSVAddressIngester().load(_write(tmp_path, _SAMPLE))
        assert len(rows) == 4
        assert failures == 0
        assert all(isinstance(r, AddressRow) for r in rows)
        assert rows[0].serial == "2012233588"
        assert rows[0].city == "Boca Raton"

    def test_embedded_newline_in_quoted_field_flattened(self, tmp_path):
        """A quoted address with an embedded newline is read as one field and flattened."""
        text = '2012233588\tSSR130\t"5550 N Military Trail\n Unit 200"\tBoca Raton\tFL\t33431\n'
        rows, failures = CSVAddressIngester().load(_write(tmp_path, text))
        assert failures == 0
        assert rows[0].serial == "2012233588"
        assert "\n" not in rows[0].address
        assert rows[0].address == "5550 N Military Trail Unit 200"
        assert rows[0].city == "Boca Raton"

    def test_empty_serial_skipped(self, tmp_path):
        """A row with an empty serial is skipped and counted as a failure."""
        text = "\tSSR130\t123 Main St\tTown\tFL\t33000\n" + _SAMPLE
        rows, failures = CSVAddressIngester().load(_write(tmp_path, text))
        assert failures == 1
        assert len(rows) == 4

    def test_non_numeric_serial_skipped(self, tmp_path):
        """A row with a non-numeric serial is skipped."""
        text = "ABC123\tSSR130\t1 A St\tT\tFL\t1\n"
        rows, failures = CSVAddressIngester().load(_write(tmp_path, text))
        assert rows == []
        assert failures == 1

    def test_whitespace_trimmed(self, tmp_path):
        """Surrounding whitespace on fields is trimmed."""
        text = "2012233588\t SSR130 \t  1 A St  \t Town \t FL \t 33000 \n"
        rows, _ = CSVAddressIngester().load(_write(tmp_path, text))
        assert rows[0].model == "SSR130"
        assert rows[0].address == "1 A St"
        assert rows[0].city == "Town"

    def test_file_not_found_raises(self):
        """A missing file raises a controlled FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            CSVAddressIngester().load("does_not_exist_12345.tsv")


class TestDelimiterDetection:
    """Auto-detection of comma vs tab delimiters (the Book1.csv bug)."""

    def _write_csv(self, tmp_path, text):
        """Write to a .csv file and return its path."""
        path = tmp_path / "Book1.csv"
        path.write_text(text, encoding="utf-8")
        return str(path)

    def test_comma_delimited_excel_export(self, tmp_path):
        """A comma-delimited .csv (Excel default) parses all rows -- regression for Book1.csv."""
        text = (
            "2012233588,SSR130,5550 N Military Trail Unit 200,Boca Raton,FL,33431\n"
            "2012234081,SSR130,6000 Glades Rd Suite 1019A,Boca Raton,FL,33431\n"
            "2017233102,SSR130,4103 14th St W Suite 101,Bradenton,FL,34205\n"
        )
        rows, failures = CSVAddressIngester().load(self._write_csv(tmp_path, text))
        assert failures == 0
        assert len(rows) == 3
        assert rows[0].serial == "2012233588"
        assert rows[0].address == "5550 N Military Trail Unit 200"
        assert rows[0].city == "Boca Raton"
        assert rows[0].zip_code == "33431"

    def test_comma_in_address_reconstructed(self, tmp_path):
        """An unquoted address containing a comma is rejoined; city/state/zip stay correct."""
        text = "2017233783,SSR130,6670 US Highway 129, Suite 1,Live Oak,FL,32060\n"
        rows, failures = CSVAddressIngester().load(self._write_csv(tmp_path, text))
        assert failures == 0
        assert len(rows) == 1
        assert rows[0].address == "6670 US Highway 129, Suite 1"
        assert rows[0].city == "Live Oak"
        assert rows[0].state == "FL"
        assert rows[0].zip_code == "32060"

    def test_bom_stripped(self, tmp_path):
        """A UTF-8 BOM on the first serial does not break numeric detection."""
        text = "\ufeff2012233588,SSR130,1 A St,Town,FL,33000\n"
        rows, failures = CSVAddressIngester().load(self._write_csv(tmp_path, text))
        assert failures == 0
        assert rows[0].serial == "2012233588"

    def test_blank_lines_skipped_silently(self, tmp_path):
        """Trailing blank lines are skipped and do not inflate the failure count."""
        text = "2012233588,SSR130,1 A St,Town,FL,33000\n\n\n"
        rows, failures = CSVAddressIngester().load(self._write_csv(tmp_path, text))
        assert len(rows) == 1
        assert failures == 0


class TestSanitize:
    """CSVAddressIngester.sanitize_address pure transform."""

    def test_collapses_and_strips(self):
        """Newlines become spaces and repeated whitespace collapses."""
        result = CSVAddressIngester.sanitize_address("  5550 N\r\n  Military   Trail \n Unit 200 ")
        assert result == "5550 N Military Trail Unit 200"
