"""Tests for the preview row order (issue #3047) and its route (issue #3048).

Why:
    The preview table let a user click a column heading, and the click changed
    only the arrow. The browser held the sort state and never sent it, and the
    route never read one.

    Warning: a table that looks sorted and is not is worse than a table with no
    sort at all. An engineer who orders a rogue DHCP result by the last time
    seen believes the newest finding sits at the top, and then works the wrong
    row first.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from web_portal.services.data_browser import DataBrowserService
from web_portal.services.row_sorter import RowSorter, SortSpec

COLUMNS = ["name", "count", "note"]
ROWS = [
    ["beta", "9", "second"],
    ["Alpha", "10", "first"],
    ["delta", "", "fourth"],
    ["charlie", "2", "third"],
]


@pytest.fixture
def csv_file(tmp_path: Path) -> Path:
    """Write one small CSV file and return its path."""
    target = tmp_path / "rows.csv"
    with open(target, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS)
        writer.writerows(ROWS)
    return target


def names(result: dict) -> list[str]:
    """Return the name column of a preview result."""
    return [row[0] for row in result.get("rows", [])]


class TestTheSortKeyOrdersByValue:
    """Prove the rules that a text compare alone would break."""

    def test_a_number_orders_by_value(self) -> None:
        """A text compare puts 10 before 9, which reads as wrong to every operator."""
        ordered = RowSorter().sort(list(ROWS), SortSpec(column=1, descending=False))
        assert [row[1] for row in ordered][:3] == ["2", "9", "10"]

    def test_an_empty_cell_sorts_last(self) -> None:
        """A missing value must never hide a real one at the top of the table."""
        ordered = RowSorter().sort(list(ROWS), SortSpec(column=1, descending=False))
        assert ordered[-1][1] == ""

    def test_text_ignores_letter_case(self) -> None:
        """A name that starts with a capital belongs beside its lower-case peers."""
        ordered = RowSorter().sort(list(ROWS), SortSpec(column=0, descending=False))
        assert [row[0] for row in ordered] == ["Alpha", "beta", "charlie", "delta"]

    def test_the_direction_reverses_the_order(self) -> None:
        """A second click on one heading must reverse the rows."""
        ascending = RowSorter().sort(list(ROWS), SortSpec(column=0, descending=False))
        descending = RowSorter().sort(list(ROWS), SortSpec(column=0, descending=True))
        assert [r[0] for r in descending] == list(reversed([r[0] for r in ascending]))

    def test_a_short_row_does_not_raise(self) -> None:
        """A ragged file holds a row with fewer cells, and the sort must survive it."""
        ordered = RowSorter().sort([["only"], ["two", "1"]], SortSpec(column=1, descending=False))
        assert len(ordered) == 2


class TestTheSorterBoundsItsMemory:
    """The paginator streams rows, and a sort cannot. The cap protects the worker."""

    def test_the_cap_reports_a_cut_read(self) -> None:
        """A silent partial order repeats the defect this work removed."""
        held, truncated = RowSorter(max_rows=3).collect(iter([[str(n)] for n in range(10)]))
        assert len(held) == 3
        assert truncated is True

    def test_a_short_file_reports_no_cut(self) -> None:
        """A file inside the cap must not carry a warning that misleads."""
        held, truncated = RowSorter(max_rows=10).collect(iter([[str(n)] for n in range(4)]))
        assert len(held) == 4
        assert truncated is False

    def test_the_cap_is_visible_to_the_caller(self) -> None:
        """The service reports the covered span, so the operator can trust the order."""
        assert RowSorter(max_rows=25).max_rows == 25

    def test_a_cap_below_one_is_raised(self) -> None:
        """A cap of zero would drop every row and show an empty table."""
        assert RowSorter(max_rows=0).max_rows == 1


class TestTheSortRequestRefusesBadInput:
    """A crafted index must never reach the row reader."""

    @pytest.mark.parametrize("value", ["9", "-1", "abc", None, ""])
    def test_an_unusable_column_yields_no_sort(self, value) -> None:
        """An out-of-range or unreadable column must leave the file order."""
        assert SortSpec.from_request(value, "asc", column_count=3) is None

    def test_a_valid_column_yields_a_request(self) -> None:
        """A good request must survive, or the feature would never order anything."""
        spec = SortSpec.from_request("2", "desc", column_count=3)
        assert spec == SortSpec(column=2, descending=True)

    def test_an_unknown_direction_reads_as_ascending(self) -> None:
        """A missing direction must pick the safer default, not raise."""
        spec = SortSpec.from_request("0", "sideways", column_count=3)
        assert spec is not None and spec.descending is False


class TestTheServiceOrdersAWholeFile:
    """Prove the order covers every row, not only the page the reader sees."""

    def test_no_sort_keeps_the_file_order(self, csv_file: Path) -> None:
        """The streaming path must stay the default, because it holds no whole file."""
        service = DataBrowserService(str(csv_file.parent))
        result = service.preview_file(csv_file.name, 1, 10, "")
        assert names(result) == ["beta", "Alpha", "delta", "charlie"]

    def test_a_sort_orders_every_row(self, csv_file: Path) -> None:
        """Issue #3047. This is the assertion the defect failed."""
        service = DataBrowserService(str(csv_file.parent))
        result = service.preview_file(csv_file.name, 1, 10, "", SortSpec(0, False))
        assert names(result) == ["Alpha", "beta", "charlie", "delta"]

    def test_the_order_spans_the_pages(self, csv_file: Path) -> None:
        """A sort that ordered one page only would still mislead the reader."""
        service = DataBrowserService(str(csv_file.parent))
        first = service.preview_file(csv_file.name, 1, 2, "", SortSpec(0, False))
        second = service.preview_file(csv_file.name, 2, 2, "", SortSpec(0, False))
        assert names(first) == ["Alpha", "beta"]
        assert names(second) == ["charlie", "delta"]

    def test_the_filter_and_the_order_work_together(self, csv_file: Path) -> None:
        """An engineer narrows the rows and then orders what remains."""
        service = DataBrowserService(str(csv_file.parent))
        result = service.preview_file(csv_file.name, 1, 10, "a", SortSpec(0, True))
        assert result["total_rows"] == len(names(result))
        assert names(result) == sorted(names(result), key=str.casefold, reverse=True)

    def test_the_result_states_the_column_it_used(self, csv_file: Path) -> None:
        """The browser confirms the server honored the click, and does not assume it."""
        service = DataBrowserService(str(csv_file.parent))
        result = service.preview_file(csv_file.name, 1, 10, "", SortSpec(1, True))
        assert result["sorted_by"] == 1
        assert result["sort_dir"] == "desc"

    def test_the_column_names_are_readable(self, csv_file: Path) -> None:
        """The route reads the column count to refuse a crafted index."""
        service = DataBrowserService(str(csv_file.parent))
        assert service.read_column_names(csv_file.name) == COLUMNS

    def test_a_missing_file_yields_no_column(self, tmp_path: Path) -> None:
        """A lost file must answer with no column, not raise into the route."""
        assert DataBrowserService(str(tmp_path)).read_column_names("absent.csv") == []


class TestTheRouteCarriesTheSort:
    """Prove the whole path, from the query argument to the ordered rows."""

    @pytest.fixture
    def portal(self, tmp_path: Path):
        """Build a portal client whose data directory holds the test file."""
        with open(tmp_path / "rows.csv", "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(COLUMNS)
            writer.writerows(ROWS)
        from web_portal.app import WebPortalApp
        from web_portal.menu_registry import build_static_menu_actions

        app = WebPortalApp.create_app(apisession=None, menu_actions=build_static_menu_actions(), org_id="test-org")
        app.config["TESTING"] = True
        app.config["DATA_DIR"] = str(tmp_path)
        yield app.test_client()
        WebPortalApp.shutdown_app(app)

    def test_the_route_orders_when_asked(self, portal) -> None:
        """Issue #3047. The argument must reach the service and change the rows."""
        response = portal.get("/api/data/preview/rows.csv?page=1&per_page=10&sort_column=0&sort_dir=asc")
        assert response.status_code == 200
        assert names(response.get_json()) == ["Alpha", "beta", "charlie", "delta"]

    def test_the_route_reverses_when_asked(self, portal) -> None:
        """A second click sends the other direction, and the rows must follow."""
        response = portal.get("/api/data/preview/rows.csv?page=1&per_page=10&sort_column=0&sort_dir=desc")
        assert names(response.get_json()) == ["delta", "charlie", "beta", "Alpha"]

    def test_the_route_keeps_the_file_order_without_an_argument(self, portal) -> None:
        """Most calls send no order, and those must keep the cheap streaming path."""
        response = portal.get("/api/data/preview/rows.csv?page=1&per_page=10")
        assert names(response.get_json()) == ["beta", "Alpha", "delta", "charlie"]
        assert "sorted_by" not in response.get_json()

    def test_the_route_ignores_a_column_the_file_lacks(self, portal) -> None:
        """A crafted index must answer with a page, not with a server fault."""
        response = portal.get("/api/data/preview/rows.csv?page=1&per_page=10&sort_column=99&sort_dir=asc")
        assert response.status_code == 200
        assert names(response.get_json()) == ["beta", "Alpha", "delta", "charlie"]


class TestADamagedFileNeverRaises:
    """A result file can be empty, truncated, or malformed on disk.

    Warning: a preview that raises leaves the operator with a blank panel and no
    reason. Each case below must answer with a readable result instead.
    """

    def test_an_empty_file_yields_no_row(self, tmp_path: Path) -> None:
        """A run can write a header and then find nothing to add."""
        (tmp_path / "empty.csv").write_text("", encoding="utf-8")
        service = DataBrowserService(str(tmp_path))
        result = service.preview_file("empty.csv", 1, 10, "", SortSpec(0, False))
        assert result.get("rows") == []
        assert "error" not in result

    def test_a_header_only_file_yields_no_row(self, tmp_path: Path) -> None:
        """An empty result still carries its column names."""
        (tmp_path / "header.csv").write_text("name,count\n", encoding="utf-8")
        service = DataBrowserService(str(tmp_path))
        result = service.preview_file("header.csv", 1, 10, "", SortSpec(0, False))
        assert result["columns"] == ["name", "count"]
        assert result["rows"] == []

    def test_a_ragged_file_still_sorts(self, tmp_path: Path) -> None:
        """A row with fewer cells than the header must not end the preview."""
        (tmp_path / "ragged.csv").write_text("name,count\nonly\nfull,2\n", encoding="utf-8")
        service = DataBrowserService(str(tmp_path))
        result = service.preview_file("ragged.csv", 1, 10, "", SortSpec(1, False))
        assert len(result["rows"]) == 2
        assert "error" not in result

    def test_a_malformed_json_file_reports_a_reason(self, tmp_path: Path) -> None:
        """A half-written JSON file must name the fault, not raise."""
        broken = tmp_path / "broken.json"
        broken.write_text('{"rows": [', encoding="utf-8")
        # Prove the file really is malformed first. Without this the assertion
        # below could pass for an unrelated reason, such as a missing file.
        with pytest.raises(json.JSONDecodeError):
            json.loads(broken.read_text(encoding="utf-8"))
        result = DataBrowserService(str(tmp_path)).preview_file("broken.json", 1, 10, "")
        assert "error" in result
        assert "json" in result["error"].lower()

    def test_an_empty_json_file_reports_a_reason(self, tmp_path: Path) -> None:
        """An empty body is not valid JSON, and the reader must say so."""
        (tmp_path / "empty.json").write_bytes(b"")  # An interrupted write leaves exactly this.
        with pytest.raises(json.JSONDecodeError):  # Confirm the body cannot parse at all.
            json.loads("")
        result = DataBrowserService(str(tmp_path)).preview_file("empty.json", 1, 10, "")
        assert "error" in result

    def test_an_empty_csv_body_yields_no_row(self, tmp_path: Path) -> None:
        """A CSV reader must answer an empty body with no row, not with a fault."""
        (tmp_path / "blank.csv").write_bytes(b"")  # The same interrupted write, in the CSV path.
        result = DataBrowserService(str(tmp_path)).preview_file("blank.csv", 1, 10, "", SortSpec(0, False))
        assert result.get("rows") == []
        assert "error" not in result

    def test_an_absent_file_reports_a_reason(self, tmp_path: Path) -> None:
        """A run can report a file that the disk later lost."""
        result = DataBrowserService(str(tmp_path)).preview_file("gone.csv", 1, 10, "", SortSpec(0, False))
        assert result["error"] == "File not found"


class TestEveryAnswerStaysParseableJson:
    """The results table calls ``res.json()`` on every answer of this route.

    Warning: an answer with an empty body, or an answer that holds an HTML error
    page, makes that call raise. The table would then show a parse error instead
    of the reason the request failed, and the operator would learn nothing.
    """

    @pytest.fixture
    def portal(self, tmp_path: Path):
        """Build a portal client over a directory that holds one good file."""
        with open(tmp_path / "rows.csv", "w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(COLUMNS)
            writer.writerows(ROWS)
        from web_portal.app import WebPortalApp
        from web_portal.menu_registry import build_static_menu_actions

        app = WebPortalApp.create_app(apisession=None, menu_actions=build_static_menu_actions(), org_id="test-org")
        app.config["TESTING"] = True
        app.config["DATA_DIR"] = str(tmp_path)
        yield app.test_client()
        WebPortalApp.shutdown_app(app)

    @pytest.mark.parametrize(
        ("query", "reason"),
        [
            ("rows.csv?page=1&per_page=10", "a good request"),
            ("rows.csv?page=1&per_page=10&sort_column=0&sort_dir=asc", "an ordered request"),
            ("rows.csv?sort_column=abc&sort_dir=sideways", "an unreadable order"),
            ("rows.csv?page=-5&per_page=-5", "a negative page"),
            ("absent.csv", "a missing file"),
        ],
    )
    def test_the_body_is_never_empty(self, portal, query: str, reason: str) -> None:
        """An empty body would make the browser raise instead of showing a reason."""
        response = portal.get(f"/api/data/preview/{query}")
        assert response.data != b"", f"The route answered {reason} with an empty body."
        assert response.mimetype == "application/json", f"The route answered {reason} with a non-JSON type."

    @pytest.mark.parametrize(
        "query",
        [
            "rows.csv?page=1&per_page=10",
            "rows.csv?sort_column=99&sort_dir=asc",
            "absent.csv",
            "rows.csv?page=99999&per_page=10",
        ],
    )
    def test_every_body_parses_as_json(self, portal, query: str) -> None:
        """The table calls `.json()` on every answer, including a failure answer."""
        response = portal.get(f"/api/data/preview/{query}")
        try:  # Parse the raw bytes the browser would receive, not a helper view of them.
            parsed = json.loads(response.data.decode("utf-8"))
        except json.JSONDecodeError as error:  # This is the exact browser-side failure.
            pytest.fail(f"The route answered {query} with malformed JSON: {error}")
        assert isinstance(parsed, dict), "The table reads an object, so a list or a scalar would break it."

    def test_a_failure_answer_names_its_reason(self, portal) -> None:
        """A parseable body that holds no reason still leaves the operator guessing."""
        parsed = json.loads(portal.get("/api/data/preview/absent.csv").data.decode("utf-8"))
        assert parsed.get("error"), "The failure answer holds no reason for the operator to read."
