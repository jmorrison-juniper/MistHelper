"""Tests for the combined XML output of the Multi Site hardware action (issue #4933).

Why:
    The master XML is a second report of the finish step. These tests prove that the preset accepts its two
    formats, that the finish step publishes the files together or not at all, that the download refuses before
    the end of the run, and that no other format writes the file. Every value here is invented.
"""

from __future__ import annotations

import json  # Read the manifest of the run folder.
import os  # Fail the publication of one file.
import xml.etree.ElementTree as ET  # A standard reader, so the tests share no code with the XML writer.
import zipfile  # Check the archive entries.
from io import BytesIO  # Wrap archive bytes.
from pathlib import Path  # Test output stays under the pytest temporary folder.
from typing import Any  # Doubles have no public type.

import pytest  # Fixtures, parametrization, and errors.

from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError  # Contract errors.
from src.mist.realtime.websocket_streams.web.services.operations.artifacts import BatchArtifactStorage
from src.mist.realtime.websocket_streams.web.services.operations.hardware_xml import HardwareXmlPreset
from src.operations.exporting.ex_hardware_inventory.report.csv_file import ReportCheckError  # A sentence without data.
from src.operations.exporting.ex_hardware_inventory.run.master_xml import MasterXmlBuilder
from src.operations.exporting.ex_hardware_inventory.run.publisher import ReportHook  # Make one compile fail.
from tests.unit.websocket_streams.web.test_ws_hardware_csv import SCOPE, finished_run, rows_of

CSV_NAME = "hardware/inventory.csv"  # The CSV report, relative to the run folder.
XML_NAME = "hardware/inventory.xml"  # The master XML file, relative to the run folder.
NS = {"mh": MasterXmlBuilder.NAMESPACE}  # The prefix map for the wrapper elements.


def published(artifacts: Any, writer: Any, outcomes: list[dict]) -> dict[str, Any]:
    """Finish the run, bind it as one public session, and return its manifest."""
    writer.finish(outcomes)
    artifacts.bind_batch("run", writer)
    return artifacts.manifest("run")  # type: ignore[no-any-return]


class TestMasterXmlFormats:
    """The preset accepts the two formats and runs the one fixed XML command for each."""

    @pytest.mark.parametrize("output_format", ["master-xml", "csv-master-xml"])
    def test_the_format_is_accepted_and_runs_only_the_xml_command(self, output_format: str) -> None:
        """A combined report is compiled from the saved XML, so no JSON command runs."""
        preset = HardwareXmlPreset()
        selection = preset.parse({"preset": "ex-hardware-xml", "format": output_format, "scope_revision": 2})
        assert selection.output_format == output_format and selection.scope_revision == 2
        assert preset.batch_request(selection)["commands"] == [HardwareXmlPreset.COMMANDS["xml"]]

    @pytest.mark.parametrize(
        "output_format", ["MASTER-XML", "master_xml", "xml-master", "csv-xml", "master-xml ", "", None, 3]
    )
    def test_a_name_that_is_not_in_the_list_is_refused_with_the_established_error(self, output_format: object) -> None:
        """The refusal is the bad request that names every legal value."""
        with pytest.raises(StreamRequestError) as refusal:
            HardwareXmlPreset().parse({"preset": "ex-hardware-xml", "format": output_format, "scope_revision": 0})
        assert refusal.value.code == "bad_request" and "CSV-MASTER-XML" in str(refusal.value)

    @pytest.mark.parametrize("body", [None, {}, [], "", {"preset": "ex-hardware-xml", "format": "master-xml"}])
    def test_a_missing_or_empty_request_is_refused_and_a_missing_revision_too(self, body: object) -> None:
        """No body, an empty body, and a body without the revision never start a master XML run."""
        with pytest.raises(StreamRequestError) as refusal:
            HardwareXmlPreset().parse(body)
        assert refusal.value.code == "bad_request"

    def test_the_report_kinds_of_each_format_are_exactly_these(self) -> None:
        """The table that the finish step reads: the CSV formats and the XML formats publish, the others do not."""
        assert HardwareXmlPreset.REPORT_KINDS == {
            "csv": ("csv",),
            "master-xml": ("xml",),
            "csv-master-xml": ("csv", "xml"),
        }
        assert set(HardwareXmlPreset.REPORT_KINDS) <= HardwareXmlPreset.FORMATS
        assert set(HardwareXmlPreset.COMMAND_FORMATS) == set(HardwareXmlPreset.FORMATS)  # No format lacks a command.


class TestFinishStep:
    """The finish step publishes the master XML next to the saved replies, with the CSV report when asked."""

    def test_the_master_xml_alone_is_published_listed_downloaded_and_archived(self, tmp_path: Path) -> None:
        """One valid file, listed in the manifest and in the archive, and no CSV report."""
        artifacts, writer, outcomes = finished_run(tmp_path, "master-xml")
        manifest = published(artifacts, writer, outcomes)
        assert XML_NAME in manifest["files"] and CSV_NAME not in manifest["files"]
        assert manifest["status"] == "ready" and manifest["partial"] is False
        assert len([name for name in manifest["files"] if name.endswith(".xml")]) == 3  # Two replies and the master.
        name, data = artifacts.xml_download("run")
        root = ET.fromstring(data)  # A standard reader accepts the bytes.
        assert name.startswith("ExHardwareInventory_") and name.endswith(".xml")
        assert data.startswith(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        assert (root.get("scope"), root.get("devices"), root.get("collected")) == ("organization", "2", "2")
        assert [d.get("name") for d in root.iterfind(".//mh:device", NS)] == ["ex-01", "ex-02"]
        with zipfile.ZipFile(BytesIO(artifacts.zip_download("run")[1])) as archive:
            assert XML_NAME in archive.namelist() and archive.read(XML_NAME) == data

    def test_both_reports_are_published_together_and_agree(self, tmp_path: Path) -> None:
        """The CSV report and the master XML name the same devices."""
        artifacts, writer, outcomes = finished_run(tmp_path, "csv-master-xml")
        manifest = published(artifacts, writer, outcomes)
        assert {CSV_NAME, XML_NAME} <= set(manifest["files"]) and manifest["status"] == "ready"
        csv_devices = {row["device_name"] for row in rows_of(artifacts.csv_download("run")[1])}
        xml_devices = {
            d.get("name") for d in ET.fromstring(artifacts.xml_download("run")[1]).iterfind(".//mh:device", NS)
        }
        assert csv_devices == xml_devices == {"ex-01", "ex-02"}

    def test_a_failed_target_and_a_failed_organization_are_elements_with_reasons(self, tmp_path: Path) -> None:
        """The scope that the service stored lists an organization that Mist could not read."""
        org_id = next(iter(SCOPE["organizations"]))  # The one organization that has switches.
        scope = {"mode": "msp", "organizations": {org_id: "Alpha Org"}, "failed": {"org-2": "discovery_failed"}}
        artifacts, writer, outcomes = finished_run(tmp_path, "master-xml", scope=scope)
        outcomes.append(
            {
                "target": {"org_id": org_id, "site_id": "site-9", "device_id": "device-9", "label": "ex-09"},
                "state": "failed",
                "reason_code": "completion_unproven",
                "files": [],
            }
        )
        assert published(artifacts, writer, outcomes)["partial"] is True
        root = ET.fromstring(artifacts.xml_download("run")[1])
        counts = (root.get("scope"), root.get("unread"), root.get("failed"), root.get("collected"))
        assert counts == ("msp", "1", "1", "2")  # The unread organization is not a device.
        failed_device = next(d for d in root.iterfind(".//mh:device", NS) if d.get("name") == "ex-09")
        assert failed_device.get("detail") == "The shell did not show a stable prompt." and len(failed_device) == 0
        unread = [o for o in root.iterfind("mh:organization", NS) if o.get("status") == "failed"]
        assert [o.get("id") for o in unread] == ["org-2"] and unread[0].get("reason") == "discovery_failed"

    def test_a_missing_scope_still_publishes_with_the_identifier_as_the_organization_name(self, tmp_path: Path) -> None:
        """A run with no stored scope is an organization run, and the name of the organization is its identifier."""
        artifacts, writer, outcomes = finished_run(tmp_path, "master-xml", scope=None)
        assert published(artifacts, writer, outcomes)["status"] == "ready"
        root = ET.fromstring(artifacts.xml_download("run")[1])
        organization = root.find("mh:organization", NS)
        assert root.get("scope") == "organization" and isinstance(organization, ET.Element)
        assert organization.get("name") == organization.get("id") == next(iter(SCOPE["organizations"]))

    @pytest.mark.parametrize("stored_format", ["", "unknown", "MASTER-XML"])
    def test_an_empty_or_unknown_stored_format_publishes_no_report_and_fails_nothing(
        self, tmp_path: Path, stored_format: str
    ) -> None:
        """The finish step reads the stored format. A value that names no report gives no report and no error."""
        artifacts, writer, outcomes = finished_run(tmp_path, stored_format)
        manifest = published(artifacts, writer, outcomes)
        assert manifest["status"] == "ready" and not {CSV_NAME, XML_NAME} & set(manifest["files"])
        with pytest.raises(StreamRequestError) as refusal:
            artifacts.xml_download("run")
        assert refusal.value.code == "artifact_not_ready"

    @pytest.mark.parametrize("damage", [b"", b"   \n", b"<broken", b'<?xml version="1.0"?>'])
    def test_a_saved_reply_that_was_damaged_after_the_run_is_one_failed_device_in_both_reports(
        self, tmp_path: Path, damage: bytes
    ) -> None:
        """An empty or truncated file under the run folder fails its device. The other device and the CSV agree."""
        artifacts, writer, outcomes = finished_run(tmp_path, "csv-master-xml")
        next(tmp_path.glob("*/hardware/ex-01--*.xml")).write_bytes(damage)  # The disk lost the reply of ex-01.
        published(artifacts, writer, outcomes)
        root = ET.fromstring(artifacts.xml_download("run")[1])
        devices = {d.get("name"): d for d in root.iterfind(".//mh:device", NS)}
        assert devices["ex-01"].get("status") == "failed" and devices["ex-01"].get("reason") == "reply_unreadable"
        assert devices["ex-01"].get("detail") == "The saved reply could not be read." and len(devices["ex-01"]) == 0
        assert devices["ex-02"].get("status") == "collected" and len(devices["ex-02"]) == 1
        csv_status = {row["device_name"]: row["collection_status"] for row in rows_of(artifacts.csv_download("run")[1])}
        assert csv_status == {"ex-01": "failed", "ex-02": "collected"}  # The two reports tell the same story.

    @pytest.mark.parametrize("output_format", ["xml", "json", "both", "csv"])
    def test_the_other_formats_publish_no_master_xml(self, tmp_path: Path, output_format: str) -> None:
        """The existing formats write the same files as before."""
        artifacts, writer, outcomes = finished_run(tmp_path, output_format)
        assert XML_NAME not in published(artifacts, writer, outcomes)["files"]
        with pytest.raises(StreamRequestError) as refusal:
            artifacts.xml_download("run")
        assert refusal.value.code == "artifact_not_ready"

    def test_the_csv_only_format_still_publishes_only_the_csv(self, tmp_path: Path) -> None:
        """The change did not alter the CSV format."""
        artifacts, writer, outcomes = finished_run(tmp_path, "csv")
        manifest = published(artifacts, writer, outcomes)
        assert CSV_NAME in manifest["files"] and XML_NAME not in manifest["files"]

    def test_the_log_names_the_failed_check_of_a_report_and_never_the_text_of_another_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A report error holds a sentence without data, so the log carries it. Any other error logs its kind only."""
        for error, logged, hidden in (
            (ReportCheckError("Embedded reply 3 differs from its source."), "Embedded reply 3 differs", ""),
            (ValueError("SECRET-TEXT-OF-ANOTHER-ERROR"), "ValueError", "SECRET-TEXT-OF-ANOTHER-ERROR"),
        ):
            caplog.clear()
            artifacts, writer, outcomes = finished_run(tmp_path, "master-xml")

            def explode(*_args: object, _error: Exception = error, **_kwargs: object) -> bytes:
                """Fail with the planned error."""
                raise _error

            monkeypatch.setattr(ReportHook, "compile_xml", explode)
            with caplog.at_level("ERROR"), pytest.raises(StreamRequestError):
                writer.finish(outcomes)
            assert logged in caplog.text and (not hidden or hidden not in caplog.text)

    def test_one_report_that_does_not_fit_fails_the_run_and_publishes_neither(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A small CSV fits, and the XML does not. The run fails, and the CSV is not published either."""
        artifacts, writer, outcomes = finished_run(tmp_path, "csv-master-xml")
        monkeypatch.setattr(ReportHook, "compile", lambda self, outcomes, limit: b"a,b\r\n")  # A CSV of 5 bytes.
        artifacts.OUTPUT_LIMIT = writer._record.bytes_written + 100  # Room for the small CSV, and not for the XML.
        with pytest.raises(StreamRequestError) as refusal:
            writer.finish(outcomes)
        assert refusal.value.code == "output_failed"
        assert not list(tmp_path.rglob("inventory.*")) and not list(tmp_path.rglob("*.tmp"))
        artifacts.bind_batch("run", writer)
        manifest = artifacts.manifest("run")
        assert manifest["status"] == "failed" and len([n for n in manifest["files"] if n.endswith(".xml")]) == 2

    def test_a_compile_failure_of_the_xml_fails_the_run_and_keeps_the_replies(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Any error of the XML compile becomes output_failed, and the CSV that compiled first is not published."""
        artifacts, writer, outcomes = finished_run(tmp_path, "csv-master-xml")

        def explode(*_args: object, **_kwargs: object) -> bytes:
            """Fail like a broken compile."""
            raise ValueError("boom")

        monkeypatch.setattr(ReportHook, "compile_xml", explode)
        with pytest.raises(StreamRequestError) as refusal:
            writer.finish(outcomes)
        assert refusal.value.code == "output_failed"
        artifacts.bind_batch("run", writer)
        manifest = artifacts.manifest("run")
        assert manifest["status"] == "failed" and manifest["partial"] is True
        assert CSV_NAME not in manifest["files"] and XML_NAME not in manifest["files"]
        assert not list(tmp_path.rglob("inventory.*"))
        assert json.loads(next(tmp_path.glob("*/manifest.json")).read_text(encoding="utf-8"))["status"] == "failed"

    def test_a_publication_error_of_one_file_removes_both(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An error while the second file is published rolls the first one back."""
        artifacts, writer, outcomes = finished_run(tmp_path, "csv-master-xml")
        real_replace = os.replace

        def fail_for_the_xml(source: Any, destination: Any) -> None:
            """Fail only the publication of the master XML."""
            if str(destination).endswith("inventory.xml"):
                raise OSError("simulated")
            real_replace(source, destination)

        monkeypatch.setattr(os, "replace", fail_for_the_xml)
        with pytest.raises(StreamRequestError):
            writer.finish(outcomes)
        assert not list(tmp_path.rglob("inventory.*")) and not list(tmp_path.rglob("*.tmp"))


class TestXmlDownload:
    """The master XML is offered only when the run is complete, and the pin is always released."""

    def test_the_download_waits_for_the_end_of_the_run(self, tmp_path: Path) -> None:
        """Before the finish step, the file is not ready."""
        artifacts, writer, _ = finished_run(tmp_path, "master-xml")
        artifacts.bind_batch("run", writer)
        with pytest.raises(StreamRequestError) as refusal:
            artifacts.xml_download("run")
        assert refusal.value.code == "artifact_not_ready" and "combined XML file" in str(refusal.value)

    @pytest.mark.parametrize("session_id", ["unknown", "", None])
    def test_an_unknown_empty_or_missing_session_is_not_a_batch(self, tmp_path: Path, session_id: object) -> None:
        """A session with no bound batch gives the not-a-batch refusal, whatever the identifier is."""
        artifacts, _, _ = finished_run(tmp_path, "master-xml")
        with pytest.raises(StreamRequestError) as refusal:
            artifacts.xml_download(session_id)
        assert refusal.value.code == "not_batch"

    def test_the_download_pin_is_released_after_success_and_after_a_failed_read(self, tmp_path: Path) -> None:
        """A download never leaves the run folder pinned, even when the file cannot be read."""
        artifacts, writer, outcomes = finished_run(tmp_path, "master-xml")
        published(artifacts, writer, outcomes)
        artifacts.xml_download("run")
        assert writer._record.pins == 0
        next(tmp_path.glob("*/hardware/inventory.xml")).unlink()  # The file is listed, and the disk lost it.
        with pytest.raises(OSError):
            artifacts.xml_download("run")
        assert writer._record.pins == 0

    def test_the_download_bytes_are_the_published_bytes_and_are_read_through_the_checked_path(
        self, tmp_path: Path
    ) -> None:
        """The service returns exactly what the run folder holds."""
        artifacts, writer, outcomes = finished_run(tmp_path, "master-xml")
        published(artifacts, writer, outcomes)
        (on_disk,) = tmp_path.glob("*/hardware/inventory.xml")
        assert artifacts.xml_download("run")[1] == on_disk.read_bytes()

    def test_a_download_of_a_file_over_the_output_limit_is_refused(self, tmp_path: Path) -> None:
        """The read has the same size limit as every other download of the run folder."""
        artifacts, writer, outcomes = finished_run(tmp_path, "master-xml")
        published(artifacts, writer, outcomes)
        artifacts.OUTPUT_LIMIT = 10  # The file is larger than ten bytes.
        with pytest.raises(StreamRequestError) as refusal:
            artifacts.xml_download("run")
        assert refusal.value.code == "output_failed" and writer._record.pins == 0


class TestRestartCleanup:
    """A finished master XML survives a restart, because the manifest of a hardware run is durable."""

    @staticmethod
    def restart(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Admit a new run while no earlier owner process is alive, which makes the cleanup scan every old tree."""
        monkeypatch.setattr(BatchArtifactStorage.Retention, "process_is_alive", staticmethod(lambda _pid: False))
        finished_run(tmp_path)  # The admission of the new run scans the data root first.

    def test_a_finished_master_xml_survives_a_restart(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A new admission removes only the runs that a dead process left behind."""
        _, writer, outcomes = finished_run(tmp_path, "csv-master-xml")
        writer.finish(outcomes)
        folder = next(tmp_path.glob("*/manifest.json")).parent
        self.restart(tmp_path, monkeypatch)
        assert (folder / XML_NAME).is_file() and (folder / CSV_NAME).is_file()

    @pytest.mark.parametrize("content", [b"", b"bad json", b"[]"])
    def test_a_damaged_manifest_keeps_the_folder_and_its_master_xml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, content: bytes
    ) -> None:
        """An empty manifest, a manifest that is not JSON, and one that is not an object prove no owner."""
        _, writer, outcomes = finished_run(tmp_path, "master-xml")
        writer.finish(outcomes)
        folder = next(tmp_path.glob("*/manifest.json")).parent
        (folder / "manifest.json").write_bytes(content)  # A damaged manifest, with no owner and no durable flag.
        self.restart(tmp_path, monkeypatch)
        assert (folder / XML_NAME).is_file()  # An unknown owner is not proof of an abandoned run.
