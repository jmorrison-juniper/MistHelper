"""Contract tests of the later site checks after a lost page (issue #3439).

Why:
    Issue #3438 names a lost page of the site read in the site picker. Nine
    later steps read the site list again, and each step refused a site of a
    lost page as unknown. The operator then read the wrong cause and chose the
    sites again. These tests drive the real routes with a site read that loses
    page two. Each step must answer the status 503 with the code
    `site_list_incomplete`, and it must change no stored state. A whole read
    keeps the answer of today, and a site of a kept page still passes. No test
    opens a socket, and no test sends a firmware request.
"""

from __future__ import annotations

import html
import logging
import re
from collections.abc import Callable, Iterator
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.upgrade_portal.app.routes import capture, org_upgrade, select
from src.upgrade_portal.capture.devices import DeviceRead
from src.upgrade_portal.runtime import identity, lock
from tests.contract.upgrade_portal.test_org_child_controls_routes import (
    AP_ONE,
    AP_TWO,
    PLAN_CHOICES,
    RETRY_ID,
    SITE_TWO,
    SWITCH_ONE,
    SWITCH_TWO,
    ControlsHarness,
    ControlsService,
    RecordStore,
    SiteVersionReader,
    inventory_row,
    option_builder,
    settled_record,
)
from tests.contract.upgrade_portal.test_org_precheck_routes import RecordingRunner
from tests.support.lock_store_double import FakeLockStore
from tests.support.org_cascade_seams import CascadeSeamStandIn
from tests.support.org_precheck_seams import PrecheckAdopterStandIn

OPERATOR_EMAIL = "later-site-checks.operator@juniper.net"  # A reachable address, because a saved plan names it.
CLOUD_ACCOUNT = "mist.account@juniper.net"  # The account label behind the signed cloud session.
FOREIGN_SITE = "00000000-0000-0000-0000-0000000000dd"  # A site that no site list holds.
SITE_ONE_NAME = "Test Site"  # The site of page one.
SITE_TWO_NAME = "Site Two"  # The site of page two, which a lost page leaves out.

INCOMPLETE_CODE = "site_list_incomplete"  # FR-001: the error code of each refusal.
INCOMPLETE_MESSAGE = (  # FR-002: the refusal sentence of each later site check.
    "The portal did not read the complete site list, so it cannot check your site choice. Try again."
)
INCOMPLETE_TITLE = "The portal did not read the complete site list"  # FR-002: the heading of the error page.
UNAVAILABLE_STATUS = 503  # FR-001: the cloud read did not complete, and a later read can pass.
EXPECTED_ENVELOPE = (UNAVAILABLE_STATUS, INCOMPLETE_CODE, INCOMPLETE_MESSAGE)  # FR-001, FR-002, and FR-004.
OPTIONS_INVALID = (400, org_upgrade.OPTIONS_INVALID)  # The save refusal of a body that names no valid option.
JSON_TYPE = "application/json"  # The content type of a script post.
REDIRECT_STATUS = 303  # A refused picker post from a browser opens the picker with GET.
SITE_NOT_FOUND = (404, "site_not_found")  # FR-007: a whole list without the site, at a single-site check.
SITES_NOT_CHOSEN = (404, "sites_not_chosen")  # FR-007: a whole list without a selected site, at a plan step.

BROWSER_HEADERS = {"Accept": "text/html,application/xhtml+xml"}  # A person opens a page.
SCRIPT_HEADERS = {"X-Requested-With": "XMLHttpRequest"}  # The page script reads JSON.
PORTAL_ORIGIN = "http://localhost"  # The host of the Flask test client, for the link back of a form post.

SITE_PICKER = "/select/site"  # The site picker, and the multi-site forward post.
OPTIONS_PAGE = "/upgrade/org/options"  # The multi-site options page.
OPTIONS_API = "/api/org-upgrades/options"  # The save of the multi-site options.
CONFIRM_PAGE = "/upgrade/org/confirm"  # The typed confirmation page.
OPTIONS_SESSION_KEY = "org_upgrade_options"  # The cookie key that holds the saved options.
RETRY_SESSION_KEY = "org_upgrade_retry"  # The cookie key that holds the retry reference.
SELECTED_SITE_KEY = "selected_site_id"  # The cookie key that holds the single-site pick.
SINGLE_SITE_MODE = "single_site"  # One site uses the current workflow.
MULTI_SITE_MODE = "multi_site"  # Many sites use the organization workflow.

SITE_READ = "listOrgSites"  # The site read that can lose a page.
COUNT_READ = "listOrgSiteStats"  # The device count read of the site picker.
WHOLE, LOST, FAILED = "whole", "lost", "failed"  # The three answers of the site read stand-in.
LOST_REASON = {"section": SITE_READ, "reason": "page_count_mismatch", "http_status": 503}  # Page two is lost.
FAILED_REASON = {"section": SITE_READ, "reason": "cloud_error_status", "http_status": 503}  # Page one failed.
LEGACY_BODY = {  # An older access point request, with no `selected_types` field.
    "version": "0.14.29411",
    "strategy": "canary",
    "canary_phases": "10,100",
    "max_failure_percentage": "5",
}


class SiteReadStandIn:
    """Answer the site read whole, with a lost page two, or with a failed first page.

    Why:
        The real reader walks each page. A lost page keeps the rows of the pages
        before it and adds one partial reason (issue #3438). The stand-in gives
        the same `DeviceRead` shape, so each check reads the real completeness
        flag. Each other read goes to the shared stub, which records each call.
    """

    def __init__(self, api: Any, kept_ids: tuple[str, ...]) -> None:
        """Keep the shared stub and the sites of page one.

        Args:
            api: The shared stub of the cloud reads.
            kept_ids: The sites of page one, which a lost page keeps.
        """
        self.api = api  # The shared stub answers each read and records each call.
        self.kept_ids = kept_ids  # A lost page keeps these sites only.
        self.mode = WHOLE  # A test sets LOST or FAILED before the step.

    def __call__(self, name: str, **parameters: Any) -> Any:
        """Answer one read in the current mode.

        Args:
            name: The read name.
            **parameters: The call parameters.

        Returns:
            The plain list of the stub, or a site read that lost data.
        """
        answer = self.api.read(name, **parameters)  # The stub records the call in each mode (FR-010).
        if name != SITE_READ or self.mode == WHOLE:  # Only the site read loses data.
            return answer  # The plain list of the stub.
        if self.mode == FAILED:  # The first page failed, so the read holds no row.
            return DeviceRead(name, [], [dict(FAILED_REASON)])  # No row and one partial reason.
        kept = [dict(row) for row in answer if str(row.get("id", "")) in self.kept_ids]  # The rows of page one.
        return DeviceRead(name, kept, [dict(LOST_REASON)])  # The kept rows and the reason of the lost page.


@dataclass
class LaterCheckHarness:
    """Hold the signed client and each stand-in of one test."""

    controls: ControlsHarness  # The signed client, the store, the locks, and the operator record.
    sites: SiteReadStandIn  # The site read, whole or with a lost page.
    runner: RecordingRunner  # The capture worker seam. A refusal starts no job.
    api: Any  # The shared stub, which records each cloud read.


def install_seams(app: Flask, sites: SiteReadStandIn, runner: RecordingRunner, parts: tuple[Any, ...]) -> None:
    """Replace each cloud edge and each store of the portal with a stand-in.

    Args:
        app: The portal application.
        sites: The site read stand-in.
        runner: The capture worker stand-in.
        parts: The record store, the version reader, the lock store, and the first site.
    """
    store, reader, locks, site_one = parts  # One name for each part.
    devices = {  # One access point and one switch at each site.
        site_one: [inventory_row(AP_ONE), inventory_row(SWITCH_ONE)],
        SITE_TWO: [inventory_row(AP_TWO), inventory_row(SWITCH_TWO)],
    }
    app.config.update(  # Replace each cloud edge with a stand-in.
        {
            "WTF_CSRF_ENABLED": False,  # The contract drives the routes, not the form tokens.
            "MIST_READER": sites,  # The site read loses page two on request.
            "SITE_LOCK_READER": lambda org_id, site_ids: {site_id: None for site_id in site_ids},  # No holder.
            select.LOCK_CLIENT_KEY: locks,  # Every lock write stays in memory.
            capture.RUNNER_KEY: runner,  # No capture reads the cloud.
            "RUN_STORE": store,  # Every operation stays in memory.
            "AGGREGATE_UPGRADE_SERVICE": ControlsService(),  # The production build with no cloud call.
            org_upgrade.DEVICE_VERSION_READER_CONFIG_KEY: reader,  # No stats read reaches the cloud.
            org_upgrade.OPTIONS_VIEW_CONFIG_KEY: lambda session, org, site: {"targets": deepcopy(devices[site])},
            org_upgrade.OPTIONS_BUILDER_CONFIG_KEY: option_builder(devices),  # The save reaches no cloud.
            "MIST_SELF_READER": lambda cloud_session: {"email": CLOUD_ACCOUNT},  # No self read.
        }
    )
    CascadeSeamStandIn().install(app.config)  # Issue #3245: no anchor read and no watch thread.
    PrecheckAdopterStandIn((site_one, SITE_TWO)).install(app.config)  # Issue #3243: each site holds a pre-check.


def register_operator(site_ids: tuple[str, ...]) -> identity.OperatorSession:
    """Register one signed operator with a selected site set.

    Args:
        site_ids: The selected sites, in the order of the selection.

    Returns:
        The server record of the operator.
    """
    owner = identity.build_owner(OPERATOR_EMAIL, identity.issue_browser_id())  # The operator and a new browser.
    operator = identity.OperatorSession(  # The server record that the session guard reads.
        owner=owner,
        cloud_session=object(),  # A plain object states no scope, so every organization passes.
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
        selected_site_ids=site_ids,  # The multi-site selection stays in the server record.
    )
    identity.SESSION_REGISTRY.register(operator)  # The session guard admits a registered owner only.
    return operator  # The test reads and changes the selection through this record.


def sign_in(client: FlaskClient, operator: identity.OperatorSession, org_id: str) -> None:
    """Sign the browser session of one client with the multi-site scope.

    Args:
        client: The test client.
        operator: The registered operator.
        org_id: The selected organization.
    """
    client.set_cookie(identity.BROWSER_ID_COOKIE, operator.owner.browser_id)  # The browser half of the pair.
    with client.session_transaction() as browser_session:  # The signed half of the pair.
        browser_session[identity.SESSION_OWNER_KEY] = operator.owner.key  # The owner of each operation.
        browser_session["selected_org_id"] = org_id  # The selected organization.
        browser_session["selected_upgrade_mode"] = MULTI_SITE_MODE  # The multi-site mode.


@pytest.fixture
def harness(portal_app: Flask, fake_mist_api: Any, fake_org_id: str, fake_site_id: str) -> Iterator[LaterCheckHarness]:
    """Return a signed multi-site client with two selected sites and no live service."""
    fake_mist_api.payloads[SITE_READ] = [  # Page one holds the first site, and page two holds the second.
        {"id": fake_site_id, "name": SITE_ONE_NAME, "org_id": fake_org_id},
        {"id": SITE_TWO, "name": SITE_TWO_NAME, "org_id": fake_org_id},
    ]
    sites, runner = SiteReadStandIn(fake_mist_api, (fake_site_id,)), RecordingRunner()  # The two new seams.
    stores = (RecordStore(), SiteVersionReader(), FakeLockStore())  # The store, the version read, and the locks.
    install_seams(portal_app, sites, runner, (*stores, fake_site_id))  # No live service.
    operator = register_operator((fake_site_id, SITE_TWO))  # The operator selected both sites.
    try:  # Drop the operator record after the test, also after a failure.
        with portal_app.test_client() as client:  # Keep the signed session across the requests.
            sign_in(client, operator, fake_org_id)  # The multi-site scope.
            controls = ControlsHarness(client, *stores, operator, fake_org_id, fake_site_id)  # The shared handles.
            yield LaterCheckHarness(controls, sites, runner, fake_mist_api)
    finally:
        identity.SESSION_REGISTRY.drop(operator.owner.key)  # No later test finds this operator.


def use_mode(harness: LaterCheckHarness, mode: str) -> None:
    """Store one operation mode in the signed session.

    Args:
        harness: The test harness.
        mode: The single-site mode or the multi-site mode.
    """
    with harness.controls.client.session_transaction() as browser_session:  # The signed cookie.
        browser_session["selected_upgrade_mode"] = mode  # The picker stores the mode the same way.


def browser_value(harness: LaterCheckHarness, key: str) -> Any:
    """Return one value of the signed browser session, or None.

    Args:
        harness: The test harness.
        key: The session key.

    Returns:
        A detached copy of the value.
    """
    with harness.controls.client.session_transaction() as browser_session:  # Read the signed cookie.
        return deepcopy(browser_session.get(key))  # Detach the value for the assertions.


def save_plan(harness: LaterCheckHarness) -> str:
    """Save one plan of every selected device during a whole read, and return its operation identifier.

    Args:
        harness: The test harness.

    Returns:
        The durable identity of the saved plan.
    """
    answer = harness.controls.client.post(OPTIONS_API, json=PLAN_CHOICES, headers=SCRIPT_HEADERS)  # The save.
    assert answer.status_code == 200, answer.get_json()  # A refused save stops the test with its reason.
    options = browser_value(harness, OPTIONS_SESSION_KEY) or {}  # The saved options of the session.
    return str(options.get("operation_id", ""))  # The durable identity of the plan.


def stored_lock(harness: LaterCheckHarness, site_id: str) -> lock.LockRecord | None:
    """Return the lock that the store holds for one site, or None.

    Args:
        harness: The test harness.
        site_id: The site of the lock.

    Returns:
        The stored lock record, or None for a free site.
    """
    return lock.read_lock(harness.controls.org_id, site_id, harness.controls.locks)  # The real reader.


def error_code(answer: Any) -> str:
    """Return the error code of one refusal envelope.

    Args:
        answer: The test response.

    Returns:
        The code, or an empty string.
    """
    body = answer.get_json(silent=True) or {}  # A page answer holds no JSON body.
    return str(body.get("error", {}).get("code", ""))  # An absent code reads as empty text.


def text_of(page: str, test_id: str) -> str:
    """Return the plain text of one element of a page.

    Args:
        page: The page text.
        test_id: The test identifier of the element.

    Returns:
        The text with collapsed white space.
    """
    found = re.search(rf'data-testid="{re.escape(test_id)}"[^>]*>(.*?)</', page, re.DOTALL)  # The first text.
    assert found is not None, f"The page shows no element with the identifier {test_id}."
    return " ".join(html.unescape(found.group(1)).split())  # Collapse the wrapped text.


def assert_error_page(answer: Any, back_path: str | None) -> None:
    """Check the shared error page of FR-003.

    Args:
        answer: The test response.
        back_path: The expected link back to the form, or None for no link back.
    """
    page = answer.get_data(as_text=True)  # The rendered page.
    assert answer.status_code == UNAVAILABLE_STATUS, page[:400]  # FR-001: the status 503.
    assert answer.mimetype == "text/html"  # A person reads a page, not an envelope.
    assert text_of(page, "error-title") == INCOMPLETE_TITLE  # FR-002: the heading.
    assert text_of(page, "error-message") == INCOMPLETE_MESSAGE  # FR-002: the sentence.
    assert (text_of(page, "error-status-code"), text_of(page, "error-code")) == ("503", INCOMPLETE_CODE)  # FR-003.
    assert 'data-testid="error-site-list-link"' in page  # FR-003: the link to the site list.
    back_link = re.search(r'href="([^"]*)" data-testid="error-back-link"', page)  # D7: the link back.
    assert (back_link.group(1) if back_link else None) == back_path  # A page request gets no link back.


def envelope_of(answer: Any) -> tuple[int, str, str]:
    """Return the status, the code, and the sentence of one answer.

    Why:
        One value holds the whole envelope, so a test compares it with
        `EXPECTED_ENVELOPE` in one assert. A page answer holds no JSON body,
        so its code and its sentence read as empty text.

    Args:
        answer: The test response.

    Returns:
        The status, the error code, and the error sentence.
    """
    error = (answer.get_json(silent=True) or {}).get("error", {})  # The error part of the envelope.
    return answer.status_code, str(error.get("code", "")), str(error.get("message", ""))  # One value.


def assert_envelope(answer: Any) -> None:
    """Check the error envelope of FR-004.

    Args:
        answer: The test response.
    """
    assert envelope_of(answer) == EXPECTED_ENVELOPE, answer.get_data(as_text=True)[:400]  # FR-001 and FR-004.


def caution_messages(page: str) -> list[str]:
    """Return each Caution message of the shared message region.

    Args:
        page: The page text.

    Returns:
        The text of each flashed Caution message, in page order.
    """
    found = re.findall(r'<div class="flash-item flash-warning">(.*?)</div>', page, re.DOTALL)  # Flashed only.
    return [" ".join(html.unescape(text).split()) for text in found]  # Collapse the wrapped text.


# ---------------------------------------------------------------------------
# The nine steps, as a script sends each one.
# ---------------------------------------------------------------------------


def no_preparation(harness: LaterCheckHarness) -> None:
    """Prepare nothing, because the step needs no saved state.

    Args:
        harness: The test harness.
    """
    del harness  # The signed session already holds the scope.


def write_settled_operation(harness: LaterCheckHarness) -> None:
    """Write one settled operation whose retry holds both sites.

    Args:
        harness: The test harness.
    """
    harness.controls.store.write_run(settled_record(harness.controls))  # An access point failed at each site.


@dataclass(frozen=True)
class Step:
    """One later site check, as a script reaches it.

    Attributes:
        mode: The operation mode of the step.
        prepare: The saved state that the step needs, made during a whole read.
        method: The HTTP method of the step.
        path: The request path. `{site}` names the site of page two.
        reads: The cloud reads of the step during a lost page (FR-010).
    """

    mode: str
    prepare: Callable[[LaterCheckHarness], object]
    method: str
    path: str
    reads: tuple[str, ...]

    def send(self, harness: LaterCheckHarness) -> Any:
        """Send the step as a script request.

        Args:
            harness: The test harness.

        Returns:
            The test response.
        """
        path = self.path.format(site=SITE_TWO)  # The step names the site of page two.
        body = {"site_ids": [harness.controls.site_one, SITE_TWO]} if path == SITE_PICKER else {"tier": 2}
        if path == OPTIONS_API:  # The save sends the choices of the plan.
            body = dict(PLAN_CHOICES)  # A plan of the access points and the switches of both sites.
        if self.method == "GET":  # A page read carries no body.
            return harness.controls.client.get(path, headers=SCRIPT_HEADERS)
        return harness.controls.client.post(path, json=body, headers=SCRIPT_HEADERS)  # A script post.


BOTH_READS = (SITE_READ, COUNT_READ)  # The site rows read both lists.
STEPS = {  # The nine steps of the issue, in the order of the issue table.
    "site_choice": Step(MULTI_SITE_MODE, no_preparation, "POST", SITE_PICKER, BOTH_READS),
    "inventory_page": Step(SINGLE_SITE_MODE, no_preparation, "GET", "/select/site/{site}", (SITE_READ,)),
    "inventory_answer": Step(SINGLE_SITE_MODE, no_preparation, "GET", "/api/sites/{site}/inventory", (SITE_READ,)),
    "capture_start": Step(SINGLE_SITE_MODE, no_preparation, "POST", "/api/sites/{site}/captures", (SITE_READ,)),
    "precheck_start": Step(MULTI_SITE_MODE, save_plan, "POST", "/api/org-upgrades/prechecks/{site}", (SITE_READ,)),
    "options_page": Step(MULTI_SITE_MODE, no_preparation, "GET", OPTIONS_PAGE, BOTH_READS),
    "options_save": Step(MULTI_SITE_MODE, no_preparation, "POST", OPTIONS_API, BOTH_READS),
    "confirm_page": Step(MULTI_SITE_MODE, save_plan, "GET", CONFIRM_PAGE, BOTH_READS),
    "retry": Step(MULTI_SITE_MODE, write_settled_operation, "POST", f"/api/org-upgrades/{RETRY_ID}/retry", BOTH_READS),
}


def run_step(harness: LaterCheckHarness, step: Step, mode: str) -> Any:
    """Prepare one step during a whole read, then send it during the named read.

    Args:
        harness: The test harness.
        step: The step.
        mode: The answer of the site read during the step.

    Returns:
        The test response.
    """
    use_mode(harness, step.mode)  # The operation mode of the step.
    step.prepare(harness)  # The saved state, made during a whole read.
    harness.api.calls.clear()  # Count only the reads of the step itself.
    harness.sites.mode = mode  # The later site read loses page two, or fails at page one.
    return step.send(harness)  # The script request of the step.


@pytest.mark.parametrize("name", list(STEPS))
def test_each_step_answers_a_script_with_the_503_envelope(harness: LaterCheckHarness, name: str) -> None:
    """SC-002 and FR-004: each step answers 503 for a site of a lost page, and never "no such site"."""
    answer = run_step(harness, STEPS[name], LOST)  # The site of page two, while page two is lost.
    assert envelope_of(answer) == EXPECTED_ENVELOPE, answer.get_data(as_text=True)[:400]  # The code and the sentence.


@pytest.mark.parametrize("name", list(STEPS))
def test_each_step_makes_the_reads_of_today(harness: LaterCheckHarness, name: str) -> None:
    """FR-010 and SC-005: the refusal adds no cloud read. The test passes on both code versions."""
    run_step(harness, STEPS[name], LOST)  # The refused step.
    assert tuple(read for read, _ in harness.api.calls) == STEPS[name].reads  # The same reads, in the same order.


# ---------------------------------------------------------------------------
# User Story 1: the single-site steps.
# ---------------------------------------------------------------------------


def test_the_inventory_page_shows_the_error_page_with_no_link_back(harness: LaterCheckHarness) -> None:
    """US1 scenario 1, FR-003, and D7: a person reads the error page, and the page stores no site pick."""
    use_mode(harness, SINGLE_SITE_MODE)  # The single-site mode.
    harness.sites.mode = LOST  # The later site read loses page two.
    answer = harness.controls.client.get(f"{SITE_PICKER}/{SITE_TWO}", headers=BROWSER_HEADERS)  # Open the site.
    assert_error_page(answer, back_path=None)  # A reload repeats the check, so the page holds no link back.
    assert browser_value(harness, SELECTED_SITE_KEY) is None  # FR-008: the portal stores no site pick.


def test_the_capture_start_starts_no_capture_and_takes_no_lock(
    harness: LaterCheckHarness, caplog: pytest.LogCaptureFixture
) -> None:
    """US1 scenario 3, FR-008, and FR-011: a refused capture start changes no state, and the log names a count."""
    use_mode(harness, SINGLE_SITE_MODE)  # The single-site mode.
    harness.sites.mode = LOST  # The later site read loses page two.
    caplog.set_level(logging.WARNING, logger=select.__name__)  # The refusal warning of the site check.
    path = f"/api/sites/{SITE_TWO}/captures"  # The capture start of the site of page two.
    answer = harness.controls.client.post(path, json={"tier": 2}, headers=SCRIPT_HEADERS)  # Start a capture.
    assert_envelope(answer)  # The 503 envelope.
    assert harness.runner.jobs == []  # No capture starts.
    assert stored_lock(harness, SITE_TWO) is None  # The portal takes no site lock.
    warnings = [record.getMessage() for record in caplog.records if record.name == select.__name__]  # FR-011.
    assert any("1 named site(s) are not in the list" in message for message in warnings), warnings


def test_a_failed_first_page_refuses_a_site_of_page_one_with_503(harness: LaterCheckHarness) -> None:
    """Edge case: a failed first page holds no site, so the portal cannot prove that any site exists."""
    use_mode(harness, SINGLE_SITE_MODE)  # The single-site mode.
    harness.sites.mode = FAILED  # The first page of the later site read fails.
    path = f"/api/sites/{harness.controls.site_one}/inventory"  # A site of page one.
    answer = harness.controls.client.get(path, headers=SCRIPT_HEADERS)  # The inventory answer of that site.
    assert envelope_of(answer) == EXPECTED_ENVELOPE, answer.get_data(as_text=True)[:400]  # The 503 envelope.


def test_a_site_of_a_kept_page_passes_each_single_site_step(harness: LaterCheckHarness) -> None:
    """US1 scenario 4 and FR-006: a site of page one still opens and starts a capture after a lost page."""
    use_mode(harness, SINGLE_SITE_MODE)  # The single-site mode.
    harness.sites.mode = LOST  # The later site read loses page two.
    client, site_one = harness.controls.client, harness.controls.site_one  # The site of page one.
    page = client.get(f"{SITE_PICKER}/{site_one}", headers=BROWSER_HEADERS)  # Open the site.
    assert page.status_code == 200, page.get_data(as_text=True)[:400]  # The device table opens.
    answer = client.get(f"/api/sites/{site_one}/inventory", headers=SCRIPT_HEADERS)  # The inventory answer.
    assert answer.status_code == 200, answer.get_json()  # The device list answers.
    started = client.post(f"/api/sites/{site_one}/captures", json={"tier": 2}, headers=SCRIPT_HEADERS)
    assert started.status_code == 202, started.get_json()  # The capture starts.
    assert harness.runner.started.wait(timeout=5)  # The worker thread received the job.
    assert [job["site_id"] for job in harness.runner.jobs] == [site_one]  # One capture of the site of page one.


def test_a_whole_list_keeps_the_404_answers_of_the_single_site_steps(harness: LaterCheckHarness) -> None:
    """FR-007: a whole list proves that the organization does not hold the site, so each answer stays."""
    use_mode(harness, SINGLE_SITE_MODE)  # The single-site mode, with a whole site read.
    client = harness.controls.client  # The signed client.
    page = client.get(f"{SITE_PICKER}/{FOREIGN_SITE}", headers=BROWSER_HEADERS)  # A site of no list.
    answer = client.get(f"/api/sites/{FOREIGN_SITE}/inventory", headers=SCRIPT_HEADERS)  # The inventory answer.
    started = client.post(f"/api/sites/{FOREIGN_SITE}/captures", json={"tier": 2}, headers=SCRIPT_HEADERS)
    assert page.status_code == 404  # The empty site picker of today.
    assert (answer.status_code, error_code(answer)) == SITE_NOT_FOUND  # The contract answer of today.
    assert (started.status_code, error_code(started)) == SITE_NOT_FOUND  # The contract answer of today.


def test_a_whole_read_opens_the_site_after_the_refusal(harness: LaterCheckHarness) -> None:
    """US1 scenario 5 and SC-006: one reload after a whole read opens the site and stores the pick."""
    use_mode(harness, SINGLE_SITE_MODE)  # The single-site mode.
    harness.sites.mode = LOST  # The first attempt meets a lost page.
    refused = harness.controls.client.get(f"{SITE_PICKER}/{SITE_TWO}", headers=BROWSER_HEADERS)  # The refusal.
    harness.sites.mode = WHOLE  # The reload reads the whole list.
    opened = harness.controls.client.get(f"{SITE_PICKER}/{SITE_TWO}", headers=BROWSER_HEADERS)  # The reload.
    assert (refused.status_code, opened.status_code) == (UNAVAILABLE_STATUS, 200)  # The reload recovers.
    assert browser_value(harness, SELECTED_SITE_KEY) == SITE_TWO  # The check passed, so the pick is stored.


# ---------------------------------------------------------------------------
# User Story 2: the multi-site site choice.
# ---------------------------------------------------------------------------


def test_the_site_choice_returns_a_browser_to_the_picker_with_a_caution(harness: LaterCheckHarness) -> None:
    """US2 scenarios 1 and 4, and FR-005: the picker shows the sentence, and the stored choice stays."""
    site_one = harness.controls.site_one  # The site of page one.
    harness.controls.operator.selected_site_ids = (site_one,)  # The stored choice before the post.
    harness.sites.mode = LOST  # The later site read loses page two.
    form = {"site_ids": [site_one, SITE_TWO]}  # One site of page one and one site of page two.
    answer = harness.controls.client.post(SITE_PICKER, data=form, headers=BROWSER_HEADERS)  # The forward press.
    assert (answer.status_code, answer.headers.get("Location")) == (REDIRECT_STATUS, SITE_PICKER)  # The picker.
    picker = harness.controls.client.get(SITE_PICKER, headers=BROWSER_HEADERS).get_data(as_text=True)
    assert caution_messages(picker) == [INCOMPLETE_MESSAGE]  # One Caution message with the sentence.
    assert harness.controls.operator.selected_site_ids == (site_one,)  # FR-008: the stored choice stays.


def test_a_choice_of_kept_sites_moves_forward_after_a_lost_page(harness: LaterCheckHarness) -> None:
    """US2 scenario 3 and FR-006: a choice of sites of page one opens the options page."""
    harness.sites.mode = LOST  # The later site read loses page two.
    body = {"site_ids": [harness.controls.site_one]}  # A site of page one only.
    answer = harness.controls.client.post(SITE_PICKER, json=body, headers=SCRIPT_HEADERS)  # The script post.
    assert (answer.status_code, answer.get_json()) == (200, {"next": OPTIONS_PAGE})  # The options page opens.


def test_a_whole_list_keeps_the_site_not_found_answer_of_the_choice(harness: LaterCheckHarness) -> None:
    """FR-007: a whole list without a chosen site keeps the 404 answer of today."""
    body = {"site_ids": [harness.controls.site_one, FOREIGN_SITE]}  # A site of no list.
    answer = harness.controls.client.post(SITE_PICKER, json=body, headers=SCRIPT_HEADERS)  # The script post.
    assert (answer.status_code, error_code(answer)) == SITE_NOT_FOUND  # The contract answer of today.


# ---------------------------------------------------------------------------
# User Story 3: the multi-site plan steps.
# ---------------------------------------------------------------------------


def test_the_options_page_shows_the_error_page_with_no_link_back(harness: LaterCheckHarness) -> None:
    """US3 scenario 1 and FR-003: a person reads the error page when the options page opens."""
    before = harness.controls.operator.selected_site_ids  # The selection before the refusal.
    harness.sites.mode = LOST  # The later site read loses page two.
    assert_error_page(harness.controls.client.get(OPTIONS_PAGE, headers=BROWSER_HEADERS), back_path=None)
    assert harness.controls.operator.selected_site_ids == before  # FR-008: the refusal keeps the selection.


def test_the_options_save_stores_no_plan_and_no_saved_options(harness: LaterCheckHarness) -> None:
    """US3 scenario 2 and FR-008: a refused save stores no plan and no saved options."""
    harness.sites.mode = LOST  # The later site read loses page two.
    answer = harness.controls.client.post(OPTIONS_API, json=PLAN_CHOICES, headers=SCRIPT_HEADERS)  # The save.
    assert_envelope(answer)  # The page script shows the sentence in the message region.
    assert harness.controls.store.records == {}  # No plan exists.
    assert browser_value(harness, OPTIONS_SESSION_KEY) is None  # No saved options.


def test_a_browser_form_save_links_back_to_the_options_page(harness: LaterCheckHarness) -> None:
    """FR-003 and D7: a refused form post from a browser links back to the form."""
    harness.sites.mode = LOST  # The later site read loses page two.
    headers = {**BROWSER_HEADERS, "Referer": f"{PORTAL_ORIGIN}{OPTIONS_PAGE}"}  # The browser names the form.
    answer = harness.controls.client.post(OPTIONS_API, data=dict(PLAN_CHOICES), headers=headers)  # A form post.
    assert_error_page(answer, back_path=OPTIONS_PAGE)  # The link back opens the options page again.
    assert harness.controls.store.records == {}  # FR-008: no plan exists.


def test_the_confirm_page_keeps_the_saved_options_for_a_later_read(harness: LaterCheckHarness) -> None:
    """US3 scenarios 3 and 6: the confirm page refuses, the saved options stay, and a whole read opens it."""
    operation_id = save_plan(harness)  # The operator saved the plan during a whole read.
    harness.sites.mode = LOST  # The later site read loses page two.
    refused = harness.controls.client.get(CONFIRM_PAGE, headers=BROWSER_HEADERS)  # Open the confirm page.
    assert_error_page(refused, back_path=None)  # A reload repeats the check.
    assert str((browser_value(harness, OPTIONS_SESSION_KEY) or {}).get("operation_id")) == operation_id  # Kept.
    harness.sites.mode = WHOLE  # The reload reads the whole list.
    reopened = harness.controls.client.get(CONFIRM_PAGE, headers=BROWSER_HEADERS)  # The reload.
    assert reopened.status_code == 200, reopened.get_data(as_text=True)[:400]  # SC-006: one reload recovers.


def test_the_precheck_start_starts_no_capture_and_takes_no_lock(harness: LaterCheckHarness) -> None:
    """US3 scenario 4 and FR-008: a refused pre-check start changes no state."""
    save_plan(harness)  # The operator saved the plan during a whole read.
    harness.sites.mode = LOST  # The later site read loses page two.
    path = f"/api/org-upgrades/prechecks/{SITE_TWO}"  # The pre-check of the site of page two.
    answer = harness.controls.client.post(path, json={"tier": 2}, headers=SCRIPT_HEADERS)  # The card starts it.
    assert_envelope(answer)  # The card shows the sentence in its error region.
    assert harness.runner.jobs == []  # No capture starts.
    assert stored_lock(harness, SITE_TWO) is None  # The portal takes no site lock.


def test_the_retry_selects_no_retry_site(harness: LaterCheckHarness) -> None:
    """US3 scenario 5 and FR-008: a refused retry stores no retry reference and keeps the selection."""
    write_settled_operation(harness)  # A settled operation whose retry holds both sites.
    before = harness.controls.operator.selected_site_ids  # The selection before the retry.
    harness.sites.mode = LOST  # The later site read loses page two.
    path = f"/api/org-upgrades/{RETRY_ID}/retry"  # The retry button of the progress page.
    answer = harness.controls.client.post(path, json={}, headers=SCRIPT_HEADERS)  # The retry.
    assert_envelope(answer)  # The 503 envelope.
    assert browser_value(harness, RETRY_SESSION_KEY) is None  # No retry reference.
    assert harness.controls.operator.selected_site_ids == before  # No retry site is selected.


def test_a_plan_of_kept_sites_passes_each_plan_step_after_a_lost_page(harness: LaterCheckHarness) -> None:
    """FR-006: a plan that holds only a site of page one passes each multi-site step."""
    site_one = harness.controls.site_one  # The site of page one.
    harness.controls.operator.selected_site_ids = (site_one,)  # The operator selected one site of page one.
    harness.sites.mode = LOST  # The later site read loses page two.
    client = harness.controls.client  # The signed client.
    assert client.get(OPTIONS_PAGE, headers=BROWSER_HEADERS).status_code == 200  # The options page opens.
    save_plan(harness)  # The save passes.
    assert client.get(CONFIRM_PAGE, headers=BROWSER_HEADERS).status_code == 200  # The confirm page opens.
    started = client.post(f"/api/org-upgrades/prechecks/{site_one}", json={"tier": 2}, headers=SCRIPT_HEADERS)
    assert started.status_code == 202, started.get_json()  # The pre-check capture starts.


def test_a_whole_list_keeps_the_answers_of_today_for_a_site_that_left(harness: LaterCheckHarness) -> None:
    """FR-007: after a site leaves the organization, each plan step keeps its answer of today."""
    save_plan(harness)  # The operator saved the plan while the organization held both sites.
    write_settled_operation(harness)  # A settled operation whose retry holds both sites.
    harness.api.payloads[SITE_READ] = harness.api.payloads[SITE_READ][:1]  # The second site left the organization.
    client = harness.controls.client  # The signed client, with a whole site read.
    options = client.get(OPTIONS_PAGE, headers=SCRIPT_HEADERS)  # The options page.
    confirm = client.get(CONFIRM_PAGE, headers=SCRIPT_HEADERS)  # The confirm page.
    precheck = client.post(f"/api/org-upgrades/prechecks/{SITE_TWO}", json={"tier": 2}, headers=SCRIPT_HEADERS)
    retry = client.post(f"/api/org-upgrades/{RETRY_ID}/retry", json={}, headers=SCRIPT_HEADERS)  # The retry.
    answers = [(answer.status_code, error_code(answer)) for answer in (options, confirm, precheck, retry)]
    expected = [SITES_NOT_CHOSEN, SITES_NOT_CHOSEN, SITE_NOT_FOUND, SITES_NOT_CHOSEN]  # The answers of today.
    assert answers == expected, answers  # A whole list keeps each answer.


def test_a_save_with_no_selected_types_field_makes_no_site_check(harness: LaterCheckHarness) -> None:
    """Research: an older access point request makes no site check today, and this change keeps that rule."""
    harness.sites.mode = LOST  # The later site read loses page two.
    answer = harness.controls.client.post(OPTIONS_API, json=LEGACY_BODY, headers=SCRIPT_HEADERS)  # The old save.
    assert (answer.status_code, answer.get_json()) == (200, {"next": CONFIRM_PAGE})  # The save of today.
    assert SITE_READ not in [read for read, _ in harness.api.calls]  # No site read, so no site check.


def test_an_empty_save_body_answers_400_before_the_site_check(portal_app: Flask, harness: LaterCheckHarness) -> None:
    """Edge case: an empty body holds no field, so the save refuses it and makes no site read."""
    with portal_app.test_request_context(OPTIONS_API, method="POST", data="", content_type=JSON_TYPE):
        assert dict(org_upgrade.request_source()) == {}  # The body reader reads an empty body as no field.
    harness.sites.mode = LOST  # The later site read loses page two.
    client = harness.controls.client  # The signed client.
    answer = client.post(OPTIONS_API, data="", content_type=JSON_TYPE, headers=SCRIPT_HEADERS)  # An empty body.
    assert (answer.status_code, error_code(answer)) == OPTIONS_INVALID, answer.get_data(as_text=True)[:400]
    assert SITE_READ not in [read for read, _ in harness.api.calls]  # The body check comes before the site read.
    assert harness.controls.store.records == {}  # No plan exists.


def test_a_malformed_json_save_body_answers_400_before_the_site_check(
    portal_app: Flask, harness: LaterCheckHarness
) -> None:
    """Edge case: bad json reads as an empty body, so the save refuses it and makes no site read."""
    body = '{"selected_types": bad json'  # A body that no JSON parser can read.
    with portal_app.test_request_context(OPTIONS_API, method="POST", data=body, content_type=JSON_TYPE):
        assert dict(org_upgrade.request_source()) == {}  # The body reader never raises for a broken body.
    harness.sites.mode = LOST  # The later site read loses page two.
    client = harness.controls.client  # The signed client.
    answer = client.post(OPTIONS_API, data=body, content_type=JSON_TYPE, headers=SCRIPT_HEADERS)  # A broken body.
    assert (answer.status_code, error_code(answer)) == OPTIONS_INVALID, answer.get_data(as_text=True)[:400]
    assert SITE_READ not in [read for read, _ in harness.api.calls]  # The body check comes before the site read.
    assert harness.controls.store.records == {}  # No plan exists.
