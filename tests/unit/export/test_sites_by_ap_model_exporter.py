"""Unit tests for ``src.export.sites_by_ap_model_exporter.SitesByAPModelExporter``.

Why: Un-omitting this module from ``[tool.coverage.run].omit`` requires 100%
line + branch coverage across the 12 static methods that back menu 88 -- the
Sites by AP Model CSV export. Cross-class collaborators (APICoreFetchUtils,
InputUtils, ConfigUtils, DataExporter) are resolved lazily through
``importlib.import_module("MistHelper")``. Tests inject a fake ``MistHelper``
module via ``sys.modules`` to observe and control those interactions without
importing the monolith.
"""

from __future__ import annotations

import logging
import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def fake_mh(monkeypatch):
    """Install a fake MistHelper module for lazy importlib resolution.

    Why: SitesByAPModelExporter reads ``mh.APICoreFetchUtils``, ``mh.InputUtils``,
    ``mh.ConfigUtils``, and ``mh.DataExporter`` at call time. Replacing the module
    lets tests observe and control those interactions cleanly.
    """
    mh = ModuleType("MistHelper")
    mh.APICoreFetchUtils = MagicMock()
    mh.InputUtils = MagicMock()
    mh.ConfigUtils = MagicMock()
    mh.DataExporter = MagicMock()
    monkeypatch.setitem(sys.modules, "MistHelper", mh)
    return mh


class TestGetApModels:
    """Cover SitesByAPModelExporter._get_ap_models."""

    def test_filters_non_ap_devices_and_sorts_distinct_models(self, fake_mh):
        """Non-AP devices are dropped, and remaining models are returned distinct + sorted."""
        from src.export.sites_by_ap_model_exporter import SitesByAPModelExporter

        inventory = [
            {"type": "ap", "model": "AP45"},
            {"type": "ap", "model": "AP41"},
            {"type": "ap", "model": "AP45"},
            {"type": "switch", "model": "EX4300"},
            {"type": "ap", "model": ""},  # empty model -> excluded from models list
        ]
        fake_mh.APICoreFetchUtils.all_inventory_with_limit.return_value = inventory

        aps, models = SitesByAPModelExporter._get_ap_models("org1")

        assert len(aps) == 4  # 4 APs kept (including empty-model AP)
        assert all(d["type"] == "ap" for d in aps)
        assert models == ["AP41", "AP45"]  # sorted + distinct + empty dropped


class TestPrintModelOptions:
    """Cover SitesByAPModelExporter._print_model_options."""

    def test_prints_numbered_list_with_counts(self, caplog):
        """Prints a numbered list with per-model AP counts."""
        from src.export.sites_by_ap_model_exporter import SitesByAPModelExporter

        models = ["AP41", "AP45"]
        aps = [
            {"model": "AP41"},
            {"model": "AP45"},
            {"model": "AP45"},
        ]
        with caplog.at_level(logging.INFO):
            SitesByAPModelExporter._print_model_options(models, aps)

        messages = [r.getMessage() for r in caplog.records]
        assert any("Available AP models" in m for m in messages)
        assert any("1. AP41 (1 APs)" in m for m in messages)
        assert any("2. AP45 (2 APs)" in m for m in messages)


class TestResolveModelChoice:
    """Cover SitesByAPModelExporter._resolve_model_choice."""

    def test_valid_selection_returns_model(self):
        """1-based valid index returns the matching model string."""
        from src.export.sites_by_ap_model_exporter import SitesByAPModelExporter

        models = ["AP41", "AP45"]
        assert SitesByAPModelExporter._resolve_model_choice("2", models) == "AP45"

    def test_out_of_bounds_returns_none(self, caplog):
        """Out-of-range selection returns None (bounds check branch, no notice)."""
        from src.export.sites_by_ap_model_exporter import SitesByAPModelExporter

        models = ["AP41"]
        with caplog.at_level(logging.INFO):
            assert SitesByAPModelExporter._resolve_model_choice("5", models) is None
        assert not any("Invalid selection" in r.getMessage() for r in caplog.records)

    def test_zero_selection_returns_none(self, caplog):
        """Zero (1-based) becomes -1 index which is out of bounds -> None (no notice)."""
        from src.export.sites_by_ap_model_exporter import SitesByAPModelExporter

        models = ["AP41"]
        with caplog.at_level(logging.INFO):
            assert SitesByAPModelExporter._resolve_model_choice("0", models) is None
        assert not any("Invalid selection" in r.getMessage() for r in caplog.records)

    def test_non_numeric_returns_none(self, caplog):
        """Non-numeric input triggers ValueError branch -> None with error notice."""
        from src.export.sites_by_ap_model_exporter import SitesByAPModelExporter

        with caplog.at_level(logging.INFO):
            assert SitesByAPModelExporter._resolve_model_choice("abc", ["AP41"]) is None
        assert any("Invalid selection" in r.getMessage() for r in caplog.records)


class TestPromptModelSelection:
    """Cover SitesByAPModelExporter._prompt_model_selection."""

    def test_empty_input_cancels(self, fake_mh):
        """Empty (or whitespace) operator input returns None without resolving."""
        from src.export.sites_by_ap_model_exporter import SitesByAPModelExporter

        fake_mh.InputUtils.safe_input.return_value = "   "
        result = SitesByAPModelExporter._prompt_model_selection(["AP41"], [{"model": "AP41"}])

        assert result is None

    def test_valid_choice_returns_model(self, fake_mh):
        """Valid numeric choice returns the corresponding model."""
        from src.export.sites_by_ap_model_exporter import SitesByAPModelExporter

        fake_mh.InputUtils.safe_input.return_value = "1"
        result = SitesByAPModelExporter._prompt_model_selection(["AP41", "AP45"], [{"model": "AP41"}])

        assert result == "AP41"


class TestSplitAddress:
    """Cover SitesByAPModelExporter._split_address."""

    def test_happy_path_full_address(self):
        """A well-formed address is split into street/city/state/zip/country."""
        from src.export.sites_by_ap_model_exporter import SitesByAPModelExporter

        result = SitesByAPModelExporter._split_address("123 Main St, Sunnyvale, CA 94089, USA")
        assert result == ("123 Main St", "Sunnyvale", "CA", "94089", "USA")

    def test_short_address_falls_back(self):
        """Address that can't be split raises IndexError -> fallback to (addr, "", "", "", "")."""
        from src.export.sites_by_ap_model_exporter import SitesByAPModelExporter

        result = SitesByAPModelExporter._split_address("just a street")
        assert result == ("just a street", "", "", "", "")

    def test_empty_address_falls_back(self):
        """Empty address hits the exception branch and returns the fallback tuple."""
        from src.export.sites_by_ap_model_exporter import SitesByAPModelExporter

        result = SitesByAPModelExporter._split_address("")
        assert result == ("", "", "", "", "")


class TestGroupApsBySite:
    """Cover SitesByAPModelExporter._group_aps_by_site."""

    def test_groups_matching_model_by_site_id(self):
        """Only APs matching model AND having a site_id are grouped by site_id."""
        from src.export.sites_by_ap_model_exporter import SitesByAPModelExporter

        aps = [
            {"model": "AP41", "site_id": "s1", "mac": "aa"},
            {"model": "AP41", "site_id": "s1", "mac": "bb"},
            {"model": "AP41", "site_id": "s2", "mac": "cc"},
            {"model": "AP45", "site_id": "s1", "mac": "dd"},  # model mismatch -> skipped
            {"model": "AP41", "site_id": None, "mac": "ee"},  # no site_id -> skipped
        ]
        grouped = SitesByAPModelExporter._group_aps_by_site(aps, "AP41")

        assert set(grouped.keys()) == {"s1", "s2"}
        assert len(grouped["s1"]) == 2
        assert len(grouped["s2"]) == 1


class TestBuildSiteRow:
    """Cover SitesByAPModelExporter._build_site_row."""

    def test_row_has_all_fields_including_macs_joined(self):
        """Row includes site name, model, count, address parts, and comma-joined MACs."""
        from src.export.sites_by_ap_model_exporter import SitesByAPModelExporter

        devices = [{"mac": "aabbcc"}, {"mac": "ddeeff"}]
        site_map = {"s1": {"name": "HQ", "address": "1 Way, City, CA 90000, USA"}}
        row = SitesByAPModelExporter._build_site_row("s1", devices, "AP41", site_map)

        assert row["site_id"] == "s1"
        assert row["site_name"] == "HQ"
        assert row["ap_model"] == "AP41"
        assert row["ap_count"] == 2
        assert row["address"] == "1 Way"
        assert row["city"] == "City"
        assert row["state"] == "CA"
        assert row["zip"] == "90000"
        assert row["country"] == "USA"
        assert row["ap_macs"] == "aabbcc, ddeeff"

    def test_missing_site_uses_empty_defaults(self):
        """Site missing from map -> empty name and empty address parts."""
        from src.export.sites_by_ap_model_exporter import SitesByAPModelExporter

        row = SitesByAPModelExporter._build_site_row("s99", [{"mac": "aa"}], "AP41", {})

        assert row["site_name"] == ""
        assert row["address"] == ""


class TestBuildExportRows:
    """Cover SitesByAPModelExporter._build_export_rows."""

    def test_rows_sorted_by_site_name(self):
        """Rows are grouped by site and ordered alphabetically by site name."""
        from src.export.sites_by_ap_model_exporter import SitesByAPModelExporter

        aps = [
            {"model": "AP41", "site_id": "sB", "mac": "bb"},
            {"model": "AP41", "site_id": "sA", "mac": "aa"},
        ]
        site_map = {
            "sA": {"name": "Alpha", "address": ""},
            "sB": {"name": "Beta", "address": ""},
        }
        rows = SitesByAPModelExporter._build_export_rows(aps, "AP41", site_map)

        assert [r["site_name"] for r in rows] == ["Alpha", "Beta"]


class TestBuildSiteMap:
    """Cover SitesByAPModelExporter._build_site_map."""

    def test_indexes_sites_by_id_and_skips_missing_id(self):
        """Entries without an ``id`` are skipped; others are indexed by id."""
        from src.export.sites_by_ap_model_exporter import SitesByAPModelExporter

        sites = [
            {"id": "s1", "name": "HQ"},
            {"name": "Unregistered"},  # no id -> dropped
            {"id": "s2", "name": "Branch"},
        ]
        result = SitesByAPModelExporter._build_site_map(sites)

        assert set(result.keys()) == {"s1", "s2"}
        assert result["s1"]["name"] == "HQ"


class TestFinalizeApModelExport:
    """Cover SitesByAPModelExporter._finalize_ap_model_export."""

    def test_slugifies_model_and_writes_csv(self, fake_mh, caplog):
        """Model name is slugified for filename, DataExporter is called, summary is logged."""
        from src.export.sites_by_ap_model_exporter import SitesByAPModelExporter

        rows = [{"site_id": "s1"}]
        with caplog.at_level(logging.INFO):
            SitesByAPModelExporter._finalize_ap_model_export(rows, "AP-45 / Special!")

        fake_mh.DataExporter.write_with_format_selection.assert_called_once()
        call = fake_mh.DataExporter.write_with_format_selection.call_args
        assert call.args[0] == rows
        # Slugified: non-alphanumeric (except _-) become underscores
        assert call.args[1] == "SitesByAPModel_AP-45___Special_.csv"
        assert call.kwargs.get("api_function_name") == "getSitesByAPModel"

        assert any("Exported 1 sites" in r.getMessage() for r in caplog.records)


class TestExportSitesByApModel:
    """Cover SitesByAPModelExporter.export_sites_by_ap_model (public entry)."""

    def test_no_models_returns_early(self, fake_mh, caplog, monkeypatch):
        """Empty AP inventory -> tells the user and returns before prompting."""
        from src.export.sites_by_ap_model_exporter import SitesByAPModelExporter

        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org1"
        monkeypatch.setattr(
            SitesByAPModelExporter,
            "_get_ap_models",
            staticmethod(lambda org_id: ([], [])),
        )
        prompt = MagicMock()
        monkeypatch.setattr(SitesByAPModelExporter, "_prompt_model_selection", staticmethod(prompt))

        with caplog.at_level(logging.INFO):
            SitesByAPModelExporter.export_sites_by_ap_model()

        assert any("No APs found" in r.getMessage() for r in caplog.records)
        prompt.assert_not_called()

    def test_operator_cancels_prompt(self, fake_mh, monkeypatch):
        """Prompt returns None -> abort before fetching sites."""
        from src.export.sites_by_ap_model_exporter import SitesByAPModelExporter

        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org1"
        monkeypatch.setattr(
            SitesByAPModelExporter,
            "_get_ap_models",
            staticmethod(lambda org_id: ([{"model": "AP41"}], ["AP41"])),
        )
        monkeypatch.setattr(
            SitesByAPModelExporter,
            "_prompt_model_selection",
            staticmethod(lambda models, aps: None),
        )
        SitesByAPModelExporter.export_sites_by_ap_model()

        fake_mh.APICoreFetchUtils.all_sites_with_limit.assert_not_called()

    def test_no_matching_rows_returns_early(self, fake_mh, caplog, monkeypatch):
        """Prompt returns model but no sites match -> notice + no CSV write."""
        from src.export.sites_by_ap_model_exporter import SitesByAPModelExporter

        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org1"
        fake_mh.APICoreFetchUtils.all_sites_with_limit.return_value = [{"id": "s1", "name": "HQ"}]

        monkeypatch.setattr(
            SitesByAPModelExporter,
            "_get_ap_models",
            staticmethod(lambda org_id: ([{"model": "AP41", "site_id": "s99"}], ["AP41"])),
        )
        monkeypatch.setattr(
            SitesByAPModelExporter,
            "_prompt_model_selection",
            staticmethod(lambda models, aps: "AP41"),
        )
        monkeypatch.setattr(
            SitesByAPModelExporter,
            "_build_export_rows",
            staticmethod(lambda aps, model, site_map: []),
        )
        finalize = MagicMock()
        monkeypatch.setattr(SitesByAPModelExporter, "_finalize_ap_model_export", staticmethod(finalize))

        with caplog.at_level(logging.INFO):
            SitesByAPModelExporter.export_sites_by_ap_model()

        assert any("No sites found with AP41" in r.getMessage() for r in caplog.records)
        finalize.assert_not_called()

    def test_success_path_writes_csv(self, fake_mh, monkeypatch):
        """Happy path: models found, model chosen, rows built -> finalize called."""
        from src.export.sites_by_ap_model_exporter import SitesByAPModelExporter

        fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org1"
        fake_mh.APICoreFetchUtils.all_sites_with_limit.return_value = [{"id": "s1", "name": "HQ"}]

        rows = [{"site_id": "s1"}]
        monkeypatch.setattr(
            SitesByAPModelExporter,
            "_get_ap_models",
            staticmethod(lambda org_id: ([{"model": "AP41", "site_id": "s1"}], ["AP41"])),
        )
        monkeypatch.setattr(
            SitesByAPModelExporter,
            "_prompt_model_selection",
            staticmethod(lambda models, aps: "AP41"),
        )
        monkeypatch.setattr(
            SitesByAPModelExporter,
            "_build_export_rows",
            staticmethod(lambda aps, model, site_map: rows),
        )
        finalize = MagicMock()
        monkeypatch.setattr(SitesByAPModelExporter, "_finalize_ap_model_export", staticmethod(finalize))

        SitesByAPModelExporter.export_sites_by_ap_model()

        finalize.assert_called_once_with(rows, "AP41")
