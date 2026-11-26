"""Integration tests of menu 309 against the real portal batch services.

Everything between the menu and the CSV file is real here: the scope resolver, the picker, the request
checker, the session manager, the batch runner, the artifact writer, the report builder, and the standard
exporter. Only the Mist REST calls and the shell on each switch are fake, so no test needs a network or a
credential.
"""

from __future__ import annotations

import json  # Read the manifest of the run folder.
import logging  # Prove that no log line holds the credential.
import xml.etree.ElementTree as ET  # A standard reader, so the tests share no code with the XML writer.

import pytest  # Capture the console.
import requests  # Build the transport faults that the SDK can raise.

from src.operations.exporting.ex_hardware_inventory.operation import ExHardwareInventoryReport  # Unit.
from tests.unit.ex_hardware_inventory.support.hardware_fakes import FakeMist, Payloads  # Fakes.
from tests.unit.ex_hardware_inventory.support.hardware_master_xml import NS, Written, infoset_of  # Readers.
from tests.unit.ex_hardware_inventory.support.hardware_shells import make_uuid  # Invented identifiers.
from tests.unit.ex_hardware_inventory.support.hardware_world import (
    COMMAND,
    ORG_A,
    ORG_B,
    SITE_1,
    SITE_2,
    TOKEN,
    World,
    run_menu,
)  # The shared world of the integration tests.


class TestOneOrganizationEndToEnd:
    """The whole path for one organization token, with every kind of switch outcome."""

    def build(self, world: World) -> None:
        """Script five targets: two good, one with bad XML, one silent, and one that goes offline later."""
        world.org_token()
        world.mixed_site_one()
        world.mist.add(
            ORG_A,
            (SITE_2, "Site Two"),
            [
                (make_uuid(201), "ex-04", "switch", "EX4100-48P"),
                (make_uuid(202), "ex-05", "switch", "EX4100-48P"),
                (make_uuid(203), "ex-06", "switch", "EX4100-48P"),
                (make_uuid(204), "srx-01", "gateway", "SRX345"),
            ],
        )
        world.mist.statuses[make_uuid(203)] = [
            "connected",
            "disconnected",
        ]  # Connected at the preview, offline at dispatch.
        world.shells.behavior[make_uuid(102)] = "bad_xml"
        world.shells.behavior[make_uuid(202)] = "silent"

    def test_the_report_holds_each_outcome_and_the_console_is_plain(
        self, world: World, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
    ) -> None:
        """One CSV file, a row for each hardware item, an outcome row for each missing reply, and a partial run."""
        caplog.set_level(logging.DEBUG)  # Capture every log line to prove that the credential never appears.
        self.build(world)
        world.answer = "RUN 5 TARGETS"
        result, lines = run_menu(capsys)
        rows = world.rows()
        assert result == len(rows) and result > 0  # The return value counts the rows.
        assert "  Credential: API token (organization token)" in lines and "  Scope: organization" in lines
        assert "  Alpha Org: 5 connected EX switches" in lines
        assert "  Left out: offline 1, unknown status 0, other device types 2, repeated chassis 0" in lines
        assert "  Alpha Org: collected 2, failed 2, skipped 1, cancelled 0" in lines  # Step 4.
        assert lines[-1] == "Run status: partial"
        outcomes = {row["device_name"]: row for row in rows if row["record_type"] == "device_outcome"}
        assert set(outcomes) == {"ex-02", "ex-05", "ex-06"}  # One outcome row for each missing reply.
        assert outcomes["ex-02"]["collection_detail"] == "The reply was not a valid chassis inventory."
        assert outcomes["ex-05"]["collection_detail"] == "The shell did not show a stable prompt."
        assert outcomes["ex-06"]["collection_status"] == "skipped"
        assert outcomes["ex-06"]["collection_detail"] == "The switch was offline when its turn came."
        items = [row for row in rows if row["record_type"] == "hardware_item"]
        assert {row["device_name"] for row in items} == {"ex-01", "ex-04"}  # Only the good replies.
        assert {row["collection_status"] for row in items} == {"collected"}
        assert TOKEN not in capsys.readouterr().out + caplog.text + json.dumps(rows)  # The credential never leaks.

    def test_a_serial_number_in_the_report_equals_the_one_in_the_saved_reply(self, world: World) -> None:
        """The report serial numbers equal the serial numbers of the saved XML files."""
        self.build(world)
        world.answer = "RUN 5 TARGETS"
        ExHardwareInventoryReport.run()
        replies = Written.replies(world.tmp_path / "data")
        saved = "".join(path.read_text(encoding="utf-8") for path in replies.values())
        reported = {row["item_serial_number"] for row in world.rows() if row["item_serial_number"]}
        assert reported and all(serial in saved for serial in reported)  # Every reported serial is in a saved file.
        assert len(replies) == 2  # One saved reply for each collected switch.

    def test_the_master_xml_holds_every_outcome_and_each_reply_equals_its_saved_file(self, world: World) -> None:
        """Five targets: two replies, two failures, and one skip. A standard reader finds the same data as the files."""
        self.build(world)
        world.answer = "RUN 5 TARGETS"
        ExHardwareInventoryReport.run()
        data_dir = world.tmp_path / "data"
        root = Written.master(data_dir)
        devices = {device.get("name"): device for device in root.iterfind(".//mh:device", NS)}
        assert {name: device.get("status") for name, device in devices.items()} == {
            "ex-01": "collected",
            "ex-02": "failed",
            "ex-04": "collected",
            "ex-05": "failed",
            "ex-06": "skipped",
        }
        assert devices["ex-02"].get("detail") == "The reply was not a valid chassis inventory."
        assert devices["ex-06"].get("detail") == "The switch was offline when its turn came."
        assert (root.get("devices"), root.get("collected"), root.get("failed"), root.get("skipped")) == (
            "5",
            "2",
            "2",
            "1",
        )
        replies = Written.replies(data_dir)
        for label in ("ex-01", "ex-04"):  # Each collected switch has exactly one embedded reply.
            (embedded,) = list(devices[label])
            assert infoset_of(embedded) == infoset_of(ET.parse(replies[label]).getroot()), label

    def test_the_credential_never_reaches_the_master_xml(self, world: World) -> None:
        """The master XML is a file that a customer reads, so it must not hold the credential."""
        self.build(world)
        world.answer = "RUN 5 TARGETS"
        ExHardwareInventoryReport.run()
        (master,) = (world.tmp_path / "data").glob("ExHardwareInventory_*.xml")
        assert master.stat().st_size > 0 and TOKEN not in master.read_text(encoding="utf-8")

    def test_only_the_fixed_command_reaches_a_switch_and_no_shell_opens_for_a_skipped_switch(
        self, world: World
    ) -> None:
        """Four shells open, each receives exactly the fixed command, and the offline switch gets none."""
        self.build(world)
        world.answer = "RUN 5 TARGETS"
        ExHardwareInventoryReport.run()
        assert world.shells.opened == 4  # ex-06 was skipped before its shell opened.
        assert {command for _, command in world.shells.commands} == {COMMAND}  # The one fixed command.
        assert sorted(device for device, _ in world.shells.commands) == sorted(
            [make_uuid(101), make_uuid(102), make_uuid(201), make_uuid(202)]
        )  # One command for each shell.
        assert world.shells.open == 0  # Every shell closed.

    def test_the_ledger_holds_the_organization_during_every_site_read_and_is_restored(self, world: World) -> None:
        """Each site-level Mist read ran with the organization in the shared ledger, and the ledger is clean after."""
        self.build(world)
        world.answer = "RUN 5 TARGETS"
        ExHardwareInventoryReport.run()
        site_reads = world.mist.calls("listSiteDevices") + world.mist.calls("listSiteDevicesStats")
        assert site_reads and {entry[2] for entry in site_reads} == {ORG_A}  # Bound for every site read.
        assert world.ledger.org_id is None  # Restored after the run.

    def test_the_run_folder_holds_the_replies_and_a_partial_manifest(self, world: World) -> None:
        """The private run folder keeps the saved XML and a manifest that marks the run partial."""
        self.build(world)
        world.answer = "RUN 5 TARGETS"
        ExHardwareInventoryReport.run()
        manifests = list((world.tmp_path / "data" / "websocket-streams").glob("*/manifest.json"))
        assert len(manifests) == 1
        manifest = json.loads(manifests[0].read_text(encoding="utf-8"))
        assert manifest["partial"] is True and manifest["durable"] is True and manifest["status"] == "ready"
        assert len(manifest["files"]) == 2 and all(name.endswith(".xml") for name in manifest["files"])

    def test_the_default_concurrency_never_opens_more_than_three_shells(self, world: World) -> None:
        """Shells overlap, and the peak stays at the setting."""
        self.build(world)
        world.shells.hold_seconds = 0.15
        world.answer = "RUN 5 TARGETS"
        ExHardwareInventoryReport.run()
        assert 1 < world.shells.peak <= 3  # They overlapped, and the limit held.


class TestSafeOutcomes:
    """Cancelled and empty runs open nothing."""

    def test_a_wrong_phrase_opens_no_shell_and_writes_no_file(
        self, world: World, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The preview ran, but no shell opened and no file or run folder exists."""
        world.org_token()
        world.mixed_site_one()
        world.answer = "yes"
        result, lines = run_menu(capsys)
        assert result == 0 and lines[-1] == "Cancelled. No shell was opened and no file was written."
        assert world.shells.opened == 0 and world.shells.commands == []
        assert not list((world.tmp_path / "data").glob("*.csv"))  # No report.

    def test_an_organization_with_no_connected_switch_asks_nothing(
        self, world: World, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Only offline switches: no question, no shell, no file."""
        world.org_token()
        world.mist.add(ORG_A, (SITE_1, "Site One"), [(make_uuid(101), "ex-01", "switch", "EX4100-48P")])
        world.mist.statuses[make_uuid(101)] = ["disconnected"]
        result, lines = run_menu(capsys)
        assert result == 0 and world.prompts == []
        assert lines[-1] == "No connected EX switch was found. No file was written."


class TestRefusedShells:
    """Mist refuses the shell session of every switch, as it did for the read-only token of the live test."""

    NOTE = (
        "  Note: This credential has the read-only role. Mist can refuse a switch shell for that role,"
        " and then each switch fails."
    )  # The contract text of the console.
    DETAIL = "The shell could not collect this switch. See the log for the cause."  # The plain cause for the report.

    def refuse_both(self, world: World, role: str) -> None:
        """Script two connected switches whose shell sessions Mist refuses, for a credential with the role."""
        world.org_token(role=role)
        world.mixed_site_one()
        world.shells.behavior.update({make_uuid(101): "refused", make_uuid(102): "refused"})
        world.answer = "RUN 2 TARGETS"

    def test_a_read_only_token_gets_the_note_first_and_every_switch_is_an_outcome_row(
        self, world: World, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
    ) -> None:
        """The note comes before the phrase, no shell opens, and the report names each failed switch."""
        caplog.set_level(logging.DEBUG)  # Capture every log line to prove that the credential never appears.
        self.refuse_both(world, "read")
        result, lines = run_menu(capsys)
        rows = world.rows()
        assert self.NOTE in lines and lines.index(self.NOTE) < lines.index(
            "Step 2 of 4: Find the connected EX switches"
        )
        assert (
            "  Alpha Org: collected 0, failed 2, skipped 0, cancelled 0" in lines and lines[-1] == "Run status: partial"
        )
        assert result == len(rows) == 2 and {row["collection_status"] for row in rows} == {"failed"}
        assert {row["collection_detail"] for row in rows} == {self.DETAIL}  # One plain sentence for each switch.
        assert world.shells.opened == 0 and TOKEN not in "\n".join(lines) + caplog.text

    def test_the_same_refusal_for_another_role_gives_no_note(
        self, world: World, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The note belongs to the read-only role only. The refusal itself reads the same for every role."""
        self.refuse_both(world, "write")
        result, lines = run_menu(capsys)
        assert not [line for line in lines if line.startswith("  Note:")]  # No note.
        assert result == 2 and "  Alpha Org: collected 0, failed 2, skipped 0, cancelled 0" in lines


class TestMspEndToEnd:
    """An MSP login runs every organization, and a failed organization does not stop the others."""

    def build(self, world: World, status: int = 403) -> None:
        """Script an MSP with a good organization, a second good one, and a third that Mist fails with the status."""
        org_c = make_uuid(3)
        FakeMist(
            world.monkeypatch,
            Payloads.profile([Payloads.msp_grant(make_uuid(9))], email="user@example.invalid"),
            {
                make_uuid(9): [
                    Payloads.response(
                        status=200,
                        data=[
                            {"id": ORG_A, "name": "Alpha Org"},
                            {"id": ORG_B, "name": "Beta Org"},
                            {"id": org_c, "name": "Gamma Org"},
                        ],
                    )
                ]
            },
        )
        world.mist.add(ORG_A, (SITE_1, "Site One"), [(make_uuid(101), "ex-01", "switch", "EX4100-48P")])
        world.mist.add(
            ORG_B,
            (SITE_2, "Site Two"),
            [(make_uuid(201), "ex-02", "switch", "EX4100-48P"), (make_uuid(202), "ex-03", "switch", "EX4100-48P")],
        )
        world.mist.failures[f"listOrgSites:{org_c}"] = Payloads.response(status=status, data={"detail": "refused"})

    def test_one_phrase_one_report_and_the_failed_organization_is_a_row(
        self, world: World, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Three organizations: the total phrase is for three switches, and the report has the failure row."""
        self.build(world)
        world.answer = "RUN 3 TARGETS"
        result, lines = run_menu(capsys)
        rows = world.rows()
        assert result == len(rows)
        assert "  Scope: MSP" in lines and "  Organizations in scope: 3" in lines
        assert "  Gamma Org was not read, because Mist could not list its switches. See the log for the cause." in lines
        assert "  Total targets: 3" in lines  # The phrase names the total of the organizations that were read.
        assert {row["scope"] for row in rows} == {"msp"}
        assert {row["org_name"] for row in rows} == {"Alpha Org", "Beta Org", "Gamma Org"}
        failure = [row for row in rows if row["org_name"] == "Gamma Org"]
        assert len(failure) == 1 and failure[0]["collection_status"] == "failed" and failure[0]["device_id"] == ""
        assert lines[-1] == "Run status: partial"
        root = Written.master(world.tmp_path / "data")  # The XML file tells the same story as the CSV report.
        assert (root.get("scope"), root.get("organizations"), root.get("unread")) == ("msp", "3", "1")
        unread = [org for org in root.iterfind("mh:organization", NS) if org.get("status") == "failed"]
        assert [org.get("name") for org in unread] == ["Gamma Org"] and len(unread[0]) == 0  # No site below it.

    @pytest.mark.parametrize("status", [401, 404, 429, 500, 502, 503])
    def test_any_http_failure_of_one_organization_leaves_the_others_running(
        self, world: World, capsys: pytest.CaptureFixture[str], status: int
    ) -> None:
        """Gamma Org fails with each HTTP status, and Alpha Org and Beta Org still give their hardware rows."""
        self.build(world, status)
        world.answer = "RUN 3 TARGETS"
        result, lines = run_menu(capsys)
        rows = world.rows()
        assert result == len(rows) and lines[-1] == "Run status: partial"
        failure = [row for row in rows if row["org_name"] == "Gamma Org"]
        assert [row["collection_status"] for row in failure] == ["failed"]  # One outcome row for the unread one.
        assert {row["org_name"] for row in rows if row["record_type"] == "hardware_item"} == {"Alpha Org", "Beta Org"}

    def test_the_ledger_organization_follows_the_organization_being_read(self, world: World) -> None:
        """A site read of each organization ran with that organization in the ledger."""
        self.build(world)
        world.answer = "RUN 3 TARGETS"
        ExHardwareInventoryReport.run()
        by_site = {site: org for _, site, org in world.mist.calls("listSiteDevices")}
        assert by_site[SITE_1] == ORG_A and by_site[SITE_2] == ORG_B  # Each read had its own organization.
        assert world.ledger.org_id is None  # Restored.


class TestMistFailures:
    """Mist refuses a read, answers with a server error, or cannot be reached: the run stays safe and plain."""

    NOT_READ = "  Alpha Org was not read, because Mist could not list its switches. See the log for the cause."
    EMPTY = "No connected EX switch was found. No file was written."  # The last line when nothing could be read.
    UPSTREAM = "UPSTREAM-ERROR-TEXT"  # Text that only the failed call holds. It must never reach a reader.

    @staticmethod
    def run_unread(capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture) -> tuple[int, list[str], str]:
        """Run the menu and return its result, its console lines, and everything that a reader can see."""
        caplog.set_level(logging.DEBUG)  # Capture every log line to prove that no error text leaks.
        result, lines = run_menu(capsys)
        return result, lines, "\n".join(lines) + caplog.text  # The console and the log.

    def check_nothing_ran(self, world: World, shown: str) -> None:
        """Prove that no shell opened, no report exists, and neither the error text nor the credential leaked."""
        assert world.shells.opened == 0 and world.ledger.org_id is None  # Nothing ran and the ledger is clean.
        assert not list((world.tmp_path / "data").glob("*.csv"))  # No report.
        assert self.UPSTREAM not in shown and TOKEN not in shown  # Neither the error text nor the credential leaks.

    @pytest.mark.parametrize("call", ["listOrgSites", "listSiteDevices", "listSiteDevicesStats"])
    @pytest.mark.parametrize("status", [401, 403, 404, 429, 500, 502, 503])
    def test_an_http_error_on_a_discovery_read_leaves_the_organization_unread(
        self,
        world: World,
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
        call: str,
        status: int,
    ) -> None:
        """Each 4xx and 5xx answer to each discovery read gives the plain sentence."""
        world.org_token()
        world.mixed_site_one()
        world.mist.failures[call] = Payloads.response(status=status, data={"detail": self.UPSTREAM})
        result, lines, shown = self.run_unread(capsys, caplog)
        assert result == 0 and self.NOT_READ in lines and lines[-1] == self.EMPTY
        self.check_nothing_ran(world, shown)

    @pytest.mark.parametrize(
        "fault",
        [requests.exceptions.ConnectionError, requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout],
    )
    def test_a_transport_fault_leaves_the_organization_unread(
        self,
        world: World,
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
        fault: type[Exception],
    ) -> None:
        """A refused connection and a timeout give the same plain sentence, and the error text stays out."""
        world.org_token()
        world.mixed_site_one()
        world.mist.failures["listOrgSites"] = fault(self.UPSTREAM)  # The SDK call raises instead of answering.
        result, lines, shown = self.run_unread(capsys, caplog)
        assert result == 0 and self.NOT_READ in lines and lines[-1] == self.EMPTY
        self.check_nothing_ran(world, shown)

    def test_a_server_error_when_the_status_is_read_again_runs_no_shell(
        self, world: World, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Mist fails after the operator confirmed: no shell opens, and each switch is an outcome row."""
        world.org_token()
        world.mixed_site_one()
        world.answer = "RUN 2 TARGETS"
        world.before_answer = lambda: world.mist.failures.update(
            {"listSiteDevicesStats": Payloads.response(status=503, data={"detail": self.UPSTREAM})}
        )  # The preview worked, and the read at dispatch fails.
        result, lines = run_menu(capsys)
        rows = world.rows()
        assert result == len(rows) and lines[-1] == "Run status: partial"
        assert world.shells.opened == 0 and world.ledger.org_id is None  # No shell opened and the ledger is clean.
        assert {row["collection_status"] for row in rows} == {"skipped"}  # Both switches are outcome rows.
        assert {row["record_type"] for row in rows} == {"device_outcome"}
        assert {row["collection_detail"] for row in rows} == {
            "Mist reported no status for the switch when its turn came."
        }  # The plain cause, with no text from Mist.
        assert self.UPSTREAM not in json.dumps(rows)  # The error body of Mist never reaches the report.
