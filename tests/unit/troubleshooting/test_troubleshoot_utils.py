"""Unit tests for TroubleshootUtils delegator (initiative #878 / #1017 PR-1)."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest

from src.troubleshooting.troubleshoot_utils import TroubleshootUtils


@pytest.fixture(autouse=True)
def _capture_warnings(caplog):
    """Ensure caplog captures WARNING+ records for every test in this module.

    Why:
        After #886 slice 17/N, TroubleshootUtils emits user-visible menu and
        exit messages via ``logging.warning`` rather than ``print()``. Tests
        assert on those strings via ``caplog.text``; setting the level here
        keeps behavior deterministic across CI runners regardless of the
        default logger propagation state.
    """
    caplog.set_level(logging.WARNING)


@pytest.fixture
def mh_mocks(monkeypatch):
    """Patch every MistHelper attribute referenced by TroubleshootUtils lazy imports."""
    mocks = {
        "MarvisTroubleshootDeps": MagicMock(name="MarvisTroubleshootDeps"),
        "apisession": MagicMock(name="apisession"),
        "mistapi": MagicMock(name="mistapi"),
        "ConfigUtils": MagicMock(name="ConfigUtils"),
        "PromptClientUtils": MagicMock(name="PromptClientUtils"),
        "PromptUtils": MagicMock(name="PromptUtils"),
        "DataExporter": MagicMock(name="DataExporter"),
        "MarvisDataUtilsFactory": MagicMock(name="MarvisDataUtilsFactory"),
        "ExtractedMarvisTroubleshootUtils": MagicMock(name="ExtractedMarvisTroubleshootUtils"),
        "InputUtils": MagicMock(name="InputUtils"),
    }
    for attr, value in mocks.items():
        monkeypatch.setattr(f"MistHelper.{attr}", value, raising=False)
    mocks["MarvisDataUtilsFactory"].instance.return_value = MagicMock(name="marvis_data_utils_instance")
    mocks["ConfigUtils"].get_cached_or_prompted_org_id.return_value = "org-abc"
    return mocks


class TestBuildDeps:
    def test_composes_deps_with_all_kwargs(self, mh_mocks):
        result = TroubleshootUtils._build_deps()
        mh_mocks["MarvisTroubleshootDeps"].assert_called_once()
        kwargs = mh_mocks["MarvisTroubleshootDeps"].call_args.kwargs
        assert kwargs["apisession"] is mh_mocks["apisession"]
        assert kwargs["mistapi"] is mh_mocks["mistapi"]
        assert kwargs["config_utils"] is mh_mocks["ConfigUtils"]
        assert kwargs["prompt_client_utils"] is mh_mocks["PromptClientUtils"]
        assert kwargs["prompt_utils"] is mh_mocks["PromptUtils"]
        assert kwargs["data_exporter"] is mh_mocks["DataExporter"]
        assert kwargs["marvis_data_utils"] is mh_mocks["MarvisDataUtilsFactory"].instance.return_value
        # data_processing_utils is a direct import, not from mh
        from src.data.data_processing_utils import DataProcessingUtils

        assert kwargs["data_processing_utils"] is DataProcessingUtils
        assert result is mh_mocks["MarvisTroubleshootDeps"].return_value


class TestDelegations:
    def test_client_connectivity_delegates(self, mh_mocks):
        TroubleshootUtils.client_connectivity()
        mh_mocks["ExtractedMarvisTroubleshootUtils"].client_connectivity.assert_called_once()

    def test_device_performance_delegates(self, mh_mocks):
        TroubleshootUtils.device_performance()
        mh_mocks["ExtractedMarvisTroubleshootUtils"].device_performance.assert_called_once()

    def test_network_connectivity_delegates(self, mh_mocks):
        TroubleshootUtils.network_connectivity()
        mh_mocks["ExtractedMarvisTroubleshootUtils"].network_connectivity.assert_called_once()

    def test_view_insights_delegates(self, mh_mocks):
        TroubleshootUtils.view_insights()
        mh_mocks["ExtractedMarvisTroubleshootUtils"].view_insights.assert_called_once()

    def test_display_usage_guide_delegates(self, mh_mocks):
        TroubleshootUtils._display_usage_guide()
        mh_mocks["ExtractedMarvisTroubleshootUtils"]._display_usage_guide.assert_called_once()


class TestPrintHelpers:
    def test_print_marvis_menu_writes_header(self, caplog):
        TroubleshootUtils._print_marvis_menu()
        out = caplog.text
        assert "Marvis" in out
        assert "=" * 65 in out

    def test_print_marvis_options_lists_five(self, caplog):
        TroubleshootUtils._print_marvis_options()
        out = caplog.text
        for token in ("1.", "2.", "3.", "4.", "5."):
            assert token in out
        assert "Exit" in out


class TestHandlers:
    def test_invalid_choice_logs_warning(self, caplog):
        caplog.set_level(logging.WARNING)
        TroubleshootUtils._handle_marvis_invalid_choice("9")
        assert "Invalid option selected." in caplog.text
        assert "Invalid troubleshooting option selected" in caplog.text

    def test_exit_prints_message(self, caplog):
        TroubleshootUtils._handle_marvis_exit()
        assert "Exiting Marvis troubleshooting." in caplog.text


class TestInvokers:
    def test_invoke_client_connectivity(self, mh_mocks):
        TroubleshootUtils._invoke_marvis_client_connectivity()
        mh_mocks["ExtractedMarvisTroubleshootUtils"].client_connectivity.assert_called_once()

    def test_invoke_device_performance(self, mh_mocks):
        TroubleshootUtils._invoke_marvis_device_performance()
        mh_mocks["ExtractedMarvisTroubleshootUtils"].device_performance.assert_called_once()

    def test_invoke_network_connectivity(self, mh_mocks):
        TroubleshootUtils._invoke_marvis_network_connectivity()
        mh_mocks["ExtractedMarvisTroubleshootUtils"].network_connectivity.assert_called_once()

    def test_invoke_view_insights(self, mh_mocks):
        TroubleshootUtils._invoke_marvis_view_insights()
        mh_mocks["ExtractedMarvisTroubleshootUtils"].view_insights.assert_called_once()


class TestDispatchMarvisChoice:
    @pytest.mark.parametrize(
        ("choice", "attr"),
        [
            ("1", "client_connectivity"),
            ("2", "device_performance"),
            ("3", "network_connectivity"),
            ("4", "view_insights"),
        ],
    )
    def test_valid_choices_dispatch(self, mh_mocks, choice, attr):
        TroubleshootUtils._dispatch_marvis_choice(choice)
        getattr(mh_mocks["ExtractedMarvisTroubleshootUtils"], attr).assert_called_once()

    def test_choice_5_exits(self, caplog, mh_mocks):
        TroubleshootUtils._dispatch_marvis_choice("5")
        assert "Exiting Marvis troubleshooting." in caplog.text

    def test_invalid_choice_routes_to_invalid_handler(self, caplog, mh_mocks):
        caplog.set_level(logging.WARNING)
        TroubleshootUtils._dispatch_marvis_choice("bogus")
        assert "Invalid option selected." in caplog.text
        mh_mocks["ExtractedMarvisTroubleshootUtils"].client_connectivity.assert_not_called()


class TestLaunchInteractive:
    def test_launch_dispatches_choice(self, mh_mocks, caplog):
        mh_mocks["InputUtils"].safe_input.return_value = "1"
        TroubleshootUtils.launch_interactive()
        mh_mocks["ConfigUtils"].get_cached_or_prompted_org_id.assert_called_once()
        mh_mocks["InputUtils"].safe_input.assert_called_once()
        mh_mocks["ExtractedMarvisTroubleshootUtils"].client_connectivity.assert_called_once()
        assert "Marvis" in caplog.text

    def test_launch_invalid_choice(self, mh_mocks, caplog):
        mh_mocks["InputUtils"].safe_input.return_value = "99"
        TroubleshootUtils.launch_interactive()
        assert "Invalid option selected." in caplog.text

    def test_launch_exit_choice(self, mh_mocks, caplog):
        mh_mocks["InputUtils"].safe_input.return_value = "5"
        TroubleshootUtils.launch_interactive()
        assert "Exiting Marvis troubleshooting." in caplog.text

    def test_launch_strips_whitespace_from_input(self, mh_mocks):
        mh_mocks["InputUtils"].safe_input.return_value = "  2  "
        TroubleshootUtils.launch_interactive()
        mh_mocks["ExtractedMarvisTroubleshootUtils"].device_performance.assert_called_once()
