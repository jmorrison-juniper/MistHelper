"""Tests for WanClientEventsExporter, the menu-wired WAN client events export.

Why:
    The exporter held four risk areas with no test. The top-level guard keeps a
    failed fetch from crashing the menu loop. The site-name lookup opens a file
    and must fall back when that file is corrupt or absent. The fetch must
    normalize a ``None`` page into an empty list. The no-data path writes a real
    sentinel file. This module covers all four. Every Mist call is mocked, so no
    test reaches the live cloud.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.export.wan_client_events_exporter import (
    _OUTPUT_CSV,
    _PLACEHOLDER_HEADER,
    _PLACEHOLDER_MESSAGE,
    _SITE_LIST_CSV,
    _UNKNOWN_SITE,
    WanClientEventsExporter,
    _SiteStamp,
)


def _build_exporter() -> WanClientEventsExporter:
    """Return an exporter whose eight collaborators are all mocks.

    Why:
        The class takes every dependency by injection, so a test can drive each
        branch without touching the network, the filesystem, or MistHelper.
    """
    return WanClientEventsExporter(  # WHY: each argument is a collaborator handle, not a value.
        cache_utils=MagicMock(),  # WHY: seeds the SiteList cache before any prompt runs.
        org_site_exporter=MagicMock(),  # WHY: supplies the org-scoped site collection to the cache.
        prompt_utils=MagicMock(),  # WHY: owns the interactive site picker.
        file_path_utils=MagicMock(),  # WHY: resolves canonical CSV paths under the data directory.
        data_processing_utils=MagicMock(),  # WHY: flattens and escapes the vendor payload.
        data_exporter=MagicMock(),  # WHY: persists the final rows through the chosen backend.
        mistapi_module=MagicMock(),  # WHY: stands in for the vendor SDK entry points.
        apisession=MagicMock(),  # WHY: the authenticated session each SDK call receives.
    )


@pytest.fixture
def exporter() -> WanClientEventsExporter:
    """Return a fresh exporter for one test.

    Why:
        The mocks record calls, so each test needs its own instance to keep the
        assertions independent.
    """
    return _build_exporter()  # WHY: a new instance per test avoids shared call history.


class TestEnsureSiteSelected:
    """Cover site resolution, which decides whether the workflow continues."""

    def test_a_supplied_site_skips_the_prompt(self, exporter: WanClientEventsExporter) -> None:
        """A caller-supplied site must not trigger an interactive prompt."""
        assert exporter._ensure_site_selected("site-1") == "site-1"  # WHY: value passes through.
        # WHY: an unattended run must never block on a prompt it does not need.
        exporter.prompt_utils.select_site_id_from_csv.assert_not_called()

    def test_the_cache_is_seeded_before_any_resolution(self, exporter: WanClientEventsExporter) -> None:
        """The SiteList cache is a precondition for both the picker and the lookup."""
        exporter._ensure_site_selected("site-1")  # WHY: drive the precondition step.
        # WHY: the cache call must name the canonical file and the site source.
        exporter.cache_utils.check_and_generate_csv.assert_called_once_with(
            _SITE_LIST_CSV, exporter.org_site_exporter.sites
        )

    def test_a_missing_site_triggers_the_prompt(self, exporter: WanClientEventsExporter) -> None:
        """An absent site identifier must fall through to the interactive picker."""
        exporter.prompt_utils.select_site_id_from_csv.return_value = "site-9"  # WHY: operator picks.
        assert exporter._ensure_site_selected(None) == "site-9"  # WHY: the pick becomes the target.

    def test_a_cancelled_prompt_returns_none(self, exporter: WanClientEventsExporter) -> None:
        """A cancelled prompt must abort so the run writes no artifact."""
        exporter.prompt_utils.select_site_id_from_csv.return_value = ""  # WHY: an empty pick cancels.
        assert exporter._ensure_site_selected(None) is None  # WHY: None signals abort to the caller.


class TestScanSiteListForName:
    """Cover the CSV scan, which opens a real file handle."""

    def test_a_matching_row_returns_its_name(self, tmp_path: Path) -> None:
        """The scan must return the name of the row whose identifier matches."""
        path = tmp_path / _SITE_LIST_CSV  # WHY: a real file exercises the open and the reader.
        # WHY: two rows prove the scan selects by identifier and not by position.
        path.write_text("id,name\nsite-1,Branch One\nsite-2,Branch Two\n", encoding="utf-8")
        assert WanClientEventsExporter._scan_site_list_for_name(str(path), "site-2") == "Branch Two"

    def test_a_missing_row_returns_the_fallback(self, tmp_path: Path) -> None:
        """A site absent from the cache must still yield a stable label."""
        path = tmp_path / _SITE_LIST_CSV  # WHY: a real file with no matching row.
        path.write_text("id,name\nsite-1,Branch One\n", encoding="utf-8")  # WHY: no site-9 row.
        # WHY: the fallback keeps the stamping stable when the cache is stale.
        assert WanClientEventsExporter._scan_site_list_for_name(str(path), "site-9") == _UNKNOWN_SITE

    def test_a_row_without_a_name_column_returns_the_fallback(self, tmp_path: Path) -> None:
        """A cache written by an older release may lack the name column."""
        path = tmp_path / _SITE_LIST_CSV  # WHY: a real file with a reduced header.
        path.write_text("id,country_code\nsite-1,US\n", encoding="utf-8")  # WHY: name column absent.
        # WHY: the reader yields None for the missing key, so the fallback must apply.
        assert WanClientEventsExporter._scan_site_list_for_name(str(path), "site-1") == _UNKNOWN_SITE

    def test_an_empty_file_returns_the_fallback(self, tmp_path: Path) -> None:
        """An empty cache must not raise, because the export still has to run."""
        path = tmp_path / _SITE_LIST_CSV  # WHY: a real but empty file.
        path.write_text("", encoding="utf-8")  # WHY: mimic a truncated cache write.
        # WHY: the reader yields no rows, so the scan falls through to the default.
        assert WanClientEventsExporter._scan_site_list_for_name(str(path), "site-1") == _UNKNOWN_SITE


class TestResolveSiteName:
    """Cover the lookup wrapper, whose whole purpose is the fallback."""

    def test_a_missing_cache_file_falls_back(self, exporter: WanClientEventsExporter, tmp_path: Path) -> None:
        """A missing cache file must degrade to the fallback, not raise."""
        missing = tmp_path / "absent.csv"  # WHY: a path that was never written.
        exporter.file_path_utils.get_csv_path.return_value = str(missing)  # WHY: point at the gap.
        # WHY: the exporter must produce output even when the cache is absent.
        assert exporter._resolve_site_name("site-1") == _UNKNOWN_SITE

    def test_a_path_lookup_failure_falls_back(self, exporter: WanClientEventsExporter) -> None:
        """A failure inside the path helper must reach the same fallback."""
        # WHY: the path helper touches the filesystem, so it can fail on its own.
        exporter.file_path_utils.get_csv_path.side_effect = OSError("read-only volume")
        assert exporter._resolve_site_name("site-1") == _UNKNOWN_SITE  # WHY: must not raise.

    def test_a_resolved_name_is_returned(self, exporter: WanClientEventsExporter, tmp_path: Path) -> None:
        """A healthy cache must yield the real name for the stamping step."""
        path = tmp_path / _SITE_LIST_CSV  # WHY: a real file the scan can read.
        path.write_text("id,name\nsite-1,Head Office\n", encoding="utf-8")  # WHY: one matching row.
        exporter.file_path_utils.get_csv_path.return_value = str(path)  # WHY: point at the cache.
        assert exporter._resolve_site_name("site-1") == "Head Office"  # WHY: the real name wins.


class TestFetchEvents:
    """Cover the fetch, which normalizes the vendor response."""

    def test_the_endpoint_receives_the_session_and_the_page_limit(self, exporter: WanClientEventsExporter) -> None:
        """The first-page call must carry the session, the site, and the page limit."""
        endpoint = exporter.mistapi_module.api.v1.sites.wan_clients.searchSiteWanClientEvents
        exporter.mistapi_module.get_all.return_value = []  # WHY: paging result is not under test here.
        exporter._fetch_events("site-1")  # WHY: drive the first-page call.
        # WHY: a missing limit would page one record at a time and hit the rate limiter.
        endpoint.assert_called_once_with(exporter.apisession, "site-1", limit=1000)

    def test_a_none_page_becomes_an_empty_list(self, exporter: WanClientEventsExporter) -> None:
        """The SDK returns None for an empty response, which callers must not index."""
        exporter.mistapi_module.get_all.return_value = None  # WHY: reproduce the SDK boundary case.
        # WHY: the caller checks truthiness, so a None would work but an index would crash.
        assert exporter._fetch_events("site-1") == []

    def test_rows_pass_through_unchanged(self, exporter: WanClientEventsExporter) -> None:
        """A populated page must reach the caller without loss."""
        rows = [{"mac": "aa:bb"}, {"mac": "cc:dd"}]  # WHY: two rows prove nothing is dropped.
        exporter.mistapi_module.get_all.return_value = rows  # WHY: mimic a full page.
        assert exporter._fetch_events("site-1") == rows  # WHY: the fetch must not filter rows.


class TestWriteNoDataPlaceholder:
    """Cover the sentinel write, which creates a real file."""

    def test_the_placeholder_carries_the_header_and_the_site(
        self, exporter: WanClientEventsExporter, tmp_path: Path
    ) -> None:
        """Downstream readers expect a fixed schema plus the site that produced it."""
        path = tmp_path / _OUTPUT_CSV  # WHY: a real path so the write is observable.
        exporter.file_path_utils.get_csv_path.return_value = str(path)  # WHY: redirect the write.
        exporter._write_no_data_placeholder(_SiteStamp("site-1", "Branch One"))  # WHY: drive the write.
        with open(path, encoding="utf-8", newline="") as handle:  # WHY: read back what was written.
            rows = list(csv.reader(handle))  # WHY: compare the exact rows, not a substring.
        assert rows[0] == _PLACEHOLDER_HEADER  # WHY: the header must match the published schema.
        # WHY: the body row lets an operator attribute the empty result to a site.
        assert rows[1] == ["site-1", "Branch One", _PLACEHOLDER_MESSAGE]

    def test_the_placeholder_overwrites_a_previous_run(self, exporter: WanClientEventsExporter, tmp_path: Path) -> None:
        """A stale file from an earlier run must not leave orphan rows behind."""
        path = tmp_path / _OUTPUT_CSV  # WHY: a real path that already holds data.
        path.write_text("id,name\nold,row\nsecond,row\n", encoding="utf-8")  # WHY: seed stale content.
        exporter.file_path_utils.get_csv_path.return_value = str(path)  # WHY: redirect the write.
        exporter._write_no_data_placeholder(_SiteStamp("site-1", "Branch One"))  # WHY: drive the write.
        with open(path, encoding="utf-8", newline="") as handle:  # WHY: read back what was written.
            rows = list(csv.reader(handle))  # WHY: count the rows to prove truncation.
        assert len(rows) == 2  # WHY: exactly the header plus the sentinel body row.


class TestStampEvents:
    """Cover the stamping step, which adds the join keys."""

    def test_every_row_gets_both_identifiers(self) -> None:
        """Downstream joins need the identifier, and operators need the name."""
        events: list[dict[str, Any]] = [{"mac": "aa:bb"}, {"mac": "cc:dd"}]  # WHY: two raw rows.
        stamped = WanClientEventsExporter._stamp_events(events, _SiteStamp("site-1", "Branch One"))
        # WHY: a row without the identifier cannot join back to the site table.
        assert all(row["site_id"] == "site-1" for row in stamped)
        # WHY: a row without the name forces the operator into a second lookup.
        assert all(row["site_name"] == "Branch One" for row in stamped)

    def test_an_empty_list_stays_empty(self) -> None:
        """An empty input must not raise, because the caller guards on truthiness."""
        # WHY: the loop body never runs, so the function returns the same empty list.
        assert WanClientEventsExporter._stamp_events([], _SiteStamp("site-1", "Branch One")) == []


class TestFinalizeExport:
    """Cover the finalize chain, which persists the run."""

    def test_the_operation_name_reaches_the_writer(self, exporter: WanClientEventsExporter) -> None:
        """The operationId selects the primary key strategy, so it must reach the writer."""
        sanitized = [{"mac": "aa:bb", "site_id": "site-1"}]  # WHY: one sanitized row is enough.
        exporter.data_processing_utils.flatten_nested_fields.return_value = sanitized
        exporter.data_processing_utils.escape_multiline.return_value = sanitized
        exporter._finalize_export([{"mac": "aa:bb"}])  # WHY: drive the full finalize chain.
        _, kwargs = exporter.data_exporter.write_with_format_selection.call_args  # WHY: read the keyword.
        # WHY: a wrong name would pick the wrong strategy and duplicate rows across runs.
        assert kwargs["api_function_name"] == "searchSiteWanClientEvents"

    def test_the_flatten_output_feeds_the_escape_step(self, exporter: WanClientEventsExporter) -> None:
        """The two sanitize steps must run in order, not in parallel on raw rows."""
        flattened = [{"mac": "aa:bb"}]  # WHY: the intermediate value under test.
        exporter.data_processing_utils.flatten_nested_fields.return_value = flattened
        exporter.data_processing_utils.escape_multiline.return_value = flattened
        exporter._flatten_and_sanitize([{"mac": "aa:bb", "nested": {"a": 1}}])  # WHY: drive both steps.
        # WHY: escaping raw rows would leave nested values unescaped in the output.
        exporter.data_processing_utils.escape_multiline.assert_called_once_with(flattened)


class TestExecute:
    """Cover the public entry point, its abort guard, and its error handler."""

    def test_a_cancelled_site_writes_nothing(self, exporter: WanClientEventsExporter) -> None:
        """A cancelled site selection must abort before any API call."""
        exporter.prompt_utils.select_site_id_from_csv.return_value = ""  # WHY: an empty pick cancels.
        exporter.execute()  # WHY: drive the abort guard with no supplied site.
        endpoint = exporter.mistapi_module.api.v1.sites.wan_clients.searchSiteWanClientEvents
        endpoint.assert_not_called()  # WHY: no site means no endpoint to query.
        # WHY: an aborted run must leave the output directory untouched.
        exporter.data_exporter.write_with_format_selection.assert_not_called()

    def test_an_empty_result_writes_the_placeholder_not_the_dataset(
        self, exporter: WanClientEventsExporter, tmp_path: Path
    ) -> None:
        """An endpoint that returns nothing must produce the sentinel, not a data file."""
        exporter.mistapi_module.get_all.return_value = []  # WHY: reproduce an empty response.
        # WHY: both the name lookup and the placeholder write resolve through this helper.
        exporter.file_path_utils.get_csv_path.return_value = str(tmp_path / _OUTPUT_CSV)
        exporter.execute("site-1")  # WHY: drive the empty-result branch.
        # WHY: the backend writer must stay unused so no empty dataset is persisted.
        exporter.data_exporter.write_with_format_selection.assert_not_called()
        assert (tmp_path / _OUTPUT_CSV).exists()  # WHY: the sentinel artifact must still appear.

    def test_a_fetch_failure_is_logged_and_not_raised(self, exporter: WanClientEventsExporter, caplog: Any) -> None:
        """A network or SDK failure must be logged, not raised into the menu loop."""
        caplog.set_level("ERROR")  # WHY: the handler reports the failure at ERROR level.
        endpoint = exporter.mistapi_module.api.v1.sites.wan_clients.searchSiteWanClientEvents
        endpoint.side_effect = RuntimeError("gateway timeout")  # WHY: drive the except branch.
        exporter.execute("site-1")  # WHY: must not raise.
        assert "gateway timeout" in caplog.text  # WHY: the operator needs the cause to triage.

    def test_a_write_failure_is_logged_and_not_raised(self, exporter: WanClientEventsExporter, caplog: Any) -> None:
        """A backend write failure must reach the same guard as a fetch failure."""
        caplog.set_level("ERROR")  # WHY: the handler reports the failure at ERROR level.
        rows = [{"mac": "aa:bb"}]  # WHY: a non-empty result reaches the finalize stage.
        exporter.mistapi_module.get_all.return_value = rows  # WHY: mimic a populated page.
        exporter.data_processing_utils.flatten_nested_fields.return_value = rows
        exporter.data_processing_utils.escape_multiline.return_value = rows
        # WHY: a full disk or a locked database fails at the write, not at the fetch.
        exporter.data_exporter.write_with_format_selection.side_effect = OSError("disk full")
        exporter.execute("site-1")  # WHY: must not raise.
        assert "disk full" in caplog.text  # WHY: the operator needs the cause to triage.

    def test_a_successful_run_stamps_and_persists_the_rows(
        self, exporter: WanClientEventsExporter, tmp_path: Path
    ) -> None:
        """The happy path must stamp the site onto each row before persisting it."""
        path = tmp_path / _SITE_LIST_CSV  # WHY: a real cache so the real name resolves.
        path.write_text("id,name\nsite-1,Head Office\n", encoding="utf-8")  # WHY: one matching row.
        exporter.file_path_utils.get_csv_path.return_value = str(path)  # WHY: point at the cache.
        rows = [{"mac": "aa:bb"}]  # WHY: one row is enough to observe the stamping.
        exporter.mistapi_module.get_all.return_value = rows  # WHY: mimic a populated page.
        exporter.data_processing_utils.flatten_nested_fields.return_value = rows
        exporter.data_processing_utils.escape_multiline.return_value = rows
        exporter.execute("site-1")  # WHY: drive the full happy path.
        # WHY: the stamp runs before the flatten, so the flatten input carries both keys.
        flattened_input = exporter.data_processing_utils.flatten_nested_fields.call_args[0][0]
        assert flattened_input[0]["site_name"] == "Head Office"  # WHY: the real name must be stamped.
        exporter.data_exporter.write_with_format_selection.assert_called_once()  # WHY: one write.
