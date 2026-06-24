"""Unit tests for OrgAlarmEventExporter in-place 52w legacy decomposition."""

from types import SimpleNamespace

import MistHelper


class TestCheckpointHelpers:
    """Verify checkpoint load/save/remove helpers behave correctly."""

    def test_load_checkpoint_returns_none_when_file_missing(self, tmp_path):
        result = MistHelper.OrgAlarmEventExporter._52w_load_checkpoint(str(tmp_path / "missing.checkpoint"))
        assert result is None

    def test_load_checkpoint_returns_token_when_present(self, tmp_path):
        cp = tmp_path / "test.checkpoint"
        cp.write_text("abc123\n")

        result = MistHelper.OrgAlarmEventExporter._52w_load_checkpoint(str(cp))

        assert result == "abc123"

    def test_save_checkpoint_writes_token(self, tmp_path):
        cp = str(tmp_path / "test.checkpoint")

        MistHelper.OrgAlarmEventExporter._52w_save_checkpoint(cp, "tok-xyz")

        assert open(cp).read() == "tok-xyz"

    def test_remove_checkpoint_deletes_file(self, tmp_path):
        cp = tmp_path / "test.checkpoint"
        cp.write_text("tok")

        MistHelper.OrgAlarmEventExporter._52w_remove_checkpoint(str(cp))

        assert not cp.exists()

    def test_remove_checkpoint_is_noop_when_missing(self, tmp_path):
        """Removing a non-existent checkpoint should not raise."""
        MistHelper.OrgAlarmEventExporter._52w_remove_checkpoint(str(tmp_path / "nope.checkpoint"))


class TestParsePageData:
    """Verify _52w_parse_page_data handles all SDK response shapes."""

    def test_parses_dict_with_results_key(self):
        response = SimpleNamespace(data={"results": [{"id": 1}], "search_after": "tok1"})
        results, token = MistHelper.OrgAlarmEventExporter._52w_parse_page_data(response)
        assert results == [{"id": 1}]
        assert token == "tok1"

    def test_returns_empty_for_missing_data(self):
        response = SimpleNamespace(data=None)
        results, token = MistHelper.OrgAlarmEventExporter._52w_parse_page_data(response)
        assert results == []
        assert token is None

    def test_parses_flat_list_payload(self):
        response = SimpleNamespace(data=[{"id": 2}, {"id": 3}])
        results, token = MistHelper.OrgAlarmEventExporter._52w_parse_page_data(response)
        assert len(results) == 2
        assert token is None


class TestWriteBatch:
    """Verify _52w_write_batch handles CSV initial and append modes."""

    def test_csv_initial_write_creates_file_with_header(self, tmp_path):
        rows = [{"a": "1", "b": "2"}]
        csv_file = str(tmp_path / "out.csv")

        MistHelper.OrgAlarmEventExporter._52w_write_batch(rows, ["a", "b"], csv_file, "t", append=False)

        content = open(csv_file).read()
        assert "a,b" in content
        assert "1,2" in content

    def test_csv_append_does_not_duplicate_header(self, tmp_path):
        csv_file = str(tmp_path / "out.csv")
        # Write initial batch
        MistHelper.OrgAlarmEventExporter._52w_write_batch([{"a": "1"}], ["a"], csv_file, "t", append=False)
        # Append a second row
        MistHelper.OrgAlarmEventExporter._52w_write_batch([{"a": "2"}], ["a"], csv_file, "t", append=True)

        lines = open(csv_file).readlines()
        assert lines[0].strip() == "a"  # Only one header row
        assert len(lines) == 3  # header + 2 data rows


class TestDevice52wLegacyOrchestration:
    """Verify orchestrator calls helpers in the correct order."""

    def test_empty_preload_exits_without_writing_real_file(self, monkeypatch):
        """No rows -> write_with_format_selection called with empty list (issue #431)."""
        monkeypatch.setattr(MistHelper.ConfigUtils, "get_cached_or_prompted_org_id", lambda: "org-1")
        monkeypatch.setattr(MistHelper.OrgAlarmEventExporter, "_52w_load_checkpoint", lambda cp: None)
        monkeypatch.setattr(
            MistHelper.OrgAlarmEventExporter,
            "_52w_preload_pages",
            lambda org_id, search_after, limit, duration, preload_count: ([], None),
        )
        saved = {"rows": None}
        monkeypatch.setattr(
            MistHelper.DataExporter,
            "write_with_format_selection",
            lambda rows, fname, **_kw: saved.__setitem__("rows", rows),
        )

        MistHelper.OrgAlarmEventExporter.device_events_52w_legacy()

        assert saved["rows"] == []

    def test_full_path_calls_write_and_cleanup(self, tmp_path, monkeypatch):
        """One page of data → write_batch called, checkpoint cleaned up."""
        monkeypatch.setattr(MistHelper.ConfigUtils, "get_cached_or_prompted_org_id", lambda: "org-1")
        monkeypatch.setattr(MistHelper.os, "makedirs", lambda path, exist_ok=True: None)
        monkeypatch.setattr(MistHelper.OrgAlarmEventExporter, "_52w_load_checkpoint", lambda cp: None)
        monkeypatch.setattr(
            MistHelper.OrgAlarmEventExporter,
            "_52w_preload_pages",
            lambda org_id, sa, limit, dur, preload_count: ([{"x": "1"}], None),
        )
        monkeypatch.setattr(MistHelper.DataProcessingUtils, "get_unique_keys", lambda rows: ["x"])
        calls = {"write": 0, "remove": 0}
        monkeypatch.setattr(
            MistHelper.OrgAlarmEventExporter,
            "_52w_write_batch",
            lambda rows, header_fields, csv_file, table_name, append: calls.__setitem__("write", calls["write"] + 1),
        )
        monkeypatch.setattr(
            MistHelper.OrgAlarmEventExporter,
            "_52w_remove_checkpoint",
            lambda cp: calls.__setitem__("remove", calls["remove"] + 1),
        )

        MistHelper.OrgAlarmEventExporter.device_events_52w_legacy()

        assert calls["write"] == 1  # Initial batch written
        assert calls["remove"] == 1  # Checkpoint cleaned up
