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

    def test_embedded_newline_sanitized(self, tmp_path):
        """An address with an embedded newline is flattened to a single line."""
        text = "2012233588\tSSR130\t5550 N Military Trail\n Unit 200\tBoca Raton\tFL\t33431\n"
        # The embedded newline splits the record; the ingester reads the serial-bearing line.
        rows, _ = CSVAddressIngester().load(_write(tmp_path, text))
        assert rows[0].serial == "2012233588"
        assert "\n" not in rows[0].address

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


class TestSanitize:
    """CSVAddressIngester.sanitize_address pure transform."""

    def test_collapses_and_strips(self):
        """Newlines become spaces and repeated whitespace collapses."""
        result = CSVAddressIngester.sanitize_address("  5550 N\r\n  Military   Trail \n Unit 200 ")
        assert result == "5550 N Military Trail Unit 200"
