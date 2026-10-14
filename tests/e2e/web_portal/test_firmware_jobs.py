"""Exercise asynchronous policy and restoration APIs with real CSRF and fixture SDK calls."""

from __future__ import annotations

import json
from collections.abc import Iterator
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from flask import Flask
from flask_wtf.csrf import CSRFProtect, generate_csrf

from src.operations.execution.firmware_policy.recovery.backup import PolicyBackup
from src.operations.execution.firmware_policy.sdk import PolicyError
from tests.unit.firmware_policy.fakes import ORG_ID, OTHER_SITE_ID, SITE_ID, SettingsSession
from tests.unit.firmware_policy.recovery.fakes import RestoreSession
from tests.unit.firmware_policy_jobs.test_manager import ManualExecutor
from web_portal.routes.firmware_policy import firmware_policy_bp
from web_portal.routes.firmware_policy.jobs.manager import JobManager
from web_portal.routes.firmware_policy.jobs.ownership.targets import TargetWrites


@pytest.fixture
def job_portal(tmp_path: Path, monkeypatch: Any) -> Iterator[tuple[Flask, SettingsSession, ManualExecutor]]:
    """Use genuine SDK domain safeguards with deterministic admitted worker calls."""
    monkeypatch.setattr("src.operations.execution.firmware_policy.sdk.AdaptivePacer.next_delay", lambda self: 0.0)
    app = Flask(__name__)  # A focused application avoids unrelated portal worker startup.
    app.config.update(SECRET_KEY="offline-session-fixture", TESTING=True, DATA_DIR=str(tmp_path), ORG_ID=ORG_ID)
    api_session = SettingsSession(tmp_path)  # Never connect to a production organization.
    monkeypatch.setattr(
        api_session, "get_cloud", lambda: "api.mist.com", raising=False
    )  # Writer locks use checked cloud identity.
    app.config["APISESSION"] = api_session
    executor = ManualExecutor()
    app.extensions["firmware_policy_jobs"] = JobManager(tmp_path, executor)
    CSRFProtect(app)  # Require the same header protection as the existing portal.
    app.register_blueprint(firmware_policy_bp)

    @app.get("/operations")
    def operations() -> str:
        """Supply a fixture CSRF token through the integrated operations workspace."""
        return str(generate_csrf())  # A redirected legacy link uses the same browser session.

    yield app, api_session, executor
    app.extensions["firmware_policy_jobs"].close()  # Stop this fixture's private local worker route.


def post(client: Any, path: str, body: dict[str, Any]) -> Any:
    """Submit a real protected request with a token issued to this browser."""
    token = client.get("/operations").get_data(as_text=True)
    return client.post(path, json=body, headers={"X-CSRFToken": token})


def policy_body() -> dict[str, Any]:
    """Post a deliberately false organization name to prove server identity ownership."""
    return {
        "organizations": [{"id": ORG_ID, "name": "Forged organization"}],
        "policies": [{"kind": "ap", "enabled": False, "models": {"AP41": "new"}, "day": "any", "time": "02:00"}],
    }


def test_prepare_and_apply_are_pollable_owned_and_single_use(job_portal: Any) -> None:
    """Verify every backup before exposing confirmation or admitting a settings write."""
    app, api_session, executor = job_portal
    client = app.test_client()
    response = post(client, "/api/firmware-policy/preview", policy_body())
    assert response.status_code == 202
    identifier = response.get_json()["job_id"]
    path = f"/api/firmware-policy/jobs/{identifier}"
    assert client.get(path).get_json()["state"] == "queued"
    assert api_session.writes == []
    executor.run()
    ready = client.get(path).get_json()
    assert ready["state"] == "ready"
    assert ready["backups_verified"] == ready["settings_count"] == 3
    assert [row["name"] for row in ready["rows"]] == ["First", "Fixture Organization", "Inherited"]
    assert all(row["backup"] == "verified" for row in ready["rows"])
    assert ready["organizations"][0]["name"] == "Fixture Organization"
    assert "Forged organization" not in json.dumps(ready)
    assert "private-fixture" not in json.dumps(ready)
    assert api_session.writes == []
    assert list((api_session.data_directory / ".firmware-policy-backups").glob("*.json"))
    token = ready["token"]
    body = {"token": token, "confirmation": "CONFIGURE"}
    assert client.post("/api/firmware-policy/apply", json=body).status_code == 400
    other = app.test_client()
    assert other.get(path).status_code == 404
    assert post(other, "/api/firmware-policy/apply", body).status_code == 400
    assert post(client, "/api/firmware-policy/apply", body).status_code == 202
    assert client.get(path).get_json()["state"] == "applying"
    assert post(client, "/api/firmware-policy/apply", body).status_code == 400
    assert api_session.writes == []
    executor.run()
    complete = client.get(path).get_json()
    assert complete["state"] == "complete"
    assert len(api_session.writes) == 2
    assert "token" not in complete
    assert "private-fixture" not in json.dumps(complete)


@pytest.mark.parametrize("status", [403, 503])
def test_http_4xx_and_5xx_preparation_fail_closed(job_portal: Any, status: int) -> None:
    """A failed cloud read produces no ready token, settings write, or raw response body."""
    app, api_session, executor = job_portal
    api_session.fail_read = f"/api/v1/orgs/{ORG_ID}/setting"
    api_session.status = status
    client = app.test_client()
    response = post(client, "/api/firmware-policy/preview", policy_body())
    assert response.status_code == 202
    executor.run()
    failed = client.get(f"/api/firmware-policy/jobs/{response.get_json()['job_id']}").get_json()
    assert failed["state"] == "failed"
    assert "token" not in failed
    assert "private-fixture" not in json.dumps(failed)
    assert api_session.writes == []


@pytest.mark.parametrize("status", [400, 500])
def test_http_write_failure_reports_partial_without_replay(job_portal: Any, status: int) -> None:
    """Preserve an uncertain outcome and never submit an automatic second write."""
    app, api_session, executor = job_portal
    client = app.test_client()
    identifier = post(client, "/api/firmware-policy/preview", policy_body()).get_json()["job_id"]
    executor.run()
    ready = client.get(f"/api/firmware-policy/jobs/{identifier}").get_json()
    api_session.fail_write = f"/api/v1/orgs/{ORG_ID}/setting"
    api_session.status = status
    body = {"token": ready["token"], "confirmation": "CONFIGURE"}
    assert post(client, "/api/firmware-policy/apply", body).status_code == 202
    executor.run()
    outcome = client.get(f"/api/firmware-policy/jobs/{identifier}").get_json()
    assert outcome["state"] == "partial"
    assert len(outcome["result"]["failures"]) == 1
    assert f"HTTP {status}" in outcome["result"]["failures"][0]
    assert len(api_session.writes) == 1
    assert "private-fixture" not in json.dumps(outcome)
    assert post(client, "/api/firmware-policy/apply", body).status_code == 400
    assert len(api_session.writes) == 1


def test_failed_durable_backup_blocks_apply_and_unexpected_errors_are_private(
    job_portal: Any, monkeypatch: Any
) -> None:
    """An exception with private text must not escape worker status."""

    def failed_save(self: Any, records: Any) -> Path:
        """Reject the backup before the workflow can admit settings writes."""
        raise RuntimeError("private-backup-value")  # Exercise unexpected storage failures at the worker boundary.

    app, api_session, executor = job_portal
    monkeypatch.setattr(PolicyBackup, "save", failed_save)
    client = app.test_client()
    identifier = post(client, "/api/firmware-policy/preview", policy_body()).get_json()["job_id"]
    executor.run()
    failed = client.get(f"/api/firmware-policy/jobs/{identifier}").get_json()
    assert failed["state"] == "failed"
    assert "token" not in failed
    assert "private-backup-value" not in json.dumps(failed)
    assert api_session.writes == []


def test_restore_ready_cancel_and_ordered_application(job_portal: Any) -> None:
    """Use the same jobs endpoint for verified recovery and exact restoration confirmation."""
    app, original_session, executor = job_portal
    api_session = RestoreSession(original_session.data_directory)
    app.config["APISESSION"] = api_session
    client = app.test_client()
    choices = client.get("/api/settings-restore/bundles").get_json()
    assert choices["cloud"] == "api.mist.com"
    assert len(choices["bundles"]) == 1
    bundle = choices["bundles"][0]
    body = {
        "bundle": bundle["token"],
        "records": [f"{row['scope']}:{row['id']}" for row in bundle["records"]],
        "cloud": choices["cloud"],
    }
    identifier = post(client, "/api/settings-restore/preview", body).get_json()["job_id"]
    executor.run()
    ready = client.get(f"/api/firmware-policy/jobs/{identifier}").get_json()
    assert ready["state"] == "ready"
    assert ready["backups_verified"] == 2
    assert "private-fixture" not in json.dumps(ready)
    assert post(client, "/api/settings-restore/cancel", {"token": ready["token"]}).status_code == 200
    assert (
        post(client, "/api/settings-restore/apply", {"token": ready["token"], "confirmation": "RESTORE"}).status_code
        == 400
    )
    assert api_session.writes == []
    identifier = post(client, "/api/settings-restore/preview", body).get_json()["job_id"]
    executor.run()
    token = client.get(f"/api/firmware-policy/jobs/{identifier}").get_json()["token"]
    assert post(client, "/api/settings-restore/apply", {"token": token, "confirmation": "CONFIGURE"}).status_code == 400
    assert post(client, "/api/settings-restore/apply", {"token": token, "confirmation": "RESTORE"}).status_code == 202
    executor.run()
    complete = client.get(f"/api/firmware-policy/jobs/{identifier}").get_json()
    assert complete["state"] == "complete"
    assert [uri.split("/")[3] for uri, _ in api_session.writes] == ["orgs", "sites"]
    assert all(row["status"] == "complete" for row in complete["rows"])


def test_policy_backup_lists_and_restores_in_the_same_browser(job_portal: Any, monkeypatch: Any) -> None:
    """Restore a policy-created backup without substituting a separately seeded recovery session."""
    app, api_session, executor = job_portal
    monkeypatch.setattr(
        api_session, "get_cloud", lambda: "api.mist.com", raising=False
    )  # Supply fixture cloud identity.
    api_session.settings = {
        f"/api/v1/orgs/{ORG_ID}/setting": {
            "org_id": ORG_ID,
            "allow_mist": False,
            "auto_upgrade": {"enabled": True},
        },
        f"/api/v1/sites/{SITE_ID}/setting": {
            "org_id": ORG_ID,
            "site_id": SITE_ID,
            "auto_upgrade": {"enabled": True},
        },
        f"/api/v1/sites/{OTHER_SITE_ID}/setting": {
            "org_id": ORG_ID,
            "site_id": OTHER_SITE_ID,
            "auto_upgrade": {"enabled": True},
        },
    }  # Use writable settings accepted by both real domain workflows.
    originals = deepcopy(api_session.settings)  # Compare the entire recovered settings, not only policy fields.
    client = app.test_client()
    identifier = post(client, "/api/firmware-policy/preview", policy_body()).get_json()["job_id"]
    executor.run()
    ready = client.get(f"/api/firmware-policy/jobs/{identifier}").get_json()
    assert ready["state"] == "ready"
    assert (
        post(client, "/api/firmware-policy/apply", {"token": ready["token"], "confirmation": "CONFIGURE"}).status_code
        == 202
    )
    executor.run()
    assert client.get(f"/api/firmware-policy/jobs/{identifier}").get_json()["state"] == "complete"
    assert api_session.settings != originals
    assert client.get("/operations/settings-restore").status_code == 302
    response = client.get("/api/settings-restore/bundles")
    assert response.status_code == 200, response.get_json()
    choices = response.get_json()
    assert len(choices["bundles"]) == 1
    bundle = choices["bundles"][0]
    assert bundle["record_count"] == 3
    assert "settings" not in json.dumps(choices)
    body = {
        "bundle": bundle["token"],
        "records": [f"{row['scope']}:{row['id']}" for row in bundle["records"]],
        "cloud": choices["cloud"],
    }
    response = post(client, "/api/settings-restore/preview", body)
    assert response.status_code == 202
    restoration = response.get_json()["job_id"]
    executor.run()
    ready = client.get(f"/api/firmware-policy/jobs/{restoration}").get_json()
    assert ready["state"] == "ready", ready
    assert ready["backups_verified"] == 3
    writes_before_restore = len(api_session.writes)
    response = post(client, "/api/settings-restore/apply", {"token": ready["token"], "confirmation": "RESTORE"})
    assert response.status_code == 202
    executor.run()
    outcome = client.get(f"/api/firmware-policy/jobs/{restoration}").get_json()
    assert outcome["state"] == "complete", outcome
    assert outcome["result"]["backups_verified"] == 3
    assert [uri.split("/")[3] for uri, _ in api_session.writes[writes_before_restore:]] == ["orgs", "sites", "sites"]
    assert api_session.settings == originals
    assert len(client.get("/api/settings-restore/bundles").get_json()["bundles"]) == 2


def test_backup_metadata_names_share_one_identity_and_site_listing(job_portal: Any) -> None:
    """Label repeated backup scopes without one SDK request for each saved site."""
    app, original_session, _ = job_portal
    api_session = RestoreSession(original_session.data_directory)
    api_session.backup.save(api_session.saved)  # Two bundles must share the same metadata request budget.
    app.config["APISESSION"] = api_session
    response = app.test_client().get("/api/settings-restore/bundles")
    assert response.status_code == 200
    bundles = response.get_json()["bundles"]
    assert len(bundles) == 2
    for bundle in bundles:
        assert [row["name"] for row in bundle["records"]] == ["Fixture Organization", "First"]
        assert all(row["organization"] == "Fixture Organization" for row in bundle["records"])
        assert all(set(row) == {"scope", "id", "name", "organization", "organization_id"} for row in bundle["records"])
    paths = [uri for uri, _ in api_session.reads]
    assert paths.count(f"/api/v1/orgs/{ORG_ID}") == 1
    assert paths.count(f"/api/v1/orgs/{ORG_ID}/sites") == 1
    assert paths.count("/api/v1/self/usage") == 1
    assert len(paths) == 3
    assert "private-fixture" not in response.get_data(as_text=True)
    assert api_session.writes == []


@pytest.mark.parametrize("kind", ["policy", "restore"])
def test_conflicting_cloud_organization_writer_rejects_apply_without_writes(job_portal: Any, kind: str) -> None:
    """Both portal workflows refuse another active writer before domain freshness or cloud mutation."""
    app, api_session, executor = job_portal
    client = app.test_client()
    endpoint = "/api/firmware-policy"
    body = policy_body()
    confirmation = "CONFIGURE"
    if kind == "restore":
        api_session = RestoreSession(api_session.data_directory)
        app.config["APISESSION"] = api_session
        endpoint = "/api/settings-restore"
        confirmation = "RESTORE"
        choices = client.get(f"{endpoint}/bundles").get_json()
        bundle = choices["bundles"][0]
        body = {
            "bundle": bundle["token"],
            "records": [f"{record['scope']}:{record['id']}" for record in bundle["records"]],
            "cloud": choices["cloud"],
        }
    identifier = post(client, f"{endpoint}/preview", body).get_json()["job_id"]
    executor.run()
    ready = client.get(f"/api/firmware-policy/jobs/{identifier}").get_json()
    assert ready["state"] == "ready"
    token = ready["token"]
    api_session.reads.clear()  # A conflicting apply must stop before any cloud freshness read.
    with TargetWrites.hold(api_session.data_directory / ".firmware-policy-backups", "api.mist.com", {ORG_ID}):
        assert post(client, f"{endpoint}/apply", {"token": token, "confirmation": confirmation}).status_code == 202
        executor.run()
    outcome = client.get(f"/api/firmware-policy/jobs/{identifier}").get_json()
    assert outcome["state"] == "failed"
    assert "another active settings writer" in outcome["error"]
    assert "token" not in outcome
    assert api_session.reads == []
    assert api_session.writes == []
    assert post(client, f"{endpoint}/apply", {"token": token, "confirmation": confirmation}).status_code == 400


@pytest.mark.parametrize("status", [403, 503])
@pytest.mark.parametrize("suffix", ["", "/sites"])
def test_backup_metadata_http_failures_return_checked_reason(job_portal: Any, status: int, suffix: str) -> None:
    """Do not substitute identifiers when authenticated identity or membership access fails."""
    app, original_session, _ = job_portal
    api_session = RestoreSession(original_session.data_directory)
    api_session.fail_read = f"/api/v1/orgs/{ORG_ID}{suffix}"
    api_session.status = status
    app.config["APISESSION"] = api_session
    response = app.test_client().get("/api/settings-restore/bundles")
    assert response.status_code == 400
    assert f"HTTP {status}" in response.get_json()["error"]
    assert "private-fixture" not in response.get_data(as_text=True)
    assert "bundles" not in response.get_json()
    assert api_session.writes == []


@pytest.mark.parametrize("saved_name", [None, "Saved site label"])
def test_backup_metadata_missing_site_name_is_explicit(
    job_portal: Any, saved_name: str | None, monkeypatch: Any
) -> None:
    """Use a safe saved label only when the complete current site list has no label."""
    app, original_session, _ = job_portal
    api_session = RestoreSession(original_session.data_directory)
    api_session.saved[1]["id"] = OTHER_SITE_ID  # Select a saved site absent from the current labeled record.
    settings: Any = api_session.saved[1]["settings"]  # The fixture stores complete heterogeneous settings records.
    settings["site_id"] = OTHER_SITE_ID
    if saved_name:
        settings["name"] = saved_name
    api_session.path.unlink()  # Remove only this fixture's first bundle before saving its modified record.
    api_session.backup.save(api_session.saved)
    original_get = api_session.mist_get

    def without_site_label(uri: str, query: Any = None) -> Any:
        """Remove one current label without changing membership or request evidence."""
        response = original_get(uri, query)
        if uri.endswith("/sites"):
            response.data[1].pop("name")  # A missing label must not become the site identifier.
        return response

    monkeypatch.setattr(api_session, "mist_get", without_site_label)  # Restore the fixture method after the test.
    app.config["APISESSION"] = api_session
    response = app.test_client().get("/api/settings-restore/bundles")
    assert response.status_code == 200
    site = response.get_json()["bundles"][0]["records"][1]
    assert site["name"] == (saved_name or "Site name unavailable")
    assert site["id"] == OTHER_SITE_ID


def test_identity_failures_and_legacy_redirects_use_existing_routes(job_portal: Any, monkeypatch: Any) -> None:
    """Refuse an unavailable real name without accepting the identifier as a name."""
    app, api_session, _ = job_portal
    client = app.test_client()
    assert client.get("/operations/firmware-policy").headers["Location"] == "/operations?menu=305"
    assert client.get("/operations/settings-restore").headers["Location"] == "/operations?menu=306"
    api_session.fail_read = f"/api/v1/orgs/{ORG_ID}"
    api_session.status = 403
    denied = client.get("/api/firmware-policy/organizations")
    assert denied.status_code == 400
    assert "private-fixture" not in denied.get_data(as_text=True)

    def failed_identity(self: Any, identifier: str) -> dict[str, str]:
        """Simulate an unexpected identity SDK error with sensitive response text."""
        raise PolicyError("private-identity-value")  # Public request errors must also redact checked messages.

    monkeypatch.setattr("src.operations.execution.firmware_policy.sdk.PolicyApi.organization", failed_identity)
    denied = client.get("/api/firmware-policy/organizations")
    assert denied.status_code == 400
    assert "private-identity-value" not in denied.get_data(as_text=True)
