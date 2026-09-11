"""Wave 2 P2 coverage for src/refactors/connection_pool_executor.py (initiative #1018).

Covers `_resolve_fast_mode_env` late-binding, `ConnectionPoolExecutor`'s 15
`@staticmethod` helpers, and the top-level `execute()` orchestrator's empty and
non-empty branches. Threading primitives (`ThreadPoolExecutor`, `wait`, `tqdm`)
and MistHelper module attributes are monkeypatched so no real threads or network
calls occur. No source edits, no live I/O.
"""

from __future__ import annotations  # WHY: PEP 604 unions in method signatures under Python 3.10+.

import logging  # WHY: caplog level configuration + Semaphore type mocking.
import threading  # WHY: MagicMock(spec=threading.Semaphore) contract typing.
from unittest.mock import MagicMock  # WHY: FR-008 mandates MagicMock(spec=...) for collaborators.

import pytest  # WHY: monkeypatch, caplog, and raises fixtures.

from src.dataclasses.batch_worker import BatchWorkerConfig  # WHY: real frozen dataclass built for pool config.
from src.refactors import connection_pool_executor as cpe_mod  # WHY: import module for monkeypatch access.
from src.refactors.connection_pool_executor import (  # WHY: SUT direct imports.
    ConnectionPoolExecutor,
    _resolve_fast_mode_env,
)


def _make_config(  # WHY: helper builds a real BatchWorkerConfig with mocked collaborators for tests.
    worker: MagicMock | None = None,
    semaphore: MagicMock | None = None,
    max_threads: int = 4,
    batch_description: str = "widgets",
) -> BatchWorkerConfig:
    """Assemble a BatchWorkerConfig from mocked collaborators for the executor tests."""
    return BatchWorkerConfig(  # WHY: dataclass is frozen; construct once per test using the given mocks.
        worker_function=worker or MagicMock(name="worker"),  # WHY: worker callable is not exercised in helper tests.
        connection_semaphore=semaphore or MagicMock(spec=threading.Semaphore),  # WHY: sem spec for signature safety.
        max_threads=max_threads,  # WHY: exercised by _pool_process_batch_wait_loop and _pool_run_all_batches.
        batch_description=batch_description,  # WHY: appears in tqdm unit + log strings.
    )


class TestResolveFastModeEnv:
    """`_resolve_fast_mode_env` late-binds three fast-mode constants."""

    def test_returns_tuple_of_three_constants(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """The helper returns (use_conn_aware, max_conn, fallback_threads) sourced from live modules."""
        monkeypatch.setattr("MistHelper.FAST_MODE_FALLBACK_THREADS", 7, raising=False)  # WHY: publish fallback const.
        monkeypatch.setattr(  # WHY: publish concurrent-connection cap in the landing module.
            "src.refactors.fast_mode_constants.FAST_MODE_MAX_CONCURRENT_CONNECTIONS", 12, raising=False
        )
        monkeypatch.setattr(  # WHY: publish threading-strategy toggle in the landing module.
            "src.refactors.fast_mode_constants.FAST_MODE_USE_CONNECTION_AWARE_THREADING", True, raising=False
        )
        use_conn_aware, max_conn, fallback = _resolve_fast_mode_env()  # WHY: exercise the resolver.
        assert use_conn_aware is True  # WHY: verify the toggle was returned.
        assert max_conn == 12  # WHY: verify the cap was returned.
        assert fallback == 7  # WHY: verify the fallback thread count was returned.


class TestPoolResolveThreadSizing:
    """`_pool_resolve_thread_sizing` returns different values per strategy toggle."""

    def test_connection_aware_returns_max_conn(self) -> None:
        """With use_conn_aware=True, max_threads=max_conn and mode='connection-aware'."""
        max_threads, mode = ConnectionPoolExecutor._pool_resolve_thread_sizing(True, 8, 3)  # WHY: exercise branch A.
        assert max_threads == 8  # WHY: connection-aware caps threads at the pool max.
        assert mode == "connection-aware"  # WHY: strategy label is emitted for identification.

    def test_cpu_aware_uses_cpu_count_when_available(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """With use_conn_aware=False, max_threads=os.cpu_count() and mode='CPU-aware'."""
        monkeypatch.setattr("src.refactors.connection_pool_executor.os.cpu_count", lambda: 6)  # WHY: deterministic.
        max_threads, mode = ConnectionPoolExecutor._pool_resolve_thread_sizing(False, 8, 3)  # WHY: branch B.
        assert max_threads == 6  # WHY: CPU-aware uses cpu_count when available.
        assert mode == "CPU-aware"  # WHY: strategy label is emitted for identification.

    def test_cpu_aware_falls_back_when_cpu_count_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """If os.cpu_count() returns None, the fallback_threads argument is used."""
        monkeypatch.setattr("src.refactors.connection_pool_executor.os.cpu_count", lambda: None)  # WHY: simulate.
        max_threads, mode = ConnectionPoolExecutor._pool_resolve_thread_sizing(
            False, 8, 5
        )  # WHY: exercise or-fallback.
        assert max_threads == 5  # WHY: fallback_threads used when cpu_count returns None.
        assert mode == "CPU-aware"  # WHY: strategy label unchanged.


class TestPoolConfigure:
    """`_pool_configure` bundles thread-sizing decision + semaphore + batch size."""

    def test_returns_configured_tuple(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Full config tuple is returned when _resolve_fast_mode_env is monkeypatched to a known state."""
        monkeypatch.setattr(cpe_mod, "_resolve_fast_mode_env", lambda: (True, 4, 2))  # WHY: force known env values.
        monkeypatch.setattr(  # WHY: deterministic batch multiplier for the assertion below.
            "src.refactors.connection_pool_executor.FastModeDevicesPerThread.VALUE", 10, raising=False
        )
        max_threads, sem, batch_size, mode = ConnectionPoolExecutor._pool_configure(  # WHY: exercise helper.
            work_items=[object()] * 6, batch_description="devices"
        )
        assert max_threads == 4  # WHY: connection-aware mode caps threads at max_conn=4.
        assert isinstance(sem, threading.Semaphore)  # WHY: a real Semaphore is constructed for gating API calls.
        assert batch_size == 40  # WHY: max_threads (4) * FastModeDevicesPerThread.VALUE (10) = 40.
        assert mode == "connection-aware"  # WHY: matches the sizing decision.


class TestPoolCollectFutureResult:
    """`_pool_collect_future_result` returns ('success', payload) or ('failed', item)."""

    def test_success_when_future_returns_truthy(self) -> None:
        """Truthy future.result() surfaces as ('success', result)."""
        future = MagicMock()  # WHY: mock stand-in for a concurrent.futures.Future.
        future.result.return_value = [{"row": 1}]  # WHY: truthy payload triggers success branch.
        outcome, payload = ConnectionPoolExecutor._pool_collect_future_result(future, "item-a", _make_config())
        assert outcome == "success"  # WHY: truthy branch verdict.
        assert payload == [{"row": 1}]  # WHY: payload passthrough.

    def test_failed_when_future_returns_falsy(self) -> None:
        """Falsy future.result() (None/empty) surfaces as ('failed', item)."""
        future = MagicMock()  # WHY: mock stand-in for a concurrent.futures.Future.
        future.result.return_value = None  # WHY: falsy payload triggers failed branch.
        outcome, payload = ConnectionPoolExecutor._pool_collect_future_result(future, "item-b", _make_config())
        assert outcome == "failed"  # WHY: falsy branch verdict.
        assert payload == "item-b"  # WHY: original item is returned on failure for retry accounting.

    def test_failed_when_future_raises(self, caplog: pytest.LogCaptureFixture) -> None:
        """Future.result() raising an exception surfaces as ('failed', item) with an error log."""
        future = MagicMock()  # WHY: mock stand-in for a concurrent.futures.Future.
        future.result.side_effect = RuntimeError("worker boom")  # WHY: exercise exception branch.
        caplog.set_level(logging.ERROR)  # WHY: capture the error log line.
        outcome, payload = ConnectionPoolExecutor._pool_collect_future_result(future, "item-c", _make_config())
        assert outcome == "failed"  # WHY: exception branch verdict.
        assert payload == "item-c"  # WHY: original item is returned so retry can process it.
        assert any("Future exception" in r.getMessage() for r in caplog.records)  # WHY: log contract verified.


class TestPoolAdvanceProgressBar:
    """`_pool_advance_progress_bar` calls pbar.update(1); swallows exceptions."""

    def test_update_called_once(self) -> None:
        """The progress bar is advanced by exactly one on the happy path."""
        pbar = MagicMock()  # WHY: mock stand-in for the tqdm progress bar.
        ConnectionPoolExecutor._pool_advance_progress_bar(pbar)  # WHY: exercise happy path.
        pbar.update.assert_called_once_with(1)  # WHY: contract: pbar.update(1) is the single expected call.

    def test_swallows_pbar_update_exception(self, caplog: pytest.LogCaptureFixture) -> None:
        """A tqdm.update() exception is logged and swallowed (no raise)."""
        pbar = MagicMock()  # WHY: mock stand-in for the tqdm progress bar.
        pbar.update.side_effect = RuntimeError("tqdm boom")  # WHY: exercise exception branch.
        caplog.set_level(logging.ERROR)  # WHY: capture the error log line.
        ConnectionPoolExecutor._pool_advance_progress_bar(pbar)  # WHY: must NOT raise.
        assert any("Progress bar update failed" in r.getMessage() for r in caplog.records)  # WHY: log contract.


class TestRecordFutureOutcome:
    """`_record_future_outcome` mutates the accumulator based on the collected outcome."""

    def test_success_first_logged_toggles_flag(self, caplog: pytest.LogCaptureFixture) -> None:
        """Success path with first_logged=False appends to successful and toggles first_logged=True."""
        future = MagicMock()  # WHY: mock future.
        future.result.return_value = {"row": 1}  # WHY: truthy payload triggers success.
        accumulator: dict[str, object] = {"successful": [], "failed": [], "first_logged": False}  # WHY: fresh state.
        caplog.set_level(logging.DEBUG)  # WHY: capture the one-shot debug log.
        ConnectionPoolExecutor._record_future_outcome(future, "item-x", _make_config(), accumulator)  # WHY: SUT call.
        assert accumulator["successful"] == [{"row": 1}]  # WHY: payload appended.
        assert accumulator["first_logged"] is True  # WHY: one-shot flag toggled.
        assert any("First future result type" in r.getMessage() for r in caplog.records)  # WHY: log verified.

    def test_success_when_first_logged_true_skips_debug(self, caplog: pytest.LogCaptureFixture) -> None:
        """Success path with first_logged=True still appends but does not re-log."""
        future = MagicMock()  # WHY: mock future.
        future.result.return_value = {"row": 2}  # WHY: truthy payload triggers success.
        accumulator: dict[str, object] = {"successful": [], "failed": [], "first_logged": True}  # WHY: already logged.
        caplog.set_level(logging.DEBUG)  # WHY: verify no new debug record is emitted.
        ConnectionPoolExecutor._record_future_outcome(future, "item-y", _make_config(), accumulator)  # WHY: SUT call.
        assert accumulator["successful"] == [{"row": 2}]  # WHY: payload appended.
        assert not any("First future result type" in r.getMessage() for r in caplog.records)  # WHY: skip verified.

    def test_failed_appends_item(self) -> None:
        """Failed outcome appends the original item to the failed list."""
        future = MagicMock()  # WHY: mock future returning falsy value.
        future.result.return_value = None  # WHY: falsy payload triggers failed branch.
        accumulator: dict[str, object] = {"successful": [], "failed": [], "first_logged": False}  # WHY: fresh state.
        ConnectionPoolExecutor._record_future_outcome(future, "item-z", _make_config(), accumulator)  # WHY: SUT call.
        assert accumulator["failed"] == ["item-z"]  # WHY: original item appended for retry.


class TestPoolDrainWaitLoop:
    """`_pool_drain_wait_loop` drains futures via wait() and returns (successful, failed)."""

    def test_drain_collects_mixed_outcomes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A mix of successful + failed futures is fully drained into the expected lists."""
        success_future = MagicMock(name="success_future")  # WHY: mock resolving to a truthy payload.
        success_future.result.return_value = {"row": 1}  # WHY: truthy for success accumulator.
        failed_future = MagicMock(name="failed_future")  # WHY: mock resolving to None (failed).
        failed_future.result.return_value = None  # WHY: falsy triggers failed accumulator.
        future_to_item = {success_future: "item-1", failed_future: "item-2"}  # WHY: exercise both paths in one call.

        # WHY: sequence of wait() returns must fully drain the pending set across two iterations.
        wait_iterations = iter(  # WHY: first iteration returns success_future, second returns failed_future.
            [({success_future}, {failed_future}), ({failed_future}, set())]
        )
        monkeypatch.setattr(cpe_mod, "wait", lambda pending, return_when: next(wait_iterations))  # WHY: mock wait().
        monkeypatch.setattr(cpe_mod, "tqdm", lambda *a, **k: _NoopCtxMgr())  # WHY: neuter tqdm context manager.

        successful, failed = ConnectionPoolExecutor._pool_drain_wait_loop(  # WHY: exercise drain loop.
            future_to_item, "Batch 1/1", _make_config()
        )
        assert successful == [{"row": 1}]  # WHY: success accumulator has one entry.
        assert failed == ["item-2"]  # WHY: failed accumulator has the second item.


class _NoopCtxMgr:  # WHY: stand-in for tqdm() context manager used by drain loop.
    """Trivial context manager that exposes a MagicMock .update() attribute."""

    def __enter__(self) -> MagicMock:  # WHY: return a mock pbar so _pool_advance_progress_bar can call .update().
        self._pbar = MagicMock(name="pbar")  # WHY: capture pbar for potential later assertions.
        return self._pbar  # WHY: yielded to the with-block.

    def __exit__(self, *args: object) -> None:  # WHY: standard context-manager exit signature.
        return None  # WHY: no cleanup needed for the noop.


class TestPoolProcessBatchWaitLoop:
    """`_pool_process_batch_wait_loop` submits a batch to ThreadPoolExecutor and drains via `_pool_drain_wait_loop`."""

    def test_submits_batch_and_drains(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Each batch item is submitted via executor.submit and the drain loop returns final tallies."""
        submitted: list[object] = []  # WHY: capture the items that were submitted.

        class _FakeExecutor:  # WHY: stand-in ThreadPoolExecutor to observe submissions without spawning threads.
            def __init__(self, max_workers: int) -> None:  # WHY: accept the same signature as ThreadPoolExecutor.
                self.max_workers = max_workers  # WHY: recorded for potential assertions.

            def __enter__(self) -> _FakeExecutor:  # WHY: context-manager entry protocol.
                return self  # WHY: allow use in the `with` block.

            def __exit__(self, *args: object) -> None:  # WHY: context-manager exit protocol.
                return None  # WHY: no cleanup required.

            def submit(
                self, _fn: object, item: object, _sem: object
            ) -> MagicMock:  # WHY: capture item + return future.
                submitted.append(item)  # WHY: capture for later assertion.
                fut = MagicMock(name=f"future_for_{item}")  # WHY: return a mock future.
                fut.result.return_value = f"result_{item}"  # WHY: truthy → success branch.
                return fut  # WHY: hand the fake future back to the SUT.

        monkeypatch.setattr(cpe_mod, "ThreadPoolExecutor", _FakeExecutor)  # WHY: intercept pool construction.
        # WHY: patch drain loop to a trivial passthrough that just returns fixed lists (already unit-tested above).
        monkeypatch.setattr(
            ConnectionPoolExecutor,
            "_pool_drain_wait_loop",
            staticmethod(lambda fti, desc, cfg: (["S1", "S2"], ["F1"])),
        )
        successful, failed = ConnectionPoolExecutor._pool_process_batch_wait_loop(  # WHY: exercise SUT.
            batch=["a", "b", "c"], batch_number=1, total_batches=3, config=_make_config(max_threads=3)
        )
        assert submitted == ["a", "b", "c"]  # WHY: each batch item was submitted once.
        assert successful == ["S1", "S2"]  # WHY: drain loop's success payload propagated.
        assert failed == ["F1"]  # WHY: drain loop's failure payload propagated.


class TestPoolEmitTracebackLines:
    """`_pool_emit_traceback_lines` emits one log record per traceback line; swallows serialization errors."""

    def test_emits_lines_on_success(self, caplog: pytest.LogCaptureFixture) -> None:
        """Each traceback line is emitted as a separate error log record."""
        try:  # WHY: build a real exception with a traceback attached for realistic formatting.
            raise ValueError("test-boom")  # WHY: trigger a real traceback frame.
        except ValueError as caught:  # WHY: catch so we can pass the caught instance to the SUT.
            caplog.set_level(logging.ERROR)  # WHY: capture ERROR records.
            ConnectionPoolExecutor._pool_emit_traceback_lines(caught)  # WHY: exercise the traceback emitter.
        assert any("test-boom" in r.getMessage() for r in caplog.records)  # WHY: at least one line references the exc.

    def test_swallows_inner_exception(  # WHY: force traceback.format_exception to raise; verify soft failure.
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """If traceback.format_exception raises, the failure is logged and the outer flow continues."""
        import traceback as _tb  # WHY: patch the module.format_exception attribute.

        monkeypatch.setattr(_tb, "format_exception", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("fmt fail")))
        caplog.set_level(logging.ERROR)  # WHY: capture the fallback error log.
        ConnectionPoolExecutor._pool_emit_traceback_lines(ValueError("target"))  # WHY: exercise inner-raise path.
        assert any("Failed to log batch exception traceback" in r.getMessage() for r in caplog.records)  # WHY: log.


class TestPoolLogBatchException:
    """`_pool_log_batch_exception` logs context lines then re-raises."""

    def test_logs_and_reraises(self, caplog: pytest.LogCaptureFixture) -> None:
        """The original batch exception is re-raised after context lines are logged."""
        caplog.set_level(logging.ERROR)  # WHY: capture the context + traceback log lines.
        with pytest.raises(RuntimeError, match="batch-boom"):  # WHY: re-raise contract must hold.
            ConnectionPoolExecutor._pool_log_batch_exception(  # WHY: exercise the logger + re-raise path.
                RuntimeError("batch-boom"), batch_index=2, batch_size=100, max_threads=8, threading_mode="CPU-aware"
            )
        assert any("Batch-level exception" in r.getMessage() for r in caplog.records)  # WHY: primary context log.
        assert any("Batch context" in r.getMessage() for r in caplog.records)  # WHY: secondary context log.


class TestPoolRunAllBatches:
    """`_pool_run_all_batches` iterates over work_items in batch_size chunks."""

    def test_happy_path_accumulates_successes_and_failures(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Every batch's successes/failures are appended to the running lists."""
        calls: list[tuple[int, int]] = []  # WHY: record (batch_number, total_batches) per invocation.

        def _fake_process(  # WHY: passthrough that yields synthetic successes and failures per call.
            batch: list[object], batch_number: int, total_batches: int, cfg: BatchWorkerConfig
        ) -> tuple[list[object], list[object]]:
            calls.append((batch_number, total_batches))  # WHY: capture for assertion.
            return [f"ok_{batch_number}"], [f"fail_{batch_number}"]  # WHY: synthetic results per batch.

        monkeypatch.setattr(  # WHY: replace batch processor to keep test hermetic.
            ConnectionPoolExecutor, "_pool_process_batch_wait_loop", staticmethod(_fake_process)
        )
        work_items = list(range(10))  # WHY: 10 items, batch_size=4 → 3 batches of sizes 4/4/2.
        successful, failed = ConnectionPoolExecutor._pool_run_all_batches(  # WHY: exercise batching loop.
            work_items=work_items,
            batch_size=4,
            batch_config=_make_config(max_threads=2),
            total_batches=3,
            threading_mode="CPU-aware",
        )
        assert calls == [(1, 3), (2, 3), (3, 3)]  # WHY: three batches were dispatched in order.
        assert successful == ["ok_1", "ok_2", "ok_3"]  # WHY: successes accumulated.
        assert failed == ["fail_1", "fail_2", "fail_3"]  # WHY: failures accumulated.

    def test_batch_exception_is_logged_and_reraised(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A batch-level exception is funneled through `_pool_log_batch_exception` which re-raises."""

        def _boom(*_a: object, **_k: object) -> tuple[list[object], list[object]]:  # WHY: raise from batch processor.
            raise RuntimeError("batch-boom")  # WHY: force the outer try/except in _pool_run_all_batches.

        monkeypatch.setattr(  # WHY: force the batch processor to raise.
            ConnectionPoolExecutor, "_pool_process_batch_wait_loop", staticmethod(_boom)
        )
        with pytest.raises(RuntimeError, match="batch-boom"):  # WHY: re-raise contract preserved.
            ConnectionPoolExecutor._pool_run_all_batches(  # WHY: exercise the exception path.
                work_items=[1, 2, 3],
                batch_size=2,
                batch_config=_make_config(max_threads=2),
                total_batches=2,
                threading_mode="CPU-aware",
            )


class TestPoolApplyRetry:
    """`_pool_apply_retry` runs the retry function and merges recovered items."""

    def test_recovered_items_are_merged_and_still_failed_returned(self) -> None:
        """Retry results are appended to successful_results and still_failed is returned unchanged."""
        retry_fn = MagicMock(return_value=(["r1", "r2"], ["still-1"]))  # WHY: synthetic retry outcome.
        sem = MagicMock(spec=threading.Semaphore)  # WHY: sem passed through unchanged.
        successful: list[object] = ["s1"]  # WHY: pre-existing successes to test in-place merge.
        still_failed = ConnectionPoolExecutor._pool_apply_retry(  # WHY: exercise retry helper.
            failed_items=["f1"],
            retry_function=retry_fn,
            connection_semaphore=sem,
            successful_results=successful,
            batch_description="widgets",
        )
        retry_fn.assert_called_once_with(["f1"], sem)  # WHY: verify retry signature.
        assert successful == ["s1", "r1", "r2"]  # WHY: recovered items merged in place.
        assert still_failed == ["still-1"]  # WHY: unrecovered items returned.

    def test_still_failed_empty_returns_empty_list(self) -> None:
        """A falsy still_failed collapses to a plain empty list (not None or truthy)."""
        retry_fn = MagicMock(return_value=(["r1"], []))  # WHY: retry recovers everything.
        sem = MagicMock(spec=threading.Semaphore)  # WHY: sem passed through unchanged.
        still_failed = ConnectionPoolExecutor._pool_apply_retry(  # WHY: exercise empty-still-failed path.
            failed_items=["f1"],
            retry_function=retry_fn,
            connection_semaphore=sem,
            successful_results=[],
            batch_description="widgets",
        )
        assert still_failed == []  # WHY: empty list returned when nothing remains failed.


class TestPoolPrepareExecution:
    """`_pool_prepare_execution` delegates sizing to `_pool_configure` and packages a BatchWorkerConfig."""

    def test_returns_bundle(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Helper returns (batch_config, batch_size, total_batches, threading_mode) from `_pool_configure`."""
        # WHY: force _pool_configure to a known return so we test just the packaging logic.
        monkeypatch.setattr(
            ConnectionPoolExecutor,
            "_pool_configure",
            staticmethod(lambda items, desc: (3, MagicMock(spec=threading.Semaphore), 6, "CPU-aware")),
        )
        worker = MagicMock(name="worker")  # WHY: worker callable is embedded into the returned config.
        batch_config, batch_size, total_batches, mode = ConnectionPoolExecutor._pool_prepare_execution(  # WHY: SUT.
            work_items=[1, 2, 3, 4, 5, 6, 7], batch_description="devices", worker_function=worker
        )
        assert batch_size == 6  # WHY: passthrough from configure.
        assert mode == "CPU-aware"  # WHY: passthrough from configure.
        assert total_batches == 2  # WHY: ceil(7 / 6) == 2.
        assert batch_config.worker_function is worker  # WHY: worker passed through.
        assert batch_config.max_threads == 3  # WHY: threads passed through.
        assert batch_config.batch_description == "devices"  # WHY: description passed through.


class TestPoolMaybeRetry:
    """`_pool_maybe_retry` skips retry when failed_items or retry_function is falsy."""

    def test_no_failed_items_returns_unchanged(self) -> None:
        """When failed_items is empty, the function short-circuits and returns it unchanged."""
        retry_fn = MagicMock()  # WHY: even with a retry function present, empty failures skip retry.
        result = ConnectionPoolExecutor._pool_maybe_retry(  # WHY: exercise short-circuit path.
            failed_items=[],
            retry_function=retry_fn,
            batch_config=_make_config(),
            successful_results=[],
            batch_description="widgets",
        )
        assert result == []  # WHY: returned unchanged.
        retry_fn.assert_not_called()  # WHY: no retry function invocation.

    def test_no_retry_function_returns_unchanged(self) -> None:
        """When retry_function is None, the failed items are returned unchanged."""
        result = ConnectionPoolExecutor._pool_maybe_retry(  # WHY: exercise None-retry-function branch.
            failed_items=["f1"],
            retry_function=None,
            batch_config=_make_config(),
            successful_results=[],
            batch_description="widgets",
        )
        assert result == ["f1"]  # WHY: no retry attempted; original list returned.

    def test_both_present_invokes_retry(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When both are truthy, `_pool_apply_retry` is called and its return value is propagated."""
        monkeypatch.setattr(  # WHY: stub apply_retry to a synthetic passthrough for isolation.
            ConnectionPoolExecutor, "_pool_apply_retry", staticmethod(lambda failed, fn, sem, succ, desc: ["still-1"])
        )
        result = ConnectionPoolExecutor._pool_maybe_retry(  # WHY: exercise the branch that dispatches.
            failed_items=["f1"],
            retry_function=lambda a, b: ([], []),  # WHY: any truthy callable satisfies the guard.
            batch_config=_make_config(),
            successful_results=[],
            batch_description="widgets",
        )
        assert result == ["still-1"]  # WHY: apply_retry stub return value propagates.


class TestPoolFinalizeExecution:
    """`_pool_finalize_execution` emits final tally logs and returns the (successful, failed) tuple."""

    def test_returns_tuple_and_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        """Both lists are returned unchanged and a final tally line is emitted at INFO."""
        caplog.set_level(logging.INFO)  # WHY: capture the tally line.
        successful, failed = ConnectionPoolExecutor._pool_finalize_execution(  # WHY: exercise finalizer.
            successful_results=["s1", "s2"], failed_items=["f1"], batch_description="widgets"
        )
        assert successful == ["s1", "s2"]  # WHY: passthrough.
        assert failed == ["f1"]  # WHY: passthrough.
        assert any("Processed 2 widgets successfully, 1 failed" in r.getMessage() for r in caplog.records)  # WHY: log.


class TestExecute:
    """`ConnectionPoolExecutor.execute` orchestrates the full pipeline."""

    def test_empty_work_items_short_circuits(self, caplog: pytest.LogCaptureFixture) -> None:
        """Passing an empty work_items list returns ([], []) without configuring a pool."""
        caplog.set_level(logging.INFO)  # WHY: capture the fast-exit log.
        successful, failed = ConnectionPoolExecutor.execute(  # WHY: exercise fast-exit branch.
            work_items=[], worker_function=MagicMock(), batch_description="devices"
        )
        assert successful == []  # WHY: nothing to process.
        assert failed == []  # WHY: nothing to fail.
        assert any("No devices to process" in r.getMessage() for r in caplog.records)  # WHY: log verified.

    def test_non_empty_dispatches_full_pipeline(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Non-empty work_items flows through prepare → run_all_batches → maybe_retry → finalize."""
        # WHY: pin each sub-helper to a deterministic passthrough so we test only the wiring in execute().
        pinned_config = _make_config(max_threads=4)  # WHY: identity object we can assert flows through unchanged.
        monkeypatch.setattr(
            ConnectionPoolExecutor,
            "_pool_prepare_execution",
            staticmethod(lambda items, desc, worker: (pinned_config, 4, 2, "CPU-aware")),
        )
        monkeypatch.setattr(
            ConnectionPoolExecutor,
            "_pool_run_all_batches",
            staticmethod(lambda items, size, cfg, total, mode: (["ok1", "ok2"], ["fail1"])),
        )
        maybe_retry_called_with: dict[str, object] = {}  # WHY: capture args for assertion.

        def _fake_maybe_retry(  # WHY: verifies the return value propagates and args flow through.
            failed_items: list[object],
            retry_function: object,
            batch_config: BatchWorkerConfig,
            successful_results: list[object],
            batch_description: str,
        ) -> list[object]:
            maybe_retry_called_with.update(  # WHY: capture inputs for assertion.
                failed_items=failed_items,
                retry_function=retry_function,
                batch_config=batch_config,
                successful_results=successful_results,
                batch_description=batch_description,
            )
            return ["fail1-still"]  # WHY: synthetic still-failed list.

        monkeypatch.setattr(  # WHY: replace maybe_retry with a capture-and-return stub.
            ConnectionPoolExecutor, "_pool_maybe_retry", staticmethod(_fake_maybe_retry)
        )
        monkeypatch.setattr(  # WHY: verify finalize is called with the propagated results and returns them unchanged.
            ConnectionPoolExecutor, "_pool_finalize_execution", staticmethod(lambda succ, fail, desc: (succ, fail))
        )
        retry_fn = MagicMock(name="retry_fn")  # WHY: sentinel retry callable propagated through the pipeline.
        successful, failed = ConnectionPoolExecutor.execute(  # WHY: exercise the full orchestrator.
            work_items=[1, 2, 3, 4], worker_function=MagicMock(), batch_description="devices", retry_function=retry_fn
        )
        assert successful == ["ok1", "ok2"]  # WHY: results propagated through finalize passthrough.
        assert failed == ["fail1-still"]  # WHY: maybe_retry synthetic still-failed propagated.
        assert maybe_retry_called_with["failed_items"] == ["fail1"]  # WHY: run_all_batches failures forwarded.
        assert maybe_retry_called_with["retry_function"] is retry_fn  # WHY: sentinel identity preserved.
        assert maybe_retry_called_with["batch_config"] is pinned_config  # WHY: config identity preserved.
        assert maybe_retry_called_with["successful_results"] == ["ok1", "ok2"]  # WHY: successes forwarded.
        assert maybe_retry_called_with["batch_description"] == "devices"  # WHY: description forwarded.
