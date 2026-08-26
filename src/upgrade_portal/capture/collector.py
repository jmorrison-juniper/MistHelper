"""The capture collector: one site and one tier become one stored capture.

Why:
    ``app/routes/capture.py`` answers 202 and hands the reading to a worker
    thread. That thread calls this module. Every part of the work already
    exists: ``devices``, ``clients``, and ``extras`` read the cloud,
    ``assembly`` builds the document, and ``store`` writes it and reads it
    back. This module owns the order of that work, the concurrency, and the
    progress that the browser polls.

Concurrency:
    The reads run in two waves through ``CapturePool``. Wave one holds the
    four call groups that every tier reads, which matches the four capture
    workers of ``runtime/pools.py``. Wave two holds the tier 3 group, which
    must wait, because the radio section reads the device statistics of wave
    one. Inside one call group the calls stay in order, because the cloud
    pages with a cursor.

The six progress rows and the five stored sections:
    ``contracts/http-api.md:155`` lists six section rows in the progress body
    and ``capture/capture.html`` renders six rows. The stored document holds
    five digest sections, and ``data-model.md`` section 3.5 keeps the alarms
    inside the extras. Both readings are correct, because they describe two
    different shapes. This module therefore drives the alarms row from the
    alarm sub-read of the tier 3 group and changes no stored shape.

Failure:
    A section that fails never stops the capture. The read records a partial
    reason, the other sections keep their data, and the document reports the
    status ``partial``. A capture stops only when the store refuses the write
    or when the read-back does not match.
"""

from __future__ import annotations  # Every annotation stays text, so a name may appear before its class.

import functools  # Binds the already-read rows and the ledger into a no-argument call.
import logging  # The portal logs with the standard library only.
import threading  # One guard keeps the reported percent from moving backwards.
from collections.abc import Callable, Mapping, Sequence  # The seam types and the read holders.
from dataclasses import dataclass, field  # The three small records of this module.
from typing import Any  # A cloud session, a store result, and a document are all free-form.

from src.upgrade_portal.capture import assembly, clients, devices, extras  # Every part of the work.

logger = logging.getLogger(__name__)  # One logger for each module keeps the source visible in the log.

# One term for each concept. `assembly` already names both tiers, so this
# module points at those names rather than spelling the numbers a second time.
TIER_STANDARD = assembly.TIER_STANDARD  # The device state and the client lists.
TIER_EXTRA = assembly.TIER_EXTRA  # Tier 2, the ports, the radios, the tunnels, the peers, and the alarms.

# The six progress rows of `contracts/http-api.md:155`. `assembly.py:96` owns
# these names and states why a report row and a digest key are two different
# things. This module points at those names, so one concept keeps one term.
ROW_DEVICES = assembly.SECTION_DEVICES  # The device inventory and the device statistics.
ROW_WIRED = assembly.SECTION_WIRED  # The wired clients of the site.
ROW_WIRELESS = assembly.SECTION_WIRELESS  # The join of both wireless reads.
ROW_GUEST = assembly.SECTION_GUEST  # The guest clients of the site.
ROW_EXTRAS = assembly.SECTION_EXTRAS  # The ports, the power, the radios, the tunnels, and the peers.
ROW_ALARMS = assembly.SECTION_ALARMS  # The open alarms, which own a row because an alarm blocks an upgrade.
ROW_NAMES: tuple[str, ...] = assembly.SECTION_NAMES  # Six rows, in the order that the capture page paints.
EXTRA_ROWS: tuple[str, ...] = (ROW_EXTRAS, ROW_ALARMS)  # Tier 2 reads neither of these two rows.

# The call groups that feed each row. A row is done when every group that feeds
# it is done, and failed when any one of them failed.
ROW_SOURCES: dict[str, tuple[str, ...]] = {  # One row, one or two feeding groups.
    ROW_DEVICES: (assembly.GROUP_DEVICES,),
    ROW_WIRED: (assembly.GROUP_WIRED_CLIENTS,),
    ROW_WIRELESS: (assembly.GROUP_WIRELESS_STATISTICS, assembly.GROUP_WIRELESS_SEARCH),
    ROW_GUEST: (assembly.GROUP_WIRED_CLIENTS,),
    ROW_EXTRAS: (assembly.GROUP_TIER_THREE,),
    ROW_ALARMS: (assembly.GROUP_TIER_THREE,),
}

# The report rows that each failure name covers. A call group and a sub-read
# both carry their own name, and `app/routes/capture.py:518` paints a row red
# only when a partial reason carries that row name. A reason that kept the
# call group name would therefore paint nothing, and a reloaded page would
# show a green row over a section that the capture never read. One name may
# cover two rows, because the wired group also reads the guest clients and the
# tier 3 group also reads the alarms.
REASON_ROWS: dict[str, tuple[str, ...]] = {  # One failure name, one or two rows.
    assembly.GROUP_DEVICES: (ROW_DEVICES,),
    devices.SECTION_INVENTORY: (ROW_DEVICES,),
    devices.SECTION_STATISTICS: (ROW_DEVICES,),
    assembly.GROUP_WIRED_CLIENTS: (ROW_WIRED, ROW_GUEST),
    assembly.GROUP_WIRELESS_STATISTICS: (ROW_WIRELESS,),
    assembly.GROUP_WIRELESS_SEARCH: (ROW_WIRELESS,),
    assembly.GROUP_TIER_THREE: (ROW_EXTRAS, ROW_ALARMS),
    extras.SECTION_SWITCH_PORTS: (ROW_EXTRAS,),
    extras.SECTION_POE: (ROW_EXTRAS,),
    extras.SECTION_RADIOS: (ROW_EXTRAS,),
    extras.SECTION_TUNNELS: (ROW_EXTRAS,),
    extras.SECTION_BGP_PEERS: (ROW_EXTRAS,),
    extras.SECTION_ALARMS: (ROW_ALARMS,),
}
REASON_SOURCE_FIELD = "source"  # Holds the first name, so the log and the document still agree.

# The four section states of `app/routes/capture.py:93`. Both modules spell the
# same words, because the browser reads them straight out of the status body.
STATE_PENDING = "pending"  # The row waits for its read.
STATE_DONE = "done"  # The read of this row finished.
STATE_SKIPPED = "skipped"  # This tier never reads the row.
STATE_FAILED = "failed"  # At least one read of this row did not finish.

# The capture states of `app/routes/capture.py:98` that this module reports.
CAPTURE_COLLECTING = "collecting"  # The reads run now.
CAPTURE_VERIFIED = "verified"  # The store wrote the record and the read-back matched.
CAPTURE_FAILED = "failed"  # The capture reached no stored record.

# The progress bar. The reads own the wide middle, because they hold the time.
READ_FLOOR = 5  # The bar shows a little as soon as the first read starts.
READ_CEILING = 85  # Every read finished, and the document is not built yet.
ASSEMBLE_PERCENT = 90  # The document is built.
WRITE_PERCENT = 95  # The write and the read-back run now.
WHOLE_PERCENT = 100  # The capture reached a final state.

COLLECTING_MESSAGE = "The portal is reading the site."  # Rides the `collecting` state.
ASSEMBLE_MESSAGE = "The portal is building the capture."  # Rides the `assembling` state.
WRITE_MESSAGE = "The portal is writing the capture."  # Rides the `writing` state.
VERIFIED_MESSAGE = "The portal read the capture back and the record matches."  # Rides the `verified` state.
PARTIAL_MESSAGE = "The portal stored the capture, but at least one section is missing."  # Also `verified`.
NO_SESSION_MESSAGE = "The portal holds no cloud session for this worker, so it cannot read the site."  # `failed`.
WRITE_FAILED_MESSAGE = "The portal could not store the capture. Read the portal log for the cause."  # `failed`.
READ_BACK_MESSAGE = "The portal stored the capture, but the read-back did not match."  # Also `failed`.
MISSING_RUN_MESSAGE = "The capture job names no run, so the portal cannot build a capture key."  # Also `failed`.

ProgressReport = Callable[[str, Mapping[str, Any]], None]  # Writes one change into the progress record.
SessionProvider = Callable[[Mapping[str, Any]], Any]  # Finds a cloud session for one job.
DeviceCall = Callable[[Any, str, str], tuple[Any, Any]]  # The inventory read and the statistics read.
ClientCall = Callable[[Any, str], tuple[Any, Any]]  # The wired read and the guest read.
RowCall = Callable[[Any, str], list[dict[str, Any]]]  # One paged row read.
ExtraCall = Callable[[Any, extras.SiteScope, Any], dict[str, extras.ExtraSection]]  # Every tier 3 section.
WriteCall = Callable[[Mapping[str, Any]], Any]  # Writes one capture document.
LoadCall = Callable[[str], Any]  # Reads one stored capture by identifier.

# The worker thread holds no request, so `runtime/identity.py` answers nothing
# there. The start route therefore reads the session and carries it in the job.
# An operator of this module may set one provider here for a caller that builds
# a job by hand, such as a command-line run.
SESSION_PROVIDER: SessionProvider | None = None  # An operator of this module may set one provider.


# ---------------------------------------------------------------------------
# The progress rows
# ---------------------------------------------------------------------------


def starting_rows(tier: int) -> dict[str, str]:
    """Build the first section map of one capture.

    Why:
        ``app/routes/capture.py`` builds the same map when the start route
        answers. This module builds it again rather than importing the web
        layer, because a module that reads the cloud must not need Flask.

    Args:
        tier: The data tier of the capture.

    Returns:
        One state for each of the six rows.
    """
    skipped = tier < TIER_EXTRA  # Tier 2 reads neither extra row.
    return {name: STATE_SKIPPED if skipped and name in EXTRA_ROWS else STATE_PENDING for name in ROW_NAMES}


def fold_states(states: Sequence[str]) -> str:
    """Fold the outcome of every group that feeds one row into one row state.

    Args:
        states: The outcome of each feeding group. An empty string means that
            the group has not finished.

    Returns:
        The row state ``failed``, ``done``, or ``pending``.
    """
    if STATE_FAILED in states:  # One lost group loses the whole row.
        return STATE_FAILED
    if states and all(state == STATE_DONE for state in states):  # Every feeding group finished.
        return STATE_DONE
    return STATE_PENDING  # At least one feeding group still runs.


class ProgressLedger:
    """Counts the finished call groups and reports a rising percent.

    Why:
        The browser polls the status endpoint every 30 seconds, so a percent
        that jumps from 0 to 100 tells the operator nothing. Several call
        groups finish at the same moment in different threads, so one guard
        keeps the reported percent from moving backwards.
    """

    def __init__(self, capture_id: str, report: ProgressReport, groups: Sequence[str], tier: int) -> None:
        """Build the ledger of one capture.

        Args:
            capture_id: The identifier of the capture.
            report: The callable that writes one progress change.
            groups: Every call group name that this capture runs.
            tier: The data tier, which fixes the skipped rows.
        """
        self._capture_id = capture_id  # The progress record that this ledger writes.
        self._report = report  # The one writer of the progress record.
        self._rows = starting_rows(tier)  # One state for each of the six rows.
        self._groups: dict[str, str] = dict.fromkeys(groups, "")  # An empty value means the group still runs.
        self._guard = threading.Lock()  # Four worker threads report through this ledger.

    def rows(self) -> dict[str, str]:
        """Read a copy of the section map.

        Returns:
            One state for each of the six rows.
        """
        with self._guard:  # A worker thread writes the same map.
            return dict(self._rows)  # A copy, so no caller writes the ledger.

    def finish(self, group: str, state: str) -> None:
        """Record the outcome of one call group and report the new progress.

        Why:
            The worker thread of each group calls this the moment its read
            ends, so the bar moves while the wave still runs.

        Args:
            group: The call group name.
            state: The outcome ``done`` or ``failed``.
        """
        with self._guard:  # The report stays under the guard, so no percent arrives out of order.
            self._groups[group] = state  # Record the outcome of this one group.
            self._refresh()  # Every row that this group feeds reads the new outcome.
            self._publish({"percent": self._percent()})  # The bar moves one step.
        logger.info("capture collector: the call group %s ended as %s", group, state)

    def mark(self, row: str, state: str) -> None:
        """Write one row state and report the new section map.

        Args:
            row: The row name.
            state: The new state of that row.
        """
        with self._guard:  # The poll reads this map from another thread.
            self._rows[row] = state  # A refinement that no group outcome carries.
            self._publish({})  # The map alone, because the percent did not change.
        logger.info("capture collector: the row %s reads %s", row, state)

    def reconcile(self, results: Mapping[str, Any]) -> None:
        """Set the final outcome of every call group that one wave reported.

        Why:
            A group that the pool loses never reaches its own worker, so its
            row would stay pending for ever. ``run_call_groups`` reports every
            group, with a reason for each loss, so this pass settles them all.

        Args:
            results: The group results of one wave.
        """
        for name, result in results.items():  # Every group of the wave appears here, lost or not.
            self.finish(name, STATE_FAILED if result.reasons else STATE_DONE)  # A reason marks a loss.

    def _publish(self, changes: dict[str, Any]) -> None:
        """Send the section map and the named changes to the progress record.

        Args:
            changes: The fields to write beside the section map.
        """
        changes["sections"] = dict(self._rows)  # The poll always carries the whole map.
        self._report(self._capture_id, changes)  # The one writer of the progress record.

    def _refresh(self) -> None:
        """Set each row from the outcome of every call group that feeds it."""
        for row, sources in ROW_SOURCES.items():  # Six rows and five groups.
            if self._rows.get(row) == STATE_SKIPPED:  # This tier never reads the row.
                continue
            self._rows[row] = fold_states([self._groups.get(name, "") for name in sources])

    def _percent(self) -> int:
        """Report the read progress as a whole percent.

        Returns:
            A percent between the read floor and the read ceiling.
        """
        finished = sum(1 for state in self._groups.values() if state)  # An empty value still runs.
        span = READ_CEILING - READ_FLOOR  # The reads own the wide middle of the bar.
        return READ_FLOOR + round(span * finished / max(1, len(self._groups)))  # Never a division by zero.


# ---------------------------------------------------------------------------
# The reads, the store, and the reporter
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class SiteReads:
    """The five site reads of one capture.

    Why:
        A unit test must open no socket, so every cloud read arrives through
        one holder. A test builds this record from its own callables, and the
        collector then reaches no network.

    Attributes:
        devices: Reads the inventory and the device statistics of one site.
        wired: Reads the wired clients and the guest clients of one site.
        wireless_stats: Reads the wireless client statistics rows.
        wireless_search: Reads the wireless client search rows.
        extras: Reads every tier 3 section of one site.
    """

    devices: DeviceCall
    wired: ClientCall
    wireless_stats: RowCall
    wireless_search: RowCall
    extras: ExtraCall


def read_devices(session: Any, org_id: str, site_id: str) -> tuple[devices.DeviceRead, devices.DeviceRead]:
    """Read the inventory and then the device statistics of one site.

    Why:
        Both calls page with a cursor, so they stay in order inside one call
        group. The parallel work happens between the groups, never inside one.

    Args:
        session: The cloud session.
        org_id: The organization that owns the site.
        site_id: The site to read.

    Returns:
        The inventory read and the statistics read, in that order.
    """
    inventory, statistics = assembly.sequential_reads(
        [
            lambda: devices.read_inventory(session, org_id, site_id),
            lambda: devices.read_device_statistics(session, site_id),
        ]
    )
    return inventory, statistics


def read_clients(session: Any, site_id: str) -> tuple[Any, Any]:
    """Read the wired clients and then the guest clients of one site.

    Why:
        ``assembly.CALL_GROUPS`` rides the guest read inside the wired group,
        because both calls are small and the cloud call budget is shared.

    Args:
        session: The cloud session.
        site_id: The site to read.

    Returns:
        The wired records and the guest records, in that order.
    """
    wired, guest = assembly.sequential_reads(
        [lambda: clients.read_wired_clients(session, site_id), lambda: clients.read_guest_clients(session, site_id)]
    )
    return wired, guest


def read_extras(session: Any, scope: extras.SiteScope, device_stats: Any) -> dict[str, extras.ExtraSection]:
    """Read every tier 3 section of one site.

    Why:
        The radio section reads the tier 2 device statistics rather than
        calling the cloud again, so this read waits for the device group. The
        shared port read runs inside this group as well, because
        ``collect_extras`` owns it and derives two sections from it.

    Args:
        session: The cloud session.
        scope: The organization and the site to read.
        device_stats: The device statistics rows of the same capture.

    Returns:
        One section for each name of ``extras.SECTION_NAMES``.
    """
    payload = extras.SourcePayloads(device_stats=device_stats)  # The radio section reads this instead of the cloud.
    return extras.collect_extras(session, scope, payload)


def default_reads() -> SiteReads:
    """Return the five reads that reach the real cloud.

    Returns:
        The read holder that the portal uses in production.
    """
    return SiteReads(
        devices=read_devices,
        wired=read_clients,
        wireless_stats=clients.fetch_wireless_stats_rows,
        wireless_search=clients.fetch_wireless_search_rows,
        extras=read_extras,
    )


@dataclass(frozen=True, slots=True)
class CaptureStore:
    """The write and the read-back of one capture.

    Why:
        A unit test must touch no database. Both store calls arrive through
        this holder, so a test builds it from its own callables.

    Attributes:
        write: Writes one capture document and reports the outcome.
        read_back: Reads one stored capture by identifier.
    """

    write: WriteCall
    read_back: LoadCall


def _write_capture(document: Mapping[str, Any]) -> Any:
    """Write one capture document through the real store.

    Why:
        ``capture/store.py`` imports the database driver and the exporter at
        load time, so the import stays inside this function. A test that
        supplies its own store then never loads the driver at all.

    Args:
        document: The capture document.

    Returns:
        The store result.
    """
    from src.upgrade_portal.capture import store  # Late import. The store pulls the database driver.

    return store.write_capture(document)


def _load_capture(capture_id: str) -> Any:
    """Read one stored capture through the real store.

    Args:
        capture_id: The identifier of the capture.

    Returns:
        The load result of the store.
    """
    from src.upgrade_portal.capture import store  # Late import. The store pulls the database driver.

    return store.load_capture(capture_id)


def default_store() -> CaptureStore:
    """Return the store calls that reach the real database.

    Returns:
        The store holder that the portal uses in production.
    """
    return CaptureStore(write=_write_capture, read_back=_load_capture)


def report_to_routes(capture_id: str, changes: Mapping[str, Any]) -> None:
    """Write one progress change into the progress store of the capture routes.

    Why:
        The progress store lives beside the routes, because the poll reads it.
        The import stays inside this function, so this module never depends on
        Flask and a unit test drives the collector with its own reporter.

    Args:
        capture_id: The identifier of the capture.
        changes: The fields to write.
    """
    from src.upgrade_portal.app.routes.capture import record_status  # Late import. Keeps Flask out of load time.

    record_status(capture_id, **changes)


def default_report() -> ProgressReport:
    """Return the reporter that writes into the capture routes.

    Returns:
        The reporter that the portal uses in production.
    """
    return report_to_routes


@dataclass(frozen=True, slots=True)
class CaptureResources:
    """Everything that one capture needs beside the job.

    Why:
        The worker thread holds no request, so nothing here can come out of
        Flask. A test builds this record from fakes, and the collector then
        opens no socket and touches no database.

    Attributes:
        session: The cloud session. None asks this module to resolve one.
        reads: The five site reads.
        store: The write and the read-back.
        report: The progress reporter.
        executor: The call group runner. None uses ``CapturePool``.
    """

    session: Any = None
    reads: SiteReads = field(default_factory=default_reads)
    store: CaptureStore = field(default_factory=default_store)
    report: ProgressReport = field(default_factory=default_report)
    executor: assembly.GroupExecutor | None = None


def resolve_session(job: Mapping[str, Any], kit: CaptureResources) -> Any:
    """Find the cloud session that one capture reads with.

    Why:
        ``runtime/identity.py`` reads the Flask session, so it answers nothing
        inside a worker thread. The start route therefore reads the session on
        the request thread and carries it in the job. This function takes the
        session from the resources, then from the job, then from the module
        provider, and names the gap when all three are empty.

    Args:
        job: The capture job.
        kit: The resources of this capture.

    Returns:
        The cloud session, or None when no source holds one.
    """
    if kit.session is not None:  # A test and a caller that already signed in both land here.
        return kit.session
    carried = job.get("cloud_session")  # The start route puts the signed-in session here.
    if carried is not None:
        return carried
    if SESSION_PROVIDER is not None:  # The process may hold one provider for every capture.
        return SESSION_PROVIDER(job)
    return None  # The caller names the gap and marks the capture failed.


# ---------------------------------------------------------------------------
# The call groups
# ---------------------------------------------------------------------------


def run_watched(name: str, work: Callable[[], Any], ledger: ProgressLedger) -> Any:
    """Run one read and tell the ledger how it ended.

    Args:
        name: The call group name.
        work: The read of that group.
        ledger: The progress ledger of this capture.

    Returns:
        The value of the read.

    Raises:
        Exception: Whatever the read raised. The caller owns the reason.
    """
    try:  # The read reaches a network, so it may raise.
        value = work()
    except Exception:  # `assembly.guarded_call` still records the partial reason.
        ledger.finish(name, STATE_FAILED)  # The row turns red at once.
        raise  # The caller of this group owns the reason.
    ledger.finish(name, STATE_DONE)  # The row turns green at once.
    return value


def watched(name: str, work: Callable[[], Any], ledger: ProgressLedger) -> assembly.CallGroup:
    """Wrap one read, so the ledger reports the outcome the moment it ends.

    Why:
        ``run_call_groups`` returns only when a whole wave ends. A bar that
        moved only then would jump. This wrapper reports from inside the
        worker thread, so the bar moves while the wave still runs.

    Args:
        name: The call group name.
        work: The read of that group.
        ledger: The progress ledger of this capture.

    Returns:
        The call group.
    """
    return assembly.CallGroup(name, functools.partial(run_watched, name, work, ledger))


def wave_names(tier: int) -> tuple[str, ...]:
    """Name every call group that one tier runs.

    Args:
        tier: The data tier of the capture.

    Returns:
        The group names of both waves.
    """
    names = (
        assembly.GROUP_DEVICES,
        assembly.GROUP_WIRED_CLIENTS,
        assembly.GROUP_WIRELESS_STATISTICS,
        assembly.GROUP_WIRELESS_SEARCH,
    )
    return (names + (assembly.GROUP_TIER_THREE,)) if tier >= TIER_EXTRA else names


def wave_one(session: Any, scope: extras.SiteScope, reads: SiteReads, ledger: ProgressLedger) -> list[Any]:
    """Build the four call groups that every tier reads.

    Why:
        Four groups match the four capture workers of ``runtime/pools.py``, so
        one wave fills the pool exactly one time.

    Args:
        session: The cloud session.
        scope: The organization and the site to read.
        reads: The five site reads.
        ledger: The progress ledger of this capture.

    Returns:
        The call groups of wave one.
    """
    return [
        watched(assembly.GROUP_DEVICES, lambda: reads.devices(session, scope.org_id, scope.site_id), ledger),
        watched(assembly.GROUP_WIRED_CLIENTS, lambda: reads.wired(session, scope.site_id), ledger),
        watched(assembly.GROUP_WIRELESS_STATISTICS, lambda: reads.wireless_stats(session, scope.site_id), ledger),
        watched(assembly.GROUP_WIRELESS_SEARCH, lambda: reads.wireless_search(session, scope.site_id), ledger),
    ]


def wave_two(session: Any, scope: extras.SiteScope, reads: SiteReads, ledger: ProgressLedger, rows: Any) -> list[Any]:
    """Build the one call group that only tier 3 reads.

    Why:
        The radio section reads the device statistics of wave one, so this
        group cannot join that wave.

    Args:
        session: The cloud session.
        scope: The organization and the site to read.
        reads: The five site reads.
        ledger: The progress ledger of this capture.
        rows: The device statistics rows of wave one.

    Returns:
        The call groups of wave two.
    """
    return [watched(assembly.GROUP_TIER_THREE, lambda: reads.extras(session, scope, rows), ledger)]


def statistics_rows(results: Mapping[str, Any]) -> list[dict[str, Any]] | None:
    """Return the device statistics rows that the radio section needs.

    Args:
        results: The group results of wave one.

    Returns:
        The statistics rows, or None when the device group did not finish.
    """
    pair = assembly.group_value(results, assembly.GROUP_DEVICES)  # The inventory read and the statistics read.
    if pair is None:  # The device group failed, so the radio section reports an absent source.
        return None
    return [dict(row) for row in pair[1].records]


def run_reads(job: Mapping[str, Any], session: Any, kit: CaptureResources, ledger: ProgressLedger) -> dict[str, Any]:
    """Run every call group of one capture, in two waves.

    Why:
        The tier 3 radio section reads the device statistics of wave one, so
        that group waits. Every other read still runs at the same time.

    Args:
        job: The capture job.
        session: The cloud session.
        kit: The resources of this capture.
        ledger: The progress ledger of this capture.

    Returns:
        One result for each call group, by name.
    """
    scope = extras.SiteScope(org_id=str(job.get("org_id", "")), site_id=str(job.get("site_id", "")))
    results = dict(assembly.run_call_groups(wave_one(session, scope, kit.reads, ledger), kit.executor))
    ledger.reconcile(results)  # A group that the pool lost settles here.
    if int(job.get("tier", TIER_STANDARD)) < TIER_EXTRA:  # Tier 2 reads no extra section.
        return results
    groups = wave_two(session, scope, kit.reads, ledger, statistics_rows(results))
    later = dict(assembly.run_call_groups(groups, kit.executor))
    ledger.reconcile(later)  # The tier 3 group settles here.
    return results | later  # The later wave wins no key, because the two waves share none.


# ---------------------------------------------------------------------------
# The document
# ---------------------------------------------------------------------------


def device_reads(results: Mapping[str, Any]) -> tuple[Any, Any]:
    """Return the inventory read and the statistics read of one capture.

    Args:
        results: The group results of one capture.

    Returns:
        Both reads, or two None values when the device group failed.
    """
    pair = assembly.group_value(results, assembly.GROUP_DEVICES)  # None after a lost group.
    if pair is None:
        return None, None
    return pair[0], pair[1]


def device_index_of(inventory: Any, statistics: Any) -> dict[str, dict[str, Any]]:
    """Build the device index out of both device reads.

    Args:
        inventory: The inventory read, or None.
        statistics: The statistics read, or None.

    Returns:
        One index entry for each device address.
    """
    if inventory is None:  # No inventory means no index and no device rows.
        return {}
    rows = list(statistics.records) if statistics is not None else []  # A lost statistics read still leaves an index.
    return devices.build_device_index(inventory.records, rows)


def device_rows(inventory: Any) -> list[dict[str, Any]]:
    """Return the device records that the index also holds.

    Why:
        Validation rule 7 asks the index and the device list to hold the same
        members. ``build_device_index`` drops a record with no address, so
        this filter drops the same records and the rule then holds.

    Args:
        inventory: The inventory read, or None.

    Returns:
        One row for each device that carries an address.
    """
    if inventory is None:
        return []
    return [dict(record) for record in inventory.records if devices.normalize_device_mac(record.get("mac"))]


def device_reasons(inventory: Any, statistics: Any) -> list[dict[str, Any]]:
    """Collect every reason that the two device reads report.

    Why:
        The statistics call answers with access points alone when the caller
        omits the type, and the cloud reports no error.
        ``guard_statistics_coverage`` names a lost device type, so a capture
        that lost every switch reports the loss instead of looking complete.

    Args:
        inventory: The inventory read, or None.
        statistics: The statistics read, or None.

    Returns:
        One reason for each fault that the device reads found.
    """
    if inventory is None:  # `assembly.group_reasons` already named the lost group.
        return []
    rows = list(statistics.records) if statistics is not None else []
    reasons = list(inventory.partial_reasons)
    reasons.extend(statistics.partial_reasons if statistics is not None else [])
    reasons.extend(devices.guard_statistics_coverage(inventory.records, rows))
    return reasons


def already_read_rows(rows: Any, session: Any, site_id: str) -> list[dict[str, Any]]:
    """Answer with the rows that a call group already read.

    Why:
        The two wireless call groups run at the same time and each returns raw
        rows. ``clients.read_wireless_clients`` owns the join of those two
        reads, so a bound copy of this function hands it the rows it holds and
        the reader then makes no further call.

    Args:
        rows: The rows that a call group already read.
        session: Unused. The read already ran.
        site_id: Unused. The read already ran.

    Returns:
        A copy of those rows.
    """
    del session, site_id  # The read already ran, so neither value is used.
    return [dict(row) for row in rows or ()]


def wireless_records(results: Mapping[str, Any]) -> list[Any]:
    """Join the two wireless reads into one client list.

    Why:
        Neither wireless call holds every field. The statistics call holds the
        signal strength and the search call holds the randomized-address flag,
        so the two groups read at the same time and this step joins them.

    Args:
        results: The group results of one capture.

    Returns:
        One record for each address in either read.
    """
    stats = assembly.group_value(results, assembly.GROUP_WIRELESS_STATISTICS, [])  # Empty after a lost group.
    search = assembly.group_value(results, assembly.GROUP_WIRELESS_SEARCH, [])  # Empty after a lost group.
    return clients.read_wireless_clients(  # Both sources are bound rows, so the reader calls no cloud.
        None, "", functools.partial(already_read_rows, stats), functools.partial(already_read_rows, search)
    )


def client_rows(results: Mapping[str, Any], index: Mapping[str, Mapping[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Build the three client lists with the serving device named.

    Why:
        The client reads leave ``device_name`` empty, because the client calls
        answer with an address alone. The moved-client report shows a name, so
        every list passes through ``fill_device_names``.

    Args:
        results: The group results of one capture.
        index: The device index of the same capture.

    Returns:
        One flat row list for each name of ``assembly.CLIENT_GROUPS``.
    """
    wired, guest = assembly.group_value(results, assembly.GROUP_WIRED_CLIENTS, ([], []))  # Both after one group.
    return {
        "wired": assembly.fill_device_names(wired, index),
        "wireless": assembly.fill_device_names(wireless_records(results), index),
        "guest": assembly.fill_device_names(guest, index),
    }


def extra_records(results: Mapping[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Flatten the tier 3 sections into the map that the document holds.

    Args:
        results: The group results of one capture.

    Returns:
        One list for each tier 3 section name. The lists are empty when the
        group failed, so the document still holds every name.
    """
    sections = assembly.group_value(results, assembly.GROUP_TIER_THREE)  # None after a lost group.
    if sections is None:
        return dict.fromkeys(extras.SECTION_NAMES, [])
    return extras.section_records(sections)


def extra_reasons_of(results: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Name each tier 3 section whose read did not finish.

    Args:
        results: The group results of one capture.

    Returns:
        One reason for each failed tier 3 section, named after that section.
    """
    sections = assembly.group_value(results, assembly.GROUP_TIER_THREE)  # None after a lost group.
    if sections is None:
        return []
    return assembly.extra_reasons(sections)


def refine_extra_rows(results: Mapping[str, Any], ledger: ProgressLedger) -> None:
    """Set the extras row and the alarms row from the tier 3 read.

    Why:
        The progress body holds six rows and the stored document holds five
        digest sections, because ``data-model.md`` section 3.5 keeps the
        alarms inside the extras. The alarms row therefore reads the alarm
        sub-read of the tier 3 group. This is the same rule that
        ``app/routes/capture.py`` applies to a stored capture, where a partial
        reason named ``alarms`` paints that row red.

    Args:
        results: The group results of one capture.
        ledger: The progress ledger of this capture.
    """
    sections = assembly.group_value(results, assembly.GROUP_TIER_THREE)  # None at tier 2 and after a lost group.
    if sections is None:
        return
    failed = {section.name for section in extras.failed_sections(sections)}  # The sub-reads that did not finish.
    ledger.mark(ROW_ALARMS, STATE_FAILED if extras.SECTION_ALARMS in failed else STATE_DONE)
    ledger.mark(ROW_EXTRAS, STATE_FAILED if failed - {extras.SECTION_ALARMS} else STATE_DONE)


def build_sections(results: Mapping[str, Any], tier: int) -> assembly.CaptureSections:
    """Turn the call group results into the sections of one capture.

    Args:
        results: The group results of one capture.
        tier: The data tier of the capture.

    Returns:
        The device index, the device rows, the client lists, and the extras.
    """
    inventory, statistics = device_reads(results)
    index = device_index_of(inventory, statistics)
    return assembly.CaptureSections(
        device_index=index,
        devices=device_rows(inventory),
        clients=client_rows(results, index),
        extras=extra_records(results) if tier >= TIER_EXTRA else None,  # None marks a tier 2 capture.
    )


def row_reasons(reason: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Rewrite one failure reason, so its section names a report row.

    Why:
        The capture page paints a row red when a partial reason carries that
        row name. A reason that carried a call group name or a sub-read name
        would paint nothing, and a reloaded page would show a green row over a
        section that the capture never read. The first name moves to the
        ``source`` field, so the document still names the exact read that
        failed. Validation rule 5 asks for three fields at the least, so the
        extra field breaks no rule.

    Args:
        reason: One partial reason.

    Returns:
        One reason for each report row that this failure covers.
    """
    section = str(reason.get("section", ""))
    rows = REASON_ROWS.get(section, (section,))  # An unknown name keeps itself.
    return [dict(reason, section=row, **{REASON_SOURCE_FIELD: section}) for row in rows]


def collect_reasons(results: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Gather every partial reason of one capture, named by report row.

    Why:
        A failed section never stops the capture. Each reason names its own
        row, so the stored document paints the same rows that the live poll
        painted, and a reader still sees every section that arrived.

    Args:
        results: The group results of one capture.

    Returns:
        One reason for each failure, named by report row.
    """
    inventory, statistics = device_reads(results)
    raw = list(assembly.group_reasons(results))  # One reason for each group that raised or was lost.
    raw.extend(device_reasons(inventory, statistics))  # A short read and a lost device type.
    raw.extend(extra_reasons_of(results))  # One reason for each failed tier 3 sub-read.
    reasons = [named for entry in raw for named in row_reasons(entry)]
    logger.info("capture collector: the capture holds %s partial reasons", len(reasons))
    return reasons


def capture_identity(job: Mapping[str, Any]) -> assembly.CaptureIdentity:
    """Build the run identity of one capture.

    Why:
        ``assembly.capture_key`` builds the capture key from the run alone. An
        empty run therefore builds the key ``cap--01``, and a second empty run
        overwrites the first record. A placeholder key collides the same way.

    Args:
        job: The capture job.

    Returns:
        The run, the ordinal, and the operator.

    Raises:
        ValueError: If the job names no run.
    """
    run_id = str(job.get("run_id", "")).strip()  # A blank value names no run.
    if not run_id:  # An empty run reaches the key of every other empty run.
        raise ValueError(MISSING_RUN_MESSAGE)  # The route marks the capture failed.
    return assembly.CaptureIdentity(
        run_id=run_id,  # The guard above proved this value.
        ordinal=int(job.get("ordinal", assembly.FIRST_ORDINAL)),
        actor_email=str(job.get("actor_email", "")),
    )


def site_identity(job: Mapping[str, Any]) -> assembly.SiteIdentity:
    """Build the site identity of one capture.

    Why:
        The start route reads the organization name and the site name on the
        request thread and carries both in the job, because a worker thread
        holds no request. A job that a caller builds by hand may hold neither
        name. Each read therefore falls back to an empty value. A reader of the
        stored capture then shows an identifier in place of a name.

    Args:
        job: The capture job.

    Returns:
        The organization and the site.
    """
    return assembly.SiteIdentity(
        org_id=str(job.get("org_id", "")),
        org_name=str(job.get("org_name", "")),
        site_id=str(job.get("site_id", "")),
        site_name=str(job.get("site_name", "")),
    )


def report_counts(capture_id: str, document: Mapping[str, Any], kit: CaptureResources) -> None:
    """Send the counts and the reasons of one capture to the progress record.

    Why:
        The status body carries both, so the operator reads the device total
        and every partial reason before the write ends.

    Args:
        capture_id: The identifier of the capture.
        document: The capture document.
        kit: The resources of this capture.
    """
    counts = dict(document.get("counts") or {})
    kit.report(capture_id, {"counts": counts, "partial_reasons": list(document.get("partial_reasons") or [])})
    logger.info("capture collector: the capture %s holds %s device records", capture_id, counts.get("devices_total"))


def warn_broken_rules(capture_id: str, document: Mapping[str, Any]) -> None:
    """Log every validation rule that the assembled document breaks.

    Why:
        A broken rule never stops the write, because a stored partial capture
        is worth more than no capture at all. The log names the rule, so an
        operator can see why a comparison later refuses the record.

    Args:
        capture_id: The identifier of the capture.
        document: The capture document.
    """
    broken = assembly.validate_capture(document)
    if broken:  # An empty list is the common case.
        logger.warning("capture collector: the capture %s breaks the rules %s", capture_id, ", ".join(broken))


def build_document(job: Mapping[str, Any], session: Any, kit: CaptureResources) -> dict[str, Any]:
    """Read every section of one site and assemble the capture document.

    Args:
        job: The capture job.
        session: The cloud session.
        kit: The resources of this capture.

    Returns:
        The capture document.
    """
    capture_id = str(job.get("capture_id", ""))
    tier = int(job.get("tier", TIER_STANDARD))
    ledger = ProgressLedger(capture_id, kit.report, wave_names(tier), tier)
    kit.report(capture_id, {"state": CAPTURE_COLLECTING, "percent": READ_FLOOR, "message": COLLECTING_MESSAGE})
    timer = assembly.CaptureTimer()  # The window starts before the first read.
    results = run_reads(job, session, kit, ledger)
    refine_extra_rows(results, ledger)  # The alarms row reads the alarm sub-read.
    sections = build_sections(results, tier)
    reasons = collect_reasons(results)
    kit.report(capture_id, {"percent": ASSEMBLE_PERCENT, "message": ASSEMBLE_MESSAGE})
    document = assembly.build_capture(capture_identity(job), site_identity(job), timer.finish(), sections, reasons)
    report_counts(capture_id, document, kit)
    warn_broken_rules(capture_id, document)
    return document


# ---------------------------------------------------------------------------
# The store step
# ---------------------------------------------------------------------------


def progress_change(document: Mapping[str, Any], result: Any, verified: bool, message: str) -> dict[str, Any]:
    """Build the last progress change of one capture.

    Args:
        document: The capture document.
        result: The store result.
        verified: True only after a matching read-back.
        message: One sentence for the operator.

    Returns:
        The fields to write into the progress record.
    """
    return {
        "state": CAPTURE_VERIFIED if verified else CAPTURE_FAILED,
        "percent": WHOLE_PERCENT,
        "verified": verified,
        "message": message,
        "counts": dict(document.get("counts") or {}),
        "partial_reasons": list(document.get("partial_reasons") or []),
        "stored_size_bytes": result.stored_size_bytes,  # FR-032b. Retention has no end, so the size matters.
    }


def verified_message(document: Mapping[str, Any]) -> str:
    """Choose the sentence for a stored capture.

    Args:
        document: The capture document.

    Returns:
        The sentence for the operator.
    """
    return PARTIAL_MESSAGE if document.get("partial_reasons") else VERIFIED_MESSAGE


def stop_after_store(
    capture_id: str, document: Mapping[str, Any], result: Any, message: str, kit: CaptureResources
) -> None:
    """Report one capture that reached no verified record, and log the cause.

    Args:
        capture_id: The identifier of the capture.
        document: The capture document.
        result: The store result, which also names the refusal.
        message: One sentence for the operator.
        kit: The resources of this capture.
    """
    logger.error(
        "capture collector: the capture %s reached no stored record: %s (%s)", capture_id, message, result.reason
    )
    kit.report(capture_id, progress_change(document, result, False, message))


def store_capture(capture_id: str, document: Mapping[str, Any], kit: CaptureResources) -> None:
    """Write one capture, read the key back, and report the outcome.

    Why:
        A write result alone proves nothing, so the portal reads the key back
        and only then reports the capture verified.
        ``contracts/http-api.md`` answers 409 ``capture_not_verified`` for a
        capture that fails this step, so the flag must never rest on the write.

    Args:
        capture_id: The identifier that the progress record carries.
        document: The capture document.
        kit: The resources of this capture.
    """
    kit.report(capture_id, {"percent": WRITE_PERCENT, "message": WRITE_MESSAGE})
    result = kit.store.write(document)
    if not result.verified:  # The store refused the write, or its own read-back failed.
        stop_after_store(capture_id, document, result, WRITE_FAILED_MESSAGE, kit)
        return
    load = kit.store.read_back(str(document.get("capture_id", "")))  # A second, independent proof.
    if not load.comparable:  # The key came back, but the record is not fit to compare.
        stop_after_store(capture_id, document, result, READ_BACK_MESSAGE, kit)
        return
    kit.report(capture_id, progress_change(document, result, True, verified_message(document)))
    logger.info("capture collector: the capture %s is verified at %s bytes", capture_id, result.stored_size_bytes)


def run_capture(job: Mapping[str, Any], resources: CaptureResources | None = None) -> None:
    """Read one whole site and store one capture document.

    Why:
        ``app/routes/capture.py`` calls this function with one job on a worker
        thread. That caller catches every exception and marks the capture
        failed, so a fault never leaves the page waiting for ever.

    Args:
        job: The capture job that the start route built.
        resources: The reads, the store, the reporter, and the call group
            runner. None builds the production set.
    """
    kit = resources if resources is not None else CaptureResources()
    capture_id = str(job.get("capture_id", ""))
    session = resolve_session(job, kit)
    if session is None:  # No session means no read at all, so the capture stops here.
        logger.error("capture collector: the capture %s holds no cloud session", capture_id)
        kit.report(capture_id, {"state": CAPTURE_FAILED, "percent": WHOLE_PERCENT, "message": NO_SESSION_MESSAGE})
        return
    logger.info("capture collector: the capture %s starts at tier %s", capture_id, job.get("tier"))
    store_capture(capture_id, build_document(job, session, kit), kit)
    logger.debug("capture collector: the capture %s ended", capture_id)


__all__ = [
    "ASSEMBLE_PERCENT",
    "CAPTURE_COLLECTING",
    "CAPTURE_FAILED",
    "CAPTURE_VERIFIED",
    "EXTRA_ROWS",
    "NO_SESSION_MESSAGE",
    "PARTIAL_MESSAGE",
    "READ_BACK_MESSAGE",
    "READ_CEILING",
    "READ_FLOOR",
    "REASON_ROWS",
    "REASON_SOURCE_FIELD",
    "ROW_ALARMS",
    "ROW_DEVICES",
    "ROW_EXTRAS",
    "ROW_GUEST",
    "ROW_NAMES",
    "ROW_SOURCES",
    "ROW_WIRED",
    "ROW_WIRELESS",
    "SESSION_PROVIDER",
    "STATE_DONE",
    "STATE_FAILED",
    "STATE_PENDING",
    "STATE_SKIPPED",
    "TIER_EXTRA",
    "TIER_STANDARD",
    "VERIFIED_MESSAGE",
    "WHOLE_PERCENT",
    "WRITE_FAILED_MESSAGE",
    "WRITE_PERCENT",
    "CaptureResources",
    "CaptureStore",
    "ProgressLedger",
    "ProgressReport",
    "SessionProvider",
    "SiteReads",
    "already_read_rows",
    "build_document",
    "build_sections",
    "client_rows",
    "collect_reasons",
    "default_reads",
    "default_report",
    "default_store",
    "fold_states",
    "read_clients",
    "read_devices",
    "read_extras",
    "refine_extra_rows",
    "report_to_routes",
    "resolve_session",
    "row_reasons",
    "run_capture",
    "run_reads",
    "run_watched",
    "starting_rows",
    "statistics_rows",
    "stop_after_store",
    "store_capture",
    "wave_names",
    "wave_one",
    "wave_two",
    "watched",
    "wireless_records",
]
