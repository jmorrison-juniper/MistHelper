"""Contract tests for the cancel outcome panel of one multi-site operation.

Why:
    Issue #3246. The single-site stop page shows which devices the cloud
    canceled, which devices can still write firmware, and which devices have
    no cancel path. The multi-site page showed one status word for each child
    job. These tests drive the real Flask routes and the production aggregate
    service, with stand-ins only at the cloud edge. No test opens a socket.
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
from src.firmware.upgrade_service import CancelOutcome, DeviceTarget, UpgradeOptions, UpgradeSubmission
from src.upgrade_portal.app.routes import org_upgrade, select
from src.upgrade_portal.runtime import identity
from src.upgrade_portal.upgrade.org_cancel_outcomes import NEVER_STARTED_NOTE, UNSORTED_NOTE, OrgCancelOutcomes
from tests.support.lock_store_double import FakeLockStore
from tests.support.org_cascade_seams import CascadeSeamStandIn

OPERATOR_EMAIL = "org-cancel.operator@juniper.net"  # A reachable address, because a firmware write needs one.
SITE_ONE = "00000000-0000-0000-0000-0000000000bb"  # The shared site fixture value, which is the first site.
SITE_TWO = "00000000-0000-0000-0000-0000000000cc"  # The second selected site of each test.
AP_ONE = "001122334455"  # The access point at the first site. It stops.
AP_TWO = "001122334466"  # The access point at the second site. It still writes firmware.
SWITCH_ONE = "001122334477"  # The switch at the first site. Its site child job stops.
GATEWAY_TWO = "001122334488"  # The gateway at the second site. The cloud refused its child job.
WRITE_SESSION = SimpleNamespace(_MAX_429_RETRIES=0, _session=SimpleNamespace(adapters={}))  # A no-retry session.
CAUTION = "Caution: the cancellation stops each upgrade that waits to start."  # The first words of the caution.
SWITCH_TEXT = "The cloud stopped 1 device(s), and no device was writing firmware."  # The switch cancel sentence.


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


class OrgStandIn:
    """Answer the organization calls of the access point child job."""

    def __init__(self) -> None:
        """Start with an accepted cancel and no call."""
        self.cancel_error: str | None = None  # A test sets a cloud error to refuse the cancel.
        self.cancels: list[str] = []  # Each entry names one cancel call.

    def submit(self, session: Any, org_id: str, body: Any) -> OrgUpgradeResult:
        """Accept the access point child job."""
        del session, body  # The stand-in reads no request value.
        return OrgUpgradeResult(org_id, "ap-job", 200, {"id": "ap-job"}, None)  # A valid accepted answer.

    def cancel(self, session: Any, org_id: str, upgrade_id: str) -> OrgUpgradeResult:
        """Accept or refuse one cancel, as the test chooses."""
        del session  # The stand-in opens no socket.
        self.cancels.append(upgrade_id)  # A test counts the cancel calls.
        return OrgUpgradeResult(org_id, upgrade_id, 404 if self.cancel_error else 200, {}, self.cancel_error)


class DeviceStandIn:
    """Accept the switch child job, refuse the gateway child job, and stop the switch on a cancel."""

    ACCEPTED_STATUS = (200, 202)  # Match the production service contract.
    GatewayFamily = SimpleNamespace(SSR="ssr", JUNOS="junos")  # Supply the family values used by the reader.

    def invoke_upgrade(self, session: Any, plan: Any) -> UpgradeSubmission:
        """Accept the switch child job, and refuse the gateway child job with a client error."""
        del session  # The stand-in opens no socket.
        accepted = plan.targets[0].device_type == "switch"  # The cloud refuses the gateway child job.
        return UpgradeSubmission(
            upgrade_id="switch-job" if accepted else None,
            scope=plan.scope,
            accepted=tuple(target.mac for target in plan.targets) if accepted else (),
            rejected=() if accepted else ((plan.targets[0].mac, "refused"),),
            raw_status=202 if accepted else 400,
        )

    def cancel_upgrade(self, session: Any, plan: Any, upgrade_id: str, status: Any) -> CancelOutcome:
        """Stop each device of the switch child job."""
        del session, upgrade_id, status  # The fixed answer needs the plan targets only.
        return CancelOutcome(tuple(target.mac for target in plan.targets), (), (), SWITCH_TEXT)


class QuietService(AggregateUpgradeService):
    """Keep the production cancel, and read no child job on a page view."""

    def status(self, cloud_session: Any, record: Any, store: Any) -> Any:
        """Return the stored record as it is."""
        del cloud_session, store  # The test record already holds the cloud answers.
        return record  # No child read runs.


@dataclass
class CancelHarness:
    """Hold the signed client, the stand-ins, and the operation of one test."""

    client: FlaskClient  # The signed browser session.
    store: RecordStore  # The durable store of every operation.
    org: OrgStandIn  # The organization cloud edge.
    operation_id: str  # The operation that each test cancels.


def site_job(site_id: str, rebooting: list[str]) -> dict[str, Any]:
    """Build one site entry in the shape of the real organization answer."""
    job = {"id": f"job-{site_id[-4:]}", "status": "upgrading", "targets": {"reboot_in_progress": rebooting}}
    return {"site_id": site_id, "upgrade": job}  # The cloud nests the site job under "upgrade".


def running_operation(service: AggregateUpgradeService, store: RecordStore, owner: str, org_id: str) -> str:
    """Build and submit one operation, and mark one access point as rebooting.

    Args:
        service: The production aggregate service with the cloud stand-ins.
        store: The durable store of the operation.
        owner: The owner key of the signed operator.
        org_id: The selected organization.

    Returns:
        The identifier of the operation.
    """
    sites = ({"site_id": SITE_ONE, "name": "Test Site"}, {"site_id": SITE_TWO, "name": "Site Two"})  # Approved.
    targets = (  # Two access points, one switch, and one gateway across the two sites.
        DeviceTarget(AP_ONE, "ap-one", "ap", "AP45", "0.14.1", "0.15.1", SITE_ONE),
        DeviceTarget(AP_TWO, "ap-two", "ap", "AP45", "0.14.1", "0.15.1", SITE_TWO),
        DeviceTarget(SWITCH_ONE, "switch-one", "switch", "EX4400", "23.4R1.8", "23.4R1.9", SITE_ONE),
        DeviceTarget(GATEWAY_TWO, "gateway-two", "gateway", "SRX345", "23.4R1.8", "23.4R1.9", SITE_TWO),
    )
    record = service.build(AggregateBuildInput(owner, org_id, sites, targets, UpgradeOptions(), "nonce"))  # No call.
    store.write_run(record)  # The submission reads the durable record first.
    service.submit(WRITE_SESSION, record, store, lambda operation, child: None)  # The stand-ins accept or refuse.
    stored = store.records[str(record["run_id"])]  # The durable copy after the submission.
    ap_child = next(child for child in stored["children"] if child["device_family"] == "ap")  # The AP child job.
    ap_child["status"] = "running"  # A status read found the job in progress.
    ap_child["status_data"] = {"id": "ap-job", "upgrades": [site_job(SITE_ONE, []), site_job(SITE_TWO, [AP_TWO])]}
    return str(record["operation_id"])  # Each test cancels this operation.


@pytest.fixture
def harness(portal_app: Flask, fake_mist_api: Any, fake_org_id: str, fake_site_id: str) -> Iterator[CancelHarness]:
    """Return a signed client that owns one running operation across two sites."""
    store, org = RecordStore(), OrgStandIn()  # One fresh stand-in of each kind.
    service = QuietService(org, DeviceStandIn())  # The production cancel with stand-ins at the cloud edge.
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
    operation_id = running_operation(service, store, owner.key, fake_org_id)  # One running operation.
    identity.SESSION_REGISTRY.register(operator)  # The session guard finds the operator record.
    try:  # Drop the operator record after the test, also after a failure.
        with portal_app.test_client() as client:  # Keep the signed session across the requests.
            client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)  # The browser identity.
            with client.session_transaction() as browser_session:  # Sign the multi-site scope.
                browser_session[identity.SESSION_OWNER_KEY] = owner.key  # The owner of each operation.
                browser_session["selected_org_id"] = fake_org_id  # The selected organization.
                browser_session["selected_upgrade_mode"] = "multi_site"  # The multi-site mode.
            yield CancelHarness(client, store, org, operation_id)
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)  # No later test finds this operator.


def child_id(harness: CancelHarness, family: str) -> str:
    """Return the child job identifier of one device family."""
    record = harness.store.records[harness.operation_id]  # The durable operation.
    return next(str(child["child_id"]) for child in record["children"] if child["device_family"] == family)


def page_of(harness: CancelHarness) -> str:
    """Return the progress page of the operation."""
    return harness.client.get(f"/upgrade/org/jobs/{harness.operation_id}").get_data(as_text=True)  # A page view.


def cancel(harness: CancelHarness) -> Any:
    """Send the typed cancel from the browser form, and return the answer."""
    path = f"/api/org-upgrades/{harness.operation_id}/cancel"  # The cancel route of the operation.
    return harness.client.post(path, data={"confirmation": "CANCEL"}, headers={"Accept": "text/html"})


def items(page: str, test_id: str) -> list[str]:
    """Return the text of each item of one list of the page, in page order."""
    match = re.search(rf'data-testid="{re.escape(test_id)}">(.*?)</ul>', page, re.DOTALL)  # The list body.
    assert match is not None, f"The page shows no list with the identifier {test_id}."
    return [text.strip() for text in re.findall(r"<li[^>]*>([^<]*)</li>", match.group(1))]  # Each item.


def text_of(page: str, test_id: str) -> str:
    """Return the text of one element of the page."""
    match = re.search(rf'data-testid="{re.escape(test_id)}">([^<]*)<', page)  # The element text.
    assert match is not None, f"The page shows no element with the identifier {test_id}."
    return match.group(1).strip()  # The text without the indentation.


def panel_of(page: str) -> str:
    """Return the markup of the cancel outcome panel of the page."""
    match = re.search(r'<section[^>]*data-testid="org-cancel-outcome".*?</section>', page, re.DOTALL)  # The panel.
    assert match is not None, "The page shows no cancel outcome panel."
    return match.group(0)  # The complete panel markup.


def test_the_page_shows_the_caution_and_no_panel_before_a_cancel(harness: CancelHarness) -> None:
    """The panel stays hidden until a child job holds a cancel result."""
    page = page_of(harness)  # The progress page before the cancel.
    poll = harness.client.get(f"/api/org-upgrades/{harness.operation_id}").get_json()  # The status poll.
    assert 'data-testid="org-upgrade-cancel-caution"' in page and CAUTION in page  # The caution of the stop.
    assert 'data-testid="org-cancel-outcome"' not in page  # No cancel result exists yet.
    assert poll["cancel_outcomes"] == []  # The poll holds no row.
    assert poll["controls"]["signature"].endswith(";cancel=")  # The signature names no cancel status.


def test_the_cancel_sorts_each_child_job_into_three_lists(harness: CancelHarness) -> None:
    """Each child job shows its own three lists, and a reload shows the same lists."""
    answer = cancel(harness)  # The operator types CANCEL and presses the button.
    ap_id, switch_id, gateway_id = (child_id(harness, family) for family in ("ap", "switch", "gateway"))
    page = page_of(harness)  # The progress page after the cancel.
    assert answer.status_code == 303 and answer.headers["Location"].endswith(harness.operation_id)  # Same page.
    assert (items(page, f"org-cancel-outcome-cancelled-{ap_id}"), harness.org.cancels) == ([AP_ONE], ["ap-job"])
    assert items(page, f"org-cancel-outcome-writing-{ap_id}") == [AP_TWO]  # It reboots into the new firmware.
    assert items(page, f"org-cancel-outcome-no-cancel-{ap_id}") == ["Every device has a cancel path."]
    assert items(page, f"org-cancel-outcome-cancelled-{switch_id}") == [SWITCH_ONE]  # The site job stopped.
    assert text_of(page, f"org-cancel-outcome-message-{switch_id}") == SWITCH_TEXT  # The exact sentence.
    assert items(page, f"org-cancel-outcome-writing-{gateway_id}") == ["No device writes firmware."]
    assert text_of(page, f"org-cancel-outcome-note-{gateway_id}") == NEVER_STARTED_NOTE  # No cloud job exists.
    assert text_of(page, f"org-cancel-outcome-status-{gateway_id}") == "unavailable"  # The cancel had no job.
    assert panel_of(page_of(harness)) == panel_of(page)  # A reload shows the same stored lists.


def test_the_json_answer_and_the_poll_carry_the_same_rows(harness: CancelHarness) -> None:
    """A script reads the same three lists as the browser, and the signature names each cancel status."""
    path = f"/api/org-upgrades/{harness.operation_id}/cancel"  # The cancel route of the operation.
    answer = harness.client.post(path, json={"confirmation": "CANCEL"}).get_json()  # A script cancel.
    poll = harness.client.get(f"/api/org-upgrades/{harness.operation_id}").get_json()  # The status poll.
    ap_id, switch_id, gateway_id = (child_id(harness, family) for family in ("ap", "switch", "gateway"))
    assert answer["cancel_outcomes"] == poll["cancel_outcomes"]  # One rule builds both answers.
    assert [row["child_id"] for row in poll["cancel_outcomes"]] == [ap_id, switch_id, gateway_id]  # Plan order.
    signature = f"cancel={ap_id}:requested,{switch_id}:requested,{gateway_id}:unavailable"  # Each status.
    assert poll["controls"]["signature"].endswith(signature)  # A second tab loads the page again.


def test_a_stored_operation_shows_one_section_for_each_cancel_result(harness: CancelHarness) -> None:
    """A stored, a claimed, and a never-started result show a section, and a child job with no result shows none."""
    stored = harness.store.records[harness.operation_id]  # The durable operation of the page.
    ap, switch, gateway = stored["children"]  # The three child jobs, in plan order.
    stored["children"].append({**deepcopy(switch), "child_id": "child-quiet", "cancellation": None})  # No result.
    lists = {"cancelled": [AP_ONE], "already_writing": [AP_TWO], "no_cancel_available": []}  # A stored sort.
    ap["cancellation"] = {"status": "requested", "raw_status": 200, "message": "The stored sentence.", **lists}
    switch["cancellation"] = {"status": "cancel_claimed", "message": None}  # A cancel with no known outcome.
    gateway["cancellation"] = {"status": "unavailable", "message": "The child job holds no upgrade identifier."}
    page = page_of(harness)  # The progress page of the stored operation.
    assert page.count('<div class="status-panel" data-testid="org-cancel-outcome-') == 3  # One section each.
    assert 'data-testid="org-cancel-outcome-child-quiet"' not in page  # No result gives no section.
    assert items(page, f"org-cancel-outcome-writing-{ap['child_id']}") == [AP_TWO]  # The stored list.
    assert items(page, f"org-cancel-outcome-writing-{switch['child_id']}") == [SWITCH_ONE]  # No stop claim.
    assert text_of(page, f"org-cancel-outcome-note-{switch['child_id']}") == UNSORTED_NOTE  # The reason.
    assert text_of(page, f"org-cancel-outcome-note-{gateway['child_id']}") == NEVER_STARTED_NOTE  # No cloud job.


def test_a_refused_access_point_cancel_lists_each_access_point_as_writing(harness: CancelHarness) -> None:
    """The portal claims no stop when the cloud refuses the organization cancel."""
    harness.org.cancel_error = "The cloud returned HTTP 404."  # The cloud refuses the cancel.
    cancel(harness)  # The operator types CANCEL and presses the button.
    ap_id = child_id(harness, "ap")  # The access point child job.
    page = page_of(harness)  # The progress page after the refused cancel.
    assert items(page, f"org-cancel-outcome-cancelled-{ap_id}") == ["The portal canceled no device."]
    assert items(page, f"org-cancel-outcome-writing-{ap_id}") == [AP_ONE, AP_TWO]  # Each one can still write.
    assert text_of(page, f"org-cancel-outcome-status-{ap_id}") == "failed"  # The request failed.
    assert text_of(page, f"org-cancel-outcome-message-{ap_id}").startswith("The cloud returned HTTP 404.")


@pytest.mark.parametrize("body", [b"", b"bad json"], ids=["empty-body", "malformed-json"])
def test_a_damaged_cancel_body_sends_no_cancel_and_adds_no_panel(harness: CancelHarness, body: bytes) -> None:
    """An empty body or a body that is not JSON gets 400, and the page shows no cancel result."""
    path = f"/api/org-upgrades/{harness.operation_id}/cancel"  # The cancel route of the operation.
    answer = harness.client.post(path, data=body, content_type="application/json")  # A damaged script request.
    stored = harness.store.records[harness.operation_id]  # The durable operation after the request.
    assert (answer.status_code, answer.get_json()["error"]["code"]) == (400, "confirmation_required")
    assert harness.org.cancels == []  # No cancel call reached the cloud.
    assert all(child.get("cancellation") is None for child in stored["children"])  # No result is stored.
    assert OrgCancelOutcomes.rows(stored) == []  # The view builds no cancel result row.
    assert 'data-testid="org-cancel-outcome"' not in page_of(harness)  # The page shows no cancel result.
