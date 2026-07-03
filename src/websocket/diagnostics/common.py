"""Shared helpers for WebSocket diagnostic command executors (ping, ARP)."""

from __future__ import annotations  # Defer annotation evaluation for forward refs

import logging  # Standard logging used by every helper for action observability
import sys  # Inspected to detect --debug / -d flags on the CLI
from typing import Any  # Generic typing for loose JSON-like payloads

import requests  # HTTP client for the device-command POST endpoints

from src.websocket.manager import (  # Shared WebSocket helpers reused across executors
    WebSocketManager,
    check_mist_credentials,
    get_mist_credentials,
)


def detect_debug_mode() -> bool:
    """Return True when the user passed --debug or -d on the CLI."""
    logging.debug("Inspecting sys.argv for WebSocket diagnostic debug flag")  # Action log before scan
    debug_flag_present = "--debug" in sys.argv or "-d" in sys.argv  # Match either accepted flag spelling
    logging.debug("Debug mode flag detected: %s", debug_flag_present)  # Action log after scan
    return debug_flag_present  # Tell caller whether to enable verbose printing


def post_device_command(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    debug_mode: bool,
    command_label: str,
) -> requests.Response | None:
    """POST a device-command to the Mist REST API and return the raw Response."""
    if debug_mode:  # Surface request metadata for the operator before sending
        print(f"[DEBUG] POST URL = {url}")  # Print target URL exactly as the legacy code did
        print(  # Print headers but never the real token value (security)
            "[DEBUG] Headers = {'Authorization': 'Token [REDACTED]', " "'Content-Type': 'application/json'}"
        )
    logging.info("Issuing %s POST to %s", command_label, url)  # Action log before HTTP call
    response = requests.post(url, headers=headers, json=payload, timeout=30)  # Fire HTTP request
    logging.debug(  # Action log after HTTP call with status only (body may contain sensitive data)
        "%s POST completed with status=%s", command_label, response.status_code
    )
    if debug_mode:  # Mirror legacy debug prints of full response
        print(f"[DEBUG] HTTP Response Status = {response.status_code}")  # Show numeric status
        print(f"[DEBUG] HTTP Response Body = {response.text}")  # Show raw body for diagnosis
    return response  # Caller inspects status/body and decides next step


def extract_command_session(
    response: requests.Response,
    websocket_manager: WebSocketManager,
    command_label: str,
) -> str | None:
    """Return the session id from a command response or disconnect+None on failure."""
    if response.status_code != 200:  # Any non-200 is a hard failure for the command
        print(f"! Failed to issue {command_label} command: {response.status_code}")  # User-facing error
        print(f"! Response: {response.text}")  # Show body for operator triage
        websocket_manager.disconnect()  # Free the WS since we will not consume results
        logging.warning(  # Action log after failure path
            "%s command failed; status=%s", command_label, response.status_code
        )
        return None  # Signal caller to abort
    response_payload = response.json()  # Parse JSON body returned by the API
    session_id = response_payload.get("session")  # Pull the session identifier used for demux
    if not session_id:  # API contract requires a session id for result correlation
        print(f"! No session ID returned from {command_label} command")  # User-facing error
        websocket_manager.disconnect()  # Free the WS since we cannot demux results
        logging.warning("%s command returned no session id", command_label)  # Action log
        return None  # Signal caller to abort
    logging.debug(  # Action log after success path
        "%s command session established (len=%d)", command_label, len(session_id)
    )
    return session_id  # Caller awaits results on this session id


def prepare_command_credentials(
    deps_apisession: Any,
    websocket_manager: WebSocketManager,
    debug_mode: bool,
) -> tuple[str, str] | None:
    """Pull Mist host/token, validate, or disconnect+None on missing credentials."""
    logging.debug("Fetching Mist host+token for diagnostic command")  # Action log before lookup
    mist_host, mist_apitoken = get_mist_credentials(deps_apisession)  # Pull cloud + API token
    logging.debug("Validating Mist credentials for diagnostic command")  # Action log before check
    if not check_mist_credentials(  # check_mist_credentials prints its own error + disconnects on fail
        websocket_manager, mist_host, mist_apitoken, debug_mode
    ):
        logging.warning("Mist credential validation failed for diagnostic command")  # After log
        return None  # Caller aborts the diagnostic
    logging.debug("Mist credentials accepted for diagnostic command")  # Action log after success
    return mist_host, mist_apitoken  # Caller uses these to build the POST URL+headers


def print_extra_result_fields(
    result_payload: dict[str, Any],
    excluded_keys: set[str],
) -> None:
    """Print any result keys outside the well-known ones (raw, Output, session)."""
    extra_keys = [key for key in result_payload if key not in excluded_keys]  # Anything novel
    if not extra_keys:  # Nothing to show; keep output clean
        return  # Early return preserves prior visual layout
    print(f"\nOTHER AVAILABLE FIELDS: {extra_keys}")  # Header matches legacy phrasing
    _print_extra_field_values(result_payload, extra_keys)  # Extracted so CC stays <=5


def _print_extra_field_values(
    result_payload: dict[str, Any],
    extra_keys: list[str],
) -> None:
    """Print each non-empty extra key's value on its own line."""
    # WHY: pulling the for/if pair out of print_extra_result_fields drops its CC from 6 to 4.
    for field_name in extra_keys:  # Walk each unexpected key for visibility
        field_value = result_payload.get(field_name)  # Look up the actual value
        if field_value:  # Skip empty/falsey values per legacy behavior
            print(f"{field_name}: {field_value}")  # Show the value verbatim
