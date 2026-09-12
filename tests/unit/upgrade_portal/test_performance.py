"""Budget tests for the capture time target and the comparison render target.

Why:
    Task T219 asks for a guard on two performance promises of the upgrade
    capture portal. A tier 2 capture of a 250-device site finishes in 90 seconds
    or less. A comparison page renders in 3 seconds or less.

    Correction to the task text. Task T219 names SC-002 for the capture target
    and SC-005 for the render target. Neither criterion states either number.
    On disk, `spec.md` SC-002 asks an operator to read the full comparison in
    under 30 seconds, and `spec.md` SC-005 asks that two operators on two sites
    never block each other. Both numbers are real, but they come from
    `plan.md` lines 64 to 67, which `quickstart.md` repeats and which
    `data-model.md` line 76 ties to the digest short circuit. The repository
    already records the wrong citation as finding I4 of `analysis.md` and the
    missing criterion as finding U1. This file therefore tests the two numbers
    and does not repeat the two wrong labels.

    Method. Both targets are promises about a live site, and a unit test cannot
    reach a live site. A timed run against fakes measures the speed of the
    fakes, so it would pass whatever the portal did. Each test below counts the
    work instead: call groups, read calls, and comparison deltas. A count is
    exact on every machine, and it fails when the work starts to grow with the
    size of the site. Growth with site size is the one way either target is
    lost.

    One test does measure time. It uses the real 3-second budget for work that
    takes a few milliseconds in memory, and its docstring states the margin. No
    test asserts a lower bound on speed.

    No test here opens a socket, reads the `.env` file, or names a real
    credential.
"""

from __future__ import annotations  # Keeps every annotation as text, per the repository style.

import threading  # The fake executor hands each worker a real semaphore, as the pool does.
import time  # The one timed test reads the monotonic clock.
from collections import Counter  # One tally for each read name of a fake site.
from collections.abc import Callable, Mapping  # The worker shape of the pool, and the store write shape.
from dataclasses import dataclass, field  # The fakes of this module.
from types import SimpleNamespace  # The two-field shape of a cloud answer.
from typing import Any  # A session, a store result, and a document are all free-form.

from src.upgrade_portal.capture import assembly, collector, devices, extras  # The capture lane under test.
from src.upgrade_portal.capture import clients as capture_clients  # The client records that a site read answers with.
from src.upgrade_portal.compare import clients as compare_clients  # The client half of a comparison.
from src.upgrade_portal.compare import diff, render  # The device half and the page builder.
from src.upgrade_portal.compare import statistics as compare_statistics  # The roll-up that the page shows.

LARGE_SITE_DEVICES = 250  # The site size that plan.md line 64 names for the 90 second capture target.
SMALL_SITE_DEVICES = 50  # The site size that spec.md SC-001 names for the first capture of a site.
TIER_TWO_GROUPS = 4  # The four call groups of wave one.
TIER_THREE_GROUPS = 5  # Wave one, and the one extra group of wave two.
RENDER_BUDGET_SECONDS = 3.0  # The comparison render target of plan.md line 66.
CAPTURE_BUDGET_SECONDS = 90.0  # The tier 2 capture target of plan.md line 64, for a 250 device site.
CLOUD_PAGE_SECONDS = 2.5  # A pessimistic wall clock for one paged cloud call, used by the duration model.
CAPTURE_POOL_WORKERS = 4  # plan.md sizes the capture pool at four workers.
WAVE_ONE_READS = ("devices", "wired", "wireless_stats", "wireless_search")  # The four groups that run together.
WAVE_TWO_READS = ("extras",)  # The one group that only tier 3 runs, and only after wave one.
TIER_THREE_GROUP = "extras"  # The name of the group that fans its cloud calls out.
TIER_THREE_READS = tuple(extras.CLOUD_FETCHERS)  # The four cloud calls inside that one group.
TIER_THREE_CLOUD_CALLS = 4  # The ports, the tunnels, the BGP peers, and the alarms.
OLD_VERSION = "21.4R3.15"  # The firmware before the upgrade.
NEW_VERSION = "23.4R2.13"  # The firmware after the upgrade.
QUIET_DIGEST = "b1946ac92492d2347c6235b4d2611184"  # One digest that both captures of a quiet site carry.
RUN_ID = "run-0123456789abcdef"  # The owning run of every fake capture.
ORG_ID = "11111111-1111-1111-1111-111111111111"  # The fake organization.
SITE_ID = "22222222-2222-2222-2222-222222222222"  # The fake site.


def fake_device_mac(ordinal: int) -> str:
    """Return the address of one fake device.

    Why:
        Both lanes of this file need the same address for the same ordinal, so
        a capture test and a comparison test describe one fake site. The prefix
        is obviously invented, so a reader sees at once that no test reaches
        real hardware.

    Args:
        ordinal: The position of the device in the fake site.

    Returns:
        One twelve character address.
    """
    return f"0011220{ordinal:05x}"  # Seven fixed characters and five that carry the ordinal.


def fake_client_mac(ordinal: int) -> str:
    """Return the address of one fake client.

    Args:
        ordinal: The position of the client in the fake site.

    Returns:
        One twelve character address.
    """
    return f"aabbcc{ordinal:06x}"  # Six fixed characters and six that carry the ordinal.


# ---------------------------------------------------------------------------
# The capture lane fakes
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class FakeStoreResult:
    """Stands in for ``store.StoreResult`` with a verified write.

    Attributes:
        verified: True when the store wrote the record and read it back.
        reason: Names the refusal. Empty after a verified write.
        stored_size_bytes: The measured size of the stored record.
    """

    verified: bool = True  # Every capture of this file writes cleanly.
    reason: str = ""  # No refusal to report.
    stored_size_bytes: int = 4096  # A plausible stored size.


@dataclass(frozen=True, slots=True)
class FakeCaptureLoad:
    """Stands in for ``store.CaptureLoad`` with a comparable record.

    Attributes:
        comparable: True when the stored record is fit for a comparison.
        reason: Names the refusal. Empty after a matching read-back.
        capture: The stored record.
    """

    comparable: bool = True  # Every read-back of this file succeeds.
    reason: str = ""  # No refusal to report.
    capture: dict[str, Any] | None = None  # No test here reads the record back.


@dataclass
class FakeStore:
    """Keeps every document that a fake capture writes.

    Why:
        The capture tests read the stored document to prove that the reads
        really happened. A store that threw the document away would let a
        broken capture pass a call count test.

    Attributes:
        written: Each document that the collector wrote.
    """

    written: list[dict[str, Any]] = field(default_factory=list)  # In write order.

    def write(self, document: Mapping[str, Any]) -> FakeStoreResult:
        """Keep one document and answer with a verified result.

        Args:
            document: The capture document.

        Returns:
            The fixed store result.
        """
        self.written.append(dict(document))  # A copy, so a later change cannot reach the test.
        return FakeStoreResult()  # The write always verifies here.

    def read_back(self, capture_id: str) -> FakeCaptureLoad:
        """Answer one read-back with a comparable load.

        Args:
            capture_id: The identifier of the capture.

        Returns:
            The fixed load result.
        """
        del capture_id  # The fake store holds one document, so the key never selects.
        return FakeCaptureLoad()  # The read-back always succeeds here.

    def holder(self) -> collector.CaptureStore:
        """Return this fake in the shape that the collector expects.

        Returns:
            The store holder.
        """
        return collector.CaptureStore(write=self.write, read_back=self.read_back)  # The two call seams.


@dataclass
class FakeSite:
    """A fake site of a chosen size that counts every read of one capture.

    Why:
        The 90 second capture target holds only while the cost of a capture
        stays flat as the site grows. A tally on each read turns that promise
        into a number that a test can compare between two site sizes. The five
        methods match the five reads of ``collector.SiteReads``, so a change to
        that holder breaks this fake instead of hiding behind it.

    Attributes:
        device_count: The number of devices the fake site holds.
        calls: One tally for each call group name.
        cloud_calls: One tally for each cloud call inside the tier 3 group. The
            two tallies stay apart, because a group and a call inside a group
            answer two different questions.
    """

    device_count: int  # Every read answers with this many rows.
    calls: Counter[str] = field(default_factory=Counter)  # Starts empty and grows one call group at a time.
    cloud_calls: Counter[str] = field(default_factory=Counter)  # Starts empty and grows one tier 3 call at a time.

    def inventory_rows(self) -> list[dict[str, Any]]:
        """Build one inventory row for each device of the fake site.

        Returns:
            The inventory rows.
        """
        return [
            {
                "mac": fake_device_mac(number),  # The address that both lanes share.
                "type": "switch",  # One device type keeps the fixture readable.
                "model": "EX4400-48P",  # A plausible model.
                "status": "connected",  # Every device answers before the upgrade.
                "name": f"switch-{number:03d}",  # A readable name for the page.
                "version": OLD_VERSION,  # The firmware before the upgrade.
            }
            for number in range(self.device_count)  # One row for each device.
        ]

    def statistics_rows(self) -> list[dict[str, Any]]:
        """Build one statistics row for each device of the fake site.

        Returns:
            The statistics rows.
        """
        return [
            {"mac": fake_device_mac(number), "type": "switch", "status": "connected", "uptime": 900000}
            for number in range(self.device_count)  # One row for each device, so no device type is lost.
        ]

    def read_devices(self, session: Any, org_id: str, site_id: str) -> tuple[devices.DeviceRead, devices.DeviceRead]:
        """Answer the device group with the inventory read and the statistics read.

        Args:
            session: Unused.
            org_id: Unused.
            site_id: Unused.

        Returns:
            Both device reads.
        """
        del session, org_id, site_id  # A fake site needs no session and no identifier.
        self.calls["devices"] += 1  # One call group, whatever the size of the site.
        inventory = devices.DeviceRead(devices.SECTION_INVENTORY, self.inventory_rows(), [])  # The inventory read.
        return inventory, devices.DeviceRead(devices.SECTION_STATISTICS, self.statistics_rows(), [])  # Both reads.

    def read_clients(self, session: Any, site_id: str) -> tuple[list[Any], list[Any]]:
        """Answer the wired group with one wired client for each device.

        Args:
            session: Unused.
            site_id: Unused.

        Returns:
            The wired records and the guest records.
        """
        del session, site_id  # A fake site needs no session and no identifier.
        self.calls["wired"] += 1  # One call group, whatever the size of the site.
        wired = [
            capture_clients.ClientRecord(
                mac=fake_client_mac(number),  # The client address.
                attachment=capture_clients.ClientAttachment(device_mac=fake_device_mac(number), port_id="ge-0/0/1"),
            )
            for number in range(self.device_count)  # One wired client on each device.
        ]
        return wired, []  # This fake site holds no guest client.

    def read_wireless_stats(self, session: Any, site_id: str) -> list[dict[str, Any]]:
        """Answer the wireless statistics group with one row for each device.

        Args:
            session: Unused.
            site_id: Unused.

        Returns:
            The wireless statistics rows.
        """
        del session, site_id  # A fake site needs no session and no identifier.
        self.calls["wireless_stats"] += 1  # One call group, whatever the size of the site.
        return [
            {"mac": fake_client_mac(number), "ap_mac": fake_device_mac(number), "rssi": -55, "ssid": "corp"}
            for number in range(self.device_count)  # One wireless client on each device.
        ]

    def read_wireless_search(self, session: Any, site_id: str) -> list[dict[str, Any]]:
        """Answer the wireless search group with one row for each device.

        Args:
            session: Unused.
            site_id: Unused.

        Returns:
            The wireless search rows.
        """
        del session, site_id  # A fake site needs no session and no identifier.
        self.calls["wireless_search"] += 1  # One call group, whatever the size of the site.
        return [
            {"mac": fake_client_mac(number), "random_mac": False, "last_hostname": f"laptop-{number:03d}"}
            for number in range(self.device_count)  # One search row for each wireless client.
        ]

    def read_extras(self, session: Any, scope: extras.SiteScope, device_stats: Any) -> dict[str, extras.ExtraSection]:
        """Answer the tier 3 group through the real collector of that group.

        Why:
            An earlier version of this fake answered the six sections itself.
            The model then saw one call for the whole group, while the real
            group made four cloud calls one after another, and no test could
            tell. This fake now drives ``extras.collect_extras`` and counts each
            cloud call of its own, so the model measures the code and not a
            stand-in.

        Args:
            session: Passed through. The fake cloud calls ignore it.
            scope: Passed through. The fake cloud calls ignore it.
            device_stats: The tier 2 statistics that the radio section reads.

        Returns:
            One section for each tier 3 name.
        """
        self.calls["extras"] += 1  # The fifth call group, which only tier 3 runs.
        payloads = extras.SourcePayloads(device_stats=device_stats)  # The radio section costs no cloud call.
        return extras.collect_extras(session, scope, payloads, self.tier_three_fetchers())  # The real group.

    def tier_three_fetchers(self) -> dict[str, Any]:
        """Return one counted stand-in for each cloud call of the tier 3 group.

        Why:
            Each name gets its own tally, so the model can tell four calls that
            run at one time from four calls that run one after another.

        Returns:
            One fake cloud call for each name of ``extras.CLOUD_FETCHERS``.
        """
        return {name: self.tier_three_call(name) for name in extras.CLOUD_FETCHERS}  # One counted call for each name.

    def tier_three_call(self, name: str) -> Any:
        """Return one counted stand-in for one tier 3 cloud call.

        Args:
            name: The cloud call name to count.

        Returns:
            A call that tallies its name and answers with an empty page.
        """

        def fetch(session: Any, scope: extras.SiteScope) -> SimpleNamespace:
            """Tally this cloud call and answer with one empty page."""
            del session, scope  # A fake cloud call needs no session and no scope.
            self.cloud_calls[name] += 1  # One tally for each tier 3 cloud call.
            return SimpleNamespace(status_code=200, data=[])  # The two fields the reader looks at.

        return fetch

    def reads(self) -> collector.SiteReads:
        """Return the five reads in the holder that the collector expects.

        Returns:
            The read holder.
        """
        return collector.SiteReads(
            devices=self.read_devices,  # The device group.
            wired=self.read_clients,  # The wired client group.
            wireless_stats=self.read_wireless_stats,  # The wireless statistics group.
            wireless_search=self.read_wireless_search,  # The wireless search group.
            extras=self.read_extras,  # The tier 3 group.
        )


def sequential_executor(
    work_items: list[Any], worker_function: Callable[[Any, threading.Semaphore], Any], batch_description: str
) -> tuple[list[Any], list[Any]]:
    """Run every call group in this thread, in order.

    Why:
        A unit test must not depend on a thread pool that reads the settings of
        the whole program. This stands in for ``CapturePool.execute`` and keeps
        the same contract: a falsy worker result counts as lost. The signature
        repeats the ``assembly.GroupExecutor`` type exactly, because a looser
        stand-in would accept a worker that the real pool refuses.

    Args:
        work_items: The call groups.
        worker_function: The worker that runs one call group.
        batch_description: Unused. The real pool logs it.

    Returns:
        The finished results and the lost work items.
    """
    del batch_description  # The real pool logs this, and a test does not read the log.
    finished: list[Any] = []  # The result of each group that the worker finished.
    lost: list[Any] = []  # The work item of each group that the worker lost.
    for item in work_items:
        result = worker_function(item, threading.Semaphore(1))  # The real pool hands over a semaphore too.
        finished.append(result) if result else lost.append(item)  # A falsy result counts as lost.
    return finished, lost


def capture_job(tier: int) -> dict[str, Any]:
    """Build the job that the start route hands to a capture worker.

    Args:
        tier: The data tier of the capture.

    Returns:
        The fields of one capture job.
    """
    return {
        "capture_id": assembly.capture_key(RUN_ID, assembly.FIRST_ORDINAL),  # The identifier of this capture.
        "run_id": RUN_ID,  # The owning run.
        "ordinal": assembly.FIRST_ORDINAL,  # The first capture of the run.
        "role": "pre",  # The pre-check capture.
        "org_id": ORG_ID,  # The fake organization.
        "site_id": SITE_ID,  # The fake site.
        "tier": tier,  # The data tier under test.
        "actor_email": "operator@example.com",  # An obviously invented address.
    }


def run_capture_for(site: FakeSite, tier: int = collector.TIER_STANDARD) -> dict[str, Any]:
    """Run one whole capture against a fake site and return the stored document.

    Why:
        Three tests need the same run with a different site size or tier. One
        helper keeps each test to the one line that names its difference.

    Args:
        site: The fake site to read.
        tier: The data tier of the capture.

    Returns:
        The document that the collector stored.
    """
    store = FakeStore()  # Keeps the one document that this capture writes.
    resources = collector.CaptureResources(
        session=object(),  # Any object stands in for a cloud session, because no read uses it.
        reads=site.reads(),  # The five counted reads.
        store=store.holder(),  # The store that keeps the document.
        report=lambda capture_id, changes: None,  # No test here reads the progress record.
        executor=sequential_executor,  # No thread pool, so the run is repeatable.
    )
    collector.run_capture(capture_job(tier), resources)  # Opens no socket and reaches no database.
    return store.written[-1]  # The stored document of this capture.


def bounded_rounds(work_count: int) -> int:
    """Return how many full rounds a bounded pool needs for one set of work.

    Why:
        Both the call group pool and the tier 3 fan-out hold four workers, so
        work wider than four costs more than one round. One helper states that
        rule, and both parts of the model read it.

    Args:
        work_count: How many pieces of work run together.

    Returns:
        The round count, which is 1 for any set that fits the pool.
    """
    return -(-work_count // CAPTURE_POOL_WORKERS)  # Round up, because a part round still costs a whole wait.


def group_pages(site: FakeSite, name: str) -> int:
    """Return how many cloud pages one call group waits for, one after another.

    Why:
        Most groups make one call, so their page tally is the wait. The tier 3
        group makes four calls and runs them at one time, so its wait is the
        longest of the four and never their sum. A model that added them would
        pass a serial group, which is the exact regression this file exists to
        catch.

    Args:
        site: The fake site, already read by one capture.
        name: The call group name.

    Returns:
        The page count that this group waits for.
    """
    if name != TIER_THREE_GROUP:  # Every other group makes one call of its own
        return site.calls[name]
    pages = [site.cloud_calls[read] for read in TIER_THREE_READS]  # One tally for each tier 3 cloud call
    return max(pages, default=0) * bounded_rounds(len(TIER_THREE_READS))  # The longest call decides the group


def modeled_capture_seconds(site: FakeSite, tier: int) -> float:
    """Return the modeled wall clock of one capture against a real cloud.

    Why:
        A fake cloud answers in microseconds, so a stopwatch around a fake
        capture measures nothing that the 90 second target is about. The target
        is spent on cloud latency, and the shape of the plan decides how much of
        that latency runs at the same time. This model turns the measured call
        tally into a duration, so a test can assert seconds and not a count.

        The model follows the two rules that the collector obeys. The pages
        inside one call run one after another, because the cloud paginates with
        a cursor. Independent calls run at one time, up to the four workers of
        the pool. That rule holds between the groups of one wave and inside the
        tier 3 group. Wave two waits for wave one, because the radio section
        reads the device statistics of wave one.

    Args:
        site: The fake site, already read by one capture.
        tier: The data tier of that capture.

    Returns:
        The modeled seconds.
    """
    waves = [WAVE_ONE_READS] if tier < collector.TIER_EXTRA else [WAVE_ONE_READS, WAVE_TWO_READS]
    total = 0.0  # The modeled seconds of every wave.
    for wave in waves:
        pages = [group_pages(site, name) for name in wave]  # The page count of each group of this wave.
        total += max(pages, default=0) * CLOUD_PAGE_SECONDS * bounded_rounds(len(wave))  # The slowest group decides
    return total


def serial_tier_three_seconds(site: FakeSite) -> float:
    """Return what the tier 3 group would cost with its calls in order.

    Why:
        A test that can never fail proves nothing. This is the regression the
        fan-out removed, so one test compares it against the real model and
        proves the model can tell the two shapes apart.

    Args:
        site: The fake site, already read by one tier 3 capture.

    Returns:
        The modeled seconds of a tier 3 group that waits for each call in turn.
    """
    return sum(site.cloud_calls[read] for read in TIER_THREE_READS) * CLOUD_PAGE_SECONDS


# ---------------------------------------------------------------------------
# The comparison lane fixtures
# ---------------------------------------------------------------------------


def device_index(count: int, version: str) -> dict[str, dict[str, Any]]:
    """Build a device index of a chosen size, all on one firmware version.

    Args:
        count: The number of devices.
        version: The firmware version of every device.

    Returns:
        One index row for each device, by address.
    """
    return {
        fake_device_mac(number): {
            "name": f"switch-{number:03d}",  # A readable name for the page.
            "model": "EX4400-48P",  # A plausible model.
            "version": version,  # The field that an upgrade changes.
            "status": "connected",  # Every device answers.
            "ip": f"10.10.{number // 256}.{number % 256}",  # A distinct address for each device.
            "uptime": 900000,  # A reboot resets this, so no comparison reads it.
            "vc_role": "master",  # A single member chassis.
            "num_members": 1,  # A single member chassis.
        }
        for number in range(count)  # One row for each device.
    }


def client_rows(count: int) -> dict[str, list[dict[str, Any]]]:
    """Build the three client sections of a fake site.

    Args:
        count: The number of clients in each section.

    Returns:
        One row list for each client kind.
    """
    rows = [
        {"mac": fake_client_mac(number), "hostname": f"laptop-{number:03d}", "device_mac": fake_device_mac(number)}
        for number in range(count)  # One client for each device.
    ]
    return {kind: [dict(row) for row in rows] for kind in compare_clients.CLIENT_KINDS}  # A copy for each kind.


def quiet_digests() -> dict[str, str]:
    """Build the digest map of a site that did not change.

    Why:
        Both captures of a quiet site carry the same digest for every section,
        which is what lets a comparison skip the whole section. Building the map
        here keeps the skip tests to the difference each one names.

    Returns:
        One matching digest for the device section and for all three client sections.
    """
    names = (diff.SECTION_DEVICES, *compare_clients.CLIENT_SECTIONS)  # The four comparison sections.
    return dict.fromkeys(names, QUIET_DIGEST)  # The same digest under every name.


def comparison_capture(count: int, version: str, digests: dict[str, str] | None = None) -> dict[str, Any]:
    """Build one capture document for the comparison lane.

    Args:
        count: The number of devices, and the number of clients in each section.
        version: The firmware version of every device.
        digests: The digest map, when the test needs one.

    Returns:
        One capture document.
    """
    capture: dict[str, Any] = {
        "device_index": device_index(count, version),  # The rows that the device comparison reads.
        "clients": client_rows(count),  # The rows that the client comparison reads.
        "site_name": "Fake Campus",  # The header of the page shows this.
        "org_name": "Fake Organization",  # The header of the page shows this.
    }
    if digests is not None:  # A test that drives the short circuit supplies the map.
        capture["digests"] = digests
    return capture


# ---------------------------------------------------------------------------
# The capture time target of plan.md line 64
# ---------------------------------------------------------------------------


def test_a_tier_two_capture_runs_four_call_groups() -> None:
    """A tier 2 capture runs four call groups, and tier 3 adds one more.

    Why:
        The 90 second target rests on a fixed, small number of cloud calls that
        run at the same time. Four groups match the four capture workers of the
        pool, so one wave fills the pool exactly one time. A fifth group at
        tier 2 would add a second wave and put the target at risk.
    """
    tier_two = collector.wave_names(collector.TIER_STANDARD)  # The group names of a tier 2 capture.
    tier_three = collector.wave_names(collector.TIER_EXTRA)  # The group names of a tier 3 capture.
    assert len(tier_two) == TIER_TWO_GROUPS  # Wave one holds four groups.
    assert len(tier_three) == TIER_THREE_GROUPS  # Tier 3 adds the one group of wave two.
    assert tier_three[:TIER_TWO_GROUPS] == tier_two  # Tier 3 adds a group and replaces none.
    assert len(set(tier_two)) == TIER_TWO_GROUPS  # Four distinct names, so no group is counted twice.


def test_the_capture_cost_stays_flat_as_the_site_grows() -> None:
    """A 250-device site costs the same number of cloud calls as a 50-device site.

    Why:
        This is the whole basis of the 90 second target. Every read of the
        capture is a paged list call for the site, not a call for each device.
        A per-device call would make a 250-device site five times the work of a
        50-device site, and no wall-clock test on a fake would ever notice. The
        tally below notices at once.
    """
    small = FakeSite(SMALL_SITE_DEVICES)  # The site of spec.md SC-001.
    large = FakeSite(LARGE_SITE_DEVICES)  # The site of the 90 second target.
    small_document = run_capture_for(small)  # One whole tier 2 capture.
    large_document = run_capture_for(large)  # One whole tier 2 capture, five times the devices.
    assert small.calls == large.calls  # Five times the devices, and the same call count.
    assert sum(large.calls.values()) == TIER_TWO_GROUPS  # Four calls, one for each group of wave one.
    assert len(small_document["device_index"]) == SMALL_SITE_DEVICES  # The small capture really read 50 devices.
    assert len(large_document["device_index"]) == LARGE_SITE_DEVICES  # The large capture really read 250 devices.


def test_a_tier_two_capture_never_reads_the_tier_three_group() -> None:
    """Tier 2 leaves the extra section group alone, and tier 3 reads it once.

    Why:
        The tier 3 group waits for the device statistics of wave one, so it
        starts a second wave and adds its whole round trip to the elapsed time.
        The 90 second target belongs to tier 2, so tier 2 must never pay for it.
    """
    tier_two_site = FakeSite(SMALL_SITE_DEVICES)  # A site that runs at tier 2.
    tier_three_site = FakeSite(SMALL_SITE_DEVICES)  # The same site that runs at tier 3.
    run_capture_for(tier_two_site, collector.TIER_STANDARD)  # One tier 2 capture.
    run_capture_for(tier_three_site, collector.TIER_EXTRA)  # One tier 3 capture.
    assert tier_two_site.calls["extras"] == 0  # Tier 2 never runs the second wave.
    assert tier_three_site.calls["extras"] == 1  # Tier 3 runs it exactly one time.
    assert sum(tier_two_site.calls.values()) == TIER_TWO_GROUPS  # Four calls at tier 2.
    assert sum(tier_three_site.calls.values()) == TIER_THREE_GROUPS  # Five calls at tier 3.


# ---------------------------------------------------------------------------
# The comparison render target of plan.md line 66
# ---------------------------------------------------------------------------


def test_matching_digests_skip_every_comparison_section() -> None:
    """A quiet 250-device site skips all four comparison sections.

    Why:
        `data-model.md` line 76 names the digest short circuit as the reason the
        page renders in 3 seconds. A comparison that ignored the digests would
        walk 250 device rows and 750 client rows for a site where nothing moved.
        This test states the skip as a count of sections and a count of deltas.
    """
    before = comparison_capture(LARGE_SITE_DEVICES, OLD_VERSION, quiet_digests())  # The pre-check capture.
    after = comparison_capture(LARGE_SITE_DEVICES, OLD_VERSION, quiet_digests())  # The post-check capture.
    device_result = diff.compare_devices(before, after)  # The device half.
    client_result = compare_clients.compare_clients(before, after)  # The client half.
    assert device_result.deltas == ()  # No device row reached the page.
    assert client_result.deltas == ()  # No client row reached the page.
    assert device_result.skipped_sections == (diff.SECTION_DEVICES,)  # The device section is named as skipped.
    assert client_result.skipped_sections == compare_clients.CLIENT_SECTIONS  # All three client sections are skipped.


def test_the_skip_reads_no_device_row_at_all() -> None:
    """A skipped section never reads its rows, and the same pair without digests does.

    Why:
        An empty delta list alone does not prove a short circuit, because an
        empty fixture gives the same answer. This test empties the index of the
        post-check capture and keeps the digest matching. A comparison that read
        the rows would report 250 removed devices. It reports none. The second
        half runs the identical pair with the digests removed and gets the 250
        deltas back, which proves the fixture holds real work to skip.
    """
    before = comparison_capture(LARGE_SITE_DEVICES, OLD_VERSION, quiet_digests())  # A full pre-check capture.
    after = comparison_capture(LARGE_SITE_DEVICES, OLD_VERSION, quiet_digests())  # A post-check capture.
    after["device_index"] = {}  # An empty index that the matching digest must hide.
    quiet = diff.compare_devices(before, after)  # The comparison with the digests in place.
    assert quiet.deltas == ()  # The short circuit answered before it read one row.
    assert quiet.skipped_sections == (diff.SECTION_DEVICES,)  # The page reports the skip to the operator.
    loud = diff.compare_devices({"device_index": before["device_index"]}, {"device_index": {}})  # No digests.
    assert len(loud.deltas) == LARGE_SITE_DEVICES  # The same rows, read in full, give 250 deltas.


def test_the_comparison_work_stays_linear_with_the_site() -> None:
    """The delta count of a changed site equals the device count, at both sizes.

    Why:
        A comparison that matched every device against every other device would
        answer 62500 deltas for a 250-device site and would miss the 3 second
        target on a real page. One delta for each address proves the comparison
        joins on the address instead. Two sizes prove the count follows the
        site rather than a constant in the fixture.
    """
    counts = []  # The delta count at each site size.
    for size in (SMALL_SITE_DEVICES, LARGE_SITE_DEVICES):
        before = comparison_capture(size, OLD_VERSION)  # Every device on the old firmware.
        after = comparison_capture(size, NEW_VERSION)  # Every device on the new firmware.
        counts.append(len(diff.compare_devices(before, after).deltas))  # One comparison at this size.
    assert counts == [SMALL_SITE_DEVICES, LARGE_SITE_DEVICES]  # One delta for each device, never one for each pair.
    assert counts[1] == counts[0] * 5  # Five times the devices gives five times the work, not twenty five times.


def test_a_tier_two_capture_of_a_large_site_fits_the_ninety_second_target() -> None:
    """A tier 2 capture of a 250-device site models 2.5 seconds of cloud time.

    Why:
        `plan.md` line 64 promises a 90 second capture. Every other test of this
        section counts call groups, and a count is not a duration. This test
        turns the measured tally into seconds with `modeled_capture_seconds`, so
        it fails the moment the plan grows a wave, serializes a group, or starts
        a per-device call.

        A 250-device site fills one page of every read, so wave one is four
        groups of one page each. Four groups fit the four workers of the pool in
        one round, and the slowest group decides the wave. The model therefore
        gives one page of latency, which is 2.5 seconds against a budget of 90.
        The margin is 36 times.
    """
    site = FakeSite(LARGE_SITE_DEVICES)  # The site size that the target names.
    run_capture_for(site)  # One whole tier 2 capture, which fills the tally.
    modeled = modeled_capture_seconds(site, collector.TIER_STANDARD)  # The tally, turned into seconds.
    assert modeled == CLOUD_PAGE_SECONDS  # One page of latency, because four groups share four workers.
    assert modeled < CAPTURE_BUDGET_SECONDS  # The capture stays inside the documented target.


def test_a_tier_three_capture_of_a_large_site_also_fits_the_target() -> None:
    """The extra tier adds one wave and still fits inside 90 seconds.

    Why:
        The extra tier is the slowest capture the portal runs, so the target
        must hold for it as well. Wave two waits for wave one, so the extra tier
        costs two waves and never four.
    """
    site = FakeSite(LARGE_SITE_DEVICES)  # The site size that the target names.
    run_capture_for(site, collector.TIER_EXTRA)  # One whole tier 3 capture.
    modeled = modeled_capture_seconds(site, collector.TIER_EXTRA)  # Two waves, one after the other.
    assert modeled == CLOUD_PAGE_SECONDS * 2  # Wave one, then wave two.
    assert modeled < CAPTURE_BUDGET_SECONDS  # The extra tier stays inside the target too.


def test_the_tier_three_group_makes_exactly_four_cloud_calls() -> None:
    """The extra tier costs four cloud calls, whatever the size of the site.

    Why:
        The fan-out changes when the calls run, never how many run. A change
        that raised the count would take a larger share of the hourly cloud
        call budget than the plan allows.
    """
    site = FakeSite(LARGE_SITE_DEVICES)  # The site size that the target names.
    run_capture_for(site, collector.TIER_EXTRA)  # One whole tier 3 capture.
    assert [site.cloud_calls[read] for read in TIER_THREE_READS] == [1] * len(TIER_THREE_READS)
    assert len(TIER_THREE_READS) == TIER_THREE_CLOUD_CALLS  # The count the budget document names.


def test_a_tier_two_capture_makes_no_tier_three_cloud_call() -> None:
    """The default tier never reaches one tier 3 endpoint.

    Why:
        Tier 3 is an option that an operator turns on for one run. A tier 2
        capture that paid for it would raise the cost of every capture.
    """
    site = FakeSite(SMALL_SITE_DEVICES)  # A small site keeps the fixture fast.
    run_capture_for(site)  # One whole tier 2 capture.
    assert site.cloud_calls == Counter()  # Not one tier 3 endpoint answered.


def test_the_tier_three_group_costs_one_page_and_not_four() -> None:
    """The four tier 3 calls run at one time, so the group waits for one page.

    Why:
        Four calls that ran in order would cost four pages. The model reads the
        four tallies apart, so it reports the longest call and never the sum.
    """
    site = FakeSite(LARGE_SITE_DEVICES)  # The site size that the target names.
    run_capture_for(site, collector.TIER_EXTRA)  # One whole tier 3 capture.
    assert group_pages(site, TIER_THREE_GROUP) == 1  # One page, because the four calls share four workers.


def test_a_serial_tier_three_group_would_cost_four_times_the_cloud_time() -> None:
    """The model tells a fan-out apart from a group that waits for each call.

    Why:
        A test that can never fail proves nothing. This test measures the
        regression the fan-out removed, so a later change that puts the four
        calls back in order shows up as four times the cloud time.
    """
    site = FakeSite(LARGE_SITE_DEVICES)  # The site size that the target names.
    run_capture_for(site, collector.TIER_EXTRA)  # One whole tier 3 capture.
    fanned = group_pages(site, TIER_THREE_GROUP) * CLOUD_PAGE_SECONDS  # What the code costs today.
    assert serial_tier_three_seconds(site) == fanned * TIER_THREE_CLOUD_CALLS  # Four times, one for each call.


def test_the_local_work_of_a_large_capture_is_a_small_part_of_the_target() -> None:
    """The in-process work of a 250-device tier 2 capture takes well under a second.

    Why:
        The duration model above credits the whole budget to cloud latency. That
        credit holds only while the local work stays small. This test measures
        the local half with a fake cloud, so the number is the assembly, the
        flattening, the digest, and the store write alone. The measured work
        takes a few milliseconds on a development machine, so a tenth of the
        budget is a margin wide enough that a loaded build agent cannot fail the
        test at random. The test asserts no lower bound, because fast is never a
        fault.
    """
    site = FakeSite(LARGE_SITE_DEVICES)  # The site size that the target names.
    started = time.perf_counter()  # The monotonic clock, which no clock change can move.
    document = run_capture_for(site)  # One whole tier 2 capture against a cloud with no latency.
    elapsed = time.perf_counter() - started  # The measured local work.
    assert elapsed < CAPTURE_BUDGET_SECONDS / 10  # The local half stays a small part of the budget.
    assert len(document["device_index"]) == LARGE_SITE_DEVICES  # The timing really covered 250 devices.


def test_a_per_device_call_would_break_the_modeled_target() -> None:
    """The model fails a plan that calls the cloud once for each device.

    Why:
        A test that can never fail proves nothing. This test injects the
        regression that the target exists to catch, which is a read that grows
        with the site, and proves that the model reports a breach. Without this
        proof, a reader cannot tell whether the two tests above pass because the
        plan is good or because the model is blind.
    """
    site = FakeSite(LARGE_SITE_DEVICES)  # The site size that the target names.
    run_capture_for(site)  # One whole tier 2 capture, which fills the tally.
    site.calls["devices"] = LARGE_SITE_DEVICES  # The regression: one device call for each device.
    modeled = modeled_capture_seconds(site, collector.TIER_STANDARD)  # The same model, on the broken plan.
    assert modeled > CAPTURE_BUDGET_SECONDS  # The model catches the per-device read.

    """A changed 250-device site builds its whole comparison page well inside 3 seconds.

    Why:
        `plan.md` line 66 promises a 3 second render. This is the one timed test
        of the file, and it measures the busiest case: every device changed, so
        no digest skip helps, and all four sections are read in full. The
        measured work takes about 6 milliseconds in memory on a development
        machine, so the 3 second budget leaves a margin of more than 500 times.
        That margin is wide enough that a loaded build agent cannot fail the
        test at random, and the test still fails if a change turns the render
        into per-device work of a different order. The test asserts no lower
        bound, because a fast render is never a fault.
    """
    before = comparison_capture(LARGE_SITE_DEVICES, OLD_VERSION)  # Every device on the old firmware.
    after = comparison_capture(LARGE_SITE_DEVICES, NEW_VERSION)  # Every device on the new firmware.
    started = time.perf_counter()  # The monotonic clock, which no clock change can move.
    device_result = diff.compare_devices(before, after)  # The device half.
    client_result = compare_clients.compare_clients(before, after)  # The client half.
    totals = compare_statistics.build_statistics(device_result, client_result)  # The roll-up.
    view = render.build_view((before, after), device_result, client_result, totals)  # The whole page record.
    elapsed = time.perf_counter() - started  # The measured render time.
    assert elapsed < RENDER_BUDGET_SECONDS  # The render stays inside the documented budget.
    assert len(view.devices.rows) == LARGE_SITE_DEVICES  # The page really holds 250 device rows.
    assert view.header.skipped_sections == ()  # No section was skipped, so the timing covers the full read.
