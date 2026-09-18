"""Measure fixed local run-control workloads without external services."""

from __future__ import annotations  # Keep annotation parsing independent from import order.

import logging  # Report performance numbers through the pytest log path.
import statistics  # Use a stable aggregate instead of one noisy sample.
import time  # Measure elapsed wall time with the required high resolution clock.
from collections.abc import Callable, Mapping, Sequence  # Type the local builders without concrete stores.
from dataclasses import dataclass  # Return named measurements to the pytest report.
from datetime import UTC, datetime  # Build fixed aware times for deterministic stale checks.
from functools import partial  # Bind the history workload to the generic sample runner.
from typing import Any, Final  # Mark fixed workload sizes and thresholds.

from src.upgrade_portal.api.run_controls.services import BulkRunActionService, SiteMutationGuard  # Use real service.
from src.upgrade_portal.api.run_controls.views import RunStalePolicy  # Use the shared history stale policy.
from src.upgrade_portal.app.routes.review import run_history_row  # Use the route row builder under test.
from src.upgrade_portal.persistence.actions import (  # Use real journal.
    RUN_COLLECTION,  # Name the real run collection that the fake database exposes.
    ActionRepository,  # Exercise the production action journal.
    DurableActorScope,  # Build the actor scope without a request context.
)
from tests.integration.upgrade_portal.run_controls import FakeDatabase  # Trap ArangoDB in process memory.

logger = logging.getLogger(__name__)  # A module logger keeps the record source readable.
HISTORY_ROWS: Final[int] = 50  # The plan and research files fix the history workload size.
HISTORY_WARMUPS: Final[int] = 10  # The research file fixes the history warm-up count.
HISTORY_SAMPLES: Final[int] = 30  # The research file fixes the history timed sample count.
BULK_RUNS: Final[int] = 50  # The plan and research files fix the no-cloud batch size.
BULK_WARMUPS: Final[int] = 5  # The research file fixes the no-cloud batch warm-up count.
BULK_SAMPLES: Final[int] = 20  # The research file fixes the no-cloud batch timed sample count.
HISTORY_LIMIT_SECONDS: Final[float] = 1.0  # The spec target is the margin, so no tighter local limit is added.
BULK_LIMIT_SECONDS: Final[float] = 5.0  # The spec target is generous enough for slow workstations.
FIXED_NOW: Final[datetime] = datetime(2026, 9, 12, 12, 0, tzinfo=UTC)  # One clock removes time drift.
STARTED_AT: Final[str] = "2026-09-11T12:00:00+00:00"  # All rows share one fixed start.
UPDATED_AT: Final[str] = "2026-09-11T12:30:00+00:00"  # All rows are stale by the fixed clock.
ACTOR = DurableActorScope.build("email", "operator@example.invalid")  # Use one durable actor for all samples.


def _install_safe_logging() -> None:
    """Route measurement logs to the test stream."""
    logging.basicConfig(level=logging.INFO, format="%(message)s", force=True)  # Avoid the shared rotating log file.


_install_safe_logging()  # Keep performance evidence visible and independent from local file locks.


@dataclass(frozen=True, slots=True)
class Measurement:
    """Hold one aggregate performance result."""

    name: str  # Name the measured boundary in the report.
    median_seconds: float  # Report the stable center of the timed samples.
    maximum_seconds: float  # Enforce the fixed SpecKit maximum target.
    sample_count: int  # Expose the timed sample count in the report.


def _history_records() -> tuple[dict[str, Any], ...]:
    """Return the fixed 50-row history workload."""
    logger.info("Build the fixed history workload")  # Record the deterministic setup before work starts.
    rows = tuple(  # Keep row order stable for every timed sample.
        {
            "run_id": f"history-run-{index:02d}",  # Give each row one stable identifier.
            "site_id": f"site-{index % 5:02d}",  # Reuse five sites to match normal operator history.
            "site_name": f"Site {index % 5:02d}",  # Give the view builder a stored site name.
            "state": "created",  # Keep each row nonterminal so stale assessment runs the full rule.
            "created_at": STARTED_AT,  # Remove clock variance from the started text.
            "updated_at": UPDATED_AT,  # Remove clock variance from the stale decision.
            "targets": [{"device_id": f"device-{index:02d}"}],  # Exercise deterministic device counts.
        }
        for index in range(HISTORY_ROWS)  # Create the exact fixed row count from the plan.
    )
    logger.debug("Built %s fixed history row(s)", len(rows))  # Confirm the setup size.
    return rows  # Share one immutable workload across history samples.


def _build_history_view(rows: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], ...]:
    """Return shaped rows for the fixed history view."""
    logger.info("Build the measured history view")  # Record the measured action before the loop.
    policy = RunStalePolicy(FIXED_NOW)  # Use one fixed clock for all rows in this view.
    shaped = tuple(run_history_row(row, policy) for row in rows)  # Exercise the real row shaping path.
    logger.debug("Built the measured history view with %s row(s)", len(shaped))  # Report the safe count.
    return shaped  # Expose the built view for correctness checks.


def _repository() -> tuple[FakeDatabase, ActionRepository]:
    """Return one bootstrapped fake action repository."""
    database = FakeDatabase()  # Start with one process-owned store.
    database.create_collection(RUN_COLLECTION)  # Create the authoritative run collection without ArangoDB.
    repository = ActionRepository(database)  # Use the real repository against the fake database.
    repository.bootstrap()  # Build the action journal in the fake store.
    return database, repository  # Give one isolated store to each batch sample.


def _bulk_context() -> tuple[BulkRunActionService, dict[str, Any]]:
    """Return one fixed no-cloud bulk cancel workload."""
    logger.info("Build the fixed no-cloud batch workload")  # Record local setup before the measured action.
    database, repository = _repository()  # Isolate each timed batch from prior mutations.
    run_ids = tuple(f"batch-run-{index:02d}" for index in range(BULK_RUNS))  # Fix the ordered run identifiers.
    tokens = {f"site-{index:02d}": "token" for index in range(BULK_RUNS)}  # Give each site one valid local lock.

    def allow_write(_organization_id: str, _site_id: str) -> bool:
        """Return the fixed local write permission."""
        return True  # Keep the measured path on the successful local branch.

    def read_lock(_organization_id: str, site_id: str) -> dict[str, str]:
        """Return the fixed local lock token."""
        return {"lock_token": tokens[site_id]}  # Recheck the expected token without Redis or a network call.

    _seed_precloud_runs(database, run_ids)  # Store the exact pre-cloud runs in the fake database.
    collection = database.collection(RUN_COLLECTION)  # Read and write through the fake collection handle.
    guard = SiteMutationGuard(allow_write, read_lock, tokens)  # Reuse the same guard path as other tests.
    service = BulkRunActionService(repository, collection.get, guard, clock=_fixed_clock)  # Reach no cloud seam.
    preview = _bulk_preview(run_ids)  # Build the signed-preview stand-in without a route or cloud call.
    logger.debug("Built the fixed no-cloud batch workload with %s run(s)", len(run_ids))  # Confirm size.
    return service, preview  # Return only the objects needed inside the timed boundary.


def _seed_precloud_runs(database: FakeDatabase, run_ids: Sequence[str]) -> None:
    """Seed deterministic pre-cloud runs into the fake store."""
    for index, run_id in enumerate(run_ids):  # Keep one stable site and revision for each source run.
        row = database.seed_run(run_id, "created")  # Use the existing fake helper to build a run record.
        row.update(_run_fields(index))  # Add the fields that the bulk service reads.
        database.collections[RUN_COLLECTION]["documents"][run_id] = row  # Store the complete fake run.


def _run_fields(index: int) -> dict[str, Any]:
    """Return deterministic fields for one pre-cloud run."""
    return {  # Keep the record shape small and stable.
        "org_id": "org-one",  # Bind all runs to the same local organization.
        "site_id": f"site-{index:02d}",  # Give each run one stable site.
        "created_at": STARTED_AT,  # Remove current time from the input.
        "updated_at": UPDATED_AT,  # Give the cancel result a known prior time.
        "targets": [],  # Model pre-cloud runs that reached no device work.
        "options": {},  # Keep the local cancel path free of option processing.
    }


def _bulk_preview(run_ids: Sequence[str]) -> dict[str, Any]:
    """Return the fixed preview data for one bulk action."""
    return {  # Match the service contract without route or token work.
        "preview_id": "preview-performance",  # Use one deterministic preview identifier.
        "organization_id": "org-one",  # Keep the batch in one organization.
        "history_scope": "all-sites",  # Match the plan term for a history scope.
        "run_ids": list(run_ids),  # Preserve the exact preview order.
        "site_count": BULK_RUNS,  # Give one site for each fixed run.
    }


def _cancel_batch() -> Any:
    """Run one fixed no-cloud bulk cancel action."""
    service, preview = _bulk_context()  # Build local state outside the service call.
    logger.info("Run the measured no-cloud batch path")  # Record the measured action before it starts.
    action = service.cancel(  # Exercise the real batch service with only fake local stores.
        actor=ACTOR,  # Use one durable actor for deterministic idempotency.
        idempotency_key="performance-cancel-key-0001",  # Reuse is safe because each sample has a fresh store.
        confirmation="CANCEL 50 RUNS",  # Match the fixed workload size.
        preview=preview,  # Use the deterministic preview payload.
    )
    logger.debug("The measured no-cloud batch path returned %s item(s)", len(action.ledger.items))  # Summarize result.
    return action  # Let the caller check that the full batch completed.


def _fixed_clock() -> datetime:
    """Return the fixed clock for the bulk service."""
    return FIXED_NOW  # Remove live time from batch outcomes.


def _elapsed(action: Callable[..., Any], *args: Any) -> float:
    """Return elapsed seconds for one action."""
    disabled_level = logging.root.manager.disable  # Preserve the caller logging state during timing.
    start = time.perf_counter()  # Use the required timer at the measured boundary.
    logging.disable(logging.CRITICAL)  # Measure code work, not shared log file rollover on this workstation.
    try:  # Restore logging even when the measured path raises.
        action(*args)  # Run the measured operation once.
    finally:  # Always return the test process to its prior logging state.
        logging.disable(disabled_level)  # Keep later human-readable measurement logs visible.
    return time.perf_counter() - start  # Return wall time in seconds.


def _history_sample(rows: Sequence[Mapping[str, Any]]) -> float:
    """Return one timed history sample."""
    return _elapsed(_build_history_view, rows)  # Time only the real history view builder.


def _bulk_sample() -> float:
    """Return one timed no-cloud batch sample."""
    return _elapsed(_cancel_batch)  # Time only the real no-cloud service path.


def _measure(name: str, warmups: int, samples: int, sample: Callable[[], float]) -> Measurement:
    """Return one measured aggregate after warm-up calls."""
    logger.info("Warm up the %s measurement", name)  # Record warm-up before any unreported samples run.
    for _ in range(warmups):  # Stabilize the interpreter and caches before timing.
        sample()  # Exercise the same measured boundary as the timed phase.
    logger.debug("Finished %s warm-up call(s) for %s", warmups, name)  # Confirm warm-up count.
    logger.info("Collect timed samples for %s", name)  # Record the measured phase before samples run.
    values = [sample() for _ in range(samples)]  # Collect the fixed timed sample count.
    result = Measurement(name, statistics.median(values), max(values), len(values))  # Report median and maximum.
    logger.debug("Measured %s median %s and maximum %s", name, result.median_seconds, result.maximum_seconds)
    return result  # Expose the aggregate to assertions and reports.


def _record_measurement(record_property: Callable[[str, object], None], measurement: Measurement) -> None:
    """Expose one measurement through pytest reports and console output."""
    record_property(f"{measurement.name}_median_seconds", measurement.median_seconds)  # Store the median in reports.
    record_property(f"{measurement.name}_maximum_seconds", measurement.maximum_seconds)  # Store the maximum in reports.
    logger.info(  # Write the human-readable result through the logging path.
        "%s performance median %.6f seconds maximum %.6f seconds samples %s",
        measurement.name,
        measurement.median_seconds,
        measurement.maximum_seconds,
        measurement.sample_count,
    )
    message = (  # Build one console line outside the logging call.
        f"{measurement.name} performance median {measurement.median_seconds:.6f} "
        f"seconds maximum {measurement.maximum_seconds:.6f} seconds samples {measurement.sample_count}"
    )
    print(message)  # Keep the exact numbers visible when pytest runs with -s.


def test_history_view_builds_fifty_rows_under_the_spec_target(
    record_property: Callable[[str, object], None],
) -> None:
    """Prove the fixed 50-row history view stays below the required target."""
    rows = _history_records()  # Build the deterministic workload once for all samples.
    sample = partial(_history_sample, rows)  # Keep setup out of the measured boundary.
    measurement = _measure("history_view", HISTORY_WARMUPS, HISTORY_SAMPLES, sample)  # Run fixed counts.
    _record_measurement(record_property, measurement)  # Expose the measurement before the threshold assert.
    assert len(_build_history_view(rows)) == HISTORY_ROWS  # Prove the workload size before the speed claim.
    assert measurement.maximum_seconds < HISTORY_LIMIT_SECONDS  # Enforce SC-009 from the specification.


def test_no_cloud_batch_cancels_fifty_runs_under_the_spec_target(
    record_property: Callable[[str, object], None],
) -> None:
    """Prove the fixed 50-run no-cloud batch stays below the required target."""
    measurement = _measure("no_cloud_batch", BULK_WARMUPS, BULK_SAMPLES, _bulk_sample)  # Run fixed counts.
    _record_measurement(record_property, measurement)  # Expose the measurement before the threshold assert.
    action = _cancel_batch()  # Run one correctness check outside the timed sample list.
    assert len(action.ledger.items) == BULK_RUNS  # Prove every fixed run received one outcome.
    assert all(item.completion.reason == "precloud_run_cancelled" for item in action.ledger.items)  # Prove no refusal.
    assert measurement.maximum_seconds < BULK_LIMIT_SECONDS  # Enforce SC-010 from the specification.
