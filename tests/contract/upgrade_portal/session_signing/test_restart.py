"""Prove signed-cookie restart behavior without pretending authentication persists."""

from __future__ import annotations

import logging
import secrets

import pytest

from src.upgrade_portal.runtime import identity

from .conftest import PortalSessionHarness


class TestSessionSigningRestart:
    """Keep signing decisions and server-side authentication decisions separate."""

    @pytest.mark.parametrize("mode", ["environment_token", "browser_token", "provider_login"])
    def test_same_key_accepts_original_cookie_and_form_token(
        self, session_harness: PortalSessionHarness, mode: str
    ) -> None:
        """A new application accepts actual cookies when authentication state remains."""
        first, form_token = session_harness.sign_in(mode)
        original_fields = session_harness.cookie_fields(first)
        restarted = session_harness.restart(first, mode)
        assert first.application is not restarted.application
        assert session_harness.cookie_fields(restarted) == original_fields
        page = restarted.get("/select/org")
        assert page.status_code == 200
        assert "Synthetic Organization" in page.get_data(as_text=True)
        response = restarted.post(
            "/select/org",
            json={"org_id": "00000000-0000-0000-0000-000000003213"},
            headers={"X-CSRFToken": form_token},
        )
        assert response.status_code == 200
        assert response.get_json() == {"next": "/select/mode"}
        session_harness.responses.extend((page, response))
        print(f"session_signing_restart: mode={mode} applications=2 cookies=2 decisions_checked=3 status=pass")

    @pytest.mark.parametrize("mode", ["environment_token", "browser_token", "provider_login"])
    def test_changed_key_rejects_the_same_cookie(self, session_harness: PortalSessionHarness, mode: str) -> None:
        """Changing only the key invalidates the original session and form token."""
        first, form_token = session_harness.sign_in(mode)
        session_harness.patch.setenv("CAPTURE_SECRET_KEY", secrets.token_urlsafe(32))
        restarted = session_harness.restart(first, mode)
        assert restarted.get_cookie("session").value == first.get_cookie("session").value
        assert session_harness.cookie_fields(restarted) == {}
        page = restarted.get("/select/org", headers={"Accept": "application/json"})
        assert page.status_code == 401
        assert page.get_json()["error"]["code"] == "not_authenticated"
        response = restarted.post(
            "/select/org",
            json={"org_id": "00000000-0000-0000-0000-000000003213"},
            headers={"X-CSRFToken": form_token},
        )
        assert response.status_code == 400
        assert response.get_json()["error"]["code"] == "csrf_missing"
        assert session_harness.registry.owner_count() == 1  # Authentication remains, so only signing caused refusal.
        print(f"session_signing_restart: mode={mode} applications=2 cookies=2 decisions_checked=3 changed_key=refused")

    @pytest.mark.parametrize("browser_cookie", ["missing", "different"])
    def test_browser_binding_still_applies(self, session_harness: PortalSessionHarness, browser_cookie: str) -> None:
        """A valid signed session cannot replace its required browser identifier."""
        first, _ = session_harness.sign_in()
        restarted = session_harness.restart(first)
        original_fields = session_harness.cookie_fields(first)
        if browser_cookie == "missing":
            restarted.delete_cookie("browser_id")
        else:
            restarted.set_cookie("browser_id", identity.issue_browser_id())
        assert session_harness.cookie_fields(restarted) == original_fields
        response = restarted.get("/select/org", headers={"Accept": "application/json"})
        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "not_authenticated"
        print("session_signing_restart: applications=2 decisions_checked=2 browser_binding=refused")

    @pytest.mark.parametrize("mode", ["environment_token", "browser_token", "provider_login"])
    def test_worker_registry_loss_does_not_invalidate_the_cookie(
        self, session_harness: PortalSessionHarness, mode: str
    ) -> None:
        """A cold worker retains valid cookie contents but requires another sign-in."""
        first, form_token = session_harness.sign_in(mode)
        original_fields = session_harness.cookie_fields(first)
        session_harness.registry = identity.SessionRegistry()
        session_harness.patch.setattr(identity, "SESSION_REGISTRY", session_harness.registry)
        restarted = session_harness.restart(first, mode)
        assert session_harness.registry.owner_count() == 0
        assert session_harness.cookie_fields(restarted) == original_fields
        response = restarted.get("/select/org", headers={"Accept": "application/json"})
        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "not_authenticated"
        refused_form = restarted.post(
            "/select/org",
            json={"org_id": "00000000-0000-0000-0000-000000003213"},
            headers={"X-CSRFToken": form_token},
        )
        assert refused_form.status_code == 401  # The actual form-token guard passed before authentication refused.
        assert refused_form.get_json()["error"]["code"] == "not_authenticated"
        print(f"session_signing_restart: mode={mode} applications=2 decisions_checked=3 cookie=valid registry=empty")

    def test_unset_key_keeps_random_development_signing(
        self, session_harness: PortalSessionHarness, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An unset key still warns and invalidates the cookie on application recreation."""
        session_harness.patch.delenv("CAPTURE_SECRET_KEY", raising=False)
        first, _ = session_harness.sign_in()
        restarted = session_harness.restart(first)
        assert first.application.secret_key != restarted.application.secret_key
        assert session_harness.cookie_fields(restarted) == {}
        response = restarted.get("/select/org", headers={"Accept": "application/json"})
        assert response.status_code == 401
        warnings = [record for record in caplog.records if "CAPTURE_SECRET_KEY" in record.getMessage()]
        assert len(warnings) == 2
        assert all(record.levelno == logging.WARNING for record in warnings)
        assert all(record.args == ("CAPTURE_SECRET_KEY",) for record in warnings)
        assert all(
            record.getMessage()
            == "The variable CAPTURE_SECRET_KEY is empty. The portal signs the session with a new key."
            for record in warnings
        )
        print(
            "session_signing_restart: applications=2 warnings_checked=2 decisions_checked=3 development_cookie=refused"
        )
