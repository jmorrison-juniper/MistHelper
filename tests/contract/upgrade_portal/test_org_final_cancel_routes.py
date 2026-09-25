"""Contract tests for the cancel controls of a final multi-site operation.

Why:
    Issue #3225. The progress page of a completed operation still showed the
    cancel form, and the cancel route sent one cloud cancel call for each child
    job. The single-site stop refuses a final run with 409 and sends no cloud
    request. These tests drive the real Flask routes and the production
    aggregate service, with stand-ins only at the cloud edge. No test opens a
    socket.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from copy import deepcopy
from dataclasses import dataclass
from threading import Lock
from types import SimpleNamespace
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.firmware.aggregate_upgrade_service import AggregateBuildInput, AggregateUpgradeService
from src.firmware.org_upgrade_service import OrgUpgradeResult
from src.firmware.upgrade_service import CancelOutcome, DeviceTarget, UpgradeOptions
from src.upgrade_portal.app.routes import org_upgrade, select
from src.upgrade_portal.runtime import identity
from tests.support.lock_store_double import FakeLockStore
from tests.support.org_cascade_seams import CascadeSeamStandIn

OPERATOR_EMAIL = "org-final.operator@juniper.net"  # A reachable address, because a firmware write needs one.
SITE_ONE = "00000000-0000-0000-0000-0000000000bb"  # The shared site fixture value, which is the first site.
SITE_TWO = "00000000-0000-0000-0000-0000000000cc"  # The second selected site of each test.
AP_ONE = "001122334455"  # The access point at the first site.
SWITCH_TWO = "001122334477"  # The switch at the second site.
WRITE_SESSION = SimpleNamespace(_MAX_429_RETRIES=0, _session=SimpleNamespace(adapters={}))  # A no-retry session.
FINAL_STATES = ("cancelled", "completed", "failed")  # The three final words of issue #3225.
LIVE_STATES = ("running", "partial", "attention_required")  # A cancel can still change these operations.
STOPPED = "The cloud stopped 1 device(s), and no device was writing firmware."  # The sentence of a site cancel.
NOT_CANCELLABLE = "org_upgrade_not_cancellable"  # The code of the refusal.


class RecordStore:
    """Keep aggregate records in memory behind a compare-and-set, as the durable store does."""

    def __init__(self) -> None:
        """Start with no record."""
        self.records: dict[str, dict[str, Any]] = {}  # One detached record for each operation.
        self.guard = Lock()  # Serialize each read and each replacement.

    def write_run(self, record: dict[str, Any]) -> bool:
        """Store one detached record."""
        with self.guard:  # Keep the write atomic.
            self.records[str(record["run_id"])] = deepcopy(record)  # Detach the value of the caller.
        return True  # The memory store accepts every write.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one detached record, or None."""
        with self.guard:  # Keep the read consistent with the writes.
            record = self.records.get(run_id)  # An unknown key reads as None.
            return deepcopy(record) if record is not None else None  # Detach the stored value.

    def compare_and_set_run(self, run_id: str, expected_version: int, replacement: dict[str, Any]) -> bool:
        """Replace one record only when its version matches."""
        with self.guard:  # Keep the comparison and the replacement atomic.
            record = self.records.get(run_id)  # The current durable value.
            if record is None or record.get("record_version") != expected_version:  # A stale caller.
                return False  # Refuse the replacement.
            self.records[run_id] = deepcopy(replacement)  # Store the detached replacement.
            return True  # Report the accepted change.


class CloudEdge:
    """Record each cancel call of the organization edge and of the site edge."""

    ACCEPTED_STATUS = (200, 202)  # Match the production service contract.
    GatewayFamily = SimpleNamespace(SSR="ssr", JUNOS="junos")  # Supply the family values that the reader uses.

    def __init__(self) -> None:
        """Start with no call."""
        self.cancels: list[str] = []  # Each entry names the job of one cancel call.

    def cancel(self, session: Any, org_id: str, upgrade_id: str) -> OrgUpgradeResult:
        """Accept one organization cancel."""
        del session  # The stand-in opens no socket.
        self.cancels.append(upgrade_id)  # A test counts the cancel calls.
        return OrgUpgradeResult(org_id, upgrade_id, 200, {}, None)  # The contract permits an empty body.

    def cancel_upgrade(self, session: Any, plan: Any, upgrade_id: str, status: Any) -> CancelOutcome:
        """Stop each device of one site child job."""
        del session, status  # The fixed answer needs the plan targets only.
        self.cancels.append(upgrade_id)  # A test counts the cancel calls.
        return CancelOutcome(tuple(device.mac for device in plan.targets), (), (), STOPPED)


class QuietService(AggregateUpgradeService):
    """Keep the production cancel, and read no child job on a page view."""

    def status(self, cloud_session: Any, record: Any, store: Any) -> Any:
        """Return the stored record as it is."""
        del cloud_session, store  # The test record already holds the cloud answers.
        return record  # No child read runs.


@dataclass
class FinalHarness:
    """Hold the signed client, the store, the cloud edge, and the owner of one test."""

    client: FlaskClient  # The signed browser session.
    store: RecordStore  # The durable store of every operation.
    edge: CloudEdge  # The cloud edge of every child job.
    service: AggregateUpgradeService  # The production service with the stand-ins.
    owner: str  # The owner key of the signed operator.
    org_id: str  # The selected organization.


@pytest.fixture
def harness(portal_app: Flask, fake_mist_api: Any, fake_org_id: str, fake_site_id: str) -> Iterator[FinalHarness]:
    """Return a signed client for the multi-site mode, with no operation yet."""
    store, edge = RecordStore(), CloudEdge()  # One fresh stand-in of each kind.
    service = QuietService(edge, edge)  # The production cancel with stand-ins at the cloud edge.
    fake_mist_api.payloads["listOrgSites"] = [  # The organization holds both selected sites.
        {"id": fake_site_id, "name": "Test Site", "org_id": fake_org_id},
        {"id": SITE_TWO, "name": "Site Two", "org_id": fake_org_id},
    ]
    portal_app.config.update(  # Replace each cloud edge with a stand-in.
        {
            "WTF_CSRF_ENABLED": False,  # The contract drives the routes, not the form tokens.
            "MIST_READER": fake_mist_api.read,  # The site list reaches no cloud.
            "SITE_LOCK_READER": lambda org_id, site_ids: {site_id: None for site_id in site_ids},  # No holder.
            select.LOCK_CLIENT_KEY: FakeLockStore(),  # Every lock write stays in memory.
            "RUN_STORE": store,  # Every operation stays in memory.
            "AGGREGATE_UPGRADE_SERVICE": service,  # The production cancel with no real cloud call.
            org_upgrade.DEVICE_VERSION_READER_CONFIG_KEY: lambda cloud_session, site_id: {},  # No stats read.
            "MIST_SELF_READER": lambda cloud_session: {"email": OPERATOR_EMAIL},  # No self read.
        }
    )
    CascadeSeamStandIn().install(portal_app.config)  # Issue #3245: no anchor read and no watch thread.
    owner = identity.build_owner(OPERATOR_EMAIL, identity.issue_browser_id())  # The signed operator.
    operator = identity.OperatorSession(  # The server-side record that the session guard reads.
        owner=owner,
        cloud_session=WRITE_SESSION,  # The cancel requires the no-retry write session.
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
        selected_site_ids=(fake_site_id, SITE_TWO),
    )
    assert fake_site_id == SITE_ONE, "The shared site fixture changed, so the site rows no longer match."
    identity.SESSION_REGISTRY.register(operator)  # The session guard finds the operator record.
    try:  # Drop the operator record after the test, also after a failure.
        with portal_app.test_client() as client:  # Keep the signed session across the requests.
            client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)  # The browser identity.
            with client.session_transaction() as browser_session:  # Sign the multi-site scope.
                browser_session[identity.SESSION_OWNER_KEY] = owner.key  # The owner of each operation.
                browser_session["selected_org_id"] = fake_org_id  # The selected organization.
                browser_session["selected_upgrade_mode"] = "multi_site"  # The multi-site mode.
            yield FinalHarness(client, store, edge, service, owner.key, fake_org_id)
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)  # No later test finds this operator.


def seed(harness: FinalHarness, state: str, child_state: str) -> str:
    """Store one operation whose two child jobs reached the cloud.

    Args:
        harness: The signed client and its stand-ins.
        state: The stored state of the operation.
        child_state: The stored state of each child job.

    Returns:
        The identifier of the operation.
    """
    sites = ({"site_id": SITE_ONE, "name": "Test Site"}, {"site_id": SITE_TWO, "name": "Site Two"})  # Approved.
    targets = (  # One access point and one switch across the two sites.
        DeviceTarget(AP_ONE, "ap-one", "ap", "AP45", "0.14.1", "0.15.1", SITE_ONE),
        DeviceTarget(SWITCH_TWO, "switch-two", "switch", "EX4400", "23.4R1.8", "23.4R1.9", SITE_TWO),
    )
    build = AggregateBuildInput(harness.owner, harness.org_id, sites, targets, UpgradeOptions(), "nonce")
    record = harness.service.build(build)  # The production plan, with no cloud call.
    for child in record["children"]:  # Each child job holds a cloud job.
        child["upgrade_id"] = f"job-{child['device_family']}"  # The cloud identity of the child job.
        child["status"] = child_state  # The last read state.
    record["state"] = state  # The stored state of the operation.
    harness.store.write_run(record)  # The routes read the durable record.
    return str(record["operation_id"])  # Each test reads or cancels this operation.


def change_child(harness: FinalHarness, operation_id: str, family: str, values: dict[str, Any]) -> None:
    """Change the stored fields of one child job.

    Args:
        harness: The signed client and its stand-ins.
        operation_id: The operation that holds the child job.
        family: The device family of the child job.
        values: The fields to set. A value of None removes the field.
    """
    record = harness.store.records[operation_id]  # The durable operation.
    child = next(child for child in record["children"] if child["device_family"] == family)  # The child job.
    for key, value in values.items():  # Apply each change in order.
        if value is None:  # A removed field.
            child.pop(key, None)
        else:  # A changed field.
            child[key] = value


def typed_cancel(harness: FinalHarness, operation_id: str) -> Any:
    """Send the typed cancel as the page script does, and return the answer."""
    path = f"/api/org-upgrades/{operation_id}/cancel"  # The cancel route of the operation.
    headers = {"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"}  # The page script headers.
    return harness.client.post(path, json={"confirmation": "CANCEL"}, headers=headers)


def page_of(harness: FinalHarness, operation_id: str) -> str:
    """Return the progress page of one operation."""
    return harness.client.get(f"/upgrade/org/jobs/{operation_id}").get_data(as_text=True)  # A page view.


def poll_of(harness: FinalHarness, operation_id: str) -> dict[str, Any]:
    """Return the status poll answer of one operation."""
    answer = harness.client.get(f"/api/org-upgrades/{operation_id}")  # The poll of the page script.
    assert answer.status_code == 200, answer.get_data(as_text=True)  # The owned operation answers.
    return dict(answer.get_json())  # The poll body.


def tag_with(page: str, test_id: str) -> str:
    """Return the opening tag of the element with one test identifier."""
    match = re.search(rf'<[a-z]+[^>]*data-testid="{re.escape(test_id)}"[^>]*>', page)  # The opening tag.
    assert match is not None, f"The page shows no element with the identifier {test_id}."
    return match.group(0)  # The tag with its attributes.


def site_cells(page: str, site_name: str) -> list[str]:
    """Return the cell texts of the site table row of one site, with no markup."""
    table = re.search(r"<tbody data-org-upgrade-sites>(.*?)</tbody>", page, re.DOTALL)  # The site table body.
    assert table is not None, "The page shows no site table."
    for row in re.findall(r"<tr>(.*?)</tr>", table.group(1), re.DOTALL):  # Each child job row.
        cells = [
            " ".join(re.sub(r"<[^>]+>", " ", cell).split())
            for cell in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row, re.DOTALL)
        ]
        if cells and cells[0] == site_name:  # The row of the site.
            return cells
    raise AssertionError(f"The site table shows no row for {site_name}.")


@pytest.mark.parametrize("state", FINAL_STATES)
def test_a_final_operation_refuses_the_typed_cancel_with_no_cloud_call(harness: FinalHarness, state: str) -> None:
    """The route answers 409 with its own code, and the store and the cloud see nothing."""
    operation_id = seed(harness, state, "completed")  # A final operation.
    version = harness.store.records[operation_id]["record_version"]  # The version before the cancel.
    answer = typed_cancel(harness, operation_id)  # The operator sends the typed cancel.
    error = answer.get_json()["error"]  # The refusal envelope.
    assert (answer.status_code, error["code"]) == (409, NOT_CANCELLABLE)  # The documented refusal.
    assert error["message"] == f"The operation is final: {state}. The portal sent no cancel request."
    assert harness.edge.cancels == []  # No cloud cancel call left the portal.
    stored = harness.store.records[operation_id]  # The durable operation after the refusal.
    assert (stored["record_version"], stored["cancellation"]["requested"]) == (version, False)  # No write.


@pytest.mark.parametrize("state", FINAL_STATES)
def test_the_page_of_a_final_operation_shows_no_cancel_form(harness: FinalHarness, state: str) -> None:
    """The page shows the final note, and the poll reports that no cancel is allowed."""
    operation_id = seed(harness, state, "completed")  # A final operation.
    page = page_of(harness, operation_id)  # The progress page.
    assert 'data-testid="org-upgrade-cancel-confirmation"' not in page  # No typed word field.
    assert 'data-testid="org-upgrade-cancel"' not in page  # No cancel button.
    assert 'data-testid="org-upgrade-cancel-caution"' not in page  # No caution about a cancel.
    assert " hidden" not in tag_with(page, "org-upgrade-cancel-closed")  # The final note shows.
    assert f"The operation is final: <span data-org-cancel-state>{state}</span>." in page  # The state word.
    assert poll_of(harness, operation_id)["cancel_allowed"] is False  # The poll hides a form of an old page.


@pytest.mark.parametrize("state", LIVE_STATES)
def test_the_page_of_a_live_operation_keeps_the_cancel_form(harness: FinalHarness, state: str) -> None:
    """A live operation keeps the form and the caution, and the final note stays hidden."""
    operation_id = seed(harness, state, "running")  # A live operation.
    page = page_of(harness, operation_id)  # The progress page.
    assert 'data-testid="org-upgrade-cancel-confirmation"' in page  # The typed word field.
    assert "disabled" in tag_with(page, "org-upgrade-cancel")  # The button waits for the typed word.
    assert 'data-testid="org-upgrade-cancel-caution"' in page  # The caution about a cancel.
    assert " hidden" in tag_with(page, "org-upgrade-cancel-closed")  # The final note waits for a final poll.
    assert poll_of(harness, operation_id)["cancel_allowed"] is True  # The poll keeps the form.


def test_a_live_operation_still_sends_the_typed_cancel(harness: FinalHarness) -> None:
    """The refusal applies to a final operation only."""
    operation_id = seed(harness, "running", "running")  # A live operation.
    answer = typed_cancel(harness, operation_id)  # The operator sends the typed cancel.
    assert answer.status_code == 200, answer.get_data(as_text=True)  # The cancel ran.
    assert sorted(harness.edge.cancels) == ["job-ap", "job-switch"]  # One cancel call for each child job.


def test_a_child_job_with_no_family_reads_unknown(harness: FinalHarness) -> None:
    """The site table and the cancel outcome panel never claim a family that the record does not hold."""
    operation_id = seed(harness, "cancelled", "cancelled")  # A final operation with a cancel result.
    result = {"status": "requested", "message": STOPPED, "cancelled": [SWITCH_TWO], "already_writing": []}
    change_child(harness, operation_id, "switch", {"cancellation": {**result, "no_cancel_available": []}})
    change_child(harness, operation_id, "switch", {"device_family": None})  # An earlier record holds no family.
    page = page_of(harness, operation_id)  # The progress page.
    assert site_cells(page, "Site Two")[1] == "unknown"  # The family cell of the site table.
    assert "Site Two (unknown)" in page and "Site Two ()" not in page  # The heading of the outcome panel.
    rows = poll_of(harness, operation_id)["site_upgrades"]  # The poll keeps the stored value.
    assert [row["device_family"] for row in rows] == ["ap", ""]  # The page script shows "unknown" for "".


def test_the_cancellation_cell_shows_one_text_in_the_page_and_the_poll(harness: FinalHarness) -> None:
    """The server builds one text, so the first render and each poll show the same words."""
    operation_id = seed(harness, "running", "running")  # A live operation.
    result = {"status": "requested", "message": STOPPED, "cancelled": [SWITCH_TWO], "already_writing": []}
    change_child(harness, operation_id, "switch", {"cancellation": {**result, "no_cancel_available": []}})
    expected = f"Status: requested. {STOPPED} Cancelled: {SWITCH_TWO}."  # The one text of the cell.
    page = page_of(harness, operation_id)  # The progress page.
    assert site_cells(page, "Site Two")[8] == expected  # The Cancellation cell of the site table.
    assert "Already writing:" not in page and "No cancellation:" not in page  # The old labels are gone.
    rows = poll_of(harness, operation_id)["site_upgrades"]  # The poll rows.
    assert [row["cancellation_text"] for row in rows] == ["", expected]  # The same text for the repaint.


def test_the_word_cells_of_the_tables_use_the_whole_word_class(harness: FinalHarness) -> None:
    """The family, status, site, type, and state cells never break inside a word."""
    operation_id = seed(harness, "completed", "completed")  # A final operation.
    page = page_of(harness, operation_id)  # The progress page.
    table = re.search(r"<tbody data-org-upgrade-sites>(.*?)</tbody>", page, re.DOTALL)  # The site table body.
    assert isinstance(table, re.Match), "The page holds no site table body."  # The table renders.
    assert table.group(1).count('<td class="cell-word">') == 4  # Two cells in each row.
    state_cell = tag_with(page, f"org-upgrade-device-state-{SWITCH_TWO}")  # The state cell of one device.
    assert 'class="cell-word"' in state_cell  # The state word stays whole.
    device_row = re.search(rf'data-testid="org-upgrade-device-row-{SWITCH_TWO}">(.*?)</tr>', page, re.DOTALL)
    assert isinstance(device_row, re.Match), "The page holds no row for the device."  # The row renders.
    assert device_row.group(1).count('class="cell-word"') == 3  # The site, the type, and the state.


def raw_cancel(harness: FinalHarness, operation_id: str, body: str) -> Any:
    """Send one cancel request with a raw JSON body, and return the answer."""
    headers = {"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"}  # The page script headers.
    path = f"/api/org-upgrades/{operation_id}/cancel"  # The cancel route of the operation.
    return harness.client.post(path, data=body, content_type="application/json", headers=headers)


def test_an_empty_body_sends_no_cancel_request(harness: FinalHarness) -> None:
    """A cancel with an empty body holds no typed word, so no cloud call and no write follow."""
    operation_id = seed(harness, "running", "running")  # A live operation, so only the body can refuse.
    version = harness.store.records[operation_id]["record_version"]  # The version before the request.
    answer = harness.client.post(
        f"/api/org-upgrades/{operation_id}/cancel",
        data="",
        headers={"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"},
    )  # The body holds no byte.
    assert (answer.status_code, answer.get_json()["error"]["code"]) == (400, "confirmation_required")
    assert harness.edge.cancels == []  # No cloud cancel call left the portal.
    assert harness.store.records[operation_id]["record_version"] == version  # The store saw no write.


def test_a_malformed_json_body_sends_no_cancel_request(harness: FinalHarness) -> None:
    """A cancel whose JSON body does not parse holds no typed word, so no cloud call and no write follow."""
    operation_id = seed(harness, "running", "running")  # A live operation, so only the body can refuse.
    version = harness.store.records[operation_id]["record_version"]  # The version before the request.
    answer = raw_cancel(harness, operation_id, '{"confirmation": bad json')  # The parser rejects the body.
    assert (answer.status_code, answer.get_json()["error"]["code"]) == (400, "confirmation_required")
    assert harness.edge.cancels == []  # No cloud cancel call left the portal.
    assert harness.store.records[operation_id]["record_version"] == version  # The store saw no write.
