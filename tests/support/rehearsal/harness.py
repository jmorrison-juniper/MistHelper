"""The harness that drives the shipped run driver against a stand-in cloud.

Why:
    The harness must drive the shipped code and never a copy of it. The entry
    point is ``RunDriver.start`` at ``src/upgrade_portal/upgrade/driver.py``. A
    test that passed while the shipped settle gate never ran would prove
    nothing at all.

    The harness replaces five attachment points and fills four time seats. It
    holds no settle rule, no phase order, and no stop rule. Every rule that the
    rehearsal proves lives in the shipped modules.
"""

from __future__ import annotations

import logging
import threading
import uuid
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import mistapi
import pytest

from src.firmware import upgrade_service
from src.upgrade_portal.runtime.runs import PHASE_ORDER, RunRecordBuilder, RunState
from src.upgrade_portal.upgrade import driver, events, gate, phase_gate
from tests.support.rehearsal.clock import RehearsalClock
from tests.support.rehearsal.cloud import StandInCloud
from tests.support.rehearsal.errors import RehearsalNetworkError
from tests.support.rehearsal.script import FleetScript, cascade_fleet

logger = logging.getLogger(__name__)  # The module logger, so each run carries this name.

# WHY: An obviously fake organization and site. No value of the rehearsal names
# a real Mist tenant, so a stray call could not reach a real site even if the
# network guard were absent.
ORG_ID: str = "00000000-0000-0000-0000-000000000992"
SITE_ID: str = "00000000-0000-0000-0000-000000001992"

# WHY: The schema version that ``RunRecordBuilder.validate`` accepts. The
# harness reads it from the shipped builder and states no number of its own.
JOIN_SECONDS: float = 5.0

# WHY: ``gate.read_fleet_statistics`` reads the shared page size, and the
# shared reader imports ``MistHelper``. That import runs a dependency check
# that asks the package index over the network for a newer version. The check
# belongs to the start-up path of the program and not to the upgrade path, so
# the harness answers the page size directly and reaches no network.
PAGE_LIMIT: int = 1000


@dataclass(frozen=True, slots=True)
class ProgressRound:
    """The progress report of one poll round.

    Attributes:
        phase: The phase name that the round watched.
        settled: How many devices of the phase had returned.
        total: How many devices the phase holds.
        at: The clock reading of the round.
    """

    phase: str
    settled: int
    total: int
    at: float


class ProgressLog:
    """Record the progress report of every poll round.

    Why:
        Section 5 of ``contracts/rehearsal-clock.md`` proves the settle window
        from the poll record of one composed run. This reporter is that record.
    """

    def __init__(self, clock: RehearsalClock) -> None:
        """Build one empty progress log.

        Args:
            clock: The one time source of the run.
        """
        self._clock = clock  # The reading that dates each round.
        self._rounds: list[ProgressRound] = []  # Every round, in round order.
        self._guard = threading.Lock()  # The driver thread appends while the test thread reads.

    def report(self, progress: phase_gate.PhaseProgress) -> None:
        """Record how far one phase moved after one poll round.

        Args:
            progress: The report that the shipped phase gate built.
        """
        entry = ProgressRound(progress.phase, progress.settled, progress.total, self._clock.now())  # One round.
        with self._guard:  # One writer at a time keeps the list whole.
            self._rounds.append(entry)  # The settle window test walks this list.

    def rounds(self) -> tuple[ProgressRound, ...]:
        """Return every recorded round in round order.

        Returns:
            The progress rounds.
        """
        with self._guard:  # The driver thread may append at this moment.
            return tuple(self._rounds)  # A tuple copy leaves the record safe.


class RunStoreDouble:
    """An in-memory run record store with the two shipped operations.

    Why:
        The driver reads the record back before every write, so a plain
        dictionary is not enough. This double keeps the same read-then-write
        order that the ArangoDB store keeps.
    """

    def __init__(self) -> None:
        """Build one empty store."""
        self.records: dict[str, dict[str, Any]] = {}  # Every written record, by run key.
        self.writes: list[str] = []  # The state after each write, for the phase order test.
        self._guard = threading.Lock()  # The driver thread writes while the test thread reads.

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return one run record.

        Args:
            run_id: The run key.

        Returns:
            A copy of the record, or None when the store holds no such run.
        """
        with self._guard:  # The driver thread may write at this moment.
            record = self.records.get(run_id)  # The stored copy of the record.
            return dict(record) if record is not None else None  # A copy leaves the store unchanged.

    def write_run(self, run: dict[str, Any]) -> bool:
        """Write one run record and report the true result.

        Args:
            run: The whole record, with the changed fields already in place.

        Returns:
            True, because the in-memory store always accepts a write.
        """
        with self._guard:  # One writer at a time keeps the record whole.
            self.records[str(run.get("run_id", ""))] = dict(run)  # A copy stops a later edit by the caller.
            self.writes.append(str(run.get("state", "")))  # The state order proves the cascade order.
        return True  # The driver fails the run when a write reports False.


class CaptureDouble:
    """The post-check capture path of the rehearsal.

    Why:
        FR-022 asks the suite to prove that the driver started the second
        capture after the client phase settled. This double records the request
        and answers a key, so the run reaches its final state.
    """

    def __init__(self) -> None:
        """Build one capture double."""
        self.requests: list[dict[str, Any]] = []  # Every capture request, in call order.
        self.started_at: list[float] = []  # The clock reading of each start, for the order test.

    def start(self, request: Any) -> str | None:
        """Start one capture and return its key.

        Args:
            request: The run key, the ordinal, and the role.

        Returns:
            The capture key of the rehearsal.
        """
        logger.info("The capture double starts the capture of run %s", request.get("run_id", ""))  # The action.
        self.requests.append(dict(request))  # The post-check test reads the ordinal and the role.
        logger.debug("The capture double holds %s requests", len(self.requests))  # The result of the action.
        return "capture-rehearsal-0002"  # A key, because an empty answer fails the run.


@dataclass(frozen=True, slots=True)
class RehearsalDeps:
    """Everything one rehearsal run needs from outside itself.

    Attributes:
        clock: The one time source of the run.
        fleet: The scripts of the run.
        store: The in-memory run record store.
        capture: The post-check capture double.
    """

    clock: RehearsalClock = field(default_factory=RehearsalClock)
    fleet: FleetScript | None = None
    store: RunStoreDouble = field(default_factory=RunStoreDouble)
    capture: CaptureDouble = field(default_factory=CaptureDouble)


def build_targets(fleet: FleetScript, site_id: str = SITE_ID) -> list[dict[str, Any]]:
    """Return one run record target for each device of the fleet.

    Why:
        ``phase_gate.build_targets`` reads five keys of each entry, and it
        drops an entry with no usable address. The builder writes all five and
        adds the two fields that the stop path reads.

    Args:
        fleet: The scripts of the run.
        site_id: The site that holds every device.

    Returns:
        The target entries of the run record.
    """
    return [
        {
            "mac": script.mac,  # The address that the gate joins against a statistics record.
            "device_type": script.device_type,  # The family that sorts the device into one phase.
            "version_before": script.version_before,  # One half of the reboot proof.
            "uptime_before": script.uptime_before,  # The other half, which must fall at the reboot.
            "last_seen_before": None,  # The pre-check read no cloud moment, so the anchor path stays shut.
            "name": script.mac,  # The plan needs a name, and the address is the honest one here.
            "site_id": site_id,  # The site of the device, which the plan route reads.
        }
        for script in fleet.scripts
    ]


def build_record(fleet: FleetScript, run_id: str | None = None) -> dict[str, Any]:
    """Return one run record that is ready for the driver.

    Why:
        Rule 1 of section 5 of ``data-model.md`` asks for a unique run key,
        because ``RunDriver._THREADS`` keys the live thread by that key. A
        repeated key would hand the second test the thread of the first.

    Args:
        fleet: The scripts of the run.
        run_id: The run key, or None to mint a fresh one.

    Returns:
        The run record, in the state that comes before the submission.
    """
    key = run_id if run_id is not None else f"run-{uuid.uuid4().hex}"  # A fresh key for each run.
    record: dict[str, Any] = {"_key": key, "run_id": key, "schema_version": 1}  # The three identity fields.
    record.update({"org_id": ORG_ID, "org_name": "Rehearsal", "site_id": SITE_ID, "site_name": "Rehearsal site"})
    record.update({"actor_email": "operator@example.com", "browser_id": "rehearsal", "tier": 2})
    record.update({"created_at": "2026-01-01T00:00:00+00:00", "updated_at": "2026-01-01T00:00:00+00:00"})
    record.update({"state": RunState.AWAITING_CONFIRMATION.value, "options": {}, "error": None})
    record.update({"targets": build_targets(fleet), "phases": RunRecordBuilder.initial_phases()})
    record.update({"stop_request": None, "pre_capture_id": "capture-rehearsal-0001", "post_capture_id": None})
    return record


class RehearsalHarness:
    """Drive the shipped run driver against the stand-in cloud.

    Why:
        The harness owns the wiring and nothing else. It builds the shipped
        settle gate, the shipped phase gate, and the shipped run driver, and it
        gives each one the driven clock.
    """

    def __init__(self, deps: RehearsalDeps | None = None) -> None:
        """Build one harness.

        Args:
            deps: The clock, the fleet, the store, and the capture double.
        """
        base = deps if deps is not None else RehearsalDeps()  # A default harness runs the cascade fleet.
        self.clock = base.clock  # The one time source of all four seats.
        self.fleet = self._anchored(base.fleet)  # The scripts, anchored on the first clock reading of the run.
        self.deps = base  # The store and the capture double travel on this record.
        self.progress = ProgressLog(self.clock)  # The poll record that the settle window test reads.
        self.cloud = StandInCloud(self.fleet, self.clock)  # The five answers of the stand-in cloud.
        self.record_body = build_record(self.fleet)  # The run record that the driver carries.
        self._thread: threading.Thread | None = None  # The driver thread, once the run starts.

    def _anchored(self, fleet: FleetScript | None) -> FleetScript:
        """Return the fleet of the run, anchored on the clock of the harness.

        Why:
            Every scripted offset counts from the start of the run, and the
            clock starts at an epoch moment. A fleet that a test built with no
            anchor would place every event far in the past, and no device would
            ever reconnect.

        Args:
            fleet: The scripts that the test supplied, or None.

        Returns:
            The fleet with a true start moment.
        """
        logger.info("Anchor the fleet of the run on the clock")  # The action, before it happens.
        anchored = cascade_fleet(self.clock.now()) if fleet is None else fleet  # The default fleet of a bare harness.
        if anchored.started_at == 0.0:  # A test that named no anchor takes the first reading of this clock.
            anchored = replace(anchored, started_at=self.clock.now())  # The offsets now count from the run start.
        logger.debug("The fleet starts at reading %s", anchored.started_at)  # The result of the action.
        return anchored  # Every stand-in answer reads the offsets from this moment.

    def attach(self, monkeypatch: pytest.MonkeyPatch, data_root: Path | None = None) -> StandInCloud:
        """Replace the five attachment points with the stand-in answers.

        Why:
            ``monkeypatch`` reverts every replacement at the end of the test,
            so no rehearsal leaves a patch behind for the next test.

        Args:
            monkeypatch: The pytest patch helper.
            data_root: The directory of the upgrade tracker file. None leaves
                the shipped directory of the repository.

        Returns:
            The stand-in cloud that now answers each point.
        """
        logger.info("Attach the stand-in cloud of run %s", self.record_body["run_id"])  # The action.
        monkeypatch.setattr(mistapi.api.v1.orgs.stats, "listOrgDevicesStats", self.cloud.list_org_devices_stats)
        monkeypatch.setattr(mistapi, "get_all", self.cloud.get_all)  # The page walk of the statistics read.
        monkeypatch.setattr(mistapi.api.v1.orgs.devices, "searchOrgDeviceEvents", self.cloud.search_org_device_events)
        monkeypatch.setattr(
            mistapi.api.v1.const.device_events,
            "listDeviceEventsDefinitions",
            self.cloud.list_device_events_definitions,
        )
        monkeypatch.setattr(upgrade_service, "_resolve_endpoint", self.cloud.resolve_endpoint)  # The write refusal.
        monkeypatch.setattr(gate, "resolve_page_limit", lambda: PAGE_LIMIT)  # The start-up import reaches the index.
        if data_root is not None:  # The tracker write must land in a temporary directory and not in the repository.
            monkeypatch.setattr(driver, "data_root", lambda: data_root)  # The shipped resolver of the tracker path.
        logger.debug("The stand-in cloud now answers 5 attachment points")  # The result of the action.
        return self.cloud  # The test reads the counters and the call record from this object.

    def _phase_gate(self) -> phase_gate.PhaseSettleGate:
        """Build the shipped phase gate with the driven clock in every seat.

        Why:
            Three of the four time seats live here. The fourth lives on the run
            driver. One ``RehearsalClock`` fills all four, so the phase
            deadline and the device wait never drift apart.

        Returns:
            The shipped phase gate, wired to the stand-in cloud.
        """
        settle = gate.SettleGate(clock=self.clock.now)  # Seat 1 of the four time seats.
        catalogue = events.EventCatalogue()  # A fresh catalogue, so the cached answer belongs to this run alone.
        reader = phase_gate.CloudReconnectReader(None, ORG_ID, catalogue, self.clock.now)  # Seat 3 of the four.
        statistics = phase_gate.CloudStatisticsReader(None, ORG_ID, SITE_ID)  # The fleet statistics read.
        deps = phase_gate.PhaseGateDeps(reader, statistics, settle, self.progress, self.clock.sleep)  # Seat 2.
        return phase_gate.PhaseSettleGate(deps)  # The shipped loop, which holds every settle rule.

    def start(self) -> threading.Thread:
        """Build the run driver and start the one thread that owns the run.

        Returns:
            The driver thread.
        """
        run_id = str(self.record_body["run_id"])  # The key that names the thread and the record.
        logger.info("Start the rehearsal of run %s", run_id)  # The action, before it happens.
        gate_adapter = phase_gate.as_phase_gate(self._phase_gate())  # The protocol that the driver calls.
        deps = driver.RunDriverDeps(self.deps.store, gate_adapter, self.deps.capture, None, self.clock)  # Seat 4.
        self._thread = driver.RunDriver(deps).start(self.record_body)  # The shipped entry point of the run.
        logger.debug("The rehearsal of run %s holds a driver thread", run_id)  # The result of the action.
        return self._thread  # The test joins this thread.

    def join(self, timeout: float = JOIN_SECONDS) -> None:
        """Wait for the driver thread to finish.

        Why:
            Rule 2 of section 5 of ``data-model.md`` makes this a guard and not
            a wait. A healthy run finishes in milliseconds, because every sleep
            of the clock returns at once.

        Args:
            timeout: The real seconds to wait before the guard gives up.

        Raises:
            RehearsalNetworkError: When the driver thread did not finish.
        """
        if self._thread is None:  # A caller that joins before the start has nothing to wait for.
            return  # The test then reads an untouched record, which is honest.
        self._thread.join(timeout)  # The one real wait of the whole rehearsal.
        if self._thread.is_alive():  # A hung run must fail this test and never hang the suite.
            raise RehearsalNetworkError(f"The rehearsal run did not finish inside {timeout} seconds.")

    def record(self) -> dict[str, Any]:
        """Return the run record that the store holds.

        Returns:
            The stored record, or the in-memory record before the first write.
        """
        stored = self.deps.store.read_run(str(self.record_body["run_id"]))  # The record that the driver wrote.
        return stored if stored is not None else dict(self.record_body)  # A run that never wrote answers its start.

    def phase_entry(self, name: str) -> dict[str, Any]:
        """Return one phase entry of the stored run record.

        Args:
            name: The phase name. One of the four members of ``PHASE_ORDER``.

        Returns:
            The phase entry, or an empty mapping when the record holds none.

        Raises:
            ValueError: When the name is not a cascade phase.
        """
        if name not in PHASE_ORDER:  # A typing mistake would answer an empty entry and pass a weak test.
            raise ValueError(f"the phase {name} is not a cascade phase")
        entries = self.record().get("phases", [])  # The four entries that the driver writes.
        matches = [entry for entry in entries if str(entry.get("name", "")) == name]  # The one entry of that phase.
        return dict(matches[0]) if matches else {}  # An empty mapping names a record that holds no such phase.
