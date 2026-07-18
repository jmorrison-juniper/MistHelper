"""Unit tests for src.export.data_exporter.DataExporter.

Tranche 15 of initiative #878: un-omit `data_exporter.py` and drive it to
100% line coverage.

Why:
    DataExporter is the multi-backend export facade routing writes to CSV,
    SQLite, and the optional polyglot DB layer. Tests mock the optional
    DB layer, filesystem, SQLite writer, and lazy MistHelper import so that
    pure logic (branch selection, throttling, error handling, and one-shot
    guards) is exercised without touching real IO or external dependencies.
"""

from __future__ import annotations

import importlib
import sys
import types
from unittest.mock import MagicMock, mock_open, patch

import pytest

from src.dataclasses.export_backend_options import ExportBackendOptions
from src.export import data_exporter as de_module
from src.export.data_exporter import DataExporter


@pytest.fixture(autouse=True)
def _reset_class_state():
    """Reset DataExporter class-level mutable state between tests.

    Why:
        The DataExporter class caches ``_router``, ``_router_initialized``,
        ``_last_snapshot_times``, and ``_standalone_logged`` at class scope.
        Without a reset, ordering-sensitive tests would leak state.
    """
    DataExporter._router = None
    DataExporter._router_initialized = False
    DataExporter._last_snapshot_times = {}
    DataExporter._standalone_logged = False
    yield
    DataExporter._router = None
    DataExporter._router_initialized = False
    DataExporter._last_snapshot_times = {}
    DataExporter._standalone_logged = False


@pytest.fixture
def fake_mh(monkeypatch):
    """Install a fake ``MistHelper`` module for the lazy importlib lookup.

    Why:
        ``write_with_format_selection`` reads the OUTPUT_FORMAT global from
        MistHelper via ``importlib.import_module("MistHelper")``. Injecting a
        synthetic module isolates tests from the real project bootstrap.
    """
    module = types.ModuleType("MistHelper")
    module.OUTPUT_FORMAT = "csv"
    monkeypatch.setitem(sys.modules, "MistHelper", module)
    return module


class TestPolyglotDbLayerAvailable:
    def test_returns_false_when_db_layer_unavailable(self, monkeypatch):
        monkeypatch.setattr(de_module, "DB_LAYER_AVAILABLE", False)
        assert DataExporter._polyglot_db_layer_available() is False

    def test_returns_false_when_databaseconfig_missing(self, monkeypatch):
        monkeypatch.setattr(de_module, "DB_LAYER_AVAILABLE", True)
        monkeypatch.setattr(de_module, "DatabaseConfig", None)
        assert DataExporter._polyglot_db_layer_available() is False

    def test_returns_false_when_configure_db_logging_missing(self, monkeypatch):
        monkeypatch.setattr(de_module, "DB_LAYER_AVAILABLE", True)
        monkeypatch.setattr(de_module, "DatabaseConfig", MagicMock())
        monkeypatch.setattr(de_module, "configure_db_logging", None)
        assert DataExporter._polyglot_db_layer_available() is False

    def test_returns_false_when_router_missing(self, monkeypatch):
        monkeypatch.setattr(de_module, "DB_LAYER_AVAILABLE", True)
        monkeypatch.setattr(de_module, "DatabaseConfig", MagicMock())
        monkeypatch.setattr(de_module, "configure_db_logging", MagicMock())
        monkeypatch.setattr(de_module, "DatabaseRouter", None)
        assert DataExporter._polyglot_db_layer_available() is False

    def test_returns_true_when_all_available(self, monkeypatch):
        monkeypatch.setattr(de_module, "DB_LAYER_AVAILABLE", True)
        monkeypatch.setattr(de_module, "DatabaseConfig", MagicMock())
        monkeypatch.setattr(de_module, "configure_db_logging", MagicMock())
        monkeypatch.setattr(de_module, "DatabaseRouter", MagicMock())
        assert DataExporter._polyglot_db_layer_available() is True


class TestBuildPolyglotRouter:
    def test_success_sets_router(self, monkeypatch):
        config = MagicMock()
        db_config = MagicMock()
        db_config.from_env.return_value = config
        router_cls = MagicMock()
        router_instance = MagicMock()
        router_cls.return_value = router_instance
        configure_logger = MagicMock()

        monkeypatch.setattr(de_module, "DB_LAYER_AVAILABLE", True)
        monkeypatch.setattr(de_module, "DatabaseConfig", db_config)
        monkeypatch.setattr(de_module, "configure_db_logging", configure_logger)
        monkeypatch.setattr(de_module, "DatabaseRouter", router_cls)

        DataExporter._build_polyglot_router()

        configure_logger.assert_called_once()
        db_config.from_env.assert_called_once()
        router_cls.assert_called_once()
        assert DataExporter._router is router_instance

    def test_failure_sets_router_none(self, monkeypatch):
        monkeypatch.setattr(de_module, "DB_LAYER_AVAILABLE", True)
        monkeypatch.setattr(de_module, "DatabaseConfig", MagicMock())
        monkeypatch.setattr(de_module, "configure_db_logging", MagicMock(side_effect=RuntimeError("boom")))
        monkeypatch.setattr(de_module, "DatabaseRouter", MagicMock())

        DataExporter._router = MagicMock()  # Prior state to prove reset on failure
        DataExporter._build_polyglot_router()
        assert DataExporter._router is None


class TestInitRouter:
    def test_skip_when_already_initialized(self):
        DataExporter._router_initialized = True
        with patch.object(DataExporter, "_polyglot_db_layer_available") as check:
            DataExporter._init_router()
            check.assert_not_called()

    def test_skip_when_layer_unavailable(self):
        with (
            patch.object(DataExporter, "_polyglot_db_layer_available", return_value=False),
            patch.object(DataExporter, "_build_polyglot_router") as build,
        ):
            DataExporter._init_router()
            build.assert_not_called()
            assert DataExporter._router_initialized is True

    def test_builds_router_when_layer_available(self):
        with (
            patch.object(DataExporter, "_polyglot_db_layer_available", return_value=True),
            patch.object(DataExporter, "_build_polyglot_router") as build,
        ):
            DataExporter._init_router()
            build.assert_called_once()
            assert DataExporter._router_initialized is True


class TestDispatchFormatWrite:
    def test_csv_branch(self):
        with patch.object(DataExporter, "_write_csv_format", return_value=True) as csv_writer:
            ok = DataExporter._dispatch_format_write([{"a": 1}], "out.csv", "csv", ["a"], "listStuff")
        assert ok is True
        csv_writer.assert_called_once_with([{"a": 1}], "out.csv", fieldnames=["a"])

    def test_sqlite_branch(self):
        with patch.object(DataExporter, "_write_sqlite_format", return_value=True) as sql_writer:
            ok = DataExporter._dispatch_format_write([{"a": 1}], "table", "sqlite", None, "listStuff")
        assert ok is True
        sql_writer.assert_called_once_with([{"a": 1}], "table", "listStuff")

    def test_exception_returns_false(self):
        with patch.object(DataExporter, "_write_csv_format", side_effect=RuntimeError("boom")):
            ok = DataExporter._dispatch_format_write([{"a": 1}], "out.csv", "csv", None, "listStuff")
        assert ok is False


class TestWriteWithFormatSelection:
    def test_uses_global_output_format_from_mh(self, fake_mh):
        fake_mh.OUTPUT_FORMAT = "csv"
        with (
            patch.object(DataExporter, "_validate_write_inputs", return_value=True) as validate,
            patch.object(DataExporter, "_dispatch_format_write", return_value=True) as dispatch,
            patch.object(DataExporter, "_route_to_polyglot") as route,
        ):
            ok = DataExporter.write_with_format_selection([{"a": 1}], "target", api_function_name="listStuff")
        assert ok is True
        validate.assert_called_once_with([{"a": 1}], "target", "csv")
        dispatch.assert_called_once_with([{"a": 1}], "target", "csv", None, "listStuff")
        route.assert_called_once()

    def test_uses_format_override(self, fake_mh):
        fake_mh.OUTPUT_FORMAT = "csv"
        opts = ExportBackendOptions(format_override="sqlite")
        with (
            patch.object(DataExporter, "_validate_write_inputs", return_value=True),
            patch.object(DataExporter, "_dispatch_format_write", return_value=True) as dispatch,
            patch.object(DataExporter, "_route_to_polyglot"),
        ):
            DataExporter.write_with_format_selection(
                [{"a": 1}], "target", api_function_name="listStuff", backend_options=opts
            )
        assert dispatch.call_args.args[2] == "sqlite"

    def test_returns_false_on_invalid_inputs(self, fake_mh):
        with (
            patch.object(DataExporter, "_validate_write_inputs", return_value=False),
            patch.object(DataExporter, "_dispatch_format_write") as dispatch,
            patch.object(DataExporter, "_route_to_polyglot") as route,
        ):
            ok = DataExporter.write_with_format_selection([], "target")
        assert ok is False
        dispatch.assert_not_called()
        route.assert_not_called()

    def test_passes_raw_data_to_route(self, fake_mh):
        raw = [{"raw": 1}]
        opts = ExportBackendOptions(raw_data=raw)
        with (
            patch.object(DataExporter, "_validate_write_inputs", return_value=True),
            patch.object(DataExporter, "_dispatch_format_write", return_value=True),
            patch.object(DataExporter, "_route_to_polyglot") as route,
        ):
            DataExporter.write_with_format_selection(
                [{"a": 1}], "target", api_function_name="listStuff", backend_options=opts
            )
        route.assert_called_once_with([{"a": 1}], "listStuff", raw_data=raw)

    def test_handles_none_data_for_debug_log(self, fake_mh):
        with (
            patch.object(DataExporter, "_validate_write_inputs", return_value=False),
            patch.object(DataExporter, "_dispatch_format_write"),
        ):
            ok = DataExporter.write_with_format_selection(None, "target")
        assert ok is False


class TestIsStandaloneMode:
    def test_env_true_forces_standalone(self, monkeypatch):
        monkeypatch.setenv("MISTHELPER_STANDALONE", "TRUE")
        assert DataExporter._is_standalone_mode() is True

    def test_env_false_forces_non_standalone(self, monkeypatch):
        monkeypatch.setenv("MISTHELPER_STANDALONE", "false")
        assert DataExporter._is_standalone_mode() is False

    def test_autodetect_not_in_container_logs_once(self, monkeypatch):
        monkeypatch.delenv("MISTHELPER_STANDALONE", raising=False)
        with patch(
            "src.export.data_exporter.EnvironmentUtils.is_running_in_container",
            return_value=False,
        ):
            assert DataExporter._is_standalone_mode() is True
            assert DataExporter._standalone_logged is True
            # Second call reuses the latched log guard.
            assert DataExporter._is_standalone_mode() is True

    def test_autodetect_in_container_returns_false(self, monkeypatch):
        monkeypatch.delenv("MISTHELPER_STANDALONE", raising=False)
        with patch(
            "src.export.data_exporter.EnvironmentUtils.is_running_in_container",
            return_value=True,
        ):
            assert DataExporter._is_standalone_mode() is False


class TestShouldSkipPolyglot:
    def test_skip_when_no_api_name(self, monkeypatch):
        monkeypatch.setattr(de_module, "DB_LAYER_AVAILABLE", True)
        assert DataExporter._should_skip_polyglot(None) is True

    def test_skip_when_db_layer_unavailable(self, monkeypatch):
        monkeypatch.setattr(de_module, "DB_LAYER_AVAILABLE", False)
        assert DataExporter._should_skip_polyglot("listStuff") is True

    def test_skip_when_standalone(self, monkeypatch):
        monkeypatch.setattr(de_module, "DB_LAYER_AVAILABLE", True)
        with patch.object(DataExporter, "_is_standalone_mode", return_value=True):
            assert DataExporter._should_skip_polyglot("listStuff") is True

    def test_skip_when_router_none_after_init(self, monkeypatch):
        monkeypatch.setattr(de_module, "DB_LAYER_AVAILABLE", True)
        with (
            patch.object(DataExporter, "_is_standalone_mode", return_value=False),
            patch.object(DataExporter, "_init_router"),
        ):
            DataExporter._router = None
            assert DataExporter._should_skip_polyglot("listStuff") is True

    def test_do_not_skip_when_router_available(self, monkeypatch):
        monkeypatch.setattr(de_module, "DB_LAYER_AVAILABLE", True)
        with (
            patch.object(DataExporter, "_is_standalone_mode", return_value=False),
            patch.object(DataExporter, "_init_router"),
        ):
            DataExporter._router = MagicMock()
            assert DataExporter._should_skip_polyglot("listStuff") is False


class TestPerformPolyglotWrite:
    def test_success_logs_result(self):
        router = MagicMock()
        result = MagicMock()
        result.backend = "arango"
        result.records_written = 5
        result.records_failed = 0
        router.write.return_value = result
        DataExporter._router = router
        DataExporter._perform_polyglot_write([{"a": 1}], "listStuff")
        router.write.assert_called_once_with([{"a": 1}], "listStuff")

    def test_failure_swallowed(self):
        router = MagicMock()
        router.write.side_effect = RuntimeError("boom")
        DataExporter._router = router
        # Should not raise
        DataExporter._perform_polyglot_write([{"a": 1}], "listStuff")


class TestRouteToPolyglot:
    def test_skip_short_circuits(self):
        with (
            patch.object(DataExporter, "_should_skip_polyglot", return_value=True),
            patch.object(DataExporter, "_perform_polyglot_write") as perform,
        ):
            DataExporter._route_to_polyglot([{"a": 1}], "listStuff")
            perform.assert_not_called()

    def test_uses_raw_data_when_provided(self):
        raw = [{"raw": True}]
        with (
            patch.object(DataExporter, "_should_skip_polyglot", return_value=False),
            patch.object(DataExporter, "_perform_polyglot_write") as perform,
        ):
            DataExporter._route_to_polyglot([{"a": 1}], "listStuff", raw_data=raw)
            perform.assert_called_once_with(raw, "listStuff")

    def test_falls_back_to_data_when_raw_data_none(self):
        with (
            patch.object(DataExporter, "_should_skip_polyglot", return_value=False),
            patch.object(DataExporter, "_perform_polyglot_write") as perform,
        ):
            DataExporter._route_to_polyglot([{"a": 1}], "listStuff", raw_data=None)
            perform.assert_called_once_with([{"a": 1}], "listStuff")


class TestCheckPeriodicSnapshot:
    def test_first_call_returns_true_and_records(self):
        # Default threshold is 3600s; use a small threshold so 1000-0=1000 exceeds it.
        with patch("src.export.data_exporter.time.time", return_value=1000.0):
            assert DataExporter._check_periodic_snapshot("listStuff", threshold_seconds=500.0) is True
        assert DataExporter._last_snapshot_times["listStuff"] == 1000.0

    def test_default_threshold_below_returns_false(self):
        # 1000 - 0 = 1000 < 3600 default -> False, timestamp not updated.
        with patch("src.export.data_exporter.time.time", return_value=1000.0):
            assert DataExporter._check_periodic_snapshot("listStuff") is False
        assert DataExporter._last_snapshot_times.get("listStuff", 0.0) == 0.0

    def test_below_threshold_returns_false(self):
        DataExporter._last_snapshot_times["listStuff"] = 900.0
        with patch("src.export.data_exporter.time.time", return_value=1000.0):
            assert DataExporter._check_periodic_snapshot("listStuff", threshold_seconds=200.0) is False
        assert DataExporter._last_snapshot_times["listStuff"] == 900.0

    def test_above_threshold_returns_true_and_updates(self):
        DataExporter._last_snapshot_times["listStuff"] = 100.0
        with patch("src.export.data_exporter.time.time", return_value=5000.0):
            assert DataExporter._check_periodic_snapshot("listStuff", threshold_seconds=1000.0) is True
        assert DataExporter._last_snapshot_times["listStuff"] == 5000.0


class TestValidateWriteInputs:
    def test_empty_data_rejected(self):
        assert DataExporter._validate_write_inputs([], "target", "csv") is False

    def test_bad_format_rejected(self):
        assert DataExporter._validate_write_inputs([{"a": 1}], "target", "xml") is False

    def test_valid_inputs_accepted_csv(self):
        assert DataExporter._validate_write_inputs([{"a": 1}], "target", "csv") is True

    def test_valid_inputs_accepted_sqlite(self):
        assert DataExporter._validate_write_inputs([{"a": 1}], "target", "sqlite") is True


class TestWriteCsvFormat:
    def test_appends_csv_extension_when_missing(self):
        with patch.object(DataExporter, "write_to_csv") as writer:
            assert DataExporter._write_csv_format([{"a": 1}], "target") is True
        writer.assert_called_once_with([{"a": 1}], "target.csv", fieldnames=None)

    def test_preserves_extension_when_present(self):
        with patch.object(DataExporter, "write_to_csv") as writer:
            assert DataExporter._write_csv_format([{"a": 1}], "target.csv") is True
        writer.assert_called_once_with([{"a": 1}], "target.csv", fieldnames=None)

    def test_passes_fieldnames_through(self):
        with patch.object(DataExporter, "write_to_csv") as writer:
            DataExporter._write_csv_format([{"a": 1}], "target", fieldnames=["a"])
        writer.assert_called_once_with([{"a": 1}], "target.csv", fieldnames=["a"])


class TestWriteSqliteFormat:
    def test_strips_csv_extension_for_table_name(self):
        writer_instance = MagicMock()
        writer_instance.write.return_value = True
        with patch("src.export.data_exporter.SQLiteDatabaseWriter", return_value=writer_instance) as writer_cls:
            ok = DataExporter._write_sqlite_format([{"a": 1}], "target.csv", "listStuff")
        assert ok is True
        writer_cls.assert_called_once_with([{"a": 1}], "target", "listStuff")

    def test_uses_bare_name_when_no_csv_extension(self):
        writer_instance = MagicMock()
        writer_instance.write.return_value = False
        with patch("src.export.data_exporter.SQLiteDatabaseWriter", return_value=writer_instance) as writer_cls:
            ok = DataExporter._write_sqlite_format([{"a": 1}], "target", None)
        assert ok is False
        writer_cls.assert_called_once_with([{"a": 1}], "target", None)


class TestWriteToCsv:
    def test_empty_data_short_circuits(self):
        with patch.object(DataExporter, "_resolve_csv_path") as resolver:
            DataExporter.write_to_csv([], "target.csv")
        resolver.assert_not_called()

    def test_full_flow_writes(self, monkeypatch):
        escaped = [{"a": 1, "b": 2}]
        monkeypatch.setattr(
            "src.export.data_exporter.DataProcessingUtils.escape_multiline",
            MagicMock(return_value=escaped),
        )
        monkeypatch.setattr(
            "src.export.data_exporter.DataProcessingUtils.get_unique_keys",
            MagicMock(return_value=["a", "b"]),
        )
        with (
            patch.object(DataExporter, "_resolve_csv_path", return_value="data/target.csv"),
            patch.object(DataExporter, "_write_csv_with_exception_handling") as handler,
        ):
            DataExporter.write_to_csv([{"a": 1, "b": 2}], "target.csv")
        handler.assert_called_once_with("data/target.csv", escaped, ["a", "b"])


class TestResolveCsvPath:
    def test_bare_filename_placed_under_data(self):
        with patch("os.makedirs") as mk:
            path = DataExporter._resolve_csv_path("target.csv")
        mk.assert_called_once_with("data", exist_ok=True)
        assert path.replace("\\", "/") == "data/target.csv"

    def test_absolute_path_honored(self):
        with patch("os.makedirs"):
            path = DataExporter._resolve_csv_path("/tmp/target.csv")
        assert path == "/tmp/target.csv"


class TestResolveCsvFields:
    def test_uses_caller_supplied_fields(self):
        assert DataExporter._resolve_csv_fields([{"a": 1}], ["a", "b"]) == ["a", "b"]

    def test_derives_fields_when_none(self, monkeypatch):
        monkeypatch.setattr(
            "src.export.data_exporter.DataProcessingUtils.get_unique_keys",
            MagicMock(return_value=["a", "b"]),
        )
        assert DataExporter._resolve_csv_fields([{"a": 1}], None) == ["a", "b"]


class TestEmitRows:
    def test_writes_every_row(self):
        writer = MagicMock()
        rows = [{"a": 1, "b": 2}, {"a": 3, "b": 4}, {"a": 5}, {"a": 6}]
        DataExporter._emit_rows(writer, rows, ["a", "b"])
        assert writer.writerow.call_count == 4
        # Missing key falls back to empty string
        writer.writerow.assert_any_call({"a": 5, "b": ""})


class TestWriteCsvOpenAndEmit:
    def test_opens_and_writes_header_and_rows(self):
        m_open = mock_open()
        with (
            patch("builtins.open", m_open),
            patch("csv.DictWriter") as writer_cls,
            patch.object(DataExporter, "_emit_rows") as emit,
        ):
            writer_instance = MagicMock()
            writer_cls.return_value = writer_instance
            DataExporter._write_csv_open_and_emit("path.csv", [{"a": 1}], ["a"])
        m_open.assert_called_once_with("path.csv", "w", newline="", encoding="utf-8")
        writer_instance.writeheader.assert_called_once()
        emit.assert_called_once_with(writer_instance, [{"a": 1}], ["a"])


class TestWriteCsvWithExceptionHandling:
    def test_success_passes_through(self):
        with patch.object(DataExporter, "_write_csv_open_and_emit") as inner:
            DataExporter._write_csv_with_exception_handling("p", [{"a": 1}], ["a"])
        inner.assert_called_once()

    def test_permission_error_reraises(self, capsys):
        with patch.object(DataExporter, "_write_csv_open_and_emit", side_effect=PermissionError("locked")):
            with pytest.raises(PermissionError):
                DataExporter._write_csv_with_exception_handling("p", [{"a": 1}], ["a"])
        captured = capsys.readouterr()
        assert "another program" in captured.out

    def test_os_error_reraises(self):
        with patch.object(DataExporter, "_write_csv_open_and_emit", side_effect=OSError("disk full")):
            with pytest.raises(OSError):
                DataExporter._write_csv_with_exception_handling("p", [{"a": 1}], ["a"])

    def test_unexpected_error_reraises(self):
        with patch.object(DataExporter, "_write_csv_open_and_emit", side_effect=RuntimeError("weird")):
            with pytest.raises(RuntimeError):
                DataExporter._write_csv_with_exception_handling("p", [{"a": 1}], ["a"])


class TestExportWithProcessing:
    def test_empty_data_returns_zero(self):
        assert DataExporter.export_with_processing([], "target") == 0

    def test_none_data_returns_zero(self):
        assert DataExporter.export_with_processing(None, "target") == 0

    def test_flow_calls_write_with_format_selection(self, monkeypatch):
        raw_rows = [{"a": 1, "b": 2}]
        flat = [{"a": 1, "b": 2, "flat": True}]
        escaped = [{"a": 1, "b": 2, "flat": True, "e": True}]
        monkeypatch.setattr(
            "src.export.data_exporter.DataProcessingUtils.flatten_nested_fields",
            MagicMock(return_value=flat),
        )
        monkeypatch.setattr(
            "src.export.data_exporter.DataProcessingUtils.escape_multiline",
            MagicMock(return_value=escaped),
        )
        with patch.object(DataExporter, "write_with_format_selection", return_value=True) as writer:
            count = DataExporter.export_with_processing(raw_rows, "target", api_function_name="listStuff")
        assert count == 1
        writer.assert_called_once()

    def test_write_failure_returns_zero(self, monkeypatch):
        monkeypatch.setattr(
            "src.export.data_exporter.DataProcessingUtils.flatten_nested_fields",
            MagicMock(return_value=[{"a": 1}]),
        )
        monkeypatch.setattr(
            "src.export.data_exporter.DataProcessingUtils.escape_multiline",
            MagicMock(return_value=[{"a": 1}]),
        )
        with patch.object(DataExporter, "write_with_format_selection", return_value=False):
            assert DataExporter.export_with_processing([{"a": 1}], "target") == 0

    def test_non_dict_entries_filtered_out(self, monkeypatch):
        monkeypatch.setattr(
            "src.export.data_exporter.DataProcessingUtils.flatten_nested_fields",
            MagicMock(side_effect=lambda rows: rows),
        )
        monkeypatch.setattr(
            "src.export.data_exporter.DataProcessingUtils.escape_multiline",
            MagicMock(side_effect=lambda rows: rows),
        )
        with patch.object(DataExporter, "write_with_format_selection", return_value=True) as writer:
            count = DataExporter.export_with_processing([{"a": 1}, "not a dict", 42, {"b": 2}], "target")
        assert count == 2
        # Ensure only dicts made it to the write
        rows_arg = writer.call_args.args[0]
        assert rows_arg == [{"a": 1}, {"b": 2}]


class TestSortRecords:
    def test_no_sort_key_preserves_order(self):
        rows = [{"a": 3}, {"a": 1}, {"a": 2}]
        assert DataExporter._sort_records(rows, None) == rows

    def test_sort_key_orders_records(self):
        rows = [{"a": 3}, {"a": 1}, {"a": 2}]
        assert DataExporter._sort_records(rows, "a") == [{"a": 1}, {"a": 2}, {"a": 3}]

    def test_missing_key_defaults_to_empty_string(self):
        rows = [{"a": "z"}, {"b": "y"}, {"a": "a"}]
        result = DataExporter._sort_records(rows, "a")
        # Missing "a" sorts before other values because "" < any non-empty string
        assert result[0] == {"b": "y"}


class TestFinalizeExport:
    def test_success_returns_processed_count(self):
        assert DataExporter._finalize_export(True, 42, "target") == 42

    def test_failure_returns_zero(self):
        assert DataExporter._finalize_export(False, 42, "target") == 0


class TestModuleImport:
    def test_module_reimportable(self):
        importlib.reload(de_module)
        assert hasattr(de_module, "DataExporter")
