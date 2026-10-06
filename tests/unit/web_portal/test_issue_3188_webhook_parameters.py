"""Tests for the menu 256 organization webhook parameter route."""

from __future__ import annotations  # Keep modern annotations import-safe.

from types import SimpleNamespace  # Build small response and menu doubles.
from unittest.mock import patch  # Keep each Mist SDK boundary offline.

import pytest  # Provide fixtures and parameterized failure cases.
from flask import Flask, jsonify  # Build an isolated route test application.

from web_portal.routes.settings import settings_bp  # Test the assigned always-registered blueprint.

_PROVIDER_MODULE = "web_portal.routes.settings"  # Keep patch targets on the assigned module.
_TITLE = "Search organization webhook deliveries (searchOrgWebhooksDeliveries)"  # Match menu 256.


@pytest.fixture
def parameter_app() -> Flask:
    """Return a small Flask app with the exact route and a generic fallback."""
    app = Flask(__name__)  # Isolate route behavior from portal background services.
    app.config.update(  # Supply the same configuration keys as the real app factory.
        APISESSION=object(),  # Use a local marker instead of an authenticated Mist session.
        ORG_ID="org-1",  # Provide one stable organization context.
        MENU_ACTIONS={"256": SimpleNamespace(title=_TITLE)},  # Provide the existing menu title.
        TESTING=True,  # Raise unexpected Flask failures during the test.
    )

    @app.get("/api/operations/parameters/<menu_number>")
    def generic_parameters(menu_number: str):  # Type the fallback route input.
        """Return a marker that proves whether the static route won."""
        return jsonify({"route": "generic", "menu_number": menu_number})  # Expose fallback selection.

    app.register_blueprint(settings_bp)  # Add the always-registered blueprint with the exact route.
    return app  # Hand the configured app to each test.


def _response(status_code: int = 200) -> SimpleNamespace:
    """Return a local Mist response double with one HTTP status."""
    return SimpleNamespace(status_code=status_code)  # Keep the provider transport check explicit.


class TestMenu256WebhookParameters:
    """Verify the exact route and the existing choice parameter envelope."""

    def test_exact_route_returns_stable_webhook_choices(self, parameter_app: Flask) -> None:
        """Return identifiers, readable labels, source order, and no unusable row."""
        webhooks = [  # Cover duplicate labels, missing names, and a missing identifier.
            {"id": "wh-b", "name": "Shared name"},  # Keep the first Mist row first.
            {"id": "wh-a", "name": "Shared name"},  # Keep duplicate names distinct by identifier.
            {"id": "wh-c", "name": ""},  # Use the identifier when the display name is empty.
            {"name": "No identifier"},  # Exclude a row that cannot make a stable selection.
        ]
        with (
            patch(f"{_PROVIDER_MODULE}.mistapi.api.v1.orgs.webhooks.listOrgWebhooks", return_value=_response()),
            patch(f"{_PROVIDER_MODULE}.mistapi.get_all", return_value=webhooks),
        ):
            response = parameter_app.test_client().get("/api/operations/parameters/256")  # Request the exact path.
        assert response.status_code == 200  # A valid empty or populated list is a successful response.
        assert response.get_json() == {
            "menu_number": "256",
            "description": _TITLE,
            "category": "interactive",
            "parameters": [
                {
                    "name": "webhook_id",
                    "label": "Webhook",
                    "param_type": "choice",
                    "required": True,
                    "options": [
                        {"value": "wh-b", "label": "Shared name"},
                        {"value": "wh-a", "label": "Shared name"},
                        {"value": "wh-c", "label": "wh-c"},
                    ],
                }
            ],
        }  # Prove the complete existing choice envelope and static-route precedence.

    def test_empty_webhook_list_returns_one_empty_choice(self, parameter_app: Flask) -> None:
        """Keep the choice shape when an organization has no webhooks."""
        with (
            patch(f"{_PROVIDER_MODULE}.mistapi.api.v1.orgs.webhooks.listOrgWebhooks", return_value=_response()),
            patch(f"{_PROVIDER_MODULE}.mistapi.get_all", return_value=[]),
        ):
            response = parameter_app.test_client().get("/api/operations/parameters/256")  # Request the exact path.
        payload = response.get_json()  # Read the returned parameter envelope.
        assert response.status_code == 200  # An empty configured list is not a cloud failure.
        assert len(payload["parameters"]) == 1  # Keep one required control for the browser.
        assert payload["parameters"][0]["options"] == []  # Do not fabricate a selectable webhook.

    @pytest.mark.parametrize("status_code", [403, 503])  # Cover one client and one server HTTP failure.
    def test_http_failure_returns_no_choice_data(self, parameter_app: Flask, status_code: int) -> None:
        """Reject failed Mist responses before pagination can make them look empty."""
        with (
            patch(
                f"{_PROVIDER_MODULE}.mistapi.api.v1.orgs.webhooks.listOrgWebhooks",
                return_value=_response(status_code),
            ),
            patch(f"{_PROVIDER_MODULE}.mistapi.get_all") as get_all,
        ):
            response = parameter_app.test_client().get("/api/operations/parameters/256")  # Request the exact path.
        assert response.status_code == 503  # Convert cloud read failures into a clear unavailable response.
        assert response.get_json() == {"error": f"Mist returned HTTP {status_code} while listing webhooks."}
        get_all.assert_not_called()  # A failed initial response must not enter pagination.

    def test_sdk_failure_returns_no_stale_or_fabricated_choices(self, parameter_app: Flask) -> None:
        """Return an explicit failure when the SDK raises before any list exists."""
        with (
            patch(
                f"{_PROVIDER_MODULE}.mistapi.api.v1.orgs.webhooks.listOrgWebhooks",
                side_effect=RuntimeError("offline SDK failure"),
            ),
            patch(f"{_PROVIDER_MODULE}.mistapi.get_all") as get_all,
        ):
            response = parameter_app.test_client().get("/api/operations/parameters/256")  # Request the exact path.
        payload = response.get_json()  # Read the error body once.
        assert response.status_code == 503  # Keep SDK failures distinct from an empty successful list.
        assert payload == {"error": "Mist could not list organization webhooks."}  # Expose no partial choices.
        assert "parameters" not in payload  # Prevent stale or fabricated controls after a failed read.
        get_all.assert_not_called()  # An exception before a response cannot paginate.

    @pytest.mark.parametrize(("config_key", "config_value"), [("APISESSION", None), ("ORG_ID", "")])
    def test_missing_configuration_returns_no_choice(
        self,
        parameter_app: Flask,
        config_key: str,
        config_value: object,
    ) -> None:
        """Reject a missing session or organization before the Mist SDK call."""
        parameter_app.config[config_key] = config_value  # Remove one required provider input.
        with patch(f"{_PROVIDER_MODULE}.mistapi.api.v1.orgs.webhooks.listOrgWebhooks") as list_call:
            response = parameter_app.test_client().get("/api/operations/parameters/256")  # Request the exact path.
        assert response.status_code == 503  # A missing runtime dependency makes the route unavailable.
        assert "error" in response.get_json()  # Give the operator a clear failure body.
        list_call.assert_not_called()  # Invalid local configuration must stop before a Mist call.
