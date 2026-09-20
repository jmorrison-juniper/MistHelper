"""Unit tests for the site lock heartbeat of the upgrade run driver.

Why:
    The site lock lives 3600 seconds and the browser alone renewed it before
    the driver took a heartbeat. An operator who closed the page during a long
    cascade lost the site while a switch still wrote firmware, and a second
    operator could then take that site. These tests hold the run thread to its
    own renewal.

    No test sleeps. A fake ticker moves the seconds by hand, so a run of 4000
    simulated seconds finishes in milliseconds.
"""

from __future__ import annotations

import inspect
import logging
import threading
from pathlib import Path
from typing import Any

import pytest

from src.upgrade_portal.runtime import lock
from src.upgrade_portal.runtime.identity import SessionOwner
from src.upgrade_portal.runtime.runs import PHASE_ORDER, PhaseState, RunRecordBuilder, RunState
from src.upgrade_portal.upgrade import driver

RUN_ID = "run-" + "b" * 32
LOCK_TOKEN = "token-that-no-log-line-may-hold"  # A value a test can search every log record for
ACTOR_EMAIL = "sam@example.com"  # A plain address that no log record may hold either
BROWSER_ID = "browser-0123456789"  # 18 URL-safe characters, inside the 16 to 128 the identity module asks for
POLL_SECONDS = 20.0  # The poll round of src/upgrade_portal/upgrade/phase_gate.py
ROUNDS_PER_PHASE = 50  # 1000 simulated seconds for one phase, so the four phases pass the 3600-second lock life


class FakeTicker:
    """Return a count of seconds that a test moves by hand.

    Why:
        The heartbeat reads one count of seconds that only moves forward. A
        test that used the real clock would have to wait 60 seconds for one
        beat. This double advances by any step at no cost.
    """

    def __init__(self, start: float = 0.0) -> None:
        """Hold the first reading.

        Args:
            start: The seconds this ticker reports before any advance.
        """
        self.seconds = start

    def __call__(self) -> float:
        """Return the present reading.

        Returns:
            The seconds this ticker holds.
        """
        return self.seconds

    def advance(self, seconds: float) -> None:
        """Move the reading forward.

        Args:
            seconds: How far forward the reading moves.
        """
        self.seconds += seconds


class RecordingRefresher:
    """Count every compare-and-extend and answer like `refresh_site_lock`.

    Why:
        A stand-in that is more permissive than the real call hides the very
        defect these tests exist to catch. This double therefore takes the
        exact three parameters of `refresh_site_lock`, returns the same whole
        number of seconds, and raises the same errors.
    """

    def __init__(self, ticker: FakeTicker) -> None:
        """Hold the ticker, so every beat carries the time it happened.

        Args:
            ticker: The clock the test moves by hand.
        """
        self.ticker = ticker
        self.keys: list[str] = []
        self.times: list[float] = []
        self.errors: list[BaseException | None] = []  # One entry for each call, in order. None means success

    def __call__(self, key: str, record: lock.LockRecord, client: Any = None) -> int:
        """Note one beat and answer the way the real refresh call answers.

        Args:
            key: The lock key.
            record: The lock record the caller holds.
            client: A lock store client. This double reaches no store.

        Returns:
            The seconds the lock now has left.

        Raises:
            BaseException: The error the test queued for this call.
        """
        self.keys.append(key)
        self.times.append(self.ticker())
        error = self.errors.pop(0) if self.errors else None
        if error is not None:
            raise error
        return lock.LOCK_TTL_SECONDS

    @property
    def gaps(self) -> list[float]:
        """Return the seconds between the run start and each later beat.

        Returns:
            One gap for each beat, measured from the beat before it.
        """
        marks = [0.0, *self.times]
        return [later - earlier for earlier, later in zip(marks[:-1], marks[1:], strict=True)]


class ZeroRefresher:
    """Answer every beat with zero seconds left.

    Why:
        The Redis script behind the refresh call answers 0 when the lock
        changed hands. A caller that read 0 as a healthy answer would hold a
        site it lost, so the heartbeat must read 0 as a lost lock.
    """

    def __init__(self) -> None:
        """Start with no call."""
        self.calls = 0

    def __call__(self, key: str, record: lock.LockRecord, client: Any = None) -> int:
        """Report that the lock has no life left.

        Args:
            key: The lock key.
            record: The lock record the caller holds.
            client: A lock store client. This double reaches no store.

        Returns:
            Always zero.
        """
        self.calls += 1
        return 0


class QuietReleaser:
    """Release a test lock without reaching Redis."""

    def __call__(self, key: str, record: lock.LockRecord, client: Any = None) -> lock.ReleaseOutcome:
        """Return a released outcome.

        Args:
            key: The lock key under test.
            record: The lock record that carries the token.
            client: A lock store client. This double reaches no store.

        Returns:
            The released outcome.
        """
        return lock.ReleaseOutcome.RELEASED  # A unit test must never reach the real Redis release path.


class FakeStore:
    """Hold one run record in memory."""

    def __init__(self) -> None:
        """Start with no record."""
        self.record: dict[str, Any] | None = None

    def read_run(self, run_id: str) -> dict[str, Any] | None:
        """Return the stored record.

        Args:
            run_id: The run key. This store holds one run only.

        Returns:
            A copy of the stored record, or None before the first write.
        """
        return None if self.record is None else dict(self.record)

    def write_run(self, run: dict[str, Any]) -> bool:
        """Store one record.

        Args:
            run: The whole record.

        Returns:
            Always True.
        """
        self.record = dict(run)
        return True


class PollingGate:
    """Settle each phase after a run of poll rounds, and never sleep.

    Why:
        `PhaseSettleGate` blocks the run thread for up to half an hour and
        calls its progress reporter once every 20 seconds. This double moves
        the fake ticker by the same step and calls the same reporter, so a
        test proves the beat rides the poll loop without waiting one real
        second.
    """

    def __init__(self, ticker: FakeTicker, sink: driver.ProgressSink, rounds: int = ROUNDS_PER_PHASE) -> None:
        """Hold the ticker, the reporter, and the length of one phase.

        Args:
            ticker: The clock the test moves by hand.
            sink: The progress reporter, which is the heartbeat under test.
            rounds: How many poll rounds one phase takes.
        """
        self.ticker = ticker
        self.sink = sink
        self.rounds = rounds
        self.calls: list[str] = []

    def settle(self, run_id: str, phase: str, targets: Any) -> driver.PhaseOutcome:
        """Poll one phase for the wanted number of rounds.

        Args:
            run_id: The run key.
            phase: The phase name.
            targets: The targets of the phase.

        Returns:
            The settled outcome of the phase.
        """
        self.calls.append(phase)
        total = len(list(targets))
        for _ in range(self.rounds):
            self.ticker.advance(POLL_SECONDS)  # The gate waited one poll round
            self.sink.report({"phase": phase, "settled": total, "total": total})
        return driver.PhaseOutcome(phase, PhaseState.SETTLED.value, settled=total, total=total)


class QuietGate:
    """Settle every phase at once and move no clock."""

    def settle(self, run_id: str, phase: str, targets: Any) -> driver.PhaseOutcome:
        """Report the phase as settled.

        Args:
            run_id: The run key.
            phase: The phase name.
            targets: The targets of the phase.

        Returns:
            The settled outcome of the phase.
        """
        total = len(list(targets))
        return driver.PhaseOutcome(phase, PhaseState.SETTLED.value, settled=total, total=total)


class RecordingCapture:
    """Return one capture key for every request."""

    def start(self, request: Any) -> str | None:
        """Return the post-check capture key.

        Args:
            request: The run key, the ordinal, and the role.

        Returns:
            The capture key this double holds.
        """
        return "cap-abc-02"


class AcceptingSubmitter:
    """Accept every submission."""

    def submit(self, record: Any) -> bool:
        """Accept the upgrade.

        Args:
            record: The run record.

        Returns:
            Always True.
        """
        return True


class RefusingSubmitter:
    """Refuse every submission, so the run fails at the first step."""

    def submit(self, record: Any) -> bool:
        """Refuse the upgrade.

        Args:
            record: The run record.

        Returns:
            Always False.
        """
        return False


class RecordingSink:
    """Note every progress report that reaches the reporter behind the beat."""

    def __init__(self) -> None:
        """Start with no report."""
        self.reports: list[Any] = []

    def report(self, progress: Any) -> None:
        """Note one report.

        Args:
            progress: The counts the settle gate reported.
        """
        self.reports.append(progress)


class FixedClock:
    """Return one fixed time, so no test waits for a real clock."""

    def now_text(self) -> str:
        """Return the fixed time stamp.

        Returns:
            One ISO 8601 time stamp in UTC.
        """
        return "2026-08-19T12:00:00+00:00"


def make_lock() -> lock.LockRecord:
    """Return one lock record with a token a test can search for.

    Returns:
        A lock record for the run under test.
    """
    owner = SessionOwner(actor_email=ACTOR_EMAIL, browser_id=BROWSER_ID)
    stamp = "2026-08-19T11:00:00+00:00"
    return lock.LockRecord(owner=owner, lock_token=LOCK_TOKEN, run_id=RUN_ID, acquired_at=stamp, refreshed_at=stamp)


def make_record() -> dict[str, Any]:
    """Return one run record that waits for the operator to confirm.

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
        "targets": [
            {"mac": "aa0000000001", "device_type": "gateway", "name": "gw1"},
            {"mac": "aa0000000002", "device_type": "switch", "name": "sw1"},
            {"mac": "aa0000000003", "device_type": "ap", "name": "ap1"},
        ],
        "phases": RunRecordBuilder.initial_phases(),
        "stop_request": None,
        "pre_capture_id": "cap-abc-01",
        "post_capture_id": None,
        "updated_at": "",
        "error": None,
    }


def make_beat(ticker: FakeTicker, refresh: Any, progress: driver.ProgressSink | None = None) -> driver.LockHeartbeat:
    """Return one heartbeat that reaches no lock store.

    Args:
        ticker: The clock the test moves by hand.
        refresh: The stand-in for the compare-and-extend call.
        progress: The reporter behind the heartbeat, when a test needs one.

    Returns:
        The heartbeat under test.
    """
    plan = driver.LockHeartbeatPlan(
        key=lock.build_key("org-1", "site-1"),
        record=make_lock(),
        refresh=refresh,
        ticker=ticker,
        progress=progress,
        release=QuietReleaser(),
    )
    return driver.LockHeartbeat(plan)


@pytest.fixture
def parts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Return a driver whose gate polls a fake clock and beats the lock.

    Why:
        Every long test needs the same wiring: a heartbeat that reaches no
        store, a gate that polls it, and a tracker under a temporary
        directory.

    Args:
        tmp_path: The temporary directory pytest supplies.
        monkeypatch: The pytest patch helper.

    Returns:
        The doubles and the driver under test.
    """
    monkeypatch.setattr(driver, "data_root", lambda: tmp_path / "data")
    ticker = FakeTicker()
    refresher = RecordingRefresher(ticker)
    beat = make_beat(ticker, refresher)
    store = FakeStore()
    gate = PollingGate(ticker, beat)
    deps = driver.RunDriverDeps(
        store=store,
        gate=gate,
        capture=RecordingCapture(),
        submit=AcceptingSubmitter(),
        clock=FixedClock(),
        heartbeat=beat,
    )
    return {"ticker": ticker, "refresher": refresher, "beat": beat, "store": store, "driver": driver.RunDriver(deps)}


class TestLongRun:
    """A run longer than the life of the lock renews the lock more than once."""

    def test_a_run_longer_than_the_lock_life_beats_more_than_once(self, parts: dict[str, Any]) -> None:
        """The headline defect: one beat per run is not enough.

        Why:
            The lock lives 3600 seconds and a long cascade runs for more than
            an hour. A run that beat once would lose the site while it wrote
            firmware.

        Args:
            parts: The doubles and the driver.
        """
        parts["driver"].run(make_record())
        assert parts["ticker"]() > lock.LOCK_TTL_SECONDS  # The simulated run passed the life of the lock
        assert len(parts["refresher"].times) > 1  # More than one beat reached the lock store

    def test_no_gap_between_two_beats_reaches_the_life_of_the_lock(self, parts: dict[str, Any]) -> None:
        """Every gap between two beats stays under the 3600-second life.

        Why:
            A count of beats alone would pass even if every beat arrived at
            the end. The gap is the property that keeps the lock alive.

        Args:
            parts: The doubles and the driver.
        """
        parts["driver"].run(make_record())
        assert max(parts["refresher"].gaps) < lock.LOCK_TTL_SECONDS

    def test_the_beat_rides_the_poll_loop_of_the_settle_gate(self, parts: dict[str, Any]) -> None:
        """One phase of 1000 seconds holds more than one beat.

        Why:
            The driver blocks inside one settle gate for up to half an hour.
            A beat that fired only between two phases would still lose a lock
            inside one long phase.

        Args:
            parts: The doubles and the driver.
        """
        parts["driver"].run(make_record())
        first_phase = [at for at in parts["refresher"].times if at <= POLL_SECONDS * ROUNDS_PER_PHASE]
        assert len(first_phase) > 1

    def test_every_beat_names_the_key_of_this_site(self, parts: dict[str, Any]) -> None:
        """Each beat carries the lock key that the run record builds.

        Args:
            parts: The doubles and the driver.
        """
        parts["driver"].run(make_record())
        assert set(parts["refresher"].keys) == {"misthelper:lock:site:org-1:site-1"}

    def test_the_run_still_reaches_the_complete_state(self, parts: dict[str, Any]) -> None:
        """The heartbeat changes no state of a healthy run.

        Args:
            parts: The doubles and the driver.
        """
        record = parts["driver"].run(make_record())
        assert record["state"] == RunState.COMPLETE.value


class TestInterval:
    """A beat inside the interval spends no round trip."""

    def test_the_first_beat_waits_one_whole_interval(self) -> None:
        """The lock was fresh at the start, so the run start beats nowhere."""
        ticker = FakeTicker()
        refresher = RecordingRefresher(ticker)
        beat = make_beat(ticker, refresher)
        beat.beat()
        assert refresher.times == []

    def test_a_beat_after_the_interval_reaches_the_lock_store(self) -> None:
        """The first beat lands one interval after the run started."""
        ticker = FakeTicker()
        refresher = RecordingRefresher(ticker)
        beat = make_beat(ticker, refresher)
        ticker.advance(float(lock.HEARTBEAT_SECONDS))
        assert beat.beat() is True
        assert refresher.times == [float(lock.HEARTBEAT_SECONDS)]

    def test_many_calls_inside_one_interval_send_one_refresh(self) -> None:
        """A caller adds a beat at every wait and never counts the seconds."""
        ticker = FakeTicker()
        refresher = RecordingRefresher(ticker)
        beat = make_beat(ticker, refresher)
        ticker.advance(float(lock.HEARTBEAT_SECONDS))
        for _ in range(5):
            beat.beat()
        assert len(refresher.times) == 1


class TestLostLock:
    """A lost lock is loud in the log and plain in the run record."""

    def test_a_lost_lock_logs_a_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        """The operator must never lose a site in silence.

        Args:
            caplog: The pytest log capture helper.
        """
        ticker = FakeTicker()
        refresher = RecordingRefresher(ticker)
        refresher.errors = [lock.LockLostError(lock.LOCK_LOST_MESSAGE)]
        beat = make_beat(ticker, refresher)
        ticker.advance(float(lock.HEARTBEAT_SECONDS))
        with caplog.at_level(logging.WARNING, logger=driver.logger.name):
            assert beat.beat() is False
        assert any("lost the site lock" in item.getMessage() for item in caplog.records)

    def test_a_lost_lock_reaches_the_run_record(self, parts: dict[str, Any]) -> None:
        """The progress page reads the run record, so the fact lands there.

        Args:
            parts: The doubles and the driver.
        """
        parts["refresher"].errors = [lock.LockLostError(lock.LOCK_LOST_MESSAGE)]
        parts["driver"].run(make_record())
        stored = parts["store"].record or {}
        assert stored[driver.LOCK_FIELD]["state"] == driver.LOCK_STATE_LOST
        assert stored[driver.LOCK_FIELD]["message"] == driver.LOCK_LOST_REASON

    def test_a_lost_lock_fails_the_run(self, parts: dict[str, Any]) -> None:
        """A run must not act on a site after it loses the site lock.

        Args:
            parts: The doubles and the driver.
        """
        parts["refresher"].errors = [lock.LockLostError(lock.LOCK_LOST_MESSAGE)]  # The next beat loses ownership.
        record = parts["driver"].run(make_record())  # The driver must fail before the next site action.
        assert record["state"] == RunState.FAILED.value  # A lost lock can never report success.
        assert record["post_capture_id"] is None  # The post-check would read the site without a lock.

    def test_the_heartbeat_asks_no_more_after_it_loses_the_lock(self, parts: dict[str, Any]) -> None:
        """A dead token cannot be renewed, so the portal stops asking.

        Args:
            parts: The doubles and the driver.
        """
        parts["refresher"].errors = [lock.LockLostError(lock.LOCK_LOST_MESSAGE)]
        parts["driver"].run(make_record())
        assert parts["beat"].stopped is True
        assert len(parts["refresher"].times) == 1

    def test_a_zero_answer_reads_as_a_lost_lock(self) -> None:
        """The Redis script answers 0 when the lock changed hands."""
        ticker = FakeTicker()
        refresher = ZeroRefresher()
        beat = make_beat(ticker, refresher)
        ticker.advance(float(lock.HEARTBEAT_SECONDS))
        assert beat.beat() is False
        assert beat.stopped is True

    def test_an_error_of_another_class_fails_the_run(self, parts: dict[str, Any]) -> None:
        """An unknown heartbeat fault must stop the next site action.

        Args:
            parts: The doubles and the driver.
        """
        parts["refresher"].errors = [RuntimeError("The lock client broke.")]  # The heartbeat treats this as loss.
        record = parts["driver"].run(make_record())  # The driver must not continue after an unknown lock fault.
        assert record["state"] == RunState.FAILED.value  # A lock fault is a run failure now.
        assert parts["beat"].stopped is True  # The heartbeat asks no more after the fault.


class TestBoundedHeartbeat:
    """A driver heartbeat cannot renew one site lock without a limit."""

    def test_an_empty_run_lock_does_not_reach_the_lock_store(self) -> None:
        """A lock with no run has no live upgrade for the driver to protect."""
        ticker = FakeTicker()  # The test controls time without a sleep.
        refresher = RecordingRefresher(ticker)  # The call count proves whether a renewal left the driver.
        empty_lock = lock.LockRecord(  # The issue record held an empty run identifier.
            owner=SessionOwner(actor_email=ACTOR_EMAIL, browser_id=BROWSER_ID),  # The owner shape stays valid.
            lock_token=LOCK_TOKEN,  # A token would be valid if a run existed.
            run_id="",  # The driver must treat this as no live run.
            acquired_at="2026-08-19T11:00:00+00:00",  # The first hold time is not enough to name a run.
            refreshed_at="2026-08-19T11:00:00+00:00",  # The last beat time is not enough to name a run.
        )
        plan = driver.LockHeartbeatPlan(  # The plan uses the same shape as production.
            key=lock.build_key("org-1", "site-1"),  # The key identifies the site under test.
            record=empty_lock,  # The no-run lock is the defect shape.
            refresh=refresher,  # The double records a forbidden renewal.
            ticker=ticker,  # The fake clock triggers the beat.
        )
        beat = driver.LockHeartbeat(plan)  # The heartbeat under test owns the no-run guard.
        ticker.advance(float(lock.HEARTBEAT_SECONDS))  # The first beat is now due.
        assert beat.beat() is False  # The heartbeat stops instead of renewing a no-run lock.
        assert refresher.times == []  # No renewal reached the lock store.

    def test_the_heartbeat_stops_after_the_configured_bound(self) -> None:
        """The driver must not push `refreshed_at` forward without a bound."""
        ticker = FakeTicker()  # The test moves past the bound at no cost.
        refresher = RecordingRefresher(ticker)  # A later call would show an over-bound renewal.
        plan = driver.LockHeartbeatPlan(  # The plan carries the measurable renewal limit.
            key=lock.build_key("org-1", "site-1"),  # The key matches the run site.
            record=make_lock(),  # A real run may renew until the bound.
            refresh=refresher,  # The double records each accepted renewal.
            ticker=ticker,  # The fake clock supplies the elapsed age.
            max_age_seconds=120,  # A small limit keeps the test focused.
        )
        beat = driver.LockHeartbeat(plan)  # The heartbeat starts its age counter now.
        ticker.advance(float(lock.HEARTBEAT_SECONDS))  # The first renewal remains inside the bound.
        assert beat.beat() is True  # A real run still keeps the lock while it is inside the bound.
        ticker.advance(float(lock.HEARTBEAT_SECONDS))  # The next due beat lands on the configured limit.
        assert beat.beat() is False  # The heartbeat stops at the bound.
        assert refresher.times == [float(lock.HEARTBEAT_SECONDS)]  # Only the in-bound renewal reached the store.


class TestALostLockFailsClosed:
    """A lost lock reports the cause and fails before the next site action.

    Why:
        The portal submits the upgrade to the cloud, and the cloud then owns the
        work. A lost lock stops the portal from touching the site again. The
        run must therefore fail with a lock reason, not continue unlocked.
    """

    def test_a_lost_lock_writes_the_failed_state(self, parts: dict[str, Any]) -> None:
        """The run state must not say complete when the lock is gone.

        Args:
            parts: The doubles and the driver.
        """
        parts["refresher"].errors = [lock.LockLostError(lock.LOCK_LOST_MESSAGE)]  # The beat loses the site.
        record = parts["driver"].run(make_record())  # The driver must stop before more site reads.
        assert record["state"] == RunState.FAILED.value  # The operator sees a failed run.
        assert (parts["store"].record or {}).get("state") == RunState.FAILED.value  # The store agrees.

    def test_a_lost_lock_writes_an_error_on_the_run(self, parts: dict[str, Any]) -> None:
        """The error field must name the lost lock.

        Args:
            parts: The doubles and the driver.
        """
        parts["refresher"].errors = [lock.LockLostError(lock.LOCK_LOST_MESSAGE)]  # The beat loses the site.
        record = parts["driver"].run(make_record())  # The driver writes a terminal failure.
        assert record["error"]["message"] == driver.LOCK_LOST_REASON  # The banner states the lock cause.

    def test_a_quiet_lock_store_fails_the_run_after_the_retry_window(self, parts: dict[str, Any]) -> None:
        """A dead lock store must not let the run continue unlocked.

        Args:
            parts: The doubles and the driver.
        """
        parts["refresher"].errors = [
            lock.LockStoreUnreachableError(lock.LOCK_STORE_DOWN_MESSAGE) for _ in range(20)
        ]  # The store stays quiet past the retry window.
        record = parts["driver"].run(make_record())  # The driver fails when the retry window closes.
        assert record["state"] == RunState.FAILED.value  # The run must not continue without proof of the lock.
        assert record["error"]["message"] == driver.LOCK_STORE_QUIET_REASON  # The reason names the lock store.

    def test_the_lost_lock_state_word_is_no_run_state(self) -> None:
        """One word must never mean a lost lock in one field and a run in another.

        Why:
            The status body carries `state` twice: once for the run and once
            inside the lock report. A word shared by the two sets would let a
            reader of either field draw the wrong conclusion.
        """
        assert driver.LOCK_STATE_LOST not in {item.value for item in RunState}

    def test_the_post_check_does_not_run_after_a_lost_lock(self, parts: dict[str, Any]) -> None:
        """A post-check must not read a site after the run lost the lock.

        Args:
            parts: The doubles and the driver.
        """
        parts["refresher"].errors = [lock.LockLostError(lock.LOCK_LOST_MESSAGE)]  # The run loses ownership.
        record = parts["driver"].run(make_record())  # The driver must fail before the post-check.
        assert record["post_capture_id"] is None  # No unlocked post-check capture starts.


class TestQuietStore:
    """A lock store that does not answer gets a retry window and no more."""

    def test_the_beat_retries_while_the_window_is_open(self) -> None:
        """contracts/site-lock.md line 137 gives the store 60 seconds."""
        ticker = FakeTicker()
        refresher = RecordingRefresher(ticker)
        refresher.errors = [lock.LockStoreUnreachableError(lock.LOCK_STORE_DOWN_MESSAGE)]
        beat = make_beat(ticker, refresher)
        ticker.advance(float(lock.HEARTBEAT_SECONDS))
        assert beat.beat() is True  # The window opened at this refusal
        assert beat.beat() is True  # The next call retried at once, and the store answered
        assert len(refresher.times) == 2

    def test_a_store_that_answers_again_keeps_the_lock(self, parts: dict[str, Any]) -> None:
        """One outage inside the window costs the run nothing.

        Args:
            parts: The doubles and the driver.
        """
        parts["refresher"].errors = [lock.LockStoreUnreachableError(lock.LOCK_STORE_DOWN_MESSAGE)]
        parts["driver"].run(make_record())
        stored = parts["store"].record or {}
        assert driver.LOCK_FIELD not in stored  # The run record names no loss, because the store came back
        assert len(parts["refresher"].times) > 1  # The beat went on after the one refusal

    def test_the_beat_gives_up_after_the_window_closes(self) -> None:
        """A dead store must never hold the run thread for ever."""
        ticker = FakeTicker()
        refresher = RecordingRefresher(ticker)
        refresher.errors = [lock.LockStoreUnreachableError(lock.LOCK_STORE_DOWN_MESSAGE) for _ in range(4)]
        beat = make_beat(ticker, refresher)
        ticker.advance(float(lock.HEARTBEAT_SECONDS))
        beat.beat()  # The window opens here
        ticker.advance(float(driver.LOCK_RETRY_WINDOW_SECONDS))
        assert beat.beat() is False  # The window closed, so the portal stops asking
        assert beat.stopped is True

    def test_a_quiet_store_names_its_own_reason_on_the_record(self, parts: dict[str, Any]) -> None:
        """The two ways to lose a lock read differently on the run record.

        Args:
            parts: The doubles and the driver.
        """
        parts["refresher"].errors = [lock.LockStoreUnreachableError(lock.LOCK_STORE_DOWN_MESSAGE) for _ in range(20)]
        parts["driver"].run(make_record())
        stored = parts["store"].record or {}
        assert stored[driver.LOCK_FIELD]["message"] == driver.LOCK_STORE_QUIET_REASON


class TestTerminalState:
    """The beat stops when the run reaches a final state."""

    def test_the_heartbeat_stops_at_the_end_of_the_run(self, parts: dict[str, Any]) -> None:
        """A run in a final state needs no lock.

        Args:
            parts: The doubles and the driver.
        """
        parts["driver"].run(make_record())
        assert parts["beat"].stopped is True

    def test_no_beat_reaches_the_store_after_the_run_ends(self, parts: dict[str, Any]) -> None:
        """A beat after the end would hold a site that nobody upgrades.

        Args:
            parts: The doubles and the driver.
        """
        parts["driver"].run(make_record())
        sent = len(parts["refresher"].times)
        parts["ticker"].advance(float(lock.HEARTBEAT_SECONDS) * 10)
        assert parts["beat"].beat() is False
        assert len(parts["refresher"].times) == sent

    def test_a_failed_run_also_stops_the_heartbeat(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A run that failed holds no site either.

        Args:
            tmp_path: The temporary directory pytest supplies.
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(driver, "data_root", lambda: tmp_path / "data")
        ticker = FakeTicker()
        beat = make_beat(ticker, RecordingRefresher(ticker))
        deps = driver.RunDriverDeps(
            store=FakeStore(),
            gate=QuietGate(),
            capture=RecordingCapture(),
            submit=RefusingSubmitter(),
            clock=FixedClock(),
            heartbeat=beat,
        )
        record = driver.RunDriver(deps).run(make_record())
        assert record["state"] == RunState.FAILED.value
        assert beat.stopped is True


class TestSafeLogging:
    """No log record holds the lock token or a plain email address."""

    def test_no_log_record_holds_the_lock_token(self, parts: dict[str, Any], caplog: pytest.LogCaptureFixture) -> None:
        """contracts/site-lock.md line 37 keeps the token out of every log.

        Args:
            parts: The doubles and the driver.
            caplog: The pytest log capture helper.
        """
        parts["refresher"].errors = [lock.LockLostError(lock.LOCK_LOST_MESSAGE)]
        with caplog.at_level(logging.DEBUG):
            parts["driver"].run(make_record())
        assert not any(LOCK_TOKEN in item.getMessage() for item in caplog.records)

    def test_no_log_record_holds_the_plain_address(
        self, parts: dict[str, Any], caplog: pytest.LogCaptureFixture
    ) -> None:
        """A work email address is personal data, so a digest goes in its place.

        Args:
            parts: The doubles and the driver.
            caplog: The pytest log capture helper.
        """
        parts["refresher"].errors = [lock.LockLostError(lock.LOCK_LOST_MESSAGE)]
        with caplog.at_level(logging.DEBUG):
            parts["driver"].run(make_record())
        assert not any(ACTOR_EMAIL in item.getMessage() for item in caplog.records)

    def test_the_warning_names_the_digest_of_the_operator(self, caplog: pytest.LogCaptureFixture) -> None:
        """An audit still joins the work of one person, without the address.

        Args:
            caplog: The pytest log capture helper.
        """
        ticker = FakeTicker()
        refresher = RecordingRefresher(ticker)
        refresher.errors = [lock.LockLostError(lock.LOCK_LOST_MESSAGE)]
        beat = make_beat(ticker, refresher)
        ticker.advance(float(lock.HEARTBEAT_SECONDS))
        with caplog.at_level(logging.WARNING, logger=driver.logger.name):
            beat.beat()
        digest = make_lock().owner.email_digest
        assert any(digest in item.getMessage() for item in caplog.records)

    def test_the_run_record_holds_no_token(self, parts: dict[str, Any]) -> None:
        """The run record reaches the store and the browser, so it stays clean.

        Args:
            parts: The doubles and the driver.
        """
        parts["refresher"].errors = [lock.LockLostError(lock.LOCK_LOST_MESSAGE)]
        parts["driver"].run(make_record())
        assert LOCK_TOKEN not in str(parts["store"].record)
        assert ACTOR_EMAIL not in str(parts["store"].record[driver.LOCK_FIELD])


class TestSeams:
    """The heartbeat fits the two seams it must fit."""

    def test_the_double_matches_the_real_refresh_signature(self) -> None:
        """A permissive stand-in would hide the defect the tests exist to catch.

        Why:
            The heartbeat passes two positional arguments and reads an int.
            A double with another shape would pass while the production call
            failed.
        """
        real = inspect.signature(lock.refresh_site_lock)
        double = inspect.signature(RecordingRefresher(FakeTicker()).__call__)
        assert list(double.parameters) == list(real.parameters)
        assert double.return_annotation == real.return_annotation

    def test_the_real_refresh_call_fits_the_named_shape(self) -> None:
        """The production call is the default of the plan, and it must fit."""
        plan = driver.LockHeartbeatPlan(key=lock.build_key("org-1", "site-1"), record=make_lock())
        assert plan.refresh is lock.refresh_site_lock
        assert plan.interval == lock.HEARTBEAT_SECONDS

    def test_the_key_comes_from_the_run_record(self) -> None:
        """The driver thread reads no session, so the record supplies the key.

        Why:
            The run thread holds no Flask request, so the signed session is
            out of reach. The organization and the site already sit on the run
            record, and the builder reads them from there.
        """
        beat = driver.lock_heartbeat(make_record(), make_lock())
        assert beat._plan.key == "misthelper:lock:site:org-1:site-1"  # WHY: The plan is the only seam.

    def test_the_key_reaches_every_refresh_call(self) -> None:
        """The key of the plan is the key the compare-and-extend call reads."""
        ticker = FakeTicker()
        refresher = RecordingRefresher(ticker)
        beat = make_beat(ticker, refresher)
        ticker.advance(float(lock.HEARTBEAT_SECONDS))  # After the build, because the build reads the clock
        beat.beat()
        assert refresher.keys == ["misthelper:lock:site:org-1:site-1"]

    def test_the_reporter_behind_the_beat_still_gets_every_round(self, tmp_path: Path) -> None:
        """The settle gate holds one reporter seat, so the beat passes it on.

        Args:
            tmp_path: The temporary directory pytest supplies.
        """
        ticker = FakeTicker()
        sink = RecordingSink()
        beat = make_beat(ticker, RecordingRefresher(ticker), progress=sink)
        gate = PollingGate(ticker, beat, rounds=3)
        gate.settle(RUN_ID, "gateways", [])
        assert len(sink.reports) == 3

    def test_the_driver_runs_without_a_heartbeat(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A caller that holds no lock still drives a run.

        Args:
            tmp_path: The temporary directory pytest supplies.
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(driver, "data_root", lambda: tmp_path / "data")
        deps = driver.RunDriverDeps(store=FakeStore(), gate=QuietGate(), capture=RecordingCapture(), clock=FixedClock())
        record = driver.RunDriver(deps).run(make_record())
        assert record["state"] == RunState.COMPLETE.value

    def test_every_phase_of_the_run_still_settles(self, parts: dict[str, Any]) -> None:
        """The beat rides the cascade and changes none of its order.

        Args:
            parts: The doubles and the driver.
        """
        record = parts["driver"].run(make_record())
        assert [str(item["name"]) for item in record["phases"]] == list(PHASE_ORDER)

    def test_the_driver_thread_writes_the_lost_lock(self, parts: dict[str, Any]) -> None:
        """One thread writes the run record, even when a beat fails.

        Args:
            parts: The doubles and the driver.
        """
        parts["refresher"].errors = [lock.LockLostError(lock.LOCK_LOST_MESSAGE)]
        thread = threading.current_thread().name
        record = parts["driver"].run(make_record())
        assert threading.current_thread().name == thread  # The run stayed on this thread, and so did the write
        assert parts["store"].record == record  # The driver thread wrote the same terminal record.
