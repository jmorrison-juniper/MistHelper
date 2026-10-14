"""Exercise protected restoration APIs and actual Chromium completion and failure flows."""

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

from src.foundation.support.utils.rate_limiting import RateLimitingUtils
from src.operations.execution.firmware_policy.sdk import PolicyError
from tests.e2e.web_portal.test_firmware_policy import PolicyJobs
from tests.unit.firmware_policy.fakes import ORG_ID, SITE_ID
from tests.unit.firmware_policy.recovery.fakes import RestoreSession
from web_portal.app import WebPortalApp
from web_portal.routes.firmware_policy.restore import RestoreInputs


@pytest.fixture
def restore_portal(tmp_path: Path, monkeypatch: Any) -> Iterator[tuple[Any, RestoreSession]]:
    """Build the production portal with a private fixture bundle and mocked SDK."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setattr(RateLimitingUtils, "get_rate_limited_delay", lambda *_args: (0.0, 0.0))
    sdk = RestoreSession(tmp_path)
    app = WebPortalApp.create_app(sdk, {}, ORG_ID)
    app.config["TESTING"] = True
    yield app, sdk
    WebPortalApp.shutdown_app(app)


class RestoreRequests:
    """Use actual CSRF tokens for every mutation endpoint under test."""

    @staticmethod
    def post(client: Any, endpoint: str, body: Any, raw: bool = False) -> Any:
        """Send a protected request using the rendered restore page's token."""
        page = client.get("/operations/settings-restore", follow_redirects=True).get_data(as_text=True)
        match = re.search(r'<meta name="csrf-token" content="([^"]+)"', page)
        assert match is not None
        options = {"data": body, "content_type": "application/json"} if raw else {"json": body}
        return client.post("/api/settings-restore/" + endpoint, **options, headers={"X-CSRFToken": match.group(1)})

    @staticmethod
    def preview(client: Any, sdk: RestoreSession) -> Any:
        """Select explicit saved organization and site identifiers on the active cloud."""
        return PolicyJobs.finish(
            client,
            RestoreRequests.post(
                client,
                "preview",
                {
                    "bundle": sdk.path.stem,
                    "records": [f"org:{ORG_ID}", f"site:{SITE_ID}"],
                    "cloud": sdk.cloud,
                },
            ),
        )


class TestRestorePortal:
    """Prove privacy and pre-write failure behavior through real portal middleware."""

    @pytest.mark.parametrize("body", [b"", b"bad json"])
    def test_fresh_portal_rejects_unreadable_json(self, tmp_path: Path, monkeypatch: Any, body: bytes) -> None:
        """Reject unreadable input before any prepared plan exists in a fresh application."""
        monkeypatch.setenv("DATA_DIR", str(tmp_path))
        sdk = RestoreSession(tmp_path)
        app = WebPortalApp.create_app(sdk, {}, ORG_ID)
        try:
            with app.test_request_context(data=body, content_type="application/json"):
                with pytest.raises(PolicyError, match="required restoration request fields"):
                    RestoreInputs.body({"token", "confirmation"})
            assert sdk.reads == []
            assert sdk.writes == []
        finally:
            WebPortalApp.shutdown_app(app)

    def test_full_api_flow_and_private_output_denial(self, restore_portal: tuple[Any, RestoreSession]) -> None:
        """Preview and restore the full writable snapshot without exposing credentials."""
        app, sdk = restore_portal
        client = app.test_client()
        original = sdk.path.read_bytes()
        assert 'data-testid="settings-restore-workspace"' in client.get("/operations").get_data(as_text=True)
        listing = client.get("/api/settings-restore/bundles")
        assert listing.status_code == 200
        assert listing.get_json()["bundles"][0]["record_count"] == 2
        data = RestoreRequests.preview(client, sdk)
        assert data["state"] == "ready"
        assert data["writes"] == 0
        assert sdk.writes == []
        response = RestoreRequests.post(client, "apply", {"token": data["token"], "confirmation": "RESTORE"})
        result = PolicyJobs.finish(client, response)
        assert result["state"] == "complete"
        assert result["result"]["backups_verified"] == 2
        assert result["result"]["completed"] == [f"org:{ORG_ID}", f"site:{SITE_ID}"]
        assert sdk.path.read_bytes() == original
        relative = sdk.path.relative_to(sdk.data_directory).as_posix()
        assert client.get("/api/data/download/" + relative).status_code == 404
        assert client.get("/api/data/preview/" + relative).status_code == 404
        assert "private-fixture" not in listing.get_data(as_text=True) + json.dumps(data) + json.dumps(result)

    @pytest.mark.parametrize("body", [b"", b"bad json", b"[]", b'{"token":"x","confirmation":"RESTORE","settings":{}}'])
    def test_empty_body_and_malformed_json_input_fails(
        self, restore_portal: tuple[Any, RestoreSession], body: bytes
    ) -> None:
        """Malformed or injected posted settings must not become SDK request bodies."""
        app, sdk = restore_portal
        with app.test_request_context(data=body, content_type="application/json"):
            with pytest.raises(PolicyError, match="required restoration request fields"):
                RestoreInputs.body({"token", "confirmation"})
        response = RestoreRequests.post(app.test_client(), "apply", body, raw=True)
        assert response.status_code == 400
        assert sdk.reads == []
        assert sdk.writes == []

    def test_csrf_owner_cancel_and_repeat(self, restore_portal: tuple[Any, RestoreSession]) -> None:
        """Every prepared operation remains private, cancelable, and single-use."""
        app, sdk = restore_portal
        client = app.test_client()
        token = RestoreRequests.preview(client, sdk)["token"]
        body = {"token": token, "confirmation": "RESTORE"}
        assert client.post("/api/settings-restore/apply", json=body).status_code == 400
        assert RestoreRequests.post(app.test_client(), "apply", body).status_code == 400
        assert RestoreRequests.post(client, "apply", {"token": token, "confirmation": "RESTORE "}).status_code == 400
        assert RestoreRequests.post(client, "cancel", {"token": token}).get_json()["writes"] == 0
        assert RestoreRequests.post(client, "apply", body).status_code == 400
        assert sdk.writes == []
        token = RestoreRequests.preview(client, sdk)["token"]
        body = {"token": token, "confirmation": "RESTORE"}
        assert PolicyJobs.finish(client, RestoreRequests.post(client, "apply", body))["state"] == "complete"
        assert RestoreRequests.post(client, "apply", body).status_code == 400
        assert len(sdk.writes) == 2

    @pytest.mark.parametrize("status", [403, 503])
    def test_failed_write_reports_partial(self, restore_portal: tuple[Any, RestoreSession], status: int) -> None:
        """Do not convert HTTP failures into a successful graphical completion."""
        app, sdk = restore_portal
        client = app.test_client()
        token = RestoreRequests.preview(client, sdk)["token"]
        sdk.fail_write = f"/api/v1/orgs/{ORG_ID}/setting"
        sdk.status = status
        result = PolicyJobs.finish(
            client, RestoreRequests.post(client, "apply", {"token": token, "confirmation": "RESTORE"})
        )
        assert result["state"] == "partial"
        assert result["result"]["failed"] == [f"org:{ORG_ID}"]
        assert result["result"]["remaining"] == [f"site:{SITE_ID}"]
        assert f"HTTP {status}" in result["result"]["error"]
        assert "private-fixture" not in json.dumps(result)


@pytest.mark.parametrize("failure", [False, True])
def test_chromium_selection_preview_confirmation_and_result(
    restore_portal: tuple[Any, RestoreSession], page: Any, failure: bool, pytestconfig: pytest.Config
) -> None:
    """Drive the production template and dynamic scripts against mocked SDK requests."""
    app, sdk = restore_portal
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    evidence = (
        pytestconfig.rootpath / "test-artifacts" / ("issue4218-partial.png" if failure else "issue4218-complete.png")
    )
    evidence.parent.mkdir(parents=True, exist_ok=True)
    try:
        page.goto(f"http://127.0.0.1:{server.server_port}/operations/settings-restore", wait_until="networkidle")
        expect(page.get_by_test_id("restore-active-cloud")).to_have_text(sdk.cloud)
        page.get_by_test_id("restore-bundle").select_option(sdk.path.stem)
        page.get_by_test_id(f"restore-record-org-{ORG_ID}").check()
        page.get_by_test_id(f"restore-record-site-{SITE_ID}").check()
        page.get_by_test_id("restore-cloud").fill(sdk.cloud)
        page.get_by_test_id("restore-preview-button").click()
        expect(page.get_by_test_id("restore-message")).to_contain_text("All backups verified")
        expect(page.get_by_test_id("restore-rows")).to_contain_text("First")
        assert sdk.writes == []
        expect(page.get_by_test_id("restore-apply")).to_be_disabled()
        page.get_by_test_id("restore-confirmation").fill("RESTORE ")
        expect(page.get_by_test_id("restore-apply")).to_be_disabled()
        page.get_by_test_id("restore-confirmation").fill("RESTORE")
        if failure:
            sdk.fail_write = f"/api/v1/orgs/{ORG_ID}/setting"
        page.get_by_test_id("restore-apply").click()
        expect(page.get_by_test_id("restore-result")).to_contain_text(
            "failed targets" if failure else "readback verification"
        )
        assert len(sdk.writes) == (1 if failure else 2)
        assert "private-fixture" not in page.content()
        page.screenshot(path=str(evidence), full_page=True)
    except BaseException:
        page.screenshot(path=str(evidence.with_name("issue4218-failed-flow.png")), full_page=True)
        raise
    finally:
        server.shutdown()
        thread.join(timeout=10)
