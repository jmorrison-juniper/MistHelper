"""Wave 5 P2 coverage for src/inventory/inventory_summary/pivot_renderer.py (initiative #1018).

Covers every static method of ``PivotRenderer``:
- ``render``: orchestrator delegates to compute/build/print/emit with expected args.
- ``_populate_pivot``: writes ``pivot[model][version] = count`` for each row.
- ``_compute_pivot``: sorts models + versions, builds model_type map, delegates to _populate_pivot.
- ``_update_row_and_columns``: returns dense row counts + row total and mutates col_totals in place.
- ``_build_table``: composes PrettyTable + export rows + grand total; footer TOTAL row appended.
- ``_build_export_row``: emits CSV-shaped dict with dense zero-filled columns.
- ``_print_table``: prints the legacy banner + PrettyTable.
- ``_emit_export``: delegates to ``_parent.DataExporter.write_with_format_selection`` with stable field order.

Uses monkeypatch to swap ``_parent.DataExporter`` for a mock and capsys for stdout assertions.
No live network, no disk I/O. MagicMock(spec=...) mandatory on injected doubles.
"""

from __future__ import annotations  # WHY: PEP 604 unions in test type hints.

import logging  # WHY: caplog verification of pre/post-action log lines.
from unittest.mock import MagicMock, patch  # WHY: spec= mocks + patch decorators.

import pytest  # WHY: monkeypatch + capsys + caplog fixtures.
from prettytable import PrettyTable  # WHY: verify _build_table returns a real PrettyTable.

from src.inventory import org_device_inventory_summary as _parent  # WHY: DI slot patched here.
from src.inventory.inventory_summary.pivot_renderer import PivotRenderer  # WHY: SUT direct import.


def _sample_rows() -> list[dict]:
    """Build a small 2-model x 2-version dataset with dense counts (no missing cells)."""
    return [
        {"model": "AP32", "version": "0.14", "device_type": "ap", "count": 3},  # WHY: model A, ver A.
        {"model": "AP32", "version": "0.15", "device_type": "ap", "count": 5},  # WHY: model A, ver B.
        {"model": "SW1", "version": "0.14", "device_type": "switch", "count": 2},  # WHY: model B, ver A.
        {"model": "SW1", "version": "0.15", "device_type": "switch", "count": 7},  # WHY: model B, ver B.
    ]


class TestPopulatePivot:
    """``_populate_pivot`` writes each row's count into ``pivot[model][version]``."""

    def test_fills_all_cells(self) -> None:
        """Every input row lands in the pre-allocated model bucket."""
        rows = _sample_rows()
        pivot: dict[str, dict[str, int]] = {"AP32": {}, "SW1": {}}  # WHY: pre-allocated buckets.
        PivotRenderer._populate_pivot(rows, pivot)
        assert pivot == {
            "AP32": {"0.14": 3, "0.15": 5},
            "SW1": {"0.14": 2, "0.15": 7},
        }  # WHY: SUT stores raw count under (model, version).

    def test_missing_count_defaults_to_zero(self) -> None:
        """Rows without a 'count' key default to 0 (dict.get default)."""
        rows = [{"model": "M", "version": "V", "device_type": "ap"}]  # WHY: no count key.
        pivot: dict[str, dict[str, int]] = {"M": {}}
        PivotRenderer._populate_pivot(rows, pivot)
        assert pivot == {"M": {"V": 0}}  # WHY: default 0 fallback.


class TestComputePivot:
    """``_compute_pivot`` returns sorted axes, model_type map, and nested pivot dict."""

    def test_returns_sorted_axes_and_pivot(self) -> None:
        """Models and versions are sorted; pivot mirrors the sample counts."""
        models, versions, model_type, pivot = PivotRenderer._compute_pivot(_sample_rows())
        assert models == ["AP32", "SW1"]  # WHY: sorted alphabetically.
        assert versions == ["0.14", "0.15"]  # WHY: sorted alphabetically.
        assert model_type == {"AP32": "ap", "SW1": "switch"}  # WHY: model -> device_type map.
        assert pivot == {
            "AP32": {"0.14": 3, "0.15": 5},
            "SW1": {"0.14": 2, "0.15": 7},
        }  # WHY: nested count map.

    def test_empty_rows_returns_empty_structures(self) -> None:
        """No input rows → empty axes and empty pivot dict."""
        models, versions, model_type, pivot = PivotRenderer._compute_pivot([])
        assert models == []  # WHY: no models discovered.
        assert versions == []  # WHY: no versions discovered.
        assert model_type == {}  # WHY: no mapping.
        assert pivot == {}  # WHY: no pre-allocated buckets.


class TestUpdateRowAndColumns:
    """``_update_row_and_columns`` returns (row_counts, row_total) and mutates col_totals in place."""

    def test_returns_row_counts_and_updates_col_totals(self) -> None:
        """Row counts follow version order; col_totals accumulate contribution."""
        pivot = {"AP32": {"0.14": 3, "0.15": 5}}  # WHY: sample model bucket.
        versions = ["0.14", "0.15"]  # WHY: version order dictates dense row layout.
        col_totals = {"0.14": 10, "0.15": 20}  # WHY: pre-existing totals to prove in-place mutation.
        row_counts, row_total = PivotRenderer._update_row_and_columns("AP32", versions, pivot, col_totals)
        assert row_counts == [3, 5]  # WHY: dense counts in version order.
        assert row_total == 8  # WHY: sum of row_counts.
        assert col_totals == {"0.14": 13, "0.15": 25}  # WHY: original totals + this row's contribution.

    def test_missing_versions_default_to_zero(self) -> None:
        """Versions absent from pivot[model] contribute 0 (dict.get default)."""
        pivot: dict[str, dict[str, int]] = {"AP32": {}}  # WHY: no cells for AP32.
        versions = ["0.14", "0.15"]
        col_totals = {"0.14": 0, "0.15": 0}
        row_counts, row_total = PivotRenderer._update_row_and_columns("AP32", versions, pivot, col_totals)
        assert row_counts == [0, 0]  # WHY: missing cells default to 0.
        assert row_total == 0  # WHY: sum of zeros.
        assert col_totals == {"0.14": 0, "0.15": 0}  # WHY: unchanged.


class TestBuildTable:
    """``_build_table`` composes PrettyTable + export rows + grand total; footer row appended."""

    def test_full_dataset_produces_expected_artifacts(self) -> None:
        """Two-model dataset yields 3 rows (2 models + TOTAL footer), matching export rows, grand=17."""
        models, versions, model_type, pivot = PivotRenderer._compute_pivot(_sample_rows())
        table, export_rows, grand_total = PivotRenderer._build_table(models, versions, model_type, pivot)
        assert isinstance(table, PrettyTable)  # WHY: real PrettyTable returned.
        assert table.field_names == ["Model", "0.14", "0.15", "Total"]  # WHY: header shape.
        assert len(table.rows) == 3  # WHY: 2 model rows + 1 TOTAL footer.
        assert table.rows[0] == ["AP32", 3, 5, 8]  # WHY: first model row.
        assert table.rows[1] == ["SW1", 2, 7, 9]  # WHY: second model row.
        assert table.rows[2] == ["TOTAL", 5, 12, 17]  # WHY: footer row with column totals + grand.
        assert grand_total == 17  # WHY: sum of all counts = 3+5+2+7.
        assert len(export_rows) == 2  # WHY: one export row per model (no TOTAL row in export).
        assert export_rows[0] == {
            "Model": "AP32",
            "Device Type": "ap",
            "0.14": 3,
            "0.15": 5,
            "Total": 8,
        }  # WHY: legacy CSV shape.

    def test_empty_dataset_returns_only_total_footer(self) -> None:
        """No models means only the TOTAL footer row (with 0 grand) and empty export list."""
        table, export_rows, grand_total = PivotRenderer._build_table([], [], {}, {})
        assert table.field_names == ["Model", "Total"]  # WHY: no version columns.
        assert len(table.rows) == 1  # WHY: only the TOTAL footer.
        assert table.rows[0] == ["TOTAL", 0]  # WHY: no columns, grand=0.
        assert export_rows == []  # WHY: no data rows to export.
        assert grand_total == 0  # WHY: sum of no counts.


class TestBuildExportRow:
    """``_build_export_row`` emits a CSV-shaped dict with dense zero-filled version columns."""

    def test_full_row_shape(self) -> None:
        """All keys present in correct order; missing cells default to 0."""
        pivot = {"AP32": {"0.14": 3}}  # WHY: only 0.14 present; 0.15 must default to 0.
        model_type = {"AP32": "ap"}
        row = PivotRenderer._build_export_row("AP32", model_type, ["0.14", "0.15"], pivot, row_total=3)
        assert row == {
            "Model": "AP32",
            "Device Type": "ap",
            "0.14": 3,
            "0.15": 0,
            "Total": 3,
        }  # WHY: legacy CSV column shape with dense zero fill.

    def test_missing_model_type_defaults_to_empty_string(self) -> None:
        """Unknown model gets empty-string Device Type (dict.get default)."""
        row = PivotRenderer._build_export_row("Unknown", {}, ["0.14"], {"Unknown": {"0.14": 1}}, row_total=1)
        assert row["Device Type"] == ""  # WHY: fallback per SUT.


class TestPrintTable:
    """``_print_table`` prints the legacy banner + PrettyTable to stdout."""

    def test_prints_banner_and_table(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Banner text and the model row content must both appear in stdout."""
        models, versions, model_type, pivot = PivotRenderer._compute_pivot(_sample_rows())
        table, _export_rows, _grand_total = PivotRenderer._build_table(models, versions, model_type, pivot)
        PivotRenderer._print_table(table)
        out = capsys.readouterr().out
        assert "Version Distribution per Model (All Device Types)" in out  # WHY: banner label.
        assert "AP32" in out  # WHY: model row rendered.
        assert "TOTAL" in out  # WHY: footer row rendered.
        assert "=" * 62 in out  # WHY: legacy banner rule char-count preserved.


class TestEmitExport:
    """``_emit_export`` delegates to ``_parent.DataExporter.write_with_format_selection``."""

    def test_delegates_with_ordered_fieldnames(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Fieldnames order = Model, Device Type, versions..., Total; api name is fixed."""
        fake_exporter = MagicMock(spec=object)  # WHY: opaque stand-in for DataExporter.
        fake_exporter.write_with_format_selection = MagicMock(spec=object)  # WHY: mockable method attr.
        monkeypatch.setattr(_parent, "DataExporter", fake_exporter)  # WHY: swap DI slot on parent.

        export_rows = [{"Model": "AP32", "Device Type": "ap", "0.14": 3, "0.15": 5, "Total": 8}]
        with caplog.at_level(logging.DEBUG):
            PivotRenderer._emit_export(export_rows, ["0.14", "0.15"], "OrgVersionPerModel.csv")

        fake_exporter.write_with_format_selection.assert_called_once_with(
            export_rows,
            "OrgVersionPerModel.csv",
            api_function_name="orgDeviceVersionPerModel",
            fieldnames=["Model", "Device Type", "0.14", "0.15", "Total"],
        )  # WHY: exact SUT contract (fieldnames order, synthetic api name).
        assert "Exporting 1 pivot rows to OrgVersionPerModel.csv" in caplog.text  # WHY: pre-action info log.
        assert "Pivot export complete: OrgVersionPerModel.csv" in caplog.text  # WHY: post-action debug log.


class TestRender:
    """``render`` orchestrator: computes pivot, builds table, prints, emits export, logs summary."""

    def test_full_orchestration(
        self,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """End-to-end render call exercises compute→build→print→export path with all log lines."""
        fake_exporter = MagicMock(spec=object)  # WHY: intercept export delegation.
        fake_exporter.write_with_format_selection = MagicMock(spec=object)
        monkeypatch.setattr(_parent, "DataExporter", fake_exporter)

        with caplog.at_level(logging.DEBUG):
            PivotRenderer.render(_sample_rows(), "OrgVersionPerModel.csv")

        out = capsys.readouterr().out
        assert "Version Distribution per Model" in out  # WHY: banner reached.
        assert "AP32" in out and "SW1" in out  # WHY: both models printed.
        assert fake_exporter.write_with_format_selection.called  # WHY: export was invoked exactly once.
        assert (
            "Rendering version-per-model pivot for 4 rows -> OrgVersionPerModel.csv" in caplog.text
        )  # WHY: pre-action info log.
        assert "Pivot rendered: 2 models x 2 versions, grand_total=17" in caplog.text  # WHY: post-action debug log.

    def test_render_with_empty_rows_still_calls_export(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """render([]) still invokes export with an empty export list."""
        fake_exporter = MagicMock(spec=object)
        fake_exporter.write_with_format_selection = MagicMock(spec=object)
        monkeypatch.setattr(_parent, "DataExporter", fake_exporter)

        with patch.object(PivotRenderer, "_print_table") as fake_print:  # WHY: suppress banner in output.
            PivotRenderer.render([], "empty.csv")

        fake_print.assert_called_once()  # WHY: print step reached even with empty data.
        args, kwargs = fake_exporter.write_with_format_selection.call_args
        assert args[0] == []  # WHY: export_rows is empty.
        assert kwargs["fieldnames"] == ["Model", "Device Type", "Total"]  # WHY: no version cols.
