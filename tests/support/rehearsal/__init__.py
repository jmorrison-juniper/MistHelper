"""The rehearsal harness of the upgrade run driver.

Why:
    Issue #1992 asks for a rehearsal that drives the shipped upgrade path
    without a real device, a real cloud, and a real firmware write. This
    package holds the driven clock, the fleet scripts, the stand-in cloud, and
    the harness that joins them to the shipped run driver.

    The package holds no settle rule and no phase order. Every rule that the
    rehearsal proves lives in ``src/upgrade_portal/upgrade``.
"""

from tests.support.rehearsal.clock import START_EPOCH_SECONDS, RehearsalClock
from tests.support.rehearsal.cloud import CallRecord, StandInCloud, StandInResponse
from tests.support.rehearsal.defects import DEFECT_NAMES, DefectDrill
from tests.support.rehearsal.errors import RehearsalError, RehearsalFirmwareError, RehearsalNetworkError
from tests.support.rehearsal.harness import (
    ORG_ID,
    SITE_ID,
    CaptureDouble,
    ProgressLog,
    ProgressRound,
    RehearsalDeps,
    RehearsalHarness,
    RunStoreDouble,
    build_record,
    build_targets,
)
from tests.support.rehearsal.script import (
    TYPE_ACCESS_POINT,
    TYPE_GATEWAY,
    TYPE_SWITCH,
    VERSION_AFTER,
    VERSION_BEFORE,
    DeviceScript,
    FleetScript,
    cascade_fleet,
    stop_fleet,
)

__all__ = [
    "DEFECT_NAMES",
    "ORG_ID",
    "SITE_ID",
    "START_EPOCH_SECONDS",
    "TYPE_ACCESS_POINT",
    "TYPE_GATEWAY",
    "TYPE_SWITCH",
    "VERSION_AFTER",
    "VERSION_BEFORE",
    "CallRecord",
    "DefectDrill",
    "CaptureDouble",
    "DeviceScript",
    "FleetScript",
    "ProgressLog",
    "ProgressRound",
    "RehearsalClock",
    "RehearsalDeps",
    "RehearsalError",
    "RehearsalFirmwareError",
    "RehearsalHarness",
    "RehearsalNetworkError",
    "RunStoreDouble",
    "StandInCloud",
    "StandInResponse",
    "build_record",
    "build_targets",
    "cascade_fleet",
    "stop_fleet",
]
