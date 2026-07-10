"""detect_msp_privileges extracted from MistHelper (initiative 1015 T-05).

Owns the module-level ``detect_msp_privileges()`` function originally
defined at MistHelper.py:2232, and re-lands it as a plain top-level
function in this fresh cross-package module (Cat E). All callsites --
two internal MistHelper.py calls, one bypass in
``src/refactors/initialize_mist_session_interactive.py``, and one
bypass in ``src/export/msp_inventory_exporter.py`` -- are rewritten in
the same PR to import from this module. No wrapper shim, no re-export
alias, no ``mh.detect_msp_privileges`` proxy remains after this
extraction.

MistHelper.py still owns the ``apisession`` and ``msp_privileges``
module globals plus the three private helpers
(``_msp_fetch_user_data``, ``_msp_extract_from_user_data``,
``_msp_cache_and_report``) that this detector delegates to. Those
attributes are resolved lazily via ``importlib.import_module("MistHelper")``
inside the function body so the extracted module stays free of a
top-level MistHelper import (avoids a circular src<->MistHelper load)
and honours monkeypatched attributes in tests.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing on 3.10+

import importlib  # Late-import MistHelper module to reach live globals + helper functions
import logging  # Structured action logging per Constitution VII


def detect_msp_privileges(session=None):  # type: ignore[no-untyped-def]
    """Detect MSP-level privileges from the authenticated user's profile via GET /api/v1/self.

    An explicit ``session`` (passed by the interactive login before the module-global
    ``apisession`` is published) is promoted to the global. Returns MSP privilege dicts
    (msp_id, msp_name, role, scope), or [] when there is no MSP access or detection fails.
    """
    # BEFORE: log entry with session presence for observability
    logging.info("detect_msp_privileges: entry (session=%s)", "provided" if session is not None else "None")
    # WHY: MSP detection reads/writes MistHelper globals + delegates to three private helpers
    mh = importlib.import_module("MistHelper")
    if session is not None:  # Caller supplied an explicit session (interactive login, before publish).
        # Promote it to the MistHelper module global so helpers use the same session.
        mh.apisession = session

    if not mh.apisession:  # Still no usable session from either the argument or the module global.
        logging.warning("Cannot detect MSP privileges - no active session")  # Warn that detection cannot proceed.
        return []  # Treat as no MSP access.

    try:  # API or parsing failures must degrade to "no MSP access" rather than crash the session.
        user_data = mh._msp_fetch_user_data()  # Call getSelf and validate the payload (None when unavailable).
        if user_data is None:  # getSelf failed or returned a malformed payload.
            # AFTER: trace no-user-data path
            logging.debug("detect_msp_privileges: _msp_fetch_user_data returned None; returning empty list")
            return []  # No privileges could be detected.
        detected_msps = mh._msp_extract_from_user_data(user_data)  # Parse every MSP-scoped grant.
        mh._msp_cache_and_report(detected_msps)  # Cache to the MistHelper module global and log the outcome.
        # AFTER: trace success path with count
        logging.debug("detect_msp_privileges: exit -- returning %d MSP grant(s)", len(detected_msps))
        return detected_msps  # Hand the parsed MSP list back to the caller.
    except Exception as e:  # Any API or parsing failure.
        logging.warning("Failed to detect MSP privileges: %s", e)  # Warn but don't crash the session.
        return []  # Treat as no MSP access on error.
