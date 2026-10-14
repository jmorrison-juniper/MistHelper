"""Prove menu 305's graphical selection, verified backups, and guarded settings execution."""

from __future__ import annotations

import json
import re
import threading
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from playwright.sync_api import expect
from werkzeug.serving import make_server

from src.operations.execution.firmware_policy.recovery.backup import PolicyBackup
from src.operations.execution.firmware_policy.sdk import PolicyError
from tests.unit.firmware_policy.fakes import ORG_ID, SITE_ID, SettingsSession
from web_portal.app import WebPortalApp


@pytest.fixture
def policy_portal(tmp_path: Path, monkeypatch: Any) -> Iterator[tuple[Any, SettingsSession]]:
    """Create an isolated portal with real security middleware and mocked SDK transport."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    session = SettingsSession(tmp_path)
    app = WebPortalApp.create_app(session, {}, ORG_ID)
    app.config["TESTING"] = True
    yield app, session
    WebPortalApp.shutdown_app(app)


def post(client: Any, path: str, body: dict[str, Any], raw_body: bytes | None = None) -> Any:
    """Use the rendered portal CSRF token for a real protected POST request."""
    page = client.get("/operations/firmware-policy").get_data(as_text=True)
    match = re.search(r'<meta name="csrf-token" content="([^"]+)"', page)
    assert match is not None, "The page must supply the CSRF token."
    if raw_body is not None:
        return client.post(
            path, data=raw_body, content_type="application/json", headers={"X-CSRFToken": match.group(1)}
        )
    return client.post(path, json=body, headers={"X-CSRFToken": match.group(1)})


def preview_body() -> dict[str, Any]:
    """Supply a complete explicit disabled AP policy without firmware execution."""
    return {
        "organizations": [ORG_ID],
        "policies": [{"kind": "ap", "enabled": False, "models": {"AP41": "new"}, "day": "mon", "time": "02:00"}],
    }


def test_portal_full_preview_and_apply_verifies_every_backup(policy_portal: tuple[Any, SettingsSession]) -> None:
    """Exercise graphical API selections and settings writes through the shared workflow."""
    app, session = policy_portal
    client = app.test_client()
    page = client.get("/operations").get_data(as_text=True)
    assert 'data-testid="firmware-policy-menu"' in page
    choices = client.get("/api/firmware-policy/organizations").get_json()
    assert choices["organizations"][0]["id"] == ORG_ID
    catalog = post(client, "/api/firmware-policy/catalog", {"organizations": [ORG_ID], "kinds": ["ap"]})
    assert catalog.get_json()["catalogs"]["ap"]["AP41"] == ["new", "stable"]
    preview = post(client, "/api/firmware-policy/preview", preview_body()).get_json()
    assert preview["writes"] == 0
    assert preview["settings_count"] == 3
    assert len(preview["organizations"][0]["sites"]) == 2
    assert "private-fixture" not in json.dumps(preview)
    assert session.writes == []
    assert not (session.data_directory / ".firmware-policy-backups").exists()
    response = post(client, "/api/firmware-policy/apply", {"token": preview["token"], "confirmation": "CONFIGURE"})
    result = response.get_json()
    assert response.status_code == 200
    assert result["status"] == "complete"
    assert result["backups_verified"] == 3
    assert result["result"]["sites"] == [SITE_ID]
    assert len(session.writes) == 2
    assert "private-fixture" not in json.dumps(result)


@pytest.mark.parametrize("confirmation", ["", "YES", "configure"])
def test_portal_wrong_confirmation_sends_zero_writes(
    policy_portal: tuple[Any, SettingsSession], confirmation: str
) -> None:
    """Require the exact confirmation word at the server boundary."""
    app, session = policy_portal
    client = app.test_client()
    token = post(client, "/api/firmware-policy/preview", preview_body()).get_json()["token"]
    response = post(client, "/api/firmware-policy/apply", {"token": token, "confirmation": confirmation})
    assert response.status_code == 400
    assert "CONFIGURE" in response.get_json()["error"]
    assert session.writes == []


def test_preview_is_session_bound_single_use_and_csrf_protected(policy_portal: tuple[Any, SettingsSession]) -> None:
    """Refuse another browser, a missing CSRF token, and duplicate apply submissions."""
    app, session = policy_portal
    client = app.test_client()
    token = post(client, "/api/firmware-policy/preview", preview_body()).get_json()["token"]
    body = {"token": token, "confirmation": "CONFIGURE"}
    assert client.post("/api/firmware-policy/apply", json=body).status_code == 400
    other = app.test_client()
    assert post(other, "/api/firmware-policy/apply", body).status_code == 400
    assert session.writes == []
    assert post(client, "/api/firmware-policy/apply", body).status_code == 200
    assert post(client, "/api/firmware-policy/apply", body).status_code == 400
    assert len(session.writes) == 2


def test_portal_backup_failure_returns_error_and_zero_cloud_writes(
    policy_portal: tuple[Any, SettingsSession], monkeypatch: Any
) -> None:
    """Surface an unreadable full settings backup instead of sending a cloud change."""
    app, session = policy_portal
    client = app.test_client()
    token = post(client, "/api/firmware-policy/preview", preview_body()).get_json()["token"]

    def fail_verification(self: PolicyBackup, path: Path, expected: list[dict]) -> None:
        """Simulate a failed durable backup comparison before the first write."""
        raise PolicyError("The settings backup could not be verified.")

    monkeypatch.setattr(PolicyBackup, "verify", fail_verification)
    response = post(client, "/api/firmware-policy/apply", {"token": token, "confirmation": "CONFIGURE"})
    assert response.status_code == 400
    assert "backup could not be verified" in response.get_json()["error"]
    assert session.writes == []


@pytest.mark.parametrize("body", [b"", b"bad json"])
def test_portal_empty_body_and_malformed_json_fail_before_sdk_calls(
    policy_portal: tuple[Any, SettingsSession], body: bytes
) -> None:
    """Invalid JSON cannot become an empty successful policy plan."""
    app, session = policy_portal
    response = post(app.test_client(), "/api/firmware-policy/preview", {}, raw_body=body)
    assert response.status_code == 400
    assert response.get_json()["error"] == "Send a JSON object for the policy request."
    assert session.reads == []
    assert session.writes == []


def test_portal_empty_body_and_malformed_json_backup_block_apply(
    policy_portal: tuple[Any, SettingsSession], monkeypatch: Any
) -> None:
    """The graphical workflow must reject empty and malformed durable backup files."""
    app, session = policy_portal
    client = app.test_client()
    backup = PolicyBackup(session.data_directory)
    create_file = PolicyBackup._create_file
    for content in (b"", b"bad json"):
        token = post(client, "/api/firmware-policy/preview", preview_body()).get_json()["token"]

        def corrupt_file(backup: PolicyBackup, document: dict[str, Any]) -> Path:
            """Corrupt the actual saved file before its shared verification gate."""
            path = create_file(backup, document)
            path.write_bytes(content)
            return path

        monkeypatch.setattr(PolicyBackup, "_create_file", corrupt_file)
        response = post(client, "/api/firmware-policy/apply", {"token": token, "confirmation": "CONFIGURE"})
        assert response.status_code == 400
        assert "could not be verified" in response.get_json()["error"]
        assert session.writes == []
        for path in (session.data_directory / ".firmware-policy-backups").glob("*.json"):
            with pytest.raises(PolicyError, match="could not be verified"):
                backup.verify(path, [])


@pytest.mark.parametrize("status_code", [403, 503])
def test_portal_http_4xx_and_5xx_result_reports_partial(
    policy_portal: tuple[Any, SettingsSession], status_code: int
) -> None:
    """A failed site write reports completed organizations and remaining sites."""
    app, session = policy_portal
    client = app.test_client()
    token = post(client, "/api/firmware-policy/preview", preview_body()).get_json()["token"]
    session.fail_write = f"/api/v1/sites/{SITE_ID}/setting"
    session.status = status_code
    response = post(client, "/api/firmware-policy/apply", {"token": token, "confirmation": "CONFIGURE"})
    data = response.get_json()
    assert data["status"] == "partial"
    assert data["result"]["organizations"] == [ORG_ID]
    assert f"HTTP {status_code}" in data["result"]["failures"][0]
    assert len(data["result"]["remaining"]) == 2


def test_portal_backup_download_and_preview_are_denied(policy_portal: tuple[Any, SettingsSession]) -> None:
    """Even a known settings-backup filename cannot be downloaded through data routes."""
    app, session = policy_portal
    path = PolicyBackup(session.data_directory).save([{"settings": {"conductor_token": "private-fixture"}}])
    client = app.test_client()
    relative = path.relative_to(session.data_directory).as_posix()
    assert client.get("/api/data/download/" + relative).status_code == 404
    assert client.get("/api/data/preview/" + relative).status_code == 404
    assert "private-fixture" not in client.get("/api/data/files").get_data(as_text=True)


def test_browser_dynamic_models_preview_confirmation_and_results(
    policy_portal: tuple[Any, SettingsSession], page: Any
) -> None:
    """Complete the graphical journey without typed terminal prompts or real API transport."""
    app, session = policy_portal
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}"
    try:
        page.goto(url + "/operations/firmware-policy", wait_until="networkidle")
        page.get_by_test_id("policy-kind-ap").check()
        page.get_by_test_id("policy-load").click()
        page.get_by_test_id("policy-enabled-ap").select_option("DISABLE")
        page.get_by_test_id("policy-model-ap-0").check()
        page.get_by_test_id("policy-version-ap-0").select_option("new")
        page.get_by_test_id("policy-day").select_option("mon")
        page.get_by_test_id("policy-time").fill("02:00")
        page.get_by_test_id("policy-preview").click()
        expect(page.get_by_test_id("policy-message")).to_contain_text("Dry run complete")
        assert SITE_ID in page.get_by_test_id("policy-plan").inner_text()
        assert session.writes == []
        assert page.get_by_test_id("policy-apply").is_disabled()
        page.get_by_test_id("policy-confirmation").fill("CONFIGURE")
        page.get_by_test_id("policy-apply").click()
        expect(page.get_by_test_id("policy-message")).to_contain_text("Settings change complete")
        assert '"backups_verified": 3' in page.get_by_test_id("policy-result").inner_text()
        assert len(session.writes) == 2
        assert "private-fixture" not in page.content()
        artifact = Path("test-artifacts") / "firmware-policy-complete.png"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(artifact), full_page=True)
    except BaseException:
        artifact = Path("test-artifacts") / "firmware-policy-failed.png"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(artifact))
        raise
    finally:
        server.shutdown()
        thread.join(timeout=10)
