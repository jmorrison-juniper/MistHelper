"""Thread pool sizing and the shutdown drain for the upgrade capture portal.

Why:
    A capture fans out several cloud call groups at one time, and the cloud
    enforces a call budget. The portal must therefore bound the work in flight.
    The portal also runs under Gunicorn with the ``gthread`` worker class, so it
    must let the work in flight finish when the worker process stops. One
    module owns both rules, so no caller builds a second pool.

    The module holds two shapes, because a capture holds two shapes of work.
    ``CapturePool`` starts a batch of call groups from a request thread and
    reaches the shared ``ConnectionPoolExecutor``. ``BoundedFanOut`` runs a
    handful of named blocking calls that already sit inside one work item. The
    four tier 3 cloud calls of one call group are such a set. Both shapes bound
    the work in flight to ``CAPTURE_WORKER_TARGET``, so neither one raises the
    share of the hourly cloud call budget that a capture holds.

    ``documentation/python-parallelism-matrix.md`` decides the tool. Every call
    of this module waits on a network, so the bottleneck is input and output
    and not the processor. The matrix answers that case with a thread pool. It
    warns that a process pool would pay a pickle cost for a payload that a
    thread shares for free.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

import atexit  # Run the drain when the worker process exits normally
import logging  # Action logging per Constitution VII
import threading  # Condition and Semaphore for the budget and the drain gate
import time  # Monotonic clock for the drain deadline
from collections.abc import Callable, Mapping  # Worker shape plus the named call set of a fan-out
from concurrent.futures import Future, ThreadPoolExecutor  # Bounded fan-out of blocking calls
from typing import Any, ClassVar, Final  # Loose payload typing plus class-level state

from src.refactors.connection_pool_executor import ConnectionPoolExecutor  # The one pool the repository owns

# WHAT: number of capture call groups the portal runs at one time.
# WHY: the threading model in plan.md gives capture collection and settle-gate
#      polling 4 workers each. The shared executor sizes its own threads from
#      FAST_MODE_MAX_CONCURRENT_CONNECTIONS (src/refactors/fast_mode_constants.py:21),
#      which defaults to 8, so the portal holds a smaller budget on top of it.
CAPTURE_WORKER_TARGET: Final[int] = 4

# WHAT: seconds the drain waits for the work already in flight.
# WHY: Gunicorn asks a worker to stop and kills it 30 seconds later, because
#      container/scripts/start.sh:73-80 sets no --graceful-timeout and the
#      default is 30. The settle gate polls once every 20 seconds. A 25 second
#      drain lets one poll round finish and still returns before the kill.
SHUTDOWN_TIMEOUT_SECONDS: Final[float] = 25.0

# WHAT: the worker shape the shared executor calls.
# WHY: src/refactors/connection_pool_executor.py:178 submits
#      (item, connection_semaphore), so every worker takes exactly those two.
CaptureWorker = Callable[[Any, threading.Semaphore], Any]

# WHAT: the shape of one call inside a fan-out.
# WHY: a fan-out call already holds every argument it needs, because the caller
#      binds them before it hands the call over. The pool then needs no
#      knowledge of the cloud, and a test passes a plain function.
FanOutCall = Callable[[], Any]

# WHAT: the prefix of every fan-out thread name.
# WHY: a thread dump during a stalled capture must name the owner of the wait.
#      Without a prefix the dump shows ``ThreadPoolExecutor-3_1`` and no reader
#      can tell a portal thread from a thread of the wider application.
FANOUT_THREAD_PREFIX: Final[str] = "portal-fanout"


class DrainGate:
    """Counts the capture work in flight and refuses new work during a drain.

    Why:
        A worker process that exits while a capture runs leaves a partial
        record. The gate lets the shutdown handler wait for the work in flight
        without a busy loop, and it stops any later work item from starting.
    """

    def __init__(self) -> None:
        """Build an open gate that holds no work.

        Why:
            The portal builds one gate for each process. A test may assign a
            new gate to ``CapturePool.GATE`` to start from a clean state.
        """
        self._condition = threading.Condition()  # Guards the counters and wakes a waiting drain
        self._in_flight = 0  # Number of work items that run now
        self._draining = False  # True after the process asks for a shutdown

    def enter(self) -> bool:
        """Claim one slot for a work item.

        Returns:
            True when the caller may run the work item, False during a drain.
        """
        with self._condition:  # Hold the lock while the counters change
            if self._draining:  # A drain refuses every later work item
                return False  # Tell the caller to skip this work item
            self._in_flight += 1  # Record one more work item in flight
            return True  # The caller may run the work item

    def leave(self) -> None:
        """Release one slot and wake a waiting drain."""
        with self._condition:  # Hold the lock while the counter changes
            self._in_flight = max(0, self._in_flight - 1)  # An unbalanced call must not push the count below zero
            self._condition.notify_all()  # Wake the drain, which may now see an idle gate

    def begin_drain(self) -> None:
        """Refuse every later work item."""
        with self._condition:  # Hold the lock while the flag changes
            self._draining = True  # Close the gate for every later work item
            self._condition.notify_all()  # Wake a waiter that watches the flag

    def in_flight(self) -> int:
        """Report how many work items run now.

        Returns:
            The count of work items between ``enter`` and ``leave``.
        """
        with self._condition:  # Read the counter under the lock
            return self._in_flight  # Report the current count

    def wait_for_idle(self, timeout_seconds: float) -> bool:
        """Wait until no work item runs, or until the timeout passes.

        Why:
            The wait carries a deadline, so a worker that never returns cannot
            hold the process open past the Gunicorn kill.

        Args:
            timeout_seconds: Longest wait the caller accepts, in seconds.

        Returns:
            True when the gate reached an idle state inside the timeout.
        """
        deadline = time.monotonic() + timeout_seconds  # Fixed deadline. A spurious wake cannot extend it
        with self._condition:  # The condition wait needs the lock
            while self._in_flight > 0:  # Work still runs
                remaining = deadline - time.monotonic()  # Time left before the caller gives up
                if remaining <= 0:  # The deadline passed. Never block forever
                    return False  # Report the timeout to the caller
                self._condition.wait(remaining)  # Sleep until a worker leaves or the time runs out
            return True  # No work item runs now


class CapturePool:
    """Runs the capture call groups through the shared executor and drains them on shutdown.

    Why:
        ``ConnectionPoolExecutor`` sizes its own threads from the connection
        cap, which is larger than the portal needs. The portal wraps that
        executor with a smaller budget, so a capture keeps its share of the
        5000 call hourly quota at ``src/utils/rate_limiting.py:56``. It also
        wraps the executor with a drain gate, so a worker exit finishes the
        work in flight.
    """

    GATE: ClassVar[DrainGate] = DrainGate()  # One gate for each process. Assign a new gate to reset the state
    _HOOK_INSTALLED: ClassVar[bool] = False  # Guards against a second atexit registration

    @staticmethod
    def _read_thread_settings() -> tuple[int, int]:
        """Read the connection cap and the fallback thread count from the shared settings.

        Why:
            ``MistHelper`` imports from ``src``, so a top-level import here
            builds a cycle and the process fails to start. The late-binding
            import inside this function body copies the idiom at
            ``src/refactors/connection_pool_executor.py:46``. By the time this
            method runs, MistHelper is fully loaded and both values are
            readable.

        Returns:
            The connection cap and the fallback thread count, in that order.
        """
        import MistHelper  # Late-binding import. MistHelper is fully loaded by the time methods run
        from src.refactors.fast_mode_constants import (
            FAST_MODE_MAX_CONCURRENT_CONNECTIONS,  # Cap on simultaneous API connections
        )

        connection_cap = int(FAST_MODE_MAX_CONCURRENT_CONNECTIONS)  # Shared cap on simultaneous API connections
        fallback_threads = int(MistHelper.FAST_MODE_FALLBACK_THREADS)  # Thread count when the cap is absent
        return connection_cap, fallback_threads  # Bundle both settings for the sizing step

    @staticmethod
    def resolve_worker_count() -> int:
        """Report how many capture call groups the portal runs at one time.

        Returns:
            A count of 1 or more that never rises above ``CAPTURE_WORKER_TARGET``.
        """
        logging.debug("[CAPTURE-POOL] Resolving the worker count")  # BEFORE: sizing starts
        connection_cap, fallback_threads = CapturePool._read_thread_settings()  # Late-bound shared settings
        ceiling = connection_cap if connection_cap > 0 else fallback_threads  # An absent cap falls back
        worker_count = max(1, min(CAPTURE_WORKER_TARGET, ceiling))  # Never zero, never above the target or the cap
        logging.info("* Capture pool: %s workers, connection cap %s", worker_count, ceiling)  # Announce the size
        return worker_count  # The caller builds a semaphore of this size

    @staticmethod
    def _build_bounded_worker(worker_function: CaptureWorker, budget: threading.Semaphore) -> CaptureWorker:
        """Wrap one worker so it holds a budget slot and reports to the drain gate.

        Args:
            worker_function: Takes one work item and one connection semaphore.
            budget: Bounds how many work items run at one time.

        Returns:
            A worker with the two-argument shape the shared executor calls.
        """

        def bounded(item: Any, connection_semaphore: threading.Semaphore) -> Any:
            """Run one work item under the portal budget and the drain gate.

            Args:
                item: One work item from the caller list.
                connection_semaphore: The semaphore the shared executor supplies.

            Returns:
                The worker result, or None when the gate drains.
            """
            if not CapturePool.GATE.enter():  # A drain refuses this work item
                logging.info("* Capture pool drains. The portal skips one work item")  # State the reason
                return None  # The executor counts a falsy result as failed, which is the honest outcome
            try:  # The gate slot must return on every path
                with budget:  # Hold one portal slot for the whole call
                    return worker_function(item, connection_semaphore)  # The caller owns the cloud call
            finally:  # Runs after a return and after an exception
                CapturePool.GATE.leave()  # Release the gate slot

        return bounded  # The executor calls this with (item, connection_semaphore)

    @staticmethod
    def execute(
        work_items: list[Any],
        worker_function: CaptureWorker,
        batch_description: str = "call groups",
        retry_function: Any | None = None,
    ) -> tuple[list[Any], list[Any]]:
        """Run every work item through the shared executor under the portal budget.

        Args:
            work_items: One entry for each call group.
            worker_function: Takes one work item and one connection semaphore.
            batch_description: Plain name for the progress line and for the logs.
            retry_function: Takes the failed items and the semaphore. Returns two lists.

        Returns:
            The successful results and the failed work items, in that order.
        """
        logging.info("[CAPTURE-POOL] Starting %s work items (%s)", len(work_items), batch_description)  # BEFORE
        budget = threading.Semaphore(CapturePool.resolve_worker_count())  # Bound the work in flight
        bounded_worker = CapturePool._build_bounded_worker(worker_function, budget)  # Add the budget and the gate
        successful, failed = ConnectionPoolExecutor.execute(  # The one pool the repository owns
            work_items, bounded_worker, batch_description, retry_function
        )
        logging.debug("[CAPTURE-POOL] Finished: %s successful, %s failed", len(successful), len(failed))  # AFTER
        return successful, failed  # Both lists, so the caller can report the failures

    @staticmethod
    def shutdown(timeout_seconds: float = SHUTDOWN_TIMEOUT_SECONDS) -> bool:
        """Refuse new work and wait for the work already in flight.

        Why:
            Gunicorn asks a worker to stop and kills it a short time later. The
            drain must finish before that kill, so it always carries a
            deadline and never blocks forever.

        Args:
            timeout_seconds: Longest wait, in seconds.

        Returns:
            True when no work was in flight before the timeout passed.
        """
        logging.info("[CAPTURE-POOL] Draining the pool, timeout %s seconds", timeout_seconds)  # BEFORE
        CapturePool.GATE.begin_drain()  # Refuse every later work item
        drained = CapturePool.GATE.wait_for_idle(timeout_seconds)  # Wait, but never past the deadline
        if not drained:  # The deadline passed while work still ran
            logging.warning(  # Name the count, so an operator can judge the loss
                "! Capture pool holds %s work items after %s seconds", CapturePool.GATE.in_flight(), timeout_seconds
            )
        logging.debug("[CAPTURE-POOL] Drain finished, drained=%s", drained)  # AFTER
        return drained  # The caller may report the outcome

    @staticmethod
    def install_shutdown_hook() -> None:
        """Register the drain, so a normal worker exit runs it one time.

        Why:
            The Gunicorn worker installs its own signal handlers, and a second
            handler would break the graceful stop. A registration through
            ``atexit`` runs after the worker stops accepting requests and
            leaves the signal handling with Gunicorn.
        """
        if CapturePool._HOOK_INSTALLED:  # A second registration would drain twice
            logging.debug("[CAPTURE-POOL] Shutdown hook already installed")  # State why nothing happened
            return  # Keep the first registration
        atexit.register(CapturePool.shutdown)  # Run the drain when the process exits normally
        CapturePool._HOOK_INSTALLED = True  # Remember the registration for this process
        logging.info("* Capture pool shutdown hook installed, drain %s seconds", SHUTDOWN_TIMEOUT_SECONDS)  # Announce


class BoundedFanOut:
    """Runs a small set of named blocking calls at one time.

    Why:
        Some portal work holds several independent cloud calls inside one work
        item. The four tier 3 reads of a capture are one case, and the cancel
        call of each upgrade plan of a stop is another. Run in order, the
        operator waits for the sum of the network waits. Run at one time, the
        operator waits for the longest wait alone. The call count never
        changes, so the hourly cloud call budget never changes.

        This class does not reach ``ConnectionPoolExecutor``, and the reason is
        not style. That executor splits the work into batches, draws a ``tqdm``
        progress bar on standard output, and builds a pool for each batch. A
        progress bar belongs to the command line and not to a web worker. The
        executor also expects a two-argument worker and a semaphore that it
        owns, which a caller inside a pool worker cannot supply.

        The class holds no drain gate on purpose. Every caller already runs
        inside work that the gate counts, and ``run`` returns only after every
        call ends, so the gate still covers the fan-out. A stop must also reach
        the cloud during a shutdown, because a refused cancel leaves a device
        writing firmware.
    """

    @staticmethod
    def resolve_worker_count(call_count: int) -> int:
        """Report how many calls of one fan-out run at one time.

        Why:
            A pool wider than the work wastes a thread. A pool wider than
            ``CAPTURE_WORKER_TARGET`` takes a larger share of the hourly cloud
            call budget than the plan allows.

        Args:
            call_count: How many calls the caller supplied.

        Returns:
            A count of 1 or more that never rises above the target or the work.
        """
        return max(1, min(CAPTURE_WORKER_TARGET, call_count))  # Never zero, never wider than the work or the target

    @staticmethod
    def _log_failure(name: str, description: str, error: BaseException) -> None:
        """Write the one log record that a failed fan-out call gets.

        Why:
            Both the pool path and the single-call path report a failure. One
            writer keeps the two records identical, so an operator reads one
            sentence whatever path the call took.

        Args:
            name: The name the caller gave this call.
            description: Plain name of the batch.
            error: The fault the call raised.
        """
        logging.error("! Fan-out call %s of %s failed: %s", name, description, type(error).__name__)  # Name the call

    @staticmethod
    def _resolve(name: str, future: Future[Any], description: str) -> Any:
        """Read the answer of one call that a worker thread ran.

        Why:
            A raised call must never lose the answer of the other calls. The
            failure therefore becomes a None value and one log record, and the
            caller decides what an absent answer means.

        Args:
            name: The name the caller gave this call.
            future: The pending answer of the call.
            description: Plain name of the batch, for the log record.

        Returns:
            The value of the call, or None after a failure.
        """
        try:  # The call reaches a network, so it may raise
            return future.result()  # Block until this one call ends
        except Exception as error:  # WHY: one failed call must not lose the answer of the other calls
            BoundedFanOut._log_failure(name, description, error)  # One writer for both paths
            return None  # The caller reads an absent answer as a failed call

    @staticmethod
    def _run_in_order(calls: Mapping[str, FanOutCall], description: str) -> dict[str, Any]:
        """Run the calls in the calling thread.

        Why:
            The matrix at ``documentation/python-parallelism-matrix.md`` puts
            the cost of a thread at about 50 microseconds. It asks for work far
            above that before a thread pays. One call never pays, and a fan-out
            of one also hides a fault behind a worker thread, which makes a
            test harder to read.

            The error boundary matches the pool path exactly. A caller that met
            an exception on one path and a None value on the other could not be
            written safely.

        Args:
            calls: One named call for each piece of work.
            description: Plain name of the batch, for the log record.

        Returns:
            One answer for each name. An absent answer is None.
        """
        answers: dict[str, Any] = {}  # One entry for each name the caller gave
        for name, call in calls.items():  # The caller supplied one call or none, so the order costs nothing
            try:  # The call reaches a network, so it may raise
                answers[name] = call()  # The caller owns the cloud call
            except Exception as error:  # WHY: the pool path answers None, so this path must answer None too
                BoundedFanOut._log_failure(name, description, error)  # One writer for both paths
                answers[name] = None  # The caller reads an absent answer as a failed call
        return answers  # The caller reads every name it supplied

    @staticmethod
    def run(calls: Mapping[str, FanOutCall], description: str = "cloud calls") -> dict[str, Any]:
        """Run every call at one time and collect the answers by name.

        Args:
            calls: One named call for each piece of work. Each call takes no
                argument, because the caller binds every argument first.
            description: Plain name of the batch, for the log records.

        Returns:
            One answer for each name the caller supplied. A call that raised
            holds None, so the caller never loses the other answers.
        """
        if len(calls) < 2:  # One call or none never pays for a thread
            return BoundedFanOut._run_in_order(calls, description)
        workers = BoundedFanOut.resolve_worker_count(len(calls))  # Bound the work in flight
        logging.info("[FAN-OUT] Starting %s %s across %s workers", len(calls), description, workers)  # BEFORE
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix=FANOUT_THREAD_PREFIX) as pool:
            pending = {name: pool.submit(call) for name, call in calls.items()}  # Every call starts before any wait
            answers = {name: BoundedFanOut._resolve(name, future, description) for name, future in pending.items()}
        logging.debug("[FAN-OUT] Finished %s %s", len(answers), description)  # AFTER
        return answers  # The caller reads every name it supplied
