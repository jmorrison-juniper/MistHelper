"""Contract tests for the pre-check gate of one multi-site upgrade.

Why:
    Issue #3243. The single-site confirm page stays locked until the site holds
    a verified pre-check capture, and the start route refuses a run without
    one. The multi-site mode had no such gate, so one confirmation could
    upgrade many sites with no baseline for a comparison. These tests drive the
    real Flask routes and the production aggregate plan, with stand-ins only at
    the cloud edge and at the capture store. No test opens a socket, and no
    test sends a firmware request.
"""

from __future__ import annotations

import re
import threading
from collections.abc import Iterator, Mapping
from copy import deepcopy
from dataclasses import asdict, dataclass, field
from threading import Lock
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.firmware.aggregate_upgrade_service import AggregateUpgradeService
from src.upgrade_portal.app.routes import capture, org_upgrade, select
from src.upgrade_portal.app.routes import upgrade as upgrade_routes
from src.upgrade_portal.runtime import identity, lock
from src.upgrade_portal.runtime.runs import RunRecordBuilder, RunSpec
from src.upgrade_portal.upgrade import options as option_rules
from tests.support.lock_store_double import FakeLockStore
from tests.support.org_cascade_seams import CascadeSeamStandIn
from tests.support.org_precheck_seams import PrecheckAdopterStandIn

OPERATOR_EMAIL = "org-precheck.operator@juniper.net"  # A reachable address, because a firmware write needs one.
OTHER_EMAIL = "second.operator@juniper.net"  # A second operator who holds a site.
CLOUD_ACCOUNT = "mist.account@juniper.net"  # The account label behind the signed cloud session.
SITE_TWO = "00000000-0000-0000-0000-0000000000cc"  # The second selected site of each test.
FOREIGN_SITE = "00000000-0000-0000-0000-0000000000dd"  # A site that the selection does not hold.
AP_ONE = "001122334455"  # The access point at the first site.
AP_TWO = "001122334466"  # The access point at the second site.
OPTIONS_API = "/api/org-upgrades/options"  # The save of the multi-site options.
CONFIRM_PAGE = "/upgrade/org/confirm"  # The typed confirmation page.
SUBMIT_API = "/api/org-upgrades"  # The confirmed submission.
OPTIONS_SESSION_KEY = "org_upgrade_options"  # The cookie key that holds the saved options.
PLAN_CHOICES = {"selected_types": ["ap"], "version_ap": "0.15.1", "strategy": "big_bang"}  # One family.
HINT = "The portal needs a saved pre-check capture for each site before an upgrade starts."  # FR-004.
EMPTY_NOTE = "The portal stored no pre-check capture for this operation."  # US4.


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


class AcceptingService(AggregateUpgradeService):
    """Keep the production plan build, accept each child job, and reach no cloud."""

    def __init__(self) -> None:
        """Start with no submission."""
        super().__init__()  # The production build needs its default collaborators.
        self.submits = 0  # A test proves that a refusal sent no child job.

    def status(self, cloud_session: Any, record: Any, store: Any) -> Any:
        """Return the stored record as it is."""
        del cloud_session, store  # The record already holds the cloud answers.
        return record  # No child read runs.

    def submit(self, cloud_session: Any, record: Any, store: Any, refresh_lock: Any) -> Any:
        """Accept every child job without a cloud write."""
        del cloud_session, refresh_lock  # The production service tests cover the claim and the refresh.
        self.submits += 1  # Count each submission that reached the cloud edge.
        for child in record["children"]:  # Each child reaches the stand-in cloud one time.
            child["status"] = "accepted"  # The cloud accepted the child job.
        record["state"] = "running"  # The operation now runs, so the site locks stay.
        store.write_run(record)  # Persist the accepted child jobs.
        return record  # The route opens the progress page.


@dataclass
class RecordingRunner:
    """Record each capture job that the route hands to the worker, and read nothing."""

    jobs: list[dict[str, Any]] = field(default_factory=list)  # One entry for each started capture.
    started: threading.Event = field(default_factory=threading.Event)  # Set when a worker ran.

    def __call__(self, job: dict[str, Any]) -> None:
        """Keep the fields of one job that hold no cloud session."""
        kept = {key: job[key] for key in ("capture_id", "run_id", "role", "site_id", "tier")}  # No token.
        self.jobs.append(kept)  # A test reads the job after the worker ran.
        self.started.set()  # The test waits for this event.


@dataclass
class PrecheckHarness:
    """Hold the signed client and each stand-in of one test."""

    client: FlaskClient  # The signed browser session.
    store: RecordStore  # The durable store of every operation.
    service: AcceptingService  # The aggregate service with the stand-in cloud edge.
    locks: FakeLockStore  # The site lock store.
    adopter: PrecheckAdopterStandIn  # The pre-check capture of each site.
    runner: RecordingRunner  # The capture worker seam.
    owner: identity.SessionOwner  # The signed operator and browser.
    org_id: str  # The selected organization.
    site_one: str  # The first selected site.


def inventory_row(mac: str) -> dict[str, str]:
    """Build one access point row in the shape of both production inventory reads."""
    row = {"mac": mac, "name": f"ap-{mac[-2:]}", "device_type": "ap", "model": "AP45", "version": "0.14.1"}
    return {**row, "type": "ap"}  # The raw inventory field of the target builder.


def option_builder(devices: Mapping[str, list[dict[str, str]]]) -> Any:
    """Return the stand-in of the site option mapper, with the production record shape."""

    def build(cloud_session: Any, org_id: str, site_id: str, body: Mapping[str, Any]) -> dict[str, Any]:
        """Build the targets and the options of one site without a cloud read."""
        del cloud_session, org_id  # The stand-in reads no inventory from the cloud.
        entries = option_rules.build_targets(devices[site_id], list(body["targets"]))  # One entry for each choice.
        return {"targets": entries, "options": asdict(option_rules.build_options(dict(body)))}  # Production shape.

    return build  # The route calls the mapper one time for each site.


@pytest.fixture
def harness(portal_app: Flask, fake_mist_api: Any, fake_org_id: str, fake_site_id: str) -> Iterator[PrecheckHarness]:
    """Return a signed client with two selected sites and no live service."""
    store, service, locks, runner = RecordStore(), AcceptingService(), FakeLockStore(), RecordingRunner()
    adopter = PrecheckAdopterStandIn((fake_site_id, SITE_TWO)).install(portal_app.config)  # Both sites hold one.
    devices = {fake_site_id: [inventory_row(AP_ONE)], SITE_TWO: [inventory_row(AP_TWO)]}  # One AP at each site.
    fake_mist_api.payloads["listOrgSites"] = [  # The organization holds both selected sites.
        {"id": fake_site_id, "name": "Test Site", "org_id": fake_org_id},
        {"id": SITE_TWO, "name": "Site Two", "org_id": fake_org_id},
    ]
    portal_app.config.update(  # Replace each cloud edge with a stand-in.
        {
            "WTF_CSRF_ENABLED": False,  # The contract drives the routes, not the form tokens.
            "MIST_READER": fake_mist_api.read,  # The site list reaches no cloud.
            "SITE_LOCK_READER": lambda org_id, site_ids: {site_id: None for site_id in site_ids},  # No holder.
            select.LOCK_CLIENT_KEY: locks,  # Every lock write stays in memory.
            capture.RUNNER_KEY: runner,  # No capture reads the cloud.
            "RUN_STORE": store,  # Every operation stays in memory.
            "AGGREGATE_UPGRADE_SERVICE": service,  # The production plan with no real cloud call.
            org_upgrade.DEVICE_VERSION_READER_CONFIG_KEY: lambda cloud_session, site_id: {},  # No stats read.
            org_upgrade.OPTIONS_VIEW_CONFIG_KEY: lambda session, org, site: {"targets": deepcopy(devices[site])},
            org_upgrade.OPTIONS_BUILDER_CONFIG_KEY: option_builder(devices),  # The save reaches no cloud.
            "MIST_SELF_READER": lambda cloud_session: {"email": CLOUD_ACCOUNT},  # No self read.
        }
    )
    CascadeSeamStandIn().install(portal_app.config)  # Issue #3245: no anchor read and no watch thread.
    owner = identity.build_owner(OPERATOR_EMAIL, identity.issue_browser_id())  # The signed operator.
    operator = identity.OperatorSession(  # The server-side record that the session guard reads.
        owner=owner,
        cloud_session=object(),
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
        selected_site_ids=(fake_site_id, SITE_TWO),
    )
    identity.SESSION_REGISTRY.register(operator)  # The session guard finds the operator record.
    try:  # Drop the operator record after the test, also after a failure.
        with portal_app.test_client() as client:  # Keep the signed session across the requests.
            client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)  # The browser identity.
            with client.session_transaction() as browser_session:  # Sign the multi-site scope.
                browser_session[identity.SESSION_OWNER_KEY] = owner.key  # The owner of each operation.
                browser_session["selected_org_id"] = fake_org_id  # The selected organization.
                browser_session["selected_upgrade_mode"] = "multi_site"  # The multi-site mode.
            yield PrecheckHarness(client, store, service, locks, adopter, runner, owner, fake_org_id, fake_site_id)
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)  # No later test finds this operator.


def error_code(answer: Any) -> str:
    """Return the error code of one refusal envelope."""
    body = answer.get_json() or {}  # Every refusal answers the one error envelope of the portal.
    return str(body.get("error", {}).get("code", ""))  # An absent code reads as empty text.


def error_message(answer: Any) -> str:
    """Return the message of one refusal envelope."""
    body = answer.get_json() or {}  # Every refusal answers the one error envelope of the portal.
    return str(body.get("error", {}).get("message", ""))  # An absent message reads as empty text.


def save_plan(harness: PrecheckHarness) -> str:
    """Save one plan of the access points of both sites, and return its operation identifier."""
    answer = harness.client.post(OPTIONS_API, json=PLAN_CHOICES)  # The options save.
    assert answer.status_code == 200, answer.get_json()  # A refused save stops the test with its reason.
    with harness.client.session_transaction() as browser_session:  # Read the signed cookie.
        return str(browser_session[OPTIONS_SESSION_KEY]["operation_id"])  # The durable identity of the plan.


def start_precheck(harness: PrecheckHarness, site_id: str, body: Mapping[str, Any] | None = None) -> Any:
    """Send one pre-check start of one site, and return the answer."""
    path = f"/api/org-upgrades/prechecks/{site_id}"  # The new endpoint of FR-009.
    return harness.client.post(path, json=dict(body if body is not None else {"tier": 2}))  # A script request.


def submit(harness: PrecheckHarness) -> Any:
    """Send the typed confirmation, and return the answer."""
    return harness.client.post(SUBMIT_API, json={"confirmation": "CONFIRM"})  # The confirmed submission.


def stored_lock(harness: PrecheckHarness, site_id: str) -> lock.LockRecord | None:
    """Return the lock that the store holds for one site, or None."""
    return lock.read_lock(harness.org_id, site_id, harness.locks)  # The real reader over the stand-in store.


def seed_lock(harness: PrecheckHarness, site_id: str, owner: identity.SessionOwner, run_id: str) -> lock.LockRecord:
    """Take one site lock through the production acquire rule, and return its record."""
    request = lock.LockRequest(harness.org_id, site_id, owner, run_id)  # The operator, the site, and the run.
    return lock.acquire_site_lock(request, harness.locks).record  # The stored record of the new lock.


def element(page: str, test_id: str) -> str:
    """Return the opening tag of one element of the page."""
    match = re.search(rf'<[^>]*data-testid="{re.escape(test_id)}"[^>]*>', page)  # The first tag with the ID.
    assert match is not None, f"The page shows no element with the identifier {test_id}."
    return match.group(0)  # The complete opening tag, with each attribute.


def text_of(page: str, test_id: str) -> str:
    """Return the text of one element of the page, without the markup of its children."""
    match = re.search(rf'data-testid="{re.escape(test_id)}"[^>]*>(.*?)</', page, re.DOTALL)  # The first text.
    assert match is not None, f"The page shows no element with the identifier {test_id}."
    return re.sub(r"<[^>]+>", "", match.group(1)).strip()  # The text without the indentation.


def section_text(page: str, test_id: str) -> str:
    """Return the complete text of one section of the page."""
    pattern = rf'<section[^>]*data-testid="{re.escape(test_id)}".*?</section>'  # The whole card.
    match = re.search(pattern, page, re.DOTALL)  # The card markup.
    assert match is not None, f"The page shows no section with the identifier {test_id}."
    return " ".join(re.sub(r"<[^>]+>", " ", match.group(0)).split())  # The text with single spaces.


def confirm_page(harness: PrecheckHarness) -> str:
    """Return the confirmation page of the saved plan."""
    answer = harness.client.get(CONFIRM_PAGE)  # The page view.
    assert answer.status_code == 200, answer.get_data(as_text=True)[:400]  # A refusal stops the test.
    return answer.get_data(as_text=True)  # The complete page.


def test_the_confirm_page_shows_one_row_for_each_site_and_locks_the_start(harness: PrecheckHarness) -> None:
    """FR-001 and FR-004: a site with no capture keeps the confirmation field disabled."""
    harness.adopter.forget(SITE_TWO)  # The second site holds no pre-check capture.
    save_plan(harness)  # The operator saved the plan.
    page = confirm_page(harness)  # The confirmation page.
    one, two = (f"org-upgrade-precheck-row-{site}" for site in (harness.site_one, SITE_TWO))  # The two rows.
    assert page.index(one) < page.index(two)  # The rows keep the order of the selection.
    assert 'data-ready="true"' in element(page, one) and 'data-ready="false"' in element(page, two)
    link = element(page, f"org-upgrade-precheck-capture-{harness.site_one}")  # The capture link of the first site.
    assert f'href="/captures/pre-{harness.site_one}"' in link  # FR-001: the identifier links to the capture.
    assert text_of(page, f"org-upgrade-precheck-capture-{SITE_TWO}") == "None saved"  # FR-001.
    assert text_of(page, f"org-upgrade-precheck-tier-{harness.site_one}") == "2"  # The tier of the capture.
    assert HINT in text_of(page, "org-upgrade-precheck-hint")  # FR-004: the hint names the cure.
    assert "disabled" in element(page, "org-upgrade-confirmation")  # FR-004: the field stays locked.
    assert "disabled" not in element(page, "org-upgrade-precheck-missing")  # FR-005: the button can run.


def test_the_confirm_page_opens_the_field_when_each_site_holds_a_capture(harness: PrecheckHarness) -> None:
    """FR-004 and FR-005: the gate opens, and the button for missing captures has no work."""
    save_plan(harness)  # Both sites hold a capture.
    page = confirm_page(harness)  # The confirmation page.
    assert "disabled" not in element(page, "org-upgrade-confirmation")  # The operator can type the word.
    assert "disabled" in element(page, "org-upgrade-precheck-missing")  # No site misses a capture.
    assert "disabled" not in element(page, "org-upgrade-precheck-all")  # US5: a new baseline stays possible.
    assert 'data-testid="org-upgrade-precheck-hint"' not in page  # No hint when the gate is open.
    assert '<option value="2" selected>' in page and '<option value="3">' in page  # FR-005: tier 2 is the default.


def test_the_start_refuses_a_site_without_a_capture_before_any_write(harness: PrecheckHarness) -> None:
    """FR-012 and US3: the refusal names the site and comes before any lock and any child job."""
    harness.adopter.forget(SITE_TWO)  # The second site holds no pre-check capture.
    operation_id = save_plan(harness)  # The operator saved the plan.
    answer = submit(harness)  # A script sends the start with no pre-check of the second site.
    assert answer.status_code == 409 and error_code(answer) == upgrade_routes.PRE_CAPTURE_MISSING_CODE
    assert error_message(answer).endswith("These sites hold no pre-check capture: Site Two.")  # Names the site.
    assert harness.service.submits == 0 and harness.locks.values == {}  # No child job and no site lock.
    record = harness.store.records[operation_id]  # The durable plan after the refusal.
    assert record["state"] == "planned" and "pre_captures" not in record  # The plan stays as it was.


def test_the_start_stores_the_capture_of_each_site(harness: PrecheckHarness) -> None:
    """FR-013: the operation record names the pre-check capture of each site, in the order of the selection."""
    operation_id = save_plan(harness)  # Both sites hold a capture.
    answer = submit(harness)  # The typed confirmation.
    assert answer.status_code == 200, answer.get_json()  # The submission starts.
    stored = harness.store.records[operation_id]["pre_captures"]  # The list of FR-013.
    assert stored == [  # One entry for each site, with the four fields.
        {"site_id": harness.site_one, "site_name": "Test Site", "capture_id": f"pre-{harness.site_one}", "tier": 2},
        {"site_id": SITE_TWO, "site_name": "Site Two", "capture_id": f"pre-{SITE_TWO}", "tier": 2},
    ]
    assert harness.service.submits == 1  # One submission reached the cloud edge.


def test_the_precheck_start_needs_saved_options(harness: PrecheckHarness) -> None:
    """FR-010 step 1: no saved options answers 400 before any lock."""
    answer = start_precheck(harness, harness.site_one)  # The operator saved no plan.
    assert answer.status_code == 400 and error_code(answer) == org_upgrade.OPTIONS_INVALID  # The first refusal.
    assert harness.locks.values == {} and harness.runner.jobs == []  # No lock and no capture.


def test_the_precheck_start_refuses_a_site_outside_the_selection(harness: PrecheckHarness) -> None:
    """FR-010 step 2: a site that the selection does not hold answers 404."""
    save_plan(harness)  # The operator saved the plan.
    answer = start_precheck(harness, FOREIGN_SITE)  # A hand-typed path.
    assert answer.status_code == 404 and error_code(answer) == capture.SITE_NOT_FOUND_CODE  # The same code.
    assert harness.locks.values == {} and harness.runner.jobs == []  # No lock and no capture.


def test_the_precheck_start_refuses_an_unknown_tier(harness: PrecheckHarness) -> None:
    """FR-010 step 3: a tier other than 2 and 3 answers 400."""
    save_plan(harness)  # The operator saved the plan.
    answer = start_precheck(harness, harness.site_one, {"tier": 5})  # A tier that the portal does not read.
    assert answer.status_code == 400 and error_code(answer) == capture.BAD_TIER_CODE  # The capture code.
    assert harness.locks.values == {} and harness.runner.jobs == []  # No lock and no capture.


def test_an_empty_body_starts_a_precheck_of_the_standard_tier(harness: PrecheckHarness) -> None:
    """FR-010 step 3: an empty body names no tier, so the start reads tier 2, as the capture page does."""
    save_plan(harness)  # The operator saved the plan.
    answer = harness.client.post(f"/api/org-upgrades/prechecks/{SITE_TWO}", data=b"")  # A post with no body.
    assert answer.status_code == 202, answer.get_json()  # An empty body is not a fault.
    assert harness.runner.started.wait(5)  # The worker received the job.
    assert harness.runner.jobs[0]["tier"] == 2  # contracts/http-api.md names tier 2 as the default.
    held = stored_lock(harness, SITE_TWO)  # The start takes the site lock as a start with a body does.
    assert held is not None and held.held_by(harness.owner) and held.run_id == ""  # FR-011: no run.


def test_a_bad_json_body_reads_as_an_empty_body(harness: PrecheckHarness) -> None:
    """FR-010 step 3: a body that raises JSONDecodeError in a parser reads as an empty body, never a fault page."""
    save_plan(harness)  # The operator saved the plan.
    path = f"/api/org-upgrades/prechecks/{SITE_TWO}"  # The endpoint of FR-009.
    answer = harness.client.post(path, data="{bad json", content_type="application/json")  # Broken JSON text.
    assert answer.status_code == 202, answer.get_data(as_text=True)  # The route answers with no fault page.
    assert harness.runner.started.wait(5)  # The worker received the job.
    assert harness.runner.jobs[0]["tier"] == 2  # The broken body names no tier, so the default applies.
    held = stored_lock(harness, SITE_TWO)  # The start takes the site lock as a start with a body does.
    assert held is not None and held.held_by(harness.owner) and held.run_id == ""  # FR-011: no run.


def test_the_precheck_start_takes_a_lock_with_no_run(harness: PrecheckHarness) -> None:
    """FR-009 and FR-011: the answer has the capture shape, and the lock names no run."""
    save_plan(harness)  # The operator saved the plan.
    answer = start_precheck(harness, SITE_TWO, {"tier": 3})  # A tier 3 pre-check of the second site.
    body = answer.get_json()  # The 202 answer.
    assert answer.status_code == 202 and set(body) == {"capture_id", "status_url"}  # No lock body.
    assert body["status_url"] == f"/api/captures/{body['capture_id']}/status"  # The capture status path.
    assert harness.runner.started.wait(5)  # The worker received the job.
    job = harness.runner.jobs[0]  # The one job of the start.
    assert (job["run_id"], job["role"], job["site_id"], job["tier"]) == ("", "pre", SITE_TWO, 3)
    held = stored_lock(harness, SITE_TWO)  # The lock of the second site.
    assert held is not None and held.held_by(harness.owner) and held.run_id == ""  # FR-011.
    with harness.client.session_transaction() as browser_session:  # The signed cookie.
        assert not any("lock" in str(key) for key in browser_session)  # FR-011: no session copy.


def test_a_second_precheck_keeps_the_lock_without_a_renewal(harness: PrecheckHarness) -> None:
    """FR-011: a second start keeps the stored lock exactly as it was."""
    save_plan(harness)  # The operator saved the plan.
    assert start_precheck(harness, harness.site_one).status_code == 202  # The first start takes the lock.
    before = dict(harness.locks.values)  # The stored lock after the first start.
    assert start_precheck(harness, harness.site_one).status_code == 202  # The second start of the same site.
    assert harness.locks.values == before  # The same token and the same heartbeat time.


def test_the_precheck_start_refuses_a_site_that_another_operator_holds(harness: PrecheckHarness) -> None:
    """FR-010 step 4: a site of another operator answers 409 site_locked."""
    save_plan(harness)  # The operator saved the plan.
    other = identity.build_owner(OTHER_EMAIL, identity.issue_browser_id())  # A second operator.
    seed_lock(harness, SITE_TWO, other, "")  # The second operator holds the site.
    answer = start_precheck(harness, SITE_TWO)  # The first operator asks for a pre-check.
    assert answer.status_code == 409 and error_code(answer) == capture.SITE_LOCKED_CODE  # The capture code.
    assert harness.runner.jobs == []  # No capture started.


def test_the_precheck_start_refuses_a_lock_of_another_run(harness: PrecheckHarness) -> None:
    """FR-010 step 5: a lock of the operator that names another run answers 409 site_lock_wrong_run."""
    save_plan(harness)  # The operator saved the plan.
    seed_lock(harness, SITE_TWO, harness.owner, "run-other")  # The operator holds the site for another run.
    answer = start_precheck(harness, SITE_TWO)  # The operator asks for a pre-check.
    assert answer.status_code == 409 and error_code(answer) == "site_lock_wrong_run"  # The start code.
    assert harness.runner.jobs == []  # No capture started.


def test_the_start_binds_the_precheck_lock_to_the_operation(harness: PrecheckHarness) -> None:
    """FR-014: the start binds the lock with no run and keeps its token."""
    operation_id = save_plan(harness)  # The operator saved the plan.
    assert start_precheck(harness, harness.site_one).status_code == 202  # The pre-check takes the lock.
    token = stored_lock(harness, harness.site_one)  # The lock with no run.
    answer = submit(harness)  # The typed confirmation.
    assert answer.status_code == 200, answer.get_json()  # The submission starts.
    bound = stored_lock(harness, harness.site_one)  # The lock after the start.
    assert token is not None and bound is not None and bound.lock_token == token.lock_token  # The same lock.
    assert bound.run_id == operation_id  # The lock now names the operation.
    stored = harness.store.records[operation_id]["site_locks"][harness.site_one]  # The durable lock copy.
    assert stored["run_id"] == operation_id  # The record names the same run.


def test_the_start_refuses_a_lock_of_the_operator_for_another_run(harness: PrecheckHarness) -> None:
    """FR-014: a lock of the operator that names another run still stops the start."""
    save_plan(harness)  # The operator saved the plan.
    seed_lock(harness, SITE_TWO, harness.owner, "run-other")  # The operator holds the site for another run.
    answer = submit(harness)  # The typed confirmation.
    assert answer.status_code == 409 and error_code(answer) == "site_lock_wrong_run"  # The start stops.
    assert harness.service.submits == 0  # No child job reached the cloud edge.


def test_the_progress_page_lists_the_stored_captures(harness: PrecheckHarness) -> None:
    """FR-015: the progress page and the poll show one link for each stored capture."""
    operation_id = save_plan(harness)  # Both sites hold a capture.
    assert submit(harness).status_code == 200  # The submission starts.
    page = harness.client.get(f"/upgrade/org/jobs/{operation_id}").get_data(as_text=True)  # The progress page.
    poll = harness.client.get(f"/api/org-upgrades/{operation_id}").get_json()  # The status poll.
    assert 'data-testid="org-upgrade-precheck-list"' in page  # The card of FR-015.
    for site_id in (harness.site_one, SITE_TWO):  # One link for each site.
        assert f'href="/captures/pre-{site_id}"' in element(page, f"org-upgrade-precheck-link-{site_id}")
    assert [row["capture_id"] for row in poll["prechecks"]] == [f"pre-{harness.site_one}", f"pre-{SITE_TWO}"]


def test_the_progress_page_of_an_earlier_operation_shows_the_note(harness: PrecheckHarness) -> None:
    """US4: an operation from an earlier release holds no list, and the card says so."""
    operation_id = save_plan(harness)  # The durable plan.
    record = harness.store.records[operation_id]  # The plan holds no pre-check list.
    harness.store.write_run({**record, "state": "running"})  # An operation that started before the gate.
    page = harness.client.get(f"/upgrade/org/jobs/{operation_id}").get_data(as_text=True)  # The progress page.
    assert EMPTY_NOTE in section_text(page, "org-upgrade-precheck-list")  # The text of US4.


def seed_single_site_run(harness: PrecheckHarness) -> str:
    """Store one single-site run that waits for its confirmation and holds no pre-check capture."""
    spec = RunSpec(harness.org_id, "Probe organization", SITE_TWO, "Site Two", OPERATOR_EMAIL, "browser-probe")
    record = RunRecordBuilder().build(spec)  # The record layer owns every field and every default.
    record["state"] = "awaiting_confirmation"  # The run waits for the typed word only.
    harness.store.write_run(record)  # The start route reads this record through the store seam.
    return str(record["run_id"])  # The path of the start carries this key.


def test_both_modes_refuse_a_start_without_a_capture_with_one_answer(harness: PrecheckHarness) -> None:
    """FR-012 parity: both modes answer the same status and the same code for a start with no capture."""
    harness.adopter.forget(SITE_TWO)  # The second site holds no pre-check capture.
    save_plan(harness)  # The multi-site plan of both sites.
    multi = submit(harness)  # The multi-site start.
    run_id = seed_single_site_run(harness)  # The single-site run of the same site.
    single = harness.client.post(f"/api/runs/{run_id}/start", json={"confirm": "CONFIRM"})  # The single start.
    assert multi.status_code == single.status_code == 409  # One status for one rule.
    assert error_code(multi) == error_code(single) == upgrade_routes.PRE_CAPTURE_MISSING_CODE  # One code.
    assert harness.service.submits == 0  # Neither mode sent a firmware request.
