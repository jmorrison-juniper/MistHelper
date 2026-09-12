"""Unit tests for the capture collector.

Why:
    The collector is the one place where the reads, the assembler, and the
    store meet. A fault here records a failed capture for a whole site, so
    every path needs a test. No test here opens a socket and no test here
    reaches a database. Every read and both store calls arrive as a fake.
"""

from __future__ import annotations  # Every annotation stays text, so a name may appear before its class.

import threading  # The fake executor hands each worker a real semaphore.
from collections.abc import Mapping, Sequence  # The shapes that the collector reads.
from dataclasses import dataclass, field  # The store fakes of this module.
from typing import Any  # A session, a store result, and a document are all free-form.

import pytest  # The parameter table of the fold test.

from src.upgrade_portal.capture import assembly, clients, collector, devices, extras  # The collector and its parts.
from src.upgrade_portal.runtime import pools  # The worker target that wave one matches.

CAPTURE_ID = "cap-0123456789abcdef-01"  # The identifier of the fake capture.
RUN_ID = "run-0123456789abcdef"  # The owning run of the fake capture.
ORG_ID = "11111111-1111-1111-1111-111111111111"  # The fake organization.
SITE_ID = "22222222-2222-2222-2222-222222222222"  # The fake site.
ORG_NAME = "Fake Organization"  # The readable name that the start route carries in the job.
SITE_NAME = "Fake Campus"  # The readable name that the start route carries in the job.
SWITCH_MAC = "5c5b350e0001"  # The one switch of the fake site.
ACCESS_POINT_MAC = "5c5b350e0002"  # The one access point of the fake site.
WIRED_CLIENT_MAC = "aabbccddee01"  # The one wired client.
WIRELESS_CLIENT_MAC = "aabbccddee02"  # The one wireless client, in both wireless reads.
GUEST_CLIENT_MAC = "aabbccddee03"  # The one guest client.
READ_FAULT = "The fake read stopped on purpose."  # The message of every lost read.


# ---------------------------------------------------------------------------
# The fakes
# ---------------------------------------------------------------------------


class Recorder:
    """Collects every progress change that the collector reports.

    Why:
        The browser reads the progress record, so a test must read the same
        changes in the same order. This recorder keeps each change on its own,
        which lets a test read the percent sequence as well as the last state.
    """

    def __init__(self) -> None:
        """Start with no change."""
        self.changes: list[dict[str, Any]] = []

    def __call__(self, capture_id: str, changes: Mapping[str, Any]) -> None:
        """Record one progress change.

        Args:
            capture_id: The identifier of the capture.
            changes: The fields that the collector wrote.
        """
        self.changes.append({"capture_id": capture_id, **dict(changes)})

    def merged(self) -> dict[str, Any]:
        """Fold every change into the record that the poll would answer with.

        Returns:
            The last value of each field.
        """
        record: dict[str, Any] = {}
        for change in self.changes:
            record.update(change)
        return record

    def percents(self) -> list[int]:
        """List the reported percent of each change that carried one.

        Returns:
            The percent sequence, in report order.
        """
        return [int(change["percent"]) for change in self.changes if "percent" in change]

    def rows(self) -> dict[str, str]:
        """Read the last section map that the collector reported.

        Returns:
            One state for each of the six rows.
        """
        return dict(self.merged().get("sections") or {})


@dataclass(frozen=True, slots=True)
class FakeStoreResult:
    """Stands in for ``store.StoreResult``.

    Attributes:
        verified: True when the store wrote the record and read it back.
        reason: Names the refusal. Empty after a verified write.
        stored_size_bytes: The measured size of the stored record.
    """

    verified: bool = True
    reason: str = ""
    stored_size_bytes: int = 4096


@dataclass(frozen=True, slots=True)
class FakeCaptureLoad:
    """Stands in for ``store.CaptureLoad``.

    Attributes:
        comparable: True when the stored record is fit for a comparison.
        reason: Names the refusal. Empty after a matching read-back.
        capture: The stored record.
    """

    comparable: bool = True
    reason: str = ""
    capture: dict[str, Any] | None = None


@dataclass
class FakeStore:
    """Records every write and every read-back of one test.

    Attributes:
        result: The answer of the write call.
        load: The answer of the read-back call.
        written: Each document that the collector wrote.
        read_keys: Each key that the collector read back.
    """

    result: FakeStoreResult = field(default_factory=FakeStoreResult)
    load: FakeCaptureLoad = field(default_factory=FakeCaptureLoad)
    written: list[dict[str, Any]] = field(default_factory=list)
    read_keys: list[str] = field(default_factory=list)

    def write(self, document: Mapping[str, Any]) -> FakeStoreResult:
        """Record one document and answer with the fixed result.

        Args:
            document: The capture document.

        Returns:
            The fixed store result.
        """
        self.written.append(dict(document))
        return self.result

    def read_back(self, capture_id: str) -> FakeCaptureLoad:
        """Record one read-back and answer with the fixed load.

        Args:
            capture_id: The identifier of the capture.

        Returns:
            The fixed load result.
        """
        self.read_keys.append(capture_id)
        return self.load

    def holder(self) -> collector.CaptureStore:
        """Return this fake in the shape that the collector expects.

        Returns:
            The store holder.
        """
        return collector.CaptureStore(write=self.write, read_back=self.read_back)


def sequential_executor(
    work_items: list[Any], worker_function: Any, batch_description: str
) -> tuple[list[Any], list[Any]]:
    """Run every call group in this thread, in order.

    Why:
        A unit test must not depend on a thread pool that reads the settings
        of the whole program. This stands in for ``CapturePool.execute`` and
        keeps the same contract: a falsy worker result counts as failed.

    Args:
        work_items: The call groups.
        worker_function: The worker that runs one call group.
        batch_description: Unused. The real pool logs it.

    Returns:
        The finished results and the lost work items.
    """
    del batch_description
    finished: list[Any] = []  # The result of each group that the worker finished.
    lost: list[Any] = []  # The work item of each group that the worker lost.
    for item in work_items:
        result = worker_function(item, threading.Semaphore(1))  # The real pool hands over a semaphore too.
        finished.append(result) if result else lost.append(item)  # A falsy result counts as lost.
    return finished, lost


@dataclass
class BatchRecorder:
    """Record the group names of each wave, then run the wave in order.

    Why:
        Two tests ask the same question of the executor seam: which groups
        entered which wave. One recorder answers both, so neither test holds
        its own copy of the executor.
    """

    batches: list[list[str]] = field(default_factory=list)  # One entry for each wave, in wave order.

    def execute(
        self, work_items: list[Any], worker_function: Any, batch_description: str
    ) -> tuple[list[Any], list[Any]]:
        """Record one wave and then run it in this thread.

        Args:
            work_items: The call groups of one wave.
            worker_function: The worker that runs one call group.
            batch_description: The description that the real pool logs.

        Returns:
            The finished results and the lost work items.
        """
        self.batches.append([item.name for item in work_items])  # The names arrive before the work runs.
        return sequential_executor(work_items, worker_function, batch_description)


# ---------------------------------------------------------------------------
# The fake reads
# ---------------------------------------------------------------------------


def inventory_rows() -> list[dict[str, Any]]:
    """Build the inventory rows of the fake site.

    Returns:
        One switch and one access point.
    """
    return [
        {"mac": SWITCH_MAC, "type": "switch", "model": "EX4400-48P", "status": "connected", "name": "idf2-sw01"},
        {"mac": ACCESS_POINT_MAC, "type": "ap", "model": "AP45", "status": "connected", "name": "idf2-ap01"},
    ]


def statistics_rows() -> list[dict[str, Any]]:
    """Build the device statistics rows of the fake site.

    Returns:
        One row for each inventory device, so no device type is lost.
    """
    return [
        {"mac": SWITCH_MAC, "type": "switch", "status": "connected", "uptime": 1832140},
        {"mac": ACCESS_POINT_MAC, "type": "ap", "status": "connected", "uptime": 91240},
    ]


def fake_devices(session: Any, org_id: str, site_id: str) -> tuple[devices.DeviceRead, devices.DeviceRead]:
    """Answer with the inventory read and the statistics read of the fake site.

    Args:
        session: Unused.
        org_id: Unused.
        site_id: Unused.

    Returns:
        Both device reads.
    """
    del session, org_id, site_id
    return (
        devices.DeviceRead(devices.SECTION_INVENTORY, inventory_rows(), []),
        devices.DeviceRead(devices.SECTION_STATISTICS, statistics_rows(), []),
    )


def fake_clients(session: Any, site_id: str) -> tuple[list[Any], list[Any]]:
    """Answer with the wired records and the guest records of the fake site.

    Args:
        session: Unused.
        site_id: Unused.

    Returns:
        One wired client and one guest client.
    """
    del session, site_id
    wired = [
        clients.ClientRecord(
            mac=WIRED_CLIENT_MAC, attachment=clients.ClientAttachment(device_mac=SWITCH_MAC, port_id="ge-0/0/1")
        )
    ]
    guest = [
        clients.ClientRecord(mac=GUEST_CLIENT_MAC, attachment=clients.ClientAttachment(device_mac=ACCESS_POINT_MAC))
    ]
    return wired, guest


def fake_wireless_stats(session: Any, site_id: str) -> list[dict[str, Any]]:
    """Answer with the wireless statistics rows of the fake site.

    Args:
        session: Unused.
        site_id: Unused.

    Returns:
        One statistics row.
    """
    del session, site_id
    return [{"mac": WIRELESS_CLIENT_MAC, "ap_mac": ACCESS_POINT_MAC, "rssi": -55, "snr": 38, "ssid": "corp"}]


def fake_wireless_search(session: Any, site_id: str) -> list[dict[str, Any]]:
    """Answer with the wireless search rows of the fake site.

    Args:
        session: Unused.
        site_id: Unused.

    Returns:
        One search row.
    """
    del session, site_id
    return [{"mac": WIRELESS_CLIENT_MAC, "random_mac": False, "last_hostname": "laptop-01"}]


def extra_sections(failed: str = "") -> dict[str, extras.ExtraSection]:
    """Build one extra section for each tier 3 name.

    Args:
        failed: The one section name that reports a failed read. Empty means
            that every section read to its end.

    Returns:
        One section for each name of ``extras.SECTION_NAMES``.
    """
    built: dict[str, extras.ExtraSection] = {}
    for name in extras.SECTION_NAMES:
        if name == failed:
            built[name] = extras.ExtraSection(name, (), extras.REASON_CALL_FAILED, 0)
        else:
            built[name] = extras.ExtraSection(name, ({"name": name},), extras.REASON_READ, 0)
    return built


def fake_extras(session: Any, scope: extras.SiteScope, device_stats: Any) -> dict[str, extras.ExtraSection]:
    """Answer with a whole set of tier 3 sections.

    Args:
        session: Unused.
        scope: Unused.
        device_stats: Unused. A real read builds the radios from these rows.

    Returns:
        One section for each tier 3 name.
    """
    del session, scope, device_stats
    return extra_sections()


def raising_read(*_arguments: Any) -> Any:
    """Stand in for a read that the cloud refused.

    Args:
        *_arguments: Unused.

    Raises:
        RuntimeError: Always. A test uses this to lose one section.
    """
    raise RuntimeError(READ_FAULT)


def build_reads(**overrides: Any) -> collector.SiteReads:
    """Build the five fake reads, with any read replaced.

    Args:
        **overrides: The reads to replace by name.

    Returns:
        The read holder.
    """
    parts: dict[str, Any] = {
        "devices": fake_devices,
        "wired": fake_clients,
        "wireless_stats": fake_wireless_stats,
        "wireless_search": fake_wireless_search,
        "extras": fake_extras,
    }
    parts.update(overrides)
    return collector.SiteReads(**parts)


def build_job(tier: int = assembly.TIER_EXTRA) -> dict[str, Any]:
    """Build the job that the start route hands to the worker.

    Why:
        The route also carries the cloud session and both readable names. Each
        of those three fields belongs to one test below, so the base job holds
        none of them and every other test reads the fallback path.

    Args:
        tier: The data tier of the capture.

    Returns:
        The seven fixed fields of one capture job and the operator address.
    """
    return {
        "capture_id": assembly.capture_key(RUN_ID, assembly.FIRST_ORDINAL),
        "run_id": RUN_ID,
        "ordinal": assembly.FIRST_ORDINAL,
        "role": "pre",
        "org_id": ORG_ID,
        "site_id": SITE_ID,
        "tier": tier,
        "actor_email": "operator@example.com",
    }


def run_one(
    tier: int = assembly.TIER_EXTRA,
    reads: collector.SiteReads | None = None,
    store: FakeStore | None = None,
    executor: Any = sequential_executor,
) -> tuple[Recorder, FakeStore]:
    """Run one whole capture against fakes.

    Args:
        tier: The data tier of the capture.
        reads: The five reads. None builds the clean set.
        store: The store. None builds a store that verifies.
        executor: The call group runner.

    Returns:
        The progress recorder and the store.
    """
    recorder = Recorder()  # Holds every progress change in the order the collector reported it.
    fake_store = store if store is not None else FakeStore()  # A store that verifies by default.
    site_reads = reads if reads is not None else build_reads()  # The clean read set by default.
    resources = collector.CaptureResources(
        session=object(), reads=site_reads, store=fake_store.holder(), report=recorder, executor=executor
    )
    collector.run_capture(build_job(tier), resources)  # Opens no socket and reaches no database.
    return recorder, fake_store


# ---------------------------------------------------------------------------
# A clean capture
# ---------------------------------------------------------------------------


def test_a_clean_capture_stores_one_verified_document() -> None:
    """A capture whose reads all pass ends verified and stores one document."""
    recorder, store = run_one()
    record = recorder.merged()
    outcome = (record["state"], record["verified"], record["percent"])  # The three fields the page reads.
    assert outcome == (collector.CAPTURE_VERIFIED, True, collector.WHOLE_PERCENT)
    assert len(store.written) == 1
    assert store.read_keys == [assembly.capture_key(RUN_ID, assembly.FIRST_ORDINAL)]


def test_a_clean_capture_marks_every_row_done() -> None:
    """Every one of the six rows reads done after a clean tier 3 capture."""
    recorder, _ = run_one()
    assert recorder.rows() == dict.fromkeys(collector.ROW_NAMES, collector.STATE_DONE)


def test_a_clean_capture_writes_a_complete_document() -> None:
    """The stored document reports complete and breaks no validation rule."""
    _, store = run_one()
    document = store.written[0]
    assert document["capture_status"] == assembly.STATUS_COMPLETE
    assert document["partial_reasons"] == []
    assert assembly.validate_capture(document) == []


def test_the_stored_document_records_its_size_in_bytes() -> None:
    """The document carries a measured size, which retention needs."""
    recorder, store = run_one()
    assert store.written[0]["stored_size_bytes"] > 0
    assert recorder.merged()["stored_size_bytes"] == FakeStoreResult().stored_size_bytes


def test_the_device_index_and_the_device_list_hold_the_same_members() -> None:
    """Validation rule 7 holds, so a later comparison accepts the record."""
    _, store = run_one()
    document = store.written[0]
    assert set(document["device_index"]) == {row["mac"] for row in document["devices"]}
    assert assembly.RULE_INDEX_MATCH not in assembly.validate_capture(document)


def test_a_client_row_carries_the_name_of_its_serving_device() -> None:
    """The moved-client report shows a device name, not an address alone."""
    _, store = run_one()
    wired = store.written[0]["clients"]["wired"]
    assert wired[0]["device_name"] == "idf2-sw01"


def test_the_wireless_list_joins_both_wireless_reads() -> None:
    """One wireless client carries the signal and the randomized-address flag."""
    _, store = run_one()
    wireless = store.written[0]["clients"]["wireless"]
    assert len(wireless) == 1
    assert wireless[0]["rssi"] == -55
    assert wireless[0]["random_mac"] is False


# ---------------------------------------------------------------------------
# Tier 2
# ---------------------------------------------------------------------------


def test_tier_two_skips_both_extra_rows_and_reads_no_extra_section() -> None:
    """A tier 2 capture never calls the extra read and shows two skipped rows."""
    recorder, store = run_one(tier=assembly.TIER_STANDARD, reads=build_reads(extras=raising_read))
    rows = recorder.rows()
    assert rows[collector.ROW_EXTRAS] == collector.STATE_SKIPPED
    assert rows[collector.ROW_ALARMS] == collector.STATE_SKIPPED
    assert "extras" not in store.written[0]
    assert recorder.merged()["state"] == collector.CAPTURE_VERIFIED


# ---------------------------------------------------------------------------
# One failing section
# ---------------------------------------------------------------------------


def test_one_failed_read_still_stores_the_other_sections() -> None:
    """A lost wireless read leaves the devices and the wired clients in place."""
    recorder, store = run_one(reads=build_reads(wireless_search=raising_read))
    document = store.written[0]
    assert recorder.merged()["state"] == collector.CAPTURE_VERIFIED
    assert document["capture_status"] == assembly.STATUS_PARTIAL
    assert len(document["devices"]) == 2
    assert len(document["clients"]["wired"]) == 1


def test_one_failed_read_paints_only_its_own_row() -> None:
    """The wireless row turns red and every other row stays done."""
    recorder, _ = run_one(reads=build_reads(wireless_search=raising_read))
    rows = recorder.rows()
    assert rows[collector.ROW_WIRELESS] == collector.STATE_FAILED
    assert rows[collector.ROW_DEVICES] == collector.STATE_DONE
    assert rows[collector.ROW_WIRED] == collector.STATE_DONE


def test_a_failure_reason_names_the_report_row_and_keeps_the_read_name() -> None:
    """A stored reason names the row, so a reload paints the same red row."""
    _, store = run_one(reads=build_reads(wireless_search=raising_read))
    reasons = store.written[0]["partial_reasons"]
    assert [entry["section"] for entry in reasons] == [collector.ROW_WIRELESS]
    assert reasons[0][collector.REASON_SOURCE_FIELD] == assembly.GROUP_WIRELESS_SEARCH
    assert assembly.REASON_FIELDS <= set(reasons[0])


def test_a_lost_wired_group_reports_both_the_wired_row_and_the_guest_row() -> None:
    """One call group reads both lists, so one failure covers two rows."""
    recorder, store = run_one(reads=build_reads(wired=raising_read))
    rows = recorder.rows()
    assert rows[collector.ROW_WIRED] == collector.STATE_FAILED
    assert rows[collector.ROW_GUEST] == collector.STATE_FAILED
    named = {entry["section"] for entry in store.written[0]["partial_reasons"]}
    assert named == {collector.ROW_WIRED, collector.ROW_GUEST}


def test_a_failed_alarm_read_paints_the_alarm_row_alone() -> None:
    """The alarms row is its own row, and the extras row stays done."""

    def alarm_fault(session: Any, scope: extras.SiteScope, device_stats: Any) -> dict[str, extras.ExtraSection]:
        """Answer with a section set whose alarm read failed.

        Args:
            session: Unused.
            scope: Unused.
            device_stats: Unused.

        Returns:
            One section for each tier 3 name, with the alarms failed.
        """
        del session, scope, device_stats
        return extra_sections(failed=extras.SECTION_ALARMS)

    recorder, store = run_one(reads=build_reads(extras=alarm_fault))
    rows = recorder.rows()
    assert rows[collector.ROW_ALARMS] == collector.STATE_FAILED
    assert rows[collector.ROW_EXTRAS] == collector.STATE_DONE
    assert [entry["section"] for entry in store.written[0]["partial_reasons"]] == [collector.ROW_ALARMS]


def test_a_lost_device_read_still_writes_a_document() -> None:
    """The capture keeps going without a device read and reports the loss."""
    recorder, store = run_one(reads=build_reads(devices=raising_read))
    document = store.written[0]
    assert (document["device_index"], document["devices"]) == ({}, [])  # Neither field survives a lost read.
    assert recorder.rows()[collector.ROW_DEVICES] == collector.STATE_FAILED
    assert collector.ROW_DEVICES in {entry["section"] for entry in document["partial_reasons"]}


# ---------------------------------------------------------------------------
# The store
# ---------------------------------------------------------------------------


def test_a_store_that_refuses_the_write_fails_the_capture() -> None:
    """A refused write never reads the key back and never reports verified."""
    store = FakeStore(result=FakeStoreResult(verified=False, reason="database_unreachable", stored_size_bytes=0))
    recorder, _ = run_one(store=store)
    record = recorder.merged()
    assert record["state"] == collector.CAPTURE_FAILED
    assert record["verified"] is False
    assert record["message"] == collector.WRITE_FAILED_MESSAGE
    assert store.read_keys == []


def test_a_read_back_that_does_not_match_fails_the_capture() -> None:
    """A write result alone is no proof, so a bad read-back fails the capture."""
    store = FakeStore(load=FakeCaptureLoad(comparable=False, reason="digest_mismatch"))
    recorder, _ = run_one(store=store)
    record = recorder.merged()
    assert record["state"] == collector.CAPTURE_FAILED
    assert record["verified"] is False
    assert record["message"] == collector.READ_BACK_MESSAGE
    assert len(store.read_keys) == 1


def test_a_partial_capture_that_stores_reports_the_partial_sentence() -> None:
    """The operator reads that the record is stored and a section is missing."""
    recorder, _ = run_one(reads=build_reads(wireless_search=raising_read))
    assert recorder.merged()["message"] == collector.PARTIAL_MESSAGE


def test_a_capture_with_no_cloud_session_stops_before_any_read() -> None:
    """No session means no read, so the capture fails and names the gap."""
    recorder = Recorder()
    store = FakeStore()
    resources = collector.CaptureResources(
        session=None,
        reads=build_reads(devices=raising_read, wired=raising_read),
        store=store.holder(),
        report=recorder,
        executor=sequential_executor,
    )
    collector.run_capture(build_job(), resources)
    record = recorder.merged()
    assert record["state"] == collector.CAPTURE_FAILED
    assert record["message"] == collector.NO_SESSION_MESSAGE
    assert store.written == []


def test_the_job_may_carry_the_cloud_session() -> None:
    """A job that carries a session needs no resource session."""
    recorder = Recorder()
    store = FakeStore()
    resources = collector.CaptureResources(
        reads=build_reads(), store=store.holder(), report=recorder, executor=sequential_executor
    )
    job = dict(build_job(), cloud_session=object())
    collector.run_capture(job, resources)
    assert recorder.merged()["state"] == collector.CAPTURE_VERIFIED


# ---------------------------------------------------------------------------
# The two readable names
# ---------------------------------------------------------------------------


def test_the_stored_document_carries_both_names_of_the_job() -> None:
    """A job that carries both names puts both names in the stored document.

    Why:
        The operator compares a stored capture days later. A document that
        holds only identifiers makes that reader guess which site it reads.
    """
    store = FakeStore()
    resources = collector.CaptureResources(
        session=object(), reads=build_reads(), store=store.holder(), report=Recorder(), executor=sequential_executor
    )
    job = dict(build_job(), org_name=ORG_NAME, site_name=SITE_NAME)
    collector.run_capture(job, resources)
    assert store.written[0]["org_name"] == ORG_NAME
    assert store.written[0]["site_name"] == SITE_NAME


def test_a_job_with_no_names_stores_an_empty_name() -> None:
    """A job built by hand may name neither the organization nor the site.

    Why:
        A command-line caller and a test both build a job by hand. The read
        falls back to an empty value, so no such caller meets a raise.
    """
    _, store = run_one()
    assert store.written[0]["org_name"] == ""
    assert store.written[0]["site_name"] == ""


# ---------------------------------------------------------------------------
# The progress sequence
# ---------------------------------------------------------------------------


def test_the_percent_rises_step_by_step_and_never_moves_backwards() -> None:
    """The bar moves as each call group ends, so the poll shows real progress."""
    recorder, _ = run_one()
    percents = recorder.percents()
    assert percents[0] == collector.READ_FLOOR
    assert percents[-1] == collector.WHOLE_PERCENT
    assert percents == sorted(percents)
    assert len(set(percents)) >= len(collector.wave_names(assembly.TIER_EXTRA))


def test_the_percent_passes_through_the_read_ceiling_and_the_write_step() -> None:
    """Each stage of the work reports its own percent."""
    recorder, _ = run_one()
    percents = set(recorder.percents())
    assert collector.READ_CEILING in percents
    assert collector.ASSEMBLE_PERCENT in percents
    assert collector.WRITE_PERCENT in percents


def test_the_first_report_names_the_collecting_state() -> None:
    """The page shows the collecting state before the first read ends."""
    recorder, _ = run_one()
    assert recorder.changes[0]["state"] == collector.CAPTURE_COLLECTING
    assert recorder.changes[0]["message"] == collector.COLLECTING_MESSAGE


def test_every_report_carries_the_whole_section_map() -> None:
    """A poll between two reads still paints all six rows."""
    recorder, _ = run_one()
    shapes = {frozenset(change["sections"]) for change in recorder.changes if "sections" in change}
    assert shapes == {frozenset(collector.ROW_NAMES)}  # One shape only, and it holds every row.


# ---------------------------------------------------------------------------
# The pool seam
# ---------------------------------------------------------------------------


def test_wave_one_holds_one_call_group_for_each_capture_worker() -> None:
    """Wave one fills the capture pool exactly one time."""
    ledger = collector.ProgressLedger(CAPTURE_ID, Recorder(), collector.wave_names(assembly.TIER_EXTRA), 3)
    scope = extras.SiteScope(org_id=ORG_ID, site_id=SITE_ID)
    groups = collector.wave_one(object(), scope, build_reads(), ledger)
    assert len(groups) == pools.CAPTURE_WORKER_TARGET


def test_the_reads_run_in_two_waves_through_the_executor_seam() -> None:
    """The tier 3 read waits, because it needs the device statistics."""
    watcher = BatchRecorder()
    run_one(executor=watcher.execute)
    assert watcher.batches == [
        [
            assembly.GROUP_DEVICES,
            assembly.GROUP_WIRED_CLIENTS,
            assembly.GROUP_WIRELESS_STATISTICS,
            assembly.GROUP_WIRELESS_SEARCH,
        ],
        [assembly.GROUP_TIER_THREE],
    ]


def test_tier_two_runs_one_wave_alone() -> None:
    """A tier 2 capture never opens the second wave."""
    watcher = BatchRecorder()
    run_one(tier=assembly.TIER_STANDARD, executor=watcher.execute)
    assert len(watcher.batches) == 1


def test_the_tier_three_read_receives_the_device_statistics_rows() -> None:
    """The radio section reads the wave one rows and calls the cloud no more."""
    seen: list[Any] = []

    def watching_extras(session: Any, scope: extras.SiteScope, device_stats: Any) -> dict[str, extras.ExtraSection]:
        """Record the rows that the tier 3 read received.

        Args:
            session: Unused.
            scope: Unused.
            device_stats: The device statistics rows of wave one.

        Returns:
            One section for each tier 3 name.
        """
        del session, scope
        seen.append(device_stats)
        return extra_sections()

    run_one(reads=build_reads(extras=watching_extras))
    assert seen and [row["mac"] for row in seen[0]] == [SWITCH_MAC, ACCESS_POINT_MAC]


# ---------------------------------------------------------------------------
# The small parts
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("states", "expected"),
    [
        ((collector.STATE_DONE, collector.STATE_DONE), collector.STATE_DONE),
        ((collector.STATE_DONE, collector.STATE_FAILED), collector.STATE_FAILED),
        ((collector.STATE_DONE, ""), collector.STATE_PENDING),
        ((), collector.STATE_PENDING),
    ],
)
def test_fold_states_reads_the_worst_outcome(states: Sequence[str], expected: str) -> None:
    """One lost group loses the whole row.

    Args:
        states: The outcome of each feeding group.
        expected: The row state that the fold reports.
    """
    assert collector.fold_states(states) == expected


def test_starting_rows_skips_both_extra_rows_at_tier_two() -> None:
    """A tier 2 page waits for four rows and shows two skipped rows."""
    rows = collector.starting_rows(assembly.TIER_STANDARD)
    assert rows[collector.ROW_EXTRAS] == collector.STATE_SKIPPED
    assert rows[collector.ROW_DEVICES] == collector.STATE_PENDING


def test_starting_rows_keeps_every_row_pending_at_tier_three() -> None:
    """A tier 3 page waits for all six rows."""
    assert collector.starting_rows(assembly.TIER_EXTRA) == dict.fromkeys(collector.ROW_NAMES, collector.STATE_PENDING)


def test_every_report_row_names_at_least_one_call_group() -> None:
    """No row can stay pending for ever, because each row has a source."""
    assert set(collector.ROW_SOURCES) == set(collector.ROW_NAMES)
    assert all(collector.ROW_SOURCES[name] for name in collector.ROW_NAMES)


def test_every_failure_name_maps_onto_a_report_row() -> None:
    """A reason always lands on a row that the capture page paints."""
    for rows in collector.REASON_ROWS.values():
        assert set(rows) <= set(collector.ROW_NAMES)


def test_an_unknown_failure_name_keeps_itself() -> None:
    """A name that no map holds still reaches the stored document."""
    named = collector.row_reasons({"section": "some_new_read", "reason": "read_failed", "http_status": 0})
    assert named[0]["section"] == "some_new_read"
