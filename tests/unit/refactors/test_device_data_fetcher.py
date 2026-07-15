"""Wave 7 P2 coverage for src/refactors/device_data_fetcher.py (initiative #1018).

Covers every branch of ``DeviceDataFetcher.fetch()`` orchestration plus the
private helpers and the ``_MistHelperProxy.__getattr__`` late-binding path.
The dataclass ``DeviceFetchConfig`` is exercised via the constructor.

Every runtime dependency reached through ``_MH.*`` (PromptUtils, apisession,
DataProcessingUtils, DataExporter, DisplayUtils) is monkeypatched onto the
``MistHelper`` module. No live network, no CSV I/O, no MistHelper source
imports; ``MagicMock(spec=…)`` is used where a Response-shaped return is
required.
"""

from __future__ import annotations  # WHY: PEP 604 unions on Python 3.10+.

import logging  # WHY: caplog verification of the info/debug breadcrumbs.
from types import SimpleNamespace  # WHY: lightweight stand-in for mistapi response objects.
from typing import Any  # WHY: monkeypatched fakes carry loose typing.
from unittest.mock import MagicMock  # WHY: FR-008 mandates MagicMock for collaborators.

import pytest  # WHY: fixture + monkeypatch + caplog fixtures.

from src.refactors.device_data_fetcher import (  # WHY: direct SUT imports.
    _MH,
    DeviceDataFetcher,
    DeviceFetchConfig,
    _MistHelperProxy,
)


@pytest.fixture
def wired_misthelper(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Wire every ``_MH.*`` attribute the fetcher reaches through to a MagicMock double.

    Returns a dict of {attribute_name: mock} so tests can assert call ordering
    and argument bindings. The proxy resolves each attribute via
    ``importlib.import_module('MistHelper')`` at call time, so setting the
    module attribute is sufficient to intercept every access.
    """
    prompt_utils = MagicMock(
        name="PromptUtils"
    )  # WHY: exposes select_site_id_from_csv + select_device_id_from_inventory.
    prompt_utils.select_site_id_from_csv.return_value = "site-42"  # WHY: default happy-path site id.
    prompt_utils.select_device_id_from_inventory.return_value = "dev-99"  # WHY: default happy-path device id.

    data_processing = MagicMock(name="DataProcessingUtils")  # WHY: flatten + escape helpers reached via _MH.
    data_processing.flatten_nested_fields.side_effect = lambda rows: rows  # WHY: identity for round-trip assertions.
    data_processing.escape_multiline.side_effect = lambda rows: rows  # WHY: identity so we can verify final payload.

    data_exporter = MagicMock(name="DataExporter")  # WHY: write_with_format_selection observed only.
    display_utils = MagicMock(name="DisplayUtils")  # WHY: dict_list_as_pretty_table observed only.
    apisession_fake = MagicMock(name="apisession")  # WHY: passed as first arg into the fetch callable.

    monkeypatch.setattr("MistHelper.PromptUtils", prompt_utils, raising=False)  # WHY: proxy lookup.
    monkeypatch.setattr("MistHelper.DataProcessingUtils", data_processing, raising=False)  # WHY: proxy lookup.
    monkeypatch.setattr("MistHelper.DataExporter", data_exporter, raising=False)  # WHY: proxy lookup.
    monkeypatch.setattr("MistHelper.DisplayUtils", display_utils, raising=False)  # WHY: proxy lookup.
    monkeypatch.setattr("MistHelper.apisession", apisession_fake, raising=False)  # WHY: proxy lookup.

    return {  # WHY: bundle every published attribute for test assertions.
        "PromptUtils": prompt_utils,
        "DataProcessingUtils": data_processing,
        "DataExporter": data_exporter,
        "DisplayUtils": display_utils,
        "apisession": apisession_fake,
    }


def _make_fetch_function(response_data: Any) -> MagicMock:
    """Return a MagicMock fetch callable whose response.data attribute is ``response_data``."""
    fetch_function = MagicMock(name="fetch_function")  # WHY: represents mistapi callable.
    fetch_function.__name__ = "fetch_devices_v1"  # WHY: SUT reads __name__ for the debug log.
    fetch_function.return_value = SimpleNamespace(data=response_data)  # WHY: SUT reads response.data.
    return fetch_function  # WHY: hand back for injection into DeviceFetchConfig.


class TestDeviceFetchConfigDefaults:
    """Constructor defaults for optional dataclass fields."""

    def test_defaults_applied_when_optional_fields_omitted(self) -> None:
        """device_type defaults to 'all'; site_id and device_id default to None."""
        config = DeviceFetchConfig(  # WHY: only required positional fields supplied.
            fetch_function=lambda *a, **k: None,  # WHY: any callable satisfies typing.
            filename="out.csv",  # WHY: any string satisfies typing.
            description="test fetch",  # WHY: any string satisfies typing.
        )
        assert config.device_type == "all"  # WHY: documented default.
        assert config.site_id is None  # WHY: documented default.
        assert config.device_id is None  # WHY: documented default.


class TestMistHelperProxy:
    """``_MistHelperProxy.__getattr__`` resolves against the live MistHelper module."""

    def test_getattr_returns_module_attribute(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A value published on MistHelper is returned by the proxy."""
        sentinel = MagicMock(name="sentinel")  # WHY: unique object for identity check.
        monkeypatch.setattr("MistHelper._ddf_sentinel_attr", sentinel, raising=False)  # WHY: publish.
        proxy = _MistHelperProxy()  # WHY: fresh proxy instance.
        assert proxy._ddf_sentinel_attr is sentinel  # WHY: identity confirms zero-copy passthrough.

    def test_module_singleton_is_proxy(self) -> None:
        """The module-level `_MH` is an instance of `_MistHelperProxy`."""
        assert isinstance(_MH, _MistHelperProxy)  # WHY: guard against accidental replacement.


class TestDeviceDataFetcherFetchOrchestration:
    """End-to-end ``fetch()`` flow, including early-return branches."""

    def test_happy_path_writes_and_renders(self, wired_misthelper: dict[str, Any]) -> None:
        """Full path resolves ids, fetches, flattens, escapes, writes CSV, renders table."""
        fetch_function = _make_fetch_function({"id": "row"})  # WHY: non-empty response.data.
        config = DeviceFetchConfig(  # WHY: caller pre-supplies site + device -> skips prompts.
            fetch_function=fetch_function,
            filename="devices.csv",
            description="devices dump",
            site_id="site-A",
            device_id="dev-B",
        )
        DeviceDataFetcher(config).fetch()  # WHY: exercise full orchestration.

        # WHY: fetch callable invoked with (apisession, site_id, device_id).
        fetch_function.assert_called_once_with(wired_misthelper["apisession"], "site-A", "dev-B")
        wired_misthelper["DataProcessingUtils"].flatten_nested_fields.assert_called_once_with([{"id": "row"}])
        wired_misthelper["DataProcessingUtils"].escape_multiline.assert_called_once_with([{"id": "row"}])
        wired_misthelper["DataExporter"].write_with_format_selection.assert_called_once_with(
            [{"id": "row"}], "devices.csv"
        )
        wired_misthelper["DisplayUtils"].dict_list_as_pretty_table.assert_called_once_with([{"id": "row"}])
        # WHY: prompts never invoked because caller supplied both ids.
        wired_misthelper["PromptUtils"].select_site_id_from_csv.assert_not_called()
        wired_misthelper["PromptUtils"].select_device_id_from_inventory.assert_not_called()

    def test_prompts_when_ids_missing(self, wired_misthelper: dict[str, Any]) -> None:
        """When site/device are None, both prompt helpers are called with default device_type='all'."""
        fetch_function = _make_fetch_function({"k": "v"})  # WHY: non-empty response so full flow runs.
        config = DeviceFetchConfig(fetch_function=fetch_function, filename="f.csv", description="d")
        DeviceDataFetcher(config).fetch()  # WHY: exercise the prompting branches.

        wired_misthelper["PromptUtils"].select_site_id_from_csv.assert_called_once_with()  # WHY: site prompt.
        wired_misthelper["PromptUtils"].select_device_id_from_inventory.assert_called_once_with(
            "site-42", device_type="all"
        )  # WHY: device prompt uses resolved site + default filter.

    def test_aborts_when_site_prompt_returns_empty(self, wired_misthelper: dict[str, Any]) -> None:
        """Empty site prompt short-circuits before any fetch or device prompt occurs."""
        wired_misthelper["PromptUtils"].select_site_id_from_csv.return_value = ""  # WHY: user cancelled.
        fetch_function = _make_fetch_function({"k": "v"})  # WHY: proves callable is never invoked.
        config = DeviceFetchConfig(fetch_function=fetch_function, filename="f.csv", description="d")
        DeviceDataFetcher(config).fetch()  # WHY: exercise site-cancel branch.

        wired_misthelper["PromptUtils"].select_device_id_from_inventory.assert_not_called()  # WHY: no device prompt.
        fetch_function.assert_not_called()  # WHY: fetch skipped after site cancel.

    def test_aborts_when_device_prompt_returns_empty(self, wired_misthelper: dict[str, Any]) -> None:
        """Empty device prompt short-circuits before any fetch or CSV write occurs."""
        wired_misthelper["PromptUtils"].select_device_id_from_inventory.return_value = ""  # WHY: user cancelled.
        fetch_function = _make_fetch_function({"k": "v"})  # WHY: prove fetch is skipped.
        config = DeviceFetchConfig(fetch_function=fetch_function, filename="f.csv", description="d")
        DeviceDataFetcher(config).fetch()  # WHY: exercise device-cancel branch.

        fetch_function.assert_not_called()  # WHY: fetch skipped after device cancel.
        wired_misthelper["DataExporter"].write_with_format_selection.assert_not_called()  # WHY: no CSV write.

    def test_forwards_device_type_to_prompt(self, wired_misthelper: dict[str, Any]) -> None:
        """Custom device_type is forwarded to select_device_id_from_inventory."""
        fetch_function = _make_fetch_function({"k": "v"})  # WHY: non-empty so full flow runs.
        config = DeviceFetchConfig(  # WHY: custom device_type ripples into the device prompt kwargs.
            fetch_function=fetch_function,
            filename="f.csv",
            description="d",
            device_type="gateway",
        )
        DeviceDataFetcher(config).fetch()  # WHY: exercise device_type forwarding.

        wired_misthelper["PromptUtils"].select_device_id_from_inventory.assert_called_once_with(
            "site-42", device_type="gateway"
        )  # WHY: exact forwarding contract.

    def test_empty_response_data_skips_processing(self, wired_misthelper: dict[str, Any]) -> None:
        """When response.data is falsy, _fetch_data returns None and processing/output are skipped."""
        fetch_function = _make_fetch_function(None)  # WHY: response.data None -> result None.
        config = DeviceFetchConfig(  # WHY: pre-supplied ids to skip prompts.
            fetch_function=fetch_function,
            filename="f.csv",
            description="d",
            site_id="s",
            device_id="d",
        )
        DeviceDataFetcher(config).fetch()  # WHY: exercise empty-response branch.

        fetch_function.assert_called_once()  # WHY: fetch attempted.
        wired_misthelper["DataProcessingUtils"].flatten_nested_fields.assert_not_called()  # WHY: skip processing.
        wired_misthelper["DataExporter"].write_with_format_selection.assert_not_called()  # WHY: no CSV write.
        wired_misthelper["DisplayUtils"].dict_list_as_pretty_table.assert_not_called()  # WHY: no render.

    def test_fetch_data_returns_none_on_exception(self, wired_misthelper: dict[str, Any]) -> None:
        """A fetch_function that raises is caught; result is None and no processing occurs."""
        fetch_function = MagicMock(name="fetch_function", side_effect=RuntimeError("boom"))  # WHY: any error.
        fetch_function.__name__ = "erroring_fetch"  # WHY: SUT reads __name__ for the debug log.
        config = DeviceFetchConfig(  # WHY: pre-supplied ids to skip prompts.
            fetch_function=fetch_function,
            filename="f.csv",
            description="d",
            site_id="s",
            device_id="d",
        )
        DeviceDataFetcher(config).fetch()  # WHY: exercise exception branch.

        wired_misthelper["DataExporter"].write_with_format_selection.assert_not_called()  # WHY: no CSV write.
        wired_misthelper["DisplayUtils"].dict_list_as_pretty_table.assert_not_called()  # WHY: no render.

    def test_fetch_logs_progress(self, wired_misthelper: dict[str, Any], caplog: pytest.LogCaptureFixture) -> None:
        """The orchestration emits info + debug breadcrumbs at expected checkpoints."""
        fetch_function = _make_fetch_function({"k": "v"})  # WHY: happy-path so all log branches fire.
        config = DeviceFetchConfig(  # WHY: pre-supplied ids to keep the test focused on log content.
            fetch_function=fetch_function,
            filename="f.csv",
            description="descr",
            site_id="s",
            device_id="d",
        )
        with caplog.at_level(logging.DEBUG, logger="root"):  # WHY: capture debug + info levels.
            DeviceDataFetcher(config).fetch()  # WHY: exercise the fetch pipeline.
        messages = [rec.message for rec in caplog.records]  # WHY: aggregate for substring checks.
        assert any("Starting device data fetch" in m for m in messages)  # WHY: start log.
        assert any("descr" in m for m in messages)  # WHY: description surfaced somewhere.
        assert any("Completed device data fetch" in m for m in messages)  # WHY: completion log.
