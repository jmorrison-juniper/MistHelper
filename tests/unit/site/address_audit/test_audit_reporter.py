"""Unit tests for AddressAuditReporter (1003-site-address-audit)."""

import csv
import os
import re

from src.site.address_audit.audit_reporter import AddressAuditReporter
from src.site.address_audit.models import AddressRow, AuditResult, MatchedSite


def _result(issue="MISSING_SUITE"):
    """Build an AuditResult for report tests."""
    row = AddressRow(
        serial="2012233588", model="SSR130", address="100 Main St Suite 5", city="Town", state="FL", zip_code="33000"
    )
    site = MatchedSite(
        site_id="s1",
        site_name="Store 181",
        mist_address={"address": "100 Main St", "city": "Town", "state": "FL", "zip": "33000"},
        snmp_location="08095 - 100 Main St Suite 5",
        match_strategy="serial",
    )
    return AuditResult(
        address_row=row,
        matched_site=site,
        issue_type=issue,
        suggested_address="100 Main St Suite 5, Town, FL",
        source="Nominatim",
    )


class TestSave:
    """AddressAuditReporter.save output file."""

    def test_writes_timestamped_csv_with_header(self, tmp_path):
        """save() writes a timestamped CSV with the 7-column header and a data row."""
        out = str(tmp_path / "data")
        path = AddressAuditReporter().save([_result()], output_dir=out)
        assert os.path.isfile(path)
        assert re.search(r"address_audit_\d{8}_\d{6}\.csv$", path)
        with open(path, encoding="utf-8") as handle:
            rows = list(csv.reader(handle))
        assert rows[0] == [
            "Site Name",
            "Current Mist Address",
            "CSV Address",
            "SNMP Location",
            "Suggested Address",
            "Source",
            "Issue Type",
        ]
        assert rows[1][0] == "Store 181"
        assert rows[1][6] == "MISSING_SUITE"

    def test_creates_output_dir(self, tmp_path):
        """save() creates the output directory when it does not exist."""
        out = str(tmp_path / "nested" / "data")
        path = AddressAuditReporter().save([_result()], output_dir=out)
        assert os.path.isfile(path)

    def test_full_values_not_truncated(self, tmp_path):
        """The CSV keeps full (untruncated) suggested-address values."""
        long_result = _result()
        long_result.suggested_address = "Y" * 80
        path = AddressAuditReporter().save([long_result], output_dir=str(tmp_path))
        with open(path, encoding="utf-8") as handle:
            content = handle.read()
        assert "Y" * 80 in content
