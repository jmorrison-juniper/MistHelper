"""RunSystematicTestManager extracted from MistHelper.

Runs the systematic (read-only, non-interactive, non-destructive) menu-option
sweep used by ``--test`` mode. Each safe menu option is invoked exactly once,
with telemetry emission and a printed summary.

Runtime dependencies (``menu_actions`` global, ``org_id`` global mutation,
``ConfigUtils``, ``TelemetryEmitter``, ``SystematicTestOption``, ``TestSummary``,
and the ``_systematic_test_*`` module-level helpers) are still owned by
MistHelper.py. They are resolved lazily via ``importlib.import_module`` so the
extracted module import-graph stays flat and monkeypatched attributes are
honoured in tests.

Address the ``missing_action_logging`` guideline flag identified by the
compliance analyzer for ``run_systematic_test``: this class wraps the full
sweep in explicit info-before / debug-after envelopes at the manager level.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing on 3.10+

import importlib  # Late-import MistHelper module to avoid circular src<->MistHelper dependency
import logging  # Structured action logging required by coding standards
import time  # Measure total sweep duration and enforce inter-option API delay via helper
from dataclasses import dataclass  # Bundle sweep counters to keep _finalize_sweep within the 5-Item Rule
from types import SimpleNamespace  # Bundle runtime dependencies without coupling to a dataclass
from typing import Any  # Loose typing for late-bound module attributes and helper return values

from src.dataclasses.progress_event import TestSummary  # Aggregate result event bundled for emitter + printer


@dataclass(frozen=True)
class _SweepCounters:
    """Bundle per-option pass/fail counts and the safe-option list for finalize step."""

    success_count: int  # Count of options that completed without raising an exception
    error_count: int  # Count of options that raised or returned an error
    safe_options: list[str]  # Ordered safe-option list used to compute total attempts


def _resolve_runtime_dependencies() -> SimpleNamespace:
    """Resolve MistHelper-owned runtime dependencies without static cross-module imports."""
    logging.info("Resolving RunSystematicTestManager runtime dependencies from MistHelper")  # Log before import
    misthelper_module = importlib.import_module("MistHelper")  # Late import avoids circular dependency
    logging.debug("RunSystematicTestManager runtime dependencies resolved successfully")  # Log after resolution
    return SimpleNamespace(
        misthelper_module=misthelper_module,  # Retained so global lookups honour monkeypatch in tests
    )


class RunSystematicTestManager:
    """Run systematic test of safe menu options with telemetry and summary output.

    Owns the top-level orchestration originally defined as
    ``run_systematic_test()`` in MistHelper.py. Delegates classification,
    telemetry, and per-option execution to the ``_systematic_test_*``
    module-level helpers that remain in MistHelper.

    SECURITY: Executes only options classified as safe (GET-only,
    non-interactive, non-destructive) by OperationRegistry.

    Usage:
        RunSystematicTestManager().run()
    """

    def __init__(self) -> None:
        """Initialize manager with late-bound MistHelper handles."""
        logging.info("RunSystematicTestManager init: starting new manager instance")  # Log construction start
        self._deps: SimpleNamespace = _resolve_runtime_dependencies()  # Late-bound MistHelper handles
        logging.debug("RunSystematicTestManager init complete")  # Log after construction

    def _misthelper(self) -> Any:
        """Return the current MistHelper module so monkeypatched attributes are honoured."""
        return self._deps.misthelper_module  # Resolve at call-time so tests can substitute values

    def run(self) -> bool:
        """Run systematic test of safe menu options and return pass/fail outcome.

        Returns:
            bool: True if all tested options passed, False if any failed.
        """
        logging.info("SYSTEMATIC_TEST: RunSystematicTestManager.run starting sweep")  # Log sweep start
        start_time = time.time()  # Capture total-duration baseline before any setup work
        safe_options, unsafe_list, all_options, skip_count, emitter, telemetry_path, fast_enabled = (
            self._prepare_sweep()  # Banner, classification, telemetry, org resolution done once up front
        )
        success_count, error_count = self._execute_sweep(emitter, safe_options, fast_enabled)  # Run loop
        summary = self._build_summary(  # Bundle counts into TestSummary event reused by both finalize + print
            all_options, success_count, error_count, skip_count, start_time
        )
        counters = _SweepCounters(  # Frozen bundle keeps _finalize_sweep signature within the 5-Item Rule
            success_count=success_count, error_count=error_count, safe_options=safe_options
        )
        outcome = self._finalize_sweep(  # Emit summary, close telemetry, print summary, return outcome
            emitter, summary, telemetry_path, counters
        )
        logging.debug(  # Log sweep completion with outcome for postmortem tracing
            "SYSTEMATIC_TEST: RunSystematicTestManager.run finished outcome=%s", outcome
        )
        return outcome  # Signal pass/fail to callers for exit-code logic

    def _prepare_sweep(self) -> tuple[list[str], list[str], list[str], int, Any, Any, bool]:
        """Print banner, classify options, open telemetry, and resolve run context."""
        logging.info("RunSystematicTestManager: preparing sweep context")  # Log preparation start
        misthelper = self._misthelper()  # Cache module handle for the helper lookups below
        misthelper._print_systematic_banner()  # Banner + start timestamp + separator
        safe_options, unsafe_list, all_options = (
            misthelper._build_systematic_test_options()  # Classify menu options into safe/unsafe sets
        )
        misthelper._print_systematic_pre_run_counts(  # Print pre-run counts of total/safe/unsafe
            all_options, safe_options, unsafe_list
        )
        emitter, telemetry_path, skip_count = (
            misthelper._initialize_systematic_telemetry(unsafe_list)  # Open timestamped telemetry emitter
        )
        fast_enabled = misthelper._resolve_systematic_test_context()  # Resolve org + fast mode once
        logging.debug(  # Log resolved context for tracing (counts + fast flag)
            "RunSystematicTestManager: sweep prepared safe=%d unsafe=%d fast=%s",
            len(safe_options),
            len(unsafe_list),
            fast_enabled,
        )
        return safe_options, unsafe_list, all_options, skip_count, emitter, telemetry_path, fast_enabled

    def _execute_sweep(
        self, emitter: Any, safe_options: list[str], fast_enabled: bool
    ) -> tuple[int, int]:
        """Run every safe option through the telemetry-emitting loop and count outcomes."""
        logging.info(  # Log execution phase entry with count of safe options
            "RunSystematicTestManager: executing sweep across %d safe options", len(safe_options)
        )
        success_count, error_count = (
            self._misthelper()._execute_systematic_test_loop(  # Delegate loop body to canonical helper
                emitter, safe_options, fast_enabled
            )
        )
        logging.debug(  # Log per-run counts for observability without recomputing them
            "RunSystematicTestManager: sweep executed success=%d error=%d", success_count, error_count
        )
        return success_count, error_count

    def _build_summary(
        self,
        all_options: list[str],
        success_count: int,
        error_count: int,
        skip_count: int,
        start_time: float,
    ) -> TestSummary:
        """Build the aggregate TestSummary event from per-option counters and elapsed time."""
        total_time = time.time() - start_time  # Total elapsed includes setup, execution, and delays
        summary = TestSummary(  # Frozen bundle keeps emitter + printer signatures within the 5-Item Rule
            len(all_options), success_count, error_count, skip_count, total_time, "systematic"
        )
        logging.debug(  # Log built summary for postmortem observability without duplicating fields
            "RunSystematicTestManager: summary built total_ops=%d total_time=%.2f",
            len(all_options),
            total_time,
        )
        return summary  # Return so caller can hand it to finalize + print helpers

    def _finalize_sweep(
        self,
        emitter: Any,
        summary: TestSummary,
        telemetry_path: Any,
        counters: _SweepCounters,
    ) -> bool:
        """Emit summary, close telemetry, print operator summary, and return outcome."""
        logging.info("RunSystematicTestManager: finalizing sweep and printing summary")  # Log finalize
        misthelper = self._misthelper()  # Cache module handle for the three helper lookups below
        misthelper._finalize_systematic_telemetry(  # Emit summary event, close file, enforce retention
            emitter, summary
        )
        misthelper._print_systematic_summary(summary, telemetry_path)  # Print user-facing summary block
        outcome = bool(  # Cast Any (misthelper module attr) to bool for strict typing conformance
            misthelper._report_systematic_outcome(  # Emit pass/fail message + return boolean
                counters.success_count,
                counters.error_count,
                len(counters.safe_options),
                summary.elapsed,  # TestSummary field name is `elapsed` (wall-clock seconds)
            )
        )
        logging.debug(  # Log final outcome so callers can trace exit-code decision
            "RunSystematicTestManager: sweep finalized outcome=%s", outcome
        )
        return outcome  # Return pass/fail boolean to run()
