"""Offline contracts for compact data previews and their fixed row budget."""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from unittest.mock import Mock

import pytest

from tests.support.data_preview_harness import DataPreviewHarness, PreviewRowBudget, WidePreviewFixture
from web_portal.services.data_browser import DataBrowserService
from web_portal.services.row_sorter import SortSpec


class TestTheWideFixture:
    """Match the reported shape and retain difficult values through the real reader."""

    def test_the_fixture_matches_the_reported_shape(self, tmp_path: Path) -> None:
        """A small fixture would not reproduce the narrow-column failure."""
        fixture = WidePreviewFixture(tmp_path)
        assert len(fixture.columns) == 43
        assert len(fixture.rows) == 112
        assert {len(row) for row in fixture.rows} == {43}
        assert len(fixture.rows[0][1]) == 558
        assert len(fixture.rows[1][1]) == 2019

    def test_csv_keeps_quotes_markup_unicode_and_newlines(self, tmp_path: Path) -> None:
        """The fixture writer and reader must preserve every cell value."""
        fixture = WidePreviewFixture(tmp_path)
        fixture.write()
        with fixture.path.open(encoding="utf-8", newline="") as handle:
            records = list(csv.reader(handle))
        assert records == [fixture.columns, *fixture.rows]
        preview = DataBrowserService(str(tmp_path)).preview_file(fixture.filename, 1, 50, "")
        assert preview["columns"] == fixture.columns
        assert preview["rows"] == fixture.rows[:50]

    @pytest.mark.parametrize(("page", "count", "start"), [(1, 50, 0), (2, 50, 50), (3, 12, 100)])
    def test_real_pagination_keeps_the_reported_contract(
        self, tmp_path: Path, page: int, count: int, start: int
    ) -> None:
        """The repair must not change the original page metadata or values."""
        fixture = WidePreviewFixture(tmp_path)
        fixture.write()
        preview = DataBrowserService(str(tmp_path)).preview_file(fixture.filename, page, 50, "")
        assert preview == {
            "columns": fixture.columns,
            "rows": fixture.rows[start : start + count],
            "total_rows": 112,
            "page": page,
            "per_page": 50,
            "total_pages": 3,
        }

    def test_sort_and_search_keep_exact_values(self, tmp_path: Path) -> None:
        """Sort and search still use the actual CSV service."""
        fixture = WidePreviewFixture(tmp_path)
        fixture.write()
        service = DataBrowserService(str(tmp_path))
        descending = service.preview_file(fixture.filename, 1, 50, "", SortSpec(0, True))
        filtered = service.preview_file(fixture.filename, 1, 50, "Row 112")
        assert descending["rows"] == list(reversed(fixture.rows))[:50]
        assert descending["sorted_by"] == 0
        assert descending["sort_dir"] == "desc"
        assert filtered["rows"] == [fixture.rows[-1]]
        assert filtered["total_rows"] == 1


class TestTheFixedRowBudget:
    """Prove that the guard fails without a browser or an environment dependency."""

    @pytest.mark.parametrize("heights", [None, []], ids=["unreadable", "empty"])
    def test_missing_measurements_fail_with_a_checked_count(self, heights: list[float] | None) -> None:
        """A missing measurement cannot report success."""
        with pytest.raises(AssertionError, match="Checked 0 rows.*unavailable"):
            PreviewRowBudget.check(heights)

    @pytest.mark.parametrize("height", [0, -1, float("nan"), float("inf")], ids=["zero", "negative", "nan", "infinite"])
    def test_invalid_measurements_fail_with_a_checked_count(self, height: float) -> None:
        """Hidden rows and nonfinite bounds cannot prove the layout."""
        with pytest.raises(AssertionError, match="Checked 1 rows.*invalid"):
            PreviewRowBudget.check([height])

    @pytest.mark.parametrize(
        "height", [60.01, 1265.5, 4433], ids=["over-budget", "original-first-row", "original-second-row"]
    )
    def test_tall_rows_fail_the_fixed_budget(self, height: float) -> None:
        """The original failure stays red and the budget stays at 60 pixels."""
        assert PreviewRowBudget.maximum_height == 60
        with pytest.raises(AssertionError, match="Checked 2 rows.*exceeds 60px"):
            PreviewRowBudget.check([41, height])

    @pytest.mark.parametrize("heights", [[41], [41, 53, 60], [60] * 50])
    def test_every_valid_row_contributes_to_the_count(self, heights: list[float]) -> None:
        """The decision measures every supplied row, including the exact boundary."""
        assert PreviewRowBudget.check(heights) == len(heights)


class TestTheScopedStyles:
    """Keep the existing result rules and the shared table rule unchanged."""

    @staticmethod
    def rules(selector: str) -> dict[str, str]:
        """Read scoped declarations without a vendor stylesheet or new parser."""
        path = Path(__file__).resolve().parents[3] / "web_portal" / "static" / "css" / "portal.css"
        text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.DOTALL)
        matched = {}
        for selectors, body in re.findall(r"([^{}]+)\{([^{}]*)\}", text):
            if selector in [part.strip() for part in selectors.split(",")]:
                matched.update(dict(re.findall(r"([\w-]+)\s*:\s*([^;]+);", body)))
        return matched

    def test_preview_uses_the_unchanged_compact_result_values(self) -> None:
        """Both selectors keep the five values that fixed issue #3048."""
        expected = {
            "white-space": "nowrap",
            "overflow": "hidden",
            "text-overflow": "ellipsis",
            "max-width": "18ch",
            "word-break": "normal",
        }
        assert self.rules("#resultsTable td") == expected
        preview = self.rules("#modalPreviewTable td")
        assert {name: preview[name] for name in expected} == expected
        assert self.rules(".portal-table td")["word-break"] == "break-word"

    def test_result_details_keep_their_existing_exceptions(self) -> None:
        """A shared compact rule must not shorten an opened results detail."""
        assert self.rules("#resultsTable tr.result-detail td") == {
            "white-space": "normal",
            "max-width": "none",
            "overflow": "visible",
        }
        assert self.rules("#resultsTable .result-detail-inner") == {
            "position": "sticky",
            "left": "0",
            "max-width": "68rem",
        }


class TestOfflinePreviewFailures:
    """Prove readable failure responses without production data or network calls."""

    def test_http_4xx_names_the_missing_file(self, tmp_path: Path) -> None:
        """The actual preview route keeps its missing-file response."""
        harness = DataPreviewHarness(tmp_path)
        response = harness.app.test_client().get("/api/data/preview/Missing.csv")
        assert response.status_code == 404
        assert response.get_json() == {"error": "File not found"}

    def test_http_5xx_remains_an_error(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """An unreadable service cannot become a successful empty table."""
        harness = DataPreviewHarness(tmp_path)
        harness.app.config["PROPAGATE_EXCEPTIONS"] = False
        monkeypatch.setattr(
            DataBrowserService, "preview_file", Mock(side_effect=PermissionError("Fixture read failed."))
        )
        response = harness.app.test_client().get("/api/data/preview/OrgMarvisActions.csv")
        assert response.status_code == 500
        assert response.content_type.startswith("text/html")

    def test_empty_csv_keeps_an_empty_success_shape(self, tmp_path: Path) -> None:
        """A valid file with no records remains different from a read failure."""
        harness = DataPreviewHarness(tmp_path)
        (tmp_path / "Empty.csv").write_bytes(b"")
        response = harness.app.test_client().get("/api/data/preview/Empty.csv")
        assert response.status_code == 200
        assert response.get_json()["rows"] == []
        assert response.get_json()["total_rows"] == 0

    def test_malformed_json_is_not_a_data_table(self, tmp_path: Path) -> None:
        """The actual data route retains its parse-error status."""
        harness = DataPreviewHarness(tmp_path)
        content = "{invalid JSON"
        with pytest.raises(json.JSONDecodeError, match="Expecting property name"):
            json.loads(content)
        (tmp_path / "Broken.json").write_text(content, encoding="utf-8")
        response = harness.app.test_client().get("/api/data/preview/Broken.json")
        assert response.status_code == 400
        assert response.get_json()["error"].startswith("Failed to read JSON:")
        assert "Expecting property name" in response.get_json()["error"]
