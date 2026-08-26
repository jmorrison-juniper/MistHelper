"""Unit tests for the capture thread pool and the shutdown drain.

Why:
    The portal sizes its capture pool from a shared connection cap and drains
    the work in flight when the worker process stops. A wrong size stalls the
    portal, and a slow drain loses a capture record when Gunicorn kills the
    worker. These tests pin both rules. They patch the shared constants with
    ``monkeypatch``, so no test edits a source file and no test opens a socket.
"""

from __future__ import annotations

import atexit
import inspect
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest

from src.upgrade_portal.runtime import pools as pools_module
from src.upgrade_portal.runtime.pools import (
    CAPTURE_WORKER_TARGET,
    SHUTDOWN_TIMEOUT_SECONDS,
    CapturePool,
    CaptureWorker,
    DrainGate,
)

# WHY: Gunicorn stops a worker and kills it 30 seconds later, because
#      container/scripts/start.sh passes no --graceful-timeout. The drain must
#      return before that kill, so the test pins the relationship, not a number.
GUNICORN_GRACEFUL_TIMEOUT_SECONDS = 30.0

# WHY: The sizing code reads both settings late, inside the function body. A
#      patch on the module attribute reaches the code at call time.
CONNECTION_CAP_PATH = "src.refactors.fast_mode_constants.FAST_MODE_MAX_CONCURRENT_CONNECTIONS"
FALLBACK_THREADS_PATH = "MistHelper.FAST_MODE_FALLBACK_THREADS"

# WHY: The shipped default of the connection cap. A test that names it reads
#      better than a bare 8, and it shows which value the target of 4 answers.
DEFAULT_CONNECTION_CAP = 8

# WHY: A unit test must not wait 25 seconds. Every deadline test passes this
#      short timeout, so the suite stays fast and still proves the deadline.
SHORT_TIMEOUT_SECONDS = 0.05

# WHY: A broken barrier must fail the test in seconds, not hang the suite.
BARRIER_TIMEOUT_SECONDS = 5.0

# WHY: Enough threads to show a race, few enough to stay fast on one core.
GATE_THREAD_COUNT = 6

# WHY: Three full groups of four workers. The count divides by the target, so
#      the barrier releases even groups and no worker waits without a partner.
PROBE_ITEM_COUNT = 12


def _set_thread_settings(monkeypatch: pytest.MonkeyPatch, connection_cap: int, fallback_threads: int) -> None:
    """Publish both shared thread settings for one test.

    Why:
        ``CapturePool`` reads the connection cap and the fallback thread count
        through a late import inside the function body. A helper keeps every
        sizing test to one line of setup and names both values together.

    Args:
        monkeypatch: The pytest patch helper.
        connection_cap: Value for the shared connection cap.
        fallback_threads: Value for the fallback thread count.
    """
    monkeypatch.setattr(CONNECTION_CAP_PATH, connection_cap, raising=False)
    monkeypatch.setattr(FALLBACK_THREADS_PATH, fallback_threads, raising=False)


@pytest.fixture
def fresh_pool(monkeypatch: pytest.MonkeyPatch) -> type[CapturePool]:
    """Return ``CapturePool`` with a clean drain gate and a clean hook flag.

    Why:
        The gate and the hook flag are class-level state that lives for the
        whole process. Without a reset, one test that drains the gate makes
        every later test fail. ``monkeypatch`` restores both after the test.

    Args:
        monkeypatch: The pytest patch helper.

    Returns:
        The pool class, ready for one test.
    """
    monkeypatch.setattr(CapturePool, "GATE", DrainGate())
    monkeypatch.setattr(CapturePool, "_HOOK_INSTALLED", False)
    return CapturePool


class BudgetProbe:
    """Fake executor that starts every work item at one time and watches the budget.

    Why:
        ``ConnectionPoolExecutor.execute`` takes no worker count, so
        ``CapturePool`` wraps the caller worker in a semaphore. Only a fake
        executor that starts every work item at one time can show that the
        semaphore holds the line. The barrier makes the check exact and fast,
        because it releases a group of workers only when the group is full.
    """

    def __init__(self, party: int) -> None:
        """Build a probe that expects groups of one fixed size.

        Args:
            party: Number of workers the barrier holds before it releases them.
        """
        self._lock = threading.Lock()  # Guards the counters against a race between the threads
        self._barrier = threading.Barrier(party, timeout=BARRIER_TIMEOUT_SECONDS)  # A small budget breaks this
        self._in_flight = 0  # Number of caller workers inside the probe now
        self.calls: list[Any] = []  # Every work item the caller worker saw
        self.peak_in_flight = 0  # Highest number of caller workers seen at one time

    def execute(
        self,
        work_items: list[Any],
        worker_function: CaptureWorker,
        batch_description: str,
        retry_function: Any | None = None,
    ) -> tuple[list[Any], list[Any]]:
        """Run every work item on a thread of its own.

        Why:
            The real executor bounds its own threads. This fake removes that
            bound, so the only limit left is the portal budget under test.

        Args:
            work_items: One entry for each call group.
            worker_function: The bounded worker the pool built.
            batch_description: Plain name for the batch. The probe ignores it.
            retry_function: Retry hook. The probe ignores it.

        Returns:
            The worker results and an empty failure list, in that order.
        """
        semaphore = threading.Semaphore(len(work_items))  # The real executor supplies one shared semaphore
        with ThreadPoolExecutor(max_workers=len(work_items)) as pool:
            futures = [pool.submit(worker_function, item, semaphore) for item in work_items]
            return [future.result() for future in futures], []

    def observe(self, item: Any, connection_semaphore: threading.Semaphore) -> Any:
        """Record one busy worker, wait for a full group, and then release.

        Why:
            The barrier proves the lower bound of the budget, because a group
            forms only when the budget lets that many workers run. The peak
            counter proves the upper bound.

        Args:
            item: One work item from the caller list.
            connection_semaphore: The semaphore the executor supplies.

        Returns:
            The work item, so the executor counts the call as successful.
        """
        with self._lock:
            self._in_flight += 1
            self.peak_in_flight = max(self.peak_in_flight, self._in_flight)
            self.calls.append(item)
        self._barrier.wait()  # Blocks until a full group arrives. A small budget raises BrokenBarrierError
        with self._lock:
            self._in_flight -= 1
        return item


class TestResolveWorkerCount:
    """The pool sizing answers the shared connection cap and never returns zero.

    Why:
        A pool of zero workers accepts no work and hangs the portal forever. A
        pool larger than the target spends the hourly call quota of the cloud
        account. Both ends need a test.
    """

    def test_returns_the_target_for_the_shipped_connection_cap(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A cap of 8 gives the capture target of 4 workers.

        Why:
            This is the shipped state of the portal. A change to either number
            must fail here first, before it reaches a live capture.

        Args:
            monkeypatch: The pytest patch helper.
        """
        _set_thread_settings(monkeypatch, DEFAULT_CONNECTION_CAP, DEFAULT_CONNECTION_CAP)
        assert CapturePool.resolve_worker_count() == CAPTURE_WORKER_TARGET
        assert CAPTURE_WORKER_TARGET == 4

    def test_clamps_a_large_cap_down_to_the_target(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A cap far above the target still gives the target.

        Why:
            An operator may raise the shared cap for another workflow. The
            capture pool must keep its own smaller budget.

        Args:
            monkeypatch: The pytest patch helper.
        """
        _set_thread_settings(monkeypatch, 64, DEFAULT_CONNECTION_CAP)
        assert CapturePool.resolve_worker_count() == CAPTURE_WORKER_TARGET

    def test_a_cap_below_the_target_wins(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A cap under the target lowers the worker count to the cap.

        Why:
            The shared cap protects the cloud account. The portal must never
            run more workers than that cap allows.

        Args:
            monkeypatch: The pytest patch helper.
        """
        _set_thread_settings(monkeypatch, 2, DEFAULT_CONNECTION_CAP)
        assert CapturePool.resolve_worker_count() == 2

    def test_uses_the_fallback_when_the_cap_is_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A cap of 0 sends the sizing to the fallback thread count.

        Why:
            A missing environment value reads as 0. The fallback keeps the
            portal running instead of leaving it with no workers.

        Args:
            monkeypatch: The pytest patch helper.
        """
        _set_thread_settings(monkeypatch, 0, 2)
        assert CapturePool.resolve_worker_count() == 2

    @pytest.mark.parametrize(("connection_cap", "fallback_threads"), [(0, 0), (-3, -5), (0, -1), (1, 0)])
    def test_never_returns_zero_or_a_negative_number(
        self, monkeypatch: pytest.MonkeyPatch, connection_cap: int, fallback_threads: int
    ) -> None:
        """Every broken setting still gives at least one worker.

        Why:
            A semaphore of zero blocks the first worker forever, and the portal
            never answers again. The floor of 1 is the guard against that hang.

        Args:
            monkeypatch: The pytest patch helper.
            connection_cap: A broken value for the shared connection cap.
            fallback_threads: A broken value for the fallback thread count.
        """
        _set_thread_settings(monkeypatch, connection_cap, fallback_threads)
        worker_count = CapturePool.resolve_worker_count()
        assert worker_count >= 1
        assert worker_count <= CAPTURE_WORKER_TARGET


class TestDrainGate:
    """The gate counts the work in flight and refuses new work during a drain.

    Why:
        The shutdown handler trusts the counter. A wrong count makes the drain
        return early and the portal writes a partial capture record.
    """

    def test_enter_and_leave_move_the_count(self) -> None:
        """Two claims raise the count to 2, and two releases clear it.

        Why:
            The count is the only signal the drain reads. It must follow every
            claim and every release exactly.
        """
        gate = DrainGate()
        assert gate.enter() is True
        assert gate.enter() is True
        assert gate.in_flight() == 2
        gate.leave()
        assert gate.in_flight() == 1

    def test_leave_never_pushes_the_count_below_zero(self) -> None:
        """A release without a claim leaves the count at 0.

        Why:
            A negative count would make the drain wait forever, because the
            loop that waits watches for a count above zero.
        """
        gate = DrainGate()
        gate.leave()
        assert gate.in_flight() == 0

    def test_enter_returns_false_during_a_drain(self) -> None:
        """A drained gate refuses a new work item and holds the count at 0.

        Why:
            A work item that starts during a drain cannot finish before the
            Gunicorn kill, so the gate must stop it at the door.
        """
        gate = DrainGate()
        gate.begin_drain()
        assert gate.enter() is False
        assert gate.in_flight() == 0

    def test_the_count_stays_correct_across_several_threads(self) -> None:
        """Six threads claim a slot and the count reports 6.

        Why:
            A capture runs its call groups on several threads at one time. A
            race in the counter would lose a slot and end the drain early.
        """
        gate = DrainGate()
        with ThreadPoolExecutor(max_workers=GATE_THREAD_COUNT) as pool:
            claims = list(pool.map(lambda _: gate.enter(), range(GATE_THREAD_COUNT)))
        assert all(claims)
        assert gate.in_flight() == GATE_THREAD_COUNT

    def test_several_threads_clear_the_count(self) -> None:
        """Six threads release their slot and the count returns to 0.

        Why:
            The drain ends only at a count of zero. A lost release would hold
            the process open until the deadline passes.
        """
        gate = DrainGate()
        with ThreadPoolExecutor(max_workers=GATE_THREAD_COUNT) as pool:
            list(pool.map(lambda _: gate.enter(), range(GATE_THREAD_COUNT)))
            list(pool.map(lambda _: gate.leave(), range(GATE_THREAD_COUNT)))
        assert gate.in_flight() == 0

    def test_wait_for_idle_returns_true_when_nothing_runs(self) -> None:
        """An empty gate reports an idle state at once.

        Why:
            The common shutdown finds no work in flight. That path must return
            immediately and must not spend the timeout.
        """
        gate = DrainGate()
        started = time.monotonic()
        assert gate.wait_for_idle(SHORT_TIMEOUT_SECONDS) is True
        assert time.monotonic() - started < SHORT_TIMEOUT_SECONDS

    def test_wait_for_idle_returns_false_after_the_deadline(self) -> None:
        """Work that never ends makes the wait report a timeout.

        Why:
            The deadline is the guard against a worker that hangs. Without it
            the process stays open until Gunicorn kills it.
        """
        gate = DrainGate()
        assert gate.enter() is True
        started = time.monotonic()
        assert gate.wait_for_idle(SHORT_TIMEOUT_SECONDS) is False
        assert time.monotonic() - started >= SHORT_TIMEOUT_SECONDS

    def test_wait_for_idle_ends_when_the_last_worker_leaves(self) -> None:
        """The wait ends as soon as the last work item releases its slot.

        Why:
            The wait must react to the release, not poll a clock. A timer
            proves that the release wakes the waiting drain.
        """
        gate = DrainGate()
        assert gate.enter() is True
        releaser = threading.Timer(SHORT_TIMEOUT_SECONDS, gate.leave)
        releaser.start()
        assert gate.wait_for_idle(BARRIER_TIMEOUT_SECONDS) is True
        releaser.join()


class TestShutdown:
    """The shutdown drain returns before Gunicorn kills the worker process.

    Why:
        Gunicorn sends a stop signal and kills the worker 30 seconds later.
        A drain that runs past that point loses the capture record it was
        trying to protect.
    """

    def test_the_drain_timeout_beats_the_gunicorn_kill(self) -> None:
        """The drain budget stays under the 30 second Gunicorn default.

        Why:
            ``container/scripts/start.sh`` passes no ``--graceful-timeout``, so
            the Gunicorn default of 30 seconds applies. The inequality is the
            rule. The literal only records the value that holds it today.
        """
        assert SHUTDOWN_TIMEOUT_SECONDS < GUNICORN_GRACEFUL_TIMEOUT_SECONDS
        assert SHUTDOWN_TIMEOUT_SECONDS == 25.0

    def test_the_default_timeout_matches_the_module_constant(self) -> None:
        """A caller that names no timeout gets the module budget.

        Why:
            The atexit hook calls the drain with no argument. The default must
            carry the same 25 second budget the constant states.
        """
        parameters = inspect.signature(CapturePool.shutdown).parameters
        assert parameters["timeout_seconds"].default == SHUTDOWN_TIMEOUT_SECONDS

    def test_returns_true_when_no_work_is_in_flight(self, fresh_pool: type[CapturePool]) -> None:
        """An idle pool drains and reports success.

        Why:
            This is the normal shutdown. It must finish fast and report a
            clean drain to the caller.

        Args:
            fresh_pool: The pool class with a clean gate.
        """
        assert fresh_pool.shutdown(SHORT_TIMEOUT_SECONDS) is True

    def test_the_drain_refuses_every_later_work_item(self, fresh_pool: type[CapturePool]) -> None:
        """The gate closes for good once the drain starts.

        Why:
            A request that arrives during the stop must not start a capture it
            cannot finish.

        Args:
            fresh_pool: The pool class with a clean gate.
        """
        fresh_pool.shutdown(SHORT_TIMEOUT_SECONDS)
        assert fresh_pool.GATE.enter() is False

    def test_reports_a_timeout_and_names_the_count(
        self, fresh_pool: type[CapturePool], caplog: pytest.LogCaptureFixture
    ) -> None:
        """Work that never ends makes the drain return False and log a warning.

        Why:
            An operator needs the count of lost work items in the log, because
            the drain gives up and the process exits soon after.

        Args:
            fresh_pool: The pool class with a clean gate.
            caplog: The pytest log capture helper.
        """
        assert fresh_pool.GATE.enter() is True
        with caplog.at_level(logging.WARNING):
            drained = fresh_pool.shutdown(SHORT_TIMEOUT_SECONDS)
        assert drained is False
        assert any("Capture pool holds 1 work items" in record.getMessage() for record in caplog.records)


class TestInstallShutdownHook:
    """The shutdown hook registers one time for each worker process.

    Why:
        A second registration drains twice. The second drain finds a closed
        gate and logs a false warning, which sends an operator to a fault that
        does not exist.

        Every test here patches ``atexit.register`` on the standard library
        module, which is the exact object ``pools`` holds. No test leaves a
        real registration behind for the end of the session.
    """

    def test_the_first_call_registers_the_drain(
        self, fresh_pool: type[CapturePool], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """One call passes the drain to atexit.

        Why:
            Gunicorn owns the signal handlers, so the portal must use atexit.
            The test proves the pool registers the drain and nothing else.

        Args:
            fresh_pool: The pool class with a clean hook flag.
            monkeypatch: The pytest patch helper.
        """
        registrations: list[Any] = []
        monkeypatch.setattr(atexit, "register", registrations.append)
        fresh_pool.install_shutdown_hook()
        assert registrations == [CapturePool.shutdown]

    def test_a_second_call_registers_nothing_more(
        self, fresh_pool: type[CapturePool], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Two calls still leave one registration.

        Why:
            The application factory may run more than one time in a test or in
            a reload. The guard flag must make the second call do nothing.

        Args:
            fresh_pool: The pool class with a clean hook flag.
            monkeypatch: The pytest patch helper.
        """
        registrations: list[Any] = []
        monkeypatch.setattr(atexit, "register", registrations.append)
        fresh_pool.install_shutdown_hook()
        fresh_pool.install_shutdown_hook()
        assert len(registrations) == 1

    def test_the_guard_flag_records_the_registration(
        self, fresh_pool: type[CapturePool], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The pool remembers that it registered the hook.

        Why:
            The flag is the whole guard. A test that reads it shows why the
            second call returns early.

        Args:
            fresh_pool: The pool class with a clean hook flag.
            monkeypatch: The pytest patch helper.
        """
        monkeypatch.setattr(atexit, "register", [].append)
        fresh_pool.install_shutdown_hook()
        assert fresh_pool._HOOK_INSTALLED is True


class TestExecuteBudget:
    """The pool holds its own budget on top of the shared executor.

    Why:
        ``ConnectionPoolExecutor.execute`` accepts no worker count, so the pool
        wraps the caller worker in a semaphore. Only a test that runs the
        wrapped worker can prove the semaphore works.
    """

    def test_the_budget_holds_the_workers_at_the_target(
        self, fresh_pool: type[CapturePool], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Twelve work items on twelve threads still run four at a time.

        Why:
            The barrier proves the pool reaches four workers, and the peak
            counter proves it never passes four. Together they pin the budget.

        Args:
            fresh_pool: The pool class with a clean gate.
            monkeypatch: The pytest patch helper.
        """
        _set_thread_settings(monkeypatch, DEFAULT_CONNECTION_CAP, DEFAULT_CONNECTION_CAP)
        probe = BudgetProbe(CAPTURE_WORKER_TARGET)
        monkeypatch.setattr(pools_module, "ConnectionPoolExecutor", probe)
        successful, failed = fresh_pool.execute(list(range(PROBE_ITEM_COUNT)), probe.observe, "call groups")
        assert probe.peak_in_flight == CAPTURE_WORKER_TARGET
        assert len(successful) == PROBE_ITEM_COUNT
        assert failed == []

    def test_every_work_item_reaches_the_caller_worker(
        self, fresh_pool: type[CapturePool], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The budget delays work items but drops none of them.

        Why:
            A semaphore that leaks a slot would lose a call group, and the
            capture record would miss a section without any error.

        Args:
            fresh_pool: The pool class with a clean gate.
            monkeypatch: The pytest patch helper.
        """
        _set_thread_settings(monkeypatch, DEFAULT_CONNECTION_CAP, DEFAULT_CONNECTION_CAP)
        probe = BudgetProbe(CAPTURE_WORKER_TARGET)
        monkeypatch.setattr(pools_module, "ConnectionPoolExecutor", probe)
        fresh_pool.execute(list(range(PROBE_ITEM_COUNT)), probe.observe, "call groups")
        assert sorted(probe.calls) == list(range(PROBE_ITEM_COUNT))

    def test_a_drained_gate_skips_every_work_item(
        self, fresh_pool: type[CapturePool], monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A drain stops the caller worker before it makes a cloud call.

        Why:
            The gate check sits inside the wrapped worker, so a late work item
            never reaches the cloud after the process starts to stop.

        Args:
            fresh_pool: The pool class with a clean gate.
            monkeypatch: The pytest patch helper.
        """
        _set_thread_settings(monkeypatch, DEFAULT_CONNECTION_CAP, DEFAULT_CONNECTION_CAP)
        probe = BudgetProbe(CAPTURE_WORKER_TARGET)
        monkeypatch.setattr(pools_module, "ConnectionPoolExecutor", probe)
        fresh_pool.GATE.begin_drain()
        fresh_pool.execute([1, 2], probe.observe, "call groups")
        assert probe.calls == []
