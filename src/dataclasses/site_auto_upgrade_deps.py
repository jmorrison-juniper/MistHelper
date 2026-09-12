"""Frozen dataclass that bundles the dependency-injection params shared across the site auto-upgrade workflow.

The original functions in ``src/firmware/site_auto_upgrade.py`` each took 6-9 positional
parameters which exceeded the 5-Item Rule's max-5 limit. This dataclass packages the
5 shared dependencies that every site-auto-upgrade entry point needs into one immutable
container, leaving room for per-function specifics within the budget.

Issue: https://github.com/jmorrison-juniper/issues/433 (Phase B)
"""

from __future__ import annotations  # Enable PEP 604 union syntax on Python 3.13.

from dataclasses import dataclass  # Standard-library dataclass decorator.
from typing import Any  # Type alias for the runtime-injected callables and apisession.


@dataclass(frozen=True, slots=True)
class SiteAutoUpgradeCoreDeps:
    """Five core dependencies every site-auto-upgrade function needs.

    Splitting the bundle from the MSP-only extras keeps both this class and
    ``SiteAutoUpgradeMspDeps`` at <=5 fields each (the 5-Item Rule).
    """

    apisession: Any  # Authenticated mistapi session used for every API call.
    safe_input_fn: Any  # Callable that wraps input() with EOF + interrupt handling.
    fetch_sites_fn: Any  # Callable returning the list of sites for a given org id.
    check_stop_fn: Any  # Predicate that returns True when the user requested a stop signal.
    dry_run: bool  # When True, skip the API mutations and only print the planned changes.


@dataclass(frozen=True, slots=True)
class SiteAutoUpgradeMspDeps:
    """Two MSP-mode-only dependencies for the multi-org auto-upgrade workflow."""

    select_msps_fn: Any  # Callable that prompts for + returns the list of MSPs to operate on.
    select_orgs_fn: Any  # Callable that prompts for + returns the list of orgs under an MSP.
