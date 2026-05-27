"""Unit tests for extracted packet capture download/poll helper."""

from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.capture.packet_capture_download import PacketCaptureDownloadManager


class _FakeResponse:
    """Simple fake requests response object for download tests."""

    def __init__(self, status_code: int, content: bytes = b"", chunks: list[bytes] | None = None) -> None:
        self.status_code = status_code
        self.content = content
        self._chunks = chunks or []

    def iter_content(self, chunk_size: int = 8192):
        """Yield configured chunks to mimic streamed HTTP responses."""
        del chunk_size
        yield from self._chunks


class _FakeRequests:
    """Simple fake requests module that returns preconfigured responses."""

    def __init__(self, response: _FakeResponse) -> None:
        self.response = response

    def get(self, url: str, stream: bool = False, timeout: int = 300):
        """Return preconfigured fake response while validating key call args."""
        assert url
        assert timeout == 300
        if stream:
            return self.response
        return self.response


@pytest.fixture()
def helper() -> PacketCaptureDownloadManager:
    """Create fresh helper instance per test."""
    return PacketCaptureDownloadManager()


@pytest.fixture(autouse=True)
def _tmp_cwd(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run tests in isolated working directory to avoid file side effects."""
    monkeypatch.chdir(tmp_path)
    os.makedirs("data", exist_ok=True)


def test_parse_captures_response_supports_results_dict(helper: PacketCaptureDownloadManager) -> None:
    """Parser should extract captures from results-style payload."""
    parsed = helper.parse_captures_response({"results": [{"id": "cap-1"}]}, 1)
    assert parsed == [{"id": "cap-1"}]


def test_parse_captures_response_supports_list(helper: PacketCaptureDownloadManager) -> None:
    """Parser should return list payload unchanged."""
    parsed = helper.parse_captures_response([{"id": "cap-2"}], 1)
    assert parsed == [{"id": "cap-2"}]


def test_find_capture_url_returns_ready_url(helper: PacketCaptureDownloadManager) -> None:
    """Finder should return URL when target capture has pcap_url."""
    url = helper.find_capture_url([{"id": "cap-3", "pcap_url": "https://example/cap-3.pcap"}], "cap-3", 1)
    assert url == "https://example/cap-3.pcap"


def test_download_single_pcap_success(helper: PacketCaptureDownloadManager) -> None:
    """Single download should write file and return 1 on HTTP 200."""
    fake_requests = _FakeRequests(_FakeResponse(200, chunks=[b"abc", b"123"]))
    result = helper.download_single_pcap(
        "https://example/cap-4.pcap",
        os.path.join("data", "PacketCapture_cap-4.pcap"),
        "PacketCapture_cap-4.pcap",
        "cap-4",
        requests_module=fake_requests,
    )
    assert result == 1
    assert os.path.exists(os.path.join("data", "PacketCapture_cap-4.pcap"))


def test_download_single_pcap_http_error(helper: PacketCaptureDownloadManager) -> None:
    """Single download should return 0 for non-200 response."""
    fake_requests = _FakeRequests(_FakeResponse(404))
    result = helper.download_single_pcap(
        "https://example/cap-5.pcap",
        os.path.join("data", "PacketCapture_cap-5.pcap"),
        "PacketCapture_cap-5.pcap",
        "cap-5",
        requests_module=fake_requests,
    )
    assert result == 0


def test_fetch_completed_pcaps_filters_to_downloadable_items(helper: PacketCaptureDownloadManager) -> None:
    """Fetch helper should retain only pcap entries with pcap_url."""
    response = SimpleNamespace(
        status_code=200,
        data={
            "results": [
                {"id": "cap-a", "format": "pcap", "pcap_url": "https://example/a.pcap"},
                {"id": "cap-b", "format": "stream"},
            ]
        },
    )
    result = helper.fetch_completed_pcaps(lambda: response, 1)
    assert result == [{"id": "cap-a", "format": "pcap", "pcap_url": "https://example/a.pcap"}]


def test_download_pending_pcaps_skips_existing_files(helper: PacketCaptureDownloadManager) -> None:
    """Pending download scan should skip already-downloaded files."""
    existing = os.path.join("data", "PacketCapture_cap-existing.pcap")
    with open(existing, "wb") as existing_file:
        existing_file.write(b"done")
    calls: list[tuple[str, str, str, str]] = []

    def _fake_download(url: str, local_path: str, filename: str, capture_id: str) -> int:
        calls.append((url, local_path, filename, capture_id))
        return 1

    result = helper.download_pending_pcaps(
        [
            {"id": "cap-existing", "pcap_url": "https://example/existing.pcap"},
            {"id": "cap-new", "pcap_url": "https://example/new.pcap"},
        ],
        "data",
        _fake_download,
    )
    assert result == 1
    assert len(calls) == 1
    assert calls[0][3] == "cap-new"


def test_poll_for_pcap_url_returns_when_url_ready(helper: PacketCaptureDownloadManager) -> None:
    """Polling should return URL once target capture has pcap_url."""
    responses = [
        SimpleNamespace(status_code=200, data={"results": [{"id": "cap-6"}]}),
        SimpleNamespace(
            status_code=200,
            data={"results": [{"id": "cap-6", "pcap_url": "https://example/cap-6.pcap"}]},
        ),
    ]

    def _list_fn():
        return responses.pop(0)

    url = helper.poll_for_pcap_url(_list_fn, "cap-6", duration=1, sleep_fn=lambda _: None)
    assert url == "https://example/cap-6.pcap"


def test_save_pcap_file_writes_expected_name(helper: PacketCaptureDownloadManager) -> None:
    """Final save helper should write canonical prefixed filename."""
    fake_requests = _FakeRequests(_FakeResponse(200, content=b"pcap-bytes"))
    helper.save_pcap_file(
        "https://example/cap-7.pcap",
        "cap-7",
        prefix="org_",
        requests_module=fake_requests,
        output_dir=Path("data"),
    )
    assert os.path.exists(os.path.join("data", "PacketCapture_org_cap-7.pcap"))
