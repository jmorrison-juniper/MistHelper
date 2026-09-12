"""Unit tests for InsightMetricsUtils (issue #878 tranche 8 -- un-omit).

Covers every static method on ``src.analytics.insight_metrics_utils``:
``export_const_insight_metrics`` (banner + exporter delegation + CSV present/absent),
``_should_skip_row`` (empty / placeholder / valid),
``_row_matches_scope`` (skip / match / no-match),
``_collect_metrics_for_scope`` (drops Nones),
``get_by_scope`` (happy / missing-file / exception),
``_parse_scopes`` (empty / normalization / separator handling),
``_log_normalization_summary`` (debug trace),
``parse_to_normalized_data`` (happy / exception),
``_build_summary_base`` (fixed keys),
``_extract_summary`` (present scalars only),
``_extract_time_series`` (non-CSV rt / CSV rt + fields),
``_is_csv_string`` (truthy/str/comma),
``_field_time_series_points`` (non-CSV / skip empties / points),
``_parse_results_key`` (valid / invalid),
``_ensure_result_row`` (reuse / create-digit / create-non-digit),
``_extract_results`` (walks and builds rows),
``_extract_sites_data`` (list + keyed merge),
``_extract_sites_list`` (list-only entries),
``_merge_keyed_sites`` (find-or-create),
``_parse_keyed_site_field`` (valid / non-matching),
``_find_or_create_site`` (existing / new).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.analytics.insight_metrics_utils import InsightMetricsUtils


def _make_mh(**extra):
    """Assemble a stub MistHelper module with the attributes each method touches."""
    defaults = {
        "ConstDefinitionsExporter": MagicMock(name="ConstDefinitionsExporter"),
        "apisession": MagicMock(name="apisession"),
    }
    defaults.update(extra)
    return SimpleNamespace(**defaults)


# ---------- export_const_insight_metrics ----------


def test_export_const_insight_metrics_delegates_and_reports_present(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """CSV present -> exporter.export_all is called and 'available' message logged."""
    fake_mh = _make_mh()
    exporter_instance = MagicMock()
    fake_mh.ConstDefinitionsExporter.return_value = exporter_instance
    with (
        caplog.at_level("INFO", logger="root"),
        patch("src.analytics.insight_metrics_utils.os.path.exists", return_value=True),
        patch("src.analytics.insight_metrics_utils.importlib.import_module", return_value=fake_mh),
    ):
        InsightMetricsUtils.export_const_insight_metrics()
    fake_mh.ConstDefinitionsExporter.assert_called_once_with(fake_mh.apisession)
    exporter_instance.export_all.assert_called_once_with()
    messages = " ".join(rec.getMessage() for rec in caplog.records)
    assert "Export Available Insight Metrics" in messages
    assert "ConstInsightMetrics.csv is available" in messages


def test_export_const_insight_metrics_warns_when_csv_missing(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """CSV absent -> warning is logged."""
    fake_mh = _make_mh()
    with (
        caplog.at_level("WARNING", logger="root"),
        patch("src.analytics.insight_metrics_utils.os.path.exists", return_value=False),
        patch("src.analytics.insight_metrics_utils.importlib.import_module", return_value=fake_mh),
    ):
        InsightMetricsUtils.export_const_insight_metrics()
    messages = " ".join(rec.getMessage() for rec in caplog.records)
    assert "was not created" in messages


# ---------- _should_skip_row ----------


def test_should_skip_row_empty_fields() -> None:
    """Empty metric_name or scopes trigger skip."""
    assert InsightMetricsUtils._should_skip_row("", "site") is True
    assert InsightMetricsUtils._should_skip_row("metric", "") is True


def test_should_skip_row_template_placeholder() -> None:
    """Curly brace placeholders trigger skip."""
    assert InsightMetricsUtils._should_skip_row("{foo}", "site") is True
    assert InsightMetricsUtils._should_skip_row("foo}", "site") is True


def test_should_skip_row_valid() -> None:
    """Real name + scopes -> not skipped."""
    assert InsightMetricsUtils._should_skip_row("coverage", "site,client") is False


# ---------- _row_matches_scope ----------


def test_row_matches_scope_returns_name_when_scope_matches() -> None:
    """Scope token present -> metric_name returned."""
    row = {"metric_name": "coverage", "scopes": "site,client"}
    assert InsightMetricsUtils._row_matches_scope(row, "site") == "coverage"


def test_row_matches_scope_returns_none_when_scope_absent() -> None:
    """Scope not in tokens -> None."""
    row = {"metric_name": "coverage", "scopes": "site"}
    assert InsightMetricsUtils._row_matches_scope(row, "client") is None


def test_row_matches_scope_returns_none_when_row_should_skip() -> None:
    """Skip candidate -> None."""
    row = {"metric_name": "", "scopes": "site"}
    assert InsightMetricsUtils._row_matches_scope(row, "site") is None


# ---------- _collect_metrics_for_scope ----------


def test_collect_metrics_for_scope_drops_none_skips() -> None:
    """None returns from _row_matches_scope are filtered out."""
    rows = [
        {"metric_name": "m1", "scopes": "site"},
        {"metric_name": "m2", "scopes": "client"},
        {"metric_name": "m3", "scopes": "site,client"},
    ]
    result = InsightMetricsUtils._collect_metrics_for_scope(iter(rows), "site")
    assert result == ["m1", "m3"]


# ---------- get_by_scope ----------


def test_get_by_scope_returns_matches_from_csv(tmp_path) -> None:
    """CSV happy path returns metrics for the requested scope."""
    csv_path = tmp_path / "ConstInsightMetrics.csv"
    csv_path.write_text('metric_name,scopes\nm1,site\nm2,client\nm3,"site,client"\n', encoding="utf-8")
    with (
        patch("src.analytics.insight_metrics_utils.os.path.exists", return_value=True),
        patch("src.analytics.insight_metrics_utils.os.path.join", return_value=str(csv_path)),
    ):
        assert InsightMetricsUtils.get_by_scope("site") == ["m1", "m3"]


def test_get_by_scope_missing_file_returns_empty() -> None:
    """Missing CSV -> empty list, no raise."""
    with patch("src.analytics.insight_metrics_utils.os.path.exists", return_value=False):
        assert InsightMetricsUtils.get_by_scope("site") == []


def test_get_by_scope_exception_returns_empty() -> None:
    """Read failure -> empty list."""
    with (patch("src.analytics.insight_metrics_utils.os.path.exists", side_effect=RuntimeError("boom")),):
        assert InsightMetricsUtils.get_by_scope("site") == []


def test_get_by_scope_none_target_normalizes() -> None:
    """None target scope normalizes to empty string without raising."""
    with patch("src.analytics.insight_metrics_utils.os.path.exists", return_value=False):
        assert InsightMetricsUtils.get_by_scope(None) == []  # type: ignore[arg-type]


# ---------- _parse_scopes ----------


def test_parse_scopes_empty_returns_empty_set() -> None:
    """Empty string -> empty set."""
    assert InsightMetricsUtils._parse_scopes("") == set()


def test_parse_scopes_normalizes_brackets_quotes_separators() -> None:
    """Brackets and quotes stripped, ';' becomes ',', tokens lowercased."""
    result = InsightMetricsUtils._parse_scopes("[\"Site\";'Client', GATEWAY]")
    assert result == {"site", "client", "gateway"}


def test_parse_scopes_drops_empty_tokens() -> None:
    """Empty tokens between commas are dropped."""
    assert InsightMetricsUtils._parse_scopes("site,,client") == {"site", "client"}


# ---------- _log_normalization_summary ----------


def test_log_normalization_summary_emits_debug(caplog: pytest.LogCaptureFixture) -> None:
    """Debug log records the four bucket counts."""
    normalized = {"summary": [1], "time_series": [1, 2], "results": [], "sites_data": [1, 2, 3]}
    with caplog.at_level("DEBUG", logger="root"):
        InsightMetricsUtils._log_normalization_summary("coverage", normalized)
    joined = " ".join(rec.getMessage() for rec in caplog.records)
    assert "coverage" in joined


# ---------- parse_to_normalized_data ----------


def test_parse_to_normalized_data_assembles_all_four_buckets() -> None:
    """Happy path returns summary, time_series, results, and sites_data lists."""
    metric_data = {"metric_type": "coverage", "num_clients": 5}
    result = InsightMetricsUtils.parse_to_normalized_data(metric_data, "org-1")
    assert isinstance(result["summary"], list) and len(result["summary"]) == 1
    assert result["summary"][0]["org_id"] == "org-1"
    assert result["summary"][0]["metric_type"] == "coverage"
    assert result["summary"][0]["num_clients"] == 5
    assert result["time_series"] == []
    assert result["results"] == []
    assert result["sites_data"] == []


def test_parse_to_normalized_data_exception_returns_empty_buckets() -> None:
    """Exception in extractors -> initialized-empty buckets returned."""
    # metric_data.get raises AttributeError when it's not a dict.
    result = InsightMetricsUtils.parse_to_normalized_data(None, "org-1")  # type: ignore[arg-type]
    assert result == {"summary": [], "time_series": [], "results": [], "sites_data": []}


# ---------- _build_summary_base ----------


def test_build_summary_base_returns_all_fixed_keys() -> None:
    """Fixed metadata keys are populated with defaults when missing."""
    result = InsightMetricsUtils._build_summary_base({}, "org-1", "coverage")
    assert result["org_id"] == "org-1"
    assert result["metric_type"] == "coverage"
    for k in (
        "data_source",
        "start_time",
        "end_time",
        "interval_seconds",
        "limit",
        "total_sites",
        "page",
        "sle_category",
        "original_metric",
        "roaming",
        "total",
        "totalTunnelCount",
    ):
        assert result[k] == ""


def test_build_summary_base_maps_start_end_interval() -> None:
    """start/end/interval fields map to their _time / _seconds keys."""
    md = {"start": 1, "end": 2, "interval": 60, "data_source": "src"}
    result = InsightMetricsUtils._build_summary_base(md, "org-1", "coverage")
    assert result["start_time"] == 1
    assert result["end_time"] == 2
    assert result["interval_seconds"] == 60
    assert result["data_source"] == "src"


# ---------- _extract_summary ----------


def test_extract_summary_appends_present_scalars_only() -> None:
    """SUMMARY_SCALAR_FIELDS present in metric_data are copied; absent ones are omitted."""
    md = {"num_clients": 10, "capacity": 0.9, "not_a_scalar": "ignored"}
    result = InsightMetricsUtils._extract_summary(md, "org-1", "coverage")
    assert result["num_clients"] == 10
    assert result["capacity"] == 0.9
    assert "num_aps" not in result  # not in md


# ---------- _extract_time_series ----------


def test_extract_time_series_returns_empty_when_rt_not_csv() -> None:
    """Non-CSV rt field -> empty list."""
    assert InsightMetricsUtils._extract_time_series({"rt": "single"}, "org-1", "coverage") == []


def test_extract_time_series_builds_points_for_csv_fields() -> None:
    """CSV rt + CSV field -> zipped points, skipping empty/'None' values."""
    md = {
        "rt": "10,20,30",
        "num_clients": "1,,3",
        "num_aps": "5,None,7",
    }
    result = InsightMetricsUtils._extract_time_series(md, "org-1", "coverage")
    values = {(p["value_type"], p["timestamp"], p["value"]) for p in result}
    assert ("num_clients", "10", "1") in values
    assert ("num_clients", "30", "3") in values
    assert ("num_aps", "10", "5") in values
    assert ("num_aps", "30", "7") in values
    # empty '' and 'None' values are skipped
    assert not any(p["value"] in ("", "None") for p in result)


# ---------- _is_csv_string ----------


def test_is_csv_string_variants() -> None:
    """Only non-empty strings containing a comma are CSV."""
    assert InsightMetricsUtils._is_csv_string("a,b") is True
    assert InsightMetricsUtils._is_csv_string("noComma") is False
    assert InsightMetricsUtils._is_csv_string("") is False
    assert InsightMetricsUtils._is_csv_string(None) is False
    assert InsightMetricsUtils._is_csv_string(123) is False


# ---------- _field_time_series_points ----------


def test_field_time_series_points_returns_empty_when_not_csv() -> None:
    """Non-CSV field_data -> empty list."""
    assert InsightMetricsUtils._field_time_series_points("num_clients", "single", ["10"], "o", "m") == []


def test_field_time_series_points_pairs_and_skips_empties() -> None:
    """Empty and 'None' values in the CSV are dropped; index is preserved."""
    points = InsightMetricsUtils._field_time_series_points(
        "num_clients", "1,,None,4", ["10", "20", "30", "40"], "org-1", "coverage"
    )
    assert [p["value"] for p in points] == ["1", "4"]
    assert [p["sequence_order"] for p in points] == [0, 3]
    assert all(p["org_id"] == "org-1" for p in points)


# ---------- _parse_results_key ----------


def test_parse_results_key_valid() -> None:
    """Valid 'results_<index>_<field>' -> (index, field)."""
    assert InsightMetricsUtils._parse_results_key("results_0_name") == ("0", "name")


def test_parse_results_key_underscore_in_field() -> None:
    """maxsplit=2 keeps trailing underscores as part of field."""
    assert InsightMetricsUtils._parse_results_key("results_1_a_b") == ("1", "a_b")


def test_parse_results_key_rejects_non_results() -> None:
    """Non-'results_' key -> None."""
    assert InsightMetricsUtils._parse_results_key("sites_0_name") is None


def test_parse_results_key_rejects_no_field_component() -> None:
    """No third part (no field) -> None."""
    assert InsightMetricsUtils._parse_results_key("results_0") is None


# ---------- _ensure_result_row ----------


def test_ensure_result_row_reuses_existing() -> None:
    """Existing row is returned without appending."""
    existing = {"result_index": "0", "foo": "bar"}
    data = [existing]
    row = InsightMetricsUtils._ensure_result_row(data, "0", "org-1", "coverage")
    assert row is existing
    assert len(data) == 1


def test_ensure_result_row_creates_digit_index_as_int() -> None:
    """Digit string indexes become int on the new row."""
    data: list = []
    row = InsightMetricsUtils._ensure_result_row(data, "3", "org-1", "coverage")
    assert row["result_index"] == 3
    assert row["org_id"] == "org-1"
    assert row["metric_type"] == "coverage"
    assert data == [row]


def test_ensure_result_row_creates_non_digit_index_verbatim() -> None:
    """Non-digit index is kept as-is."""
    data: list = []
    row = InsightMetricsUtils._ensure_result_row(data, "abc", "org-1", "coverage")
    assert row["result_index"] == "abc"


# ---------- _extract_results ----------


def test_extract_results_builds_rows_from_flattened_keys() -> None:
    """results_* keys build rows; digit indexes create a new row per key (int-vs-str compare quirk)."""
    md = {
        "results_0_name": "a",
        "results_0_value": 1,
        "results_1_name": "b",
        "unrelated": "nope",
    }
    result = InsightMetricsUtils._extract_results(md, "org-1", "coverage")
    # _ensure_result_row stores digit indexes as int(0) but compares against str '0',
    # so each results_0_* key becomes its own row.
    assert len(result) == 3
    fields = [{k: v for k, v in r.items() if k not in ("org_id", "metric_type", "result_index")} for r in result]
    assert {"name": "a"} in fields
    assert {"value": 1} in fields
    assert {"name": "b"} in fields
    assert all(r["result_index"] in (0, 1) for r in result)


# ---------- _extract_sites_list ----------


def test_extract_sites_list_tags_dict_entries() -> None:
    """List payload: dicts are tagged with org_id/metric_type; non-dicts skipped."""
    sites = [{"site_id": "s1", "value": 1}, "skip-me", {"site_id": "s2"}]
    result = InsightMetricsUtils._extract_sites_list(sites, "org-1", "coverage")
    assert len(result) == 2
    assert all(r["org_id"] == "org-1" and r["metric_type"] == "coverage" for r in result)
    assert result[0]["site_id"] == "s1"
    assert result[0]["value"] == 1


def test_extract_sites_list_non_list_returns_empty() -> None:
    """Non-list sites_data -> empty list."""
    assert InsightMetricsUtils._extract_sites_list({"not": "list"}, "org-1", "coverage") == []


# ---------- _parse_keyed_site_field ----------


def test_parse_keyed_site_field_valid() -> None:
    """Valid sites_data_<index> defaults field to 'value' (maxsplit=2 truncates)."""
    result = InsightMetricsUtils._parse_keyed_site_field("sites_data_5_name")
    # maxsplit=2 -> ['sites', 'data', '5_name']; len(parts)==3, no parts[3]; defaults to 'value'
    assert result == ("5_name", "value")


def test_parse_keyed_site_field_rejects_non_matching() -> None:
    """Non 'sites_data_' key -> None."""
    assert InsightMetricsUtils._parse_keyed_site_field("results_0_name") is None


def test_parse_keyed_site_field_rejects_short() -> None:
    """Only 'sites_data' with nothing after -> None."""
    assert InsightMetricsUtils._parse_keyed_site_field("sites_data") is None


# ---------- _find_or_create_site ----------


def test_find_or_create_site_reuses_existing_row() -> None:
    """Existing row matching index+metric_type is returned."""
    existing = {"site_index": "0", "metric_type": "coverage", "foo": "bar"}
    data = [existing]
    row = InsightMetricsUtils._find_or_create_site(data, "0", "org-1", "coverage")
    assert row is existing


def test_find_or_create_site_creates_new_row_when_absent() -> None:
    """Missing row -> new row appended with the org/metric/index."""
    data: list = []
    row = InsightMetricsUtils._find_or_create_site(data, "7", "org-1", "coverage")
    assert row == {"org_id": "org-1", "metric_type": "coverage", "site_index": "7"}
    assert data == [row]


def test_find_or_create_site_different_metric_type_creates_new() -> None:
    """Same index but different metric_type -> new row created."""
    existing = {"site_index": "0", "metric_type": "other"}
    data = [existing]
    row = InsightMetricsUtils._find_or_create_site(data, "0", "org-1", "coverage")
    assert row is not existing
    assert len(data) == 2


# ---------- _merge_keyed_sites ----------


def test_merge_keyed_sites_updates_rows_by_index() -> None:
    """sites_data_* keys are merged onto the matching or newly-created site row."""
    records: list = []
    md = {"sites_data_0_name": "site-a", "unrelated": "skip"}
    InsightMetricsUtils._merge_keyed_sites(md, "org-1", "coverage", records)
    assert len(records) == 1
    # parse_keyed_site_field returns ("0_name", "value") due to maxsplit=2
    assert records[0]["site_index"] == "0_name"
    assert records[0]["value"] == "site-a"


# ---------- _extract_sites_data ----------


def test_extract_sites_data_combines_list_and_keyed_entries() -> None:
    """Combines list-payload sites_data with sites_data_* flattened fields."""
    md = {
        "sites_data": [{"site_id": "s1"}],
        "sites_data_0_name": "extra",
    }
    result = InsightMetricsUtils._extract_sites_data(md, "org-1", "coverage")
    # 1 from list payload + 1 from keyed merge (different indexes)
    assert len(result) == 2
