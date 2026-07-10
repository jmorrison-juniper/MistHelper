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
attributes are resolved via a call-time ``import MistHelper as mh``
inside the function body so the extracted module stays free of a
top-level MistHelper import (which would create a circular
src<->MistHelper load, since MistHelper imports this function at
module load) and continues to honour monkeypatched attributes in
tests. The call-time import is also cheap because ``import`` after the
module is loaded is a plain ``sys.modules`` lookup.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing on 3.10+

import logging  # Structured action logging per Constitution VII
from typing import Any  # apisession + priv-grant values are dynamically typed at the mistapi seam


def detect_msp_privileges(session: Any = None) -> list[dict[str, Any]]:
    """Detect MSP-level privileges from the authenticated user's profile via GET /api/v1/self.

    An explicit ``session`` (passed by the interactive login before the module-global
    ``apisession`` is published) is promoted to the global. Returns MSP privilege dicts
    (msp_id, msp_name, role, scope), or [] when there is no MSP access or detection fails.
    """
    # BEFORE: log entry with session presence for observability
    logging.info("detect_msp_privileges: entry (session=%s)", "provided" if session is not None else "None")
    # Call-time import breaks the circular src<->MistHelper load; mypy treats MistHelper
    # as Any via [tool.mypy.overrides] follow_imports="skip", so mh's attributes are Any
    # and no attr-defined error is raised on mh.apisession / mh._msp_* helpers.
    import MistHelper as mh  # noqa: PLC0415  # Deliberate call-time import to avoid circular load

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
        # Explicitly-typed variable coerces the Any return of the follow_imports=skip'd helper
        # into the concrete list[dict[str, Any]] we contract to return -- satisfies warn_return_any.
        detected_msps: list[dict[str, Any]] = mh._msp_extract_from_user_data(user_data)
        mh._msp_cache_and_report(detected_msps)  # Cache to the MistHelper module global and log the outcome.
        # AFTER: trace success path with count
        logging.debug("detect_msp_privileges: exit -- returning %d MSP grant(s)", len(detected_msps))
        return detected_msps  # Hand the parsed MSP list back to the caller.
    except Exception as e:  # Any API or parsing failure.
        logging.warning("Failed to detect MSP privileges: %s", e)  # Warn but don't crash the session.
        return []  # Treat as no MSP access on error.
