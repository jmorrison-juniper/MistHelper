"""Settings routes for the MistHelper web portal.

Provides theme listing and exact menu parameter API endpoints.
"""

from __future__ import annotations  # Keep modern annotations import-safe.

import logging  # Record each external read and route result.
from typing import Any  # Type the Mist session and JSON-shaped rows.

import mistapi  # Use the supported Mist SDK for every cloud request.
from flask import Blueprint, current_app, jsonify

logger = logging.getLogger(__name__)  # Keep settings route records tied to this module.
settings_bp = Blueprint("settings", __name__)


class OrgWebhookChoiceProvider:
    """Read organization webhooks and build stable portal choices."""

    class Error(RuntimeError):
        """Report a webhook read that cannot produce safe options."""

    def __init__(self, mist_session: Any | None, org_id: str | None) -> None:
        """Store the runtime values required for one organization webhook read."""
        self._mist_session = mist_session  # Keep the active authenticated session private.
        self._org_id = org_id.strip() if isinstance(org_id, str) else ""  # Normalize the organization identifier.

    def get_options(self) -> list[dict[str, str]]:
        """Return stable webhook options in the order that Mist supplies them."""
        if self._mist_session is None:  # Stop before the SDK call when the session is missing.
            logger.error("The portal cannot list webhooks because the Mist session is missing")
            raise self.Error("The Mist session is not available.")
        if not self._org_id:  # Stop before the SDK call when the organization is missing.
            logger.error("The portal cannot list webhooks because the organization identifier is missing")
            raise self.Error("The organization identifier is not available.")
        logger.info("Listing organization webhooks for portal org_id=%s", self._org_id)  # Log before the read.
        options = self._build_options(self._read_webhooks())  # Read all pages and keep stable rows.
        logger.debug("Listed %d portal webhook choices for org_id=%s", len(options), self._org_id)
        return options  # Return a new list, so a failed request cannot reuse stale options.

    def _read_webhooks(self) -> list[dict[str, Any]]:
        """Read every webhook page or raise one explicit provider failure."""
        try:
            response = mistapi.api.v1.orgs.webhooks.listOrgWebhooks(self._mist_session, self._org_id)
            status_code = getattr(response, "status_code", 200)  # Read the initial HTTP result when exposed.
            if isinstance(status_code, int) and status_code >= 400:  # Reject HTTP failures before pagination.
                logger.error("Mist returned HTTP %s while listing webhooks for org_id=%s", status_code, self._org_id)
                raise self.Error(f"Mist returned HTTP {status_code} while listing webhooks.")
            webhooks = mistapi.get_all(response=response, mist_session=self._mist_session)  # Collect every page.
            return list(webhooks)  # Detach the result from the SDK container.
        except self.Error:
            raise  # Preserve the explicit HTTP failure text for the route.
        except Exception as exception:
            logger.exception("Mist could not list organization webhooks for org_id=%s", self._org_id)
            raise self.Error("Mist could not list organization webhooks.") from exception

    @staticmethod
    def _build_options(webhooks: list[dict[str, Any]]) -> list[dict[str, str]]:
        """Build stable choice values without sorting or inventing identifiers."""
        options: list[dict[str, str]] = []  # Preserve source order in one new response list.
        for webhook in webhooks:  # Inspect each Mist row once.
            webhook_id = str(webhook.get("id") or "").strip()  # Normalize the stable selection value.
            if not webhook_id:  # A missing identifier cannot produce a safe browser choice.
                continue  # Skip the unusable row without changing later row order.
            webhook_name = str(webhook.get("name") or "").strip()  # Normalize optional display text.
            options.append({"value": webhook_id, "label": webhook_name or webhook_id})  # Use the id as fallback.
        return options  # Return only stable choices.


class OrgWebhookParametersRoute:
    """Build the existing parameter envelope for menu 256."""

    @staticmethod
    def get() -> tuple[Any, int] | Any:
        """Return one required stable webhook choice or an explicit failure."""
        provider = OrgWebhookChoiceProvider(  # Read dependencies from the registered portal application.
            current_app.config.get("APISESSION"),
            current_app.config.get("ORG_ID"),
        )
        try:
            options = provider.get_options()  # Read current choices before building any response.
        except OrgWebhookChoiceProvider.Error as error:
            logger.error("Menu 256 webhook choices are unavailable: %s", error)  # Record the safe failure reason.
            return jsonify({"error": str(error)}), 503  # Return no stale or fabricated parameter data.
        description = OrgWebhookParametersRoute._description()  # Reuse the existing menu title.
        if description is None:  # A missing menu row is a local configuration failure.
            logger.error("Menu 256 is missing from the portal menu actions")
            return jsonify({"error": "Menu 256 is not available."}), 503
        payload = {  # Match the envelope that the existing JavaScript already reads.
            "menu_number": "256",
            "description": description,
            "category": "interactive",
            "parameters": [OrgWebhookParametersRoute._parameter(options)],
        }
        logger.debug("Menu 256 parameter route returned %d webhook choices", len(options))  # Log after the action.
        return jsonify(payload)  # Return HTTP 200 for populated and empty successful lists.

    @staticmethod
    def _description() -> str | None:
        """Return the current menu 256 title from the injected menu actions."""
        menu_actions: dict[str, Any] = current_app.config.get("MENU_ACTIONS", {})  # Read the shared catalog.
        menu_entry = menu_actions.get("256")  # Select the assigned menu row.
        description = getattr(menu_entry, "title", None)  # Use the named MenuEntry field.
        return description if isinstance(description, str) and description else None  # Reject invalid local data.

    @staticmethod
    def _parameter(options: list[dict[str, str]]) -> dict[str, Any]:
        """Return the established required choice parameter shape."""
        return {  # Keep each field compatible with the existing JavaScript renderer.
            "name": "webhook_id",
            "label": "Webhook",
            "param_type": "choice",
            "required": True,
            "options": options,
        }


@settings_bp.route("/api/themes")
def list_themes() -> Any:
    """Return available themes with default indicator."""
    theme_manager = current_app.config.get("THEME_MANAGER")
    if theme_manager is None:
        return jsonify({"themes": [], "current_default": "dark"})
    themes = theme_manager.get_themes()
    default_name = theme_manager.get_default_name()
    return jsonify(
        {
            "themes": themes,
            "current_default": default_name,
        }
    )


settings_bp.add_url_rule(  # Register the exact static path on an always-loaded blueprint.
    "/api/operations/parameters/256",
    endpoint="menu_256_parameters",
    view_func=OrgWebhookParametersRoute.get,
    methods=["GET"],
)
