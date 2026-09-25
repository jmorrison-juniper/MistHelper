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

from src.firmware.aggregate_upgrade_service import AggregateBuildInput, AggregateUpgradeService
from src.firmware.org_upgrade_service import OrgUpgradeResult
from src.firmware.upgrade_service import DeviceTarget, UpgradeOptions
from src.upgrade_portal.app.routes import org_upgrade, select
from src.upgrade_portal.app.routes.org_upgrade import status_summary
from src.upgrade_portal.runtime import identity, lock
from src.upgrade_portal.upgrade.options import BadOptionError, build_options
from tests.support.lock_store_double import FakeLockStore
from tests.support.org_cascade_seams import CascadeSeamStandIn
from tests.support.org_precheck_seams import PrecheckAdopterStandIn

ORG_OPTIONS_PAGE = "/upgrade/org/options"
ORG_OPTIONS_API = "/api/org-upgrades/options"
ORG_CONFIRM_PAGE = "/upgrade/org/confirm"
ORG_SUBMIT_API = "/api/org-upgrades"
UPGRADE_ID = "33333333-3333-3333-3333-333333333333"
SITE_UPGRADE_ID = "44444444-4444-4444-4444-444444444444"
PROBE_EMAIL = "org-upgrade.operator@juniper.net"  # Issue #2615: a firmware write needs a reachable address.
RESERVED_EMAIL = "org-upgrade.operator@example.invalid"  # The reserved address that a firmware write must refuse.
CLOUD_ACCOUNT = "mist.account@juniper.net"  # Issue #3249: the account label behind the signed cloud session.
SECOND_SITE_ID = "55555555-5555-5555-5555-555555555555"  # Issue #3249: a second selected site.
AP_ONE = "001122334455"  # The access point at the first site.
AP_TWO = "001122334466"  # The access point at the second site.
SWITCH_ONE = "001122334477"  # The switch at the first site.


def test_request_source_empty_body_uses_form_mapping() -> None:
    """A zero-byte options body must fall back to the form mapping."""
    app = Flask(__name__)  # WHY: request parsing needs an application context.
    with app.test_request_context(ORG_OPTIONS_API, method="POST", data=b""):  # WHY: model an empty request body.
        result = org_upgrade.request_source()  # WHY: drive the product request parser.
    assert dict(result) == {}  # WHY: the route must continue to its explicit missing-option error.


def test_request_source_malformed_json_uses_form_mapping() -> None:
    """A malformed options body must fall back to the form mapping."""
    app = Flask(__name__)  # WHY: request parsing needs an application context.
    headers = {"Content-Type": "application/json"}  # WHY: force Flask to parse the body as JSON.
    with app.test_request_context(  # WHY: model a damaged browser JSON request.
        ORG_OPTIONS_API,
        method="POST",
        data="{not valid JSONDecodeError",
        headers=headers,
    ):
        result = org_upgrade.request_source()  # WHY: drive the product request parser.
    assert dict(result) == {}  # WHY: the route must continue to its explicit missing-option error.


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
        self.requests: list[Any] = []  # Store build inputs so safety tests can inspect validated options.
        self.final_state = ""  # An empty value keeps the mixed status answer below.

    def build(self, request: Any) -> dict[str, Any]:
        """Build three child rows for the selected device families."""
        self.requests.append(request)  # Record the validated input before this stand-in builds child rows.
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

    def record_device_versions(
        self,
        record: dict[str, Any],
        store: Any,
        readings: dict[str, str],
        final_child_ids: tuple[str, ...],
    ) -> dict[str, Any]:
        """Merge the running version readings, as the production service does."""
        versions = record.setdefault("device_versions", {})  # Keep each earlier reading.
        for mac, version in readings.items():  # Store each new reading under its MAC address.
            versions[mac] = {"version": version, "reads": 1}
        record["versions_final"] = [*record.get("versions_final", []), *final_child_ids]  # Close each child.
        store.write_run(record)
        return record


class VersionReaderStandIn:
    """Answer the running versions of each site, and record every site read."""

    def __init__(self) -> None:
        """Start with no answer and no read."""
        self.answers: dict[str, dict[str, str]] = {}  # A test fills the answer of each site.
        self.calls: list[str] = []  # Each entry names one site read.

    def __call__(self, cloud_session: Any, site_id: str) -> dict[str, str]:
        """Record the site read and return its fixed answer."""
        del cloud_session  # The stand-in opens no socket.
        self.calls.append(site_id)
        return dict(self.answers.get(site_id, {}))


class QuietAggregateService(AggregateUpgradeService):
    """Keep the production version store, and read no child job."""

    def status(self, cloud_session: Any, record: Any, store: Any) -> Any:
        """Return the stored record as it is."""
        del cloud_session, store  # The test record already holds the cloud answers.
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
    portal_app.config[org_upgrade.DEVICE_VERSION_READER_CONFIG_KEY] = VersionReaderStandIn()  # No stats read.
    CascadeSeamStandIn().install(portal_app.config)  # Issue #3245: no anchor read and no watch thread.
    PrecheckAdopterStandIn((fake_site_id, SECOND_SITE_ID)).install(portal_app.config)  # Issue #3243: each pre-check.
    portal_app.config["MIST_SELF_READER"] = lambda cloud_session: {"email": CLOUD_ACCOUNT}  # No self read.
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
    assert b'data-testid="org-upgrade-reboot-at"' in answer.data
    assert b"Reboot each switch and each gateway after this much time" in answer.data
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


@pytest.mark.parametrize("phases", ["50,10", "10,101", "10,50", "0,100"])
def test_multidevice_invalid_canary_phases_build_no_plan(
    org_upgrade_client: FlaskClient,
    monkeypatch: pytest.MonkeyPatch,
    phases: str,
) -> None:
    """Issue #3223: the current multi-device form refuses phases that do not rise from 1 to 100."""
    store = AggregateStoreStandIn()  # A plan must never reach this store.
    boundary = AggregateBoundaryStandIn()  # A plan build records its request here.
    org_upgrade_client.application.config["RUN_STORE"] = store
    org_upgrade_client.application.config["AGGREGATE_UPGRADE_SERVICE"] = boundary
    devices = [{"mac": "001122334455", "name": "ap", "device_type": "ap", "model": "AP45"}]  # One AP target.
    monkeypatch.setattr(org_upgrade, "build_options_view", lambda session, org_id, site_id: {"targets": devices})
    monkeypatch.setattr(
        org_upgrade,
        "build_options_record",
        lambda session, org_id, site_id, body: {  # Pass the submitted phases through, as the shipped mapper does.
            "targets": [{**devices[0], "version_before": "old", "version_target": "0.15.1", "site_id": site_id}],
            "options": {key: body[key] for key in ("strategy", "canary_phases") if key in body},
        },
    )
    answer = org_upgrade_client.post(
        ORG_OPTIONS_API,
        json={
            "selected_types": ["ap"],  # The current page always sends the family list.
            "version_ap": "0.15.1",
            "strategy": "canary",
            "canary_phases": phases,
            "max_failure_percentage": "5",
        },
    )
    assert answer.status_code == 400  # The options step refuses the phases.
    assert answer.get_json()["error"]["code"] == "org_upgrade_options_invalid"
    assert boundary.requests == []  # No plan was built, so no child can carry the phases.


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


def test_options_view_restores_multisite_saved_choices() -> None:
    """The options page reads every saved choice after Back."""
    view = org_upgrade.options_view(  # Build the same display record that the route sends to the template.
        {
            "selected_types": ["ap", "switch"],
            "version_ap": "0.15.1",
            "version_switch": "23.4R1.9",
            "version_gateway": "23.4R1.9",
            "strategy": "big_bang",
            "reboot": False,
            "junos_file_action": False,
            "force": True,
        }
    )
    assert view["selected_types"] == ["ap", "switch"]  # The cleared gateway box must stay cleared.
    assert view["reboot"] is False  # The No reboot choice must survive a return from confirmation.
    assert view["junos_file_action"] is False  # The No Junos action choice must survive.
    assert view["force"] is True  # The force checkbox must survive.


def test_bad_option_message_names_the_page_label_and_model() -> None:
    """A version refusal must name the page label, not an internal field."""
    error = BadOptionError("version_target", model="EX4400")  # Build the refusal raised by target validation.
    message = str(error)  # Read the operator text that the route returns.
    assert "Target version" in message  # The operator sees this label on the options page.
    assert "EX4400" in message  # The operator needs the model that refused the version.
    assert "version_target" not in message  # An internal field name does not help the operator.


# One access point and one switch at the stand-in site, in the shape of the options view. Issue #3273.
FAMILY_VIEW_ROWS = [
    {"mac": "001122334455", "name": "ap", "device_type": "ap", "model": "AP45"},
    {"mac": "001122334466", "name": "switch", "device_type": "switch", "model": "EX4400"},
]


def refused_message(client: FlaskClient, body: dict[str, Any]) -> str:
    """Post one multi-site option body, and return the refusal text that the flash message shows."""
    answer = client.post(ORG_OPTIONS_API, json=body)  # Save the options through the JSON contract.
    assert answer.status_code == 400  # The route must refuse the body before the confirmation step.
    payload = answer.get_json()  # Read the structured refusal.
    assert payload["error"]["code"] == "org_upgrade_options_invalid"  # Keep the existing route error code.
    return str(payload["error"]["message"])  # Return the text that the operator reads.


def family_view(session: Any, org_id: str, site_id: str) -> dict[str, Any]:
    """Return the device rows of the stand-in site, in the shape of the options view."""
    return {"targets": FAMILY_VIEW_ROWS}  # Each selected site answers with the same two devices.


def test_a_refused_switch_version_names_the_switch_control(
    org_upgrade_client: FlaskClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Issue #3273: a model refusal names the family control that the multi-site page paints."""
    monkeypatch.setattr(org_upgrade, "build_options_view", family_view)  # Keep the inventory read offline.

    def refused(session: Any, org_id: str, site_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Refuse the switch version as the shared target validator does."""
        raise BadOptionError("version_target", model="EX4400")

    monkeypatch.setattr(org_upgrade, "build_options_record", refused)  # Keep the test offline.
    message = refused_message(
        org_upgrade_client,
        {"selected_types": ["ap", "switch"], "version_ap": "0.15.1", "version_switch": "23.4R1.9"},
    )
    assert '"Switch target version"' in message  # The multi-site page paints this label.
    assert "EX4400" in message  # The operator needs the model that refused the version.
    assert '"Target version"' not in message  # The multi-site page paints no control with this label.
    assert "version_target" not in message  # An internal field name does not help the operator.
    assert "23.4R1.9" not in message  # No refusal repeats the typed value.


@pytest.mark.parametrize(
    ("field", "value", "label"),
    [
        ("canary_phases", "1,10,fifty,100", "Canary phases"),
        ("max_failure_percentage", "five", "Maximum failure percentage"),
        ("start_time", "not-a-moment", "Start time (UTC)"),
    ],
)
def test_an_unreadable_value_names_the_multisite_control(
    org_upgrade_client: FlaskClient,
    field: str,
    value: str,
    label: str,
) -> None:
    """Issue #3273: a value that the route cannot read names its control and never repeats the value."""
    body = {  # Start from a valid canary body, then break one field.
        "selected_types": ["switch"],
        "version_switch": "23.4R1.9",
        "strategy": "canary",
        "canary_phases": "1,10,50,100",
        "max_failure_percentage": "5",
        field: value,
    }
    message = refused_message(org_upgrade_client, body)  # The route refuses before any inventory read.
    assert f'"{label}"' in message  # The multi-site page paints this label.
    assert value not in message  # No refusal repeats the typed value.
    assert "invalid literal" not in message  # The parser text of Python never reaches the operator.
    assert "isoformat" not in message  # The date parser text never reaches the operator.


def test_a_past_start_time_names_the_multisite_control(
    org_upgrade_client: FlaskClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Issue #3273: the shared guard refuses a past start, and the text names the multi-site control."""
    monkeypatch.setattr(org_upgrade, "build_options_view", family_view)  # Keep the inventory read offline.

    def guarded(session: Any, org_id: str, site_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Run the shared option mapper, which refuses a start time in the past."""
        build_options(body)  # The shared guard raises for the past moment.
        raise AssertionError("The shared guard accepted a start time in the past.")

    monkeypatch.setattr(org_upgrade, "build_options_record", guarded)  # Keep the inventory read offline.
    message = refused_message(
        org_upgrade_client,
        {
            "selected_types": ["switch"],
            "version_switch": "23.4R1.9",
            "strategy": "big_bang",
            "start_time": "2020-01-01T00:00",
        },
    )
    assert '"Start time (UTC)"' in message  # The multi-site page paints this label.
    assert "Begin the firmware download" not in message  # The single-site label names no multi-site control.
    assert "Write a number and a unit" not in message  # The multi-site control holds a date and a time.


def test_a_shared_mapper_refusal_names_the_multisite_label(
    org_upgrade_client: FlaskClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Issue #3273: a refusal from the shared mapper names the label of the multi-site page."""
    monkeypatch.setattr(org_upgrade, "build_options_view", family_view)  # Keep the inventory read offline.

    def refused(session: Any, org_id: str, site_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Refuse the failure limit with the single-site label, as the shared mapper does."""
        raise BadOptionError("max_failure_percentage")

    monkeypatch.setattr(org_upgrade, "build_options_record", refused)  # Keep the test offline.
    message = refused_message(
        org_upgrade_client,
        {"selected_types": ["switch"], "version_switch": "23.4R1.9", "strategy": "serial"},
    )
    assert '"Maximum failure percentage"' in message  # The multi-site page paints this label.
    assert "Failures allowed across the whole run" not in message  # The single-site label is absent.


def test_no_typed_target_names_a_multisite_control(
    org_upgrade_client: FlaskClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Issue #3273: a request with no typed target names a control that the multi-site page paints."""
    monkeypatch.setattr(org_upgrade, "build_options_view", family_view)  # Keep the inventory read offline.
    monkeypatch.setattr(  # Each site answers with no target, as the shared mapper does for no choice.
        org_upgrade,
        "build_options_record",
        lambda session, org_id, site_id, body: {"targets": [], "options": {"strategy": "big_bang"}},
    )
    message = refused_message(
        org_upgrade_client,
        {"selected_types": ["switch"], "version_switch": "", "strategy": "big_bang"},
    )
    assert '"Device types to upgrade"' in message  # The multi-site page paints this legend.
    assert "Target version control" not in message  # The multi-site page paints no control with this label.


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
    fake_org_id: str,
) -> None:
    """The status paths show the organization and site job states."""
    with org_upgrade_client.session_transaction() as browser_session:  # This browser started the job.
        browser_session["org_upgrade_last_job"] = {"upgrade_id": UPGRADE_ID, "org_id": fake_org_id}
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


@pytest.mark.parametrize("path", [f"/upgrade/org/jobs/{UPGRADE_ID}", f"/api/org-upgrades/{UPGRADE_ID}"])
def test_a_job_of_another_browser_is_refused_with_no_cloud_read(
    org_upgrade_client: FlaskClient,
    org_service: OrgUpgradeServiceStandIn,
    path: str,
) -> None:
    """Issue #3241: the page and the poll refuse a job that this browser session did not start."""
    answer = org_upgrade_client.get(path)  # No signed marker names this job.
    assert answer.status_code == 409  # The same refusal as the cancel route.
    assert answer.get_json()["error"]["code"] == "org_upgrade_job_not_owned"  # The documented code.
    assert org_service.calls == []  # The portal read no cloud job for a job that it does not own.


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


@pytest.mark.parametrize("state", ["cancelled", "completed", "failed"])
def test_cancellation_refuses_a_final_organization_job_with_no_cloud_call(
    org_upgrade_client: FlaskClient,
    org_service: OrgUpgradeServiceStandIn,
    fake_org_id: str,
    state: str,
) -> None:
    """Issue #3225: an organization job in a final state offers no cancel and sends no cancel request."""
    org_service.job_status = state  # The cloud reports the final state.
    with org_upgrade_client.session_transaction() as browser_session:  # This browser started the job.
        browser_session["org_upgrade_last_job"] = {"upgrade_id": UPGRADE_ID, "org_id": fake_org_id, "site_count": 1}
    page = org_upgrade_client.get(f"/upgrade/org/jobs/{UPGRADE_ID}").get_data(as_text=True)  # Stores the state.
    answer = org_upgrade_client.post(f"/api/org-upgrades/{UPGRADE_ID}/cancel", json={"confirmation": "CANCEL"})
    assert (answer.status_code, answer.get_json()["error"]["code"]) == (409, "org_upgrade_not_cancellable")
    assert (
        answer.get_json()["error"]["message"] == f"The operation is final: {state}. The portal sent no cancel request."
    )
    assert [call[0] for call in org_service.calls] == ["status"]  # The page read only. No cancel call left.
    assert 'data-testid="org-upgrade-cancel-confirmation"' not in page  # The page offered no cancel form.


def test_the_organization_job_rows_name_the_access_point_family(
    org_upgrade_client: FlaskClient,
    fake_org_id: str,
) -> None:
    """Issue #3225: the organization job upgrades access points only, so each row names that family."""
    with org_upgrade_client.session_transaction() as browser_session:  # This browser started the job.
        browser_session["org_upgrade_last_job"] = {"upgrade_id": UPGRADE_ID, "org_id": fake_org_id}
    answer = org_upgrade_client.get(f"/api/org-upgrades/{UPGRADE_ID}").get_json()  # The poll of a live job.
    assert [row["device_family"] for row in answer["site_upgrades"]] == ["ap"]  # The server names the family.
    assert answer["cancel_allowed"] is True  # The cloud word "inprogress" is a live state.


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
    # WHY: Issue #3220. A cancel request does not stop a device that already
    # writes firmware, and the gateway child still runs, so both sites stay held.
    assert store.records["org-run-contract"]["site_locks"] != {}  # A running child keeps the site.
    held = lock.read_lock(fake_org_id, fake_site_id, select.lock_client())  # The lock of the running operation.
    assert isinstance(held, lock.LockRecord) and held.run_id == "org-run-contract"  # No new work can start.
    boundary.final_state = "cancelled"  # The next read finds every child past any write.
    org_upgrade_client.get("/api/org-upgrades/org-run-contract")  # The status read releases the sites.
    assert store.records["org-run-contract"]["site_locks"] == {}  # A settled operation blocks no later work.
    assert lock.read_lock(fake_org_id, fake_site_id, select.lock_client()) is None  # The site accepts new work.


def test_multidevice_reboot_delay_reaches_the_confirmed_options(
    org_upgrade_client: FlaskClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The multi-site path stores the same reboot delay field as the single-site path."""
    store = AggregateStoreStandIn()  # Hold the aggregate plan without a database.
    boundary = AggregateBoundaryStandIn()  # Capture the build input without a cloud write.
    org_upgrade_client.application.config["RUN_STORE"] = store  # Route aggregate plans to the test store.
    org_upgrade_client.application.config["AGGREGATE_UPGRADE_SERVICE"] = boundary  # Stop before the cloud seam.
    devices = [{"mac": "001122334466", "name": "switch", "device_type": "switch", "model": "EX4400"}]  # Use one switch.
    monkeypatch.setattr(org_upgrade, "build_options_view", lambda session, org_id, site_id: {"targets": devices})

    def built(session: Any, org_id: str, site_id: str, body: dict[str, Any]) -> dict[str, Any]:
        """Return a validated option record that preserves the submitted reboot delay."""
        target = {  # Build the target that the aggregate service will plan.
            **devices[0],
            "version_before": "old",
            "version_target": body["targets"][0]["version_target"],
            "site_id": site_id,
        }
        options = {"strategy": "big_bang", "reboot": True, "reboot_at": body["reboot_at"]}  # Preserve the field.
        return {"targets": [target], "options": options}  # Return the same shape as the production mapper.

    monkeypatch.setattr(org_upgrade, "build_options_record", built)  # Keep the test offline and deterministic.
    saved = org_upgrade_client.post(  # Save the multi-device options with the new reboot delay.
        ORG_OPTIONS_API,
        json={
            "selected_types": ["switch"],
            "version_switch": "23.4R1.9",
            "strategy": "big_bang",
            "reboot_at": "8h",
        },
    )
    page = org_upgrade_client.get(ORG_CONFIRM_PAGE)  # Read the confirmation that the operator sees.
    with org_upgrade_client.session_transaction() as browser_session:  # Inspect the signed browser session.
        saved_options = dict(browser_session["org_upgrade_options"])  # Detach the session record for assertions.
    assert saved.status_code == 200  # The valid delay must not block the save.
    assert saved_options["reboot_at"] == "8h"  # The route stores the same field name and duration units.
    reboot_at = boundary.requests[0].options.reboot_at  # The value that the service sends to the cloud.
    assert isinstance(reboot_at, int) and reboot_at > 0  # The service receives an epoch value for the cloud.
    assert b'data-testid="org-upgrade-reboot-at"' in page.data  # The confirmation names the reboot delay.
    assert b"8h" in page.data  # The operator sees the same duration they entered.


def test_multidevice_without_reboot_delay_preserves_current_behavior(
    org_upgrade_client: FlaskClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An empty reboot delay keeps the existing immediate-reboot behavior."""
    boundary = AggregateBoundaryStandIn()  # Capture the build input without a cloud write.
    org_upgrade_client.application.config["RUN_STORE"] = AggregateStoreStandIn()  # Hold the plan in memory.
    org_upgrade_client.application.config["AGGREGATE_UPGRADE_SERVICE"] = boundary  # Stop before submission.
    devices = [{"mac": "001122334466", "name": "switch", "device_type": "switch", "model": "EX4400"}]  # Use one switch.
    monkeypatch.setattr(org_upgrade, "build_options_view", lambda session, org_id, site_id: {"targets": devices})
    monkeypatch.setattr(  # Return a production-shaped record that has no reboot_at field.
        org_upgrade,
        "build_options_record",
        lambda session, org_id, site_id, body: {
            "targets": [{**devices[0], "version_before": "old", "version_target": "23.4R1.9", "site_id": site_id}],
            "options": {"strategy": "big_bang", "reboot": True},
        },
    )
    saved = org_upgrade_client.post(  # Save the multi-device options without the new control.
        ORG_OPTIONS_API,
        json={"selected_types": ["switch"], "version_switch": "23.4R1.9", "strategy": "big_bang"},
    )
    assert saved.status_code == 200  # Empty delay must keep the existing successful path.
    assert boundary.requests[0].options.reboot_at is None  # The cloud body keeps its immediate-reboot default.


def test_past_multidevice_reboot_delay_is_refused(org_upgrade_client: FlaskClient) -> None:
    """A past reboot delay must not fall back to an immediate reboot."""
    answer = org_upgrade_client.post(  # Submit an old epoch value through the same field name.
        ORG_OPTIONS_API,
        json={
            "selected_types": ["switch"],
            "version_switch": "23.4R1.9",
            "strategy": "big_bang",
            "reboot_at": "1000000000",
        },
    )
    payload = answer.get_json()  # Read the refusal as structured JSON.
    assert answer.status_code == 400  # The route must fail closed before the confirmation page.
    assert payload["error"]["code"] == "org_upgrade_options_invalid"  # Keep the existing route error code.
    assert "Reboot each switch and each gateway after this much time" in payload["error"]["message"]  # Name control.


def test_aggregate_service_applies_reboot_delay_to_each_selected_site() -> None:
    """Each selected non-AP site child receives the same reboot_at epoch seconds."""
    service = AggregateUpgradeService()  # Use the production aggregate planner.
    moment = 1_900_028_800  # Use a fixed epoch value so the assertion is deterministic.
    request = AggregateBuildInput(  # Build a multi-site request without a cloud session.
        owner="operator",
        org_id="org",
        sites=[{"site_id": "site-one", "name": "Site One"}, {"site_id": "site-two", "name": "Site Two"}],
        targets=[
            DeviceTarget("001122334466", "switch-one", "switch", "EX4400", "old", "23.4R1.9", "site-one"),
            DeviceTarget("001122334477", "switch-two", "switch", "EX4400", "old", "23.4R1.9", "site-two"),
        ],
        options=UpgradeOptions(reboot=True, reboot_at=moment),
        request_nonce="nonce",
    )
    record = service.build(request)  # Plan the aggregate record with no cloud write.
    site_children = [child for child in record["children"] if child["scope"] == "site"]  # Inspect non-AP children.
    assert len(site_children) == 2  # The planner must keep both selected sites.
    assert {child["site_id"] for child in site_children} == {"site-one", "site-two"}  # No site may lose the delay.
    assert {child["body"]["reboot_at"] for child in site_children} == {moment}  # The cloud body uses epoch seconds.
    assert {child["reboot_at"] for child in site_children} == {moment}  # The durable child stores the same field.


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
    held = lock.read_lock(fake_org_id, fake_site_id, select.lock_client())  # The lock that the write took.
    assert isinstance(held, lock.LockRecord) and held.run_id == "org-run-contract"  # The write holds the site.
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


def test_a_reserved_operator_address_cannot_start_a_multi_site_upgrade(
    org_upgrade_client: FlaskClient,
    org_service: OrgUpgradeServiceStandIn,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A reserved operator address refuses the multi-site firmware write.

    Why:
        Issue #2615. A multi-site upgrade writes firmware to every selected
        site, so it reaches far more devices than a single-site run. A reserved
        domain such as `.invalid` reaches no mailbox, so no person can answer
        for that write. The portal must refuse the write before any cloud call.

    Args:
        org_upgrade_client: The signed multi-site client.
        org_service: The stand-in that records every submitted job.
        monkeypatch: The fixture that replaces the owner reader.
    """
    save_valid_options(org_upgrade_client)  # Reach the confirmed state that the submit route needs.
    reserved_owner = identity.build_owner(RESERVED_EMAIL, identity.issue_browser_id())  # An unreachable operator.
    monkeypatch.setattr(org_upgrade.identity, "current_owner", lambda: reserved_owner)  # Change only the address.
    before = len(org_service.calls)  # Record the call count, so the refusal can prove it sent nothing.

    answer = org_upgrade_client.post(  # Send the confirmed multi-site write.
        ORG_SUBMIT_API,
        json={"confirmation": "CONFIRM"},
        headers={"X-Requested-With": "XMLHttpRequest"},
    )

    assert answer.status_code == 400, "A reserved operator address must refuse the multi-site firmware write."
    body = answer.get_json() or {}  # Read the refusal envelope that the contract fixes.
    assert body.get("error", {}).get("code") == "unreachable_operator_address"  # Name the exact refusal code.
    assert len(org_service.calls) == before, "The refusal must reach no cloud service at all."


def table_target(mac: str, device_type: str, site_id: str, version: str) -> dict[str, str]:
    """Build one stored target record of the device table test."""
    return {
        "mac": mac,
        "name": f"{device_type}-{mac[-2:]}",
        "device_type": device_type,
        "model": "AP45" if device_type == "ap" else "EX4400",
        "version_before": "0.14.1" if device_type == "ap" else "23.4R1.8",
        "version_target": version,
        "site_id": site_id,
    }


def device_table_record(owner: str, org_id: str, site_id: str) -> dict[str, Any]:
    """Build one finished operation with an access point at each site and one switch."""
    ap_status = {
        "site_upgrades": [
            {"site_id": site_id, "upgrade": {"targets": {"upgraded": [AP_ONE]}}},
            {"site_id": SECOND_SITE_ID, "upgrade": {"targets": {"failed": [AP_TWO]}}},
        ]
    }
    ap_child = {
        "child_id": "child-ap",
        "route": "upgradeOrgDevices",
        "site_id": None,
        "site_name": "Site One, Site Two",
        "device_family": "ap",
        "status": "failed",
        "target_ids": [AP_ONE, AP_TWO],
        "targets": [
            table_target(AP_ONE, "ap", site_id, "0.15.1"),
            table_target(AP_TWO, "ap", SECOND_SITE_ID, "0.15.1"),
        ],
        "status_data": ap_status,
        "error": None,
        "cancellation": None,
    }
    switch_child = {
        "child_id": "child-switch",
        "route": "upgradeSiteDevices",
        "site_id": site_id,
        "site_name": "Site One",
        "device_family": "switch",
        "status": "completed",
        "target_ids": [SWITCH_ONE],
        "targets": [table_target(SWITCH_ONE, "switch", site_id, "23.4R1.9")],
        "status_data": {"targets": {"upgraded": [SWITCH_ONE]}},
        "error": None,
        "cancellation": None,
    }
    return {
        "_key": "org-run-devices",
        "run_id": "org-run-devices",
        "operation_id": "org-run-devices",
        "owner": owner,
        "org_id": org_id,
        "site_ids": [site_id, SECOND_SITE_ID],
        "record_version": 0,
        "state": "failed",
        "site_names": {site_id: "Site One", SECOND_SITE_ID: "Site Two"},
        "device_versions": {},
        "versions_final": [],
        "updated_at": "2026-09-24T01:00:00+00:00",
        "actor_email": PROBE_EMAIL,
        "cloud_account": CLOUD_ACCOUNT,
        "site_locks": {},
        "children": [ap_child, switch_child],
        "errors": [],
        "cancellation": {"requested": False, "results": []},
    }


def test_the_multisite_page_shows_one_row_for_each_device(
    org_upgrade_client: FlaskClient,
    fake_org_id: str,
    fake_site_id: str,
) -> None:
    """Issue #3249: each device shows its site, its state, its versions, and its version check.

    Why:
        The single-site page shows one row for each device. The multi-site
        page showed counts only, so an operator could not see which device
        failed or which firmware each device runs after the upgrade.
    """
    store = AggregateStoreStandIn()  # Hold the finished operation without a database.
    org_upgrade_client.application.config["RUN_STORE"] = store
    org_upgrade_client.application.config["AGGREGATE_UPGRADE_SERVICE"] = QuietAggregateService()
    reader = org_upgrade_client.application.config[org_upgrade.DEVICE_VERSION_READER_CONFIG_KEY]
    reader.answers = {fake_site_id: {AP_ONE: "0.15.1", SWITCH_ONE: "23.4R1.8"}, SECOND_SITE_ID: {AP_TWO: "0.14.1"}}
    with org_upgrade_client.session_transaction() as browser_session:
        owner_key = browser_session[identity.SESSION_OWNER_KEY]  # The operation belongs to this browser.
    store.write_run(device_table_record(owner_key, fake_org_id, fake_site_id))

    page = org_upgrade_client.get("/upgrade/org/jobs/org-run-devices")

    assert page.status_code == 200
    text = page.get_data(as_text=True)
    assert 'data-testid="org-upgrade-device-table"' in text
    assert f'data-testid="org-upgrade-device-row-{AP_ONE}"' in text
    assert f'data-testid="org-upgrade-device-row-{AP_TWO}"' in text
    assert f'data-testid="org-upgrade-device-row-{SWITCH_ONE}"' in text
    assert "Site Two" in text
    assert text.count("Version matches") == 1  # The access point at the first site runs the target.
    assert text.count("Version mismatch") == 2  # The failed access point and the switch run other firmware.
    assert "The cloud lists this device as failed." in text
    assert PROBE_EMAIL in text and CLOUD_ACCOUNT in text  # The page names who started the operation.
    assert 'data-testid="org-upgrade-last-update-age"' in text
    assert sorted(reader.calls) == sorted([fake_site_id, SECOND_SITE_ID])  # One read for each site.

    polled = org_upgrade_client.get("/api/org-upgrades/org-run-devices")

    body = polled.get_json()
    assert len(reader.calls) == 2  # SC-002: a finished operation causes no second read.
    assert {row["mac"]: row["version_after"] for row in body["devices"]} == {
        AP_ONE: "0.15.1",
        AP_TWO: "0.14.1",
        SWITCH_ONE: "23.4R1.8",
    }
    assert {row["mac"]: row["site_name"] for row in body["devices"]}[AP_TWO] == "Site Two"
    assert (body["operator_address"], body["cloud_account"]) == (PROBE_EMAIL, CLOUD_ACCOUNT)
    assert body["updated_at"] and body["age_text"] != "unknown"  # The record change set a fresh time.


def test_the_multisite_submission_records_the_operator_and_the_account(
    org_upgrade_client: FlaskClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Issue #3249: the multi-site record keeps the typed address and the Mist account, as a run does."""
    store = AggregateStoreStandIn()  # Hold the plan without a database.
    boundary = AggregateBoundaryStandIn()  # Stop before the cloud seam.
    org_upgrade_client.application.config["RUN_STORE"] = store
    org_upgrade_client.application.config["AGGREGATE_UPGRADE_SERVICE"] = boundary
    devices = [{"mac": AP_ONE, "name": "ap", "device_type": "ap", "model": "AP45"}]
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
    stored = store.records["org-run-contract"]
    assert (stored["actor_email"], stored["cloud_account"]) == (PROBE_EMAIL, CLOUD_ACCOUNT)
    page = org_upgrade_client.get("/upgrade/org/jobs/org-run-contract")
    assert PROBE_EMAIL in page.get_data(as_text=True)
    assert CLOUD_ACCOUNT in page.get_data(as_text=True)


def test_the_operator_record_write_failure_stops_before_any_lock(
    org_upgrade_client: FlaskClient,
    monkeypatch: pytest.MonkeyPatch,
    fake_org_id: str,
    fake_site_id: str,
) -> None:
    """A stale record refuses the write before the portal takes a site lock or calls the cloud."""
    store = AggregateStoreStandIn()  # Hold the plan without a database.
    boundary = AggregateBoundaryStandIn()  # Stop before the cloud seam.
    org_upgrade_client.application.config["RUN_STORE"] = store
    org_upgrade_client.application.config["AGGREGATE_UPGRADE_SERVICE"] = boundary
    devices = [{"mac": AP_ONE, "name": "ap", "device_type": "ap", "model": "AP45"}]
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
    monkeypatch.setattr(store, "compare_and_set_run", lambda run_id, expected, replacement: False)

    started = org_upgrade_client.post(ORG_SUBMIT_API, json={"confirmation": "CONFIRM"})

    assert started.status_code == 503
    assert started.get_json()["error"]["code"] == "org_upgrade_submission_failed"
    assert boundary.submit_count == 0  # No child reached the cloud.
    assert lock.read_lock(fake_org_id, fake_site_id, select.lock_client()) is None  # No site lock exists.


# --------------------------------------------------------------------------
# Issue #3242: the refusal of a repeated start names the job that started.
# --------------------------------------------------------------------------

REPLAY_CODE = "org_upgrade_already_submitted"  # The code of each refusal of a repeated start.
AGGREGATE_ID = "org-run-contract"  # The operation identifier of `AggregateBoundaryStandIn.build`.
LEGACY_SENTENCE = "This confirmed request already started an organization upgrade."  # The access point path.
AGGREGATE_SENTENCE = "This confirmed request already started a multi-site upgrade."  # The durable path.
UNKNOWN_SENTENCE = (  # The legacy path after a cloud answer that named no job.
    "The cloud response to the last organization upgrade request is unknown. "
    "Reconcile the job history before another submission."
)
WRITE_SESSION_REFUSAL = "Use an OrgUpgradeSession with SDK write retries disabled."  # A service refusal of no job.


class RefusingBoundaryStandIn(AggregateBoundaryStandIn):
    """Refuse each submission as `check_write_session` does, and change no child."""

    def submit(self, cloud_session: Any, record: dict[str, Any], store: Any, refresh_lock: Any) -> dict[str, Any]:
        """Raise the refusal of a cloud session that can retry a write."""
        del cloud_session, record, store, refresh_lock  # The refusal comes before any claim.
        raise ValueError(WRITE_SESSION_REFUSAL)


def save_durable_ap_plan(
    client: FlaskClient, monkeypatch: pytest.MonkeyPatch, boundary: AggregateBoundaryStandIn
) -> AggregateStoreStandIn:
    """Install the aggregate stand-ins, and save one access point plan through the options route.

    Args:
        client: The signed client of the operator.
        monkeypatch: The pytest helper that replaces the device reads.
        boundary: The aggregate service stand-in of the test.

    Returns:
        The store that holds the durable plan.
    """
    store = AggregateStoreStandIn()  # Hold the plan without a database.
    client.application.config["RUN_STORE"] = store  # Route the plan to the test store.
    client.application.config["AGGREGATE_UPGRADE_SERVICE"] = boundary  # Stop before the cloud seam.
    devices = [{"mac": AP_ONE, "name": "ap", "device_type": "ap", "model": "AP45"}]  # One access point.
    monkeypatch.setattr(org_upgrade, "build_options_view", lambda session, org_id, site_id: {"targets": devices})
    monkeypatch.setattr(
        org_upgrade,
        "build_options_record",
        lambda session, org_id, site_id, body: {
            "targets": [{**devices[0], "version_before": "old", "version_target": "0.15.1", "site_id": site_id}],
            "options": {"strategy": "big_bang", "reboot": True},
        },
    )
    body = {"selected_types": ["ap"], "version_ap": "0.15.1", "strategy": "big_bang"}  # One access point plan.
    saved = client.post(ORG_OPTIONS_API, json=body)  # The options route saves the durable plan.
    assert saved.status_code == 200  # The durable plan exists.
    return store  # The caller reads the plan after the submission.


def test_a_legacy_replay_names_the_job_that_started(org_upgrade_client: FlaskClient) -> None:
    """FR-003 and FR-004: the access point path links the cloud job of the browser marker."""
    save_valid_options(org_upgrade_client)  # The legacy access point plan.
    first = org_upgrade_client.post(ORG_SUBMIT_API, json={"confirmation": "CONFIRM"})
    second = org_upgrade_client.post(ORG_SUBMIT_API, json={"confirmation": "CONFIRM"})

    error = second.get_json()["error"]
    assert first.status_code == 200  # The first request started the job.
    assert (second.status_code, error["code"], error["message"]) == (409, REPLAY_CODE, LEGACY_SENTENCE)
    assert error["details"] == {"upgrade_id": UPGRADE_ID, "next": f"/upgrade/org/jobs/{UPGRADE_ID}"}


def test_a_legacy_replay_after_an_unknown_answer_names_no_job(org_upgrade_client: FlaskClient) -> None:
    """FR-005: a marker with no job gets the sentence about the unknown answer and no link."""

    class UnknownService:
        @staticmethod
        def submit(cloud_session: Any, org_id: str, body: dict[str, object]) -> OrgUpgradeResult:
            raise RuntimeError("connection ended after the write")

    org_upgrade_client.application.config["ORG_UPGRADE_SERVICE"] = UnknownService
    save_valid_options(org_upgrade_client)  # The legacy access point plan.
    first = org_upgrade_client.post(ORG_SUBMIT_API, json={"confirmation": "CONFIRM"})
    second = org_upgrade_client.post(ORG_SUBMIT_API, json={"confirmation": "CONFIRM"})

    error = second.get_json()["error"]
    assert first.status_code == 503  # The cloud answer is unknown.
    assert (second.status_code, error["code"], error["message"]) == (409, REPLAY_CODE, UNKNOWN_SENTENCE)
    assert "details" not in error  # No code knows the job, so the page links to nothing.


def test_a_durable_replay_names_the_operation_that_runs(
    org_upgrade_client: FlaskClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-003 and FR-004: the aggregate path links the operation of the saved plan."""
    boundary = AggregateBoundaryStandIn()  # The first submission touches each child.
    save_durable_ap_plan(org_upgrade_client, monkeypatch, boundary)
    started = org_upgrade_client.post(ORG_SUBMIT_API, json={"confirmation": "CONFIRM"})
    repeated = org_upgrade_client.post(ORG_SUBMIT_API, json={"confirmation": "CONFIRM"})

    error = repeated.get_json()["error"]
    assert started.get_json() == {"next": f"/upgrade/org/jobs/{AGGREGATE_ID}"}  # The first request started it.
    assert (repeated.status_code, error["code"], error["message"]) == (409, REPLAY_CODE, AGGREGATE_SENTENCE)
    assert error["details"] == {"upgrade_id": AGGREGATE_ID, "next": f"/upgrade/org/jobs/{AGGREGATE_ID}"}
    assert boundary.submit_count == 1  # No child went to the cloud again.


def test_a_refusal_of_an_untouched_plan_names_no_job(
    org_upgrade_client: FlaskClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FR-004: a service refusal that started no job keeps its text and gets no link."""
    store = save_durable_ap_plan(org_upgrade_client, monkeypatch, RefusingBoundaryStandIn())
    refused = org_upgrade_client.post(ORG_SUBMIT_API, json={"confirmation": "CONFIRM"})

    error = refused.get_json()["error"]
    assert (refused.status_code, error["code"], error["message"]) == (409, REPLAY_CODE, WRITE_SESSION_REFUSAL)
    assert "details" not in error  # The plan started no job, so the page links to nothing.
    assert {child["status"] for child in store.records[AGGREGATE_ID]["children"]} == {"planned"}  # No child left.


@pytest.mark.parametrize(
    ("record", "expected"),
    (
        ({"state": "planned", "children": [{"status": "planned"}]}, False),
        ({"state": "planned", "children": []}, False),
        ({"state": "submission_claimed", "children": [{"status": "planned"}]}, True),
        ({"state": "running", "children": [{"status": "planned"}, {"status": "accepted"}]}, True),
    ),
)
def test_the_durable_record_decides_whether_a_job_started(record: dict[str, Any], expected: bool) -> None:
    """D6: a claim or a child that left the plan proves a start, and nothing else does."""
    assert org_upgrade.OrgReplayRefusal.started(record) is expected
