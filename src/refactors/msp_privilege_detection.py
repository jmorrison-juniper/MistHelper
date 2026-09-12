"""detect_msp_privileges extracted from MistHelper (initiative 1015 T-05 + cleanup).

Owns the module-level ``detect_msp_privileges()`` function originally
defined at MistHelper.py:2232, and the six private helpers that made up
its call chain (``_msp_fetch_user_data``, ``_msp_extract_from_user_data``,
``_msp_parse_one_privilege``, ``_msp_resolve_name``, ``_fetch_msp_name``,
``_extract_msp_name``). The entire chain now lives here so this module
is fully self-contained: no ``import MistHelper``, no ``mh.*`` reach-back,
no dependency on any MistHelper module-global.

``detect_msp_privileges(session)`` now takes ``session`` as a REQUIRED
positional parameter, threads it through the private helper chain, and
RETURNS the detected MSP grant list. It does NOT write to any global.
Callers that want to publish the result to MistHelper's ``msp_privileges``
module-global do so explicitly at the callsite:
``MistHelper.msp_privileges = detect_msp_privileges(apisession)``.

Callsites rewritten in this PR:
- MistHelper.py two internal calls (``_attempt_interactive_login_with_rollback``
  and ``_establish_mist_session``) explicitly assign the return value to the
  module-global cache.
- ``src/refactors/initialize_mist_session_interactive.py`` already passed the
  session and returned the list to the LoginOrchestrator, which stashes it
  into the state bag. No change required beyond signature (session now
  required, no default).
- ``src/export/msp_inventory_exporter.py`` explicitly assigns the return
  value to ``MistHelper.msp_privileges`` after detection.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing on 3.10+

import logging  # Structured action logging per Constitution VII
from typing import Any  # session + priv-grant values are dynamically typed at the mistapi seam


def _extract_msp_name(response: Any) -> str | None:
    """Return the 'name' string from an MSP details response, or None when absent/malformed."""
    logging.debug("_extract_msp_name: entry")  # BEFORE: trace helper entry
    data = getattr(response, "data", None)  # Unwrap the response payload if present
    if not isinstance(data, dict):  # Need a dict payload to read the name field
        logging.debug("_extract_msp_name: response.data is not a dict, returning None")  # AFTER: no-data trace
        return None  # Malformed or empty response
    name = data.get("name")  # Extract the MSP's name field
    result = name if isinstance(name, str) else None  # Return the name only if it is a valid string
    logging.debug("_extract_msp_name: exit -- name=%s", "<set>" if result else "None")  # AFTER: success trace
    return result  # Yield the resolved name (or None when absent)


def _fetch_msp_name(msp_id: str, session: Any) -> str | None:
    """Fetch MSP name from the MSP details API when not carried inside the privilege grant."""
    logging.info("_fetch_msp_name: entry (msp_id=%s...)", msp_id[:8])  # BEFORE: trace fetch entry
    if session is None:  # No active session to query with
        logging.debug("_fetch_msp_name: no session, returning None")  # AFTER: no-session trace
        return None  # Cannot look anything up
    try:  # API call and payload parsing may fail. Degrade to None on any error
        import mistapi.api.v1.msps.msps as msps_api  # Lazy import of MSP details endpoint

        response = msps_api.getMspDetails(session, msp_id)  # Fetch the MSP record by ID via the shared session
        result = _extract_msp_name(response)  # Pull the name from the payload (None when absent/malformed)
        logging.debug("_fetch_msp_name: exit -- result=%s", "<set>" if result else "None")  # AFTER: success trace
        return result  # Hand back the resolved name (or None)
    except Exception as e:  # Lookup failed (network, permissions, and so on)
        logging.debug("Could not fetch MSP name for %s...: %s", msp_id[:8], e)  # Note the failure at debug level
        return None  # Default to None when the name cannot be resolved


def _msp_resolve_name(msp_id: str, priv: dict[str, Any], session: Any) -> str:
    """Resolve a human-readable MSP name from a grant, falling back to the MSP API or a short id label."""
    logging.debug("_msp_resolve_name: entry (msp_id=%s...)", msp_id[:8])  # BEFORE: trace resolve entry
    msp_name = priv.get("msp_name") or priv.get("name")  # The API uses different keys across versions.
    if not msp_name or msp_name == "Unknown":  # Name absent or placeholder.
        resolved = _fetch_msp_name(msp_id, session) or f"MSP-{msp_id[:8]}"  # Look it up, else derive short label.
        logging.debug("_msp_resolve_name: fell back to fetch or short label -- %s", resolved)  # AFTER: fallback trace
        return resolved  # Return the fallback name
    logging.debug("_msp_resolve_name: exit -- using grant-provided name")  # AFTER: happy-path trace
    return str(msp_name)  # The grant already carried a usable name (str-coerced for return typing)


def _msp_parse_one_privilege(priv: Any, session: Any) -> dict[str, Any] | None:
    """Parse one privilege grant into a normalized MSP record, or None when it is not a valid MSP grant."""
    logging.debug("_msp_parse_one_privilege: entry")  # BEFORE: trace parse entry
    if not (isinstance(priv, dict) and priv.get("msp_id")):  # Only MSP-scoped dict grants qualify.
        logging.debug("_msp_parse_one_privilege: not an MSP grant, returning None")  # AFTER: non-msp trace
        return None  # Not an MSP grant. Skip it.
    logging.debug(
        "MSP privilege found: scope=%s, role=%s", priv.get("scope"), priv.get("role")
    )  # Log the grant details.
    msp_id = priv.get("msp_id")  # Extract the MSP identifier.
    if not msp_id or not isinstance(msp_id, str):  # Guard against missing/invalid IDs.
        logging.debug("_msp_parse_one_privilege: msp_id missing or non-str, returning None")  # AFTER: bad-id trace
        return None  # Skip malformed grants.
    msp_name = _msp_resolve_name(msp_id, priv, session)  # Resolve the human-readable MSP name (using session).
    msp_info: dict[str, Any] = {  # Build a normalized record for this MSP grant.
        "msp_id": msp_id,  # The MSP's unique identifier.
        "msp_name": msp_name,  # Human-readable MSP name.
        "role": priv.get("role", "unknown"),  # The user's role within this MSP.
        "scope": priv.get("scope", "unknown"),  # The scope of the grant.
    }
    logging.info(
        "Detected MSP privilege: %s (ID: %s..., role: %s, scope: %s)",
        msp_info["msp_name"],
        msp_info["msp_id"][:8],
        msp_info["role"],
        msp_info["scope"],
    )  # Report the detected grant.
    logging.debug("_msp_parse_one_privilege: exit -- built normalized MSP record")  # AFTER: success trace
    return msp_info  # Hand back the normalized MSP record.


def _msp_extract_from_user_data(user_data: dict[str, Any], session: Any) -> list[dict[str, Any]]:
    """Extract all MSP-scoped privilege records from a getSelf user-data payload."""
    logging.debug("_msp_extract_from_user_data: entry")  # BEFORE: trace extract entry
    privileges = user_data.get("privileges", [])  # Pull the list of privilege grants.
    logging.debug("MSP detection: parsing %s privilege entries", len(privileges))  # Log how many grants we'll scan.
    detected_msps: list[dict[str, Any]] = []  # Accumulate any MSP-scoped privileges we find.
    for priv in privileges:  # Examine each privilege grant.
        msp_info = _msp_parse_one_privilege(priv, session)  # Normalize this grant (None when not an MSP grant).
        if msp_info is not None:  # The grant was a valid MSP grant.
            detected_msps.append(msp_info)  # Record it.
    logging.debug("_msp_extract_from_user_data: exit -- found %d MSP grant(s)", len(detected_msps))  # AFTER trace
    return detected_msps  # Return every MSP grant found in the payload.


def _msp_fetch_user_data(session: Any) -> dict[str, Any] | None:
    """Call getSelf and return the validated user-data dict, or None when unavailable or malformed."""
    logging.info("_msp_fetch_user_data: entry")  # BEFORE: trace API call
    import mistapi.api.v1.self.self as self_api  # Lazy import of the "self" endpoint module

    response = self_api.getSelf(session)  # Ask the API who the authenticated user is (via injected session).
    if not response or not hasattr(response, "data"):  # No usable payload came back.
        logging.warning("getSelf returned no data - cannot detect MSP privileges")  # Warn we cannot determine access.
        return None  # No privileges could be detected.
    user_data = response.data  # Extract the decoded JSON body.
    if not isinstance(user_data, dict):  # The body should be a JSON object.
        logging.warning("getSelf returned unexpected type: %s", type(user_data))  # Warn about the malformed shape.
        return None  # Cannot parse privileges from this.
    logging.debug("_msp_fetch_user_data: exit -- returning validated user_data dict")  # AFTER: success trace
    return user_data  # Hand back the validated user-data payload.


def detect_msp_privileges(session: Any) -> list[dict[str, Any]]:
    """Detect MSP-level privileges from the authenticated user's profile via GET /api/v1/self.

    ``session`` is REQUIRED (an authenticated mistapi session). Returns the list of MSP
    privilege dicts (msp_id, msp_name, role, scope), or [] when there is no MSP access or
    detection fails. This function does NOT touch any module-global. The caller is
    responsible for publishing the result to ``MistHelper.msp_privileges`` if desired.
    """
    logging.info(
        "detect_msp_privileges: entry (session=%s)", "provided" if session is not None else "None"
    )  # BEFORE: log entry for observability

    if not session:  # No usable session was supplied.
        logging.warning("Cannot detect MSP privileges - no active session")  # Warn that detection cannot proceed.
        return []  # Treat as no MSP access.

    try:  # API or parsing failures must degrade to "no MSP access" rather than crash the session.
        user_data = _msp_fetch_user_data(session)  # Call getSelf and validate the payload (None when unavailable).
        if user_data is None:  # getSelf failed or returned a malformed payload.
            logging.debug(
                "detect_msp_privileges: _msp_fetch_user_data returned None; returning empty list"
            )  # AFTER: trace no-user-data path
            return []  # No privileges could be detected.
        detected_msps = _msp_extract_from_user_data(user_data, session)  # Parse the payload for MSP grants.
        if detected_msps:  # At least one MSP grant was found.
            logging.info("User has MSP-level access to %s MSP(s)", len(detected_msps))  # Report the count.
        else:  # No MSP grants present in the payload.
            logging.debug("No MSP privileges detected for current user")  # Note the absence at debug level.
        logging.debug(
            "detect_msp_privileges: exit -- returning %d MSP grant(s)", len(detected_msps)
        )  # AFTER: trace success path with count
        return detected_msps  # Hand the parsed MSP list back to the caller.
    except Exception as e:  # Any API or parsing failure.
        logging.warning("Failed to detect MSP privileges: %s", e)  # Warn but do not crash the session.
        return []  # Treat as no MSP access on error.
