"""Contract tests for the phase watch of one multi-site operation.

Why:
    Issue #3245. A single-site run follows each cascade phase until the devices
    of that phase settle. A multi-site run showed the child job states only, so
    the page could read "completed" while the devices still rebooted. These
    tests drive the real Flask routes and the production aggregate build. The
    stand-ins sit only at the cloud edge and at the watch thread. No test opens
    a socket, no test starts a thread, and no test sends a firmware request.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator, Mapping, MutableMapping
from contextlib import contextmanager
from copy import deepcopy
from dataclasses import asdict, dataclass
from threading import Lock
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.firmware.aggregate_upgrade_service import AggregateUpgradeService
from src.upgrade_portal.app.routes import org_upgrade, select
from src.upgrade_portal.runtime import identity
from src.upgrade_portal.runtime.runs import PHASE_ORDER
from src.upgrade_portal.upgrade import options as option_rules
from src.upgrade_portal.upgrade.org_cascade.record import (
    ANCHORS_KEY,
    NO_CHILD_NOTE,
    NOT_STARTED_NOTE,
    PHASES_KEY,
    RUNNING_NOTE,
    WATCH_KEY,
    OrgPhaseWatch,
    WatchState,
)
from tests.support.lock_store_double import FakeLockStore
from tests.support.org_cascade_seams import CascadeSeamStandIn
from tests.support.org_precheck_seams import PrecheckAdopterStandIn

OPERATOR_EMAIL = "org-phase.operator@juniper.net"  # A reachable address, because a firmware write needs one.
CLOUD_ACCOUNT = "mist.account@juniper.net"  # The account label behind the signed cloud session.
SITE_TWO = "00000000-0000-0000-0000-0000000000cc"  # The second selected site of each test.
AP_ONE = "001122334455"  # The access point at the first site.
AP_TWO = "001122334466"  # The access point at the second site.
SWITCH_ONE = "001122334477"  # The switch at the first site.
GATEWAY_ONE = "001122334499"  # The gateway at the first site.
DEVICE_ROWS = {  # The name, the family, the model, and the version before, for each device address.
    AP_ONE: ("ap-one", "ap", "AP45", "0.14.1"),
    AP_TWO: ("ap-two", "ap", "AP45", "0.14.1"),
    SWITCH_ONE: ("switch-one", "switch", "EX4400", "23.4R1.8"),
    GATEWAY_ONE: ("gateway-one", "gateway", "SRX345", "23.4R1.8"),
}
ANCHOR = {"uptime": 86400, "last_seen": 1790000000}  # One uptime and one last report time before the write.
OPTIONS_API = "/api/org-upgrades/options"  # The save of the multi-site options.
SUBMIT_API = "/api/org-upgrades"  # The confirmed submission.
OPTIONS_SESSION_KEY = "org_upgrade_options"  # The cookie key that holds the saved options.
PLAN_CHOICES = {  # One plan of the three device families across both sites.
    "selected_types": ["ap", "switch", "gateway"],
    "version_ap": "0.15.1",
    "version_switch": "23.4R1.9",
    "version_gateway": "23.4R1.9",
    "strategy": "big_bang",
}
PHASE_TESTIDS = tuple(  # The three cells of each phase row, in the page order.
    f'data-testid="org-upgrade-phase-{kind}{name}"' for name in PHASE_ORDER for kind in ("", "progress-", "note-")
)
BROKEN_BODIES = (  # Two request bodies that hold no JSON object: an empty body and a malformed JSON body.
    pytest.param(b"", id="empty-body"),
    pytest.param(b"{bad json", id="malformed-json"),
)


class RecordStore:
    """Keep aggregate records in memory behind a compare-and-set, as the durable store does."""

    def __init__(self) -> None:
        """Start with no record."""
        self.records: dict[str, dict[str, Any]] = {}  # One detached record for each operation.
        self.guard = Lock()  # Serialize each read and each replacement.

    def write_run(self, record: Mapping[str, Any]) -> bool:
        """Store one detached record."""
        with self.guard:  # Keep the write atomic.
            self.records[str(record["run_id"])] = deepcopy(dict(record))  # Detach the value of the caller.
        return True  # The memory store accepts every write.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one detached record, or None."""
        with self.guard:  # Keep the read consistent with the writes.
            record = self.records.get(run_id)  # An unknown key reads as None.
            return deepcopy(record) if record is not None else None  # Detach the stored value.

    def compare_and_set_run(self, run_id: str, expected_version: int, replacement: Mapping[str, Any]) -> bool:
        """Replace one record only when its version matches."""
        with self.guard:  # Keep the comparison and the replacement atomic.
            record = self.records.get(run_id)  # The current durable value.
            if record is None or record.get("record_version") != expected_version:  # A stale caller.
                return False  # Refuse the replacement.
            self.records[run_id] = deepcopy(dict(replacement))  # Store the detached replacement.
            return True  # Report the accepted change.


class WatchService(AggregateUpgradeService):
    """Keep the production build, accept or refuse each child job, and reach no cloud.

    Attributes:
        accept: True when the stand-in cloud accepts every child job.
        seen: The durable record at the start of each submission, and the start calls at that moment.
    """

    def __init__(self, starter: RecordingStarter) -> None:
        """Keep the starter, so the submission can record the start calls before the first write."""
        super().__init__()  # The production build needs no cloud service.
        self.accept = True  # A test sets False to refuse every child job.
        self.seen: list[tuple[dict[str, Any], int]] = []  # One entry for each submission.
        self._starter = starter  # The recorded start calls of the route.

    def status(self, cloud_session: Any, record: Any, store: Any) -> Any:
        """Return the stored record as it is."""
        del cloud_session, store  # The test record already holds the cloud answers.
        return record  # No child read runs.

    def submit(self, cloud_session: Any, record: Any, store: Any, refresh_lock: Any) -> Any:
        """Record the durable record, then accept or refuse every child job without a cloud write."""
        del cloud_session, refresh_lock  # The production service tests cover the claim and the refresh.
        durable = store.read_run(str(record["run_id"])) or {}  # FR-001: the record before the first write.
        self.seen.append((durable, len(self._starter.calls)))  # FR-005: no start call before the write.
        for child in record["children"]:  # Each child reaches the stand-in cloud one time.
            child["status"] = "accepted" if self.accept else "rejected"  # The answer of the stand-in cloud.
        record["state"] = "running" if self.accept else "failed"  # The aggregate state after the answers.
        store.write_run(record)  # Persist the child answers.
        return record  # The route opens the progress page.


class RecordingStarter:
    """Record the operation of each start call, and start no thread.

    Attributes:
        calls: The child states and the watch state of each call, in order.
        fault: An error that each call raises, or None.
    """

    def __init__(self) -> None:
        """Start with no call and no fault."""
        self.calls: list[dict[str, Any]] = []  # The tests read the order and the count of the calls.
        self.fault: Exception | None = None  # A test sets an error to prove that the page still answers.

    def __call__(self, record: Mapping[str, Any], deps: Any) -> bool:
        """Record one call, and raise the fault when a test set one."""
        del deps  # The recorder starts no walk.
        children = [str(child.get("status", "")) for child in record.get("children", [])]  # The child states.
        self.calls.append({"children": children, "watch": OrgPhaseWatch.state_of(record)})  # One entry.
        if self.fault is not None:  # The test asks for a fault in the watch start.
            raise self.fault  # The route must catch the fault.
        return False  # No thread started.


@dataclass
class WatchHarness:
    """Hold the signed client and each stand-in of one test."""

    client: FlaskClient  # The signed browser session.
    app: Flask  # The application, so a test can replace one seam.
    store: RecordStore  # The durable store of every operation.
    service: WatchService  # The production build with a stand-in cloud.
    seams: CascadeSeamStandIn  # The anchor read that reaches no cloud.
    starter: RecordingStarter  # The watch start that starts no thread.


def inventory_row(mac: str) -> dict[str, str]:
    """Build one device row of the site inventory, with the field of the options page and the raw field."""
    name, family, model, version = DEVICE_ROWS[mac]  # The fixed identity of the device.
    return {
        "mac": mac,
        "name": name,
        "device_type": family,
        "type": family,
        "model": model,
        "version": version,
    }  # The row matches the option reader.


def option_builder(devices: Mapping[str, list[dict[str, str]]]) -> Callable[..., dict[str, Any]]:
    """Return the stand-in of the site option mapper, with the production record shape."""

    def build(cloud_session: Any, org_id: str, site_id: str, body: Mapping[str, Any]) -> dict[str, Any]:
        """Build the targets and the options of one site without a cloud read."""
        del cloud_session, org_id  # The stand-in reads no inventory from the cloud.
        entries = option_rules.build_targets(devices[site_id], list(body["targets"]))  # One entry for each choice.
        return {"targets": entries, "options": asdict(option_rules.build_options(dict(body)))}  # Production shape.

    return build  # The route calls the mapper one time for each site.


def install_edges(app: Flask, fake_mist_api: Any, org_id: str, site_one: str, store: RecordStore) -> None:
    """Replace each cloud edge of the multi-site routes with a stand-in."""
    devices = {  # The inventory of both sites.
        site_one: [inventory_row(AP_ONE), inventory_row(SWITCH_ONE), inventory_row(GATEWAY_ONE)],
        SITE_TWO: [inventory_row(AP_TWO)],
    }
    fake_mist_api.payloads["listOrgSites"] = [  # The organization holds both selected sites.
        {"id": site_one, "name": "Test Site", "org_id": org_id},
        {"id": SITE_TWO, "name": "Site Two", "org_id": org_id},
    ]
    app.config.update(  # Every read and every write stays in memory.
        {
            "WTF_CSRF_ENABLED": False,  # The contract drives the routes, not the form tokens.
            "MIST_READER": fake_mist_api.read,  # The site list reaches no cloud.
            "SITE_LOCK_READER": lambda org_id, site_ids: {site_id: None for site_id in site_ids},  # No holder.
            select.LOCK_CLIENT_KEY: FakeLockStore(),  # Every lock write stays in memory.
            "RUN_STORE": store,  # Every operation stays in memory.
            org_upgrade.DEVICE_VERSION_READER_CONFIG_KEY: lambda cloud_session, site_id: {},  # No stats read.
            org_upgrade.OPTIONS_VIEW_CONFIG_KEY: lambda session, org, site: {"targets": deepcopy(devices[site])},
            org_upgrade.OPTIONS_BUILDER_CONFIG_KEY: option_builder(devices),  # The save reaches no cloud.
            "MIST_SELF_READER": lambda cloud_session: {"email": CLOUD_ACCOUNT},  # No self read.
        }
    )


@contextmanager
def signed_client(app: Flask, org_id: str, site_one: str) -> Iterator[FlaskClient]:
    """Yield a client whose signed session selects the multi-site mode and both sites."""
    owner = identity.build_owner(OPERATOR_EMAIL, identity.issue_browser_id())  # The signed operator.
    identity.SESSION_REGISTRY.register(  # The session guard finds the operator record.
        identity.OperatorSession(
            owner=owner,
            cloud_session=object(),
            credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
            selected_site_ids=(site_one, SITE_TWO),
        )
    )
    try:  # Drop the operator record after the test, also after a failure.
        with app.test_client() as client:  # Keep the signed session across the requests.
            client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)  # The browser identity.
            with client.session_transaction() as browser_session:  # Sign the multi-site scope.
                browser_session[identity.SESSION_OWNER_KEY] = owner.key  # The owner of each operation.
                browser_session["selected_org_id"] = org_id  # The selected organization.
                browser_session["selected_upgrade_mode"] = "multi_site"  # The multi-site mode.
            yield client  # The test drives the routes.
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)  # No later test finds this operator.


@pytest.fixture
def harness(portal_app: Flask, fake_mist_api: Any, fake_org_id: str, fake_site_id: str) -> Iterator[WatchHarness]:
    """Return a signed client with two selected sites, a stand-in cloud, and a recorded watch start."""
    store, starter = RecordStore(), RecordingStarter()  # One fresh stand-in of each kind.
    service = WatchService(starter)  # The production build that records each submission.
    install_edges(portal_app, fake_mist_api, fake_org_id, fake_site_id, store)  # No cloud edge stays live.
    portal_app.config["AGGREGATE_UPGRADE_SERVICE"] = service  # The production writes with no cloud call.
    seams = CascadeSeamStandIn(anchors={mac: ANCHOR for mac in DEVICE_ROWS}).install(
        portal_app.config
    )  # The seam supplies anchors.
    portal_app.config[org_upgrade.CASCADE_STARTER_CONFIG_KEY] = starter  # Record each watch start.
    PrecheckAdopterStandIn((fake_site_id, SITE_TWO)).install(portal_app.config)  # Issue #3243: each pre-check.
    with signed_client(portal_app, fake_org_id, fake_site_id) as client:  # The signed multi-site operator.
        yield WatchHarness(client, portal_app, store, service, seams, starter)  # The test receives every stand-in.


def save_plan(harness: WatchHarness) -> str:
    """Save the plan of every device at both sites, and return its operation identifier."""
    answer = harness.client.post(OPTIONS_API, json=PLAN_CHOICES)  # The options save.
    assert answer.status_code == 200, answer.get_json()  # A refused save stops the test with its reason.
    with harness.client.session_transaction() as browser_session:  # Read the signed cookie.
        options = deepcopy(browser_session.get(OPTIONS_SESSION_KEY)) or {}  # The saved options of the session.
    return str(options.get("operation_id", ""))  # The durable identity of the new plan.


def confirm(harness: WatchHarness, operation_id: str) -> None:
    """Send the typed confirmation, and require the answer that opens the progress page."""
    answer = harness.client.post(SUBMIT_API, json={"confirmation": "CONFIRM"})  # The typed confirmation.
    assert answer.status_code == 200, answer.get_json()  # A refused submission stops the test with its reason.
    assert answer.get_json() == {"next": f"/upgrade/org/jobs/{operation_id}"}  # The progress page opens.


def job_page(harness: WatchHarness, operation_id: str) -> str:
    """Return the progress page of one operation."""
    answer = harness.client.get(f"/upgrade/org/jobs/{operation_id}")  # The page of the operation.
    assert answer.status_code == 200, answer.get_data(as_text=True)[:400]  # The page must answer.
    return answer.get_data(as_text=True)  # The rendered page.


def job_status(harness: WatchHarness, operation_id: str) -> dict[str, Any]:
    """Return the status poll answer of one operation."""
    answer = harness.client.get(f"/api/org-upgrades/{operation_id}")  # The poll of the page.
    assert answer.status_code == 200, answer.get_json()  # The poll must answer.
    return dict(answer.get_json())  # The public status.


def phase_active_attribute(page: str) -> str:
    """Return the poll rule that the page gives to the script."""
    found = re.search(r'data-org-upgrade-region[^>]*?data-phase-active="([a-z]+)"', page, re.DOTALL)  # The region.
    assert found is not None, "The status region holds no data-phase-active attribute."  # The script needs it.
    return found.group(1)  # "true" or "false".


def put_watch(harness: WatchHarness, operation_id: str, change: Callable[[MutableMapping[str, Any]], None]) -> None:
    """Change the stored record of one operation, as the watch thread does between two polls."""
    change(harness.store.records[operation_id])  # The next page read and the next poll read the change.


def switches_wait_after_the_jobs_end(record: MutableMapping[str, Any]) -> None:
    """Store a watch that waits for the switches after the cloud ended every child job."""
    for child in record["children"]:  # The cloud reports every child job as ended.
        child["status"] = "completed"  # A final child state.
    record["state"] = "completed"  # The aggregate state of the ended child jobs.
    record[PHASES_KEY][0].update({"state": "settled", "settled": 1, "total": 1})  # The gateways settled.
    record[PHASES_KEY][1].update({"state": "waiting", "settled": 0, "total": 1})  # The switches still reboot.
    OrgPhaseWatch.set_state(record, WatchState.RUNNING, RUNNING_NOTE, None)  # The watch still runs.


def watch_finished(record: MutableMapping[str, Any]) -> None:
    """Store a watch that ended every phase."""
    for entry in record[PHASES_KEY]:  # Every phase ended.
        entry.update({"state": "settled", "settled": 1, "total": 1})  # One device settled in each phase.
    OrgPhaseWatch.set_state(record, WatchState.FINISHED, "Every phase ended.", None)  # The watch ended.


def earlier_release(record: MutableMapping[str, Any]) -> None:
    """Remove the watch fields, as a record of a release before issue #3245 holds none."""
    for key in (WATCH_KEY, PHASES_KEY, ANCHORS_KEY):  # The three fields that the submission adds.
        record.pop(key, None)  # An earlier release stored none of them.


# ---------------------------------------------------------------------------
# The submission stores the anchors, the phases, and the watch state.
# ---------------------------------------------------------------------------


def test_the_submission_stores_the_anchors_before_the_first_write(harness: WatchHarness) -> None:
    """FR-001, FR-003, and FR-004: the durable record holds the watch fields before the cloud receives a job."""
    operation_id = save_plan(harness)  # The planned operation.
    confirm(harness, operation_id)  # The operator types CONFIRM.
    durable, starts_before = harness.service.seen[0]  # The record at the start of the submission.
    assert {child["device_family"] for child in durable["children"]} == {"ap", "switch", "gateway"}  # 3 families.
    assert harness.seams.anchor_reads == [operation_id]  # One anchor read for the operation.
    assert durable[ANCHORS_KEY] == {mac: ANCHOR for mac in DEVICE_ROWS}  # FR-001: every device has its anchor.
    assert [entry["name"] for entry in durable[PHASES_KEY]] == list(PHASE_ORDER)  # FR-003: the cascade order.
    assert {entry["state"] for entry in durable[PHASES_KEY]} == {"pending"}  # No phase started yet.
    assert durable[WATCH_KEY]["state"] == WatchState.NOT_STARTED.value  # FR-004: the first watch state.
    assert durable[WATCH_KEY]["note"] == NOT_STARTED_NOTE  # The page explains the wait.
    assert starts_before == 0  # FR-005: no watch start before the first write.


def test_the_watch_starts_after_the_cloud_accepts_a_child_job(harness: WatchHarness) -> None:
    """FR-005: the submission calls the starter one time, with the accepted child jobs."""
    operation_id = save_plan(harness)  # The planned operation.
    confirm(harness, operation_id)  # The operator types CONFIRM.
    assert len(harness.starter.calls) == 1  # One start call for the submission.
    assert set(harness.starter.calls[0]["children"]) == {"accepted"}  # The cloud accepted every child job.
    assert harness.starter.calls[0]["watch"] == WatchState.NOT_STARTED.value  # The starter sees the first state.


def test_a_repeated_submission_keeps_the_first_anchors(harness: WatchHarness) -> None:
    """A submission after a lost answer keeps the anchors of the first try, and reads no new anchor."""
    operation_id = save_plan(harness)  # The planned operation.
    first = {AP_ONE: {"uptime": 7, "last_seen": 1}}  # The anchors that an earlier try stored.
    put_watch(
        harness, operation_id, lambda record: record.update(OrgPhaseWatch.prepared(record, first, ""))
    )  # The first try stored anchors.
    confirm(harness, operation_id)  # The operator types CONFIRM again.
    assert harness.seams.anchor_reads == []  # No second anchor read.
    assert harness.store.records[operation_id][ANCHORS_KEY] == first  # The first anchors stay.


def test_a_fault_in_the_anchor_read_never_blocks_the_submission(harness: WatchHarness) -> None:
    """FR-002: a fault in the anchor step leaves no watch, and every child job still reaches the cloud."""

    def broken_reader(cloud_session: Any, record: Any) -> Any:
        """Raise the fault of an unreachable cloud."""
        del cloud_session, record  # The fault comes before any read.
        raise RuntimeError("The statistics read failed.")  # The route must catch the fault.

    harness.app.config[org_upgrade.ANCHOR_READER_CONFIG_KEY] = broken_reader  # Replace the anchor seam.
    operation_id = save_plan(harness)  # The planned operation.
    confirm(harness, operation_id)  # The submission continues.
    stored = harness.store.records[operation_id]  # The durable record after the submission.
    assert WATCH_KEY not in stored and ANCHORS_KEY not in stored  # No watch fields exist.
    assert {child["status"] for child in stored["children"]} == {"accepted"}  # Every child job reached the cloud.
    assert 'data-testid="org-upgrade-phases"' not in job_page(harness, operation_id)  # No phase card.


def test_a_fault_in_the_watch_start_never_hides_the_page(harness: WatchHarness) -> None:
    """A fault in the watch start leaves the submission, the page, and the poll working."""
    harness.starter.fault = RuntimeError("The thread did not start.")  # Each start call raises.
    operation_id = save_plan(harness)  # The planned operation.
    confirm(harness, operation_id)  # The submission answers.
    assert 'data-testid="org-upgrade-phases"' in job_page(harness, operation_id)  # The page still answers.
    assert job_status(harness, operation_id)["phase_watch"]["state"] == WatchState.NOT_STARTED.value  # The poll.
    assert len(harness.starter.calls) == 3  # The submission, the page, and the poll each tried one start.


@pytest.mark.parametrize("body", BROKEN_BODIES)
def test_the_confirmation_parser_reads_a_broken_body_as_no_word(portal_app: Flask, body: bytes) -> None:
    """The parser reads an empty body or a malformed JSON body as empty text, and raises no JSON fault.

    Why:
        The submit route reads the typed word before every other step. The
        parser turns a JSON fault into empty text, so the route answers 400,
        and never 500, for a broken body.
    """
    context = portal_app.test_request_context(  # One request with the broken body, and no route call.
        SUBMIT_API, method="POST", data=body, content_type="application/json"
    )
    with context:  # The parser reads the body of the current request.
        assert org_upgrade.confirmation_value() == ""  # No typed word, so no confirmation matches.


@pytest.mark.parametrize("body", BROKEN_BODIES)
def test_a_broken_confirmation_body_prepares_no_watch(harness: WatchHarness, body: bytes) -> None:
    """A confirmation with an empty body or a malformed JSON body stores no watch and reaches no cloud.

    Why:
        FR-001 prepares the watch only inside a confirmed submission. A body
        that holds no valid JSON object holds no typed word, so the route
        refuses it before the anchor read, the store write, and the cloud.
    """
    operation_id = save_plan(harness)  # The planned operation.
    planned = deepcopy(harness.store.records[operation_id])  # The durable plan before the broken request.
    answer = harness.client.post(SUBMIT_API, data=body, content_type="application/json")  # The broken body.
    assert (answer.status_code, answer.get_json()["error"]["code"]) == (
        400,
        "confirmation_required",
    )  # The route refuses the body.
    assert harness.store.records[operation_id] == planned  # The route wrote nothing.
    assert WATCH_KEY not in planned and ANCHORS_KEY not in planned  # The plan holds no watch fields yet.
    assert (harness.seams.anchor_reads, harness.starter.calls, harness.service.seen) == ([], [], [])  # No step ran.


# ---------------------------------------------------------------------------
# The page and the poll start the watch again, and show the phases.
# ---------------------------------------------------------------------------


def test_each_page_read_and_each_poll_starts_the_watch_again(harness: WatchHarness) -> None:
    """FR-012: the page and the poll call the starter, so a watch starts again after a portal restart."""
    operation_id = save_plan(harness)  # The planned operation.
    confirm(harness, operation_id)  # The first start call.
    job_page(harness, operation_id)  # The second start call.
    job_status(harness, operation_id)  # The third start call.
    assert len(harness.starter.calls) == 3  # One start call for each request.


def test_the_page_shows_the_phase_card_with_every_test_identifier(harness: WatchHarness) -> None:
    """FR-017: the page shows the four phase rows, the watch line, and the poll rule."""
    operation_id = save_plan(harness)  # The planned operation.
    confirm(harness, operation_id)  # The operator types CONFIRM.
    page = job_page(harness, operation_id)  # The progress page.
    assert 'data-testid="org-upgrade-phases"' in page  # The phase card.
    assert all(testid in page for testid in PHASE_TESTIDS)  # Three cells for each of the four phases.
    watch_state = re.search(r'data-testid="org-upgrade-phase-watch-state"[^>]*>([^<]*)<', page)  # The label.
    assert watch_state is not None and watch_state.group(1) == "Not started"  # The first watch label.
    assert phase_active_attribute(page) == "true"  # FR-018: the poll starts the watch.


def test_the_poll_reports_the_phases_and_the_poll_rule(harness: WatchHarness) -> None:
    """FR-017 and FR-019: the poll answer holds the phases, the watch line, and the current phase."""
    operation_id = save_plan(harness)  # The planned operation.
    confirm(harness, operation_id)  # The operator types CONFIRM.
    status = job_status(harness, operation_id)  # The first poll.
    assert [entry["name"] for entry in status["phases"]] == list(PHASE_ORDER)  # The four phases.
    assert status["phase_watch"]["label"] == "Not started"  # The watch line.
    assert status["phase_active"] is True  # The poll continues until the watch ends.
    assert status["current_phase"] is None  # FR-019: no phase waits yet.


def test_the_poll_continues_while_the_watch_runs_after_the_jobs_end(harness: WatchHarness) -> None:
    """FR-018: a final child state does not stop the poll while the devices of a phase still reboot."""
    operation_id = save_plan(harness)  # The planned operation.
    confirm(harness, operation_id)  # The operator types CONFIRM.
    put_watch(harness, operation_id, switches_wait_after_the_jobs_end)  # The cloud ended every child job.
    status = job_status(harness, operation_id)  # The poll after the child jobs ended.
    assert status["status"] == "completed" and status["phase_active"] is True  # The poll must continue.
    assert status["current_phase"] == "Switches"  # FR-019: the label of the waiting phase.
    assert phase_active_attribute(job_page(harness, operation_id)) == "true"  # A reload keeps the poll.
    put_watch(harness, operation_id, watch_finished)  # The watch ended every phase.
    assert job_status(harness, operation_id)["phase_active"] is False  # Now the poll can stop.


def test_a_record_with_no_watch_shows_no_phase_card(harness: WatchHarness) -> None:
    """A record of an earlier release shows no phase card, and the poll rule reads the job state only."""
    operation_id = save_plan(harness)  # The planned operation.
    confirm(harness, operation_id)  # The operator types CONFIRM.
    put_watch(harness, operation_id, earlier_release)  # An earlier release stored no watch fields.
    page = job_page(harness, operation_id)  # The progress page.
    status = job_status(harness, operation_id)  # The poll.
    assert 'data-testid="org-upgrade-phases"' not in page  # No phase card.
    assert phase_active_attribute(page) == "false"  # The poll rule reads the job state only.
    assert (status["phases"], status["phase_watch"], status["phase_active"]) == (
        [],
        None,
        False,
    )  # The poll reports no watch.


def test_no_accepted_child_job_names_the_gap_and_stops_the_poll_rule(harness: WatchHarness) -> None:
    """FR-005: when the cloud refuses every child job, the watch line says so, and the poll can stop."""
    harness.service.accept = False  # The stand-in cloud refuses every child job.
    operation_id = save_plan(harness)  # The planned operation.
    confirm(harness, operation_id)  # The submission ends with no accepted child job.
    status = job_status(harness, operation_id)  # The poll.
    assert status["phase_watch"]["note"] == NO_CHILD_NOTE  # The watch line names the gap.
    assert status["phase_active"] is False  # No watch can start, so the poll can stop.
