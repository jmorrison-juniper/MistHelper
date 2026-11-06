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
import sqlite3  # Build a real local database without an external service.
from collections.abc import Iterator  # Type the isolated portal fixture without a shared application.
from contextlib import closing  # Release SQLite handles before temporary-directory cleanup.
from pathlib import Path
from urllib.parse import quote  # Match the browser's encoded path segment for nested files.

import pytest
from flask.testing import FlaskClient  # Keep route tests on the real Flask request boundary.

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


class TestNestedResultPreviews:  # Keep issue #4036 fixtures separate from the sort fixtures.
    """Verify file selection through real requests without Mist credentials."""

    @pytest.fixture
    def portal(self, tmp_path: Path) -> Iterator[FlaskClient]:  # Give each case its own data directory.
        """Create an isolated portal and release its workers after each test."""
        from web_portal.app import WebPortalApp  # Use the production routes without a live server.
        from web_portal.menu_registry import build_static_menu_actions  # Avoid Mist menu discovery.

        app = WebPortalApp.create_app(  # Disable live API access.
            apisession=None, menu_actions=build_static_menu_actions(), org_id="test-org"
        )
        app.config.update(TESTING=True, DATA_DIR=str(tmp_path))  # Restrict requests to synthetic files.
        try:  # Always release workers, including after a failed assertion.
            yield app.test_client()  # Exercise Flask route selection rather than a service mock.
        finally:  # A failed regression must not leave application workers active.
            WebPortalApp.shutdown_app(app)  # Release only this fixture's application.

    @pytest.mark.parametrize("filename", ["allowlist.json", "oid_assignments.json"])
    @pytest.mark.parametrize("directory", ["", "mib_generator", "exports/mib_generator", "exports/results.db"])
    def test_json_preview_and_download(  # Cover both reported files at three depths.
        self, portal: FlaskClient, tmp_path: Path, filename: str, directory: str
    ) -> None:
        """Keep each file's contents, row order, pagination, and download bytes."""
        target = tmp_path / directory / filename  # Build a portable fixture path.
        content = json.dumps({"result": filename, "scope": "synthetic"}).encode("utf-8")  # Identify each file.
        portal.application.logger.info("Writing a synthetic JSON result.")  # Trace fixture creation.
        target.parent.mkdir(parents=True, exist_ok=True)  # Create only the temporary parent directories.
        target.write_bytes(content)  # Preserve exact bytes for the download comparison.
        portal.application.logger.debug("Wrote %d synthetic bytes.", len(content))  # Report size, not contents.
        relative_path = target.relative_to(tmp_path).as_posix()  # URLs use forward slashes on every platform.
        encoded_path = quote(relative_path, safe="")  # Match encodeURIComponent used by the Results panel.
        portal.application.logger.info("Requesting synthetic download and preview responses.")  # Trace requests.
        with portal.get(f"/api/data/download/{encoded_path}") as download:  # Close the file response after use.
            assert download.status_code == 200  # Prove the file exists before testing the failed preview.
            assert download.data == content  # Downloads must retain the exact source bytes.
        first = portal.get(f"/api/data/preview/{encoded_path}?page=1&per_page=1")  # Reproduce the browser request.
        second = portal.get(f"/api/data/preview/{encoded_path}?page=2&per_page=1")  # Preserve pagination.
        portal.application.logger.debug(  # Record actual outcomes.
            "Preview statuses: %s, %s.", first.status_code, second.status_code
        )
        assert first.status_code == second.status_code == 200  # A nested file must not return a false 404.
        assert first.get_json() == {  # Preserve the existing object representation.
            "columns": ["Key", "Value"],
            "rows": [["result", filename]],
            "total_rows": 2,
            "page": 1,
            "per_page": 1,
            "total_pages": 2,
        }
        assert second.get_json() == {  # Preserve the second row and metadata.
            "columns": ["Key", "Value"],
            "rows": [["scope", "synthetic"]],
            "total_rows": 2,
            "page": 2,
            "per_page": 1,
            "total_pages": 2,
        }
        assert target.read_bytes() == content  # Neither preview nor download may change the source.

    @pytest.mark.parametrize(
        ("filename", "content", "expected_status", "expected_error"),
        [
            ("missing.json", None, 404, "File not found"),
            ("malformed.json", "{not valid JSON", 400, "Failed to read JSON:"),
        ],
    )
    def test_nested_json_errors_preserve_the_file_cause(
        self,
        portal: FlaskClient,
        tmp_path: Path,
        filename: str,
        content: str | None,
        expected_status: int,
        expected_error: str,
    ) -> None:
        """A missing file and invalid JSON must not look like the same route failure."""
        target = tmp_path / "mib_generator" / filename  # Keep both error fixtures below one output directory.
        target.parent.mkdir()  # Create only the synthetic parent directory.
        if content is not None:  # The absent-file case must remain absent.
            portal.application.logger.info("Writing a malformed synthetic JSON result.")  # Trace fixture creation.
            target.write_text(content, encoding="utf-8")  # Cause the parser to report invalid JSON.
            portal.application.logger.debug("Wrote the malformed synthetic JSON result.")  # Do not log its contents.
        encoded_path = quote(f"mib_generator/{filename}", safe="")  # Match the browser's encoded path segment.
        response = portal.get(f"/api/data/preview/{encoded_path}")  # Exercise the nested route matcher.
        portal.application.logger.debug(  # Report the route result without the fixture contents.
            "Nested JSON error response status: %s.", response.status_code
        )
        assert response.status_code == expected_status  # Keep missing and malformed outcomes distinct.
        assert response.get_json()["error"].startswith(expected_error)  # Preserve the useful failure reason.
        assert str(tmp_path) not in response.get_data(as_text=True)  # Never expose an internal absolute path.

    @pytest.fixture(params=["db", "sqlite", "DB", "SQLITE"])
    def sqlite_result(  # Cover both supported extensions without case dependence.
        self, portal: FlaskClient, tmp_path: Path, request: pytest.FixtureRequest
    ) -> Iterator[str]:
        """Create a nested SQLite result and verify that preview leaves it unchanged."""
        target = tmp_path / "exports" / f"results.{request.param}"  # Exercise a database below the output root.
        portal.application.logger.info("Writing a synthetic SQLite result.")  # Trace fixture creation only.
        target.parent.mkdir()  # Keep the database inside this test's output boundary.
        with closing(sqlite3.connect(target)) as connection:  # Release the real SQLite connection after creation.
            connection.execute("CREATE TABLE devices (name TEXT, count INTEGER)")  # Use a fixed test schema.
            connection.executemany(  # Give pagination and search distinct rows.
                "INSERT INTO devices VALUES (?, ?)", [("beta", 9), ("Alpha", 10), ("delta", 2)]
            )
            connection.commit()  # Make fixture rows visible to the read-only preview connection.
        source_bytes = target.read_bytes()  # Detect any preview write to the source database.
        portal.application.logger.debug("Wrote %d synthetic SQLite bytes.", len(source_bytes))  # Record only the size.
        yield target.relative_to(tmp_path).as_posix()  # Pass a URL path, not an absolute filesystem path.
        assert target.read_bytes() == source_bytes  # Preview must not modify the SQLite result.

    @pytest.mark.parametrize(
        ("selection", "expected"),
        [
            (
                "devices?page=1&per_page=2",
                {
                    "columns": ["name", "count"],
                    "rows": [["beta", 9], ["Alpha", 10]],
                    "total_rows": 3,
                    "page": 1,
                    "per_page": 2,
                    "total_pages": 2,
                },
            ),
            (
                "devices?page=2&per_page=2",
                {
                    "columns": ["name", "count"],
                    "rows": [["delta", 2]],
                    "total_rows": 3,
                    "page": 2,
                    "per_page": 2,
                    "total_pages": 2,
                },
            ),
            (
                "devices?search=ALPHA",
                {
                    "columns": ["name", "count"],
                    "rows": [["Alpha", 10]],
                    "total_rows": 1,
                    "page": 1,
                    "per_page": 50,
                    "total_pages": 1,
                },
            ),
            ("missing", {"error": "Table not found"}),
        ],
    )
    def test_sqlite_table_selection(  # Compare exact table responses at the route boundary.
        self, portal: FlaskClient, sqlite_result: str, selection: str, expected: dict
    ) -> None:
        """Preserve nested database listing, table rows, search, and missing-table errors."""
        portal.application.logger.info("Requesting synthetic SQLite previews.")  # Trace local requests.
        listing = portal.get(f"/api/data/preview/{sqlite_result}")  # A database path alone must still list its tables.
        response = portal.get(f"/api/data/preview/{sqlite_result}/{selection}")  # Select explicit table rows.
        portal.application.logger.debug("SQLite preview status: %s.", response.status_code)  # Report the actual result.
        assert listing.status_code == 200  # Nested databases must remain browsable.
        assert listing.get_json() == {  # Preserve table metadata.
            "tables": [{"table_name": "devices", "row_count": 3, "column_names": ["name", "count"]}]
        }
        assert response.status_code == (404 if "error" in expected else 200)  # Preserve missing-table denial status.
        assert response.get_json() == expected  # Verify exact rows, order, pagination, and failure reason.

    @pytest.mark.parametrize("endpoint", ["preview", "download"])
    @pytest.mark.parametrize("attack", ["traversal", "encoded", "absolute", "outside-link"])
    def test_outside_paths_remain_denied(  # Check both read routes against the same boundary.
        self, portal: FlaskClient, tmp_path: Path, endpoint: str, attack: str
    ) -> None:
        """Deny outside files without exposing their synthetic contents."""
        outside = tmp_path.with_suffix(".json")  # Give each case its own file outside the configured output root.
        portal.application.logger.info("Writing a synthetic outside-boundary fixture.")  # Record the test action.
        outside.write_text('{"scope": "outside-marker-4036"}', encoding="utf-8")  # Detect accidental content exposure.
        portal.application.logger.debug("Wrote the outside-boundary fixture.")  # Do not log its contents.
        if attack == "outside-link":  # Create a link only for the link-denial case.
            try:  # Windows accounts can lack link-creation permission.
                (tmp_path / "link.json").symlink_to(outside)  # Keep the link inside and its target outside.
            except (OSError, NotImplementedError) as error:  # Report an unavailable platform capability.
                pytest.skip(f"Cannot create the synthetic symbolic link: {error}")  # Do not claim a link test passed.
        paths = {  # Preserve each distinct attack spelling.
            "traversal": f"../{outside.name}",
            "encoded": f"%2e%2e%2f{outside.name}",
            "absolute": outside.as_posix(),
            "outside-link": "link.json",
        }
        portal.application.logger.info("Requesting an outside-boundary path.")  # Trace the denial test.
        with portal.get(  # Follow only local slash normalization.
            f"/api/data/{endpoint}/{paths[attack]}", follow_redirects=True
        ) as response:
            portal.application.logger.debug(  # Record the real denial.
                "Outside-boundary response status: %s.", response.status_code
            )
            assert response.status_code == 404  # No outside file may become reachable through either route.
            assert response.get_json() == {"error": "File not found"}  # Keep the existing nondisclosing denial body.
            assert b"outside-marker-4036" not in response.data  # A denial must expose none of the file contents.


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
