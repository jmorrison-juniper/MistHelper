"""Guard the column order the preview table shows.

Issue #3125: the table took its column order from the file, and an exporter
writes the keys alphabetically. The site export therefore opened like this.

```text
address | alarmtemplate_id | aptemplate_id | country_code | ... | name | ...
```

A reader met `300 Alamo Plaza...` with no site name beside it, and had to
scroll sideways to learn which site the row described.

These tests hold three contracts. The table must lead with the column that
names the row. A record with no identity column must keep the order the file
supplies. The column index must still select the same value, because the
browser sends the index of the column a person clicked and the server sorts on
that index.
"""

from __future__ import annotations

import csv
import json

import pytest

from web_portal.services.column_order import IDENTITY_PREFERENCE, ColumnOrder
from web_portal.services.data_browser import DataBrowserService
from web_portal.services.row_sorter import SortSpec

SITE_COLUMNS = ["address", "alarmtemplate_id", "aptemplate_id", "country_code", "id", "name"]


def _write_csv(directory, name, header, rows):
    """Write one CSV file and return its file name."""
    path = directory / name
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)
    return name


class TestColumnOrderPlan:
    """The plan must recognize an identity column and leave other records alone."""

    def test_name_leads_the_site_export(self):
        """The reported column list must put `name` first."""
        plan = ColumnOrder.plan(SITE_COLUMNS)
        assert plan.apply(SITE_COLUMNS)[0] == "name"
        assert plan.positions[0] == SITE_COLUMNS.index("name")

    def test_identity_columns_follow_the_preference_order(self):
        """Several identity columns must lead in the documented order."""
        columns = ["zone", "serial", "mac", "name", "model"]
        plan = ColumnOrder.plan(columns)
        assert plan.apply(columns)[:3] == ["name", "mac", "serial"]

    def test_remaining_columns_keep_their_order(self):
        """A column that is not an identity column must not move relative to its peers."""
        plan = ColumnOrder.plan(SITE_COLUMNS)
        arranged = plan.apply(SITE_COLUMNS)
        assert arranged == ["name", "id", "address", "alarmtemplate_id", "aptemplate_id", "country_code"]

    def test_record_without_an_identity_column_keeps_file_order(self):
        """A record that holds no identity column must produce no plan."""
        assert ColumnOrder.plan(["alpha", "beta", "gamma"]) is None

    def test_record_already_leading_with_name_produces_no_plan(self):
        """A file that already leads correctly must not pay for a rewrite."""
        assert ColumnOrder.plan(["name", "address", "country_code"]) is None

    def test_partial_name_never_matches(self):
        """`alarmtemplate_id` must not count as the `id` column."""
        assert ColumnOrder.plan(["address", "alarmtemplate_id", "aptemplate_id"]) is None

    def test_header_case_does_not_hide_the_identity_column(self):
        """A header written as `Name` must still lead the table."""
        columns = ["Address", "Name"]
        plan = ColumnOrder.plan(columns)
        assert plan.apply(columns)[0] == "Name"

    def test_short_row_yields_an_empty_cell(self):
        """A row with fewer cells than columns must not raise."""
        plan = ColumnOrder.plan(SITE_COLUMNS)
        assert plan.apply(["only-one-cell"]) == ["", "", "only-one-cell", "", "", ""]

    def test_preference_list_states_the_documented_ranking(self):
        """The ranking must match the order issue #3125 agreed."""
        assert IDENTITY_PREFERENCE == ("name", "hostname", "site_name", "mac", "serial", "id")


class TestPreviewLeadsWithTheIdentityColumn:
    """The preview endpoint must show the repaired order."""

    def test_unsorted_preview_leads_with_name(self, tmp_path):
        """The first page of an unsorted preview must name each row first."""
        rows = [["300 Alamo Plaza", "a1", "a2", "US", "id-1", "AlamoSanAntonio"]]
        name = _write_csv(tmp_path, "Sites.csv", SITE_COLUMNS, rows)
        result = DataBrowserService(str(tmp_path)).preview_file(name, page=1, per_page=25, search="")
        assert result["columns"][0] == "name"
        assert result["rows"][0][0] == "AlamoSanAntonio"

    def test_filtered_preview_leads_with_name(self, tmp_path):
        """A filtered preview must use the repaired order too."""
        rows = [
            ["300 Alamo Plaza", "a1", "a2", "US", "id-1", "AlamoSanAntonio"],
            ["1 Glacier Bay", "b1", "b2", "US", "id-2", "GlacierBay"],
        ]
        name = _write_csv(tmp_path, "Sites.csv", SITE_COLUMNS, rows)
        result = DataBrowserService(str(tmp_path)).preview_file(name, page=1, per_page=25, search="Glacier")
        assert result["columns"][0] == "name"
        assert result["rows"][0][0] == "GlacierBay"

    def test_row_values_still_match_their_headers(self, tmp_path):
        """Every cell must stay under the heading that describes it."""
        rows = [["300 Alamo Plaza", "a1", "a2", "US", "id-1", "AlamoSanAntonio"]]
        name = _write_csv(tmp_path, "Sites.csv", SITE_COLUMNS, rows)
        result = DataBrowserService(str(tmp_path)).preview_file(name, page=1, per_page=25, search="")
        paired = dict(zip(result["columns"], result["rows"][0], strict=True))
        assert paired["name"] == "AlamoSanAntonio"
        assert paired["address"] == "300 Alamo Plaza"
        assert paired["country_code"] == "US"
        assert paired["id"] == "id-1"


class TestSortIndexStaysConsistent:
    """The browser sends a display index, so the server must sort that column."""

    @pytest.mark.parametrize("descending", [False, True])
    def test_sorting_the_first_column_sorts_the_name(self, tmp_path, descending):
        """Column 0 is `name` on screen, so a sort on 0 must order the names."""
        rows = [
            ["300 Alamo Plaza", "a1", "a2", "US", "id-1", "Charlie"],
            ["1 Glacier Bay", "b1", "b2", "US", "id-2", "Alpha"],
            ["9 Bryce Road", "c1", "c2", "CA", "id-3", "Bravo"],
        ]
        name = _write_csv(tmp_path, "Sites.csv", SITE_COLUMNS, rows)
        spec = SortSpec(column=0, descending=descending)
        result = DataBrowserService(str(tmp_path)).preview_file(name, page=1, per_page=25, search="", sort=spec)
        names = [row[0] for row in result["rows"]]
        assert result["columns"][0] == "name"
        assert names == (["Charlie", "Bravo", "Alpha"] if descending else ["Alpha", "Bravo", "Charlie"])

    def test_sorting_a_moved_column_orders_that_column(self, tmp_path):
        """A column the plan moved must still sort on its own values."""
        rows = [
            ["300 Alamo Plaza", "a1", "a2", "US", "id-1", "Charlie"],
            ["1 Glacier Bay", "b1", "b2", "CA", "id-2", "Alpha"],
            ["9 Bryce Road", "c1", "c2", "BZ", "id-3", "Bravo"],
        ]
        name = _write_csv(tmp_path, "Sites.csv", SITE_COLUMNS, rows)
        service = DataBrowserService(str(tmp_path))
        unsorted = service.preview_file(name, page=1, per_page=25, search="")
        country_index = unsorted["columns"].index("country_code")
        spec = SortSpec(column=country_index, descending=False)
        result = service.preview_file(name, page=1, per_page=25, search="", sort=spec)
        assert [row[country_index] for row in result["rows"]] == ["BZ", "CA", "US"]


class TestDamagedFilesStillAnswer:
    """A reorder must not turn a damaged file into a crash."""

    def test_empty_csv_body_yields_no_row(self, tmp_path):
        """An empty file holds no header, so the preview must answer with no row."""
        (tmp_path / "Sites.csv").write_bytes(b"")  # An interrupted export leaves an empty body.
        result = DataBrowserService(str(tmp_path)).preview_file("Sites.csv", page=1, per_page=25, search="")
        assert result.get("error") is None  # An empty export is an answer, not a fault.
        assert result["rows"] == []
        assert result["total_rows"] == 0

    def test_header_only_csv_yields_no_row(self, tmp_path):
        """A header with no data row must still lead with the identity column."""
        (tmp_path / "Sites.csv").write_text(",".join(SITE_COLUMNS) + "\n", encoding="utf-8")
        result = DataBrowserService(str(tmp_path)).preview_file("Sites.csv", page=1, per_page=25, search="")
        assert result["columns"][0] == "name"
        assert result["rows"] == []

    def test_malformed_json_reports_an_error(self, tmp_path):
        """A truncated JSON export must convert a decode failure into a reason."""
        path = tmp_path / "Sites.json"
        path.write_text('{"name": "Alamo"', encoding="utf-8")  # The writer stopped mid-object.
        with pytest.raises(json.JSONDecodeError):  # Prove the body really fails to parse.
            json.loads(path.read_text(encoding="utf-8"))
        result = DataBrowserService(str(tmp_path)).preview_file("Sites.json", page=1, per_page=25, search="")
        assert "error" in result  # The reader must learn that the file is damaged.
        assert result.get("rows", []) == []  # A damaged file yields no row to display.

    def test_empty_json_body_reports_an_error(self, tmp_path):
        """An empty JSON body carries no document, so the preview must say so."""
        (tmp_path / "Sites.json").write_bytes(b"")  # An interrupted export leaves an empty body.
        result = DataBrowserService(str(tmp_path)).preview_file("Sites.json", page=1, per_page=25, search="")
        assert "error" in result  # A missing document is a reason the reader needs.

    def test_ragged_csv_row_keeps_every_header_aligned(self, tmp_path):
        """A row with missing cells must pad instead of shifting a value under the wrong heading."""
        path = tmp_path / "Sites.csv"
        path.write_text(",".join(SITE_COLUMNS) + "\n300 Alamo Plaza,a1\n", encoding="utf-8")
        result = DataBrowserService(str(tmp_path)).preview_file("Sites.csv", page=1, per_page=25, search="")
        paired = dict(zip(result["columns"], result["rows"][0], strict=True))
        assert paired["address"] == "300 Alamo Plaza"  # The present cell stays under its own heading.
        assert paired["name"] == ""  # The absent cell reads empty rather than borrowing a neighbour.
