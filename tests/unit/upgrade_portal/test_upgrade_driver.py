"""Unit tests for the upgrade run driver.

Why:
    Three rules of this feature have no second chance. The cascade order
    follows the physical dependency of a site, so a wrong order reports a
    healthy site as broken. The post-check capture starts on its own, so an
    operator who closes the page still gets the comparison. Every tracker
    path lands under the data directory, so a run started from any directory
    finds the same file.
"""

from __future__ import annotations

import json
import logging
import threading
from pathlib import Path
from typing import Any

import pytest

from src.upgrade_portal.app import config
from src.upgrade_portal.runtime.identity import SessionOwner
from src.upgrade_portal.runtime.lock import LockRecord, ReleaseOutcome
from src.upgrade_portal.runtime.runs import PHASE_ORDER, PhaseState, RunRecordBuilder, RunState
from src.upgrade_portal.upgrade import driver

RUN_ID = "run-" + "a" * 32
LOCK_KEY = "misthelper:lock:site:org-1:site-1"
LOCK_TOKEN = "token-that-no-log-line-may-hold"  # A value a test can search every log record for
ACTOR_EMAIL = "sam@example.com"  # A plain address that no log record may hold either
BROWSER_ID = "browser-0123456789"  # 18 URL-safe characters, inside the 16 to 128 the identity module asks for


class FixedClock:
    """Return one fixed time, so no test waits for a real clock."""

    def __init__(self, text: str = "2026-08-19T12:00:00+00:00") -> None:
        """Hold the text the clock returns.

        Args:
            text: The time stamp every call returns.
        """
        self.text = text

    def now_text(self) -> str:
        """Return the fixed time stamp.

        Returns:
            The text this clock holds.
        """
        return self.text


class FakeStore:
    """Hold one run record in memory and record every write.

    Why:
        The single-writer rule needs proof. This store records the thread
        that wrote each version, so a test can name every writer.
    """

    def __init__(self) -> None:
        """Start with no record and no history."""
        self.record: dict[str, Any] | None = None
        self.writers: list[str] = []
        self.states: list[str] = []
        self.inject_stop_after: int | None = None
        self.reads = 0

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return the stored record.

        Args:
            run_id: The run key. This store holds one run only.

        Returns:
            A copy of the stored record, or None before the first write.
        """
        self.reads += 1
        if self.record is None:
            return None
        copy = dict(self.record)
        if self.inject_stop_after is not None and self.reads > self.inject_stop_after:
            copy["stop_request"] = {"requested_by": "sam@example.com", "confirmation_text": "STOP"}
        return copy

    def write_run(self, run: dict[str, Any]) -> bool:
        """Store one record and note the thread that wrote it.

        Args:
            run: The whole record.

        Returns:
            Always True.
        """
        self.record = dict(run)
        self.writers.append(threading.current_thread().name)
        self.states.append(str(run.get("state", "")))
        return True

    def phase_states(self) -> dict[str, str]:
        """Return the state of each phase of the stored record.

        Returns:
            A map from the phase name to the phase state.
        """
        record = self.record or {}
        return {str(item["name"]): str(item["state"]) for item in record.get("phases", [])}


class RecordingGate:
    """Report every phase as settled and note the order of the calls."""

    def __init__(self, store: FakeStore) -> None:
        """Hold the store, so the gate can read the record at call time.

        Args:
            store: The record store the driver writes.
        """
        self.store = store
        self.calls: list[str] = []
        self.seen_before: list[dict[str, str]] = []
        self.raise_on: str | None = None
        self.state_for: dict[str, str] = {}
        self.hold: threading.Event | None = None

    def settle(self, run_id: str, phase: str, targets: Any) -> driver.PhaseOutcome:
        """Report the phase as settled.

        Why:
            The hold lets a test keep the driver thread alive without a sleep.
            The test releases the event, so the thread ends when the test says
            so and never after a wait of a fixed length.

        Args:
            run_id: The run key.
            phase: The phase name.
            targets: The targets of the phase.

        Returns:
            The outcome the test asked for. Settled by default.

        Raises:
            RuntimeError: When the test asked this phase to fail.
        """
        self.calls.append(phase)
        self.seen_before.append(self.store.phase_states())
        if self.hold is not None:
            self.hold.wait(timeout=10)
        if self.raise_on == phase:
            raise RuntimeError("The gate lost the cloud connection.")
        total = len(list(targets))
        state = self.state_for.get(phase, PhaseState.SETTLED.value)
        return driver.PhaseOutcome(phase, state, settled=total, total=total)


class RecordingCapture:
    """Record every capture request the driver starts."""

    def __init__(self, key: str | None = "cap-abc-02") -> None:
        """Hold the key this capture path returns.

        Args:
            key: The capture key, or None to report a failure.
        """
        self.key = key
        self.requests: list[dict[str, Any]] = []

    def start(self, request: Any) -> str | None:
        """Record the request and return the key.

        Args:
            request: The run key, the ordinal, and the role.

        Returns:
            The capture key this double holds.
        """
        self.requests.append(dict(request))
        return self.key


class AcceptingSubmitter:
    """Accept every submission and write one upgrade identifier."""

    def __init__(self, accept: bool = True) -> None:
        """Hold the answer this submitter returns.

        Args:
            accept: True when the cloud accepts the upgrade.
        """
        self.accept = accept
        self.calls = 0

    def submit(self, record: Any) -> bool:
        """Write one upgrade identifier on each target.

        Args:
            record: The run record.

        Returns:
            The answer this double holds.
        """
        self.calls += 1
        for target in record.get("targets", []):
            target["upgrade_id"] = "up-1"
        return self.accept


class RecordingReleaser:
    """Record every compare-and-delete the driver asks for.

    Why:
        The release must reach the lock store once for a final run state and
        never for any other state. This double counts the calls, reaches no
        Redis, and opens no socket.
    """

    def __init__(self, fault: Exception | None = None) -> None:
        """Hold the fault this releaser raises, when a test asks for one.

        Args:
            fault: The error every call raises. None releases cleanly.
        """
        self.calls: list[str] = []
        self.fault = fault

    def __call__(self, key: str, record: LockRecord, client: Any = None) -> ReleaseOutcome:
        """Record one release and answer the way the lock module answers.

        Args:
            key: The lock key.
            record: The lock record that carries the token.
            client: A lock store client. No test passes one.

        Returns:
            The outcome that names a deleted lock.

        Raises:
            Exception: The fault the test asked for.
        """
        self.calls.append(key)
        if self.fault is not None:
            raise self.fault
        return ReleaseOutcome.RELEASED


def refuse_refresh(key: str, record: LockRecord, client: Any = None) -> int:
    """Fail the test when a release test beats the site lock.

    Why:
        The default refresh of the plan is the real call, which opens a socket.
        No test of this file may reach a lock store, so a beat must fail loudly
        instead of reaching the network.

    Args:
        key: The lock key.
        record: The lock record that carries the token.
        client: A lock store client. No test passes one.

    Returns:
        Never. The call always raises.

    Raises:
        AssertionError: Always.
    """
    raise AssertionError("A release test must never beat the site lock.")


def make_lock() -> LockRecord:
    """Return one lock record with a token a test can search for.

    Returns:
        The lock record the heartbeat of a test holds.
    """
    owner = SessionOwner(actor_email=ACTOR_EMAIL, browser_id=BROWSER_ID)
    stamp = "2026-08-19T11:00:00+00:00"
    return LockRecord(owner=owner, lock_token=LOCK_TOKEN, run_id=RUN_ID, acquired_at=stamp, refreshed_at=stamp)


def with_lock(parts: dict[str, Any], release: RecordingReleaser) -> driver.RunDriver:
    """Return a driver that holds one site lock through a recording release.

    Why:
        The shared fixture builds a driver with no heartbeat, because most
        tests need none. A release test needs one, and it must keep the same
        store and the same gate, so the run still reaches a final state.

    Args:
        parts: The doubles of the shared fixture.
        release: The recorder that stands in for the compare-and-delete.

    Returns:
        The driver under test.
    """
    plan = driver.LockHeartbeatPlan(key=LOCK_KEY, record=make_lock(), refresh=refuse_refresh, release=release)
    deps = driver.RunDriverDeps(
        store=parts["store"],
        gate=parts["gate"],
        capture=parts["capture"],
        submit=parts["submitter"],
        clock=FixedClock(),
        heartbeat=driver.LockHeartbeat(plan),
    )
    return driver.RunDriver(deps)


def make_targets() -> list[dict[str, Any]]:
    """Return one target of each device family.

    Returns:
        A gateway target, a switch target, and an access point target.
    """
    return [
        {"mac": "aa0000000001", "device_type": "gateway", "name": "gw1"},
        {"mac": "aa0000000002", "device_type": "switch", "name": "sw1"},
        {"mac": "aa0000000003", "device_type": "ap", "name": "ap1"},
    ]


def make_record(targets: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Return one run record that waits for the operator to confirm.

    Args:
        targets: The device targets of the run. One of each family by default.

    Returns:
        A run record in the awaiting_confirmation state.
    """
    return {
        "_key": RUN_ID,
        "run_id": RUN_ID,
        "schema_version": 1,
        "org_id": "org-1",
        "site_id": "site-1",
        "state": RunState.AWAITING_CONFIRMATION.value,
        "targets": make_targets() if targets is None else targets,
        "phases": RunRecordBuilder.initial_phases(),
        "stop_request": None,
        "pre_capture_id": "cap-abc-01",
        "post_capture_id": None,
        "updated_at": "",
        "error": None,
    }


@pytest.fixture
def parts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Return a store, a gate, a capture path, and a driver.

    Why:
        Every test needs the same four doubles. The tracker also points at a
        temporary directory, so no test writes into the repository.

    Args:
        tmp_path: The temporary directory pytest supplies.
        monkeypatch: The pytest patch helper.

    Returns:
        The doubles and the driver under test.
    """
    monkeypatch.setattr(driver, "data_root", lambda: tmp_path / "data")
    store = FakeStore()
    gate = RecordingGate(store)
    capture = RecordingCapture()
    submitter = AcceptingSubmitter()
    deps = driver.RunDriverDeps(store=store, gate=gate, capture=capture, submit=submitter, clock=FixedClock())
    return {
        "store": store,
        "gate": gate,
        "capture": capture,
        "submitter": submitter,
        "driver": driver.RunDriver(deps),
        "tmp_path": tmp_path,
    }


class TestCascadeOrder:
    """The four gates run in the fixed physical order."""

    def test_the_gates_run_in_the_fixed_order(self, parts: dict[str, Any]) -> None:
        """The driver settles gateways, switches, access points, then clients.

        Args:
            parts: The doubles and the driver.
        """
        parts["driver"].run(make_record())
        assert parts["gate"].calls == list(PHASE_ORDER)

    def test_a_phase_starts_only_after_the_phase_before_it_settles(self, parts: dict[str, Any]) -> None:
        """Every earlier phase reads settled when the next gate opens.

        Args:
            parts: The doubles and the driver.
        """
        parts["driver"].run(make_record())
        for index, seen in enumerate(parts["gate"].seen_before):
            earlier = [seen.get(name) for name in PHASE_ORDER[:index]]
            assert earlier == [PhaseState.SETTLED.value] * index

    def test_the_run_states_follow_the_chain(self, parts: dict[str, Any]) -> None:
        """The driver writes each settling state in the cascade order.

        Why:
            One phase writes the record twice, once for the state and once for
            the result. The test collapses a repeat of the same state, so a
            return to an earlier phase still fails the test.

        Args:
            parts: The doubles and the driver.
        """
        parts["driver"].run(make_record())
        written = [state for state in parts["store"].states if state.startswith("settling_")]
        steps = [state for index, state in enumerate(written) if index == 0 or state != written[index - 1]]
        assert steps == [f"settling_{name}" for name in PHASE_ORDER]

    def test_an_empty_family_is_skipped_and_the_next_gate_opens(self, parts: dict[str, Any]) -> None:
        """A site with no gateway skips that gate and settles the switches.

        Args:
            parts: The doubles and the driver.
        """
        targets = [target for target in make_targets() if target["device_type"] != "gateway"]
        parts["driver"].run(make_record(targets))
        assert parts["gate"].calls == ["switches", "aps", "clients"]
        assert parts["store"].phase_states()["gateways"] == PhaseState.SKIPPED.value

    def test_the_client_gate_opens_after_the_access_point_gate_settles(self) -> None:
        """The client gate opens only when the access point phase completes."""
        pending = [{"name": "aps", "state": PhaseState.PENDING.value}]
        settled = [{"name": "aps", "state": PhaseState.SETTLED.value}]
        skipped = [{"name": "aps", "state": PhaseState.SKIPPED.value}]
        assert driver.client_gate_open(pending) is False
        assert driver.client_gate_open(settled) is True
        assert driver.client_gate_open(skipped) is True

    def test_the_client_gate_refuses_to_open_early(self, parts: dict[str, Any]) -> None:
        """The run fails when the access point phase never reaches settled.

        Why:
            The shut gate ends the run, and it never ends the post-check
            capture. The operator reads the failure and still holds the
            comparison data of the site.

        Args:
            parts: The doubles and the driver.
        """
        parts["gate"].state_for = {"aps": PhaseState.FAILED.value}
        final = parts["driver"].run(make_record())
        assert final["state"] == RunState.FAILED.value
        assert "access point" in final["error"]["message"]
        assert parts["capture"].requests[0]["ordinal"] == 2

    def test_a_site_with_no_access_point_still_counts_the_clients(self, parts: dict[str, Any]) -> None:
        """FR-058 skips the access point gate and leaves the client gate open.

        Why:
            A site that holds no access point is not a site whose access
            points died. The first case skips and completes. The second case
            fails. The operator must tell the two apart at a glance.

        Args:
            parts: The doubles and the driver.
        """
        targets = [target for target in make_targets() if target["device_type"] != "ap"]
        final = parts["driver"].run(make_record(targets))
        assert parts["store"].phase_states()["aps"] == PhaseState.SKIPPED.value
        assert parts["store"].phase_states()["clients"] == PhaseState.SETTLED.value
        assert final["state"] == RunState.COMPLETE.value

    def test_settling_state_refuses_an_unknown_phase(self) -> None:
        """A name that is not a cascade phase raises a plain error."""
        with pytest.raises(driver.RunDriverError, match="cascade phase"):
            driver.settling_state("printers")


class TestAutomaticPostCheck:
    """The second capture starts on its own after the client phase settles."""

    def test_the_post_check_starts_with_no_operator_action(self, parts: dict[str, Any]) -> None:
        """The driver starts exactly one post-check capture.

        Args:
            parts: The doubles and the driver.
        """
        parts["driver"].run(make_record())
        assert len(parts["capture"].requests) == 1

    def test_the_post_check_holds_ordinal_two_and_role_post(self, parts: dict[str, Any]) -> None:
        """The request names ordinal 2 and role post.

        Args:
            parts: The doubles and the driver.
        """
        parts["driver"].run(make_record())
        assert parts["capture"].requests[0] == {"run_id": RUN_ID, "ordinal": 2, "role": "post"}

    def test_the_post_check_starts_after_the_client_phase(self, parts: dict[str, Any]) -> None:
        """The client gate runs before the driver asks for the capture.

        Args:
            parts: The doubles and the driver.
        """
        parts["driver"].run(make_record())
        assert parts["gate"].calls[-1] == "clients"
        assert parts["store"].phase_states()["clients"] == PhaseState.SETTLED.value

    def test_the_capture_key_reaches_the_record(self, parts: dict[str, Any]) -> None:
        """The record holds the key of the post-check capture.

        Args:
            parts: The doubles and the driver.
        """
        final = parts["driver"].run(make_record())
        assert final["post_capture_id"] == "cap-abc-02"

    def test_the_run_reaches_complete(self, parts: dict[str, Any]) -> None:
        """A run with every gate settled ends in the complete state.

        Args:
            parts: The doubles and the driver.
        """
        final = parts["driver"].run(make_record())
        assert final["state"] == RunState.COMPLETE.value

    def test_post_check_request_names_the_run(self) -> None:
        """The request helper returns the run key, the ordinal, and the role."""
        assert driver.post_check_request("run-x") == {"run_id": "run-x", "ordinal": 2, "role": "post"}

    def test_a_capture_that_never_starts_fails_the_run(self, parts: dict[str, Any]) -> None:
        """A missing capture key moves the run to failed with a reason.

        Args:
            parts: The doubles and the driver.
        """
        parts["capture"].key = None
        final = parts["driver"].run(make_record())
        assert final["state"] == RunState.FAILED.value
        assert final["error"]["stage"] == "post_capture"


class TestTrackerPath:
    """Every tracker path lands under the data directory."""

    def test_the_tracker_lands_in_the_data_directory(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """The tracker file sits in the data directory the module resolves.

        Args:
            tmp_path: The temporary directory pytest supplies.
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(driver, "data_root", lambda: tmp_path / "data")
        path = driver.tracker_path()
        assert path.parent == tmp_path / "data"
        assert path.name == "ActiveUpgrades.json"

    def test_the_data_root_comes_from_the_module_file(self) -> None:
        """The data directory sits beside the src directory of this repository."""
        root = driver.data_root()
        assert root.is_absolute()
        assert root.name == "data"
        assert (root.parent / "src" / "upgrade_portal").is_dir()

    def test_a_directory_in_the_name_cannot_escape(self, tmp_path: Path) -> None:
        """A name that holds a directory part still lands in the data directory.

        Args:
            tmp_path: The temporary directory pytest supplies.
        """
        path = driver.tracker_path("../../escape.json", root=tmp_path)
        assert path == tmp_path / "escape.json"

    def test_the_driver_writes_the_tracker_under_the_data_directory(self, parts: dict[str, Any]) -> None:
        """The run writes the tracker into the temporary data directory.

        Args:
            parts: The doubles and the driver.
        """
        parts["driver"].run(make_record())
        written = parts["tmp_path"] / "data" / "ActiveUpgrades.json"
        rows = json.loads(written.read_text(encoding="utf-8"))
        assert rows[0]["run_id"] == RUN_ID
        assert rows[0]["upgrade_ids"] == ["up-1"]

    def test_one_run_holds_one_row(self, tmp_path: Path) -> None:
        """A second write for the same run replaces the first row.

        Args:
            tmp_path: The temporary directory pytest supplies.
        """
        record = make_record()
        driver.write_tracker(record, "t1", root=tmp_path)
        path = driver.write_tracker(record, "t2", root=tmp_path)
        rows = json.loads(path.read_text(encoding="utf-8"))
        assert len(rows) == 1
        assert rows[0]["updated_at"] == "t2"

    def test_a_damaged_tracker_does_not_stop_a_run(self, tmp_path: Path) -> None:
        """A tracker file that holds no JSON still accepts a new row.

        Args:
            tmp_path: The temporary directory pytest supplies.
        """
        (tmp_path / "ActiveUpgrades.json").write_text("not json", encoding="utf-8")
        path = driver.write_tracker(make_record(), "t1", root=tmp_path)
        rows = json.loads(path.read_text(encoding="utf-8"))
        assert len(rows) == 1


class TestSingleWriter:
    """One long-lived thread owns one run, and only that thread writes."""

    def test_a_second_start_returns_the_first_thread(self, parts: dict[str, Any]) -> None:
        """The driver never starts a second thread for one run.

        Why:
            The hold keeps the first thread inside the gateway gate, so the
            second call meets a live thread. The test releases the hold and
            never waits for a fixed length of time.

        Args:
            parts: The doubles and the driver.
        """
        hold = threading.Event()
        parts["gate"].hold = hold
        record = make_record()
        first = parts["driver"].start(record)
        second = parts["driver"].start(record)
        hold.set()
        first.join(timeout=10)
        assert first is second

    def test_only_the_driver_thread_writes_the_record(self, parts: dict[str, Any]) -> None:
        """Every write of the run record comes from the one driver thread.

        Args:
            parts: The doubles and the driver.
        """
        thread = parts["driver"].start(make_record())
        thread.join(timeout=5)
        assert set(parts["store"].writers) == {thread.name}

    def test_the_registry_releases_the_run(self, parts: dict[str, Any]) -> None:
        """The registry holds no thread after the run ends.

        Args:
            parts: The doubles and the driver.
        """
        thread = parts["driver"].start(make_record())
        thread.join(timeout=5)
        assert driver.RunDriver.active_thread(RUN_ID) is None


class TestStopAndFailure:
    """A stop and a failure both leave a record the operator can read."""

    def test_a_stop_request_ends_the_run(self, parts: dict[str, Any]) -> None:
        """A stop request written by the route moves the run to stopped.

        Args:
            parts: The doubles and the driver.
        """
        parts["store"].inject_stop_after = 3
        final = parts["driver"].run(make_record())
        assert final["state"] == RunState.STOPPED.value
        assert parts["gate"].calls != list(PHASE_ORDER)

    def test_a_stopped_run_still_takes_the_second_capture(self, parts: dict[str, Any]) -> None:
        """FR-038g still allows the post-check capture after a stop.

        Args:
            parts: The doubles and the driver.
        """
        parts["store"].inject_stop_after = 3
        parts["driver"].run(make_record())
        assert parts["capture"].requests[0]["ordinal"] == 2

    def test_the_driver_keeps_the_stop_request_of_the_route(self, parts: dict[str, Any]) -> None:
        """The driver never overwrites the field the route thread owns.

        Args:
            parts: The doubles and the driver.
        """
        parts["store"].inject_stop_after = 3
        final = parts["driver"].run(make_record())
        assert final["stop_request"]["requested_by"] == "sam@example.com"

    def test_a_gate_failure_writes_the_reason(self, parts: dict[str, Any]) -> None:
        """A gate that raises leaves the run failed with a plain sentence.

        Args:
            parts: The doubles and the driver.
        """
        parts["gate"].raise_on = "switches"
        final = parts["driver"].run(make_record())
        assert final["state"] == RunState.FAILED.value
        assert final["error"]["message"] == "The gate lost the cloud connection."

    def test_a_refused_submission_stops_the_run(self, parts: dict[str, Any]) -> None:
        """A cloud that refuses the upgrade leaves the run failed.

        Args:
            parts: The doubles and the driver.
        """
        parts["submitter"].accept = False
        final = parts["driver"].run(make_record())
        assert final["state"] == RunState.FAILED.value
        assert parts["gate"].calls == []


class ScriptedGate:
    """Return the outcome the test wrote for one phase.

    Why:
        The recording gate settles every target of a phase. A phase that
        reached its time limit brings some devices back and leaves the others
        out, so a test needs a gate that reports two different counts.
    """

    def __init__(self) -> None:
        """Start with no scripted outcome and no call history."""
        self.outcomes: dict[str, driver.PhaseOutcome] = {}
        self.calls: list[str] = []

    def settle(self, run_id: str, phase: str, targets: Any) -> driver.PhaseOutcome:
        """Return the scripted outcome of one phase.

        Args:
            run_id: The run key.
            phase: The phase name.
            targets: The targets of the phase.

        Returns:
            The scripted outcome. A settled outcome for every other phase.
        """
        self.calls.append(phase)
        total = len(list(targets))
        return self.outcomes.get(phase, driver.PhaseOutcome(phase, settled=total, total=total))


def make_two_ap_targets() -> list[dict[str, Any]]:
    """Return one switch target and two access point targets.

    Why:
        A phase that reached its time limit must hold one device that came
        back and one device that did not, so the record needs two access
        points.

    Returns:
        A switch target and two access point targets.
    """
    return [
        {"mac": "aa0000000002", "device_type": "switch", "name": "sw1"},
        {"mac": "aa0000000003", "device_type": "ap", "name": "ap1"},
        {"mac": "aa0000000004", "device_type": "ap", "name": "ap2"},
    ]


@pytest.fixture
def timeout_parts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Return the doubles and a driver whose gate follows a script.

    Args:
        tmp_path: The temporary directory pytest supplies.
        monkeypatch: The pytest patch helper.

    Returns:
        The store, the scripted gate, the capture path, and the driver.
    """
    monkeypatch.setattr(driver, "data_root", lambda: tmp_path / "data")
    store = FakeStore()
    gate = ScriptedGate()
    capture = RecordingCapture()
    submitter = AcceptingSubmitter()
    deps = driver.RunDriverDeps(store=store, gate=gate, capture=capture, submit=submitter, clock=FixedClock())
    return {"store": store, "gate": gate, "capture": capture, "driver": driver.RunDriver(deps)}


def ap_outcome(settled: int, total: int, missing: tuple[str, ...]) -> driver.PhaseOutcome:
    """Return one access point phase that reached its time limit.

    Args:
        settled: How many access points came back.
        total: How many access points the phase held.
        missing: The address of each access point that never came back.

    Returns:
        The outcome a settle gate reports at its time limit.
    """
    return driver.PhaseOutcome("aps", PhaseState.FAILED.value, settled, total, missing)


def target_states(record: dict[str, Any]) -> dict[str, Any]:
    """Return the state of each target of one record.

    Args:
        record: The run record.

    Returns:
        A map from the device address to the target state.
    """
    return {str(item["mac"]): item.get("state") for item in record["targets"]}


class TestPartlySettledPhase:
    """A phase that lost one device is not a phase that lost every device."""

    def test_the_client_gate_opens_when_some_access_points_returned(self) -> None:
        """FR-047 lets the run continue past one access point that stayed out."""
        phases = [{"name": "aps", "state": PhaseState.FAILED.value, "settled": 199, "total": 200}]
        assert driver.client_gate_open(phases) is True

    def test_the_client_gate_stays_shut_when_no_access_point_returned(self) -> None:
        """A client count of zero would report the silence of the access points."""
        phases = [{"name": "aps", "state": PhaseState.FAILED.value, "settled": 0, "total": 200}]
        assert driver.client_gate_open(phases) is False

    def test_a_phase_that_still_waits_never_opens_the_gate(self) -> None:
        """FR-057 keeps a downstream gate shut while the upstream gate waits."""
        phases = [{"name": "aps", "state": PhaseState.WAITING.value, "settled": 3, "total": 5}]
        assert driver.client_gate_open(phases) is False

    def test_partly_settled_needs_both_a_return_and_a_loss(self) -> None:
        """The answer is true only when the phase holds each of the two results."""
        timed_out = PhaseState.FAILED.value
        assert driver.phase_partly_settled({"state": timed_out, "settled": 1, "total": 2}) is True
        assert driver.phase_partly_settled({"state": timed_out, "settled": 0, "total": 2}) is False
        assert driver.phase_partly_settled({"state": timed_out, "settled": 2, "total": 2}) is False

    def test_the_not_returned_count_reads_the_two_counts(self) -> None:
        """The count tells one device that stayed out from a whole family."""
        assert driver.not_returned_count({"settled": 199, "total": 200}) == 1
        assert driver.not_returned_count({"settled": 0, "total": 200}) == 200
        assert driver.not_returned_count({"settled": 5, "total": 2}) == 0
        assert driver.not_returned_count({"settled": "bad", "total": 4}) == 4

    def test_mark_not_returned_marks_only_the_named_devices(self) -> None:
        """The mark reaches the named device and leaves the others alone."""
        record = make_record(make_two_ap_targets())
        marked = driver.mark_not_returned(record, ("AA0000000004",))
        assert marked == 1
        assert target_states(record)["aa0000000004"] == driver.TARGET_STATE_NOT_RETURNED
        assert target_states(record)["aa0000000003"] is None


class TestTimeLimitOnOneAccessPoint:
    """FR-047 marks the device that stayed out and continues with the others."""

    def test_the_run_reaches_the_post_check(self, timeout_parts: dict[str, Any]) -> None:
        """One access point of two that stayed out never loses the post-check.

        Args:
            timeout_parts: The doubles and the driver.
        """
        timeout_parts["gate"].outcomes["aps"] = ap_outcome(1, 2, ("aa0000000004",))
        final = timeout_parts["driver"].run(make_record(make_two_ap_targets()))
        assert final["state"] == RunState.COMPLETE.value
        assert timeout_parts["capture"].requests[0]["ordinal"] == 2

    def test_the_missing_access_point_carries_the_mark(self, timeout_parts: dict[str, Any]) -> None:
        """The record names the device that stayed out, not only the count.

        Args:
            timeout_parts: The doubles and the driver.
        """
        timeout_parts["gate"].outcomes["aps"] = ap_outcome(1, 2, ("aa0000000004",))
        final = timeout_parts["driver"].run(make_record(make_two_ap_targets()))
        assert target_states(final)["aa0000000004"] == driver.TARGET_STATE_NOT_RETURNED
        assert target_states(final)["aa0000000003"] is None

    def test_the_phase_entry_keeps_the_two_counts(self, timeout_parts: dict[str, Any]) -> None:
        """A later reader tells one loss of two from a phase that lost every device.

        Args:
            timeout_parts: The doubles and the driver.
        """
        timeout_parts["gate"].outcomes["aps"] = ap_outcome(1, 2, ("aa0000000004",))
        final = timeout_parts["driver"].run(make_record(make_two_ap_targets()))
        entry = next(item for item in final["phases"] if item["name"] == "aps")
        assert (entry["settled"], entry["total"]) == (1, 2)
        assert driver.not_returned_count(entry) == 1

    def test_the_client_phase_still_runs(self, timeout_parts: dict[str, Any]) -> None:
        """The wireless clients of the access points that returned still count.

        Args:
            timeout_parts: The doubles and the driver.
        """
        timeout_parts["gate"].outcomes["aps"] = ap_outcome(1, 2, ("aa0000000004",))
        timeout_parts["driver"].run(make_record(make_two_ap_targets()))
        assert timeout_parts["gate"].calls == ["switches", "aps", "clients"]

    def test_the_client_phase_settles_as_usual(self, timeout_parts: dict[str, Any]) -> None:
        """One access point of many that stayed out never fails the client phase.

        Why:
            This is the case the client gate protects. A guard that shut the
            gate on any loss would throw away the count of a whole site for
            one missing device.

        Args:
            timeout_parts: The doubles and the driver.
        """
        timeout_parts["gate"].outcomes["aps"] = ap_outcome(1, 2, ("aa0000000004",))
        timeout_parts["driver"].run(make_record(make_two_ap_targets()))
        assert timeout_parts["store"].phase_states()["clients"] == PhaseState.SETTLED.value


class TestEveryAccessPointStaysOut:
    """A phase that brought nothing back never opens the gate below it.

    Why:
        The shut gate stops the count of the wireless clients only. It never
        stops the post-check capture, and the run reports failed and never
        complete.
    """

    def test_the_run_fails_with_a_plain_sentence(self, timeout_parts: dict[str, Any]) -> None:
        """FR-057 holds the client gate shut while no access point is present.

        Args:
            timeout_parts: The doubles and the driver.
        """
        timeout_parts["gate"].outcomes["aps"] = ap_outcome(0, 2, ("aa0000000003", "aa0000000004"))
        final = timeout_parts["driver"].run(make_record(make_two_ap_targets()))
        assert final["state"] == RunState.FAILED.value
        assert "access point" in final["error"]["message"]

    def test_the_client_gate_never_runs(self, timeout_parts: dict[str, Any]) -> None:
        """A client count of zero would report the access points and not the clients.

        Args:
            timeout_parts: The doubles and the driver.
        """
        timeout_parts["gate"].outcomes["aps"] = ap_outcome(0, 2, ("aa0000000003", "aa0000000004"))
        timeout_parts["driver"].run(make_record(make_two_ap_targets()))
        assert timeout_parts["gate"].calls == ["switches", "aps"]

    def test_every_missing_access_point_still_carries_the_mark(self, timeout_parts: dict[str, Any]) -> None:
        """A run that failed still names each device the operator must chase.

        Args:
            timeout_parts: The doubles and the driver.
        """
        timeout_parts["gate"].outcomes["aps"] = ap_outcome(0, 2, ("aa0000000003", "aa0000000004"))
        final = timeout_parts["driver"].run(make_record(make_two_ap_targets()))
        marks = target_states(final)
        assert marks["aa0000000003"] == driver.TARGET_STATE_NOT_RETURNED
        assert marks["aa0000000004"] == driver.TARGET_STATE_NOT_RETURNED

    def test_the_post_check_capture_still_runs(self, timeout_parts: dict[str, Any]) -> None:
        """A site whose access points all stayed out still gets the second capture.

        Why:
            This is the case where the comparison matters most. The capture
            holds the switch versions, the switch state, the access point
            state, and the wired clients, and it is the evidence of the
            failure.

        Args:
            timeout_parts: The doubles and the driver.
        """
        timeout_parts["gate"].outcomes["aps"] = ap_outcome(0, 2, ("aa0000000003", "aa0000000004"))
        final = timeout_parts["driver"].run(make_record(make_two_ap_targets()))
        assert timeout_parts["capture"].requests == [{"run_id": RUN_ID, "ordinal": 2, "role": "post"}]
        assert final["post_capture_id"] == "cap-abc-02"

    def test_the_client_phase_reads_failed(self, timeout_parts: dict[str, Any]) -> None:
        """A site whose access points died is not a site that holds no access point.

        Why:
            FR-058 gives ``skipped`` to a family the site does not hold. The
            operator must tell that case from a family that died, so this
            phase reads failed and never skipped.

        Args:
            timeout_parts: The doubles and the driver.
        """
        timeout_parts["gate"].outcomes["aps"] = ap_outcome(0, 2, ("aa0000000003", "aa0000000004"))
        timeout_parts["driver"].run(make_record(make_two_ap_targets()))
        assert timeout_parts["store"].phase_states()["clients"] == PhaseState.FAILED.value

    def test_the_failure_names_the_upgrade_stage(self, timeout_parts: dict[str, Any]) -> None:
        """The operator reads that the upgrade lost the devices, not the capture.

        Why:
            The driver reads the reason text to pick the stage. A reason that
            named the post-check would send the operator to the capture path,
            which ran well and which holds good data.

        Args:
            timeout_parts: The doubles and the driver.
        """
        timeout_parts["gate"].outcomes["aps"] = ap_outcome(0, 2, ("aa0000000003", "aa0000000004"))
        final = timeout_parts["driver"].run(make_record(make_two_ap_targets()))
        assert final["state"] != RunState.COMPLETE.value
        assert final["error"]["stage"] == "upgrade"


class TestSiteLockRelease:
    """A final run state gives the site back, and no other state does."""

    def test_a_complete_run_releases_the_site_lock(self, parts: dict[str, Any]) -> None:
        """The site returns to the pool when the run completes.

        Why:
            contracts/site-lock.md line 105 names `complete` as a release point.
            A lock left to expire holds the site for the rest of its
            3600-second life, and the next operator waits an hour for a site
            that nobody upgrades.

        Args:
            parts: The doubles and the driver.
        """
        release = RecordingReleaser()
        record = make_record()

        final = with_lock(parts, release).run(record)

        assert final["state"] == RunState.COMPLETE.value
        assert release.calls == [LOCK_KEY]

    def test_a_stopped_run_releases_the_site_lock(self, parts: dict[str, Any]) -> None:
        """The site returns to the pool when the operator stops the run.

        Why:
            contracts/site-lock.md line 105 names `stopped` as a release point.

        Args:
            parts: The doubles and the driver.
        """
        parts["store"].inject_stop_after = 3
        release = RecordingReleaser()

        final = with_lock(parts, release).run(make_record())

        assert final["state"] == RunState.STOPPED.value
        assert release.calls == [LOCK_KEY]

    def test_a_failed_run_releases_the_site_lock(self, parts: dict[str, Any]) -> None:
        """The site returns to the pool when the run fails.

        Why:
            contracts/site-lock.md line 105 names `failed` as a release point. A
            run that died still holds the site until something gives it back.

        Args:
            parts: The doubles and the driver.
        """
        parts["gate"].raise_on = "switches"
        release = RecordingReleaser()

        final = with_lock(parts, release).run(make_record())

        assert final["state"] == RunState.FAILED.value
        assert release.calls == [LOCK_KEY]

    def test_a_run_short_of_a_final_state_keeps_the_site_lock(self, parts: dict[str, Any]) -> None:
        """A run that is still working never gives the site back.

        Why:
            contracts/site-lock.md line 106 keeps the lock when a browser
            closes, because the run continues. A release at any other state
            would hand a site to a second operator while the first run still
            writes firmware to a switch.

        Args:
            parts: The doubles and the driver.
        """
        release = RecordingReleaser()
        runner = with_lock(parts, release)
        record = make_record()
        record["state"] = RunState.UPGRADE_SUBMITTING.value

        runner._free_lock(record)

        assert release.calls == []

    def test_the_release_waits_for_the_end_of_the_cascade(self, parts: dict[str, Any]) -> None:
        """No phase of a live run gives the site back.

        Why:
            The site must stay held for the whole cascade. This test holds the
            run inside a settle gate, which is the exact moment a closed
            browser would otherwise drop the lock.

        Args:
            parts: The doubles and the driver.
        """
        parts["gate"].hold = threading.Event()
        release = RecordingReleaser()
        thread = with_lock(parts, release).start(make_record())

        assert release.calls == []

        parts["gate"].hold.set()
        thread.join(timeout=10)
        assert release.calls == [LOCK_KEY]

    def test_a_quiet_lock_store_leaves_the_run_finished(
        self,
        parts: dict[str, Any],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A release that fails never fails the run, and never prints a secret.

        Why:
            The run already ended, so a lock store fault must not change the
            state the operator reads. The message of a store fault can carry a
            connection string, so the log line names the class alone.

        Args:
            parts: The doubles and the driver.
            caplog: The pytest log recorder.
        """
        fault = ConnectionError("redis://portal:hunter2@lock-store.internal:6379/0")
        release = RecordingReleaser(fault=fault)

        with caplog.at_level(logging.WARNING, logger="src.upgrade_portal.upgrade.driver"):
            final = with_lock(parts, release).run(make_record())

        assert final["state"] == RunState.COMPLETE.value
        assert "ConnectionError" in caplog.text
        assert "hunter2" not in caplog.text
        assert LOCK_TOKEN not in caplog.text

    def test_a_run_with_no_lock_token_names_the_site_it_still_holds(
        self,
        parts: dict[str, Any],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A run that holds no lock token must report the site that stays held.

        Why:
            The heartbeat carries the key and the token, so a run built without
            one can release nothing. No other line reports that wait, so an
            operator would otherwise read a finished run beside a locked site
            with no stated cause.

        Args:
            parts: The doubles and the driver, which carry no heartbeat.
            caplog: The pytest log recorder.
        """
        record = make_record()
        record["state"] = RunState.COMPLETE.value

        with caplog.at_level(logging.WARNING, logger="src.upgrade_portal.upgrade.driver"):
            parts["driver"]._free_lock(record)

        assert RUN_ID in caplog.text
        assert LOCK_TOKEN not in caplog.text

    def test_a_live_run_with_no_lock_token_writes_no_warning(
        self,
        parts: dict[str, Any],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """A run that is still working reports no held site.

        Why:
            Every live run holds its site on purpose. A warning at each phase
            would fill the log with a fault that is not one, and would bury the
            single line that reports a real strand.

        Args:
            parts: The doubles and the driver, which carry no heartbeat.
            caplog: The pytest log recorder.
        """
        record = make_record()
        record["state"] = RunState.UPGRADE_SUBMITTING.value

        with caplog.at_level(logging.WARNING, logger="src.upgrade_portal.upgrade.driver"):
            parts["driver"]._free_lock(record)

        assert caplog.text == ""


# WHY: A typo that an operator could write for the automatic mode. The seam must
# read it as automatic, because a skipped capture leaves no evidence of the
# upgrade.
MISTYPED_MODE = "atuomatic"


def with_mode(parts: dict[str, Any], mode: str) -> driver.RunDriver:
    """Return a driver that carries one post-check mode.

    Why:
        The shared fixture builds a driver at the default mode, which is what
        most tests need. A mode test keeps the same store, the same gate, and
        the same capture path, so the run still reaches a final state.

    Args:
        parts: The doubles of the shared fixture.
        mode: The post-check mode of the driver.

    Returns:
        The driver under test.
    """
    deps = driver.RunDriverDeps(
        store=parts["store"],
        gate=parts["gate"],
        capture=parts["capture"],
        submit=parts["submitter"],
        clock=FixedClock(),
        post_check_mode=mode,
    )
    return driver.RunDriver(deps)


class TestPostCheckModeSeam:
    """The second capture stays automatic, and one setting can hold it.

    Why:
        The customer chose the automatic capture and asked for a manual switch
        under the hood. The first three tests hold the behavior of today. They
        fail on the day somebody changes the default, which is the whole point
        of this class.
    """

    def test_the_default_mode_is_automatic(self) -> None:
        """A dependency record with no mode argument carries the automatic mode.

        Why:
            This is the regression guard on the behavior of today. A change to
            ``DEFAULT_POST_CHECK_MODE`` fails here first.
        """
        store = FakeStore()
        deps = driver.RunDriverDeps(store=store, gate=RecordingGate(store), capture=RecordingCapture())
        assert driver.DEFAULT_POST_CHECK_MODE == driver.POST_CHECK_AUTOMATIC
        assert deps.post_check_mode == "automatic"

    def test_the_default_mode_starts_the_capture(self, parts: dict[str, Any]) -> None:
        """A run with no setting starts the second capture, as it does today.

        Args:
            parts: The doubles and the driver.
        """
        parts["driver"].run(make_record())
        assert parts["capture"].requests == [{"run_id": RUN_ID, "ordinal": 2, "role": "post"}]

    def test_the_default_mode_marks_no_capture_as_pending(self, parts: dict[str, Any]) -> None:
        """The automatic path writes the capture key and a false pending mark.

        Why:
            A reader of the record must never find a stale mark from an earlier
            mode. The mark reads false whenever the driver started the capture.

        Args:
            parts: The doubles and the driver.
        """
        final = parts["driver"].run(make_record())
        assert final["post_capture_pending"] is False
        assert final["post_capture_id"] == "cap-abc-02"

    def test_the_manual_mode_starts_no_capture(self, parts: dict[str, Any]) -> None:
        """The manual mode marks the record and calls no capture starter.

        Args:
            parts: The doubles and the driver.
        """
        final = with_mode(parts, driver.POST_CHECK_MANUAL).run(make_record())
        assert parts["capture"].requests == []
        assert final["post_capture_pending"] is True

    def test_the_manual_mode_still_reaches_the_final_state(self, parts: dict[str, Any]) -> None:
        """A held capture changes no step of the state machine.

        Why:
            The seam must add no run state. A run that stopped at the capture
            step would leave the site locked and the page waiting.

        Args:
            parts: The doubles and the driver.
        """
        final = with_mode(parts, driver.POST_CHECK_MANUAL).run(make_record())
        assert final["state"] == RunState.COMPLETE.value
        assert parts["store"].phase_states()["clients"] == PhaseState.SETTLED.value

    def test_an_unknown_mode_behaves_like_the_automatic_mode(self, parts: dict[str, Any]) -> None:
        """A typo in the setting still starts the second capture.

        Why:
            The capture is the evidence that the upgrade worked. A typo must
            never take that evidence away in silence.

        Args:
            parts: The doubles and the driver.
        """
        final = with_mode(parts, MISTYPED_MODE).run(make_record())
        assert parts["capture"].requests == [{"run_id": RUN_ID, "ordinal": 2, "role": "post"}]
        assert final["post_capture_pending"] is False
        assert final["state"] == RunState.COMPLETE.value

    def test_a_stop_at_the_default_mode_still_takes_the_capture(self, parts: dict[str, Any]) -> None:
        """FR-038g keeps the second capture of a stopped run at the default mode.

        Args:
            parts: The doubles and the driver.
        """
        parts["store"].inject_stop_after = 3
        final = parts["driver"].run(make_record())
        assert parts["capture"].requests[0]["ordinal"] == 2
        assert final["state"] == RunState.STOPPED.value

    def test_a_stop_honors_the_manual_mode(self, parts: dict[str, Any]) -> None:
        """The stop path reads the same mode as the finish path.

        Why:
            Both paths call one method. A guard on the finish path alone would
            start a capture that the operator asked to start by hand.

        Args:
            parts: The doubles and the driver.
        """
        parts["store"].inject_stop_after = 3
        final = with_mode(parts, driver.POST_CHECK_MANUAL).run(make_record())
        assert parts["capture"].requests == []
        assert final["state"] == RunState.STOPPED.value
        assert final["post_capture_pending"] is True

    def test_the_held_capture_writes_one_log_line(
        self,
        parts: dict[str, Any],
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """The log names the run and the mode, and it holds no other value.

        Args:
            parts: The doubles and the driver.
            caplog: The pytest log recorder.
        """
        with caplog.at_level(logging.INFO, logger="src.upgrade_portal.upgrade.driver"):
            with_mode(parts, driver.POST_CHECK_MANUAL).run(make_record())
        held = [line for line in caplog.text.splitlines() if "holds the post-check capture" in line]
        assert len(held) == 1
        assert RUN_ID in held[0]
        assert driver.POST_CHECK_MANUAL in held[0]
        assert ACTOR_EMAIL not in caplog.text

    def test_the_settings_module_names_the_same_modes(self) -> None:
        """The settings module and the driver hold one text for each mode.

        Why:
            The settings module imports the standard library only, so it names
            the two modes again instead of importing the driver. This test is
            the guard against a drift between the two files.
        """
        assert config.POST_CHECK_AUTOMATIC == driver.POST_CHECK_AUTOMATIC
        assert config.POST_CHECK_MANUAL == driver.POST_CHECK_MANUAL
        assert config.DEFAULT_POST_CHECK_MODE == driver.DEFAULT_POST_CHECK_MODE
