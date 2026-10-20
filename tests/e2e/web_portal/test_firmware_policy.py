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
from tests.e2e.web_portal.firmware_restore.evidence import BrowserEvidence
from tests.unit.prod_readiness.operations.execution.firmware.policy.fakes import ORG_ID, SITE_ID, SettingsSession
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


def test_catalog_route_excludes_srx_from_switch_choices(
    policy_portal: tuple[Any, SettingsSession], monkeypatch: Any
) -> None:
    """Keep mixed SDK rows in their correct hardware groups through the protected route."""
    app, session = policy_portal
    original_get = session.mist_get

    def mixed_get(uri: str, query: dict[str, str] | None = None) -> SimpleNamespace:
        """Return mixed switch rows without a cloud request or a settings change."""
        response = original_get(uri, query)
        if uri.endswith("/devices/versions") and (query or {}).get("type") == "switch":
            response.data.extend([{"model": "SRX320", "version": "stable"}, {"model": "QFX5120", "version": "new"}])
        return response

    monkeypatch.setattr(session, "mist_get", mixed_get)
    response = post(
        app.test_client(),
        "/api/firmware-policy/catalog",
        {"organizations": [ORG_ID], "kinds": ["switch", "juniper_srx"], "show_all": True},
    )
    assert response.status_code == 200, response.get_data(as_text=True)
    assert response.get_json()["catalogs"] == {
        "switch": {"EX4400": ["stable", "new"], "QFX5120": ["new"]},
        "juniper_srx": {"SRX320": ["stable", "new"]},
    }
    assert session.writes == []


def test_http_5xx_boundary_hides_private_response_body() -> None:
    """Reject a server failure without copying its private body into portal errors."""
    response = SimpleNamespace(status_code=503, data={"credential": "private-fixture"})
    with pytest.raises(PolicyError, match="HTTP 503") as failure:
        PolicyResponse.request(lambda: response, "Read settings", ORG_ID)
    assert "private-fixture" not in str(failure.value)
    assert "credential" not in str(failure.value)


@pytest.mark.parametrize("show_all", [False, True])
def test_catalog_route_inventory_default_and_explicit_all(
    policy_portal: tuple[Any, SettingsSession], show_all: bool
) -> None:
    """The protected route defaults to installed models while retaining explicit future equipment."""
    app, sdk = policy_portal
    body: dict[str, Any] = {"organizations": [ORG_ID], "kinds": ["ssr"]}
    if show_all:
        body["show_all"] = True
    response = post(app.test_client(), "/api/firmware-policy/catalog", body)
    assert response.status_code == 200
    expected = {"SSR120": ["6.3.0"], "SSR130": ["6.3.0"]} if show_all else {"SSR120": ["6.3.0"]}
    assert response.get_json() == {"catalogs": {"ssr": expected}}
    assert any(uri.endswith("/inventory") for uri, _ in sdk.reads) == (not show_all)
    assert sdk.writes == []


@pytest.mark.parametrize("value", ["false", 1, None, []])
def test_catalog_route_rejects_nonboolean_display_scope(policy_portal: tuple[Any, SettingsSession], value: Any) -> None:
    """Posted strings must not enable all-model scope through truthiness."""
    app, sdk = policy_portal
    response = post(
        app.test_client(),
        "/api/firmware-policy/catalog",
        {"organizations": [ORG_ID], "kinds": ["ap"], "show_all": value},
    )
    assert response.status_code == 400
    assert "must be a boolean" in response.get_json()["error"]
    assert sdk.reads == []
    assert sdk.writes == []


@pytest.mark.parametrize("status", [403, 503])
def test_catalog_route_inventory_failure_has_no_full_catalog(
    policy_portal: tuple[Any, SettingsSession], status: int
) -> None:
    """HTTP 4xx and 5xx inventory failures retain checked status without private response data."""
    app, sdk = policy_portal
    sdk.fail_read = f"/api/v1/orgs/{ORG_ID}/inventory"
    sdk.status = status
    response = post(app.test_client(), "/api/firmware-policy/catalog", {"organizations": [ORG_ID], "kinds": ["ssr"]})
    assert response.status_code == 400
    assert f"HTTP {status}" in response.get_json()["error"]
    assert "catalogs" not in response.get_json()
    assert "private-fixture" not in response.get_data(as_text=True)
    assert sdk.writes == []


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


def test_browser_inventory_scope_invalidates_prepared_confirmation(
    policy_server: tuple[str, SettingsSession], page: Any
) -> None:
    """Use actual protected routes to reveal absent models and invalidate a verified plan."""
    url, sdk = policy_server
    page.goto(url + "/operations?menu=305", wait_until="networkidle")
    expect(page.get_by_test_id("policy-show-all")).not_to_be_checked()
    page.get_by_test_id("policy-kind-ssr").check()
    page.get_by_test_id("policy-load").click()
    expect(page.get_by_test_id("policy-model-list-ssr").locator("[data-model]")).to_have_count(1)
    expect(page.get_by_test_id("policy-model-list-ssr")).not_to_contain_text("SSR130")
    page.get_by_test_id("policy-show-all").check()
    expect(page.get_by_test_id("policy-preview")).to_be_disabled()
    page.get_by_test_id("policy-load").click()
    expect(page.get_by_test_id("policy-model-list-ssr").locator("[data-model]")).to_have_count(2)
    page.get_by_test_id("policy-model-ssr-1").check()
    page.get_by_test_id("policy-enabled-ssr").select_option("DISABLE")
    page.get_by_test_id("policy-preview").click()
    expect(page.get_by_test_id("policy-confirmation")).to_be_visible(timeout=15000)
    page.reload(wait_until="networkidle")
    expect(page.get_by_test_id("policy-show-all")).to_be_checked()
    expect(page.get_by_test_id("policy-model-ssr-1")).to_be_checked()
    expect(page.get_by_test_id("policy-confirmation")).to_be_visible(timeout=15000)
    page.get_by_test_id("policy-confirmation").fill("CONFIGURE")
    expect(page.get_by_test_id("policy-apply")).to_be_enabled()
    page.get_by_test_id("policy-show-all").uncheck()
    expect(page.get_by_test_id("policy-confirm-panel")).to_be_hidden()
    expect(page.get_by_test_id("policy-preview")).to_be_disabled()
    expect(page.get_by_test_id("policy-models")).not_to_contain_text("SSR130")
    artifact = BrowserEvidence.path("issue-4253-inventory-model-filter.png")
    artifact.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(artifact), full_page=True)
    assert sdk.writes == []


def test_browser_empty_inventory_retains_explicit_all_model_control(
    policy_server: tuple[str, SettingsSession], page: Any, monkeypatch: Any
) -> None:
    """Empty membership stays visible and cannot enable preparation through a state selection."""
    url, sdk = policy_server
    original = sdk.mist_get

    def empty_inventory(uri: str, query: dict[str, str] | None = None) -> SimpleNamespace:
        """Supply an actual successful empty inventory response through the SDK boundary."""
        response = original(uri, query)
        if uri.endswith("/inventory"):
            response.data = []
        return response

    monkeypatch.setattr(sdk, "mist_get", empty_inventory)
    page.goto(url + "/operations?menu=305", wait_until="networkidle")
    page.get_by_test_id("policy-kind-ap").check()
    page.get_by_test_id("policy-load").click()
    expect(page.get_by_test_id("policy-empty-ap")).to_contain_text("No compatible inventory models")
    page.get_by_test_id("policy-enabled-ap").select_option("DISABLE")
    expect(page.get_by_test_id("policy-preview")).to_be_disabled()
    page.get_by_test_id("policy-show-all").check()
    page.get_by_test_id("policy-load").click()
    expect(page.get_by_test_id("policy-model-ap-0")).to_be_visible()
    expect(page.get_by_test_id("policy-empty-ap")).to_have_count(0)
    assert sdk.writes == []


def test_browser_inventory_error_clears_prior_choices_without_fallback(
    policy_server: tuple[str, SettingsSession], page: Any
) -> None:
    """A failed catalog reload cannot preserve old selections or enable preparation."""
    url, sdk = policy_server
    page.goto(url + "/operations?menu=305", wait_until="networkidle")
    page.get_by_test_id("policy-kind-ap").check()
    page.get_by_test_id("policy-load").click()
    expect(page.get_by_test_id("policy-model-ap-0")).to_be_visible()
    sdk.fail_read = f"/api/v1/orgs/{ORG_ID}/inventory"
    sdk.status = 503
    page.get_by_test_id("policy-load").click()
    expect(page.get_by_test_id("policy-message")).to_contain_text("HTTP 503")
    expect(page.get_by_test_id("policy-model-ap-0")).to_have_count(0)
    expect(page.get_by_test_id("policy-preview")).to_be_disabled()
    expect(page.get_by_test_id("policy-show-all")).not_to_be_checked()
    assert sdk.writes == []


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
        expect(version).to_have_value(
            {"ap": "0.15.10", "switch": "DL.10.18.1002", "ssr": "6.0.10-5", "juniper_srx": "23.4R2-S5.5"}[kind]
        )
        manual = next(iter(models.values()))[0]
        version.select_option(manual)
        page.get_by_test_id("policy-model-" + kind + "-0").uncheck()
        expect(version).to_be_hidden()
        page.get_by_test_id("policy-model-" + kind + "-0").check()
        expect(version).to_have_value(manual)
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
        expect(page.get_by_test_id("policy-preview")).to_be_disabled()
        expect(page.get_by_test_id("policy-plan")).to_contain_text("AP41: new")
        page.reload(wait_until="networkidle")
        expect(page.get_by_test_id("policy-confirm-panel")).to_be_visible()
        expect(page.get_by_test_id("policy-preview")).to_be_disabled()
        expect(page.get_by_test_id("policy-plan")).to_contain_text("AP41: new")
        page.get_by_test_id("policy-confirmation").fill("CONFIGURE")
        expect(page.get_by_test_id("policy-apply")).to_be_enabled()
        page.get_by_test_id("policy-kind-ap").uncheck()
        expect(page.get_by_test_id("policy-confirm-panel")).to_be_hidden()
        expect(page.get_by_test_id("policy-plan")).to_be_empty()
        expect(page.get_by_test_id("policy-message")).to_have_text("Selection changed. Prepare backups again.")
        expect(page.get_by_test_id("policy-progress")).to_have_attribute("aria-valuenow", "0")
        assert sdk.writes == []
    finally:
        released.set()


@pytest.mark.parametrize(
    ("failure_stage", "http_status", "expected"),
    [
        ("preparation", 200, "Preparation failed: The backup cannot be restored. No settings changed."),
        ("application", 200, "Saved changes can remain. No settings request will be repeated."),
        ("preparation", 503, "Status could not be read: The backup cannot be restored."),
    ],
)
def test_browser_distinguishes_terminal_failure_from_polling_failure(
    policy_server: tuple[str, SettingsSession], page: Any, failure_stage: str, http_status: int, expected: str
) -> None:
    """Report definite preparation rejection without hiding uncertain application or transport outcomes."""
    url, sdk = policy_server
    page.add_init_script("sessionStorage.setItem('policy-settings-job', 'fixture-failure');")
    page.route(
        "**/api/firmware-policy/jobs/fixture-failure",
        lambda route: route.fulfill(
            status=http_status,
            json={"state": "failed", "failure_stage": failure_stage, "error": "The backup cannot be restored."},
        ),
    )
    page.goto(url + "/operations?menu=305", wait_until="networkidle")
    message = page.get_by_test_id("policy-message")
    expect(message).to_contain_text(expected)
    expect(page.get_by_test_id("policy-confirm-panel")).to_be_hidden()
    if failure_stage == "application" or http_status != 200:
        expect(message).not_to_contain_text("No settings changed.")
    if http_status == 200:
        expect(message).not_to_contain_text("Status could not be read")
        assert page.evaluate("sessionStorage.getItem('policy-settings-job')") is None
    assert sdk.writes == []


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
    assert table.locator("tbody tr:not([hidden])").count() == 50
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


@pytest.mark.parametrize("state", ["preparing", "ready"])
def test_reload_preserves_prepared_form_and_job_during_delayed_identity(
    policy_server: tuple[str, SettingsSession], page: Any, state: str
) -> None:
    """Retain the owned job and exact choices while identity loading finishes after resumed status."""
    url, sdk = policy_server
    page.goto(url + "/operations?menu=305", wait_until="networkidle")
    page.get_by_test_id("policy-kind-ap").check()
    page.get_by_test_id("policy-load").click()
    page.get_by_test_id("policy-enabled-ap").select_option("DISABLE")
    page.get_by_test_id("policy-model-ap-0").check()
    page.get_by_test_id("policy-version-ap-0").select_option("new")
    page.get_by_test_id("policy-time").fill("any")
    page.get_by_test_id("policy-preview").click()
    expect(page.get_by_test_id("policy-confirm-panel")).to_be_visible()
    identifier = page.evaluate("sessionStorage.getItem('policy-settings-job')")
    delayed: list[Any] = []
    page.route("**/api/firmware-policy/organizations", lambda route: delayed.append(route))
    page.route(
        "**/api/firmware-policy/jobs/" + identifier,
        lambda route: route.fulfill(
            json={
                "state": state,
                "token": "fixture-ready" if state == "ready" else None,
                "progress": {"phase": "request_allowance", "completed": 1, "total": 145, "wait_seconds": 7201},
                "rows": [{"scope": "org", "id": ORG_ID, "name": "Fixture", "backup": "verified", "status": "ready"}],
            }
        ),
    )
    with page.expect_request("**/api/firmware-policy/organizations"):
        page.reload(wait_until="domcontentloaded")
    message = page.get_by_test_id("policy-message")
    expect(message).to_contain_text("All backups verified" if state == "ready" else "7201 seconds")
    assert page.evaluate("sessionStorage.getItem('policy-settings-job')") == identifier
    assert len(delayed) == 1
    delayed[0].fulfill(json={"count": 1, "organizations": [{"id": ORG_ID, "name": "Fixture"}]})
    expect(page.get_by_test_id("policy-time")).to_have_value("any")
    expect(page.get_by_test_id("policy-enabled-ap")).to_have_value("DISABLE")
    expect(page.get_by_test_id("policy-model-ap-0")).to_be_checked()
    expect(page.get_by_test_id("policy-version-ap-0")).to_have_value("new")
    expect(message).to_contain_text("All backups verified" if state == "ready" else "7201 seconds")
    assert page.evaluate("sessionStorage.getItem('policy-settings-job')") == identifier
    assert sdk.writes == []


def preview_body() -> dict[str, Any]:
    """Supply a complete explicit disabled AP policy without firmware execution."""
    return {
        "organizations": [ORG_ID],
        "policies": [{"kind": "ap", "enabled": False, "models": {"AP41": "new"}, "day": "mon", "time": "02:00"}],
    }


def prepare_browser_policy(page: Any, url: str) -> None:
    """Create a genuine ready fixture plan through the protected graphical controls."""
    page.goto(url + "/operations?menu=305", wait_until="networkidle")
    page.get_by_test_id("policy-kind-ap").check()
    page.get_by_test_id("policy-load").click()
    page.get_by_test_id("policy-enabled-ap").select_option("DISABLE")
    page.get_by_test_id("policy-model-ap-0").check()
    page.get_by_test_id("policy-version-ap-0").select_option("new")
    page.get_by_test_id("policy-preview").click()
    expect(page.get_by_test_id("policy-confirm-panel")).to_be_visible()


def test_browser_expands_owned_preconfirmation_comparison_without_writes(
    policy_server: tuple[str, SettingsSession], page: Any
) -> None:
    """Keyboard expansion displays textual differences and retained saved field absence."""
    url, sdk = policy_server
    page.set_viewport_size({"width": 800, "height": 1000})
    prepare_browser_policy(page, url)
    button = page.get_by_test_id("policyRows-inspect-org-" + ORG_ID)
    button.focus()
    page.keyboard.press("Enter")
    expect(button).to_have_attribute("aria-expanded", "true")
    comparison = page.get_by_test_id("firmware-comparison-table")
    expect(comparison).to_contain_text("Current observation")
    expect(comparison).to_contain_text("Proposed settings")
    expect(comparison).to_contain_text("Proposed change")
    expect(comparison).to_contain_text("Missing field")
    assert comparison.locator("dd.fw-bold").count() > 0
    assert (
        comparison.evaluate(
            "(element) => element.scrollWidth <= element.clientWidth + 1 && "
            "[...element.querySelectorAll('h6, dt, dd')].every(cell => "
            "cell.scrollWidth <= cell.clientWidth + 1 && cell.getBoundingClientRect().right <= window.innerWidth)"
        )
        is True
    )
    assert (
        page.locator("#policyRows .table-responsive").evaluate(
            "(element) => element.scrollLeft === 0 && element.scrollWidth <= element.clientWidth + 1"
        )
        is True
    )
    assert "private-fixture" not in comparison.inner_text()
    expect(page.get_by_test_id("policy-preview")).to_be_disabled()
    page.get_by_test_id("policy-confirmation").fill("CONFIGURE")
    expect(page.get_by_test_id("policy-apply")).to_be_enabled()
    assert sdk.writes == []
    artifact = BrowserEvidence.path("issue-4229-policy-comparison.png")
    artifact.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(artifact), full_page=True)
    button.focus()
    page.keyboard.press("Enter")
    expect(button).to_have_attribute("aria-expanded", "false")


def test_browser_historical_view_and_explicit_current_comparison_are_read_only(
    policy_server: tuple[str, SettingsSession], page: Any
) -> None:
    """Historical inspection remains available after synthetic settings changes without preparation."""
    url, sdk = policy_server
    page.set_viewport_size({"width": 800, "height": 1000})
    prepare_browser_policy(page, url)
    source = next((sdk.data_directory / ".firmware-policy-backups").glob("*.json"))
    original = source.read_bytes()
    sdk.settings[f"/api/v1/sites/{SITE_ID}/setting"]["auto_upgrade"]["enabled"] = True
    page.goto(url + "/operations?menu=306", wait_until="networkidle")
    page.get_by_test_id("restore-bundle").select_option(source.stem)
    page.get_by_test_id("history-record").select_option("site:" + SITE_ID)
    start = len(sdk.reads)
    page.get_by_test_id("history-view").click()
    history = page.get_by_test_id("history-comparison")
    expect(history).to_contain_text("Current settings not requested")
    assert not [uri for uri, _ in sdk.reads[start:] if uri.endswith("/setting")]
    expect(page.get_by_test_id("restore-confirm-panel")).to_be_hidden()
    page.get_by_test_id("history-compare").click()
    expect(history).to_contain_text("Current differs from saved")
    expect(history).to_contain_text("Current settings observed at")
    assert history.evaluate("(element) => element.scrollWidth <= element.clientWidth + 1") is True
    assert source.read_bytes() == original
    assert len(list(source.parent.glob("*.json"))) == 1
    assert sdk.writes == []
    artifact = BrowserEvidence.path("issue-4229-history-comparison.png")
    artifact.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(artifact), full_page=True)


def test_browser_restore_comparison_does_not_consume_ready_restoration(
    policy_server: tuple[str, SettingsSession], page: Any
) -> None:
    """Show historical and verified recovery columns while keeping restoration confirmation available."""
    url, sdk = policy_server
    page.set_viewport_size({"width": 800, "height": 1000})
    prepare_browser_policy(page, url)
    source = next((sdk.data_directory / ".firmware-policy-backups").glob("*.json"))
    page.goto(url + "/operations?menu=306", wait_until="networkidle")
    page.get_by_test_id("restore-bundle").select_option(source.stem)
    page.get_by_test_id("restore-all").check()
    page.get_by_test_id("restore-cloud").fill("api.mist.com")
    page.get_by_test_id("restore-preview-button").click()
    expect(page.get_by_test_id("restore-confirm-panel")).to_be_visible()
    expect(page.get_by_test_id("restore-preview-button")).to_be_disabled()
    button = page.get_by_test_id("restoreRows-inspect-site-" + SITE_ID)
    button.click()
    comparison = page.get_by_test_id("firmware-comparison-table")
    expect(comparison).to_contain_text("Verified recovery backup")
    expect(comparison).to_contain_text("Proposed settings")
    assert comparison.evaluate("(element) => element.scrollWidth <= element.clientWidth + 1") is True
    assert (
        page.locator("#restoreRows .table-responsive").evaluate(
            "(element) => element.scrollLeft === 0 && element.scrollWidth <= element.clientWidth + 1"
        )
        is True
    )
    expect(page.locator("#restoreRows")).to_contain_text("Proposed normalization")
    page.get_by_test_id("restore-confirmation").fill("RESTORE")
    expect(page.get_by_test_id("restore-apply")).to_be_enabled()
    assert len(list(source.parent.glob("*.json"))) == 2
    assert sdk.writes == []


def test_browser_definite_preparation_failure_allows_one_deliberate_retry(
    policy_server: tuple[str, SettingsSession], page: Any, monkeypatch: Any
) -> None:
    """Unlock preparation only after a checked preparation failure, then lock its successful retry."""
    url, sdk = policy_server
    verify = PolicyBackup.verify
    attempts = []

    def fail_once(backup: PolicyBackup, path: Path, records: list[dict[str, Any]]) -> None:
        """Reject the first synthetic verification without changing cloud settings."""
        attempts.append(path)
        if len(attempts) == 1:
            raise PolicyError("The settings backup could not be verified.")
        verify(backup, path, records)

    monkeypatch.setattr(PolicyBackup, "verify", fail_once)
    page.goto(url + "/operations?menu=305", wait_until="networkidle")
    page.get_by_test_id("policy-kind-ap").check()
    page.get_by_test_id("policy-load").click()
    page.get_by_test_id("policy-enabled-ap").select_option("DISABLE")
    page.get_by_test_id("policy-model-ap-0").check()
    page.get_by_test_id("policy-preview").click()
    expect(page.get_by_test_id("policy-message")).to_contain_text("Preparation failed")
    expect(page.get_by_test_id("policy-preview")).to_be_enabled()
    page.get_by_test_id("policy-preview").click()
    expect(page.get_by_test_id("policy-confirm-panel")).to_be_visible()
    expect(page.get_by_test_id("policy-preview")).to_be_disabled()
    assert len(set(attempts)) == 2
    assert sdk.writes == []


def test_browser_lost_preparation_response_remains_locked_after_reload(
    policy_server: tuple[str, SettingsSession], page: Any
) -> None:
    """An unavailable admission response cannot authorize an accidental second backup."""
    url, sdk = policy_server
    submitted = []

    def lose_response(route: Any) -> None:
        """Drop a synthetic admission response after recording its single request."""
        submitted.append(route.request.url)
        route.abort()

    page.route("**/api/firmware-policy/preview", lose_response)
    page.goto(url + "/operations?menu=305", wait_until="networkidle")
    page.get_by_test_id("policy-kind-ap").check()
    page.get_by_test_id("policy-load").click()
    page.get_by_test_id("policy-enabled-ap").select_option("DISABLE")
    page.get_by_test_id("policy-model-ap-0").check()
    page.get_by_test_id("policy-preview").click()
    expect(page.get_by_test_id("policy-message")).to_contain_text("Check the operation status")
    expect(page.get_by_test_id("policy-preview")).to_be_disabled()
    page.reload(wait_until="networkidle")
    expect(page.get_by_test_id("policy-preview")).to_be_disabled()
    assert len(submitted) == 1
    assert sdk.writes == []


def test_inspection_routes_require_owner_csrf_and_exact_read_only_selection(
    policy_portal: tuple[Any, SettingsSession],
) -> None:
    """Protect firmware field responses without consuming the owner's ready proof."""
    app, sdk = policy_portal
    client = app.test_client()
    preview = PolicyJobs.finish(client, post(client, "/api/firmware-policy/preview", preview_body()))
    endpoint = "/api/firmware-policy/jobs/" + preview["job_id"] + "/comparison"
    body = {"scope": "site", "id": SITE_ID}
    assert client.post(endpoint, json=body).status_code == 400
    assert post(app.test_client(), endpoint, body).status_code == 404
    result = post(client, endpoint, body)
    assert result.status_code == 200
    assert result.get_json()["scope"] == "site"
    assert "private-fixture" not in result.get_data(as_text=True)
    invalid = post(client, endpoint, {**body, "settings": {"private": "invalid"}})
    assert invalid.status_code == 400
    current = client.get("/api/firmware-policy/jobs/" + preview["job_id"]).get_json()
    assert current["token"] == preview["token"]
    assert current["state"] == "ready"
    assert sdk.writes == []


@pytest.mark.parametrize("status", [403, 503])
def test_historical_route_current_read_failure_hides_private_response(
    policy_portal: tuple[Any, SettingsSession], status: int
) -> None:
    """A failed current comparison cannot return saved values as a success-shaped fallback."""
    app, sdk = policy_portal
    client = app.test_client()
    preview = PolicyJobs.finish(client, post(client, "/api/firmware-policy/preview", preview_body()))
    source = next((sdk.data_directory / ".firmware-policy-backups").glob("*.json"))
    sdk.fail_read = f"/api/v1/sites/{SITE_ID}/setting"
    sdk.status = status
    result = post(
        client, "/api/settings-restore/inspect", {"bundle": source.stem, "record": "site:" + SITE_ID, "compare": True}
    )
    assert result.status_code == 400
    assert f"HTTP {status}" in result.get_json()["error"]
    assert "private-fixture" not in result.get_data(as_text=True)
    assert "fields" not in result.get_json()
    assert client.get("/api/firmware-policy/jobs/" + preview["job_id"]).get_json()["token"] == preview["token"]
    assert sdk.writes == []


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
