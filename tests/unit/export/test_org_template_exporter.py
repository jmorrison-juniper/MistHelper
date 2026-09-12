"""Unit tests for ``src.export.org_template_exporter.OrgTemplateExporter``.

Why: Exercises every branch of the 9 static methods so that un-omitting the
module in ``[tool.coverage.run].omit`` keeps overall coverage above the 90%
gate. The module resolves cross-class collaborators lazily via
``importlib.import_module("MistHelper")``; tests inject a fake ``MistHelper``
module via ``sys.modules`` monkeypatching to control those interactions.
"""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def fake_mh(monkeypatch):
    """Install a fake MistHelper module for lazy importlib resolution.

    Why: OrgTemplateExporter uses ``importlib.import_module("MistHelper")``
    inside each method to fetch APIDataFetcher, OrgExportUtils, ConfigUtils,
    DataExporter, and apisession. Replacing the module lets tests observe and
    control these interactions without importing the real monolith.
    """
    mh = ModuleType("MistHelper")
    mh.APIDataFetcher = MagicMock()
    mh.OrgExportUtils = MagicMock()
    mh.ConfigUtils = MagicMock()
    mh.DataExporter = MagicMock()
    mh.apisession = MagicMock()
    monkeypatch.setitem(sys.modules, "MistHelper", mh)
    return mh


class TestTemplateExportSpecs:
    """Cover OrgTemplateExporter._template_export_specs."""

    def test_returns_five_specs(self):
        """Returns a spec tuple for gateway, network, RF, site, and AP templates."""
        from src.export.org_template_exporter import OrgTemplateExporter

        specs = OrgTemplateExporter._template_export_specs()

        assert len(specs) == 5
        titles = [s[0] for s in specs]
        assert titles == [
            "Gateway Templates:",
            "Network Templates:",
            "RF Templates:",
            "Site Templates:",
            "AP Templates:",
        ]
        filenames = [s[2] for s in specs]
        assert "OrgGatewayTemplates.csv" in filenames
        assert "OrgApTemplates.csv" in filenames


class TestExportOneTemplate:
    """Cover OrgTemplateExporter._export_one_template."""

    def test_success_calls_api_data_fetcher(self, fake_mh):
        """Happy path invokes APIDataFetcher(...).execute() with the given spec."""
        from src.export.org_template_exporter import OrgTemplateExporter

        api_call = MagicMock()
        OrgTemplateExporter._export_one_template("Title:", api_call, "File.csv", "label")

        fake_mh.APIDataFetcher.assert_called_once_with(
            title="Title:", api_call=api_call, filename="File.csv", sort_key="name", limit=1000
        )
        fake_mh.APIDataFetcher.return_value.execute.assert_called_once()

    def test_exception_is_logged_not_raised(self, fake_mh):
        """APIDataFetcher failure is logged but does not propagate — other types keep exporting."""
        from src.export.org_template_exporter import OrgTemplateExporter

        fake_mh.APIDataFetcher.return_value.execute.side_effect = RuntimeError("boom")
        # Should not raise.
        OrgTemplateExporter._export_one_template("Title:", MagicMock(), "File.csv", "label")


class TestAllTemplates:
    """Cover OrgTemplateExporter.all_templates."""

    def test_iterates_all_specs(self, fake_mh):
        """all_templates delegates to _export_one_template once per spec."""
        from src.export.org_template_exporter import OrgTemplateExporter

        with patch.object(OrgTemplateExporter, "_export_one_template") as exp:
            OrgTemplateExporter.all_templates()

        assert exp.call_count == 5


class TestNetworkTemplates:
    """Cover OrgTemplateExporter.network_templates."""

    def test_delegates_to_org_export_utils(self, fake_mh):
        """Delegates to mh.OrgExportUtils.export_data with network templates data_type."""
        from src.export.org_template_exporter import OrgTemplateExporter

        OrgTemplateExporter.network_templates()

        fake_mh.OrgExportUtils.export_data.assert_called_once()
        kwargs = fake_mh.OrgExportUtils.export_data.call_args.kwargs
        assert kwargs["data_type"] == "network templates"
        assert kwargs["sort_key"] == "name"


class TestRfTemplates:
    """Cover OrgTemplateExporter.rf_templates."""

    def test_delegates_to_org_export_utils(self, fake_mh):
        """Delegates to mh.OrgExportUtils.export_data with rf templates data_type."""
        from src.export.org_template_exporter import OrgTemplateExporter

        OrgTemplateExporter.rf_templates()

        fake_mh.OrgExportUtils.export_data.assert_called_once()
        kwargs = fake_mh.OrgExportUtils.export_data.call_args.kwargs
        assert kwargs["data_type"] == "rf templates"


class TestPersistApTemplateProfiles:
    """Cover OrgTemplateExporter._persist_ap_template_profiles."""

    def test_empty_writes_empty_csv(self, fake_mh):
        """Empty profile list writes an empty file to keep output consistent."""
        from src.export.org_template_exporter import OrgTemplateExporter

        OrgTemplateExporter._persist_ap_template_profiles([], "OrgApTemplates.csv")

        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with([], "OrgApTemplates.csv")

    def test_non_empty_flattens_and_writes(self, fake_mh):
        """Non-empty list flows through flatten/escape/write."""
        from src.export.org_template_exporter import OrgTemplateExporter

        profiles = [{"id": "p1"}]
        with patch("src.export.org_template_exporter.DataProcessingUtils") as dpu:
            dpu.flatten_nested_fields.return_value = profiles
            dpu.escape_multiline.return_value = profiles
            OrgTemplateExporter._persist_ap_template_profiles(profiles, "OrgApTemplates.csv")

        dpu.flatten_nested_fields.assert_called_once_with(profiles)
        dpu.escape_multiline.assert_called_once_with(profiles)
        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(profiles, "OrgApTemplates.csv")


class TestApTemplates:
    """Cover OrgTemplateExporter.ap_templates."""

    def test_happy_path_persists_profiles(self, fake_mh):
        """Fetches ap-type deviceprofiles, pages them, delegates to _persist."""
        from src.export.org_template_exporter import OrgTemplateExporter

        profiles = [{"id": "ap1"}]
        with (
            patch(
                "src.export.org_template_exporter.mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles",
                return_value=MagicMock(),
            ) as api,
            patch("src.export.org_template_exporter.mistapi.get_all", return_value=profiles),
            patch.object(OrgTemplateExporter, "_persist_ap_template_profiles") as persist,
        ):
            fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org1"
            OrgTemplateExporter.ap_templates()

        api.assert_called_once()
        persist.assert_called_once_with(profiles, "OrgApTemplates.csv")

    def test_get_all_none_becomes_empty_list(self, fake_mh):
        """mistapi.get_all returning None is coerced to [] via `or []`."""
        from src.export.org_template_exporter import OrgTemplateExporter

        with (
            patch(
                "src.export.org_template_exporter.mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles",
                return_value=MagicMock(),
            ),
            patch("src.export.org_template_exporter.mistapi.get_all", return_value=None),
            patch.object(OrgTemplateExporter, "_persist_ap_template_profiles") as persist,
        ):
            OrgTemplateExporter.ap_templates()

        persist.assert_called_once_with([], "OrgApTemplates.csv")

    def test_exception_writes_empty_and_reraises(self, fake_mh):
        """API failure writes empty CSV best-effort and re-raises."""
        from src.export.org_template_exporter import OrgTemplateExporter

        with (
            patch(
                "src.export.org_template_exporter.mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles",
                side_effect=RuntimeError("api down"),
            ),
            pytest.raises(RuntimeError, match="api down"),
        ):
            OrgTemplateExporter.ap_templates()

        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with([], "OrgApTemplates.csv")

    def test_exception_and_cleanup_swallows_secondary_error(self, fake_mh):
        """Best-effort empty-write failure is swallowed; original error still re-raises."""
        from src.export.org_template_exporter import OrgTemplateExporter

        fake_mh.DataExporter.write_with_format_selection.side_effect = OSError("disk full")
        with (
            patch(
                "src.export.org_template_exporter.mistapi.api.v1.orgs.deviceprofiles.listOrgDeviceProfiles",
                side_effect=RuntimeError("api down"),
            ),
            pytest.raises(RuntimeError, match="api down"),
        ):
            OrgTemplateExporter.ap_templates()


class TestPersistSwitchTemplateCsv:
    """Cover OrgTemplateExporter._persist_switch_template_csv."""

    def test_empty_writes_empty_csv(self, fake_mh):
        """Empty list writes an empty CSV for output consistency."""
        from src.export.org_template_exporter import OrgTemplateExporter

        OrgTemplateExporter._persist_switch_template_csv([], "OrgSwitchTemplates.csv")

        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with([], "OrgSwitchTemplates.csv")

    def test_non_empty_flattens_and_writes(self, fake_mh):
        """Non-empty list flows through flatten/escape/write."""
        from src.export.org_template_exporter import OrgTemplateExporter

        profiles = [{"id": "sw1"}]
        with patch("src.export.org_template_exporter.DataProcessingUtils") as dpu:
            dpu.flatten_nested_fields.return_value = profiles
            dpu.escape_multiline.return_value = profiles
            OrgTemplateExporter._persist_switch_template_csv(profiles, "OrgSwitchTemplates.csv")

        dpu.flatten_nested_fields.assert_called_once_with(profiles)
        dpu.escape_multiline.assert_called_once_with(profiles)
        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with(profiles, "OrgSwitchTemplates.csv")


class TestSwitchTemplates:
    """Cover OrgTemplateExporter.switch_templates."""

    def test_happy_path_persists_profiles(self, fake_mh):
        """Fetches networktemplates, pages them, delegates to _persist."""
        from src.export.org_template_exporter import OrgTemplateExporter

        profiles = [{"id": "sw1"}]
        with (
            patch(
                "src.export.org_template_exporter.mistapi.api.v1.orgs.networktemplates.listOrgNetworkTemplates",
                return_value=MagicMock(),
            ) as api,
            patch("src.export.org_template_exporter.mistapi.get_all", return_value=profiles),
            patch.object(OrgTemplateExporter, "_persist_switch_template_csv") as persist,
        ):
            fake_mh.ConfigUtils.get_cached_or_prompted_org_id.return_value = "org1"
            OrgTemplateExporter.switch_templates()

        api.assert_called_once()
        persist.assert_called_once_with(profiles, "OrgSwitchTemplates.csv")

    def test_get_all_none_becomes_empty_list(self, fake_mh):
        """mistapi.get_all returning None is coerced to [] via `or []`."""
        from src.export.org_template_exporter import OrgTemplateExporter

        with (
            patch(
                "src.export.org_template_exporter.mistapi.api.v1.orgs.networktemplates.listOrgNetworkTemplates",
                return_value=MagicMock(),
            ),
            patch("src.export.org_template_exporter.mistapi.get_all", return_value=None),
            patch.object(OrgTemplateExporter, "_persist_switch_template_csv") as persist,
        ):
            OrgTemplateExporter.switch_templates()

        persist.assert_called_once_with([], "OrgSwitchTemplates.csv")

    def test_exception_writes_empty_and_reraises(self, fake_mh):
        """API failure writes empty CSV best-effort and re-raises."""
        from src.export.org_template_exporter import OrgTemplateExporter

        with (
            patch(
                "src.export.org_template_exporter.mistapi.api.v1.orgs.networktemplates.listOrgNetworkTemplates",
                side_effect=RuntimeError("api down"),
            ),
            pytest.raises(RuntimeError, match="api down"),
        ):
            OrgTemplateExporter.switch_templates()

        fake_mh.DataExporter.write_with_format_selection.assert_called_once_with([], "OrgSwitchTemplates.csv")

    def test_exception_and_cleanup_swallows_secondary_error(self, fake_mh):
        """Best-effort empty-write failure is swallowed; original error still re-raises."""
        from src.export.org_template_exporter import OrgTemplateExporter

        fake_mh.DataExporter.write_with_format_selection.side_effect = OSError("disk full")
        with (
            patch(
                "src.export.org_template_exporter.mistapi.api.v1.orgs.networktemplates.listOrgNetworkTemplates",
                side_effect=RuntimeError("api down"),
            ),
            pytest.raises(RuntimeError, match="api down"),
        ):
            OrgTemplateExporter.switch_templates()
