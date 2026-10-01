"""Action catalog and Mist SDK dispatch for client session control."""

from __future__ import annotations  # WHY: defer annotation evaluation for imported SDK callables.

import logging  # WHY: action logging is required around every Mist SDK call.
from collections.abc import Callable  # WHY: type the small SDK dispatch table.
from dataclasses import dataclass  # WHY: keep action metadata immutable and explicit.
from typing import Any  # WHY: mistapi sessions and responses are SDK owned objects.

import mistapi.api.v1.sites.clients  # WHY: site wireless client control SDK functions live here.
import mistapi.api.v1.sites.rogues  # WHY: rogue BSSID deauth SDK function lives here.
import mistapi.api.v1.sites.wired_clients  # WHY: wired client CoA SDK function lives here.

logger = logging.getLogger(__name__)  # WHY: module logger lets operators filter client control API calls.
SdkCallable = Callable[[Any, str, str], Any]  # WHY: all selected site scoped SDK calls share this shape.


@dataclass(frozen=True)
class ActionDefinition:  # WHY: one immutable record describes each supported destructive action.
    """Describe one supported client session control action."""

    action_key: str  # WHY: stable key used by prompts, tests, and audit rows.
    label: str  # WHY: operator-facing action name.
    target_type: str  # WHY: tells the handler whether to prompt for client MAC or rogue BSSID.
    operation_id: str  # WHY: Mist OpenAPI operation identifier for previews and audits.
    sdk_module: str  # WHY: records the SDK module that owns the operation.
    sdk_function: str  # WHY: records the SDK function name that will be called.
    scope: str  # WHY: documents that this implementation uses site scoped endpoints.


_ACTIONS: tuple[ActionDefinition, ...] = (  # WHY: tuple preserves prompt order and prevents mutation.
    ActionDefinition(  # WHY: wireless 802.1X reauth is a supported action.
        "wireless_reauthenticate",  # WHY: action key follows the data model.
        "Wireless reauthenticate",  # WHY: concise text for helpdesk operators.
        "client_mac",  # WHY: endpoint requires a client MAC path parameter.
        "reauthSiteDot1xWirelessClient",  # WHY: verified OpenAPI and SDK operation.
        "mistapi.api.v1.sites.clients",  # WHY: SDK module that exports the function.
        "reauthSiteDot1xWirelessClient",  # WHY: SDK function to call.
        "site",  # WHY: the menu flow starts with site selection.
    ),
    ActionDefinition(  # WHY: wired 802.1X reauth is a supported action.
        "wired_reauthenticate",  # WHY: action key follows the data model.
        "Wired reauthenticate",  # WHY: concise text for helpdesk operators.
        "client_mac",  # WHY: endpoint requires a client MAC path parameter.
        "reauthSiteDot1xWiredClient",  # WHY: verified OpenAPI and SDK operation.
        "mistapi.api.v1.sites.wired_clients",  # WHY: SDK module that exports the function.
        "reauthSiteDot1xWiredClient",  # WHY: SDK function to call.
        "site",  # WHY: the menu flow starts with site selection.
    ),
    ActionDefinition(  # WHY: wireless disconnect is a supported action.
        "disconnect",  # WHY: action key follows the data model.
        "Disconnect wireless client",  # WHY: clear destructive action text.
        "client_mac",  # WHY: endpoint requires a client MAC path parameter.
        "disconnectSiteWirelessClient",  # WHY: verified OpenAPI and SDK operation.
        "mistapi.api.v1.sites.clients",  # WHY: SDK module that exports the function.
        "disconnectSiteWirelessClient",  # WHY: SDK function to call.
        "site",  # WHY: the menu flow starts with site selection.
    ),
    ActionDefinition(  # WHY: guest unauthorize is a supported action.
        "unauthorize_guest",  # WHY: action key follows the data model.
        "Unauthorize guest",  # WHY: concise text for guest portal support.
        "client_mac",  # WHY: endpoint requires a client MAC path parameter.
        "unauthorizeSiteWirelessClient",  # WHY: verified OpenAPI and SDK operation.
        "mistapi.api.v1.sites.clients",  # WHY: SDK module that exports the function.
        "unauthorizeSiteWirelessClient",  # WHY: SDK function to call.
        "site",  # WHY: the menu flow starts with site selection.
    ),
    ActionDefinition(  # WHY: rogue client deauth is a supported action.
        "deauth_rogue_clients",  # WHY: action key follows the data model.
        "Deauth rogue clients",  # WHY: concise text for rogue mitigation.
        "rogue_bssid",  # WHY: endpoint requires a rogue BSSID path parameter.
        "deauthSiteWirelessClientsConnectedToARogue",  # WHY: verified OpenAPI and SDK operation.
        "mistapi.api.v1.sites.rogues",  # WHY: SDK module that exports the function.
        "deauthSiteWirelessClientsConnectedToARogue",  # WHY: SDK function to call.
        "site",  # WHY: the menu flow starts with site selection.
    ),
)
ACTION_CATALOG: dict[str, ActionDefinition] = {action.action_key: action for action in _ACTIONS}  # WHY: lookup.


class MistSessionControlApiClient:  # WHY: class owns all Mist SDK calls for the feature.
    """Call the Mist SDK function for a selected client session control action."""

    _SDK_CALLS: dict[str, SdkCallable] = {  # WHY: map action keys to verified SDK functions.
        "wireless_reauthenticate": mistapi.api.v1.sites.clients.reauthSiteDot1xWirelessClient,  # WHY: wireless.
        "wired_reauthenticate": mistapi.api.v1.sites.wired_clients.reauthSiteDot1xWiredClient,  # WHY: wired.
        "disconnect": mistapi.api.v1.sites.clients.disconnectSiteWirelessClient,  # WHY: wireless disconnect.
        "unauthorize_guest": mistapi.api.v1.sites.clients.unauthorizeSiteWirelessClient,  # WHY: guest.
        "deauth_rogue_clients": mistapi.api.v1.sites.rogues.deauthSiteWirelessClientsConnectedToARogue,  # WHY.
    }

    def send(self, session: Any, site_id: str, action_key: str, target: str) -> Any:
        """Send one verified site scoped Mist SDK request."""
        logger.info("Sending client session control request for action %s", action_key)  # WHY: before API call.
        sdk_call = self._SDK_CALLS[action_key]  # WHY: fail fast if an unsupported action reaches dispatch.
        response = sdk_call(session, site_id, target)  # WHY: call the verified mistapi endpoint once.
        status_code = getattr(response, "status_code", "unknown")  # WHY: capture a safe result summary.
        logger.debug("Client session control SDK call returned status %s", status_code)  # WHY: after API call.
        return response  # WHY: handler decides success or failure from the SDK response.


def list_actions() -> tuple[ActionDefinition, ...]:
    """Return supported actions in prompt order."""
    logger.info("Listing client session control actions")  # WHY: before action catalog read.
    logger.debug("Listed %s client session control actions", len(_ACTIONS))  # WHY: after catalog read.
    return _ACTIONS  # WHY: expose an immutable prompt order to the handler.


def get_action(action_key: str) -> ActionDefinition:
    """Return an action definition by key or numeric menu index."""
    logger.info("Resolving client session control action")  # WHY: before validation.
    action = _resolve_action(action_key.strip())  # WHY: support exact keys and numeric prompt choices.
    logger.debug("Resolved client session control action %s", action.action_key)  # WHY: after validation.
    return action  # WHY: handler needs the full action definition.


def _resolve_action(value: str) -> ActionDefinition:
    """Resolve one action key or one based prompt index."""
    if value.isdigit():  # WHY: operators can choose from the numbered prompt.
        return _resolve_action_index(int(value))  # WHY: convert one based index to catalog entry.
    if value in ACTION_CATALOG:  # WHY: tests and advanced users can enter stable keys directly.
        return ACTION_CATALOG[value]  # WHY: direct key lookup is unambiguous.
    raise ValueError("Select one supported client session control action.")  # WHY: fail before target prompt.


def _resolve_action_index(index_value: int) -> ActionDefinition:
    """Resolve a one based action index from the operator prompt."""
    if 1 <= index_value <= len(_ACTIONS):  # WHY: numbered menu choices are one based for operators.
        return _ACTIONS[index_value - 1]  # WHY: tuple indexes are zero based.
    raise ValueError("Select one supported client session control action.")  # WHY: invalid index must stop safely.
