"""Site packet capture loop runner orchestrator."""

from __future__ import annotations  # WHY: postponed annotation evaluation for forward-ref typing

import logging  # WHY: route operator-facing banners through the configured logger (issue #886)
import os  # WHY: build cross-platform download folder path via os.path.join
import time  # WHY: capture wall-clock timestamps and sleep between loop iterations
from dataclasses import dataclass  # WHY: dataclasses reduce boilerplate for manager + loop state bundles
from typing import Any  # WHY: manager duck-typed to avoid cyclic import with PacketCaptureManager

_DOWNLOAD_FOLDER_NAME = "data"  # WHY: relative folder under cwd where completed pcaps are stored
_DEFAULT_LOOP_DURATION = 60  # WHY: fallback capture duration when payload omits an explicit value
_BANNER_WIDTH = 60  # WHY: character width for iteration start/end separator banners
_INTERRUPT_BANNER_WIDTH = 80  # WHY: wider banner reserved for the user-interrupt notice
_ITER_BANNER = "=" * _BANNER_WIDTH  # WHY: precompute the standard iteration banner string
_INTERRUPT_BANNER = "=" * _INTERRUPT_BANNER_WIDTH  # WHY: precompute the interrupt notice banner
_LOOP_INTERRUPT_TITLE = " LOOP MODE INTERRUPTED BY USER"  # WHY: interrupt header text kept as constant
_READY_TO_CAPTURE = 0  # WHY: sentinel value returned by manager when cooldown has fully elapsed


@dataclass  # WHY: plain dataclass so iteration counter and timestamp remain mutable across iterations
class _LoopState:  # WHY: bundle four otherwise-local variables threaded through each loop iteration
    """Track iteration counter, last successful capture time, and precomputed loop constants."""

    min_interval: int  # WHY: minimum seconds between consecutive capture attempts, sourced from payload
    download_folder: str  # WHY: absolute path where completed pcaps are downloaded each iteration
    iteration: int = 0  # WHY: increment-first counter of loop iterations for user-visible logging
    last_capture_time: float | None = None  # WHY: epoch of last successful attempt. None on first pass


@dataclass(frozen=True, slots=True)  # WHY: frozen slotted bundle keeps the manager binding immutable
class SiteCaptureLoopRunner:  # WHY: orchestrator delegating capture steps to a PacketCaptureManager
    """Run continuous site capture loops by delegating steps to PacketCaptureManager helpers."""

    manager: Any  # WHY: PacketCaptureManager-like collaborator supplying loop delegate methods

    def run(self, site_id: str, payload: dict[str, Any]) -> None:  # WHY: single-entry orchestrator
        """Execute loop mode with download-first and start-capture cycle."""
        state = _LoopState(  # WHY: derive per-run mutable state from payload before entering the loop
            min_interval=payload.get("duration", _DEFAULT_LOOP_DURATION),
            download_folder=os.path.join(os.getcwd(), _DOWNLOAD_FOLDER_NAME),
        )
        self.manager._print_loop_banner(payload)  # WHY: initial banner shown once before iterations begin
        try:  # WHY: KeyboardInterrupt is the only expected exit path from the infinite loop
            while True:  # WHY: run forever until Ctrl+C raises KeyboardInterrupt handled below
                self._run_one_iteration(site_id, payload, state)  # WHY: delegate body to shrink run() length
        except KeyboardInterrupt:  # WHY: graceful shutdown on Ctrl+C rather than propagating to caller
            self._handle_user_interrupt(state.iteration)  # WHY: emit exit banner + notify manager

    def _run_one_iteration(  # WHY: split iteration body out of run to satisfy STRUCT-LENGTH ≤25 lines
        self, site_id: str, payload: dict[str, Any], state: _LoopState
    ) -> None:
        """Execute a single loop iteration: fetch, download, maybe capture, then sleep."""
        state.iteration += 1  # WHY: bump counter first so iteration number is 1-based in logs
        loop_start = time.time()  # WHY: mark iteration start to compute the accurate sleep budget later
        # WHY: preserve iteration header banner verbatim. Route through logger for capture/redirection.
        logging.info("\n%s\nLoop Iteration #%s\n%s", _ITER_BANNER, state.iteration, _ITER_BANNER)
        completed = self.manager._fetch_completed_pcaps(site_id, state.iteration)  # WHY: gather ready pcaps
        self.manager._download_manager.download_pending_pcaps(  # WHY: download all currently-ready pcaps
            completed, state.download_folder
        )
        wait_time = self.manager._check_capture_readiness(  # WHY: consult manager for cooldown remaining
            state.last_capture_time, state.min_interval
        )
        if wait_time == _READY_TO_CAPTURE:  # WHY: zero cooldown means we may attempt a capture this pass
            self._attempt_capture(site_id, payload, state)  # WHY: delegate attempt + timestamp update
        sleep_time = self.manager._calc_loop_sleep(wait_time, time.time() - loop_start)  # WHY: adaptive nap
        # WHY: preserve iteration close banner + nap notice verbatim. Route through logger.
        logging.info("\n%s\nLoop iteration #%s complete", _ITER_BANNER, state.iteration)
        logging.info("Waiting %.0f seconds before next check...\n%s\n", sleep_time, _ITER_BANNER)
        time.sleep(sleep_time)  # WHY: honor cooldown plus remaining sleep budget before next iteration

    def _attempt_capture(  # WHY: pack capture-attempt call and last_capture_time update into one helper
        self, site_id: str, payload: dict[str, Any], state: _LoopState
    ) -> None:
        """Attempt a new capture and record the timestamp when the manager reports success."""
        capture_time = self.manager._attempt_loop_capture(site_id, payload, state.iteration)
        if capture_time is not None:  # WHY: manager returns None when the start attempt failed
            state.last_capture_time = capture_time  # WHY: record success epoch to gate future cooldown

    def _handle_user_interrupt(self, iteration: int) -> None:  # WHY: isolate exit-path IO to one helper
        """Print the interrupt banner and notify the manager of graceful loop termination."""
        # WHY: preserve interrupt banner + iteration count + reassurance line verbatim. Route through logger.
        logging.info("\n\n%s\n%s\n%s", _INTERRUPT_BANNER, _LOOP_INTERRUPT_TITLE, _INTERRUPT_BANNER)
        logging.info("  Completed %s loop iteration(s)", iteration)
        logging.info("  All available PCAPs have been downloaded\n  Exiting gracefully...")
        self.manager._log_loop_stop(iteration)  # WHY: notify manager for structured audit/telemetry logging
