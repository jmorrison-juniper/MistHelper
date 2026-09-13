"""The three known defect classes that the rehearsal harness must catch.

Why:
    A harness that passes against broken code gives false confidence. The
    portal writes firmware to production hardware, so the harness must fail
    when the shipped code holds one of the defects that this repository met
    before. Each applier below reproduces one of those defects.

    Every applier takes the ``monkeypatch`` fixture, so pytest reverts the
    defect at the end of the test. No applier touches the ``time`` module,
    because a process-wide clock patch reaches the threads of other tests.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import mistapi

from src.firmware import upgrade_service
from src.upgrade_portal.upgrade import gate

from .clock import START_EPOCH_SECONDS
from .cloud import StandInCloud, StandInResponse

logger = logging.getLogger(__name__)

__all__ = ["DefectDrill", "DEFECT_NAMES"]

# WHY: The summary test of T038 reads these names, so one list holds them.
DEFECT_NAMES: tuple[str, str, str] = (
    "event_family_ignored",
    "uptime_rule_reads_the_clock",
    "status_field_renamed",
)


class DefectDrill:
    """Apply one known defect to the shipped code under a rehearsal run.

    Attributes:
        applied: The name of each defect that this drill applied.
    """

    def __init__(self) -> None:
        """Start a drill that has applied no defect."""
        logger.info("The rehearsal built a defect drill")  # The action before the build.
        self.applied: list[str] = []  # The record that the summary test of T038 reads.
        logger.debug("The drill holds %s applied defects", len(self.applied))  # The result of the build.

    def event_family_ignored(self, monkeypatch: Any, cloud: StandInCloud) -> None:
        """Drop the family of the event search, as the first defect class did.

        Why:
            A caller that sends no ``device_type`` reads access points alone,
            because that is the default of the cloud. The gateway phase and the
            switch phase then never see a reconnect event, and they fail.

        Args:
            monkeypatch: The pytest fixture that reverts the patch.
            cloud: The stand-in cloud that answers the search.
        """
        logger.info("The drill applies the defect %s", DEFECT_NAMES[0])  # The action before the patch.
        del cloud  # The defect sits at the call seam, so the stand-in needs no change.
        honest: Any = mistapi.api.v1.orgs.devices.searchOrgDeviceEvents  # The answer that the harness attached.

        def broken(session: Any, org_id: str, **keywords: Any) -> StandInResponse:
            """Answer the search with the family that the caller did not send."""
            keywords.pop("device_type", None)  # The defect: the family never reaches the cloud.
            answer: StandInResponse = honest(session, org_id, **keywords)  # The cloud default answers access points.
            return answer  # The caller reads one family, and it is not the family it asked for.

        monkeypatch.setattr(mistapi.api.v1.orgs.devices, "searchOrgDeviceEvents", broken)  # The seam holds it.
        self.applied.append(DEFECT_NAMES[0])  # The summary test reads this record.
        logger.debug("The drill applied %s defects", len(self.applied))  # The result of the patch.

    def uptime_rule_reads_the_clock(self, monkeypatch: Any, cloud: StandInCloud) -> None:
        """Prove a reboot from a clock reading, as the second defect class did.

        Why:
            An uptime in seconds is always smaller than a moment in epoch
            seconds, so this rule answers True for every reading. A device that
            the cloud already reports on the target version then settles before
            it rebooted.

        Args:
            monkeypatch: The pytest fixture that reverts the patch.
            cloud: The stand-in cloud, which this defect leaves unchanged.
        """
        logger.info("The drill applies the defect %s", DEFECT_NAMES[1])  # The action before the patch.
        del cloud  # The defect sits in the gate, so the stand-in needs no change.

        def broken(uptime_before: int | None, uptime_now: int | None) -> bool:
            """Compare the uptime against a moment of the local clock."""
            del uptime_before  # The defect drops the only honest half of the test.
            return uptime_now is not None and uptime_now < START_EPOCH_SECONDS  # Always True for a real uptime.

        monkeypatch.setattr(gate, "uptime_decreased", broken)  # The shipped gate now holds the defect.
        self.applied.append(DEFECT_NAMES[1])  # The summary test reads this record.
        logger.debug("The drill applied %s defects", len(self.applied))  # The result of the patch.

    def status_field_renamed(self, monkeypatch: Any, cloud: StandInCloud) -> None:
        """Read the phase under the wrong name, as the third defect class did.

        Why:
            The cloud names the phase field ``current_phase``. A reader that
            takes ``phase`` reports no phase at all, and the operator loses the
            one field that names the state of the write.

        Args:
            monkeypatch: The pytest fixture that reverts the patch.
            cloud: The stand-in cloud, which this defect leaves unchanged.
        """
        logger.info("The drill applies the defect %s", DEFECT_NAMES[2])  # The action before the patch.
        honest = upgrade_service._normalize_status  # The healthy reader fills every other field.

        def broken(payload: Mapping[str, object], upgrade_id: str, raw_status: int) -> Mapping[str, object]:
            """Return the status fields with the phase read under the wrong name."""
            fields = dict(honest(payload, upgrade_id, raw_status))  # Every other field keeps its honest value.
            fields["current_phase"] = payload.get("phase")  # The defect: the cloud never sends this name.
            return fields  # The caller now reads no phase.

        monkeypatch.setattr(upgrade_service, "_normalize_status", broken)  # The shipped reader holds the defect.
        del cloud  # The defect sits in the reader, so the stand-in needs no change.
        self.applied.append(DEFECT_NAMES[2])  # The summary test reads this record.
        logger.debug("The drill applied %s defects", len(self.applied))  # The result of the patch.
