"""Prove menu 305's graphical selection, verified backups, and guarded settings execution."""

from __future__ import annotations

import json
import re
import threading
import time
from collections.abc import Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from playwright.sync_api import expect
from werkzeug.serving import make_server

from src.foundation.support.utils.rate_limiting import RateLimitingUtils
from src.operations.execution.firmware_policy.recovery.backup import PolicyBackup
from src.operations.execution.firmware_policy.sdk import PolicyError, PolicyResponse
from tests.unit.firmware_policy.fakes import ORG_ID, SITE_ID, SettingsSession
from web_portal.app import WebPortalApp


@pytest.fixture
def policy_portal(tmp_path: Path, monkeypatch: Any) -> Iterator[tuple[Any, SettingsSession]]:
    """Create an isolated portal with real security middleware and mocked SDK transport."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setattr(RateLimitingUtils, "get_rate_limited_delay", lambda *_args: (0.0, 0.0))
    session = SettingsSession(tmp_path)
    app = WebPortalApp.create_app(session, {}, ORG_ID)
    app.config["TESTING"] = True
    yield app, session
    WebPortalApp.shutdown_app(app)


def post(client: Any, path: str, body: dict[str, Any], raw_body: bytes | None = None) -> Any:
    """Use the rendered portal CSRF token for a real protected POST request."""
    page = client.get("/operations/firmware-policy", follow_redirects=True).get_data(as_text=True)
    match = re.search(r'<meta name="csrf-token" content="([^"]+)"', page)
    assert match is not None, "The page must supply the CSRF token."
    if raw_body is not None:
        return client.post(
            path, data=raw_body, content_type="application/json", headers={"X-CSRFToken": match.group(1)}
        )
    return client.post(path, json=body, headers={"X-CSRFToken": match.group(1)})


def test_http_5xx_boundary_hides_private_response_body() -> None:
    """Reject a server failure without copying its private body into portal errors."""
    response = SimpleNamespace(status_code=503, data={"credential": "private-fixture"})
    with pytest.raises(PolicyError, match="HTTP 503") as failure:
        PolicyResponse.request(lambda: response, "Read settings", ORG_ID)
    assert "private-fixture" not in str(failure.value)
    assert "credential" not in str(failure.value)


class PolicyJobs:
    """Follow actual asynchronous status without repeating a mutation request."""

    @staticmethod
    def finish(client: Any, response: Any) -> dict[str, Any]:
        """Wait for a terminal fixture job and preserve its complete checked status."""
        assert response.status_code == 202, response.get_data(as_text=True)
        identifier = response.get_json()["job_id"]
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            status = client.get("/api/firmware-policy/jobs/" + identifier)
            assert status.status_code == 200
            result = status.get_json()
            if result.get("state", result.get("status")) not in ("queued", "preparing", "applying", "running"):
                return result
            time.sleep(0.01)
        pytest.fail("The fixture settings job did not finish within 15 seconds.")


@pytest.fixture
def policy_server(policy_portal: tuple[Any, SettingsSession]) -> Iterator[tuple[str, SettingsSession]]:
    """Expose the isolated fixture portal on a kernel-selected loopback port."""
    app, sdk = policy_portal
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", sdk
    finally:
        server.shutdown()
        thread.join(timeout=10)


@pytest.mark.parametrize("width", [1440, 800, 390])
def test_workspace_category_keyboard_and_responsive_columns(
    policy_server: tuple[str, SettingsSession], page: Any, width: int
) -> None:
    """Keep both workflows in the menu and preserve desktop and narrow-screen layouts."""
    url, sdk = policy_server
    page.set_viewport_size({"width": width, "height": 1002})
    page.goto(url + "/operations", wait_until="networkidle")
    page.get_by_role("button", name=re.compile("Firmware Policies & Recovery")).click()
    menu = page.get_by_test_id("firmware-policy-menu")
    menu.focus()
    page.keyboard.press("Enter")
    expect(page.get_by_test_id("firmware-policy-workspace")).to_be_visible()
    assert page.url.endswith("/operations?menu=305")
    left = page.get_by_test_id("operation-accordion").bounding_box()
    right = page.get_by_test_id("firmware-policy-workspace").bounding_box()
    assert left is not None and right is not None
    assert (right["x"] >= left["x"] + left["width"] - 1) == (width >= 768)
    page.get_by_test_id("settings-restore-menu").click()
    expect(page.get_by_test_id("settings-restore-workspace")).to_be_visible()
    expect(page.get_by_test_id("firmware-policy-workspace")).to_be_hidden()
    expect(page.get_by_test_id("operation-accordion")).to_be_visible()
    assert page.url.endswith("/operations?menu=306")
    page.reload(wait_until="networkidle")
    expect(page.get_by_test_id("settings-restore-workspace")).to_be_visible()
    expect(page.get_by_test_id("firmware-policy-workspace")).to_be_hidden()
    assert page.locator("iframe").count() == 0
    assert sdk.writes == []


def test_catalog_all_hardware_dynamic_versions_and_schedule_defaults(
    policy_server: tuple[str, SettingsSession], page: Any
) -> None:
    """Prove every hardware class reveals only checked models and sorts mixed numeric versions."""
    url, sdk = policy_server
    catalogs = {
        "ap": {"AP-EXAMPLE": ["0.14.99", "0.15.9", "0.15.10"]},
        "switch": {"EX-EXAMPLE": ["DL.10.9.1002", "DL.10.18.1002"]},
        "ssr": {"SSR-EXAMPLE": ["6.0.4-11", "6.0.10-5"]},
        "juniper_srx": {"SRX-EXAMPLE": ["23.4R2-S4.9", "23.4R2-S5.5", "22.4R3-S4.5"]},
    }
    page.route("**/api/firmware-policy/catalog", lambda route: route.fulfill(json={"catalogs": catalogs}))
    page.goto(url + "/operations?menu=305", wait_until="networkidle")
    for kind in catalogs:
        page.get_by_test_id("policy-kind-" + kind).check()
    page.get_by_test_id("policy-load").click()
    for kind, models in catalogs.items():
        version = page.get_by_test_id("policy-version-" + kind + "-0")
        expect(version).to_be_hidden()
        page.get_by_test_id("policy-model-" + kind + "-0").check()
        expect(version).to_be_visible()
        assert (
            version.locator("option").all_text_contents()[1]
            == {"ap": "0.15.10", "switch": "DL.10.18.1002", "ssr": "6.0.10-5", "juniper_srx": "23.4R2-S5.5"}[kind]
        )
        assert version.locator("option").count() == len(next(iter(models.values()))) + 1
        page.get_by_test_id("policy-model-" + kind + "-0").uncheck()
        expect(version).to_be_hidden()
    expect(page.get_by_test_id("policy-day")).to_have_value("any")
    expect(page.get_by_test_id("policy-time")).to_have_value("02:00")
    expect(page.get_by_test_id("policy-confirm-panel")).to_be_hidden()
    assert sdk.writes == []


def test_browser_confirmation_waits_for_complete_backup_verification(
    policy_server: tuple[str, SettingsSession], page: Any, monkeypatch: Any
) -> None:
    """Hide confirmation during actual backup verification, then reject stale UI confirmation."""
    url, sdk = policy_server
    entered = threading.Event()
    released = threading.Event()
    verify = PolicyBackup.verify

    def delayed(backup: PolicyBackup, path: Path, records: list[dict[str, Any]]) -> None:
        """Hold fixture verification so the browser can inspect the incomplete state."""
        entered.set()
        if not released.wait(10):
            raise PolicyError("The fixture verification wait exceeded ten seconds.")
        verify(backup, path, records)

    monkeypatch.setattr(PolicyBackup, "verify", delayed)
    page.goto(url + "/operations?menu=305", wait_until="networkidle")
    page.get_by_test_id("policy-kind-ap").check()
    page.get_by_test_id("policy-load").click()
    page.get_by_test_id("policy-enabled-ap").select_option("DISABLE")
    page.get_by_test_id("policy-model-ap-0").check()
    page.get_by_test_id("policy-version-ap-0").select_option("new")
    try:
        page.get_by_test_id("policy-preview").click()
        assert entered.wait(5)
        expect(page.get_by_test_id("policy-confirm-panel")).to_be_hidden()
        expect(page.get_by_test_id("policy-preview")).to_be_disabled()
        assert sdk.writes == []
        released.set()
        expect(page.get_by_test_id("policy-confirm-panel")).to_be_visible()
        expect(page.get_by_test_id("policy-plan")).to_contain_text("AP41: new")
        page.reload(wait_until="networkidle")
        expect(page.get_by_test_id("policy-confirm-panel")).to_be_visible()
        expect(page.get_by_test_id("policy-plan")).to_contain_text("AP41: new")
        page.get_by_test_id("policy-confirmation").fill("CONFIGURE")
        expect(page.get_by_test_id("policy-apply")).to_be_enabled()
        page.get_by_test_id("policy-kind-ap").check()
        expect(page.get_by_test_id("policy-confirm-panel")).to_be_hidden()
        expect(page.get_by_test_id("policy-plan")).to_be_empty()
        expect(page.get_by_test_id("policy-message")).to_have_text("Selection changed. Prepare backups again.")
        expect(page.get_by_test_id("policy-progress")).to_have_attribute("aria-valuenow", "0")
        assert sdk.writes == []
    finally:
        released.set()


def test_browser_resumes_wait_progress_and_paginates_sorted_scope_rows(
    policy_server: tuple[str, SettingsSession], page: Any
) -> None:
    """Recover long-wait progress after reload and keep a large result table compact."""
    url, sdk = policy_server
    rows = [
        {"scope": "site", "id": f"fixture-{index}", "name": f"Site {index:04}", "backup": "verified", "status": "ready"}
        for index in reversed(range(101))
    ]
    page.add_init_script("sessionStorage.setItem('policy-settings-job', 'fixture-wait');")
    page.route(
        "**/api/firmware-policy/jobs/fixture-wait",
        lambda route: route.fulfill(
            json={
                "state": "preparing",
                "progress": {"phase": "request_wait", "completed": 1, "total": 4002, "wait_seconds": 7201},
                "rows": rows,
            }
        ),
    )
    page.goto(url + "/operations?menu=305", wait_until="networkidle")
    expect(page.get_by_test_id("policy-message")).to_contain_text("7201 seconds")
    expect(page.get_by_test_id("policy-confirm-panel")).to_be_hidden()
    table = page.get_by_test_id("policyRows-table")
    assert table.locator("tbody tr").count() == 50
    assert table.locator("tbody tr").first.locator("td").first.inner_text() == "Site 0000"
    page.get_by_test_id("policyRows-next").click()
    assert table.locator("tbody tr").first.locator("td").first.inner_text() == "Site 0050"
    page.reload(wait_until="networkidle")
    expect(page.get_by_test_id("policy-message")).to_contain_text("7201 seconds")
    assert sdk.writes == []


@pytest.mark.parametrize("change", ["model", "version", "day", "time", "scope", "state"])
def test_browser_invalidates_all_obsolete_verification_state(
    policy_server: tuple[str, SettingsSession], page: Any, change: str
) -> None:
    """Remove stale plan, progress, and backup status when any prepared input changes."""
    url, sdk = policy_server
    page.goto(url + "/operations?menu=305", wait_until="networkidle")
    page.get_by_test_id("policy-kind-ap").check()
    page.get_by_test_id("policy-load").click()
    page.get_by_test_id("policy-enabled-ap").select_option("DISABLE")
    page.get_by_test_id("policy-model-ap-0").check()
    page.get_by_test_id("policy-version-ap-0").select_option("new")
    page.get_by_test_id("policy-preview").click()
    expect(page.get_by_test_id("policy-confirm-panel")).to_be_visible()
    if change == "model":
        page.get_by_test_id("policy-model-ap-0").uncheck()
    elif change == "version":
        page.get_by_test_id("policy-version-ap-0").select_option("")
    elif change == "day":
        page.get_by_test_id("policy-day").select_option("mon")
    elif change == "time":
        page.get_by_test_id("policy-time").fill("03:00")
    elif change == "scope":
        page.get_by_test_id("policy-organizations").select_option(ORG_ID)
    else:
        page.get_by_test_id("policy-enabled-ap").select_option("ENABLE")
    expect(page.get_by_test_id("policy-confirm-panel")).to_be_hidden()
    expect(page.get_by_test_id("policy-plan")).to_be_empty()
    expect(page.get_by_test_id("policy-rows")).to_be_empty()
    expect(page.get_by_test_id("policy-message")).to_have_text("Selection changed. Prepare backups again.")
    expect(page.get_by_test_id("policy-progress")).to_have_attribute("aria-valuenow", "0")
    assert page.evaluate("sessionStorage.getItem('policy-settings-job')") is None
    assert sdk.writes == []


def test_browser_large_model_catalog_keeps_backup_controls_reachable(
    policy_server: tuple[str, SettingsSession], page: Any
) -> None:
    """Keep all 179 switch models available without extending the workspace by 179 rows."""
    url, sdk = policy_server
    models = {f"EX-{index:03}-48P": ["DL.10.18.1002", "DL.10.9.1002"] for index in range(179)}
    page.route("**/api/firmware-policy/catalog", lambda route: route.fulfill(json={"catalogs": {"switch": models}}))
    page.set_viewport_size({"width": 800, "height": 1002})
    page.goto(url + "/operations?menu=305", wait_until="networkidle")
    page.get_by_test_id("policy-kind-switch").check()
    page.get_by_test_id("policy-load").click()
    model_list = page.get_by_test_id("policy-model-list-switch")
    expect(model_list.locator("[data-model]")).to_have_count(179)
    bounds = model_list.bounding_box()
    assert bounds is not None and bounds["height"] <= 288
    page.get_by_test_id("policy-model-switch-178").check()
    expect(page.get_by_test_id("policy-version-switch-178")).to_be_visible()
    page.get_by_test_id("policy-preview").scroll_into_view_if_needed()
    expect(page.get_by_test_id("policy-preview")).to_be_in_viewport()
    assert page.evaluate("document.documentElement.scrollHeight") < 2400
    assert sdk.writes == []


def test_browser_unknown_read_count_has_labeled_indeterminate_progress(
    policy_server: tuple[str, SettingsSession], page: Any
) -> None:
    """Do not show a false zero-percent measurement while discovering target settings."""
    url, sdk = policy_server
    page.add_init_script("sessionStorage.setItem('policy-settings-job', 'fixture-reading');")
    page.route(
        "**/api/firmware-policy/jobs/fixture-reading",
        lambda route: route.fulfill(json={"state": "preparing", "progress": {"phase": "read_site_settings"}}),
    )
    page.goto(url + "/operations?menu=305", wait_until="networkidle")
    progress = page.get_by_test_id("policy-progress")
    expect(progress).to_have_text("Working")
    expect(progress).to_have_attribute("aria-valuetext", "Working. The target count is not available yet.")
    assert progress.get_attribute("aria-valuenow") is None
    expect(page.get_by_test_id("policy-message")).to_contain_text("Read site settings")
    expect(page.get_by_test_id("policy-confirm-panel")).to_be_hidden()
    assert sdk.writes == []


def test_browser_lost_apply_response_recovers_status_without_duplicate_writes(
    policy_server: tuple[str, SettingsSession], page: Any
) -> None:
    """Preserve the known operation reference when a confirmed response disappears."""
    url, sdk = policy_server
    submitted = []

    def lose_response(route: Any) -> None:
        """Deliver one real mutation request and discard only its browser response."""
        submitted.append(route.request.url)
        route.fetch()
        route.abort()

    page.goto(url + "/operations?menu=305", wait_until="networkidle")
    page.get_by_test_id("policy-kind-ap").check()
    page.get_by_test_id("policy-load").click()
    page.get_by_test_id("policy-enabled-ap").select_option("DISABLE")
    page.get_by_test_id("policy-model-ap-0").check()
    page.get_by_test_id("policy-version-ap-0").select_option("new")
    page.get_by_test_id("policy-preview").click()
    expect(page.get_by_test_id("policy-confirm-panel")).to_be_visible()
    identifier = page.evaluate("sessionStorage.getItem('policy-settings-job')")
    page.route("**/api/firmware-policy/apply", lose_response)
    page.get_by_test_id("policy-confirmation").fill("CONFIGURE")
    page.get_by_test_id("policy-apply").click()
    expect(page.get_by_test_id("policy-message")).to_contain_text("Check the operation status")
    assert page.evaluate("sessionStorage.getItem('policy-settings-job')") == identifier
    page.reload(wait_until="networkidle")
    expect(page.get_by_test_id("policy-result")).to_contain_text("readback verification")
    expect(page.get_by_test_id("policy-confirm-panel")).to_be_hidden()
    assert len(submitted) == 1
    assert len(sdk.writes) == 2


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
    assert 'data-testid="firmware-policy-workspace"' in page
    choices = client.get("/api/firmware-policy/organizations").get_json()
    assert choices["organizations"][0]["id"] == ORG_ID
    catalog = post(client, "/api/firmware-policy/catalog", {"organizations": [ORG_ID], "kinds": ["ap"]})
    assert set(catalog.get_json()["catalogs"]["ap"]["AP41"]) == {"new", "stable"}
    preview = PolicyJobs.finish(client, post(client, "/api/firmware-policy/preview", preview_body()))
    assert preview["writes"] == 0
    assert preview["settings_count"] == 3
    assert len(preview["organizations"][0]["sites"]) == 2
    assert "private-fixture" not in json.dumps(preview)
    assert session.writes == []
    assert len(list((session.data_directory / ".firmware-policy-backups").glob("*.json"))) == 1
    response = post(client, "/api/firmware-policy/apply", {"token": preview["token"], "confirmation": "CONFIGURE"})
    result = PolicyJobs.finish(client, response)
    assert result["state"] == "complete"
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
    token = PolicyJobs.finish(client, post(client, "/api/firmware-policy/preview", preview_body()))["token"]
    response = post(client, "/api/firmware-policy/apply", {"token": token, "confirmation": confirmation})
    assert response.status_code == 400
    assert "CONFIGURE" in response.get_json()["error"]
    assert session.writes == []


def test_preview_is_session_bound_single_use_and_csrf_protected(policy_portal: tuple[Any, SettingsSession]) -> None:
    """Refuse another browser, a missing CSRF token, and duplicate apply submissions."""
    app, session = policy_portal
    client = app.test_client()
    token = PolicyJobs.finish(client, post(client, "/api/firmware-policy/preview", preview_body()))["token"]
    body = {"token": token, "confirmation": "CONFIGURE"}
    assert client.post("/api/firmware-policy/apply", json=body).status_code == 400
    other = app.test_client()
    assert post(other, "/api/firmware-policy/apply", body).status_code == 400
    assert session.writes == []
    assert PolicyJobs.finish(client, post(client, "/api/firmware-policy/apply", body))["state"] == "complete"
    assert post(client, "/api/firmware-policy/apply", body).status_code == 400
    assert len(session.writes) == 2


def test_portal_backup_failure_returns_error_and_zero_cloud_writes(
    policy_portal: tuple[Any, SettingsSession], monkeypatch: Any
) -> None:
    """Surface an unreadable full settings backup instead of sending a cloud change."""
    app, session = policy_portal
    client = app.test_client()

    def fail_verification(self: PolicyBackup, path: Path, expected: list[dict]) -> None:
        """Simulate a failed durable backup comparison before the first write."""
        raise PolicyError("The settings backup could not be verified.")

    monkeypatch.setattr(PolicyBackup, "verify", fail_verification)
    result = PolicyJobs.finish(client, post(client, "/api/firmware-policy/preview", preview_body()))
    assert result["state"] == "failed"
    assert "backup could not be verified" in result["error"]
    assert not result.get("token")
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

        def corrupt_file(backup: PolicyBackup, document: dict[str, Any], content: bytes = content) -> Path:
            """Corrupt the actual saved file before its shared verification gate."""
            path = create_file(backup, document)
            path.write_bytes(content)
            return path

        monkeypatch.setattr(PolicyBackup, "_create_file", corrupt_file)
        result = PolicyJobs.finish(client, post(client, "/api/firmware-policy/preview", preview_body()))
        assert result["state"] == "failed"
        assert "could not be verified" in result["error"]
        assert session.writes == []
        for path in (session.data_directory / ".firmware-policy-backups").glob("*.json"):
            with pytest.raises(PolicyError, match="could not be verified"):
                backup.verify(path, [])


@pytest.mark.parametrize("status_code", [403, 503])
def test_portal_http_4xx_and_http_5xx_result_reports_partial(
    policy_portal: tuple[Any, SettingsSession], status_code: int
) -> None:
    """A failed site write reports completed organizations and remaining sites."""
    app, session = policy_portal
    client = app.test_client()
    token = PolicyJobs.finish(client, post(client, "/api/firmware-policy/preview", preview_body()))["token"]
    session.fail_write = f"/api/v1/sites/{SITE_ID}/setting"
    session.status = status_code
    response = post(client, "/api/firmware-policy/apply", {"token": token, "confirmation": "CONFIGURE"})
    data = PolicyJobs.finish(client, response)
    assert data["state"] == "partial"
    assert data["result"]["organizations"] == [ORG_ID]
    assert f"HTTP {status_code}" in data["result"]["failures"][0]
    assert len(data["result"]["remaining"]) == 2


def test_portal_backup_download_and_preview_are_denied(policy_portal: tuple[Any, SettingsSession]) -> None:
    """Even a known settings-backup filename cannot be downloaded through data routes."""
    app, session = policy_portal
    path = PolicyBackup(session.data_directory).save(
        [{"scope": "org", "id": ORG_ID, "settings": {"conductor_token": "private-fixture"}}]
    )
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
        expect(page.get_by_test_id("policy-message")).to_contain_text("All backups verified")
        expect(page.get_by_test_id("policy-rows")).to_contain_text("First")
        assert session.writes == []
        assert page.get_by_test_id("policy-apply").is_disabled()
        page.get_by_test_id("policy-confirmation").fill("CONFIGURE")
        page.get_by_test_id("policy-apply").click()
        expect(page.get_by_test_id("policy-message")).to_contain_text("Settings change complete")
        assert "readback verification" in page.get_by_test_id("policy-result").inner_text()
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
