"""Build a scrubbed child environment for one E2E portal server.

Why:
    A child process inherits the parent environment by default. The E2E child
    must remove every production credential and persistent output path.
"""

from __future__ import annotations  # Keep annotations independent from import order.

import logging  # Record the scrub action without a credential value.
from collections.abc import Mapping  # Accept a copied environment or the process environment.

logger = logging.getLogger(__name__)  # Keep scrub records tied to this module.

ARANGO_SENTINEL = "http://127.0.0.1:1"  # Use an explicit unreachable loopback document store address.
REDIS_SENTINEL = "127.0.0.1"  # Use an explicit unreachable loopback lock store address.
REDIS_PORT_SENTINEL = "1"  # Use the reserved unreachable port from the isolation contract.

SCRUBBED_VARIABLES = (  # Remove credentials and persistent output paths before the child starts.
    "ARANGO_DATABASE",
    "ARANGO_USERNAME",
    "ARANGO_ROOT_PASSWORD",
    "REDIS_PASSWORD",
    "MIST_APITOKEN",
    "MIST_API_TOKEN",
    "API_TOKEN",
    "OUTPUT_FORMAT",
    "DATABASE_PATH",
    "PORTAL_BACKUP_PATH",
    "PORTAL_EXPORT_PATH",
    "UPGRADE_PORTAL_BACKUP_PATH",
    "UPGRADE_PORTAL_EXPORT_PATH",
    "CAPTURE_BACKUP_PATH",
    "CAPTURE_EXPORT_PATH",
)

SCRUBBED_PREFIXES = ("MIST_", "ARANGO_", "REDIS_")  # Remove provider settings before adding safe sentinels.
SCRUBBED_SUFFIXES = (  # Remove common credential and persistent path settings from any provider.
    "_API_TOKEN",
    "_DATABASE_URL",
    "_OUTPUT_PATH",
    "_BACKUP_PATH",
    "_EXPORT_PATH",
)


def build_child_environment(parent: Mapping[str, str]) -> dict[str, str]:  # Scrub one child environment.
    """Return one credential-free child environment with connector sentinels."""
    logger.info("Build the isolated E2E child environment")  # Record the scrub before it starts.
    child = dict(parent)  # Preserve interpreter and module path settings for the child.
    for variable in tuple(child):  # Inspect a stable key list while values leave the child map.
        prefixed = variable.startswith(SCRUBBED_PREFIXES)  # Detect every provider-specific setting.
        suffixed = variable.endswith(SCRUBBED_SUFFIXES)  # Detect common credential and path settings.
        if variable in SCRUBBED_VARIABLES or prefixed or suffixed:  # Remove every unsafe inherited value.
            child.pop(variable, None)  # An absent value needs no special branch.
    child["ARANGO_HOST"] = ARANGO_SENTINEL  # Force an unreachable loopback document store address.
    child["REDIS_HOST"] = REDIS_SENTINEL  # Force an unreachable loopback lock store address.
    child["REDIS_PORT"] = REDIS_PORT_SENTINEL  # Force the unreachable lock store port.
    logger.debug("Built the isolated E2E child environment with %s variables", len(child))  # Report a safe count.
    return child  # The caller adds only test-owned server settings.
