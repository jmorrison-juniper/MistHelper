"""Regression tests for streamed data browser file previews."""

from __future__ import annotations

import json

from web_portal.services.data_browser import DataBrowserService


def test_csv_preview_keeps_metadata_when_requested_page_is_too_high(tmp_path) -> None:
    """A high page request returns the last valid CSV page."""
    csv_path = tmp_path / "sites.csv"  # Use an allowed name so the path guard accepts the fixture.
    csv_path.write_text("id,name\n1,Alpha\n2,Beta\n3,Gamma\n", encoding="utf-8")  # Build three data rows.
    service = DataBrowserService(str(tmp_path))  # Scope the service to the fixture directory.

    result = service.preview_file("sites.csv", 99, 2, "")  # Ask past the end to exercise late page clamping.

    assert result == {  # The full response shape must stay stable.
        "columns": ["id", "name"],
        "rows": [["3", "Gamma"]],
        "total_rows": 3,
        "page": 2,
        "per_page": 2,
        "total_pages": 2,
    }


def test_csv_search_preview_keeps_last_page_when_request_is_too_high(tmp_path) -> None:
    """A high filtered CSV page request returns the last valid page."""
    csv_path = tmp_path / "sites.csv"  # Use an allowed name so the path guard accepts the fixture.
    csv_path.write_text("id,name\n1,Alpha\n2,Beta\n3,Gamma\n", encoding="utf-8")  # Build three data rows.
    service = DataBrowserService(str(tmp_path))  # Scope the service to the fixture directory.

    result = service.preview_file("sites.csv", 99, 2, "a")  # Ask past the end with a case-insensitive search.

    assert result == {  # The filtered high page response must match the old paginator.
        "columns": ["id", "name"],
        "rows": [["3", "Gamma"]],
        "total_rows": 3,
        "page": 2,
        "per_page": 2,
        "total_pages": 2,
    }


def test_log_preview_filters_case_insensitive_substrings(tmp_path) -> None:
    """A log search matches any cell with a case-insensitive substring."""
    log_path = tmp_path / "events.log"  # Use an allowed name so the path guard accepts the fixture.
    log_path.write_text("first line\nWarning Line\nlast line", encoding="utf-8")  # Omit the trailing newline.
    service = DataBrowserService(str(tmp_path))  # Scope the service to the fixture directory.

    result = service.preview_file("events.log", 1, 10, "warning")  # Use a lower-case search term.

    assert result["rows"] == [["2", "Warning Line"]]  # The line number and text must match the old format.
    assert result["total_rows"] == 1  # The count must include every matching line.
    assert result["total_pages"] == 1  # One result produces one page.


def test_json_lines_single_item_keeps_key_value_fallback(tmp_path) -> None:
    """A single JSON Lines item returns the item itself."""
    json_path = tmp_path / "single.json"  # The JSON preview accepts the .json extension.
    json_path.write_text('{"alpha": 1, "beta": "Two"}\n', encoding="utf-8")  # Write valid JSON Lines.
    service = DataBrowserService(str(tmp_path))  # Scope the service to the fixture directory.

    result = service.preview_file("single.json", 1, 25, "")  # Preview the single JSON Lines item.

    assert result["columns"] == ["Key", "Value"]  # A single object must use the object preview format.
    assert result["rows"] == [["alpha", "1"], ["beta", "Two"]]  # Dict insertion order must stay stable.


def test_json_lines_detection_reuses_the_first_parsed_item(tmp_path, monkeypatch) -> None:
    """A JSON Lines preview parses each item one time."""
    import json

    json_path = tmp_path / "items.json"  # The JSON preview accepts the .json extension.
    json_path.write_text('{"a": 1}\n{"a": 2}\n', encoding="utf-8")  # Use two records to select JSON Lines.
    loads_calls = []  # Count decoder calls so the test guards the single-pass path.
    original_loads = json.loads  # Keep the real decoder so behavior stays unchanged.

    def counting_loads(content):
        loads_calls.append(content)  # Record each parsed line for the assertion below.
        return original_loads(content)  # Decode the item with the standard JSON decoder.

    monkeypatch.setattr(json, "loads", counting_loads)  # Patch the module that the service imports.
    service = DataBrowserService(str(tmp_path))  # Scope the service to the fixture directory.

    result = service.preview_file("items.json", 1, 25, "")  # Preview the JSON Lines file.

    assert result["rows"] == [["1"], ["2"]]  # The response must stay unchanged.
    assert len(loads_calls) == 2  # The first JSON Lines item must not be parsed twice.


def test_json_list_column_order_and_filtering_stay_stable(tmp_path) -> None:
    """A JSON object list keeps first-seen columns and filtered row counts."""
    json_path = tmp_path / "items.json"  # The JSON preview accepts the .json extension.
    payload = [{"b": 2, "a": "Alpha"}, {"c": 3, "a": "Beta"}]  # Add a late column to test discovery order.
    json_path.write_text(json.dumps(payload), encoding="utf-8")  # Use standard JSON to test that path.
    service = DataBrowserService(str(tmp_path))  # Scope the service to the fixture directory.

    result = service.preview_file("items.json", 1, 25, "eta")  # Match the second row by substring.

    assert result["columns"] == ["b", "a", "c"]  # Column order must follow first discovery.
    assert result["rows"] == [["", "Beta", "3"]]  # Missing keys must still become empty strings.
    assert result["total_rows"] == 1  # The count must include all matching rows.
