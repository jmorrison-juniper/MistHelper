"""Read the pre-check capture of each site of one multi-site operation.

Why:
    Issue #3243. The single-site confirm page stays locked until the site holds
    a verified pre-check capture, and the single-site start refuses a run with
    no capture. The multi-site mode had no such gate. One confirmation could
    then upgrade many sites with no baseline for a later comparison. This
    module holds the gate that the confirm page, the start route, and the
    progress page share. It makes no cloud call and no write.
"""

from __future__ import annotations  # Keep the annotations independent from the import order.

import logging  # Record each gate read without a secret.
from collections.abc import Callable, Iterable, Mapping  # Accept each input without a concrete type.
from dataclasses import dataclass  # Keep each view value frozen and small.
from typing import Any  # The stored record holds JSON values of mixed types.

logger = logging.getLogger(__name__)  # Keep the records of this module under one name.

PRECHECK_FIELD = "pre_captures"  # The operation field that names the capture of each site.
DEFAULT_TIER = 2  # The tier that the capture page selects first.
NAME_SEPARATOR = ", "  # The separator of the site names in the refusal message.

PrecheckReader = Callable[[str], tuple[str, int]]  # One site in, the capture identifier and the tier out.


@dataclass(frozen=True, slots=True)
class SitePrecheck:
    """Hold the newest pre-check capture of one site, or an empty identifier."""

    site_id: str  # The site that the operator selected.
    site_name: str  # The name that the page and the refusal message show.
    capture_id: str  # The verified capture, or empty text when the site holds none.
    tier: int  # The tier of the capture.

    @property
    def ready(self) -> bool:
        """Report whether the site holds a verified pre-check capture."""
        return bool(self.capture_id)  # The adopter answers empty text for a site with no capture.

    def stored(self) -> dict[str, Any]:
        """Return the entry that the operation record stores for this site."""
        return {"site_id": self.site_id, "site_name": self.site_name, "capture_id": self.capture_id, "tier": self.tier}


@dataclass(frozen=True, slots=True)
class OrgPrecheckState:
    """Hold the pre-check capture of each selected site, in the order of the selection."""

    sites: tuple[SitePrecheck, ...]  # One entry for each selected site.

    @property
    def ready(self) -> bool:
        """Report whether the gate opens.

        Returns:
            True only when one or more sites exist and each site holds a capture.
        """
        return bool(self.sites) and all(site.ready for site in self.sites)  # An empty selection stays closed.

    @property
    def missing(self) -> tuple[SitePrecheck, ...]:
        """Return each site that holds no pre-check capture, in the order of the selection."""
        return tuple(site for site in self.sites if not site.ready)  # The sites that close the gate.

    def missing_names(self) -> str:
        """Return the names of the sites that hold no capture, for the refusal message."""
        return NAME_SEPARATOR.join(site.site_name for site in self.missing)  # One name for each missing site.

    def stored(self) -> list[dict[str, Any]]:
        """Return the list that the start route writes into the operation record."""
        return [site.stored() for site in self.sites]  # The order of the selection.


class OrgPrecheckGate:
    """Read the pre-check capture of each selected site through one reader seam."""

    def __init__(self, reader: PrecheckReader | None) -> None:
        """Keep the reader of the newest pre-check capture of one site.

        Args:
            reader: The capture reader, or None when the portal holds no pre-check seam.
        """
        self.reader = reader  # None keeps the gate closed for each site.

    def read(self, site_ids: Iterable[str], names: Mapping[str, str]) -> OrgPrecheckState:
        """Read the capture of each site, in the order of the selection.

        Args:
            site_ids: The selected sites.
            names: The name of each site. A site with no name shows its identifier.

        Returns:
            The state of the gate.
        """
        ordered = [str(site_id) for site_id in site_ids]  # One read for each site, in order.
        logger.info("org precheck: read the pre-check capture of %d sites", len(ordered))  # BEFORE the reads.
        sites = tuple(self._read_site(site_id, str(names.get(site_id) or site_id)) for site_id in ordered)
        state = OrgPrecheckState(sites)  # The gate of the confirm page and of the start route.
        logger.debug("org precheck: %d of %d sites hold a capture", len(sites) - len(state.missing), len(sites))
        return state  # The caller shows the card or refuses the start.

    def _read_site(self, site_id: str, site_name: str) -> SitePrecheck:
        """Read the capture of one site, and count a fault as a missing capture."""
        if self.reader is None:  # The portal holds no pre-check seam.
            return SitePrecheck(site_id, site_name, "", DEFAULT_TIER)  # The gate fails closed.
        try:  # A store fault must close the gate, never open it.
            capture_id, tier = self.reader(site_id)  # The newest verified capture and its tier.
        except Exception as error:  # Any fault of the store read counts as no capture.
            logger.warning("org precheck: the read of site %s failed: %s", site_id, type(error).__name__)
            return SitePrecheck(site_id, site_name, "", DEFAULT_TIER)  # The operator can start a new capture.
        return SitePrecheck(site_id, site_name, str(capture_id or ""), SitePrecheckTier.read(tier))  # The pair.

    @staticmethod
    def rows_of(record: Mapping[str, Any]) -> list[dict[str, Any]]:
        """Return the stored capture of each site, for the progress page and the poll.

        Why:
            An operation from an earlier release holds no list. A damaged entry
            must never break the progress page, so the reader skips it.

        Args:
            record: The durable operation record.

        Returns:
            One row for each stored entry that names a capture.
        """
        entries = record.get(PRECHECK_FIELD)  # The list that the start route wrote.
        if not isinstance(entries, list):  # No list, or a damaged value.
            return []  # The page shows the note of an earlier operation.
        return [OrgPrecheckGate._row_of(entry) for entry in entries if OrgPrecheckGate._names_capture(entry)]

    @staticmethod
    def _names_capture(entry: Any) -> bool:
        """Report whether one stored entry names a capture."""
        return isinstance(entry, Mapping) and bool(entry.get("capture_id"))  # Skip a damaged entry.

    @staticmethod
    def _row_of(entry: Mapping[str, Any]) -> dict[str, Any]:
        """Return one normalized row of the progress card."""
        site_id = str(entry.get("site_id") or "")  # The site of the capture.
        name = str(entry.get("site_name") or site_id)  # A site with no name shows its identifier.
        tier = SitePrecheckTier.read(entry.get("tier"))  # The stored tier, as a number.
        return SitePrecheck(site_id, name, str(entry["capture_id"]), tier).stored()  # The four fields.


class SitePrecheckTier:
    """Read one stored tier value."""

    @staticmethod
    def read(value: Any) -> int:
        """Return the stored tier as a number, or the default tier for a damaged value."""
        try:  # A stored value can be a number or text.
            return int(value)  # The tier that the capture used.
        except (TypeError, ValueError):  # A damaged value.
            return DEFAULT_TIER  # The page still shows the capture link.
