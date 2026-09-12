"""Unit tests for business-authoritative CSV ingestion and matching."""

from pathlib import Path

from src.site.address_audit.business_authority_ingester import BusinessAuthorityIngester
from src.site.address_audit.models import AddressRow, MatchedSite


def _write_csv(path: Path, body: str) -> None:
    """Write helper CSV content to a temporary file path."""
    path.write_text(body, encoding="utf-8", newline="")  # Keep deterministic UTF-8 test fixtures.


class TestBusinessAuthorityIngester:
    """Loading, indexing, and unique-match lookup behavior."""

    def test_load_merges_space_column(self, tmp_path):
        """Address + Space # become one street line when Space # is present."""
        csv_path = tmp_path / "T-Builder.csv"
        _write_csv(
            csv_path,
            "Site ID,SAP,Name,Address,Space #,City,State,Zip\n" "1,100,Store A,100 Main St,Suite 9,Town,FL,33000\n",
        )
        ingester = BusinessAuthorityIngester()
        rows = ingester.load(str(csv_path))
        assert len(rows) == 1
        assert rows[0].address == "100 Main St Suite 9"

    def test_match_by_full_address_unique(self, tmp_path):
        """A unique full-key hit returns an authoritative address dict."""
        csv_path = tmp_path / "T-Builder.csv"
        _write_csv(
            csv_path,
            "Site ID,SAP,Name,Address,Space #,City,State,Zip\n" "1,100,Store A,100 Main St,Suite 9,Town,FL,33000\n",
        )
        ingester = BusinessAuthorityIngester()
        rows = ingester.load(str(csv_path))
        index = ingester.build_index(rows)
        row = AddressRow(
            serial="1", model="SSR130", address="100 Main St Suite 9", city="Town", state="FL", zip_code="33000"
        )
        site = MatchedSite(
            site_id="s1", site_name="IAS0001", mist_address={"address": "100 Main St"}, match_strategy="serial"
        )
        matched = ingester.match(row, site, index)
        assert matched.get("address") == "100 Main St Suite 9"

    def test_match_ambiguous_returns_empty(self, tmp_path):
        """Two authority rows with the same key are treated as ambiguous (no auto-bind)."""
        csv_path = tmp_path / "T-Builder.csv"
        _write_csv(
            csv_path,
            "Site ID,SAP,Name,Address,Space #,City,State,Zip\n"
            "1,100,Store A,100 Main St,Suite 9,Town,FL,33000\n"
            "2,101,Store B,100 Main St,Suite 9,Town,FL,33000\n",
        )
        ingester = BusinessAuthorityIngester()
        rows = ingester.load(str(csv_path))
        index = ingester.build_index(rows)
        row = AddressRow(
            serial="1", model="SSR130", address="100 Main St Suite 9", city="Town", state="FL", zip_code="33000"
        )
        site = MatchedSite(
            site_id="s1", site_name="IAS0001", mist_address={"address": "100 Main St"}, match_strategy="serial"
        )
        matched = ingester.match(row, site, index)
        assert matched == {}
