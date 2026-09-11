"""Unit tests for Menu 197 ClientPacketCaptureDownloader (issue #421)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.capture import client_pcap_downloader as mod
from src.capture.client_pcap_downloader import (
    ClientPacketCaptureDownloader,
    _CaptureRow,
    capture_dir,
    normalise_mac,
)

# ---------- module helpers ----------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("aabbccddeeff", "aa:bb:cc:dd:ee:ff"),
        ("AA:BB:CC:DD:EE:FF", "aa:bb:cc:dd:ee:ff"),
        ("aa-bb-cc-dd-ee-ff", "aa:bb:cc:dd:ee:ff"),
        ("aabb.ccdd.eeff", "aa:bb:cc:dd:ee:ff"),
    ],
)
def test_normalise_mac_accepts_common_formats(raw: str, expected: str) -> None:
    """MAC normaliser strips punctuation across the four common formats."""
    assert normalise_mac(raw) == expected


@pytest.mark.parametrize("bad", ["", "notamac", "aabbcc", "aabbccddeeff11", "zz:zz:zz:zz:zz:zz"])
def test_normalise_mac_rejects_invalid(bad: str) -> None:
    """Non-12-hex inputs raise ValueError."""
    with pytest.raises(ValueError):
        normalise_mac(bad)


def test_capture_dir_builds_expected_layout() -> None:
    """capture_dir joins base/packet_captures/<mac-with-underscores>/vlan_<id>."""
    result = capture_dir(Path("data"), "aa:bb:cc:dd:ee:ff", 42)
    assert result == Path("data") / "packet_captures" / "aa_bb_cc_dd_ee_ff" / "vlan_42"


def test_capture_dir_accepts_string_vlan() -> None:
    """VLAN id may be str (e.g. 'unknown') without breaking path assembly."""
    result = capture_dir(Path("data"), "aa:bb:cc:dd:ee:ff", "unknown")
    assert result.name == "vlan_unknown"


# ---------- fixture ----------


@pytest.fixture()
def downloader() -> ClientPacketCaptureDownloader:
    """Build a downloader with mocked ConfigUtils to skip the org-id prompt."""
    with patch("src.capture.client_pcap_downloader._get_config_utils") as config_utils:
        config_utils.return_value.get_cached_or_prompted_org_id.return_value = "org-1"
        return ClientPacketCaptureDownloader(MagicMock(), org_id=None)


# ---------- _group_by_vlan ----------


def test_group_by_vlan_buckets_and_skips_urlless() -> None:
    """Captures without pcap_url are skipped; the rest are grouped by vlan_id."""
    captures = [
        {"id": "c1", "pcap_url": "u1", "vlan_id": 10, "filename": "a.pcap"},
        {"id": "c2", "pcap_url": "", "vlan_id": 10},  # skipped: no URL
        {"id": "c3", "pcap_url": "u3", "vlan_id": 20},
        {"id": "c4", "pcap_url": "u4"},  # falls back to "unknown"
    ]
    grouped = ClientPacketCaptureDownloader._group_by_vlan(captures)
    assert set(grouped) == {"10", "20", "unknown"}
    assert len(grouped["10"]) == 1
    assert grouped["10"][0] == _CaptureRow("c1", "u1", "10", "a.pcap")
    assert grouped["unknown"][0].filename == "c4.pcap"


# ---------- _resolve_client_choice ----------


def test_resolve_client_choice_index_path() -> None:
    """Numeric index picks the corresponding row and normalises its MAC."""
    clients = [{"mac": "AABBCCDDEEFF"}, {"mac": "112233445566"}]
    assert ClientPacketCaptureDownloader._resolve_client_choice("2", clients) == "11:22:33:44:55:66"


def test_resolve_client_choice_mac_path() -> None:
    """Non-numeric input is treated as a MAC and normalised."""
    assert ClientPacketCaptureDownloader._resolve_client_choice("aa-bb-cc-dd-ee-ff", []) == "aa:bb:cc:dd:ee:ff"


def test_resolve_client_choice_bad_index_returns_none() -> None:
    """Out-of-range index yields None (cancel)."""
    assert ClientPacketCaptureDownloader._resolve_client_choice("9", [{"mac": "aabbccddeeff"}]) is None


def test_resolve_client_choice_bad_mac_returns_none() -> None:
    """Malformed MAC yields None (cancel)."""
    assert ClientPacketCaptureDownloader._resolve_client_choice("not-a-mac", []) is None


# ---------- _resolve_vlan_choice ----------


def test_resolve_vlan_choice_returns_bucket() -> None:
    """Valid index returns the matching VLAN's row list."""
    rows = [_CaptureRow("c1", "u1", "10", "a.pcap")]
    grouped = {"10": rows}
    assert ClientPacketCaptureDownloader._resolve_vlan_choice("1", ["10"], grouped) == rows


@pytest.mark.parametrize("bad", ["", "x", "0", "99"])
def test_resolve_vlan_choice_rejects_bad(bad: str) -> None:
    """Blank/non-numeric/out-of-range yields [] (cancel)."""
    assert ClientPacketCaptureDownloader._resolve_vlan_choice(bad, ["10"], {"10": []}) == []


# ---------- _download_one ----------


def test_download_one_writes_file_on_200(tmp_path: Path) -> None:
    """A 200 response streams into a file at target/<filename>."""
    row = _CaptureRow("cap-1", "https://x/cap.pcap", "10", "cap.pcap")
    response = MagicMock()
    response.status_code = 200
    response.iter_content.return_value = [b"AB", b"CD"]
    response.__enter__.return_value = response  # WHY: the downloader now closes the body through a with block.
    with patch.object(mod.requests, "get", return_value=response):
        ok = ClientPacketCaptureDownloader._download_one(row, tmp_path)
    assert ok is True
    assert (tmp_path / "cap.pcap").read_bytes() == b"ABCD"
    response.__exit__.assert_called_once()  # WHY: the streamed body must close on the success path too.


def test_download_one_returns_false_on_non_200(tmp_path: Path) -> None:
    """Non-200 responses skip the write and return False."""
    row = _CaptureRow("cap-1", "https://x/cap.pcap", "10", "cap.pcap")
    response = MagicMock()
    response.status_code = 404
    response.__enter__.return_value = response  # WHY: the downloader now closes the body through a with block.
    with patch.object(mod.requests, "get", return_value=response):
        ok = ClientPacketCaptureDownloader._download_one(row, tmp_path)
    assert ok is False
    assert not (tmp_path / "cap.pcap").exists()
    response.__exit__.assert_called_once()  # WHY: a non-200 reply must not leave the socket checked out.


def test_download_one_returns_false_on_exception(tmp_path: Path) -> None:
    """A raised exception is swallowed and False is returned."""
    row = _CaptureRow("cap-1", "https://x/cap.pcap", "10", "cap.pcap")
    with patch.object(mod.requests, "get", side_effect=RuntimeError("boom")):
        ok = ClientPacketCaptureDownloader._download_one(row, tmp_path)
    assert ok is False


# ---------- run() orchestration guards ----------


def test_run_aborts_when_site_step_returns_none(downloader: ClientPacketCaptureDownloader) -> None:
    """No side effects when step 1 cancels."""
    with (
        patch.object(downloader, "_step1_select_site", return_value=None),
        patch.object(downloader, "_step2_select_client") as step2,
    ):
        downloader.run()
    step2.assert_not_called()


def test_run_aborts_when_client_step_returns_none(downloader: ClientPacketCaptureDownloader) -> None:
    """No VLAN step when step 2 cancels."""
    with (
        patch.object(downloader, "_step1_select_site", return_value="site-1"),
        patch.object(downloader, "_step2_select_client", return_value=None),
        patch.object(downloader, "_step3_select_vlan") as step3,
    ):
        downloader.run()
    step3.assert_not_called()


def test_run_aborts_when_vlan_step_returns_empty(downloader: ClientPacketCaptureDownloader) -> None:
    """No download step when step 3 returns an empty list."""
    with (
        patch.object(downloader, "_step1_select_site", return_value="site-1"),
        patch.object(downloader, "_step2_select_client", return_value="aa:bb:cc:dd:ee:ff"),
        patch.object(downloader, "_step3_select_vlan", return_value=[]),
        patch.object(downloader, "_step4_download") as step4,
    ):
        downloader.run()
    step4.assert_not_called()


def test_run_invokes_download_when_all_steps_succeed(downloader: ClientPacketCaptureDownloader) -> None:
    """Step 4 fires when the pipeline produces a non-empty VLAN row list."""
    rows = [_CaptureRow("c1", "u1", "10", "a.pcap")]
    with (
        patch.object(downloader, "_step1_select_site", return_value="site-1"),
        patch.object(downloader, "_step2_select_client", return_value="aa:bb:cc:dd:ee:ff"),
        patch.object(downloader, "_step3_select_vlan", return_value=rows),
        patch.object(downloader, "_step4_download") as step4,
    ):
        downloader.run()
    step4.assert_called_once_with("aa:bb:cc:dd:ee:ff", rows)
