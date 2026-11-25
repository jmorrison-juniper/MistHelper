"""Integration tests of the Multi Site hardware action through the real portal routes and services.

The Flask routes, the portal service factory, the picker, the checker, the session manager, the batch runner, the
artifact writer, and the report hook are real here. Only the Mist REST calls and the shell on each switch are fake.
"""

from __future__ import annotations

import csv  # Read the downloaded report the way a spreadsheet would.
import io  # Wrap the report text for the CSV reader.
import json  # Read the manifest.
import time  # Poll the batch until it ends.
import zipfile  # Check the archive entries.
from collections.abc import Iterator  # Type the fixture.
from io import BytesIO  # Wrap the archive bytes.
from pathlib import Path  # Test output stays under the pytest temporary folder.
from typing import Any  # The Flask client has no public type.

import pytest  # Fixtures and parametrization.

from src.mist.realtime.websocket_streams.live.sessions.manager import factory as manager_factory  # The shell seam.
from src.mist.realtime.websocket_streams.live.sessions.manager.factory import BatchRunner  # Patch the timers.
from tests.unit.ex_hardware_inventory.support.hardware_fakes import FakeMist, Payloads, ledger_session  # Fakes.
from tests.unit.ex_hardware_inventory.support.hardware_shells import FakeOrganization, FakeShells, uuid  # Fakes.
from web_portal.app import WebPortalApp  # The real portal app.
from web_portal.menu_registry import build_static_menu_actions  # Normal menu actions.

ORG_A, ORG_B, ORG_C = uuid(1), uuid(2), uuid(3)  # Invented organizations.
SITE_1, SITE_2, SITE_3 = uuid(11), uuid(12), uuid(13)  # Invented sites.
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
            Payloads.profile([Payloads.msp_grant(uuid(9))], email="user@example.invalid"),
            {uuid(9): [Payloads.response(200, listing)]},
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


def run_batch(client: Any, output_format: str = "csv", concurrency: int | None = None) -> tuple[dict, dict, str]:
    """Preview, start, and wait. Return the preview, the final batch summary, and the session identifier."""
    preview = client.post(
        "/api/websockets/batches/previews",
        json={"preset": "ex-hardware-xml", "format": output_format, "scope_revision": 0},
    )
    assert preview.status_code == 201, preview.get_data(as_text=True)
    body = preview.get_json()
    start = {"preview_id": body["preview_id"], "confirmation": body["confirmation"]["phrase"]}
    if concurrency is not None:
        start["concurrency"] = concurrency
    started = client.post("/api/websockets/batches", json=start)
    assert started.status_code == 201, started.get_data(as_text=True)
    session_id = started.get_json()["session_id"]
    return body, wait_final(client, session_id), session_id


def report_rows(client: Any, session_id: str) -> list[dict[str, str]]:
    """Download the combined CSV and parse it."""
    response = client.get(f"/api/websockets/batches/{session_id}/download?format=csv")
    assert response.status_code == 200 and response.mimetype == "text/csv"
    return list(csv.DictReader(io.StringIO(response.get_data(as_text=True), newline="")))


@pytest.fixture
def portal(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Portal:
    """Build the fakes for one test."""
    return Portal(monkeypatch, tmp_path)


class TestOrganizationScope:
    """The portal action for one organization: preview, run, publish, and download."""

    def build(self, portal: Portal) -> None:
        """Script four connected switches in two sites: one good, one with bad XML, one silent, and one more good."""
        portal.org_token()
        portal.mist.add(
            ORG_A,
            (SITE_1, "Site One"),
            [(uuid(101), "ex-01", "switch", "EX4100-48P"), (uuid(102), "ex-02", "switch", "EX4100-48P")],
        )
        portal.mist.add(
            ORG_A,
            (SITE_2, "Site Two"),
            [(uuid(201), "ex-03", "switch", "EX4100-48P"), (uuid(202), "ex-04", "switch", "EX4100-48P")],
        )
        portal.shells.behavior[uuid(102)] = "bad_xml"
        portal.shells.behavior[uuid(202)] = "silent"

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

    def test_only_the_fixed_command_reaches_a_switch_and_the_peak_stays_within_the_limit(self, portal: Portal) -> None:
        """Every shell gets the one command, and the open shells never pass the default of three."""
        self.build(portal)
        portal.shells.hold_seconds = 0.15
        for client in portal.build():
            run_batch(client, concurrency=3)
        assert {command for _, command in portal.shells.commands} == {COMMAND}
        assert 1 < portal.shells.peak <= 3 and portal.shells.open == 0

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
        FakeMist(portal.monkeypatch, Payloads.response(401, {}))
        self.build_sites_only(portal)
        for client in portal.build():
            response = client.post(
                "/api/websockets/batches/previews",
                json={"preset": "ex-hardware-xml", "format": "csv", "scope_revision": 0},
            )
            assert response.status_code == 503
            assert response.get_json()["error"] == "The Mist profile could not be read (HTTP 401). No shell was opened."
        assert portal.shells.opened == 0

    @staticmethod
    def build_sites_only(portal: Portal) -> None:
        """Add one site so that a refused profile is the only reason for the refusal."""
        portal.mist.add(ORG_A, (SITE_1, "Site One"), [(uuid(101), "ex-01", "switch", "EX4100-48P")])


class TestMspScope:
    """An MSP login runs every organization from the portal, and a failed organization is a row."""

    def build(self, portal: Portal) -> None:
        """Script A (two switches), B (one switch), and C (refused by Mist)."""
        portal.msp_login()
        portal.mist.add(
            ORG_A,
            (SITE_1, "Site One"),
            [(uuid(101), "ex-01", "switch", "EX4100-48P"), (uuid(102), "ex-02", "switch", "EX4100-48P")],
        )
        portal.mist.add(ORG_B, (SITE_2, "Site Two"), [(uuid(201), "ex-03", "switch", "EX4100-48P")])
        portal.mist.failures[f"listOrgSites:{ORG_C}"] = Payloads.response(403, {})

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
        assert {device for device, _ in portal.shells.commands} == {uuid(101), uuid(102), uuid(201)}

    def test_the_organizations_are_read_in_order_and_no_other_organization_is_read(self, portal: Portal) -> None:
        """The first three site reads are A, B, and C. The later reads are the site checks of A and B."""
        self.build(portal)
        for client in portal.build():
            run_batch(client)
        calls = [key for _, key, _ in portal.mist.calls("listOrgSites")]
        assert calls[:3] == [ORG_A, ORG_B, ORG_C] and set(calls) == {ORG_A, ORG_B, ORG_C}
