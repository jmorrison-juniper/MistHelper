"""Tests for the ClientPacketCaptureDownloader steps that reach the network.

Why:
    ``tests/unit/capture/test_client_pcap_downloader.py`` covers the pure
    helpers, the single-file download, and the ``run`` guard chain. It does not
    cover the two SDK fetch methods, the four step orchestrators, the batch
    accumulator, or the offline guard. Those lines hold the Mist API calls, the
    broad error handlers that keep the menu alive, and the directory creation
    that precedes every write. This module covers them. Every Mist call and
    every HTTP call is mocked, so no test reaches the live cloud.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from src.capture import client_pcap_downloader as cpd
from src.capture.client_pcap_downloader import ClientPacketCaptureDownloader, _CaptureRow


@pytest.fixture
def downloader() -> ClientPacketCaptureDownloader:
    """Return a downloader with a mock session and a fixed org identifier.

    Why:
        Passing the org identifier skips the lazy ``ConfigUtils`` lookup, which
        would otherwise import MistHelper during construction.
    """
    # WHY: a mock session records the SDK arguments without opening a connection.
    return ClientPacketCaptureDownloader(MagicMock(), org_id="org-1")


@pytest.fixture
def fake_mist_helper() -> Iterator[MagicMock]:
    """Install a fake MistHelper module for the duration of one test.

    Why:
        The three lazy factories run ``import MistHelper``. A real import pulls
        in the whole entry point, which is slow and has side effects. A stub in
        ``sys.modules`` satisfies the import statement without that cost.
    """
    stub = MagicMock()  # WHY: stand in for the MistHelper entry point module.
    original = sys.modules.get("MistHelper")  # WHY: remember any real module to restore later.
    sys.modules["MistHelper"] = stub  # WHY: the import statement reads sys.modules first.
    try:
        yield stub  # WHY: hand the stub to the test so it can assert on the returned facade.
    finally:
        if original is None:  # WHY: no real module was loaded before this test.
            sys.modules.pop("MistHelper", None)  # WHY: leave the module table as it was found.
        else:
            sys.modules["MistHelper"] = original  # WHY: restore the real module for other tests.


class TestInit:
    """Cover construction, which resolves the org identifier."""

    def test_a_supplied_org_is_used_verbatim(self) -> None:
        """A caller-supplied org must not trigger the cached lookup."""
        with patch.object(cpd, "_get_config_utils") as config_factory:
            instance = ClientPacketCaptureDownloader(MagicMock(), org_id="org-7")
        config_factory.assert_not_called()  # WHY: an unattended run must not prompt.
        assert instance._org_id == "org-7"  # WHY: the supplied value must survive construction.

    def test_a_missing_org_falls_back_to_the_cached_lookup(self) -> None:
        """An absent org must resolve through the shared cache, not fail."""
        config_utils = MagicMock()  # WHY: stand in for the MistHelper ConfigUtils facade.
        config_utils.get_cached_or_prompted_org_id.return_value = "org-cached"  # WHY: cached value.
        with patch.object(cpd, "_get_config_utils", return_value=config_utils):
            instance = ClientPacketCaptureDownloader(MagicMock())  # WHY: drive the fallback branch.
        assert instance._org_id == "org-cached"  # WHY: the cached value must reach the instance.


class TestFetchWirelessClients:
    """Cover the client search call and its offline and error guards."""

    def test_an_absent_sdk_returns_an_empty_list(self, downloader: ClientPacketCaptureDownloader) -> None:
        """Offline tooling must degrade to an abort, not an AttributeError."""
        # WHY: the module sets this flag to False when the SDK import fails.
        with patch.object(cpd, "MISTAPI_AVAILABLE", False):
            assert downloader._fetch_wireless_clients("site-1") == []

    def test_the_search_call_carries_the_window_and_the_page_limit(
        self, downloader: ClientPacketCaptureDownloader
    ) -> None:
        """A missing window or limit would scan the wrong range or page too slowly."""
        fake_sdk = MagicMock()  # WHY: stand in for the whole mistapi package.
        fake_sdk.get_all.return_value = []  # WHY: the paging result is not under test here.
        with patch.object(cpd, "mistapi", fake_sdk), patch.object(cpd, "MISTAPI_AVAILABLE", True):
            downloader._fetch_wireless_clients("site-1")  # WHY: drive the search call.
        search = fake_sdk.api.v1.sites.clients.searchSiteWirelessClients  # WHY: the call under test.
        # WHY: the seven-day window and the page size are both part of the documented contract.
        search.assert_called_once_with(downloader._session, "site-1", duration="7d", limit=1000)

    def test_a_none_page_becomes_an_empty_list(self, downloader: ClientPacketCaptureDownloader) -> None:
        """The SDK returns None for an empty response, which callers must not index."""
        fake_sdk = MagicMock()  # WHY: stand in for the whole mistapi package.
        fake_sdk.get_all.return_value = None  # WHY: reproduce the SDK boundary case.
        with patch.object(cpd, "mistapi", fake_sdk), patch.object(cpd, "MISTAPI_AVAILABLE", True):
            assert downloader._fetch_wireless_clients("site-1") == []

    def test_a_search_failure_returns_an_empty_list(
        self, downloader: ClientPacketCaptureDownloader, caplog: Any
    ) -> None:
        """A network failure must abort the step, not crash the menu dispatcher."""
        caplog.set_level("ERROR")  # WHY: the handler reports the failure at ERROR level.
        fake_sdk = MagicMock()  # WHY: stand in for the whole mistapi package.
        # WHY: the search call is the first network hop, so it fails on its own.
        fake_sdk.api.v1.sites.clients.searchSiteWirelessClients.side_effect = RuntimeError("dns fail")
        with patch.object(cpd, "mistapi", fake_sdk), patch.object(cpd, "MISTAPI_AVAILABLE", True):
            assert downloader._fetch_wireless_clients("site-1") == []
        assert "dns fail" in caplog.text  # WHY: the operator needs the cause to triage.

    def test_a_paging_failure_returns_an_empty_list(
        self, downloader: ClientPacketCaptureDownloader, caplog: Any
    ) -> None:
        """A failure inside ``get_all`` must reach the same handler as a call failure."""
        caplog.set_level("ERROR")  # WHY: the handler reports the failure at ERROR level.
        fake_sdk = MagicMock()  # WHY: stand in for the whole mistapi package.
        # WHY: paging is a second network hop, so it fails independently of the search.
        fake_sdk.get_all.side_effect = ValueError("truncated page")
        with patch.object(cpd, "mistapi", fake_sdk), patch.object(cpd, "MISTAPI_AVAILABLE", True):
            assert downloader._fetch_wireless_clients("site-1") == []
        assert "truncated page" in caplog.text  # WHY: the paging failure must stay attributable.


class TestFetchCaptures:
    """Cover the capture listing call and its offline and error guards."""

    def test_an_absent_sdk_returns_an_empty_list(self, downloader: ClientPacketCaptureDownloader) -> None:
        """Offline tooling must degrade to an abort, not an AttributeError."""
        with patch.object(cpd, "MISTAPI_AVAILABLE", False):
            assert downloader._fetch_captures("site-1", "aa:bb:cc:dd:ee:ff") == []

    def test_the_mac_filter_is_sent_without_punctuation(self, downloader: ClientPacketCaptureDownloader) -> None:
        """Mist rejects a punctuated MAC in the query filter, so the colons must go."""
        fake_sdk = MagicMock()  # WHY: stand in for the whole mistapi package.
        fake_sdk.get_all.return_value = []  # WHY: the paging result is not under test here.
        with patch.object(cpd, "mistapi", fake_sdk), patch.object(cpd, "MISTAPI_AVAILABLE", True):
            downloader._fetch_captures("site-1", "aa:bb:cc:dd:ee:ff")  # WHY: drive the listing call.
        _, kwargs = fake_sdk.api.v1.sites.pcaps.listSitePacketCaptures.call_args  # WHY: read the filter.
        # WHY: a punctuated value would silently match nothing and look like an empty result.
        assert kwargs["client_mac"] == "aabbccddeeff"

    def test_a_listing_failure_returns_an_empty_list(
        self, downloader: ClientPacketCaptureDownloader, caplog: Any
    ) -> None:
        """A network failure must abort the step, not crash the menu dispatcher."""
        caplog.set_level("ERROR")  # WHY: the handler reports the failure at ERROR level.
        fake_sdk = MagicMock()  # WHY: stand in for the whole mistapi package.
        # WHY: the listing call is the first network hop, so it fails on its own.
        fake_sdk.api.v1.sites.pcaps.listSitePacketCaptures.side_effect = RuntimeError("bad gateway")
        with patch.object(cpd, "mistapi", fake_sdk), patch.object(cpd, "MISTAPI_AVAILABLE", True):
            assert downloader._fetch_captures("site-1", "aa:bb:cc:dd:ee:ff") == []
        assert "bad gateway" in caplog.text  # WHY: the operator needs the cause to triage.


class TestStepOrchestrators:
    """Cover the four step methods and their abort guards."""

    def test_step_one_returns_none_when_no_site_is_chosen(self, downloader: ClientPacketCaptureDownloader) -> None:
        """A cancelled site prompt must abort the whole flow."""
        prompt_utils = MagicMock()  # WHY: stand in for the MistHelper PromptUtils facade.
        prompt_utils.select_site_with_logging.return_value = ""  # WHY: an empty pick cancels.
        with patch.object(cpd, "_get_prompt_utils", return_value=prompt_utils):
            assert downloader._step1_select_site() is None  # WHY: None signals abort.

    def test_step_one_normalizes_the_chosen_site_to_a_string(self, downloader: ClientPacketCaptureDownloader) -> None:
        """The picker returns a loosely typed value that later steps use as a path segment."""
        prompt_utils = MagicMock()  # WHY: stand in for the MistHelper PromptUtils facade.
        prompt_utils.select_site_with_logging.return_value = 12345  # WHY: mimic a non-string pick.
        with patch.object(cpd, "_get_prompt_utils", return_value=prompt_utils):
            result = downloader._step1_select_site()  # WHY: drive the normalization branch.
        assert result == "12345"  # WHY: a non-string would break the later URL interpolation.

    def test_step_two_aborts_when_no_clients_are_returned(self, downloader: ClientPacketCaptureDownloader) -> None:
        """A site with no recent clients must abort before the prompt runs."""
        with (
            patch.object(downloader, "_fetch_wireless_clients", return_value=[]),
            patch.object(downloader, "_prompt_client_choice") as prompt_spy,
        ):
            assert downloader._step2_select_client("site-1") is None  # WHY: None signals abort.
        prompt_spy.assert_not_called()  # WHY: an empty table gives the operator nothing to pick.

    def test_step_two_returns_the_resolved_mac(self, downloader: ClientPacketCaptureDownloader) -> None:
        """A valid pick must reach the caller as a normalized MAC."""
        clients = [{"mac": "aabbccddeeff", "hostname": "laptop"}]  # WHY: one selectable row.
        with (
            patch.object(downloader, "_fetch_wireless_clients", return_value=clients),
            patch.object(downloader, "_prompt_client_choice", return_value="aa:bb:cc:dd:ee:ff"),
        ):
            assert downloader._step2_select_client("site-1") == "aa:bb:cc:dd:ee:ff"

    def test_step_three_aborts_when_no_captures_exist(self, downloader: ClientPacketCaptureDownloader) -> None:
        """A client with no captures must abort before the grouping runs."""
        with (
            patch.object(downloader, "_fetch_captures", return_value=[]),
            patch.object(downloader, "_prompt_vlan_choice") as prompt_spy,
        ):
            assert downloader._step3_select_vlan("site-1", "aa:bb:cc:dd:ee:ff") == []
        prompt_spy.assert_not_called()  # WHY: an empty table gives the operator nothing to pick.

    def test_step_three_groups_before_prompting(self, downloader: ClientPacketCaptureDownloader) -> None:
        """The prompt must receive VLAN buckets, not the raw capture list."""
        # WHY: two captures on one VLAN must collapse into a single bucket for the prompt.
        captures = [
            {"id": "c1", "pcap_url": "https://host/c1.pcap", "vlan_id": 10, "filename": "c1.pcap"},
            {"id": "c2", "pcap_url": "https://host/c2.pcap", "vlan_id": 10, "filename": "c2.pcap"},
        ]
        with (
            patch.object(downloader, "_fetch_captures", return_value=captures),
            patch.object(downloader, "_prompt_vlan_choice", return_value=[]) as prompt_spy,
        ):
            downloader._step3_select_vlan("site-1", "aa:bb:cc:dd:ee:ff")  # WHY: drive the grouping.
        grouped = prompt_spy.call_args[0][0]  # WHY: read the argument the prompt received.
        assert list(grouped.keys()) == ["10"]  # WHY: one VLAN key, not two capture rows.
        assert len(grouped["10"]) == 2  # WHY: both captures must land in the same bucket.

    def test_step_four_creates_the_target_directory_before_downloading(
        self, downloader: ClientPacketCaptureDownloader, tmp_path: Path
    ) -> None:
        """A download into a missing directory would fail, so the directory comes first."""
        rows = [_CaptureRow("c1", "https://host/c1.pcap", "10", "c1.pcap")]  # WHY: one row.
        target = tmp_path / "packet_captures" / "aa_bb_cc_dd_ee_ff" / "vlan_10"  # WHY: expected path.
        with (
            # WHY: redirect the hard-coded data root so the test writes under tmp_path.
            patch.object(cpd, "capture_dir", return_value=target),
            patch.object(downloader, "_download_all", return_value=1) as download_spy,
        ):
            downloader._step4_download("aa:bb:cc:dd:ee:ff", rows)  # WHY: drive the directory creation.
        assert target.is_dir()  # WHY: the writer needs the directory to exist before it opens a file.
        download_spy.assert_called_once_with(rows, target)  # WHY: the batch must target that directory.

    def test_step_four_is_safe_to_repeat(self, downloader: ClientPacketCaptureDownloader, tmp_path: Path) -> None:
        """A repeat run must not fail on an existing directory."""
        rows = [_CaptureRow("c1", "https://host/c1.pcap", "10", "c1.pcap")]  # WHY: one row.
        target = tmp_path / "vlan_10"  # WHY: a path the test creates ahead of time.
        target.mkdir(parents=True)  # WHY: mimic the directory left by an earlier run.
        with (
            patch.object(cpd, "capture_dir", return_value=target),
            patch.object(downloader, "_download_all", return_value=1),
        ):
            downloader._step4_download("aa:bb:cc:dd:ee:ff", rows)  # WHY: must not raise.
        assert target.is_dir()  # WHY: the existing directory must survive the repeat run.


class TestDownloadAll:
    """Cover the batch accumulator, which must survive a partial failure."""

    def test_the_count_matches_the_successful_writes(
        self, downloader: ClientPacketCaptureDownloader, tmp_path: Path
    ) -> None:
        """A mixed batch must report only the files that reached the disk."""
        rows = [
            _CaptureRow("c1", "https://host/c1.pcap", "10", "c1.pcap"),  # WHY: this one succeeds.
            _CaptureRow("c2", "https://host/c2.pcap", "10", "c2.pcap"),  # WHY: this one fails.
            _CaptureRow("c3", "https://host/c3.pcap", "10", "c3.pcap"),  # WHY: this one succeeds.
        ]
        # WHY: a per-row result list proves the accumulator counts, not the row total.
        with patch.object(ClientPacketCaptureDownloader, "_download_one", side_effect=[True, False, True]):
            assert downloader._download_all(rows, tmp_path) == 2

    def test_a_failed_row_does_not_stop_the_batch(
        self, downloader: ClientPacketCaptureDownloader, tmp_path: Path
    ) -> None:
        """One bad pre-signed URL must not abandon the remaining captures."""
        rows = [
            _CaptureRow("c1", "https://host/c1.pcap", "10", "c1.pcap"),  # WHY: this one fails first.
            _CaptureRow("c2", "https://host/c2.pcap", "10", "c2.pcap"),  # WHY: this one must still run.
        ]
        with patch.object(ClientPacketCaptureDownloader, "_download_one", side_effect=[False, True]) as download_spy:
            downloader._download_all(rows, tmp_path)  # WHY: drive both rows.
        assert download_spy.call_count == 2  # WHY: the loop must reach the second row.

    def test_an_empty_batch_returns_zero(self, downloader: ClientPacketCaptureDownloader, tmp_path: Path) -> None:
        """An empty batch must report zero, not raise on the accumulator."""
        assert downloader._download_all([], tmp_path) == 0  # WHY: the loop body never runs.


def _streaming_response(status_code: int) -> MagicMock:
    """Build a response mock that works as a plain object and as a context manager."""
    response = MagicMock()  # WHY: stand in for the requests response object.
    # WHY: the downloader wraps the request in a with block to release the connection.
    # WHY: binding __enter__ to the same object keeps one place to set the attributes.
    response.__enter__.return_value = response
    response.__exit__.return_value = False  # WHY: a False result never swallows an exception.
    response.status_code = status_code  # WHY: the caller chooses the branch under test.
    return response  # WHY: each test then sets its own body behavior.


class TestDownloadOneResourceHandling:
    """Cover the streaming write, which owns a file handle and an HTTP response."""

    def test_the_request_streams_with_a_timeout(self, tmp_path: Path) -> None:
        """A download without a timeout can hang the menu forever."""
        response = _streaming_response(200)  # WHY: drive the success path to reach the write.
        response.iter_content.return_value = [b"payload"]  # WHY: one chunk is enough.
        row = _CaptureRow("c1", "https://host/c1.pcap", "10", "c1.pcap")  # WHY: one row.
        with patch.object(cpd.requests, "get", return_value=response) as get_spy:
            assert ClientPacketCaptureDownloader._download_one(row, tmp_path) is True
        _, kwargs = get_spy.call_args  # WHY: read the request keywords.
        assert kwargs["stream"] is True  # WHY: a large PCAP must not load fully into memory.
        assert kwargs["timeout"] == 300  # WHY: a hung transfer must eventually fail.

    def test_a_non_200_response_leaves_no_partial_file(self, tmp_path: Path) -> None:
        """A rejected download must not leave a zero-byte file that looks like a capture."""
        response = _streaming_response(403)  # WHY: an expired pre-signed URL returns a client error.
        row = _CaptureRow("c1", "https://host/c1.pcap", "10", "c1.pcap")  # WHY: one row.
        with patch.object(cpd.requests, "get", return_value=response):
            assert ClientPacketCaptureDownloader._download_one(row, tmp_path) is False
        # WHY: the guard returns before the open call, so no file may appear.
        assert not (tmp_path / "c1.pcap").exists()

    def test_every_chunk_reaches_the_file(self, tmp_path: Path) -> None:
        """A dropped chunk would produce a truncated capture that looks valid."""
        response = _streaming_response(200)  # WHY: drive the success path to reach the write.
        response.iter_content.return_value = [b"aaa", b"bbb", b"ccc"]  # WHY: three chunks.
        row = _CaptureRow("c1", "https://host/c1.pcap", "10", "c1.pcap")  # WHY: one row.
        with patch.object(cpd.requests, "get", return_value=response):
            ClientPacketCaptureDownloader._download_one(row, tmp_path)  # WHY: drive the write loop.
        # WHY: the concatenated chunks must match the payload byte for byte.
        assert (tmp_path / "c1.pcap").read_bytes() == b"aaabbbccc"

    def test_a_mid_stream_failure_is_reported_as_a_failure(self, tmp_path: Path, caplog: Any) -> None:
        """A connection reset partway through must return False, not raise."""
        caplog.set_level("ERROR")  # WHY: the handler reports the failure at ERROR level.
        response = _streaming_response(200)  # WHY: the transfer starts before it fails.
        # WHY: raising from the chunk iterator reproduces a reset partway through the body.
        response.iter_content.side_effect = OSError("connection reset")
        row = _CaptureRow("c1", "https://host/c1.pcap", "10", "c1.pcap")  # WHY: one row.
        with patch.object(cpd.requests, "get", return_value=response):
            assert ClientPacketCaptureDownloader._download_one(row, tmp_path) is False
        assert "connection reset" in caplog.text  # WHY: the operator needs the cause to triage.

    def test_a_mid_stream_failure_still_releases_the_connection(self, tmp_path: Path) -> None:
        """A leaked connection exhausts the pool and stalls a large batch."""
        response = _streaming_response(200)  # WHY: the transfer starts before it fails.
        response.iter_content.side_effect = OSError("connection reset")  # WHY: reset mid body.
        row = _CaptureRow("c1", "https://host/c1.pcap", "10", "c1.pcap")  # WHY: one row.
        with patch.object(cpd.requests, "get", return_value=response):
            ClientPacketCaptureDownloader._download_one(row, tmp_path)  # WHY: drive the failure.
        # WHY: the with block must call __exit__ so the socket returns to the pool.
        assert response.__exit__.called

    def test_a_successful_download_releases_the_connection(self, tmp_path: Path) -> None:
        """A connection held after a clean transfer still exhausts the pool."""
        response = _streaming_response(200)  # WHY: drive the success path to reach the write.
        response.iter_content.return_value = [b"payload"]  # WHY: one chunk is enough.
        row = _CaptureRow("c1", "https://host/c1.pcap", "10", "c1.pcap")  # WHY: one row.
        with patch.object(cpd.requests, "get", return_value=response):
            assert ClientPacketCaptureDownloader._download_one(row, tmp_path) is True
        assert response.__exit__.called  # WHY: the socket must return to the pool.
        assert (tmp_path / "c1.pcap").read_bytes() == b"payload"  # WHY: prove the write ran.


class TestLazyFactories:
    """Cover the three deferred imports that break the capture-to-MistHelper cycle."""

    def test_the_config_factory_returns_the_config_facade(self, fake_mist_helper: MagicMock) -> None:
        """A wrong facade would break the cached org lookup at construction time."""
        # WHY: identity proves the factory reaches through to the entry point attribute.
        assert cpd._get_config_utils() is fake_mist_helper.ConfigUtils

    def test_the_input_factory_returns_the_input_facade(self, fake_mist_helper: MagicMock) -> None:
        """A wrong facade would lose the EOF-safe input wrapper the SSH mode needs."""
        assert cpd._get_input_utils() is fake_mist_helper.InputUtils

    def test_the_prompt_factory_returns_the_prompt_facade(self, fake_mist_helper: MagicMock) -> None:
        """A wrong facade would break the site picker in step one."""
        assert cpd._get_prompt_utils() is fake_mist_helper.PromptUtils


class TestPromptClientChoice:
    """Cover the client prompt, which accepts an index or a MAC."""

    def test_a_blank_entry_cancels_the_step(self, downloader: ClientPacketCaptureDownloader) -> None:
        """A blank entry is the documented cancel signal, so it must return None."""
        input_utils = MagicMock()  # WHY: stand in for the MistHelper InputUtils facade.
        input_utils.safe_input.return_value = ""  # WHY: reproduce the blank cancel entry.
        with patch.object(cpd, "_get_input_utils", return_value=input_utils):
            assert downloader._prompt_client_choice([{"mac": "aabbccddeeff"}]) is None

    def test_the_prompt_declares_its_menu_context(self, downloader: ClientPacketCaptureDownloader) -> None:
        """The context string attributes an EOF exit to the right menu in the log."""
        input_utils = MagicMock()  # WHY: stand in for the MistHelper InputUtils facade.
        input_utils.safe_input.return_value = ""  # WHY: cancel at once, the parse is tested elsewhere.
        with patch.object(cpd, "_get_input_utils", return_value=input_utils):
            downloader._prompt_client_choice([])  # WHY: drive the prompt call.
        _, kwargs = input_utils.safe_input.call_args  # WHY: read the prompt keywords.
        assert kwargs["context"] == "menu_197_client"  # WHY: the audit trail depends on this value.

    def test_an_index_entry_reaches_the_resolver(self, downloader: ClientPacketCaptureDownloader) -> None:
        """A non-blank entry must pass through to the parse helper unchanged."""
        clients = [{"mac": "aa:bb:cc:dd:ee:ff"}]  # WHY: one selectable row.
        input_utils = MagicMock()  # WHY: stand in for the MistHelper InputUtils facade.
        input_utils.safe_input.return_value = "1"  # WHY: pick the first row by index.
        with patch.object(cpd, "_get_input_utils", return_value=input_utils):
            result = downloader._prompt_client_choice(clients)  # WHY: drive the resolve branch.
        assert result == "aa:bb:cc:dd:ee:ff"  # WHY: the resolver must return the normalized MAC.


class TestPromptVlanChoice:
    """Cover the VLAN prompt, which must abort when no capture has a URL."""

    def test_an_empty_grouping_returns_no_rows(self, downloader: ClientPacketCaptureDownloader) -> None:
        """Captures that are still running have no URL, so the prompt must abort."""
        input_utils = MagicMock()  # WHY: stand in for the MistHelper InputUtils facade.
        with patch.object(cpd, "_get_input_utils", return_value=input_utils):
            assert downloader._prompt_vlan_choice({}) == []
        # WHY: prompting for a choice among zero rows would strand the operator.
        input_utils.safe_input.assert_not_called()

    def test_the_prompt_declares_its_menu_context(self, downloader: ClientPacketCaptureDownloader) -> None:
        """The context string attributes an EOF exit to the right menu in the log."""
        grouped = {"10": [_CaptureRow("c1", "https://host/c1.pcap", "10", "c1.pcap")]}  # WHY: one bucket.
        input_utils = MagicMock()  # WHY: stand in for the MistHelper InputUtils facade.
        input_utils.safe_input.return_value = ""  # WHY: cancel at once, the parse is tested elsewhere.
        with patch.object(cpd, "_get_input_utils", return_value=input_utils):
            downloader._prompt_vlan_choice(grouped)  # WHY: drive the prompt call.
        _, kwargs = input_utils.safe_input.call_args  # WHY: read the prompt keywords.
        assert kwargs["context"] == "menu_197_vlan"  # WHY: the audit trail depends on this value.

    def test_the_resolver_sees_the_vlan_keys_in_sorted_order(self, downloader: ClientPacketCaptureDownloader) -> None:
        """An unsorted list would make the row numbers shift between runs."""
        # WHY: an out-of-order dictionary proves the method sorts rather than relying on insertion.
        grouped = {
            "30": [_CaptureRow("c3", "https://host/c3.pcap", "30", "c3.pcap")],
            "10": [_CaptureRow("c1", "https://host/c1.pcap", "10", "c1.pcap")],
            "20": [_CaptureRow("c2", "https://host/c2.pcap", "20", "c2.pcap")],
        }
        input_utils = MagicMock()  # WHY: stand in for the MistHelper InputUtils facade.
        input_utils.safe_input.return_value = "1"  # WHY: pick the first row after sorting.
        with patch.object(cpd, "_get_input_utils", return_value=input_utils):
            rows = downloader._prompt_vlan_choice(grouped)  # WHY: drive the sort and the resolve.
        assert [row.capture_id for row in rows] == ["c1"]  # WHY: VLAN 10 must rank first.

    def test_a_valid_pick_returns_every_row_in_the_bucket(self, downloader: ClientPacketCaptureDownloader) -> None:
        """Picking a VLAN downloads the whole bucket, not one capture."""
        grouped = {
            "10": [
                _CaptureRow("c1", "https://host/c1.pcap", "10", "c1.pcap"),  # WHY: first in bucket.
                _CaptureRow("c2", "https://host/c2.pcap", "10", "c2.pcap"),  # WHY: second in bucket.
            ]
        }
        input_utils = MagicMock()  # WHY: stand in for the MistHelper InputUtils facade.
        input_utils.safe_input.return_value = "1"  # WHY: pick the only VLAN row.
        with patch.object(cpd, "_get_input_utils", return_value=input_utils):
            rows = downloader._prompt_vlan_choice(grouped)  # WHY: drive the resolve branch.
        assert len(rows) == 2  # WHY: both captures on the VLAN must queue for download.
