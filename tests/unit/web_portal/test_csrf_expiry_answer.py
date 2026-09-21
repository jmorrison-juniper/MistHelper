"""Guard the answer the portal sends when a session expires.

Issue #3087: an operator whose session expired clicked Run and read this.

```text
Failed to start operation: Failed to execute 'json' on 'Response':
Unexpected token '<', "<!doctype "... is not valid JSON
```

The real cause was a stale CSRF token. `flask-wtf` answers a CSRF failure with
the default Flask error page, which is HTML, and every portal caller read the
answer with `response.json()`. The parser raised, and the operator read the
parser message instead of the reason.

These tests hold the server half of the repair. An API caller receives JSON
that names the cause and the action, and a browser form keeps the HTML page it
already expects.
"""

from __future__ import annotations

import json

import pytest
from flask import Flask

from web_portal.services.config import SESSION_EXPIRED_MESSAGE, SecurityMiddleware


@pytest.fixture()
def csrf_app():
    """Build a small Flask application that protects one API route and one form route."""
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test-secret"  # nosec B105 - a test fixture, never a deployed value.
    app.config["WTF_CSRF_ENABLED"] = True
    SecurityMiddleware()._configure_csrf(app)  # Install the handler under test.

    @app.route("/api/operations/run", methods=["POST"])
    def run():  # pragma: no cover - the CSRF check rejects before the body runs.
        return {"run_id": "never-reached"}

    @app.route("/settings", methods=["POST"])
    def settings():  # pragma: no cover - the CSRF check rejects before the body runs.
        return "saved"

    return app


class TestApiCallerReadsAReason:
    """An API caller must receive JSON that states the cause and the action."""

    def test_stale_token_answers_json(self, csrf_app):
        """The answer must parse as JSON, because the browser calls the JSON reader."""
        client = csrf_app.test_client()
        response = client.post(
            "/api/operations/run",
            json={"menu_number": "1"},
            headers={"X-CSRFToken": "stale-token-value"},
        )
        assert response.status_code == 400  # Keep the status flask-wtf already used.
        assert response.mimetype == "application/json"
        json.loads(response.get_data(as_text=True))  # This raised JSONDecodeError before the repair.

    def test_reason_names_the_cause_and_the_action(self, csrf_app):
        """The message must tell the operator what happened and what to do."""
        client = csrf_app.test_client()
        response = client.post(
            "/api/operations/run",
            json={"menu_number": "1"},
            headers={"X-CSRFToken": "stale-token-value"},
        )
        payload = response.get_json()
        assert payload["error"] == SESSION_EXPIRED_MESSAGE
        assert "Reload the page" in payload["error"]  # The operator needs one clear action.
        assert payload["code"] == "csrf_expired"  # A caller can branch without reading prose.

    def test_body_is_not_an_html_error_page(self, csrf_app):
        """The reported defect was an HTML body, so no answer may start a document."""
        client = csrf_app.test_client()
        response = client.post("/api/operations/run", json={}, headers={"X-CSRFToken": "stale"})
        body = response.get_data(as_text=True)
        assert not body.lstrip().lower().startswith("<!doctype")
        assert "<html" not in body.lower()

    def test_missing_token_answers_json_too(self, csrf_app):
        """A request with no token at all must read the same way as a stale one."""
        client = csrf_app.test_client()
        response = client.post("/api/operations/run", json={"menu_number": "1"})
        assert response.mimetype == "application/json"
        assert response.get_json()["code"] == "csrf_expired"

    def test_detail_keeps_the_library_wording(self, csrf_app):
        """A support report needs the original description beside the plain sentence."""
        client = csrf_app.test_client()
        response = client.post("/api/operations/run", json={}, headers={"X-CSRFToken": "stale"})
        assert response.get_json()["detail"]  # The library description must survive.


class TestBrowserFormKeepsItsPage:
    """A form post is not an API call, so it keeps the page it already expects."""

    def test_form_route_still_answers_html(self, csrf_app):
        """A non-API route with an HTML Accept header must keep the error page."""
        client = csrf_app.test_client()
        response = client.post("/settings", data={"a": "b"}, headers={"Accept": "text/html"})
        assert response.status_code == 400
        assert response.mimetype == "text/html"

    def test_json_accept_header_wins_outside_the_api_path(self, csrf_app):
        """A caller that asks for JSON must receive JSON, whatever the route path."""
        client = csrf_app.test_client()
        response = client.post("/settings", data={"a": "b"}, headers={"Accept": "application/json"})
        assert response.mimetype == "application/json"
        assert response.get_json()["code"] == "csrf_expired"


class TestValidTokenStillWorks:
    """The repair must not weaken the protection it reports on."""

    def test_csrf_protection_still_rejects(self, csrf_app):
        """A protected route must still refuse a request that carries no valid token."""
        client = csrf_app.test_client()
        assert client.post("/api/operations/run", json={}).status_code == 400

    def test_handler_is_registered_for_the_csrf_error(self, csrf_app):
        """The application must own a handler, so the default page never returns."""
        from flask_wtf.csrf import CSRFError

        assert any(CSRFError in mapping for mapping in csrf_app.error_handler_spec[None].values())
