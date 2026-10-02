"""Keep signing keys and synthetic credentials out of every product exit."""

from __future__ import annotations

import json
import logging
import secrets
from http.cookies import SimpleCookie
from unittest.mock import Mock

import pytest
from flask.testing import FlaskClient

from .conftest import PortalSessionHarness


def assert_private_surfaces(
    harness: PortalSessionHarness, client: FlaskClient, caplog: pytest.LogCaptureFixture
) -> None:
    """Inspect bodies, HTML, headers, decoded cookies, and actual log records."""
    surfaces = [json.dumps(harness.cookie_fields(client))]
    serializer = client.application.session_interface.get_signing_serializer(client.application)
    assert serializer is not None, "The configured application must provide its actual cookie serializer."
    for response in harness.responses:
        surfaces.extend((response.get_data(as_text=True), str(response.headers)))
        for header in response.headers.getlist("Set-Cookie"):
            cookies = SimpleCookie()
            cookies.load(header)
            if "session" in cookies and cookies["session"].value:
                surfaces.append(json.dumps(serializer.loads(cookies["session"].value)))
    formatter = logging.Formatter()
    for record in caplog.records:
        surfaces.extend((record.getMessage(), repr(record.args)))
        if record.exc_info:
            surfaces.append(formatter.formatException(record.exc_info))
    for private_value in harness.materials.values():
        assert all(private_value not in surface for surface in surfaces), "A private value left a product exit."
    print(f"session_signing_privacy: surfaces_checked={len(surfaces)} private_values_checked={len(harness.materials)}")


@pytest.mark.parametrize("mode", ["environment_token", "browser_token", "provider_login"])
def test_authenticated_restart_has_no_credential_exit(
    session_harness: PortalSessionHarness, caplog: pytest.LogCaptureFixture, mode: str
) -> None:
    """Sign-in and same-key application recreation expose no key or credential."""
    first, _ = session_harness.sign_in(mode)
    restarted = session_harness.restart(first, mode)
    response = restarted.get("/select/org")
    assert response.status_code == 200
    session_harness.responses.append(response)
    assert_private_surfaces(session_harness, restarted, caplog)


@pytest.mark.parametrize("mode", ["environment_token", "browser_token", "provider_login"])
@pytest.mark.parametrize("accept", ["application/json", "text/html"])
def test_refused_cloud_transport_exposes_no_credential(
    session_harness: PortalSessionHarness, caplog: pytest.LogCaptureFixture, mode: str, accept: str
) -> None:
    """A transport exception cannot publish its synthetic credential text."""
    client = session_harness.create(mode).test_client()
    builder = Mock(side_effect=ConnectionError(session_harness.materials["api_token"]))
    for name in ("CLOUD_TOKEN_SESSION", "CLOUD_BROWSER_TOKEN_SESSION", "CLOUD_LOGIN"):
        client.application.config[name] = builder
    page = client.get("/auth/signin")
    body = {"email": "operator@example.invalid", "mode": mode}
    body.update(password=session_harness.materials["password"], token=session_harness.materials["api_token"])
    response = client.post(
        "/auth/signin",
        json=body,
        headers={"X-CSRFToken": session_harness.csrf(page), "Accept": accept},
    )
    assert response.status_code == 400
    assert builder.call_count == 1
    if accept == "application/json":
        assert response.get_json()["error"]["code"] == "bad_credentials"
    else:
        assert 'data-testid="signin-error"' in response.get_data(as_text=True)
    session_harness.responses.extend((page, response))
    assert "owner_key" not in session_harness.cookie_fields(client)
    assert_private_surfaces(session_harness, client, caplog)


def test_anonymous_cookie_has_no_credential(
    session_harness: PortalSessionHarness, caplog: pytest.LogCaptureFixture
) -> None:
    """An unauthorized browser receives only safe anonymous session state."""
    client = session_harness.create().test_client()
    page = client.get("/auth/signin")
    assert page.status_code == 200
    refusal = client.get("/select/org", headers={"Accept": "application/json"})
    assert refusal.status_code == 401
    assert refusal.get_json()["error"]["code"] == "not_authenticated"
    session_harness.responses.extend((page, refusal))
    assert set(session_harness.cookie_fields(client)) == {"csrf_token"}
    assert_private_surfaces(session_harness, client, caplog)


def test_changed_key_refusal_has_no_credential(
    session_harness: PortalSessionHarness, caplog: pytest.LogCaptureFixture
) -> None:
    """The invalid-cookie control exposes neither the original key nor its replacement."""
    first, _ = session_harness.sign_in()
    assert_private_surfaces(session_harness, first, caplog)
    session_harness.materials["replacement_key"] = secrets.token_urlsafe(32)
    session_harness.patch.setenv("CAPTURE_SECRET_KEY", session_harness.materials["replacement_key"])
    restarted = session_harness.restart(first)
    refusal = restarted.get("/select/org", headers={"Accept": "application/json"})
    assert refusal.status_code == 401
    assert refusal.get_json()["error"]["code"] == "not_authenticated"
    session_harness.responses[:] = [refusal]  # Old cookies need their original serializer, already checked above.
    assert session_harness.cookie_fields(restarted) == {}
    assert_private_surfaces(session_harness, restarted, caplog)
