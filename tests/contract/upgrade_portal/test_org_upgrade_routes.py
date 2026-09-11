"""Contract tests for the organization AP upgrade browser workflow.

Why:
    These tests drive the real Flask routes with an injected Mist service. No
    test opens a socket or submits a firmware job.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient

from src.firmware.org_upgrade_service import OrgUpgradeResult
from src.upgrade_portal.app.routes.org_upgrade import status_summary
from src.upgrade_portal.runtime import identity

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


def test_the_options_page_shows_the_ap_scope(org_upgrade_client: FlaskClient) -> None:
    """The options page keeps the current portal style and states AP scope."""
    answer = org_upgrade_client.get(ORG_OPTIONS_PAGE)
    assert answer.status_code == 200
    assert b'data-testid="org-upgrade-options"' in answer.data
    assert b"access points only" in answer.data
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
