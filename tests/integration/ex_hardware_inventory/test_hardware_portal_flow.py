"""Integration tests of the Multi Site hardware action through the real portal routes and services.

The Flask routes, the portal service factory, the picker, the checker, the session manager, the batch runner, the
artifact writer, and the report hook are real here. Only the Mist REST calls and the shell on each switch are fake.
"""

from __future__ import annotations

import csv  # Read the downloaded report the way a spreadsheet would.
import io  # Wrap the report text for the CSV reader.
import json  # Read the manifest.
import time  # Poll the batch until it ends.
import xml.etree.ElementTree as ET  # A standard reader, so the tests share no code with the XML writer.
import zipfile  # Check the archive entries.
from collections.abc import Callable, Iterator  # Type the fixture and the hook between the preview and the start.
from io import BytesIO  # Wrap the archive bytes.
from pathlib import Path  # Test output stays under the pytest temporary folder.
from typing import Any  # The Flask client has no public type.

import pytest  # Fixtures and parametrization.
import requests  # Build the transport faults that the SDK can raise.

from src.mist.realtime.websocket_streams.live.sessions.manager import factory as manager_factory  # The shell seam.
from src.mist.realtime.websocket_streams.live.sessions.manager.factory import BatchRunner  # Patch the timers.
from tests.unit.ex_hardware_inventory.support.hardware_fakes import FakeMist, Payloads, ledger_session  # Fakes.
from tests.unit.ex_hardware_inventory.support.hardware_master_xml import NS, infoset_of  # Readers.
from tests.unit.ex_hardware_inventory.support.hardware_shells import FakeOrganization, FakeShells, make_uuid  # Fakes.
from web_portal.app import WebPortalApp  # The real portal app.
from web_portal.menu_registry import build_static_menu_actions  # Normal menu actions.

ORG_A, ORG_B, ORG_C = make_uuid(1), make_uuid(2), make_uuid(3)  # Invented organizations.
SITE_1, SITE_2, SITE_3 = make_uuid(11), make_uuid(12), make_uuid(13)  # Invented sites.
TOKEN = "SYNTHETIC-TOKEN-VALUE"  # A fake credential that must never appear in an answer.
COMMAND = "show chassis hardware detail | display xml | no-more"  # The one fixed command.


class Portal:
    """One real portal app over fake Mist calls and fake shells."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Patch the outside seams and build the fakes."""
        monkeypatch.chdir(tmp_path)  # The run folders go under data/websocket-streams of the temporary folder.
        monkeypatch.setenv("PORTAL_WS_ENABLE_SHELL", "true")  # The shell utility is unlocked for the portal.
        monkeypatch.setenv("MISTHELPER_STANDALONE", "true")  # No database backend.
        monkeypatch.delenv("PORTAL_WS_HARDWARE_CONCURRENCY", raising=False)
        monkeypatch.setattr(BatchRunner, "QUIET_SECONDS", 0)
        monkeypatch.setattr(BatchRunner, "COMMAND_SECONDS", 0.6)
        self.monkeypatch = monkeypatch
        self.session = ledger_session(None)  # A session double with an HTTP session.
        self.session._apitoken = [TOKEN]
        self.session._cloud_uri = "api.mist.com"
        self.shells = FakeShells()
        self.mist = FakeOrganization(monkeypatch)
        monkeypatch.setattr(manager_factory, "RunnerFactory", self.shells.factory())

    def org_token(self) -> None:
        """The credential is an organization token for organization A."""
        FakeMist(self.monkeypatch, Payloads.profile([Payloads.org_grant(ORG_A, "Alpha Org")]))

    def msp_login(self) -> None:
        """The credential is an MSP login that lists A, B, and C."""
        listing = [
            {"id": ORG_A, "name": "Alpha Org"},
            {"id": ORG_B, "name": "Beta Org"},
            {"id": ORG_C, "name": "Gamma Org"},
        ]
        FakeMist(
            self.monkeypatch,
            Payloads.profile([Payloads.msp_grant(make_uuid(9))], email="user@example.invalid"),
            {make_uuid(9): [Payloads.response(200, listing)]},
        )

    def build(self) -> Iterator[Any]:
        """Yield a client of the real portal app, and stop its services after the test."""
        app = WebPortalApp.create_app(apisession=self.session, menu_actions=build_static_menu_actions(), org_id=ORG_A)
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        try:
            yield app.test_client()
        finally:
            WebPortalApp.shutdown_app(app)


def wait_final(client: Any, session_id: str, seconds: float = 30.0) -> dict[str, Any]:
    """Poll the batch summary until its output is final, and return the batch part."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        batch = client.get(f"/api/websockets/batches/{session_id}").get_json()["batch"]
        if batch["artifact_status"] in {"ready", "failed"} and batch["status"] not in {"running", "stopping"}:
            return batch  # type: ignore[no-any-return]
        time.sleep(0.05)
    raise AssertionError("The batch did not end in time.")


def request_preview(client: Any, output_format: str = "csv", sites: dict[str, Any] | None = None) -> Any:
    """Post the preview request of the hardware preset and return the raw answer."""
    body: dict[str, Any] = {"preset": "ex-hardware-xml", "format": output_format, "scope_revision": 0}
    if sites is not None:  # A subset of the sites. All sites is the default and sends no field.
        body["sites"] = sites
    return client.post("/api/websockets/batches/previews", json=body)


def run_batch(
    client: Any,
    output_format: str = "csv",
    concurrency: int | None = None,
    before_start: Callable[[], None] | None = None,
    sites: dict[str, Any] | None = None,
) -> tuple[dict, dict, str]:
    """Preview, start, and wait. Return the preview, the final batch summary, and the session identifier."""
    preview = request_preview(client, output_format, sites)
    assert preview.status_code == 201, preview.get_data(as_text=True)
    body = preview.get_json()
    start = {"preview_id": body["preview_id"], "confirmation": body["confirmation"]["phrase"]}
    if concurrency is not None:
        start["concurrency"] = concurrency
    if before_start is not None:  # The operator reads the preview, and then Mist can change.
        before_start()
    started = client.post("/api/websockets/batches", json=start)
    assert started.status_code == 201, started.get_data(as_text=True)
    session_id = started.get_json()["session_id"]
    return body, wait_final(client, session_id), session_id


def report_rows(client: Any, session_id: str) -> list[dict[str, str]]:
    """Download the combined CSV and parse it."""
    response = client.get(f"/api/websockets/batches/{session_id}/download?format=csv")
    assert response.status_code == 200 and response.mimetype == "text/csv"
    return list(csv.DictReader(io.StringIO(response.get_data(as_text=True), newline="")))


def master_root(client: Any, session_id: str) -> ET.Element:
    """Download the combined XML file and parse it with a standard reader that the tool does not use."""
    response = client.get(f"/api/websockets/batches/{session_id}/download?format=xml")
    assert response.status_code == 200 and response.mimetype == "application/xml"
    assert response.headers["Content-Disposition"].startswith("attachment; filename=ExHardwareInventory_")
    return ET.fromstring(response.get_data())


def two_sites(portal: Portal) -> None:
    """Script four connected switches in two sites: one good, one with bad XML, one silent, and one more good."""
    portal.org_token()
    portal.mist.add(
        ORG_A,
        (SITE_1, "Site One"),
        [(make_uuid(101), "ex-01", "switch", "EX4100-48P"), (make_uuid(102), "ex-02", "switch", "EX4100-48P")],
    )
    portal.mist.add(
        ORG_A,
        (SITE_2, "Site Two"),
        [(make_uuid(201), "ex-03", "switch", "EX4100-48P"), (make_uuid(202), "ex-04", "switch", "EX4100-48P")],
    )
    portal.shells.behavior[make_uuid(102)] = "bad_xml"
    portal.shells.behavior[make_uuid(202)] = "silent"


@pytest.fixture
def portal(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Portal:
    """Build the fakes for one test."""
    return Portal(monkeypatch, tmp_path)


class TestOrganizationScope:
    """The portal action for one organization: preview, run, publish, and download."""

    build = staticmethod(two_sites)  # Four switches in two sites. The master XML tests use the same scenario.

    def test_the_csv_output_runs_end_to_end_and_the_download_works(self, portal: Portal) -> None:
        """The preview shows the scope, the run publishes the CSV, and the download returns it."""
        self.build(portal)
        for client in portal.build():
            preview, batch, session_id = run_batch(client)
            assert preview["scope"] == {"mode": "organization", "organization_count": 1, "failed_count": 0}
            assert preview["format"] == "csv" and preview["fixed_commands"] == [COMMAND]
            assert preview["target_count"] == 4 and preview["confirmation"]["phrase"] == "RUN 4 TARGETS"
            assert batch["artifact_status"] == "ready" and batch["format"] == "csv"
            manifest = client.get(f"/api/websockets/batches/{session_id}/artifacts").get_json()
            assert "hardware/inventory.csv" in manifest["files"] and manifest["partial"] is True
            assert len([name for name in manifest["files"] if name.endswith(".xml")]) == 2
            rows = report_rows(client, session_id)
            assert {row["org_name"] for row in rows} == {"Alpha Org"} and {row["scope"] for row in rows} == {
                "organization"
            }
            outcomes = {
                row["device_name"]: row["collection_detail"] for row in rows if row["record_type"] == "device_outcome"
            }
            assert outcomes == {
                "ex-02": "The reply was not a valid chassis inventory.",
                "ex-04": "The shell did not show a stable prompt.",
            }
            assert {row["device_name"] for row in rows if row["record_type"] == "hardware_item"} == {"ex-01", "ex-03"}
            archive = client.get(f"/api/websockets/batches/{session_id}/download?format=zip")
            with zipfile.ZipFile(BytesIO(archive.get_data())) as zipped:
                assert "hardware/inventory.csv" in zipped.namelist() and "manifest.json" in zipped.namelist()
            assert TOKEN not in json.dumps(manifest) + json.dumps(preview)

    def test_the_table_preview_shows_the_same_rows_as_the_download(self, portal: Portal) -> None:
        """The preview route and the download read one file, so the table and the CSV never differ (issue #4931)."""
        self.build(portal)
        for client in portal.build():
            _, _, session_id = run_batch(client)
            rows = report_rows(client, session_id)
            url = f"/api/websockets/batches/{session_id}/csv-preview"
            response = client.get(url)
            page = response.get_json()
            assert response.status_code == 200 and response.mimetype == "application/json"
            assert page["total"] == page["matched"] == len(rows) and page["limit"] == 1000 and page["cut_cells"] == 0
            assert [dict(zip(page["columns"], row, strict=True)) for row in page["rows"]] == rows
            wanted = [row for row in rows if any("ex-04" in cell.casefold() for cell in row.values())]
            filtered = client.get(f"{url}?q=EX-04").get_json()
            assert filtered["matched"] == len(wanted) > 0 and filtered["total"] == len(rows)
            assert [dict(zip(filtered["columns"], row, strict=True)) for row in filtered["rows"]] == wanted
            second = client.get(f"{url}?offset=1&limit=1").get_json()
            assert [dict(zip(second["columns"], row, strict=True)) for row in second["rows"]] == rows[1:2]
            assert TOKEN not in response.get_data(as_text=True)

    def test_the_table_preview_refuses_an_unknown_run_and_a_bad_query_before_any_read(self, portal: Portal) -> None:
        """An identifier that no batch owns gives a refusal, and a bad position gives HTTP 400."""
        self.build(portal)
        for client in portal.build():
            unknown = client.get("/api/websockets/batches/no-such-run/csv-preview")
            assert unknown.status_code in {404, 409} and unknown.get_json()["code"] in {"not_found", "not_batch"}
            _, _, session_id = run_batch(client)
            bad = client.get(f"/api/websockets/batches/{session_id}/csv-preview?offset=-1")
            assert bad.status_code == 400 and bad.get_json()["code"] == "bad_request"

    def test_only_the_fixed_command_reaches_a_switch_and_the_peak_stays_within_the_limit(self, portal: Portal) -> None:
        """Every shell gets the one command, and the open shells never pass the default of three."""
        self.build(portal)
        portal.shells.hold_seconds = 0.15
        for client in portal.build():
            run_batch(client, concurrency=3)
        assert {command for _, command in portal.shells.commands} == {COMMAND}
        assert 1 < portal.shells.peak <= 3 and portal.shells.open == 0

    def test_a_site_subset_runs_only_the_chosen_site_and_the_report_holds_only_its_switches(
        self, portal: Portal
    ) -> None:
        """One chosen site gives two targets and two shells, and the report names no other site."""
        self.build(portal)
        for client in portal.build():
            preview, batch, session_id = run_batch(client, sites={"mode": "selected", "ids": [SITE_2]})
            assert preview["target_count"] == 2 and preview["confirmation"]["phrase"] == "RUN 2 TARGETS"
            assert preview["site_selection"] == {"mode": "selected", "count": 1}  # A count and no name.
            assert {target["site_label"] for target in preview["targets"]} == {"Site Two"}
            assert batch["artifact_status"] == "ready"
            rows = report_rows(client, session_id)
            assert {row["site_name"] for row in rows} == {"Site Two"}
            assert {row["device_name"] for row in rows} == {"ex-03", "ex-04"}
        assert portal.shells.opened == 2  # The two switches of the other site never got a shell.

    def test_the_explicit_all_mode_and_no_selection_give_the_same_preview(self, portal: Portal) -> None:
        """Both ways to say every site list the four switches, and the preview names no subset."""
        self.build(portal)
        for client in portal.build():
            plain = request_preview(client).get_json()
            explicit = request_preview(client, sites={"mode": "all"}).get_json()
        assert plain["target_count"] == explicit["target_count"] == 4
        assert plain["site_selection"] == explicit["site_selection"] == {"mode": "all"}

    @pytest.mark.parametrize(
        "sites",
        [
            {"mode": "selected", "ids": [make_uuid(99)]},
            {"mode": "selected", "ids": [SITE_1, SITE_1]},
            {"mode": "selected", "ids": []},
            {"mode": "all", "ids": [SITE_1]},
            {"mode": "selected", "ids": ["not-a-uuid"]},
            "all",
        ],
    )
    def test_a_bad_site_choice_is_refused_before_any_shell(self, portal: Portal, sites: Any) -> None:
        """An unknown site, a repeated site, an empty subset, and a wrong shape give HTTP 400 and no shell."""
        self.build(portal)
        for client in portal.build():
            response = request_preview(client, sites=sites)
            assert response.status_code == 400 and response.get_json()["code"] == "bad_request"
        assert portal.shells.opened == 0

    @pytest.mark.parametrize("output_format", ["xml", "both"])
    def test_the_existing_outputs_publish_no_csv(self, portal: Portal, output_format: str) -> None:
        """Xml and both keep their behavior: the replies and the manifest, and no report."""
        self.build(portal)
        for client in portal.build():
            _, _, session_id = run_batch(client, output_format)
            manifest = client.get(f"/api/websockets/batches/{session_id}/artifacts").get_json()
            assert "hardware/inventory.csv" not in manifest["files"]
            refusal = client.get(f"/api/websockets/batches/{session_id}/download?format=csv")
            assert refusal.status_code == 409 and refusal.get_json()["code"] == "artifact_not_ready"
            table = client.get(f"/api/websockets/batches/{session_id}/csv-preview")  # No report, so no table.
            assert table.status_code == 409 and table.get_json()["code"] == "artifact_not_ready"

    def test_the_hardware_concurrency_setting_reaches_the_page_and_the_limit(
        self, portal: Portal, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The catalog publishes the value in use, and a run with that value never opens more shells."""
        self.build(portal)
        monkeypatch.setenv("PORTAL_WS_HARDWARE_CONCURRENCY", "2")
        portal.shells.hold_seconds = 0.15
        for client in portal.build():
            assert client.get("/api/websockets/catalog").get_json()["limits"]["hardware_concurrency"] == 2
            run_batch(client, concurrency=2)
        assert 1 < portal.shells.peak <= 2

    def test_a_refused_profile_stops_the_preview_with_a_plain_reason(self, portal: Portal) -> None:
        """HTTP 401 on the profile means no preview, no shell, and the sentence of the menu."""
        FakeMist(portal.monkeypatch, Payloads.response(status=401, data={}))
        self.build_sites_only(portal)
        for client in portal.build():
            response = request_preview(client)
            assert response.status_code == 503
            assert response.get_json()["error"] == "The Mist profile could not be read (HTTP 401). No shell was opened."
        assert portal.shells.opened == 0

    @staticmethod
    def build_sites_only(portal: Portal) -> None:
        """Add one site so that a refused profile is the only reason for the refusal."""
        portal.mist.add(ORG_A, (SITE_1, "Site One"), [(make_uuid(101), "ex-01", "switch", "EX4100-48P")])


class TestMasterXmlOutput:
    """The combined XML file of the portal, alone or with the CSV report (issue #4933)."""

    @staticmethod
    def zipped_replies(client: Any, session_id: str) -> dict[str, bytes]:
        """Return the saved reply of each collected switch from the archive, by the device label in the name."""
        archive = client.get(f"/api/websockets/batches/{session_id}/download?format=zip")
        with zipfile.ZipFile(BytesIO(archive.get_data())) as zipped:
            return {
                name.rsplit("/", 1)[-1].split("--", 1)[0]: zipped.read(name)
                for name in zipped.namelist()
                if name.endswith(".xml") and not name.endswith("inventory.xml")
            }

    def test_the_master_xml_output_publishes_one_valid_file_and_no_csv(self, portal: Portal) -> None:
        """One run gives a file that a standard reader accepts, with every switch and each reply of its saved file."""
        two_sites(portal)
        for client in portal.build():
            preview, batch, session_id = run_batch(client, "master-xml")
            assert preview["format"] == "master-xml" and preview["fixed_commands"] == [COMMAND]
            assert batch["artifact_status"] == "ready" and batch["format"] == "master-xml"
            manifest = client.get(f"/api/websockets/batches/{session_id}/artifacts").get_json()
            assert "hardware/inventory.xml" in manifest["files"] and "hardware/inventory.csv" not in manifest["files"]
            root = master_root(client, session_id)
            devices = {device.get("name"): device for device in root.iterfind(".//mh:device", NS)}
            assert {name: device.get("status") for name, device in devices.items()} == {
                "ex-01": "collected",
                "ex-02": "failed",
                "ex-03": "collected",
                "ex-04": "failed",
            }
            assert devices["ex-02"].get("detail") == "The reply was not a valid chassis inventory."
            assert devices["ex-04"].get("detail") == "The shell did not show a stable prompt."
            assert (root.get("scope"), root.get("devices"), root.get("collected"), root.get("failed")) == (
                "organization",
                "4",
                "2",
                "2",
            )
            saved = self.zipped_replies(client, session_id)
            for label in ("ex-01", "ex-03"):  # The embedded reply is the saved reply, apart from formatting.
                (embedded,) = list(devices[label])
                assert infoset_of(embedded) == infoset_of(ET.fromstring(saved[label])), label
            refusal = client.get(f"/api/websockets/batches/{session_id}/download?format=csv")
            assert refusal.status_code == 409 and refusal.get_json()["code"] == "artifact_not_ready"
            assert TOKEN not in json.dumps(manifest) + ET.tostring(root, encoding="unicode")

    def test_the_csv_and_master_xml_output_publishes_both_files_that_agree(self, portal: Portal) -> None:
        """Both reports appear together. They name the same switches with the same statuses."""
        two_sites(portal)
        for client in portal.build():
            _, batch, session_id = run_batch(client, "csv-master-xml")
            assert batch["artifact_status"] == "ready" and batch["format"] == "csv-master-xml"
            manifest = client.get(f"/api/websockets/batches/{session_id}/artifacts").get_json()
            assert {"hardware/inventory.csv", "hardware/inventory.xml"} <= set(manifest["files"])
            from_csv = {(row["device_name"], row["collection_status"]) for row in report_rows(client, session_id)}
            from_xml = {
                (device.get("name"), device.get("status"))
                for device in master_root(client, session_id).iterfind(".//mh:device", NS)
            }
            assert from_csv == from_xml and len(from_xml) == 4
            table = client.get(f"/api/websockets/batches/{session_id}/csv-preview")
            assert table.status_code == 200  # The table needs the CSV report, and it is there.
            with zipfile.ZipFile(
                BytesIO(client.get(f"/api/websockets/batches/{session_id}/download?format=zip").data)
            ) as z:
                assert {"hardware/inventory.csv", "hardware/inventory.xml"} <= set(z.namelist())

    @pytest.mark.parametrize("output_format", ["xml", "json", "both", "csv"])
    def test_the_other_outputs_publish_no_master_xml(self, portal: Portal, output_format: str) -> None:
        """Only the two master XML formats write the file, and the download says that it is not ready."""
        two_sites(portal)
        for client in portal.build():
            _, _, session_id = run_batch(client, output_format)
            manifest = client.get(f"/api/websockets/batches/{session_id}/artifacts").get_json()
            assert "hardware/inventory.xml" not in manifest["files"]
            refusal = client.get(f"/api/websockets/batches/{session_id}/download?format=xml")
            assert refusal.status_code == 409 and refusal.get_json()["code"] == "artifact_not_ready"

    def test_an_msp_run_lists_each_organization_and_the_unread_one_has_no_site(self, portal: Portal) -> None:
        """The scope of the run decides the organization elements, and Mist can fail one of them."""
        portal.msp_login()
        portal.mist.add(ORG_A, (SITE_1, "Site One"), [(make_uuid(101), "ex-01", "switch", "EX4100-48P")])
        portal.mist.add(ORG_B, (SITE_2, "Site Two"), [(make_uuid(201), "ex-02", "switch", "EX4100-48P")])
        portal.mist.failures[f"listOrgSites:{ORG_C}"] = Payloads.response(status=403, data={})
        for client in portal.build():
            _, batch, session_id = run_batch(client, "master-xml")
            root = master_root(client, session_id)
        assert batch["artifact_status"] == "ready"
        assert (root.get("scope"), root.get("organizations"), root.get("unread"), root.get("collected")) == (
            "msp",
            "3",
            "1",
            "2",
        )
        unread = [org for org in root.iterfind("mh:organization", NS) if org.get("status") == "failed"]
        assert [org.get("name") for org in unread] == ["Gamma Org"] and len(unread[0]) == 0
        assert unread[0].get("detail") == "Mist could not list the switches of this organization."

    """Mist refuses a read, answers with a server error, or cannot be reached: the portal refuses plainly."""

    UPSTREAM = "UPSTREAM-ERROR-TEXT"  # Text that only the failed call holds. It must never reach an answer.

    def build(self, portal: Portal) -> None:
        """Script one organization token with one connected switch."""
        portal.org_token()
        portal.mist.add(ORG_A, (SITE_1, "Site One"), [(make_uuid(101), "ex-01", "switch", "EX4100-48P")])

    def refused(self, portal: Portal) -> tuple[int, dict[str, Any], str]:
        """Post the preview, and return the status, the JSON body, and the raw text of the answer."""
        for client in portal.build():
            response = request_preview(client)
            return response.status_code, response.get_json(), response.get_data(as_text=True)
        raise AssertionError("The portal client was not built.")

    @pytest.mark.parametrize("call", ["listOrgSites", "listSiteDevices"])
    @pytest.mark.parametrize(
        ("status", "code", "expected"),
        [
            (401, "picker_request_failed", 502),
            (403, "picker_request_failed", 502),
            (404, "picker_request_failed", 502),
            (429, "picker_request_failed", 502),
            (500, "picker_service_failed", 503),
            (502, "picker_service_failed", 503),
            (503, "picker_service_failed", 503),
        ],
    )
    def test_an_http_error_on_a_discovery_read_refuses_the_preview(
        self, portal: Portal, call: str, status: int, code: str, expected: int
    ) -> None:
        """A 4xx answer of Mist is a refused request, a 5xx answer is an unavailable service, and no shell opens."""
        self.build(portal)
        portal.mist.failures[call] = Payloads.response(status=status, data={"detail": self.UPSTREAM})
        answer, body, text = self.refused(portal)
        assert answer == expected and body["code"] == code and body["upstream_status"] == status
        assert self.UPSTREAM not in text and TOKEN not in text  # The error body of Mist never reaches the browser.
        assert portal.shells.opened == 0

    @pytest.mark.parametrize("status", [403, 503])
    def test_an_http_error_on_the_status_read_refuses_the_preview(self, portal: Portal, status: int) -> None:
        """The status read has its own plain sentence for every HTTP error."""
        self.build(portal)
        portal.mist.failures["listSiteDevicesStats"] = Payloads.response(status=status, data={"detail": self.UPSTREAM})
        answer, body, text = self.refused(portal)
        assert answer == 503 and body["error"] == "The portal could not read current device status."
        assert self.UPSTREAM not in text and portal.shells.opened == 0

    @pytest.mark.parametrize(
        "fault",
        [requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout],
    )
    def test_a_transport_fault_on_a_site_read_refuses_the_preview(self, portal: Portal, fault: type[Exception]) -> None:
        """A refused connection and a timeout give a 503 with a plain sentence, and the error text stays out."""
        self.build(portal)
        portal.mist.failures["listOrgSites"] = fault(self.UPSTREAM)  # The SDK call raises instead of answering.
        answer, body, text = self.refused(portal)
        assert answer == 503 and body == {
            "code": "picker_service_failed",
            "error": "The portal could not list sites from Mist.",
        }
        assert self.UPSTREAM not in text and portal.shells.opened == 0

    @pytest.mark.parametrize("fault", [requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout])
    def test_a_transport_fault_on_the_profile_read_refuses_the_preview(
        self, portal: Portal, fault: type[Exception]
    ) -> None:
        """The scope cannot be decided when Mist cannot be reached, so no shell opens."""
        FakeMist(portal.monkeypatch, fault(self.UPSTREAM))  # The profile read raises.
        portal.mist.add(ORG_A, (SITE_1, "Site One"), [(make_uuid(101), "ex-01", "switch", "EX4100-48P")])
        answer, body, text = self.refused(portal)
        assert answer == 503 and body["code"] == "picker_unavailable"
        assert body["error"] == "The Mist profile could not be read (no usable answer from Mist). No shell was opened."
        assert self.UPSTREAM not in text and portal.shells.opened == 0

    def test_a_server_error_at_dispatch_skips_every_switch_and_opens_no_shell(self, portal: Portal) -> None:
        """Mist fails after the operator confirmed: the batch ends, and each switch is an outcome row."""
        self.build(portal)
        portal.mist.add(ORG_A, (SITE_2, "Site Two"), [(make_uuid(201), "ex-02", "switch", "EX4100-48P")])
        broken = {"listSiteDevicesStats": Payloads.response(status=503, data={"detail": self.UPSTREAM})}
        for client in portal.build():
            _, batch, session_id = run_batch(client, before_start=lambda: portal.mist.failures.update(broken))
            rows = report_rows(client, session_id)
        assert batch["artifact_status"] == "ready" and portal.shells.opened == 0
        assert {row["record_type"] for row in rows} == {"device_outcome"}  # No hardware item without a shell.
        assert {row["collection_status"] for row in rows} == {"skipped"}
        assert self.UPSTREAM not in json.dumps(rows)


class TestMspScope:
    """An MSP login runs every organization from the portal, and a failed organization is a row."""

    def build(self, portal: Portal, status: int = 403) -> None:
        """Script A (two switches), B (one switch), and C (failed by Mist with the status)."""
        portal.msp_login()
        portal.mist.add(
            ORG_A,
            (SITE_1, "Site One"),
            [(make_uuid(101), "ex-01", "switch", "EX4100-48P"), (make_uuid(102), "ex-02", "switch", "EX4100-48P")],
        )
        portal.mist.add(ORG_B, (SITE_2, "Site Two"), [(make_uuid(201), "ex-03", "switch", "EX4100-48P")])
        portal.mist.failures[f"listOrgSites:{ORG_C}"] = Payloads.response(status=status, data={})

    def test_one_batch_covers_every_organization_and_reports_the_failed_one(self, portal: Portal) -> None:
        """The preview counts three organizations and one unread. The report has all of them."""
        self.build(portal)
        for client in portal.build():
            preview, batch, session_id = run_batch(client)
            assert preview["scope"] == {"mode": "msp", "organization_count": 3, "failed_count": 1}
            assert preview["target_count"] == 3 and batch["artifact_status"] == "ready"
            rows = report_rows(client, session_id)
            assert {row["scope"] for row in rows} == {"msp"}
            assert {row["org_name"] for row in rows} == {"Alpha Org", "Beta Org", "Gamma Org"}
            assert {row["device_name"] for row in rows if row["record_type"] == "hardware_item"} == {
                "ex-01",
                "ex-02",
                "ex-03",
            }
            failed = [row for row in rows if row["org_name"] == "Gamma Org"]
            assert len(failed) == 1 and failed[0]["collection_status"] == "failed" and failed[0]["device_id"] == ""
            assert failed[0]["collection_detail"] == "Mist could not list the switches of this organization."
        assert {device for device, _ in portal.shells.commands} == {make_uuid(101), make_uuid(102), make_uuid(201)}

    @pytest.mark.parametrize("status", [401, 404, 429, 500, 502, 503])
    def test_any_http_failure_of_one_organization_leaves_the_others_running(self, portal: Portal, status: int) -> None:
        """Gamma Org fails with each HTTP status, and Alpha Org and Beta Org still give their hardware rows."""
        self.build(portal, status)
        for client in portal.build():
            preview, batch, session_id = run_batch(client)
            rows = report_rows(client, session_id)
        assert preview["scope"] == {"mode": "msp", "organization_count": 3, "failed_count": 1}
        assert batch["artifact_status"] == "ready"
        failed = [row for row in rows if row["org_name"] == "Gamma Org"]
        assert [row["collection_status"] for row in failed] == ["failed"]  # One outcome row for the unread one.
        assert {row["org_name"] for row in rows if row["record_type"] == "hardware_item"} == {"Alpha Org", "Beta Org"}

    def test_the_organizations_are_read_in_order_and_no_other_organization_is_read(self, portal: Portal) -> None:
        """The first three site reads are A, B, and C. The later reads are the site checks of A and B."""
        self.build(portal)
        for client in portal.build():
            run_batch(client)
        calls = [key for _, key, _ in portal.mist.calls("listOrgSites")]
        assert calls[:3] == [ORG_A, ORG_B, ORG_C] and set(calls) == {ORG_A, ORG_B, ORG_C}
