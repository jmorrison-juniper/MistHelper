"""Tests for the table preview of the combined CSV report in the portal (issue #4931)."""

from __future__ import annotations

import csv  # Read the downloaded report to compare it with the preview.
import io  # Wrap the report text for the CSV reader.
import logging  # Check the log lines of the action.
from collections.abc import Iterator  # Type the app fixture.
from pathlib import Path  # Test output stays under the pytest temporary folder.
from types import SimpleNamespace  # Fake services.
from typing import Any  # Doubles have no public type.

import pytest  # Fixtures, parametrization, and errors.

from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError  # Contract errors.
from src.mist.realtime.websocket_streams.web.services.operations.artifacts import SessionArtifactService  # Unit.
from src.mist.realtime.websocket_streams.web.services.registry import WebSocketServiceRegistry  # Inject fakes.
from tests.unit.websocket_streams.web.test_ws_hardware_csv import ORG, finished_run  # Reuse the real run helper.
from web_portal.app import WebPortalApp  # The real portal app for the route tests.
from web_portal.menu_registry import build_static_menu_actions  # Normal menu actions.


def published_rows(artifacts: SessionArtifactService) -> list[list[str]]:
    """Parse the file that the download returns, so the tests compare the table with the file."""
    data = artifacts.csv_download("run")[1]
    return list(csv.reader(io.StringIO(data.decode("utf-8"), newline="")))


class TestPreviewService:
    """The preview reads the published report through the checked read of the download."""

    def test_the_preview_shows_the_same_rows_as_the_published_file(self, tmp_path: Path) -> None:
        """Columns, rows, and the total equal the parsed file, in the same order."""
        artifacts, writer, outcomes = finished_run(tmp_path)
        writer.finish(outcomes)
        artifacts.bind_batch("run", writer)
        file_rows = published_rows(artifacts)
        page = artifacts.csv_preview("run", 0, 1000, "")
        assert page["columns"] == file_rows[0] and page["rows"] == file_rows[1:]
        assert page["total"] == page["matched"] == len(file_rows) - 1 > 2

    def test_the_filter_gives_the_rows_of_the_file_that_hold_the_text(self, tmp_path: Path) -> None:
        """Only the rows of one switch match its name, and the totals still describe the whole file."""
        artifacts, writer, outcomes = finished_run(tmp_path)
        writer.finish(outcomes)
        artifacts.bind_batch("run", writer)
        file_rows = published_rows(artifacts)
        column = file_rows[0].index("device_name")
        expected = [row for row in file_rows[1:] if row[column] == "ex-01"]
        page = artifacts.csv_preview("run", 0, 1000, "EX-01")
        assert page["rows"] == expected and page["matched"] == len(expected) < page["total"]

    def test_a_page_of_one_row_walks_the_whole_file(self, tmp_path: Path) -> None:
        """Pages of one row, joined, give every row of the file once."""
        artifacts, writer, outcomes = finished_run(tmp_path)
        writer.finish(outcomes)
        artifacts.bind_batch("run", writer)
        file_rows = published_rows(artifacts)
        walked = [artifacts.csv_preview("run", index, 1, "")["rows"][0] for index in range(len(file_rows) - 1)]  # type: ignore[index]
        assert walked == file_rows[1:]

    def test_the_preview_waits_for_the_end_of_the_run(self, tmp_path: Path) -> None:
        """Before the finish step, the report is not ready, as for the download."""
        artifacts, writer, _ = finished_run(tmp_path)
        artifacts.bind_batch("run", writer)
        with pytest.raises(StreamRequestError) as refusal:
            artifacts.csv_preview("run", 0, 10, "")
        assert refusal.value.code == "artifact_not_ready"

    def test_an_unknown_session_is_not_a_batch(self, tmp_path: Path) -> None:
        """A session with no bound batch gives the not-a-batch refusal."""
        artifacts, _, _ = finished_run(tmp_path)
        with pytest.raises(StreamRequestError) as refusal:
            artifacts.csv_preview("unknown", 0, 10, "")
        assert refusal.value.code == "not_batch"

    @pytest.mark.parametrize("output_format", ["xml", "json", "both"])
    def test_the_other_outputs_have_no_preview(self, tmp_path: Path, output_format: str) -> None:
        """Xml, json, and both publish no report, so there is nothing to show."""
        artifacts, writer, outcomes = finished_run(tmp_path, output_format)
        writer.finish(outcomes)
        artifacts.bind_batch("run", writer)
        with pytest.raises(StreamRequestError) as refusal:
            artifacts.csv_preview("run", 0, 10, "")
        assert refusal.value.code == "artifact_not_ready"

    def test_a_portal_that_is_not_ready_refuses_the_preview(self, tmp_path: Path) -> None:
        """A portal with no engine has no retained report."""
        artifacts = SessionArtifactService(SimpleNamespace(session=lambda _id: None), "No credential.", tmp_path)
        with pytest.raises(StreamRequestError) as refusal:
            artifacts.csv_preview("run", 0, 10, "")
        assert refusal.value.code == "not_ready" and refusal.value.status == 503

    def test_the_preview_pin_is_released(self, tmp_path: Path) -> None:
        """A preview never leaves the run folder pinned, so a delete is not blocked."""
        artifacts, writer, outcomes = finished_run(tmp_path)
        writer.finish(outcomes)
        artifacts.bind_batch("run", writer)
        artifacts.csv_preview("run", 0, 10, "")
        assert writer._record.pins == 0


class TestPreviewLimits:
    """A report that is too large or damaged gets a plain refusal, and the download stays available."""

    @staticmethod
    def ready_run(tmp_path: Path) -> tuple[SessionArtifactService, Any]:
        """Return an artifact service with one finished and bound run."""
        artifacts, writer, outcomes = finished_run(tmp_path)
        writer.finish(outcomes)
        artifacts.bind_batch("run", writer)
        return artifacts, writer

    def test_a_report_over_the_byte_limit_is_too_large(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """One byte over the limit is refused, and the refusal points to the download."""
        artifacts, writer = self.ready_run(tmp_path)
        size = len(artifacts.csv_download("run")[1])
        monkeypatch.setattr(SessionArtifactService.Preview, "BYTE_LIMIT", size - 1)
        with pytest.raises(StreamRequestError) as refusal:
            artifacts.csv_preview("run", 0, 10, "")
        assert refusal.value.code == "too_large" and "Download the CSV report" in refusal.value.message
        assert refusal.value.status == 413 and writer._record.pins == 0

    def test_a_report_at_the_byte_limit_is_shown(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """The limit is the most bytes that the preview parses, so a file of that size passes."""
        artifacts, _ = self.ready_run(tmp_path)
        size = len(artifacts.csv_download("run")[1])
        monkeypatch.setattr(SessionArtifactService.Preview, "BYTE_LIMIT", size)
        assert artifacts.csv_preview("run", 0, 10, "")["total"] == len(published_rows(artifacts)) - 1

    @pytest.mark.parametrize("damage", [b"", b"a,b\r\n1\r\n", b"a\r\n\xff\xfe\r\n"])
    def test_a_damaged_report_is_refused_and_the_download_still_works(self, tmp_path: Path, damage: bytes) -> None:
        """An empty file, a ragged row, and bytes that are not UTF-8 each give output_failed."""
        artifacts, writer = self.ready_run(tmp_path)
        (writer._record.directory / "hardware" / "inventory.csv").write_bytes(damage)  # Damage the published file.
        with pytest.raises(StreamRequestError) as refusal:
            artifacts.csv_preview("run", 0, 10, "")
        assert refusal.value.code == "output_failed" and writer._record.pins == 0
        assert artifacts.csv_download("run")[1] == damage  # The download is unchanged by the refusal.

    def test_the_log_lines_hold_counts_and_never_the_filter_text(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """One line before and one after, with the matching row count and no text that the operator typed."""
        artifacts, _ = self.ready_run(tmp_path)
        with caplog.at_level(logging.DEBUG):
            artifacts.csv_preview("run", 0, 10, "zz-private-filter-zz")
        assert "web.artifact.preview.start" in caplog.text and "web.artifact.preview.finish" in caplog.text
        assert "zz-private-filter-zz" not in caplog.text and '"count":0' in caplog.text


class FakePreviewArtifacts:
    """Artifact service double that records each preview call."""

    PAGE = {
        "columns": ["a", "b"],
        "rows": [["1", "2"]],
        "offset": 0,
        "limit": 100,
        "total": 1,
        "matched": 1,
        "cut_cells": 0,
    }

    def __init__(self) -> None:
        """Start with a ready report and no call."""
        self.error: StreamRequestError | None = None
        self.calls: list[tuple[str, int, int, str]] = []

    def csv_preview(self, session_id: str, offset: int, limit: int, text: str) -> dict[str, object]:
        """Record the call, then return a page or raise the planned refusal."""
        self.calls.append((session_id, offset, limit, text))
        if self.error is not None:
            raise self.error
        return dict(self.PAGE)


@pytest.fixture
def portal() -> Iterator[tuple[Any, FakePreviewArtifacts]]:
    """Build the real portal app with a fake artifact service."""
    app = WebPortalApp.create_app(apisession=object(), menu_actions=build_static_menu_actions(), org_id=ORG)
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    artifacts = FakePreviewArtifacts()
    lifecycle = SimpleNamespace(shutdown=lambda: None)  # The app teardown stops the sessions.
    app.config[WebSocketServiceRegistry.CONFIG_KEY] = SimpleNamespace(
        artifacts=artifacts, sessions=SimpleNamespace(lifecycle=lifecycle)
    )
    try:
        yield app.test_client(), artifacts
    finally:
        WebPortalApp.shutdown_app(app)


URL = "/api/websockets/batches/abc123/csv-preview"  # The route under test.


class TestPreviewRoute:
    """The route checks the query, calls the service, and keeps the shared error shape."""

    def test_the_default_query_asks_for_the_first_thousand_rows(self, portal: tuple[Any, FakePreviewArtifacts]) -> None:
        """No field means offset 0, a page of 1000, and no filter."""
        client, artifacts = portal
        response = client.get(URL)
        assert response.status_code == 200 and response.mimetype == "application/json"
        assert response.get_json() == FakePreviewArtifacts.PAGE and artifacts.calls == [("abc123", 0, 1000, "")]

    def test_each_field_reaches_the_service(self, portal: tuple[Any, FakePreviewArtifacts]) -> None:
        """The offset, the limit, and the filter text pass on unchanged."""
        client, artifacts = portal
        assert client.get(URL + "?offset=200&limit=50&q=ex-01").status_code == 200
        assert artifacts.calls == [("abc123", 200, 50, "ex-01")]

    @pytest.mark.parametrize("sent, kept", [("1", 1), ("1000", 1000), ("1001", 1000), ("999999", 1000)])
    def test_the_limit_is_cut_to_one_thousand(
        self, portal: tuple[Any, FakePreviewArtifacts], sent: str, kept: int
    ) -> None:
        """A page of more than 1000 rows becomes a page of 1000, and 1 and 1000 pass."""
        client, artifacts = portal
        assert client.get(f"{URL}?limit={sent}").status_code == 200
        assert artifacts.calls[0][2] == kept

    @pytest.mark.parametrize(
        "query",
        ["?offset=-1", "?limit=0", "?limit=-1", "?offset=abc", "?limit=1.5", "?limit=", "?offset=", "?limit=%20x"],
    )
    def test_a_bad_position_or_size_is_refused_before_the_service(
        self, portal: tuple[Any, FakePreviewArtifacts], query: str
    ) -> None:
        """A negative, a zero, or a text value gives HTTP 400, and no file is read."""
        client, artifacts = portal
        response = client.get(URL + query)
        assert response.status_code == 400 and response.get_json()["code"] == "bad_request"
        assert artifacts.calls == []

    @pytest.mark.parametrize("query", ["?format=csv", "?sort=name", "?offset=0&x=1", "?Q=a"])
    def test_an_unknown_field_is_refused(self, portal: tuple[Any, FakePreviewArtifacts], query: str) -> None:
        """Only offset, limit, and q are accepted. A field name is case sensitive."""
        client, artifacts = portal
        response = client.get(URL + query)
        assert response.status_code == 400 and "unknown query field" in response.get_json()["error"]
        assert artifacts.calls == []

    def test_a_filter_of_one_hundred_characters_passes_and_one_more_is_refused(
        self, portal: tuple[Any, FakePreviewArtifacts]
    ) -> None:
        """The filter text is bounded to 100 characters."""
        client, artifacts = portal
        assert client.get(URL + "?q=" + "a" * 100).status_code == 200
        refused = client.get(URL + "?q=" + "a" * 101)
        assert refused.status_code == 400 and refused.get_json()["code"] == "bad_request"
        assert len(artifacts.calls) == 1

    def test_a_filter_with_url_encoded_text_arrives_decoded(self, portal: tuple[Any, FakePreviewArtifacts]) -> None:
        """A space and a percent sign are plain text for the service."""
        client, artifacts = portal
        client.get(URL + "?q=ex%2001%25")
        assert artifacts.calls[0][3] == "ex 01%"

    @pytest.mark.parametrize(
        "code, status",
        [
            ("artifact_not_ready", 409),
            ("not_batch", 409),
            ("too_large", 413),
            ("output_failed", 507),
            ("not_ready", 503),
        ],
    )
    def test_a_service_refusal_reaches_the_browser_with_its_status(
        self, portal: tuple[Any, FakePreviewArtifacts], code: str, status: int
    ) -> None:
        """The shared error shape carries the code and the plain message."""
        client, artifacts = portal
        artifacts.error = StreamRequestError(code, "A plain reason.")
        response = client.get(URL)
        assert response.status_code == status and response.get_json() == {"error": "A plain reason.", "code": code}

    @pytest.mark.parametrize("method", ["post", "put", "delete"])
    def test_only_a_read_is_allowed(self, portal: tuple[Any, FakePreviewArtifacts], method: str) -> None:
        """The route changes nothing, so every other method is refused."""
        client, artifacts = portal
        assert getattr(client, method)(URL).status_code == 405
        assert artifacts.calls == []
