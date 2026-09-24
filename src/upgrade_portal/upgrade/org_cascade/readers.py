"""The cloud reads of the multi-site phase watch.

Why:
    Issue #3245. The single-site gate reads the statistics of one site. A
    multi-site phase can hold devices at many sites, so each phase gets its own
    reader. The reader asks for one device family, so the answer holds the
    devices of that phase only.

    The single-site budget assumes two calls in each 20-second round. A read of
    many pages costs more calls, so ``BudgetSleep`` stretches the wait between
    two rounds. The gate reads its deadline from the clock, so a longer wait
    gives fewer rounds and keeps the deadline correct.
"""

from __future__ import annotations

import logging
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from src.upgrade_portal.capture.devices import normalize_device_mac, resolve_page_limit
from src.upgrade_portal.upgrade import gate, phase_gate
from src.upgrade_portal.upgrade.org_cascade.record import OrgPhaseTargets

logger = logging.getLogger(__name__)  # One logger for the cloud reads of the phase watch.

ANCHOR_GAP_NOTE: Final[str] = (  # FR-002: the page names the count of devices with no uptime anchor.
    "The portal could not read the uptime of {count} device(s) before the upgrade. "
    "The gate settles those devices on the firmware version alone."
)


class OrgStatisticsReader:
    """Read the statistics of the devices of one phase (FR-015)."""

    def __init__(self, session: Any, org_id: str, family: str, site_ids: Sequence[str]) -> None:
        """Keep the scope of one phase read.

        Args:
            session: The cloud session of the operator. The caller owns it.
            org_id: The organization that owns the devices.
            family: The device family of the phase: gateway, switch, or ap.
            site_ids: The sites of the devices of the phase.
        """
        self._session = session  # The cloud session that every read uses.
        self._org_id = org_id  # The organization of the operation.
        self._family = family  # One family, so the answer holds this phase only.
        self._site_id = site_ids[0] if len(site_ids) == 1 else None  # One site narrows the read further.
        self._pages = 1  # The page count of the last read. One page before the first read.

    @property
    def page_count(self) -> int:
        """Return the page count of the last read."""
        return self._pages  # BudgetSleep reads this count after each round.

    def read(self) -> gate.FleetRead:
        """Read the statistics of one phase with one paged call.

        Returns:
            The readings and the reasons of one poll.
        """
        scope = self._site_id or "every site"  # The log names the scope of the read.
        limit = max(1, int(resolve_page_limit()))  # One page size for the read and for the cost count.
        logger.info("org cascade: read the %s statistics of %s", self._family, scope)  # Before the cloud read.
        result = gate.read_fleet_statistics(  # One paged cloud read for the family of this phase.
            self._session, self._org_id, self._site_id, page_limit=limit, device_type=self._family
        )
        self._pages = max(1, math.ceil(len(result.readings) / limit))  # FR-016: the cost of this round.
        logger.debug("org cascade: read %d readings in %d page(s)", len(result.readings), self._pages)  # After.
        return result  # The gate reads the readings and the reasons.


class BudgetSleep:
    """Stretch the wait between two rounds by the page count of the last read (FR-016)."""

    def __init__(self, reader: OrgStatisticsReader, sleep: Callable[[float], None]) -> None:
        """Keep the reader and the real sleep.

        Args:
            reader: The statistics reader of the phase.
            sleep: The real sleep. A test passes one that moves a fake clock.
        """
        self._reader = reader  # The source of the page count.
        self._sleep = sleep  # The wait itself.

    def __call__(self, seconds: float) -> None:
        """Wait for the asked time, stretched to keep the call budget.

        Args:
            seconds: The wait that the gate asked for.
        """
        factor = max(1.0, (1 + self._reader.page_count) / phase_gate.CALLS_PER_ROUND)  # One event read and pages.
        self._sleep(float(seconds) * factor)  # A longer wait gives fewer rounds before the deadline.


@dataclass(frozen=True, slots=True)
class AnchorRead:
    """Hold the anchors of one operation and the note of any gap.

    Attributes:
        anchors: The anchors of each device, keyed by the normalized address.
        note: The gap note, or empty text when every device has an uptime.
    """

    anchors: dict[str, dict[str, Any]]  # The uptime and the last report time of each device.
    note: str  # The page shows this note under the watch line.


class OrgSettleAnchors:
    """Read the uptime and the last report time of each device before the first write (FR-001)."""

    @staticmethod
    def read(session: Any, record: Mapping[str, Any]) -> AnchorRead:
        """Read the anchors of every device of one operation.

        Why:
            FR-002. The anchors help the gate, but they never block the
            upgrade. A failed read gives a null anchor and a note.

        Args:
            session: The cloud session of the operator.
            record: The durable operation record before the submission.

        Returns:
            The anchors and the note of any gap.
        """
        org_id = str(record.get("org_id", ""))  # Every child job sits in one organization.
        anchors: dict[str, dict[str, Any]] = {}  # The anchors of each device.
        for family, (macs, sites) in OrgSettleAnchors._groups(record).items():  # One read for each family.
            readings = OrgSettleAnchors._readings(session, org_id, family, sites)  # Never raises.
            for mac in macs:  # Store one anchor for each device of this family.
                reading = readings.get(mac)  # None when the answer does not hold the device.
                uptime = reading.uptime if reading is not None else None  # The uptime before the upgrade.
                seen = reading.last_seen if reading is not None else None  # The last report before the upgrade.
                anchors[mac] = {"uptime_before": uptime, "last_seen_before": seen}  # The single-site field names.
        gaps = sum(1 for anchor in anchors.values() if anchor["uptime_before"] is None)  # FR-002: count the gaps.
        note = ANCHOR_GAP_NOTE.format(count=gaps) if gaps else ""  # Name the gap on the page.
        logger.debug("org cascade: stored %d anchors with %d gap(s)", len(anchors), gaps)  # After every read.
        return AnchorRead(anchors, note)  # The submission stores both.

    @staticmethod
    def _groups(record: Mapping[str, Any]) -> dict[str, tuple[list[str], list[str]]]:
        """Group the devices of one operation by family, with the sites of each family.

        Args:
            record: The durable operation record.

        Returns:
            The addresses and the sites of each family.
        """
        groups: dict[str, tuple[list[str], list[str]]] = {}  # The addresses and the sites of each family.
        for child in OrgPhaseTargets.children(record):  # Every child job of the plan.
            for target in child.get("targets") or ():  # Every device of the child job.
                mac = (  # The normalized address, or empty text for a damaged entry.
                    normalize_device_mac(target.get("mac")) if isinstance(target, Mapping) else ""
                )
                family = str(target.get("device_type", "")).strip().lower() if mac else ""  # The phase family.
                if not family:  # A damaged entry names no device or no family.
                    continue  # The gate drops this entry too.
                macs, sites = groups.setdefault(family, ([], []))  # One group for each family.
                macs.append(mac)  # Keep the device.
                site = str(target.get("site_id") or "")  # The site of the device.
                if site and site not in sites:  # Keep each site one time.
                    sites.append(site)  # The read scope of this family.
        return groups  # The input of one read for each family.

    @staticmethod
    def _readings(session: Any, org_id: str, family: str, sites: Sequence[str]) -> Mapping[str, gate.GateReading]:
        """Read one family, and return an empty map when the read fails.

        Args:
            session: The cloud session of the operator.
            org_id: The organization of the operation.
            family: The device family to read.
            sites: The sites of the devices of this family.

        Returns:
            The readings of the family, keyed by the normalized address.
        """
        logger.info("org cascade: read the anchors of the %s family", family)  # Before the cloud read.
        try:  # A fault in one family read must not stop the submission.
            readings = OrgStatisticsReader(session, org_id, family, sites).read().readings  # One paged read.
        except Exception as error:  # Keep broad: FR-002 says an anchor read never blocks the upgrade.
            logger.warning(  # After the failed read. The type names the fault and holds no secret.
                "org cascade: the anchor read of %s failed with %s", family, type(error).__name__
            )
            return {}  # Every device of this family then holds a null anchor.
        logger.debug("org cascade: the anchor read of %s holds %d readings", family, len(readings))  # After.
        return readings  # The caller looks up each device.
