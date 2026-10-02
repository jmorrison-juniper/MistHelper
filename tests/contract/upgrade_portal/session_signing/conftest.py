"""Use real portal sessions and replace only the external cloud transport."""

from __future__ import annotations

import logging
import re
import secrets
from collections.abc import Iterator
from dataclasses import dataclass
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

import pytest
from flask import Flask, session
from flask.testing import FlaskClient
from werkzeug.test import TestResponse

from src.upgrade_portal.app.factory import configure_logging, create_app
from src.upgrade_portal.runtime import identity

logger = logging.getLogger(__name__)


@dataclass
class PortalSessionHarness:
    """Own the application instances, cloud stand-ins, and actual session state."""

    patch: pytest.MonkeyPatch
    materials: dict[str, str]
    registry: identity.SessionRegistry
    applications: list[Flask]
    responses: list[TestResponse]

    def create(self, mode: str = "environment_token") -> Flask:
        """Build the actual application with synthetic cloud transport."""
        logger.info("Build an application for the session signing contract.")
        self.patch.delenv("MIST_APITOKEN", raising=False)
        if mode == "browser_token":
            self.patch.delenv("MIST_API_TOKEN", raising=False)  # The actual startup setting permits this mode.
        else:
            self.patch.setenv("MIST_API_TOKEN", self.materials["api_token"])
        cloud = SimpleNamespace(
            privileges=[{"org_id": "00000000-0000-0000-0000-000000003213", "name": "Synthetic Organization"}],
            login_with_return=Mock(return_value={"authenticated": True}),
        )
        app = create_app()
        app.config.update(
            TESTING=True,
            DEPENDENCY_ROWS=[],  # The external dependency panel must not probe a production store.
            CLOUD_LOGIN=Mock(return_value=cloud),
            CLOUD_TOKEN_SESSION=Mock(return_value=cloud),
            CLOUD_BROWSER_TOKEN_SESSION=Mock(return_value=cloud),
            CLOUD_TOKEN_IDENTITY=Mock(return_value={"name": "synthetic-operator"}),
        )
        self.applications.append(app)
        assert app.config["ORG_UPGRADE_WRITES_ENABLED"] is False
        logger.debug("The test built %s independent applications.", len(self.applications))
        return app

    @staticmethod
    def csrf(response: TestResponse) -> str:
        """Read the actual form token from the rendered portal page."""
        assert response.status_code == 200
        match = re.search(r'name="csrf-token"[^>]*content="([^"]+)"', response.get_data(as_text=True))
        assert isinstance(match, re.Match), "The actual portal page must contain its form token."
        return match.group(1)

    def sign_in(self, mode: str = "environment_token") -> tuple[FlaskClient, str]:
        """Complete the actual sign-in and retain its next form token."""
        logger.info("Run the actual sign-in route in mode %s.", mode)
        client = self.create(mode).test_client()
        page = client.get("/auth/signin")
        response = client.post(
            "/auth/signin",
            json={
                "email": "operator@example.invalid",
                "mode": mode,
                "password": self.materials["password"],
                "token": self.materials["api_token"],
            },
            headers={"X-CSRFToken": self.csrf(page)},
        )
        assert response.status_code == 200
        assert response.get_json() == {"next": "/select/org"}
        organization_page = client.get("/select/org")
        form_token = self.csrf(organization_page)
        assert "Synthetic Organization" in organization_page.get_data(as_text=True)
        self.responses.extend((page, response, organization_page))
        logger.debug("The real registry holds %s authenticated operator.", self.registry.owner_count())
        return client, form_token

    def restart(self, source: FlaskClient, mode: str = "environment_token") -> FlaskClient:
        """Transfer the original cookies to an independent application."""
        logger.info("Transfer the two original cookies to an independent application.")
        client = self.create(mode).test_client()
        for name in ("session", "browser_id"):
            cookie = source.get_cookie(name)
            assert cookie is not None, "The restart proof requires both original cookies."
            client.set_cookie(name, cookie.value)
        logger.debug("The test transferred two cookies without another sign-in.")
        return client

    @staticmethod
    def cookie_fields(client: FlaskClient) -> dict[str, Any]:
        """Read the actual Flask session without changing the client's cookie."""
        cookie = client.get_cookie("session")
        assert cookie is not None, "The session proof requires the actual signed cookie."
        with client.application.test_request_context(headers={"Cookie": f"session={cookie.value}"}):
            return dict(session)  # Flask opens the cookie through its actual session interface.


@pytest.fixture
def signing_environment(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Keep every signing and cloud value private to one synthetic test."""
    materials = {
        "signing_key": secrets.token_urlsafe(32),
        "api_token": "synthetic-issue-3213-api-token-not-a-credential",
        "password": "synthetic-issue-3213-password-not-a-credential",
    }
    for name in ("MIST_APITOKEN", "MIST_API_TOKEN", "CAPTURE_ALLOWED_IPS", "CAPTURE_PROXY_HOPS"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.delenv("ORG_UPGRADE_WRITES_ENABLED", raising=False)
    monkeypatch.setenv("CAPTURE_SECRET_KEY", materials["signing_key"])
    monkeypatch.setenv("MISTHELPER_STANDALONE", "true")
    return materials


@pytest.fixture
def session_harness(
    monkeypatch: pytest.MonkeyPatch,
    signing_environment: dict[str, str],
    caplog: pytest.LogCaptureFixture,
) -> Iterator[PortalSessionHarness]:
    """Isolate the real registry and capture the actual product log records."""
    registry = identity.SessionRegistry()
    monkeypatch.setattr(identity, "SESSION_REGISTRY", registry)
    configure_logging()
    package_logger = logging.getLogger("src.upgrade_portal")
    caplog.set_level(logging.DEBUG, logger=package_logger.name)
    package_logger.addHandler(caplog.handler)  # The product logger deliberately stops root propagation.
    try:
        yield PortalSessionHarness(monkeypatch, signing_environment, registry, [], [])
    finally:
        package_logger.removeHandler(caplog.handler)
