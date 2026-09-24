"""Contract tests for the retry, check, and reschedule controls of one multi-site operation.

Why:
    Issue #3247. The single-site portal can retry the failed devices of a
    finished run, check an uncertain outcome against the running versions, and
    move the start time of a planned run. The multi-site portal could do none
    of the three. These tests drive the real Flask routes and the production
    aggregate service, with stand-ins only at the cloud edge. No test opens a
    socket, and no test sends a firmware request.
"""

from __future__ import annotations

import re
import time
from collections.abc import Iterator, Mapping
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from threading import Lock
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.firmware.aggregate_upgrade_service import AggregateUpgradeService
from src.upgrade_portal.app.routes import org_upgrade, select
from src.upgrade_portal.runtime import identity, lock
from src.upgrade_portal.upgrade import options as option_rules
from tests.support.lock_store_double import FakeLockStore

OPERATOR_EMAIL = "org-controls.operator@juniper.net"  # A reachable address, because a firmware write needs one.
CLOUD_ACCOUNT = "mist.account@juniper.net"  # The account label behind the signed cloud session.
SITE_TWO = "00000000-0000-0000-0000-0000000000cc"  # The second selected site of each test.
AP_ONE = "001122334455"  # The access point at the first site.
AP_TWO = "001122334466"  # The access point at the second site.
SWITCH_ONE = "001122334477"  # The switch at the first site.
SWITCH_TWO = "001122334488"  # The switch at the second site.
DEVICE_NAMES = {AP_ONE: "ap-one", AP_TWO: "ap-two", SWITCH_ONE: "switch-one", SWITCH_TWO: "switch-two"}
AP_TARGET = "0.15.1"  # The access point version that each plan requests.
AP_OLD = "0.14.1"  # The access point version before the upgrade.
JUNOS_TARGET = "23.4R1.9"  # The switch version that each plan requests.
JUNOS_OLD = "23.4R1.8"  # The switch version before the upgrade.
RETRY_ID = "org-run-retry"  # The settled operation of the retry tests.
RECONCILE_ID = "org-run-reconcile"  # The operation with one uncertain child job at each site.
RECONCILE_WORD = f"RECONCILE {RECONCILE_ID}"  # The exact typed word of the check.
RETRY_SESSION_KEY = "org_upgrade_retry"  # The cookie key that holds the retry reference.
OPTIONS_SESSION_KEY = "org_upgrade_options"  # The cookie key that holds the saved options.
OPTIONS_PAGE = "/upgrade/org/options"  # The multi-site options page.
OPTIONS_API = "/api/org-upgrades/options"  # The save of the multi-site options.
CONFIRM_PAGE = "/upgrade/org/confirm"  # The typed confirmation page.
SUBMIT_API = "/api/org-upgrades"  # The confirmed submission.
SITE_SELECTION = "/select/site"  # The site selection of the multi-site mode.
RETRY_CLEAR_API = "/api/org-upgrades/options/retry/clear"  # The end of a retry.
FIELD_FORMAT = "%Y-%m-%dT%H:%M"  # The value format of a date and time field.
START_NOW_TEXT = "The upgrade starts at once after you confirm."  # The start line of a plan with no start time.
PLAN_CHOICES = {  # The choices of a plan of the access points and the switches.
    "selected_types": ["ap", "switch"],
    "version_ap": AP_TARGET,
    "version_switch": JUNOS_TARGET,
    "strategy": "big_bang",
}


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


class SiteVersionReader:
    """Answer the running versions of each site, and record each site read."""

    def __init__(self) -> None:
        """Start with no answer and no read."""
        self.answers: dict[str, dict[str, str]] = {}  # A test fills the answer of each site.
        self.calls: list[str] = []  # Each entry names one site read.

    def __call__(self, cloud_session: Any, site_id: str) -> dict[str, str]:
        """Record the site read, and return its fixed answer."""
        del cloud_session  # The stand-in opens no socket.
        self.calls.append(site_id)  # A test can count the reads.
        return dict(self.answers.get(site_id, {}))  # An unknown site answers no device.


class ControlsService(AggregateUpgradeService):
    """Keep the production build, reschedule, and check, and reach no cloud."""

    def status(self, cloud_session: Any, record: Any, store: Any) -> Any:
        """Return the stored record as it is."""
        del cloud_session, store  # The test record already holds the cloud answers.
        return record  # No child read runs.

    def submit(self, cloud_session: Any, record: Any, store: Any, refresh_lock: Any) -> Any:
        """Accept every child job without a cloud write."""
        del cloud_session, refresh_lock  # The production service tests cover the claim and the refresh.
        for child in record["children"]:  # Each child reaches the stand-in cloud one time.
            child["status"] = "accepted"  # The cloud accepted the child job.
        record["state"] = "running"  # The operation now runs.
        store.write_run(record)  # Persist the accepted child jobs.
        return record  # The route opens the progress page.


@dataclass
class ControlsHarness:
    """Hold the signed client and each stand-in of one test."""

    client: FlaskClient  # The signed browser session.
    store: RecordStore  # The durable store of every operation.
    reader: SiteVersionReader  # The running version read of each site.
    locks: FakeLockStore  # The site lock store.
    operator: identity.OperatorSession  # The server-side record of the operator.
    org_id: str  # The selected organization.
    site_one: str  # The first selected site.


def inventory_row(mac: str) -> dict[str, str]:
    """Build one device row of the site inventory.

    Why:
        The options page reads the field `device_type`, and the shipped target
        builder reads the field `type` of the raw inventory. The row holds both,
        as the two production reads do.
    """
    device_type = "ap" if mac in (AP_ONE, AP_TWO) else "switch"  # The family of the device.
    model = "AP45" if device_type == "ap" else "EX4400"  # One model for each family.
    version = AP_OLD if device_type == "ap" else JUNOS_OLD  # The version before the upgrade.
    row = {"mac": mac, "name": DEVICE_NAMES[mac], "device_type": device_type, "model": model, "version": version}
    return {**row, "type": device_type}  # The raw inventory field of the target builder.


def option_builder(devices: Mapping[str, list[dict[str, str]]]) -> Any:
    """Return the stand-in of the site option mapper, with the production record shape.

    Args:
        devices: The inventory rows of each site.

    Returns:
        A mapper that validates each choice through the shipped option rules.
    """

    def build(cloud_session: Any, org_id: str, site_id: str, body: Mapping[str, Any]) -> dict[str, Any]:
        """Build the targets and the options of one site without a cloud read."""
        del cloud_session, org_id  # The stand-in reads no inventory from the cloud.
        entries = option_rules.build_targets(devices[site_id], list(body["targets"]))  # One entry for each choice.
        return {"targets": entries, "options": asdict(option_rules.build_options(dict(body)))}  # Production shape.

    return build  # The route calls the mapper one time for each site.


@pytest.fixture
def harness(portal_app: Flask, fake_mist_api: Any, fake_org_id: str, fake_site_id: str) -> Iterator[ControlsHarness]:
    """Return a signed client with two selected sites and no live service."""
    store, reader, locks = RecordStore(), SiteVersionReader(), FakeLockStore()  # One fresh stand-in of each kind.
    devices = {  # The inventory of both sites.
        fake_site_id: [inventory_row(AP_ONE), inventory_row(SWITCH_ONE)],
        SITE_TWO: [inventory_row(AP_TWO), inventory_row(SWITCH_TWO)],
    }
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
            "RUN_STORE": store,  # Every operation stays in memory.
            "AGGREGATE_UPGRADE_SERVICE": ControlsService(),  # The production writes with no cloud call.
            org_upgrade.DEVICE_VERSION_READER_CONFIG_KEY: reader,  # No stats read reaches the cloud.
            org_upgrade.OPTIONS_VIEW_CONFIG_KEY: lambda session, org, site: {"targets": deepcopy(devices[site])},
            org_upgrade.OPTIONS_BUILDER_CONFIG_KEY: option_builder(devices),  # The save reaches no cloud.
            "MIST_SELF_READER": lambda cloud_session: {"email": CLOUD_ACCOUNT},  # No self read.
        }
    )
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
            yield ControlsHarness(client, store, reader, locks, operator, fake_org_id, fake_site_id)
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)  # No later test finds this operator.


def stored_target(mac: str, site_id: str, before: str, wanted: str) -> dict[str, str]:
    """Build one stored target record, in the shape that the aggregate build stores."""
    row = inventory_row(mac)  # The same name, family, and model as the inventory.
    kept = {key: row[key] for key in ("mac", "name", "device_type", "model")}  # The stored identity fields.
    return {**kept, "version_before": before, "version_target": wanted, "site_id": site_id}  # One stored target.


def reading(version: str) -> dict[str, Any]:
    """Build one stored running version reading."""
    return {"version": version, "read_at": "2026-09-24T01:00:00+00:00", "reads": 1}  # One settled reading.


def operation_record(harness: ControlsHarness, operation_id: str, children: list[dict[str, Any]]) -> dict[str, Any]:
    """Build one durable operation of the signed operator across both sites."""
    return {
        "_key": operation_id,
        "run_id": operation_id,
        "operation_id": operation_id,
        "owner": harness.operator.owner.key,  # The signed operator owns the operation.
        "org_id": harness.org_id,  # The selected organization.
        "site_ids": [harness.site_one, SITE_TWO],  # The approved sites, in the approved order.
        "site_names": {harness.site_one: "Test Site", SITE_TWO: "Site Two"},
        "record_version": 0,  # The first durable version.
        "state": "failed",
        "device_versions": {},
        "versions_final": [],
        "updated_at": "2026-09-24T01:00:00+00:00",
        "actor_email": OPERATOR_EMAIL,
        "cloud_account": CLOUD_ACCOUNT,
        "site_locks": {},
        "children": children,
        "errors": [],
        "cancellation": {"requested": False, "results": []},
    }


def access_point_child(site_one: str) -> dict[str, Any]:
    """Build the organization access point child job: one device upgraded, and one device failed."""
    return {
        "child_id": "child-ap",
        "route": "upgradeOrgDevices",
        "site_id": None,  # The organization route serves both sites.
        "site_name": "Test Site, Site Two",
        "device_family": "ap",
        "status": "failed",  # One of the two access points failed.
        "target_ids": [AP_ONE, AP_TWO],
        "targets": [
            stored_target(AP_ONE, site_one, AP_OLD, AP_TARGET),
            stored_target(AP_TWO, SITE_TWO, AP_OLD, AP_TARGET),
        ],
        "status_data": {
            "site_upgrades": [
                {"site_id": site_one, "upgrade": {"targets": {"upgraded": [AP_ONE]}}},
                {"site_id": SITE_TWO, "upgrade": {"targets": {"failed": [AP_TWO]}}},
            ]
        },
        "error": None,
        "cancellation": None,
    }


def switch_child(site_one: str, status: str) -> dict[str, Any]:
    """Build the switch child job of the first site in one final or live state."""
    healthy = status == "completed"  # Only a completed switch runs the target version.
    return {
        "child_id": "child-switch",
        "route": "upgradeSiteDevices",
        "site_id": site_one,
        "site_name": "Test Site",
        "device_family": "switch",
        "status": status,
        "target_ids": [SWITCH_ONE],
        "targets": [stored_target(SWITCH_ONE, site_one, JUNOS_OLD, JUNOS_TARGET)],
        "status_data": {"targets": {"upgraded" if healthy else "failed": [SWITCH_ONE]}},
        "error": None if healthy else "The switch child failed.",
        "cancellation": None,
    }


def settled_record(harness: ControlsHarness, switch_status: str = "failed") -> dict[str, Any]:
    """Build a settled operation of the retry tests.

    Args:
        harness: The test harness.
        switch_status: The state of the switch child job. A completed switch runs the target version.

    Returns:
        The operation record. The failed access point at the second site always needs a retry.
    """
    children = [access_point_child(harness.site_one), switch_child(harness.site_one, switch_status)]  # Two jobs.
    record = operation_record(harness, RETRY_ID, children)  # The owned operation across both sites.
    switch_version = JUNOS_TARGET if switch_status == "completed" else JUNOS_OLD  # The running switch version.
    record["device_versions"] = {
        AP_ONE: reading(AP_TARGET),
        AP_TWO: reading(AP_OLD),
        SWITCH_ONE: reading(switch_version),
    }
    record["versions_final"] = ["child-ap", "child-switch"]  # The page reads no site again.
    record["plan_options"] = {**PLAN_CHOICES, "reboot": True, "reboot_at": "1h"}  # The choices of the earlier save.
    return record  # The caller writes the record to the store.


def uncertain_child(child_id: str, site_id: str, site_name: str, mac: str) -> dict[str, Any]:
    """Build one switch child job whose submission outcome is unknown."""
    return {
        "child_id": child_id,
        "route": "upgradeSiteDevices",
        "site_id": site_id,
        "site_name": site_name,
        "device_family": "switch",
        "status": "submission_unknown",  # The portal did not receive the cloud answer.
        "target_ids": [mac],
        "targets": [stored_target(mac, site_id, JUNOS_OLD, JUNOS_TARGET)],
        "status_data": {},
        "error": "The portal did not receive the cloud answer.",
        "cancellation": None,
    }


def held_lock(harness: ControlsHarness, site_id: str) -> dict[str, Any]:
    """Acquire the lock of one site for the operation of the check, and return its stored record."""
    request = lock.LockRequest(harness.org_id, site_id, harness.operator.owner, RECONCILE_ID)  # The operator holds it.
    grant = lock.acquire_site_lock(request, harness.locks)  # The fake store keeps the lock in memory.
    return grant.record.to_record()  # The JSON value that the operation stores.


def uncertain_record(harness: ControlsHarness) -> dict[str, Any]:
    """Build an operation with one uncertain switch child job at each site, and hold both site locks."""
    children = [  # One uncertain child job at each site.
        uncertain_child("child-switch-one", harness.site_one, "Test Site", SWITCH_ONE),
        uncertain_child("child-switch-two", SITE_TWO, "Site Two", SWITCH_TWO),
    ]
    record = operation_record(harness, RECONCILE_ID, children)  # The owned operation across both sites.
    record["state"] = "partial"  # The aggregate state of two uncertain child jobs.
    record["site_locks"] = {site_id: held_lock(harness, site_id) for site_id in (harness.site_one, SITE_TWO)}
    return record  # The caller writes the record to the store.


def post_json(harness: ControlsHarness, path: str, body: Mapping[str, Any] | None = None) -> Any:
    """Send one script request, and return the answer."""
    return harness.client.post(path, json=dict(body or {}))  # A JSON request receives a JSON answer.


def error_code(answer: Any) -> str:
    """Return the error code of one refusal envelope."""
    body = answer.get_json() or {}  # Every refusal answers the one error envelope of the portal.
    return str(body.get("error", {}).get("code", ""))  # An absent code reads as empty text.


def browser_value(harness: ControlsHarness, key: str) -> Any:
    """Return one value of the signed browser session, or None."""
    with harness.client.session_transaction() as browser_session:  # Read the signed cookie.
        return deepcopy(browser_session.get(key))  # Detach the value for the assertions.


def saved_operation_id(harness: ControlsHarness) -> str:
    """Return the operation identifier that the saved options of the session name."""
    options = browser_value(harness, OPTIONS_SESSION_KEY) or {}  # The saved options of the session.
    return str(options.get("operation_id", ""))  # The durable identity of the saved plan.


def table_names(page: str) -> list[str]:
    """Return the device names of the device table of the options page, in page order."""
    start = page.index('data-testid="org-upgrade-device-summary"')  # The device table starts here.
    table = page[start : page.index("</table>", start)]  # Keep the device table only.
    return re.findall(r'<th scope="row">([^<]*)</th>', table)  # One name for each device row.


def box_checked(page: str, family: str) -> bool:
    """Return true when the options page checks the box of one device family."""
    return re.search(rf'data-testid="org-upgrade-type-{family}"\s*checked', page) is not None  # Word after the id.


def planned_macs(record: Mapping[str, Any]) -> set[str]:
    """Return the MAC address of each device that one plan holds."""
    return {mac for child in record["children"] for mac in child["target_ids"]}  # Every child job of the plan.


def utc_field(offset: timedelta) -> str:
    """Return the value of a date and time field at an offset from now, in UTC."""
    return (datetime.now(UTC) + offset).strftime(FIELD_FORMAT)  # The browser sends minutes only.


def epoch_of(field_value: str) -> int:
    """Return the epoch seconds of one date and time field value, read as UTC."""
    return int(datetime.strptime(field_value, FIELD_FORMAT).replace(tzinfo=UTC).timestamp())  # The portal zone.


def start_line(field_value: str) -> str:
    """Return the start line that the confirmation page shows for one field value."""
    return f"The upgrade starts at {field_value.replace('T', ' ')} UTC."  # The text of the schedule view.


def save_plan(harness: ControlsHarness, extra: Mapping[str, str] | None = None) -> str:
    """Save one plan of every device at both sites, and return its operation identifier."""
    answer = post_json(harness, OPTIONS_API, {**PLAN_CHOICES, **dict(extra or {})})  # The options save.
    assert answer.status_code == 200, answer.get_json()  # A refused save stops the test with its reason.
    return saved_operation_id(harness)  # The durable identity of the new plan.


def save_scheduled_plan(harness: ControlsHarness) -> tuple[str, str]:
    """Save one plan that starts in two hours and reboots one hour after the save."""
    start = utc_field(timedelta(hours=2))  # A start inside the window of the site lock.
    return save_plan(harness, {"start_time": start, "reboot_at": "1h"}), start  # The identity and the start.


def reschedule_path(operation_id: str) -> str:
    """Return the reschedule path of one operation."""
    return f"/api/org-upgrades/{operation_id}/reschedule"  # The route of the confirmation page form.


def child_bodies(record: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Return the request body of each child job of one plan."""
    return [dict(child["body"]) for child in record["children"]]  # One body for each child job.


def switch_reboots(record: Mapping[str, Any]) -> list[int]:
    """Return the stored reboot moment of each switch child job of one plan."""
    switches = [child for child in record["children"] if child["device_family"] == "switch"]  # Site child jobs.
    return [int(child["body"]["reboot_at"]) for child in switches]  # The moment that the cloud receives.


# ---------------------------------------------------------------------------
# The retry of the devices that did not reach the target version.
# ---------------------------------------------------------------------------


def test_the_retry_opens_a_plan_of_the_failed_devices_only(harness: ControlsHarness) -> None:
    """A retry selects only the sites and the devices that did not reach the target version."""
    harness.store.write_run(settled_record(harness, switch_status="completed"))  # Only one access point failed.
    answer = post_json(harness, f"/api/org-upgrades/{RETRY_ID}/retry")  # The operator presses the retry button.
    page = harness.client.get(OPTIONS_PAGE).get_data(as_text=True)  # The narrowed options page.
    assert answer.status_code == 200 and answer.get_json() == {"next": OPTIONS_PAGE}  # The options page opens.
    assert browser_value(harness, RETRY_SESSION_KEY) == {"operation_id": RETRY_ID, "org_id": harness.org_id}
    assert harness.operator.selected_site_ids == (SITE_TWO,)  # The healthy site leaves the selection.
    assert 'data-testid="org-upgrade-retry-banner"' in page  # The banner names the retry.
    assert f'<span class="cell-mono">{AP_TWO}</span>' in page  # The banner names the failed device.
    assert table_names(page) == ["ap-two"]  # The device table holds the failed access point only.
    assert box_checked(page, "ap") and not box_checked(page, "switch")  # The prefill checks the retry family.
    assert f'value="{AP_TARGET}"' in page  # The prefill keeps the earlier target version.


def test_the_retry_save_plans_only_the_retry_devices(harness: ControlsHarness) -> None:
    """The saved retry plan holds each retry device and names the operation that it repeats."""
    harness.store.write_run(settled_record(harness))  # One access point and one switch failed.
    post_json(harness, f"/api/org-upgrades/{RETRY_ID}/retry")  # Open the retry.
    page = harness.client.get(OPTIONS_PAGE).get_data(as_text=True)  # The narrowed options page.
    saved = post_json(harness, OPTIONS_API, PLAN_CHOICES)  # Save the prefilled choices.
    plan = harness.store.records[saved_operation_id(harness)]  # The new durable plan.
    assert saved.status_code == 200 and saved.get_json() == {"next": CONFIRM_PAGE}  # The confirmation opens.
    assert harness.operator.selected_site_ids == (harness.site_one, SITE_TWO)  # Each site holds a retry device.
    assert table_names(page) == ["switch-one", "ap-two"]  # The healthy devices stay off the page.
    assert planned_macs(plan) == {AP_TWO, SWITCH_ONE}  # The healthy devices stay out of the plan.
    assert plan["retry_of_operation_id"] == RETRY_ID  # The audit link names the earlier operation.
    assert {"operation_id", "target_count"}.isdisjoint(plan["plan_options"])  # Browser values stay in the browser.


def test_the_submit_of_a_retry_plan_ends_the_retry(harness: ControlsHarness) -> None:
    """The confirmed submission of a retry plan drops the retry reference."""
    harness.store.write_run(settled_record(harness))  # One access point and one switch failed.
    post_json(harness, f"/api/org-upgrades/{RETRY_ID}/retry")  # Open the retry.
    assert browser_value(harness, RETRY_SESSION_KEY) == {"operation_id": RETRY_ID, "org_id": harness.org_id}
    operation_id = save_plan(harness)  # Save the narrowed plan.
    started = post_json(harness, SUBMIT_API, {"confirmation": "CONFIRM"})  # The typed confirmation.
    assert started.status_code == 200, started.get_json()  # The submission starts.
    assert started.get_json() == {"next": f"/upgrade/org/jobs/{operation_id}"}  # The progress page opens.
    assert planned_macs(harness.store.records[operation_id]) == {AP_TWO, SWITCH_ONE}  # Only the retry devices.
    assert browser_value(harness, RETRY_SESSION_KEY) is None  # The next plan covers every device again.
    assert harness.store.records[operation_id]["state"] == "running"  # The stand-in cloud accepted each job.


def test_the_clear_ends_the_retry_and_plans_every_device(harness: ControlsHarness) -> None:
    """The clear control ends the retry, and the page plans every device of the selected sites."""
    harness.store.write_run(settled_record(harness, switch_status="completed"))  # Only one access point failed.
    post_json(harness, f"/api/org-upgrades/{RETRY_ID}/retry")  # Open the retry of the second site.
    cleared = post_json(harness, RETRY_CLEAR_API)  # The operator presses the clear button.
    page = harness.client.get(OPTIONS_PAGE).get_data(as_text=True)  # The full options page.
    assert cleared.status_code == 200 and cleared.get_json() == {"next": OPTIONS_PAGE}  # The options page opens.
    assert browser_value(harness, RETRY_SESSION_KEY) is None  # The retry reference is gone.
    assert 'data-testid="org-upgrade-retry-banner"' not in page  # No banner names a retry.
    assert table_names(page) == ["ap-two", "switch-two"]  # Every device of the selected site returns.


def test_a_changed_site_selection_ends_the_retry(harness: ControlsHarness) -> None:
    """A new site selection drops the retry reference of the earlier selection."""
    harness.store.write_run(settled_record(harness))  # Both sites hold a retry device.
    post_json(harness, f"/api/org-upgrades/{RETRY_ID}/retry")  # Open the retry of both sites.
    assert browser_value(harness, RETRY_SESSION_KEY) == {"operation_id": RETRY_ID, "org_id": harness.org_id}
    changed = post_json(harness, SITE_SELECTION, {"site_ids": [harness.site_one]})  # A smaller selection.
    assert changed.status_code == 200, changed.get_json()  # The selection is valid.
    assert browser_value(harness, RETRY_SESSION_KEY) is None  # A retry of the earlier scope must not narrow.


def test_the_retry_refuses_an_operation_of_another_operator(harness: ControlsHarness) -> None:
    """A retry of an operation that another operator owns reveals nothing and changes nothing."""
    record = settled_record(harness)  # A settled operation with two retry devices.
    record["owner"] = "another-operator"  # Another operator owns the operation.
    harness.store.write_run(record)  # Store the foreign operation.
    answer = post_json(harness, f"/api/org-upgrades/{RETRY_ID}/retry")  # The request names the foreign operation.
    assert answer.status_code == 404 and error_code(answer) == "org_upgrade_operation_not_found"  # No reveal.
    assert browser_value(harness, RETRY_SESSION_KEY) is None  # No retry opens.
    assert harness.operator.selected_site_ids == (harness.site_one, SITE_TWO)  # The selection stays.


def test_the_retry_waits_until_every_child_job_ends(harness: ControlsHarness) -> None:
    """A retry while a child job can still write firmware can upgrade one device two times."""
    harness.store.write_run(settled_record(harness, switch_status="running"))  # The switch job still runs.
    answer = post_json(harness, f"/api/org-upgrades/{RETRY_ID}/retry")  # The request comes too early.
    assert answer.status_code == 409 and error_code(answer) == "org_upgrade_retry_unavailable"  # The wait.
    assert browser_value(harness, RETRY_SESSION_KEY) is None  # No retry opens.


def test_the_retry_refuses_when_each_device_runs_the_target_version(harness: ControlsHarness) -> None:
    """A version match proves the upgrade, so a failed cloud word alone does not open a retry."""
    record = settled_record(harness, switch_status="completed")  # The switch is healthy.
    record["device_versions"][AP_TWO] = reading(AP_TARGET)  # A later read found the target version.
    harness.store.write_run(record)  # Store the healthy operation.
    answer = post_json(harness, f"/api/org-upgrades/{RETRY_ID}/retry")  # No device needs a retry.
    assert answer.status_code == 409 and error_code(answer) == "org_upgrade_retry_unavailable"  # Nothing to do.


def test_the_retry_refuses_a_site_that_left_the_organization(harness: ControlsHarness, fake_mist_api: Any) -> None:
    """A retry never selects a site that the organization no longer holds."""
    harness.store.write_run(settled_record(harness, switch_status="completed"))  # The retry names site two.
    fake_mist_api.payloads["listOrgSites"] = [  # Site two left the organization after the plan.
        {"id": harness.site_one, "name": "Test Site", "org_id": harness.org_id},
    ]
    answer = post_json(harness, f"/api/org-upgrades/{RETRY_ID}/retry")  # The retry of the removed site.
    assert answer.status_code == 404 and error_code(answer) == "sites_not_chosen"  # The site check refuses.
    assert browser_value(harness, RETRY_SESSION_KEY) is None  # No retry opens.


def test_a_retry_plan_fails_closed_when_the_devices_recover(harness: ControlsHarness) -> None:
    """A retry whose devices recover before the save plans no device at all."""
    harness.store.write_run(settled_record(harness, switch_status="completed"))  # One access point failed.
    post_json(harness, f"/api/org-upgrades/{RETRY_ID}/retry")  # Open the retry.
    harness.store.records[RETRY_ID]["device_versions"][AP_TWO] = reading(AP_TARGET)  # The device recovered.
    page = harness.client.get(OPTIONS_PAGE).get_data(as_text=True)  # The options page of the empty retry.
    saved = post_json(harness, OPTIONS_API, PLAN_CHOICES)  # The save of the empty retry.
    assert "No device of that operation needs a retry now" in page  # The banner states the empty plan.
    assert table_names(page) == []  # The device table holds no device.
    assert saved.status_code == 400 and error_code(saved) == "org_upgrade_options_invalid"  # No empty plan.


def test_the_progress_page_and_the_poll_show_the_retry_control(harness: ControlsHarness) -> None:
    """The progress page lists each retry device, and the poll carries the same signature."""
    harness.store.write_run(settled_record(harness))  # One access point and one switch failed.
    page = harness.client.get(f"/upgrade/org/jobs/{RETRY_ID}").get_data(as_text=True)  # The progress page.
    poll = harness.client.get(f"/api/org-upgrades/{RETRY_ID}").get_json()  # The status poll.
    assert 'data-org-controls="retry=2;reconcile="' in page  # The signature that the poll compares.
    assert f'data-testid="org-upgrade-retry-device-{AP_TWO}"' in page  # The failed access point.
    assert f'data-testid="org-upgrade-retry-device-{SWITCH_ONE}"' in page  # The failed switch.
    assert f'data-testid="org-upgrade-retry-device-{AP_ONE}"' not in page  # The healthy access point.
    assert f'action="/api/org-upgrades/{RETRY_ID}/retry"' in page  # The retry form names the operation.
    assert poll["controls"]["signature"] == "retry=2;reconcile="  # The poll carries the same signature.
    assert poll["controls"]["retry"]["count"] == 2  # The poll counts the retry devices.


# ---------------------------------------------------------------------------
# The check of each uncertain child job.
# ---------------------------------------------------------------------------


def test_the_progress_page_offers_the_check_of_each_uncertain_child(harness: ControlsHarness) -> None:
    """The progress page names each uncertain child job and the exact typed word."""
    harness.store.write_run(uncertain_record(harness))  # Two uncertain child jobs.
    page = harness.client.get(f"/upgrade/org/jobs/{RECONCILE_ID}").get_data(as_text=True)  # The progress page.
    assert 'data-org-controls="retry=0;reconcile=child-switch-one,child-switch-two"' in page  # The signature.
    assert 'data-testid="org-upgrade-reconcile-child-child-switch-one"' in page  # The first uncertain job.
    assert 'data-testid="org-upgrade-reconcile-child-child-switch-two"' in page  # The second uncertain job.
    assert f'data-confirm-word="{RECONCILE_WORD}"' in page  # The typed word names this operation.
    assert 'data-testid="org-upgrade-retry-controls"' not in page  # No retry while a job is uncertain.


def test_a_proven_check_completes_each_child_and_frees_both_sites(harness: ControlsHarness) -> None:
    """Each device runs the target version, so each child job completes and each site goes free."""
    harness.store.write_run(uncertain_record(harness))  # Two uncertain child jobs hold both sites.
    harness.reader.answers = {harness.site_one: {SWITCH_ONE: JUNOS_TARGET}, SITE_TWO: {SWITCH_TWO: JUNOS_TARGET}}
    answer = post_json(harness, f"/api/org-upgrades/{RECONCILE_ID}/reconcile", {"confirmation": RECONCILE_WORD})
    stored = harness.store.records[RECONCILE_ID]  # The durable record after the check.
    assert answer.status_code == 200, answer.get_json()  # The check stored its verdicts.
    assert answer.get_json() == {"next": f"/upgrade/org/jobs/{RECONCILE_ID}"}  # The progress page opens.
    assert [child["status"] for child in stored["children"]] == ["completed", "completed"]  # Both proven.
    assert stored["state"] == "completed"  # The aggregate state follows the child jobs.
    assert all(child["reconciliation"]["proven"] for child in stored["children"])  # The evidence stays.
    assert {child["reconciliation"]["checked_by"] for child in stored["children"]} == {
        identity.email_digest(OPERATOR_EMAIL)  # The digest, never the address.
    }
    assert harness.reader.calls == [harness.site_one, SITE_TWO]  # One read for each site.
    assert stored["site_locks"] == {}  # The settled operation holds no site.
    assert lock.read_lock(harness.org_id, SITE_TWO, harness.locks) is None  # The site accepts new work.


def test_a_failed_site_read_proves_nothing_and_keeps_the_site(harness: ControlsHarness) -> None:
    """A site that answers no device keeps its child job uncertain and keeps each lock."""
    harness.store.write_run(uncertain_record(harness))  # Two uncertain child jobs hold both sites.
    harness.reader.answers = {harness.site_one: {SWITCH_ONE: JUNOS_TARGET}}  # Site two answers no device.
    answer = post_json(harness, f"/api/org-upgrades/{RECONCILE_ID}/reconcile", {"confirmation": RECONCILE_WORD})
    stored = harness.store.records[RECONCILE_ID]  # The durable record after the check.
    page = harness.client.get(f"/upgrade/org/jobs/{RECONCILE_ID}").get_data(as_text=True)  # The progress page.
    first, second = stored["children"]  # The child job of each site.
    assert answer.status_code == 200, answer.get_json()  # The check stored its verdicts.
    assert first["status"] == "completed"  # The proven child job completes.
    assert second["status"] == "submission_unknown"  # An empty read proves nothing.
    assert second["reconciliation"]["summary"].startswith("0 of 1 devices run the target version.")  # Evidence.
    assert set(stored["site_locks"]) == {harness.site_one, SITE_TWO}  # A live child job keeps each site.
    held = lock.read_lock(harness.org_id, SITE_TWO, harness.locks)  # The lock of the site that answered nothing.
    assert getattr(held, "run_id", None) == RECONCILE_ID  # The operation still holds the site.
    assert 'data-testid="org-upgrade-reconcile-evidence-child-switch-two"' in page  # The page shows the evidence.
    assert 'data-testid="org-upgrade-reconcile-child-child-switch-one"' not in page  # The proven job leaves.


@pytest.mark.parametrize("typed", ["", "RECONCILE", f"reconcile {RECONCILE_ID}", "RECONCILE org-run-other"])
def test_the_check_refuses_a_wrong_typed_word(harness: ControlsHarness, typed: str) -> None:
    """Only the exact typed word of this operation starts the check."""
    harness.store.write_run(uncertain_record(harness))  # Two uncertain child jobs.
    answer = post_json(harness, f"/api/org-upgrades/{RECONCILE_ID}/reconcile", {"confirmation": typed})
    assert answer.status_code == 400 and error_code(answer) == "confirmation_required"  # The word guard refuses.
    assert harness.reader.calls == []  # The guard runs before any cloud read.
    assert harness.store.records[RECONCILE_ID]["record_version"] == 0  # Nothing changes.


def test_the_check_refuses_an_empty_body(harness: ControlsHarness) -> None:
    """A request with no body holds no typed word, so the check refuses it before any read."""
    harness.store.write_run(uncertain_record(harness))  # Two uncertain child jobs.
    answer = harness.client.post(f"/api/org-upgrades/{RECONCILE_ID}/reconcile", data="")  # No body at all.
    assert answer.status_code == 400 and error_code(answer) == "confirmation_required"  # The word guard refuses.
    assert harness.reader.calls == []  # The guard runs before any cloud read.
    assert harness.store.records[RECONCILE_ID]["record_version"] == 0  # Nothing changes.


def test_the_check_refuses_a_malformed_json_body(harness: ControlsHarness) -> None:
    """A body that is not valid JSON holds no typed word, so the check refuses it before any read."""
    harness.store.write_run(uncertain_record(harness))  # Two uncertain child jobs.
    answer = harness.client.post(  # A damaged body from a scripted client.
        f"/api/org-upgrades/{RECONCILE_ID}/reconcile", data="{bad json", content_type="application/json"
    )
    assert answer.status_code == 400 and error_code(answer) == "confirmation_required"  # The word guard refuses.
    assert harness.reader.calls == []  # The guard runs before any cloud read.
    assert harness.store.records[RECONCILE_ID]["record_version"] == 0  # Nothing changes.


def test_the_check_refuses_while_the_writes_stay_disabled(harness: ControlsHarness, portal_app: Flask) -> None:
    """The check changes the record of a firmware operation, so the write gate applies."""
    portal_app.config["ORG_UPGRADE_WRITES_ENABLED"] = False  # The deployment disables the writes.
    harness.store.write_run(uncertain_record(harness))  # Two uncertain child jobs.
    answer = post_json(harness, f"/api/org-upgrades/{RECONCILE_ID}/reconcile", {"confirmation": RECONCILE_WORD})
    assert answer.status_code == 503 and error_code(answer) == "org_upgrade_write_disabled"  # The gate refuses.
    assert harness.reader.calls == []  # The gate runs before any cloud read.


def test_the_check_refuses_an_operation_of_another_operator(harness: ControlsHarness) -> None:
    """A check of an operation that another operator owns reveals nothing and reads nothing."""
    record = uncertain_record(harness)  # Two uncertain child jobs.
    record["owner"] = "another-operator"  # Another operator owns the operation.
    harness.store.write_run(record)  # Store the foreign operation.
    answer = post_json(harness, f"/api/org-upgrades/{RECONCILE_ID}/reconcile", {"confirmation": RECONCILE_WORD})
    assert answer.status_code == 404 and error_code(answer) == "org_upgrade_operation_not_found"  # No reveal.
    assert harness.reader.calls == []  # No cloud read runs.


def test_the_check_refuses_an_operation_with_no_uncertain_child(harness: ControlsHarness) -> None:
    """A settled operation needs no check."""
    harness.store.write_run(settled_record(harness))  # Every child job holds a final state.
    word = f"RECONCILE {RETRY_ID}"  # The exact word of the settled operation.
    answer = post_json(harness, f"/api/org-upgrades/{RETRY_ID}/reconcile", {"confirmation": word})
    assert answer.status_code == 409 and error_code(answer) == "org_upgrade_reconcile_unavailable"  # No work.
    assert harness.reader.calls == []  # No cloud read runs.


def test_the_check_waits_for_a_live_submission(harness: ControlsHarness) -> None:
    """A live submission can still change a child job, so the check waits and the page says so."""
    record = uncertain_record(harness)  # Two uncertain child jobs.
    record["submission_claim_id"] = "claim-live"  # A submission still runs.
    harness.store.write_run(record)  # Store the claimed operation.
    page = harness.client.get(f"/upgrade/org/jobs/{RECONCILE_ID}").get_data(as_text=True)  # The progress page.
    harness.reader.answers = {harness.site_one: {SWITCH_ONE: JUNOS_TARGET}, SITE_TWO: {SWITCH_TWO: JUNOS_TARGET}}
    answer = post_json(harness, f"/api/org-upgrades/{RECONCILE_ID}/reconcile", {"confirmation": RECONCILE_WORD})
    stored = harness.store.records[RECONCILE_ID]  # The durable record after the refusal.
    assert 'data-testid="org-upgrade-reconcile-wait"' in page  # The page states the wait.
    assert 'data-testid="org-upgrade-reconcile-confirmation"' not in page  # The page offers no form.
    assert answer.status_code == 409 and error_code(answer) == "org_upgrade_reconcile_unavailable"  # The wait.
    assert [child["status"] for child in stored["children"]] == ["submission_unknown", "submission_unknown"]


# ---------------------------------------------------------------------------
# The move of the start time before the confirmation.
# ---------------------------------------------------------------------------


def test_the_confirmation_page_names_the_start_time_and_offers_the_move(harness: ControlsHarness) -> None:
    """The confirmation page shows the start time and a form that moves it."""
    operation_id, start = save_scheduled_plan(harness)  # A plan that starts in two hours.
    page = harness.client.get(CONFIRM_PAGE).get_data(as_text=True)  # The confirmation page.
    assert start_line(start) in page  # The page names the start time.
    assert f'action="/api/org-upgrades/{operation_id}/reschedule"' in page  # The form moves this plan.
    assert f'value="{start}"' in page  # The field shows the saved start time.


def test_the_move_changes_every_child_job_and_the_saved_options(harness: ControlsHarness) -> None:
    """One move changes the start of every child job, the reboot moment, and the saved options."""
    operation_id, _ = save_scheduled_plan(harness)  # A plan that starts in two hours.
    moved = utc_field(timedelta(hours=3))  # The new start time.
    before = int(time.time())  # The clock before the move.
    answer = post_json(harness, reschedule_path(operation_id), {"start_time": moved})  # The operator moves it.
    after = int(time.time())  # The clock after the move.
    stored = harness.store.records[operation_id]  # The durable plan after the move.
    page = harness.client.get(CONFIRM_PAGE).get_data(as_text=True)  # The confirmation page after the move.
    reboots = switch_reboots(stored)  # The reboot moment of each switch child job.
    assert answer.status_code == 200 and answer.get_json() == {"next": CONFIRM_PAGE}, answer.get_json()
    assert {body["start_time"] for body in child_bodies(stored)} == {epoch_of(moved)}  # Every child job moves.
    assert reboots and all(before + 3600 <= reboot <= after + 3600 for reboot in reboots)  # One hour from now.
    assert stored["plan_options"]["start_time"] == epoch_of(moved)  # The stored choices stay in step.
    assert stored["rescheduled_by"] == identity.email_digest(OPERATOR_EMAIL)  # The digest, never the address.
    assert stored["state"] == "planned"  # The move writes no firmware.
    assert browser_value(harness, OPTIONS_SESSION_KEY)["start_time"] == epoch_of(moved)  # The session follows.
    assert start_line(moved) in page  # The page names the new start time.


def test_an_empty_field_starts_the_upgrade_at_once(harness: ControlsHarness) -> None:
    """An empty field removes the start time from every child job and from the saved options."""
    operation_id, _ = save_scheduled_plan(harness)  # A plan that starts in two hours.
    answer = post_json(harness, reschedule_path(operation_id), {"start_time": ""})  # The operator clears it.
    stored = harness.store.records[operation_id]  # The durable plan after the move.
    page = harness.client.get(CONFIRM_PAGE).get_data(as_text=True)  # The confirmation page after the move.
    assert answer.status_code == 200, answer.get_json()  # The move stored.
    assert all("start_time" not in body for body in child_bodies(stored))  # Each child job starts at once.
    assert "start_time" not in browser_value(harness, OPTIONS_SESSION_KEY)  # The session holds no old start.
    assert START_NOW_TEXT in page  # The page states the immediate start.


@pytest.mark.parametrize(
    "moved",
    [
        pytest.param(utc_field(-timedelta(days=1)), id="past"),
        pytest.param(utc_field(timedelta(days=2)), id="beyond-the-lock-window"),
        pytest.param("next tuesday", id="no-moment"),
    ],
)
def test_the_move_refuses_a_time_outside_the_window(harness: ControlsHarness, moved: str) -> None:
    """The move uses the start time guard of the single-site page."""
    operation_id, start = save_scheduled_plan(harness)  # A plan that starts in two hours.
    answer = post_json(harness, reschedule_path(operation_id), {"start_time": moved})  # A bad start time.
    stored = harness.store.records[operation_id]  # The durable plan after the refusal.
    assert answer.status_code == 400 and error_code(answer) == "org_upgrade_options_invalid"  # The guard.
    assert stored["record_version"] == 0  # Nothing changes.
    assert {body["start_time"] for body in child_bodies(stored)} == {epoch_of(start)}  # The start stays.


def test_the_move_refuses_an_empty_body(harness: ControlsHarness) -> None:
    """A request with no start time field never clears the planned start time."""
    operation_id, start = save_scheduled_plan(harness)  # A plan that starts in two hours.
    answer = harness.client.post(reschedule_path(operation_id), data="")  # No body at all.
    stored = harness.store.records[operation_id]  # The durable plan after the refusal.
    assert answer.status_code == 400 and error_code(answer) == "org_upgrade_options_invalid"  # The field guard.
    assert stored["record_version"] == 0  # Nothing changes.
    assert {body["start_time"] for body in child_bodies(stored)} == {epoch_of(start)}  # The start stays.
    assert browser_value(harness, OPTIONS_SESSION_KEY)["start_time"] == epoch_of(start)  # The session keeps it.


def test_the_move_refuses_a_malformed_json_body(harness: ControlsHarness) -> None:
    """A body that is not valid JSON never reads as a request to start the upgrade at once."""
    operation_id, start = save_scheduled_plan(harness)  # A plan that starts in two hours.
    answer = harness.client.post(  # A damaged body from a scripted client.
        reschedule_path(operation_id), data="{bad json", content_type="application/json"
    )
    stored = harness.store.records[operation_id]  # The durable plan after the refusal.
    assert answer.status_code == 400 and error_code(answer) == "org_upgrade_options_invalid"  # The field guard.
    assert stored["record_version"] == 0  # Nothing changes.
    assert {body["start_time"] for body in child_bodies(stored)} == {epoch_of(start)}  # The start stays.
    assert browser_value(harness, OPTIONS_SESSION_KEY)["start_time"] == epoch_of(start)  # The session keeps it.


def test_the_move_refuses_a_plan_that_the_session_did_not_save(harness: ControlsHarness) -> None:
    """Only the saved plan of this browser session can move."""
    save_scheduled_plan(harness)  # The session saves one plan.
    answer = post_json(harness, reschedule_path("org-run-other"), {"start_time": utc_field(timedelta(hours=3))})
    assert answer.status_code == 409 and error_code(answer) == "org_upgrade_reschedule_refused"  # Not this plan.


def test_the_move_refuses_a_claimed_plan_and_hides_the_form(harness: ControlsHarness) -> None:
    """A plan that a submission claimed cannot move, and the page offers no move."""
    operation_id, start = save_scheduled_plan(harness)  # A plan that starts in two hours.
    harness.store.records[operation_id]["submission_claim_id"] = "claim-live"  # A submission claimed the plan.
    page = harness.client.get(CONFIRM_PAGE).get_data(as_text=True)  # The confirmation page of the claimed plan.
    answer = post_json(harness, reschedule_path(operation_id), {"start_time": utc_field(timedelta(hours=3))})
    stored = harness.store.records[operation_id]  # The durable plan after the refusal.
    assert start_line(start) in page  # The page still names the start time.
    assert 'data-testid="org-upgrade-reschedule-form"' not in page  # The page offers no move.
    assert answer.status_code == 409 and error_code(answer) == "org_upgrade_reschedule_refused"  # The refusal.
    assert {body["start_time"] for body in child_bodies(stored)} == {epoch_of(start)}  # The start stays.


def test_a_plan_without_its_reboot_delay_keeps_its_schedule(harness: ControlsHarness) -> None:
    """A stored reboot moment never moves without the delay that made it."""
    operation_id, start = save_scheduled_plan(harness)  # A plan that reboots one hour after the save.
    harness.store.records[operation_id].pop("plan_options")  # An older plan holds no stored choices.
    answer = post_json(harness, reschedule_path(operation_id), {"start_time": utc_field(timedelta(hours=3))})
    stored = harness.store.records[operation_id]  # The durable plan after the refusal.
    assert answer.status_code == 409 and error_code(answer) == "org_upgrade_reschedule_refused"  # The refusal.
    assert {body["start_time"] for body in child_bodies(stored)} == {epoch_of(start)}  # The start stays.


def test_a_browser_form_post_moves_the_start_and_opens_the_confirmation(harness: ControlsHarness) -> None:
    """The form of the confirmation page works without the page script."""
    operation_id, _ = save_scheduled_plan(harness)  # A plan that starts in two hours.
    moved = utc_field(timedelta(hours=4))  # The new start time.
    answer = harness.client.post(  # A plain browser form post.
        reschedule_path(operation_id),
        data={"start_time": moved},
        headers={"Accept": "text/html"},
    )
    stored = harness.store.records[operation_id]  # The durable plan after the move.
    assert answer.status_code == 303 and answer.headers["Location"].endswith(CONFIRM_PAGE)  # See Other, then GET.
    assert {body["start_time"] for body in child_bodies(stored)} == {epoch_of(moved)}  # Every child job moves.
