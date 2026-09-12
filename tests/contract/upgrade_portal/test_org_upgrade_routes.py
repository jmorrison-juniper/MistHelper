"""Contract tests for the organization AP upgrade browser workflow.

Why:
    These tests drive the real Flask routes with an injected Mist service. No
    test opens a socket or submits a firmware job.
"""

from __future__ import annotations

from collections.abc import Iterator
from copy import deepcopy
from threading import Lock
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.firmware.org_upgrade_service import OrgUpgradeResult
from src.upgrade_portal.app.routes import org_upgrade, select
from src.upgrade_portal.app.routes.org_upgrade import status_summary
from src.upgrade_portal.runtime import identity, lock
from tests.support.lock_store_double import FakeLockStore

ORG_OPTIONS_PAGE = "/upgrade/org/options"
ORG_OPTIONS_API = "/api/org-upgrades/options"
ORG_CONFIRM_PAGE = "/upgrade/org/confirm"
ORG_SUBMIT_API = "/api/org-upgrades"
UPGRADE_ID = "33333333-3333-3333-3333-333333333333"
SITE_UPGRADE_ID = "44444444-4444-4444-4444-444444444444"
PROBE_EMAIL = "org-upgrade.operator@example.invalid"


class OrgUpgradeServiceStandIn:
    """Record organization upgrade calls and return fixed cloud outcomes."""

    def __init__(self) -> None:
        """Start with no calls and one running job."""
        self.calls: list[tuple[str, str, object]] = []
        self.job_status = "inprogress"

    def submit(self, cloud_session: Any, org_id: str, body: dict[str, object]) -> OrgUpgradeResult:
        """Record one submission and return the organization job identifier."""
        self.calls.append(("submit", org_id, body))
        return OrgUpgradeResult(org_id, UPGRADE_ID, 200, {"id": UPGRADE_ID}, None)

    def status(self, cloud_session: Any, org_id: str, upgrade_id: str) -> OrgUpgradeResult:
        """Record one status read and return site and target progress."""
        self.calls.append(("status", org_id, upgrade_id))
        return OrgUpgradeResult(
            org_id,
            upgrade_id,
            200,
            {
                "id": upgrade_id,
                "status": self.job_status,
                "current_phase": 1,
                "site_upgrades": [
                    {
                        "site_id": "11111111-1111-1111-1111-111111111111",
                        "id": SITE_UPGRADE_ID,
                        "status": "running",
                        "targets": {"total": 2, "upgraded": ["000000000001"], "failed": []},
                    }
                ],
            },
            None,
        )

    def cancel(self, cloud_session: Any, org_id: str, upgrade_id: str) -> OrgUpgradeResult:
        """Record one cancellation request and return an empty success body."""
        self.calls.append(("cancel", org_id, upgrade_id))
        return OrgUpgradeResult(org_id, upgrade_id, 200, {}, None)


class AggregateStoreStandIn:
    """Persist aggregate records without a database."""

    def __init__(self) -> None:
        """Start with no records."""
        self.records: dict[str, dict[str, Any]] = {}
        self.guard = Lock()

    def write_run(self, record: dict[str, Any]) -> bool:
        """Store one detached record."""
        with self.guard:
            self.records[str(record["run_id"])] = deepcopy(record)
        return True

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one detached record."""
        with self.guard:
            record = self.records.get(run_id)
            return deepcopy(record) if record is not None else None

    def compare_and_set_run(self, run_id: str, expected_version: int, replacement: dict[str, Any]) -> bool:
        """Replace one record only when its version matches."""
        with self.guard:
            record = self.records.get(run_id)
            if record is None or record.get("record_version") != expected_version:
                return False
            self.records[run_id] = deepcopy(replacement)
            return True


class AggregateBoundaryStandIn:
    """Model the aggregate contract without a cloud write."""

    def __init__(self) -> None:
        """Start with no submitted operation."""
        self.submit_count = 0
        self.cancel_count = 0
        self.final_state = ""  # An empty value keeps the mixed status answer below.

    def build(self, request: Any) -> dict[str, Any]:
        """Build three child rows for the selected device families."""
        children = [
            {
                "child_id": f"child-{family}",
                "route": route,
                "scope": "org" if family == "ap" else "site",
                "org_id": request.org_id,
                "site_id": None if family == "ap" else request.sites[0]["site_id"],
                "site_name": request.sites[0]["name"],
                "device_family": family,
                "target_ids": [target.mac for target in request.targets if target.device_type == family],
                "upgrade_id": None,
                "status": "planned",
                "status_data": {},
                "error": None,
                "cancellation": None,
            }
            for family, route in (
                ("ap", "upgradeOrgDevices"),
                ("switch", "upgradeSiteDevices"),
                ("gateway", "upgradeSiteDevices"),
            )
        ]
        return {
            "_key": "org-run-contract",
            "run_id": "org-run-contract",
            "operation_id": "org-run-contract",
            "owner": request.owner,
            "org_id": request.org_id,
            "site_ids": [site["site_id"] for site in request.sites],
            "request_nonce": request.request_nonce,
            "record_version": 0,
            "state": "planned",
            "site_locks": {},
            "children": children,
            "errors": [],
            "cancellation": {"requested": False, "results": []},
        }

    def submit(self, cloud_session: Any, record: dict[str, Any], store: Any, refresh_lock: Any) -> dict[str, Any]:
        """Submit the operation once and persist every child."""
        del refresh_lock  # The production service tests the per-child refresh behavior.
        if record["state"] != "planned":
            raise ValueError("This aggregate upgrade already started.")
        self.submit_count += 1
        for child in record["children"]:
            child["upgrade_id"] = f"{child['device_family']}-job"
            child["status"] = "accepted"
        record["state"] = "running"
        store.write_run(record)
        return record

    def status(self, cloud_session: Any, record: dict[str, Any], store: Any) -> dict[str, Any]:
        """Return mixed child status values."""
        if self.final_state:  # A test can end every child to prove the lock release.
            for child in record["children"]:
                child["status"] = self.final_state
            record["state"] = self.final_state
            store.write_run(record)
            return record
        record["children"][0]["status"] = "completed"
        record["children"][1]["status"] = "failed"
        record["children"][1]["error"] = "The switch child failed."
        record["children"][2]["status"] = "running"
        record["state"] = "partial"
        store.write_run(record)
        return record

    def cancel(self, cloud_session: Any, record: dict[str, Any], store: Any) -> dict[str, Any]:
        """Record one result for each child."""
        if record["cancellation"]["requested"]:
            raise ValueError("This aggregate cancellation already ran.")
        self.cancel_count += 1
        record["cancellation"] = {
            "requested": True,
            "results": [{"child_id": child["child_id"], "status": "requested"} for child in record["children"]],
        }
        store.write_run(record)
        return record


@pytest.fixture
def org_service() -> OrgUpgradeServiceStandIn:
    """Return a fresh service stand-in."""
    return OrgUpgradeServiceStandIn()


@pytest.fixture
def org_upgrade_client(
    portal_app: Flask,
    fake_mist_api: Any,
    fake_org_id: str,
    fake_site_id: str,
    org_service: OrgUpgradeServiceStandIn,
) -> Iterator[FlaskClient]:
    """Return a signed client with a multi-site selection and no live services."""
    portal_app.config["WTF_CSRF_ENABLED"] = False
    portal_app.config["MIST_READER"] = fake_mist_api.read
    portal_app.config["SITE_LOCK_READER"] = lambda org_id, site_ids: {site_id: None for site_id in site_ids}
    portal_app.config[select.LOCK_CLIENT_KEY] = FakeLockStore()
    portal_app.config["ORG_UPGRADE_SERVICE"] = org_service
    owner = identity.build_owner(PROBE_EMAIL, identity.issue_browser_id())
    operator_session = identity.OperatorSession(
        owner=owner,
        cloud_session=object(),
        credential_mode=identity.CredentialMode.ENVIRONMENT_TOKEN,
        selected_site_ids=(fake_site_id,),
    )
    identity.SESSION_REGISTRY.register(operator_session)
    try:
        with portal_app.test_client() as client:
            client.set_cookie(identity.BROWSER_ID_COOKIE, owner.browser_id)
            with client.session_transaction() as browser_session:
                browser_session[identity.SESSION_OWNER_KEY] = owner.key
                browser_session["selected_org_id"] = fake_org_id
                browser_session["selected_upgrade_mode"] = "multi_site"
            yield client
    finally:
        identity.SESSION_REGISTRY.drop(owner.key)


def save_valid_options(client: FlaskClient) -> None:
    """Save one safe canary request through the JSON contract."""
    answer = client.post(
        ORG_OPTIONS_API,
        json={
            "version": "0.14.29411",
            "strategy": "canary",
            "canary_phases": "10,100",
            "max_failure_percentage": "5",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert answer.status_code == 200
    assert answer.get_json() == {"next": ORG_CONFIRM_PAGE}


def test_the_options_page_shows_all_supported_device_types(org_upgrade_client: FlaskClient) -> None:
    """The options page keeps the style and names every supported device type."""
    answer = org_upgrade_client.get(ORG_OPTIONS_PAGE)
    assert answer.status_code == 200
    assert b'data-testid="org-upgrade-options"' in answer.data
    assert b"Access points" in answer.data
    assert b"Switches" in answer.data
    assert b"Gateways" in answer.data
    assert b"Start time (UTC)" in answer.data
    assert b'data-testid="org-strategy-serial"' in answer.data


def test_valid_options_reach_the_confirmation_page(org_upgrade_client: FlaskClient) -> None:
    """A valid request stores the options before the confirmation step."""
    save_valid_options(org_upgrade_client)
    answer = org_upgrade_client.get(ORG_CONFIRM_PAGE)
    assert answer.status_code == 200
    assert b'data-testid="org-upgrade-confirm"' in answer.data
    assert b'data-confirm-word="CONFIRM"' in answer.data
    assert b'data-confirm-target="org-upgrade-start"' in answer.data
    assert b'data-testid="org-upgrade-start"' in answer.data
    assert b"disabled" in answer.data
    assert b"0.14.29411" in answer.data


def test_big_bang_options_do_not_send_a_failure_limit(org_upgrade_client: FlaskClient) -> None:
    """The big-bang request omits the field that its Mist schema does not use."""
    answer = org_upgrade_client.post(
        ORG_OPTIONS_API,
        json={
            "version": "0.14.29411",
            "strategy": "big_bang",
            "canary_phases": "",
            "max_failure_percentage": "5",
        },
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert answer.status_code == 200
    with org_upgrade_client.session_transaction() as browser_session:
        assert "max_failure_percentage" not in browser_session["org_upgrade_options"]


def test_invalid_canary_phases_stop_before_submission(org_upgrade_client: FlaskClient) -> None:
    """Invalid phases answer 400 and call no Mist service."""
    answer = org_upgrade_client.post(
        ORG_OPTIONS_API,
        json={
            "version": "0.14.29411",
            "strategy": "canary",
            "canary_phases": "50,10",
            "max_failure_percentage": "5",
        },
    )
    assert answer.status_code == 400
    assert answer.get_json()["error"]["code"] == "org_upgrade_options_invalid"


def test_submission_requires_the_exact_confirmation(
    org_upgrade_client: FlaskClient,
    org_service: OrgUpgradeServiceStandIn,
) -> None:
    """A wrong confirmation sends no firmware write."""
    save_valid_options(org_upgrade_client)
    answer = org_upgrade_client.post(ORG_SUBMIT_API, json={"confirmation": "confirm"})
    assert answer.status_code == 400
    assert org_service.calls == []


def test_confirmed_submission_calls_the_service_once(
    org_upgrade_client: FlaskClient,
    org_service: OrgUpgradeServiceStandIn,
    fake_org_id: str,
    fake_site_id: str,
) -> None:
    """A confirmed request sends one explicit AP organization job."""
    save_valid_options(org_upgrade_client)
    answer = org_upgrade_client.post(
        ORG_SUBMIT_API,
        json={"confirmation": "CONFIRM"},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )
    assert answer.status_code == 200
    assert answer.get_json() == {"next": f"/upgrade/org/jobs/{UPGRADE_ID}"}
    assert len(org_service.calls) == 1
    name, org_id, body = org_service.calls[0]
    assert name == "submit"
    assert org_id == fake_org_id
    assert body["site_ids"] == [fake_site_id]
    assert body["device_type"] == "ap"
    assert body["all_sites"] is False


def test_repeated_confirmation_submits_only_one_job(
    org_upgrade_client: FlaskClient,
    org_service: OrgUpgradeServiceStandIn,
) -> None:
    """A repeated confirmed request cannot start a second organization job."""
    save_valid_options(org_upgrade_client)
    first = org_upgrade_client.post(ORG_SUBMIT_API, json={"confirmation": "CONFIRM"})
    second = org_upgrade_client.post(ORG_SUBMIT_API, json={"confirmation": "CONFIRM"})
    assert first.status_code == 200
    assert second.status_code == 409
    assert second.get_json()["error"]["code"] == "org_upgrade_already_submitted"
    assert [call[0] for call in org_service.calls] == ["submit"]


def test_new_valid_options_wait_for_the_previous_job_to_finish(
    org_upgrade_client: FlaskClient,
    org_service: OrgUpgradeServiceStandIn,
) -> None:
    """A later job starts only after the owned job reaches a final state."""
    save_valid_options(org_upgrade_client)
    first = org_upgrade_client.post(ORG_SUBMIT_API, json={"confirmation": "CONFIRM"})
    save_valid_options(org_upgrade_client)
    blocked = org_upgrade_client.post(ORG_SUBMIT_API, json={"confirmation": "CONFIRM"})
    org_service.job_status = "completed"
    status = org_upgrade_client.get(f"/api/org-upgrades/{UPGRADE_ID}")
    second = org_upgrade_client.post(ORG_SUBMIT_API, json={"confirmation": "CONFIRM"})
    assert first.status_code == 200
    assert blocked.status_code == 409
    assert status.status_code == 200
    assert second.status_code == 200
    assert [call[0] for call in org_service.calls] == ["submit", "status", "submit"]


def test_options_from_another_organization_cannot_reach_confirmation(
    org_upgrade_client: FlaskClient,
) -> None:
    """Saved options cannot cross an organization boundary."""
    save_valid_options(org_upgrade_client)
    with org_upgrade_client.session_transaction() as browser_session:
        browser_session["selected_org_id"] = "55555555-5555-5555-5555-555555555555"
    answer = org_upgrade_client.get(ORG_CONFIRM_PAGE)
    assert answer.status_code == 400
    assert answer.get_json()["error"]["code"] == "org_upgrade_options_invalid"


def test_unknown_submission_blocks_a_repeat(org_upgrade_client: FlaskClient) -> None:
    """An uncertain cloud answer leaves a reconciliation marker before return."""

    class UnknownService:
        @staticmethod
        def submit(cloud_session: Any, org_id: str, body: dict[str, object]) -> OrgUpgradeResult:
            raise RuntimeError("connection ended after the write")

    org_upgrade_client.application.config["ORG_UPGRADE_SERVICE"] = UnknownService
    save_valid_options(org_upgrade_client)
    first = org_upgrade_client.post(ORG_SUBMIT_API, json={"confirmation": "CONFIRM"})
    second = org_upgrade_client.post(ORG_SUBMIT_API, json={"confirmation": "CONFIRM"})
    assert first.status_code == 503
    assert first.get_json()["error"]["code"] == "org_upgrade_submission_failed"
    assert second.status_code == 409
    assert second.get_json()["error"]["code"] == "org_upgrade_already_submitted"
    with org_upgrade_client.session_transaction() as browser_session:
        assert browser_session["org_upgrade_last_job"]["state"] == "submission_unknown"


def test_zero_failure_limit_survives_the_options_round_trip(org_upgrade_client: FlaskClient) -> None:
    """The strict zero-percent failure limit stays visible after validation."""
    answer = org_upgrade_client.post(
        ORG_OPTIONS_API,
        json={
            "version": "0.14.29411",
            "strategy": "serial",
            "canary_phases": "",
            "max_failure_percentage": "0",
        },
    )
    assert answer.status_code == 200
    page = org_upgrade_client.get(ORG_OPTIONS_PAGE)
    assert page.status_code == 200
    assert b'value="0"' in page.data


def test_disabled_writes_call_no_service(
    org_upgrade_client: FlaskClient,
    org_service: OrgUpgradeServiceStandIn,
) -> None:
    """A deployment can expose the preview while it disables cloud writes."""
    org_upgrade_client.application.config["ORG_UPGRADE_WRITES_ENABLED"] = False
    save_valid_options(org_upgrade_client)
    answer = org_upgrade_client.post(ORG_SUBMIT_API, json={"confirmation": "CONFIRM"})
    assert answer.status_code == 503
    assert answer.get_json()["error"]["code"] == "org_upgrade_write_disabled"
    assert org_service.calls == []


def test_reference_site_entries_use_root_totals() -> None:
    """A reference-only site list keeps its job identifiers and root totals."""
    result = OrgUpgradeResult(
        "22222222-2222-2222-2222-222222222222",
        UPGRADE_ID,
        200,
        {
            "id": UPGRADE_ID,
            "status": "upgrading",
            "targets": {"total": 24, "upgraded": ["one"] * 8, "failed": ["bad"]},
            "site_upgrades": [
                {
                    "site_id": "11111111-1111-1111-1111-111111111111",
                    "upgrade_id": SITE_UPGRADE_ID,
                }
            ],
        },
        None,
    )
    summary = status_summary(result)
    assert summary["total"] == 24
    assert summary["upgraded_count"] == 8
    assert summary["failed_count"] == 1
    assert summary["site_upgrades"][0]["id"] == SITE_UPGRADE_ID


def test_status_page_and_api_preserve_site_progress(
    org_upgrade_client: FlaskClient,
    org_service: OrgUpgradeServiceStandIn,
) -> None:
    """The status paths show the organization and site job states."""
    page = org_upgrade_client.get(f"/upgrade/org/jobs/{UPGRADE_ID}")
    assert page.status_code == 200
    assert b'data-testid="org-upgrade-site-progress"' in page.data
    assert b'data-testid="org-upgrade-refresh"' in page.data
    assert b'data-org-upgrade-field="status"' in page.data
    answer = org_upgrade_client.get(f"/api/org-upgrades/{UPGRADE_ID}")
    assert answer.status_code == 200
    assert answer.get_json()["upgraded_count"] == 1
    assert answer.get_json()["site_upgrades"][0]["id"] == SITE_UPGRADE_ID
    assert [call[0] for call in org_service.calls] == ["status", "status"]


def test_cancellation_requires_cancel_and_calls_once(
    org_upgrade_client: FlaskClient,
    org_service: OrgUpgradeServiceStandIn,
    fake_org_id: str,
) -> None:
    """Cancellation uses its own typed safety word and one service call."""
    with org_upgrade_client.session_transaction() as browser_session:
        browser_session["org_upgrade_last_job"] = {
            "upgrade_id": UPGRADE_ID,
            "org_id": fake_org_id,
            "site_count": 1,
        }
    refused = org_upgrade_client.post(f"/api/org-upgrades/{UPGRADE_ID}/cancel", json={"confirmation": "CONFIRM"})
    assert refused.status_code == 400
    answer = org_upgrade_client.post(f"/api/org-upgrades/{UPGRADE_ID}/cancel", json={"confirmation": "CANCEL"})
    assert answer.status_code == 200
    assert answer.get_json() == {"upgrade_id": UPGRADE_ID, "cancel_requested": True}
    assert [call[0] for call in org_service.calls] == ["cancel"]


def test_cancellation_refuses_a_job_from_another_browser_session(
    org_upgrade_client: FlaskClient,
    org_service: OrgUpgradeServiceStandIn,
    fake_org_id: str,
) -> None:
    """A browser session cannot cancel an organization job that it did not start."""
    with org_upgrade_client.session_transaction() as browser_session:
        browser_session["org_upgrade_last_job"] = {
            "upgrade_id": "55555555-5555-5555-5555-555555555555",
            "org_id": fake_org_id,
            "site_count": 1,
        }
    answer = org_upgrade_client.post(f"/api/org-upgrades/{UPGRADE_ID}/cancel", json={"confirmation": "CANCEL"})
    assert answer.status_code == 409
    assert answer.get_json()["error"]["code"] == "org_upgrade_job_not_owned"
    assert org_service.calls == []


def test_multidevice_operation_is_durable_transparent_and_replay_safe(
    org_upgrade_client: FlaskClient,
    monkeypatch: pytest.MonkeyPatch,
    fake_org_id: str,
    fake_site_id: str,
) -> None:
    """The route persists AP, switch, and gateway children as one operation."""
    store = AggregateStoreStandIn()
    boundary = AggregateBoundaryStandIn()
    org_upgrade_client.application.config["RUN_STORE"] = store
    org_upgrade_client.application.config["AGGREGATE_UPGRADE_SERVICE"] = boundary
    devices = [
        {"mac": "001122334455", "name": "ap", "device_type": "ap", "model": "AP45"},
        {"mac": "001122334466", "name": "switch", "device_type": "switch", "model": "EX4400"},
        {"mac": "001122334477", "name": "gateway", "device_type": "gateway", "model": "SRX345"},
    ]
    monkeypatch.setattr(org_upgrade, "build_options_view", lambda session, org_id, site_id: {"targets": devices})

    def built(session: Any, org_id: str, site_id: str, body: dict[str, Any]) -> dict[str, Any]:
        targets = [
            {
                **device,
                "version_before": "old",
                "version_target": next(row["version_target"] for row in body["targets"] if row["mac"] == device["mac"]),
                "site_id": site_id,
            }
            for device in devices
        ]
        return {"targets": targets, "options": {"strategy": "big_bang", "reboot": True}}

    monkeypatch.setattr(org_upgrade, "build_options_record", built)
    saved = org_upgrade_client.post(
        ORG_OPTIONS_API,
        json={
            "selected_types": ["ap", "switch", "gateway"],
            "version_ap": "0.15.1",
            "version_switch": "23.4R1.9",
            "version_gateway": "23.4R1.9",
            "strategy": "big_bang",
        },
    )
    assert saved.status_code == 200
    started = org_upgrade_client.post(ORG_SUBMIT_API, json={"confirmation": "CONFIRM"})
    repeated = org_upgrade_client.post(ORG_SUBMIT_API, json={"confirmation": "CONFIRM"})
    status = org_upgrade_client.get("/api/org-upgrades/org-run-contract")
    cancelled = org_upgrade_client.post(
        "/api/org-upgrades/org-run-contract/cancel",
        json={"confirmation": "CANCEL"},
    )
    assert started.get_json() == {"next": "/upgrade/org/jobs/org-run-contract"}
    assert repeated.status_code == 409
    assert boundary.submit_count == 1
    assert status.get_json()["status"] == "partial"
    assert {row["device_family"] for row in status.get_json()["children"]} == {"ap", "switch", "gateway"}
    assert cancelled.status_code == 200
    assert len(cancelled.get_json()["cancellation"]["results"]) == 3
    assert boundary.cancel_count == 1
    assert store.records["org-run-contract"]["children"][1]["error"] == "The switch child failed."
    assert store.records["org-run-contract"]["site_locks"] == {}  # A settled operation blocks no later work.
    assert lock.read_lock(fake_org_id, fake_site_id, select.lock_client()) is None  # The site accepts new work.


def test_settled_operation_releases_every_site_lock(
    org_upgrade_client: FlaskClient,
    monkeypatch: pytest.MonkeyPatch,
    fake_org_id: str,
    fake_site_id: str,
) -> None:
    """A completed operation frees each site it locked."""
    store = AggregateStoreStandIn()
    boundary = AggregateBoundaryStandIn()
    org_upgrade_client.application.config["RUN_STORE"] = store
    org_upgrade_client.application.config["AGGREGATE_UPGRADE_SERVICE"] = boundary
    devices = [{"mac": "001122334455", "name": "ap", "device_type": "ap", "model": "AP45"}]
    monkeypatch.setattr(org_upgrade, "build_options_view", lambda session, org_id, site_id: {"targets": devices})
    monkeypatch.setattr(
        org_upgrade,
        "build_options_record",
        lambda session, org_id, site_id, body: {
            "targets": [{**devices[0], "version_before": "old", "version_target": "0.15.1", "site_id": site_id}],
            "options": {"strategy": "big_bang", "reboot": True},
        },
    )
    saved = org_upgrade_client.post(
        ORG_OPTIONS_API, json={"selected_types": ["ap"], "version_ap": "0.15.1", "strategy": "big_bang"}
    )
    assert saved.status_code == 200
    started = org_upgrade_client.post(ORG_SUBMIT_API, json={"confirmation": "CONFIRM"})
    assert started.status_code == 200
    assert lock.read_lock(fake_org_id, fake_site_id, select.lock_client()) is not None  # The write holds the site.
    boundary.final_state = "completed"  # The next read finds every child finished.
    status = org_upgrade_client.get("/api/org-upgrades/org-run-contract")
    assert status.get_json()["status"] == "completed"
    assert store.records["org-run-contract"]["site_locks"] == {}  # The durable record holds no site.
    assert lock.read_lock(fake_org_id, fake_site_id, select.lock_client()) is None  # The site is free again.


def test_aggregate_summary_counts_nested_ap_site_targets() -> None:
    """Count AP outcomes from organization status entries."""
    record = {
        "operation_id": "org-run-1",
        "state": "running",
        "children": [
            {
                "child_id": "child-ap",
                "site_id": None,
                "site_name": "Site One, Site Two",
                "device_family": "ap",
                "route": "upgradeOrgDevices",
                "upgrade_id": "upgrade-ap",
                "status": "running",
                "target_ids": ["ap-1", "ap-2", "ap-3"],
                "status_data": {
                    "site_upgrades": [
                        {
                            "site_id": "11111111-1111-1111-1111-111111111111",
                            "upgrade": {
                                "id": "site-upgrade-1",
                                "status": "completed",
                                "targets": {"total": 2, "upgraded": ["ap-1", "ap-2"], "failed": []},
                            },
                        },
                        {
                            "site_id": "22222222-2222-2222-2222-222222222222",
                            "upgrade": {
                                "id": "site-upgrade-2",
                                "status": "failed",
                                "targets": {"total": 1, "upgraded": [], "failed": ["ap-3"]},
                            },
                        },
                    ]
                },
                "error": None,
                "cancellation": None,
            }
        ],
        "errors": [],
        "cancellation": {"requested": False, "results": []},
    }

    summary = org_upgrade.aggregate_summary(record)  # The public payload combines the nested AP results.

    assert summary["total"] == 3
    assert summary["upgraded_count"] == 2
    assert summary["failed_count"] == 1
    assert summary["site_upgrades"][0]["upgraded"] == 2
    assert summary["site_upgrades"][0]["failed"] == 1
    assert summary["status"] == "running"


def test_status_summary_derives_partial_from_nested_ap_states() -> None:
    """An active AP site keeps a failed sibling operation nonterminal."""
    result = OrgUpgradeResult(
        "org",
        UPGRADE_ID,
        200,
        {
            "upgrades": [
                {"site_id": "site-one", "upgrade": {"status": "running"}},
                {"site_id": "site-two", "status": "failed"},
            ]
        },
        None,
    )  # Supply no root status.
    summary = status_summary(result)  # Derive the state from both site entries.
    assert summary["status"] == "partial"  # Keep polling the active site.


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("site_ids", ["site-two", "site-one"]),
        ("request_nonce", "other-nonce"),
        ("operation_id", "other-operation"),
    ),
)
def test_aggregate_submission_context_requires_exact_durable_plan(field: str, value: object) -> None:
    """Site order, nonce, and operation identity must all match the durable plan."""
    context = org_upgrade.SubmissionContext(
        cloud_session=object(),
        org_id="org-one",
        site_ids=["site-one", "site-two"],
        options={"operation_id": "operation-one"},
        request_nonce="nonce-one",
    )  # Build the active confirmed context.
    operation = {
        "operation_id": "operation-one",
        "org_id": "org-one",
        "site_ids": ["site-one", "site-two"],
        "request_nonce": "nonce-one",
    }  # Build the matching durable identity.
    operation[field] = value  # Drift one protected value.
    assert org_upgrade._operation_matches_context(operation, context) is False  # Refuse before any claim.
