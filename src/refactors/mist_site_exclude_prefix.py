"""``MIST_SITE_EXCLUDE_PREFIX`` constant extracted from MistHelper (initiative 1015 T-15).

Owns the site-name-prefix filter originally defined at
``MistHelper.py`` lines 2138-2143 as a module-level assignment reading
the ``MIST_SITE_EXCLUDE_PREFIX`` environment variable. The prefix
shields sites whose name starts with the configured value from
destructive operations (for example Menu #149 WAN2 migration, Menu #166 WAN
probe configuration, Menu #167 WAN probe device overrides).

Landing per E-14 as a **bare module-level constant** -- no wrapper
class, no getter function. The value is captured once at import time
from ``os.getenv`` with an empty-string default (no defaults per the
original comment; missing env var means "no sites excluded").

``MistHelper.py`` re-exports the constant so historical
``MistHelper.MIST_SITE_EXCLUDE_PREFIX`` / ``mh.MIST_SITE_EXCLUDE_PREFIX``
callers keep working transparently -- the re-exported symbol is the
same string object, not a copy or delegator.
"""

from __future__ import annotations  # Enable PEP 604 unions in annotations on 3.10+.

import logging  # Structured action logging per Constitution VII (remediates missing_action_logging).
import os  # Env var lookup for MIST_SITE_EXCLUDE_PREFIX.

# Site Exclusion Configuration from .env (REQUIRED - no defaults).
# MIST_SITE_EXCLUDE_PREFIX: Site name prefix to exclude from destructive operations.
# Example: "VRE" to exclude Juniper internal VRE sites.
MIST_SITE_EXCLUDE_PREFIX: str = os.getenv(
    "MIST_SITE_EXCLUDE_PREFIX", ""
)  # Name prefix that shields sites from destructive ops (empty string = no filter).

logging.info(  # Envelope: record the resolved value at import time so operators can audit which prefix is active.
    "mist_site_exclude_prefix: resolved MIST_SITE_EXCLUDE_PREFIX=%r at import time",
    MIST_SITE_EXCLUDE_PREFIX,
)
