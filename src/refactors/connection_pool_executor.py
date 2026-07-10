"""execute_with_connection_pool_management extracted from MistHelper (SC-003).

Owns the public ``execute_with_connection_pool_management`` orchestrator
originally defined at MistHelper.py:7545 plus its full ``_pool_*`` sibling
helper chain (MistHelper.py:7374-7542), and re-lands them as
``@staticmethod`` members on ``ConnectionPoolExecutor`` per FR-005
carry-forward. All 7 known callsites (3 in MistHelper.py + 2 in the
gateway export utilities + 1 in the override device fetcher + 1 in the
serial-CC helper) are rewritten in the same PR to reference the extracted
class method; no wrapper shim remains in MistHelper.py after this extraction.

FR-015 sibling-helpers-travel-with-parent: the full 11-helper chain moves
together to preserve behavior. Splitting the chain would leave orphaned
private helpers in MistHelper.py that no longer have any caller.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing

import logging  # Structured action logging per Constitution VII
import os  # Read cpu_count for CPU-aware threading strategy
import threading  # Semaphore for bounding concurrent API calls
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait  # Bounded parallel execution primitives
from typing import Any  # Loose typing for worker callables and return payloads

from tqdm import tqdm  # Progress bar for per-batch operator feedback

from src.dataclasses.batch_worker import BatchWorkerConfig  # Frozen bundle for the 4 constant worker params
from src.refactors.fast_mode_devices_per_thread import FastModeDevicesPerThread  # Devices-per-thread scaling constant


def _resolve_fast_mode_env() -> tuple[bool, int, int]:  # Late-bind MistHelper module-level fast-mode env values
    """Return (use_connection_aware, max_concurrent_connections, fallback_threads) from MistHelper globals.

    Late-binds via ``import MistHelper`` to avoid a circular import at module
    load time (MistHelper.py imports ConnectionPoolExecutor and vice-versa
    would deadlock). By the time these executor methods are called at
    runtime, MistHelper is fully initialized and the constants are readable.

    Note: FAST_MODE_MAX_CONCURRENT_CONNECTIONS is imported directly from
    src/refactors/fast_mode_constants.py per initiative 1015 T-02, and
    FAST_MODE_USE_CONNECTION_AWARE_THREADING is imported from the same
    module per T-03 (both bypass the ``MistHelper.SYMBOL`` module-attribute
    hop); FAST_MODE_FALLBACK_THREADS remains on MistHelper pending later
    extraction.
    """
    import MistHelper  # Late-binding import; MistHelper is fully loaded by the time methods run
    from src.refactors.fast_mode_constants import (
        FAST_MODE_MAX_CONCURRENT_CONNECTIONS,  # Direct import of the extracted concurrent-connection cap (post-T-02)
        FAST_MODE_USE_CONNECTION_AWARE_THREADING,  # Direct import of the threading-strategy toggle (post-T-03)
    )

    return (  # Bundle the 3 fast-mode env-derived constants into a tuple
        FAST_MODE_USE_CONNECTION_AWARE_THREADING,  # Threading strategy toggle (from landing module)
        FAST_MODE_MAX_CONCURRENT_CONNECTIONS,  # Cap on simultaneous API calls (from landing module)
        MistHelper.FAST_MODE_FALLBACK_THREADS,  # CPU-aware fallback thread count
    )


class ConnectionPoolExecutor:  # Class-body seam for the connection-pool-managed executor (FR-005 carry-forward)
    """Class-body seam owning the connection-pool-managed batch executor and its helper chain."""

    @staticmethod
    def _pool_resolve_thread_sizing(use_conn_aware: bool, max_conn: int, fallback_threads: int) -> tuple[int, str]:
        """Resolve (max_threads, threading_mode) from strategy toggle + env-derived caps."""
        # WHY: extracted so _pool_configure drops from 28 lines to <25 per STRUCT-LENGTH.
        if use_conn_aware:  # Connection-aware mode limits threads to API connection pool size
            max_threads = max_conn  # Cap threads at configured pool capacity
            threading_mode = "connection-aware"  # Strategy label for log identification
            logging.info(  # Announce connection-aware sizing decision
                "! Connection-aware threading: Using %s threads (respects connection pool limit)", max_threads
            )
            return max_threads, threading_mode  # Bundle for caller
        max_threads = os.cpu_count() or fallback_threads  # CPU-aware fallback when cpu_count unavailable
        threading_mode = "CPU-aware"  # Strategy label for log identification
        logging.info(  # Announce CPU-aware sizing decision
            "! CPU-aware threading: Using %s threads (maximum CPU utilization)", max_threads
        )
        return max_threads, threading_mode  # Bundle for caller

    @staticmethod
    def _pool_configure(work_items: list[Any], batch_description: str) -> tuple[int, threading.Semaphore, int, str]:
        """Determine threading strategy, semaphore, and batch size for a pool run."""
        logging.debug(  # BEFORE: log entry into pool-configure helper
            "[POOL-CONFIG] Configuring pool for %s items (%s)", len(work_items), batch_description
        )
        use_conn_aware, max_conn, fallback_threads = _resolve_fast_mode_env()  # Late-bind fast-mode env
        max_threads, threading_mode = ConnectionPoolExecutor._pool_resolve_thread_sizing(  # Sizing decision
            use_conn_aware, max_conn, fallback_threads
        )
        connection_semaphore = threading.Semaphore(max_conn)  # Bound simultaneous API calls
        logging.info("* Connection pool protection: Maximum %s concurrent API calls", max_conn)  # Announce cap
        batch_size = max_threads * FastModeDevicesPerThread.VALUE  # Scale batch size to thread count/per-thread setting
        logging.info(  # Announce batch dispatch plan
            "* Processing %s %s with connection pool management...", len(work_items), batch_description
        )
        logging.debug(  # AFTER: log resolved pool config
            "[POOL-CONFIG] Resolved max_threads=%s batch_size=%s mode=%s", max_threads, batch_size, threading_mode
        )
        return (max_threads, connection_semaphore, batch_size, threading_mode)  # Bundle pool config values

    @staticmethod
    def _pool_collect_future_result(future: Any, item: Any, config: BatchWorkerConfig) -> tuple[str, Any]:
        """Resolve one completed future: return ('success', result) on a truthy result, else ('failed', item)."""
        try:  # Future.result() can raise if the worker threw an exception
            result = future.result()  # Retrieve the worker's return value or propagate its exception
            if result:  # Truthy result means the worker succeeded and returned data
                return "success", result  # Hand the successful result back to the caller
            return "failed", item  # Falsy result (empty/None) -- treat the item as failed for retry
        except Exception as exc:  # Worker threw an exception; log and track as failed
            logging.error(  # Emit error log with item context for post-mortem debugging
                "! Future exception for %s %s: %s", config.batch_description.rstrip("s"), item, exc
            )
            return "failed", item  # Mark item as failed so retry logic can handle it

    @staticmethod
    def _pool_advance_progress_bar(pbar: Any) -> None:
        """Advance a tqdm progress bar by one, isolating any tqdm.update error so it cannot mask real results."""
        try:  # tqdm.update can fail in some environments; isolate that error
            pbar.update(1)  # Advance progress bar by one item for each completed future
        except Exception as upd_err:  # Progress bar update failure should not mask the real work result
            logging.error("! Progress bar update failed: %s", upd_err)  # Log progress bar failure for debugging

    @staticmethod
    def _record_future_outcome(future: Any, item: Any, config: BatchWorkerConfig, accumulator: dict[str, Any]) -> None:
        """Inspect one completed future and update accumulator with the success/failure outcome."""
        outcome, payload = ConnectionPoolExecutor._pool_collect_future_result(  # Resolve future -> (status, payload)
            future, item, config
        )
        if outcome == "success":  # Worker returned usable data
            accumulator["successful"].append(payload)  # Collect successful result
            if not accumulator["first_logged"]:  # First-result one-shot debug log
                logging.debug("! First future result type: %s", type(payload))  # One-shot shape debug log
                accumulator["first_logged"] = True  # Prevent repeated debug log
            return
        accumulator["failed"].append(payload)  # Empty result or worker exception -- track for retry

    @staticmethod
    def _pool_drain_wait_loop(
        future_to_item: dict[Any, Any], batch_desc: str, config: BatchWorkerConfig
    ) -> tuple[list[Any], list[Any]]:
        """Wait on the futures, collecting successful results and failed items until all have resolved."""
        accumulator: dict[str, Any] = {  # Mutable batch state for successes, failures, and first-log flag
            "successful": [],
            "failed": [],
            "first_logged": False,
        }
        pending = set(future_to_item.keys())  # Track in-flight futures so the wait loop can detect completion
        with tqdm(  # Show per-batch progress to the operator (issue #431: batch_description from config)
            total=len(pending), desc=batch_desc, unit=config.batch_description.rstrip("s")
        ) as pbar:  # progress bar
            while pending:  # Keep collecting futures until all have resolved
                done, pending = wait(pending, return_when=FIRST_COMPLETED)  # Wake on any future finish
                for future in done:  # Inspect each completed future before moving on
                    ConnectionPoolExecutor._record_future_outcome(  # Resolve + record accumulator update
                        future, future_to_item[future], config, accumulator
                    )
                    ConnectionPoolExecutor._pool_advance_progress_bar(pbar)  # Advance progress regardless of outcome
        return accumulator["successful"], accumulator["failed"]  # Return batch-level results for caller

    @staticmethod
    def _pool_process_batch_wait_loop(  # Submit one batch to a thread pool
        batch: list[Any],
        batch_number: int,
        total_batches: int,
        config: BatchWorkerConfig,
    ) -> tuple[list[Any], list[Any]]:
        """Submit one batch to a thread pool and collect results via a wait loop (Issue #431 config dataclass)."""
        logging.info(  # Log batch progress before dispatching to the thread pool
            "! Processing batch %s/%s (%s %s, ~%.0f per thread)",
            batch_number,
            total_batches,
            len(batch),
            config.batch_description,  # Issue #431: from config dataclass
            len(batch) / config.max_threads,  # Issue #431: from config dataclass
        )
        with ThreadPoolExecutor(max_workers=config.max_threads) as executor:  # Bound thread count to pool size
            future_to_item = {  # Map each future back to its source item for error reporting
                executor.submit(config.worker_function, item, config.connection_semaphore): item  # Worker per item
                for item in batch
            }
            batch_desc = f"Batch {batch_number}/{total_batches}"  # tqdm progress label
            return ConnectionPoolExecutor._pool_drain_wait_loop(  # Collect results as futures resolve
                future_to_item, batch_desc, config
            )

    @staticmethod
    def _pool_emit_traceback_lines(batch_exc: Exception) -> None:  # Emit traceback lines to log
        """Format batch exception traceback and emit each line as an error record (best-effort)."""
        try:  # Best-effort capture; serialization failure must not suppress the re-raise
            import traceback as _tb2  # Local import to avoid affecting module namespace

            formatted = "".join(  # Format the exception into a multi-line string for line-by-line emission
                _tb2.format_exception(type(batch_exc), batch_exc, batch_exc.__traceback__)
            )
            for line in formatted.rstrip().splitlines():  # One record per traceback line for log-aggregation tools
                logging.error(line)  # Emit one traceback line per log record
        except Exception as trace_log_err:  # Traceback serialization failure must not suppress the re-raise
            logging.error("! Failed to log batch exception traceback: %s", trace_log_err)

    @staticmethod
    def _pool_log_batch_exception(  # Log a batch-level exception with context
        batch_exc: Exception, batch_index: int, batch_size: int, max_threads: int, threading_mode: str
    ) -> None:
        """Log a batch-level exception with full context then re-raise it."""
        logging.error(  # Preserve legacy log prefix verbatim per Constitution VII (grep-searchable)
            "! Batch-level exception in execute_with_connection_pool_management: %s", batch_exc
        )
        logging.error(  # Log batch configuration context for post-mortem analysis
            "! Batch context: batch_index=%s, batch_size=%s, max_threads=%s, threading_mode=%s",
            batch_index,
            batch_size,
            max_threads,
            threading_mode,
        )
        ConnectionPoolExecutor._pool_emit_traceback_lines(batch_exc)  # Best-effort traceback capture
        raise batch_exc  # Re-raise so outer handlers see the original failure

    @staticmethod
    def _pool_run_all_batches(
        work_items: list[Any],
        batch_size: int,
        batch_config: BatchWorkerConfig,
        total_batches: int,
        threading_mode: str,
    ) -> tuple[list[Any], list[Any]]:
        """Split work items into batches, run each through the thread pool, and accumulate successes and failures."""
        successful_results: list[Any] = []  # Accumulate all successful worker results across all batches
        failed_items: list[Any] = []  # Accumulate all failed items across all batches for optional retry
        for batch_index in range(0, len(work_items), batch_size):  # Split work into equal-sized, bounded-memory batches
            try:  # Isolate each batch so a single failure doesn't silently skip remaining batches
                batch = work_items[batch_index : batch_index + batch_size]  # Slice the current batch from full list
                batch_number = (batch_index // batch_size) + 1  # 1-based batch number for readable progress logs
                batch_successful, batch_failed = ConnectionPoolExecutor._pool_process_batch_wait_loop(  # Batch run
                    batch, batch_number, total_batches, batch_config
                )
                successful_results.extend(batch_successful)  # Merge batch successes into the overall result list
                failed_items.extend(batch_failed)  # Merge batch failures into the overall failed list for retry
            except Exception as batch_exc:  # Batch-level exceptions need context logging before re-raise
                ConnectionPoolExecutor._pool_log_batch_exception(  # Log full batch context then re-raise
                    batch_exc, batch_index, batch_size, batch_config.max_threads, threading_mode
                )
        return successful_results, failed_items  # Return accumulated results so orchestrator can apply retries

    @staticmethod
    def _pool_apply_retry(
        failed_items: list[Any],
        retry_function: Any,
        connection_semaphore: Any,
        successful_results: list[Any],
        batch_description: str,
    ) -> list[Any]:
        """Run the caller-provided retry function on failed items, merging recoveries into successful_results."""
        logging.info("! Retrying %s failed %s...", len(failed_items), batch_description)  # Announce the retry phase
        retry_results, still_failed = retry_function(  # Run caller-provided retry logic with the semaphore constraint
            failed_items, connection_semaphore
        )
        successful_results.extend(retry_results)  # Merge recovered items into the success list in place
        # Cast Any->list[Any] for mypy strict return; retry_function's return type is dynamic
        return list(still_failed) if still_failed else []

    @staticmethod
    def _pool_prepare_execution(  # Resolve pool config + BatchWorkerConfig
        work_items: list[Any], batch_description: str, worker_function: Any
    ) -> tuple[BatchWorkerConfig, int, int, str]:
        """Resolve threading config, batch sizing, and BatchWorkerConfig for a pool execution run."""
        max_threads, connection_semaphore, batch_size, threading_mode = (  # Delegate to _pool_configure for sizing
            ConnectionPoolExecutor._pool_configure(work_items, batch_description)
        )
        total_batches = (len(work_items) + batch_size - 1) // batch_size  # Pre-compute total batch count
        batch_config = BatchWorkerConfig(  # Issue #431: bundle the 4 constant worker params per 5-Item Rule
            worker_function=worker_function,
            connection_semaphore=connection_semaphore,
            max_threads=max_threads,
            batch_description=batch_description,
        )
        return batch_config, batch_size, total_batches, threading_mode  # Bundle for caller

    @staticmethod
    def _pool_maybe_retry(
        failed_items: list[Any],
        retry_function: Any,
        batch_config: BatchWorkerConfig,
        successful_results: list[Any],
        batch_description: str,
    ) -> list[Any]:
        """Invoke retry helper only when failures exist AND a retry callable was supplied."""
        # WHY: extracted so execute() drops from 39 lines to <25 per STRUCT-LENGTH.
        if not (failed_items and retry_function):  # Fast-exit when nothing to retry
            return failed_items  # Return unchanged failure list
        return ConnectionPoolExecutor._pool_apply_retry(  # Retry failed items; merge recoveries in place
            failed_items, retry_function, batch_config.connection_semaphore, successful_results, batch_description
        )

    @staticmethod
    def _pool_finalize_execution(
        successful_results: list[Any], failed_items: list[Any], batch_description: str
    ) -> tuple[list[Any], list[Any]]:
        """Emit final pool-run tally logs and return the (successful, failed) tuple."""
        # WHY: extracted so execute() drops from 39 lines to <25 per STRUCT-LENGTH.
        logging.info(  # Log final success/failure tally for the whole pool run
            "! Processed %s %s successfully, %s failed",
            len(successful_results),
            batch_description,
            len(failed_items),
        )
        logging.debug(  # AFTER: pool run finished; log final counts
            "[POOL-EXECUTE] Pool execution finished: %s successful, %s failed",
            len(successful_results),
            len(failed_items),
        )
        return successful_results, failed_items  # Both result lists so callers can report or act on failures

    @staticmethod
    def execute(
        work_items: list[Any],
        worker_function: Any,
        batch_description: str = "items",
        retry_function: Any | None = None,
    ) -> tuple[list[Any], list[Any]]:
        """Execute work_items via pool-managed threading with semaphore limits, batching, retry, and progress."""
        logging.info(  # BEFORE: announce pool run entry with item count
            "[POOL-EXECUTE] Starting pool execution: %s items (%s)", len(work_items), batch_description
        )
        if not work_items:  # Empty work list is a valid fast-exit condition
            logging.info("* No %s to process.", batch_description)  # Tell caller why nothing ran
            return [], []  # Return empty results without configuring a thread pool
        batch_config, batch_size, total_batches, threading_mode = ConnectionPoolExecutor._pool_prepare_execution(
            work_items, batch_description, worker_function
        )  # Resolve threading + batching config in one helper
        successful_results, failed_items = ConnectionPoolExecutor._pool_run_all_batches(  # Run every batch
            work_items, batch_size, batch_config, total_batches, threading_mode
        )
        failed_items = ConnectionPoolExecutor._pool_maybe_retry(  # Retry (or no-op) then update failure list
            failed_items, retry_function, batch_config, successful_results, batch_description
        )
        return ConnectionPoolExecutor._pool_finalize_execution(  # Emit final tally logs and return tuple
            successful_results, failed_items, batch_description
        )
