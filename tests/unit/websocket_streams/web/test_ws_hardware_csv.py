"""Tests for the combined CSV output of the Multi Site hardware action (issue #4920)."""

from __future__ import annotations

import csv  # Read the published report the way a spreadsheet would.
import io  # Wrap the report bytes for the CSV reader.
import json  # Read the manifest of the run folder.
import zipfile  # Check the archive entries.
from collections.abc import Iterator  # Type the app fixture.
from io import BytesIO  # Wrap archive bytes.
from pathlib import Path  # Test output stays under the pytest temporary folder.
from types import SimpleNamespace  # Targets, sessions, and fake services.
from typing import Any  # Doubles have no public type.

import pytest  # Fixtures, parametrization, and errors.

from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError  # Contract errors.
from src.mist.realtime.websocket_streams.web.services.operations.artifacts import SessionArtifactService  # Unit.
from src.mist.realtime.websocket_streams.web.services.operations.hardware_xml import (
    HardwareXmlPreset,
    HardwareXmlSupport,
)  # The preset and the decoder.
from src.mist.realtime.websocket_streams.web.services.registry import WebSocketServiceRegistry  # Inject fakes.
from src.operations.exporting.ex_hardware_inventory.run.publisher import ReportHook  # Make the compile fail.
from tests.unit.ex_hardware_inventory.support.hardware_replies import HardwareReplies  # Invented replies.
from tests.unit.websocket_streams.web.test_ws_web_services import (
    FakeBatchChecker,
    FakeBatchPicker,
    FakeManager,
    hardware_shell_definition,
    make_batch_service,
)  # Reuse the portal service fixtures.
from web_portal.app import WebPortalApp  # The real portal app for the route tests.
from web_portal.menu_registry import build_static_menu_actions  # Normal menu actions.

ORG = "11111111-1111-4111-8111-111111111111"  # An invented organization.
PROMPT = "switch@site>"  # The prompt that the decoder expects after a reply.
CSV_NAME = "hardware/inventory.csv"  # The published report, relative to the run folder.
SCOPE = {"mode": "organization", "organizations": {ORG: "Alpha Org"}}  # What the service stores at the start.


def decode(xml: str):
    """Decode one framed reply the way the batch runner does."""
    return HardwareXmlSupport.Decoder.decode_output((xml + "\n" + PROMPT).encode(), PROMPT, HardwareXmlPreset.COMMAND)


def finished_run(
    tmp_path: Path, output_format: str = "csv", devices: int = 2, scope: dict | None = SCOPE
) -> tuple[SessionArtifactService, Any, list[dict]]:
    """Run two switches through the real artifact service and close the run."""
    artifacts = SessionArtifactService(SimpleNamespace(session=lambda _id: SimpleNamespace(live=False)), None, tmp_path)
    targets = tuple(
        SimpleNamespace(
            target_key=f"key-{index}",
            identity={
                "org_id": ORG,
                "site_id": f"site-{index}",
                "site_label": f"Site {index}",
                "device_id": f"device-{index}",
                "label": f"ex-{index:02d}",
            },
        )
        for index in range(1, devices + 1)
    )
    output: dict[str, Any] = {"preset": HardwareXmlPreset.NAME, "format": output_format, "mode": "combined"}
    if scope is not None:
        output["scope"] = scope
    writer = artifacts.prepare_batch(targets, output)
    outcomes = []
    for target in targets:
        files = writer.write_hardware(
            target.target_key,
            target.identity,
            decode(HardwareReplies.single_switch(target.identity["device_id"])),
            "xml",
        )
        outcomes.append({"target": dict(target.identity), "state": "completed", "files": list(files)})
    return artifacts, writer, outcomes


def rows_of(data: bytes) -> list[dict[str, str]]:
    """Parse report bytes into dictionaries."""
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"), newline="")))


class TestCsvFormat:
    """The preset accepts the csv format and keeps the one fixed XML command."""

    def test_the_csv_format_is_accepted_and_runs_only_the_xml_command(self) -> None:
        """A csv request builds the same batch request as xml: one command, the XML one."""
        preset = HardwareXmlPreset()
        selection = preset.parse({"preset": "ex-hardware-xml", "format": "csv", "scope_revision": 3})
        assert selection.output_format == "csv" and selection.scope_revision == 3
        assert preset.batch_request(selection)["commands"] == [HardwareXmlPreset.COMMANDS["xml"]]

    @pytest.mark.parametrize("output_format", ["yaml", "CSV", "", None, 3])
    def test_other_formats_are_still_refused(self, output_format: object) -> None:
        """Only xml, json, both, and csv pass. The refusal is the established bad request."""
        with pytest.raises(StreamRequestError) as refusal:
            HardwareXmlPreset().parse({"preset": "ex-hardware-xml", "format": output_format, "scope_revision": 0})
        assert refusal.value.code == "bad_request"

    def test_the_formats_that_exist_before_this_change_keep_their_commands(self) -> None:
        """Xml, json, and both build the same command lists as before."""
        preset = HardwareXmlPreset()
        built = {
            name: preset.batch_request(
                preset.parse({"preset": "ex-hardware-xml", "format": name, "scope_revision": 0})
            )["commands"]
            for name in ("xml", "json", "both")
        }
        assert built["xml"] == [HardwareXmlPreset.COMMANDS["xml"]]
        assert built["json"] == [HardwareXmlPreset.COMMANDS["json"]]
        assert built["both"] == [HardwareXmlPreset.COMMANDS["xml"], HardwareXmlPreset.COMMANDS["json"]]

    def test_the_preview_with_csv_freezes_the_xml_command(self, tmp_path: Path) -> None:
        """The preview shows the format and the one fixed command, and the snapshot keeps both."""
        service = make_batch_service(
            FakeBatchChecker(hardware_shell_definition()), FakeBatchPicker(device_target=True), FakeManager(), tmp_path
        )
        payload = service.preview({"preset": "ex-hardware-xml", "format": "csv", "scope_revision": 1})
        record = next(iter(service._previews.records.values()))
        assert payload["format"] == "csv" and payload["fixed_commands"] == [HardwareXmlPreset.COMMANDS["xml"]]
        assert record.commands == (HardwareXmlPreset.COMMANDS["xml"],) and record.output_format == "csv"


class TestFinishStep:
    """The finish step publishes the combined CSV next to the saved replies."""

    def test_the_report_is_published_listed_in_the_manifest_and_archived(self, tmp_path: Path) -> None:
        """One CSV with a row for each hardware item, listed in the manifest and in the archive."""
        artifacts, writer, outcomes = finished_run(tmp_path)
        writer.finish(outcomes)
        artifacts.bind_batch("run", writer)
        manifest = artifacts.manifest("run")
        assert CSV_NAME in manifest["files"] and manifest["status"] == "ready" and manifest["partial"] is False
        assert len([name for name in manifest["files"] if name.endswith(".xml")]) == 2  # The replies stay.
        name, data = artifacts.csv_download("run")
        rows = rows_of(data)
        assert name.startswith("ExHardwareInventory_") and name.endswith(".csv")
        assert {row["org_name"] for row in rows} == {"Alpha Org"} and {row["device_name"] for row in rows} == {
            "ex-01",
            "ex-02",
        }
        assert {row["record_type"] for row in rows} == {"hardware_item"} and {row["scope"] for row in rows} == {
            "organization"
        }
        with zipfile.ZipFile(BytesIO(artifacts.zip_download("run")[1])) as archive:
            assert CSV_NAME in archive.namelist() and "manifest.json" in archive.namelist()

    def test_a_target_without_a_reply_is_an_outcome_row_and_the_run_is_partial(self, tmp_path: Path) -> None:
        """A failed switch gives one outcome row. The manifest marks the run partial."""
        artifacts, writer, outcomes = finished_run(tmp_path)
        outcomes.append(
            {
                "target": {"org_id": ORG, "site_id": "site-9", "device_id": "device-9", "label": "ex-09"},
                "state": "failed",
                "reason_code": "completion_unproven",
                "files": [],
            }
        )
        writer.finish(outcomes)
        artifacts.bind_batch("run", writer)
        rows = rows_of(artifacts.csv_download("run")[1])
        failed = [row for row in rows if row["device_name"] == "ex-09"]
        assert len(failed) == 1 and failed[0]["record_type"] == "device_outcome"
        assert failed[0]["collection_detail"] == "The shell did not show a stable prompt."
        assert artifacts.manifest("run")["partial"] is True

    def test_a_failed_organization_in_the_scope_is_one_outcome_row(self, tmp_path: Path) -> None:
        """The scope that the service stored lists an organization that Mist could not read."""
        scope = {
            "mode": "msp",
            "organizations": {ORG: "Alpha Org", "org-2": "Beta Org"},
            "failed": {"org-2": "discovery_failed"},
        }
        artifacts, writer, outcomes = finished_run(tmp_path, scope=scope)
        writer.finish(outcomes)
        artifacts.bind_batch("run", writer)
        rows = rows_of(artifacts.csv_download("run")[1])
        assert [row["org_name"] for row in rows if row["record_type"] == "device_outcome"] == ["Beta Org"]
        assert {row["scope"] for row in rows} == {"msp"}

    def test_a_missing_scope_still_publishes_with_the_identifier_as_the_name(self, tmp_path: Path) -> None:
        """A run with no stored scope is an organization run, and the name is the identifier."""
        artifacts, writer, outcomes = finished_run(tmp_path, scope=None)
        writer.finish(outcomes)
        artifacts.bind_batch("run", writer)
        assert {row["org_name"] for row in rows_of(artifacts.csv_download("run")[1])} == {ORG}

    @pytest.mark.parametrize("output_format", ["xml", "json", "both"])
    def test_the_other_formats_publish_no_csv(self, tmp_path: Path, output_format: str) -> None:
        """Xml, json, and both write the same files as before, and no report."""
        artifacts, writer, outcomes = finished_run(tmp_path, output_format)
        writer.finish(outcomes)
        artifacts.bind_batch("run", writer)
        assert CSV_NAME not in artifacts.manifest("run")["files"]
        with pytest.raises(StreamRequestError) as refusal:
            artifacts.csv_download("run")
        assert refusal.value.code == "artifact_not_ready"

    def test_a_compile_failure_fails_the_artifact_and_keeps_the_xml_files(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Any compile error becomes output_failed, the manifest says failed, and the replies stay."""
        artifacts, writer, outcomes = finished_run(tmp_path)

        def explode(*_args: object, **_kwargs: object) -> bytes:
            """Fail like a broken compile."""
            raise ValueError("boom")

        monkeypatch.setattr(ReportHook, "compile", explode)
        with pytest.raises(StreamRequestError) as refusal:
            writer.finish(outcomes)
        assert refusal.value.code == "output_failed"
        artifacts.bind_batch("run", writer)
        manifest = artifacts.manifest("run")
        assert manifest["status"] == "failed" and manifest["partial"] is True
        assert CSV_NAME not in manifest["files"] and len([n for n in manifest["files"] if n.endswith(".xml")]) == 2
        assert not list(tmp_path.rglob("inventory.csv"))  # No partial file under the final name.
        on_disk = json.loads(next(tmp_path.glob("*/manifest.json")).read_text(encoding="utf-8"))
        assert on_disk["status"] == "failed"

    def test_the_remaining_quota_limits_the_report_and_no_partial_file_appears(self, tmp_path: Path) -> None:
        """A report that does not fit in the run quota fails the artifact."""
        artifacts, writer, outcomes = finished_run(tmp_path)
        artifacts.OUTPUT_LIMIT = writer._record.bytes_written + 200  # Room for 200 bytes after the replies.
        with pytest.raises(StreamRequestError) as refusal:
            writer.finish(outcomes)
        assert refusal.value.code == "output_failed"
        assert not list(tmp_path.rglob("inventory.csv")) and not list(tmp_path.rglob("*.tmp"))

    def test_a_publication_error_removes_every_partial_file(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An error while the file is published leaves no report and no temporary file."""
        import os

        artifacts, writer, outcomes = finished_run(tmp_path)
        real_replace = os.replace

        def fail_for_the_report(source: Any, destination: Any) -> None:
            """Fail only the report publication."""
            if str(destination).endswith("inventory.csv"):
                raise OSError("simulated")
            real_replace(source, destination)

        monkeypatch.setattr(os, "replace", fail_for_the_report)
        with pytest.raises(StreamRequestError):
            writer.finish(outcomes)
        assert not list(tmp_path.rglob("inventory.csv")) and not list(tmp_path.rglob("*.tmp"))


class TestCsvDownload:
    """The report is offered for download only when the run is complete."""

    def test_the_download_waits_for_the_end_of_the_run(self, tmp_path: Path) -> None:
        """Before the finish step, the report is not ready."""
        artifacts, writer, _ = finished_run(tmp_path)
        artifacts.bind_batch("run", writer)
        with pytest.raises(StreamRequestError) as refusal:
            artifacts.csv_download("run")
        assert refusal.value.code == "artifact_not_ready"

    def test_an_unknown_session_is_not_a_batch(self, tmp_path: Path) -> None:
        """A session with no bound batch gives the not-a-batch refusal."""
        artifacts, _, _ = finished_run(tmp_path)
        with pytest.raises(StreamRequestError) as refusal:
            artifacts.csv_download("unknown")
        assert refusal.value.code == "not_batch"

    def test_the_download_pin_is_released(self, tmp_path: Path) -> None:
        """A download never leaves the run folder pinned."""
        artifacts, writer, outcomes = finished_run(tmp_path)
        writer.finish(outcomes)
        artifacts.bind_batch("run", writer)
        artifacts.csv_download("run")
        assert writer._record.pins == 0


class FakeCsvArtifacts:
    """Artifact service double for the route tests."""

    def __init__(self) -> None:
        """Start with a ready report."""
        self.error: StreamRequestError | None = None

    def csv_download(self, session_id: str) -> tuple[str, bytes]:
        """Return a report, or raise the planned refusal."""
        if self.error is not None:
            raise self.error
        return "ExHardwareInventory_20261124T000000Z.csv", b"a,b\r\n1,2\r\n"

    def zip_download(self, session_id: str) -> tuple[str, bytes]:
        """Return an archive."""
        return "websocket-batch.zip", b"zip"


@pytest.fixture
def portal() -> Iterator[tuple[Any, FakeCsvArtifacts]]:
    """Build the real portal app with fake artifact services."""
    app = WebPortalApp.create_app(apisession=object(), menu_actions=build_static_menu_actions(), org_id=ORG)
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    artifacts = FakeCsvArtifacts()
    lifecycle = SimpleNamespace(shutdown=lambda: None)  # The app teardown stops the sessions.
    app.config[WebSocketServiceRegistry.CONFIG_KEY] = SimpleNamespace(
        artifacts=artifacts, sessions=SimpleNamespace(lifecycle=lifecycle)
    )
    try:
        yield app.test_client(), artifacts
    finally:
        WebPortalApp.shutdown_app(app)


class TestDownloadRoute:
    """The batch download route serves zip and csv, and nothing else."""

    def test_format_csv_returns_a_csv_attachment(self, portal: tuple[Any, FakeCsvArtifacts]) -> None:
        """The response is text/csv with a server-made attachment name."""
        client, _ = portal
        response = client.get("/api/websockets/batches/abc123/download?format=csv")
        assert response.status_code == 200 and response.mimetype == "text/csv"
        assert (
            response.headers["Content-Disposition"] == "attachment; filename=ExHardwareInventory_20261124T000000Z.csv"
        )
        assert response.get_data() == b"a,b\r\n1,2\r\n"

    def test_format_zip_still_returns_the_archive(self, portal: tuple[Any, FakeCsvArtifacts]) -> None:
        """The archive download is unchanged."""
        client, _ = portal
        response = client.get("/api/websockets/batches/abc123/download?format=zip")
        assert response.status_code == 200 and response.mimetype == "application/zip"

    @pytest.mark.parametrize("query", ["", "?format=txt", "?format=csv&x=1", "?format=CSV", "?x=1"])
    def test_any_other_query_is_refused(self, portal: tuple[Any, FakeCsvArtifacts], query: str) -> None:
        """Only format=zip and format=csv are accepted, with no other field."""
        client, _ = portal
        response = client.get("/api/websockets/batches/abc123/download" + query)
        assert response.status_code == 400 and response.get_json()["code"] == "bad_request"

    def test_a_report_that_is_not_ready_is_a_conflict(self, portal: tuple[Any, FakeCsvArtifacts]) -> None:
        """The service refusal reaches the browser with its status."""
        client, artifacts = portal
        artifacts.error = StreamRequestError("artifact_not_ready", "The combined CSV report is not ready.")
        response = client.get("/api/websockets/batches/abc123/download?format=csv")
        assert response.status_code == 409 and response.get_json()["code"] == "artifact_not_ready"
