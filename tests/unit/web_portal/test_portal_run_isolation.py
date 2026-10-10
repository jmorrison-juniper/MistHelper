"""Prove that concurrent portal runs keep their evidence isolated."""

from __future__ import annotations

import builtins
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from src.foundation.support.utils.menu_entry import MenuEntry
from web_portal.services.event_bus import PortalEventBus
from web_portal.services.operation import OperationExecutor, _RunLogHandler
from web_portal.services.output_scan import OutputFileScanner


def _menu_entry(menu_id: str, handler, title: str) -> MenuEntry:
    """Build one safe menu entry for a synchronized executor test."""
    return MenuEntry(  # Match the production menu record shape for the executor.
        menu_id=menu_id,  # Keep the dictionary key and menu record aligned.
        handler=handler,  # Run the synchronized evidence producer in the worker.
        title=title,  # Give the run a readable description for status events.
        category="safe",  # Keep the fixture operation non-destructive.
        destructive=False,  # Prevent the fixture from implying a cloud change.
        supports_fast=False,  # Fast-mode metadata does not affect evidence capture.
    )


def _emit(logger_name: str, message: str, level: int = logging.INFO) -> None:
    """Send one record through the root handlers without logger-level filtering."""
    record = logging.LogRecord(logger_name, level, __file__, 1, message, (), None)  # Use the worker thread owner.
    logging.getLogger().handle(record)  # Exercise the process-wide handler fan-out used by concurrent runs.


def _drain_events(bus: PortalEventBus, subscriber_id: str) -> list[dict]:
    """Return every queued event for one run subscriber."""
    events: list[dict] = []  # Preserve publication order for isolation assertions.
    while True:  # Read until the bounded subscriber queue becomes empty.
        event = bus.poll(subscriber_id, timeout=0)  # Avoid sleeps in the synchronized test.
        if event is None:  # An empty queue completes the deterministic drain.
            return events  # Return only the events for this subscriber filter.
        events.append(event)  # Keep the exact event type and payload.


def _wait_for_status(executor: OperationExecutor, run_id: str, status: str) -> dict:
    """Wait for one worker future and return its final status record."""
    run = executor._runs[run_id]  # Read the private record that owns the worker future.
    run["_future"].result(timeout=10)  # Bound the wait so a broken barrier cannot hang the suite.
    result = executor.get_run_status(run_id)  # Read the public response shape after completion.
    assert result is not None and result["status"] == status  # Prove the worker reached the expected terminal state.
    return result  # Return the stable response for evidence assertions.


@pytest.mark.parametrize("first_menu", ["11", "12"])
def test_concurrent_runs_keep_evidence_isolated_in_both_completion_orders(tmp_path, monkeypatch, first_menu):
    """Either worker can finish first without taking evidence from the other."""
    monkeypatch.setattr(os, "cpu_count", lambda: 3)  # Guarantee two operation workers on small CI runners.
    monkeypatch.setenv("DATA_DIR", str(tmp_path))  # Keep every operation file inside the test-owned data root.
    monkeypatch.setenv("PORTAL_RUN_LOG_MAX_ENTRIES", "3")  # Make seven owner-only discards cheap to prove.
    barrier = threading.Barrier(3)  # Hold both workers until the test proves simultaneous activity.
    release = {"11": threading.Event(), "12": threading.Event()}  # Control each completion order without sleeps.
    continued = {"11": threading.Event(), "12": threading.Event()}  # Prove the remaining worker continues capture.
    result_names = {"11": "AlphaResult.csv", "12": "BetaResult.csv"}  # Give each run a distinct preview result.
    cache_names = {"11": "SiteList.csv", "12": "SiteInventory.csv"}  # Give each run a distinct lower-priority file.
    bus = PortalEventBus()  # Use the production subscriber filters and event payloads.

    def build_handler(menu_number: str):
        """Build one worker that emits evidence before and after its release."""

        def handler() -> None:
            _emit("misthelper", f"{menu_number}-main-before")  # Add one owner-facing line before the overlap release.
            if menu_number == "11":  # Overflow one run without increasing the other run's discard count.
                for index in range(8):  # Ten total main lines with a cap of three discard exactly seven entries.
                    _emit("misthelper", f"{menu_number}-overflow-{index}")  # Add owner-only bounded log evidence.
            _emit("misthelper", f"Resolving source dependency {menu_number}-debug-before")  # Add owner debug evidence.
            (tmp_path / cache_names[menu_number]).write_text(
                "cache\n", encoding="utf-8"
            )  # Write a lower-priority file.
            barrier.wait(timeout=10)  # Prove both workers reached the overlap before either completes.
            release[menu_number].wait(timeout=10)  # Let the test select which scanner and handler stop first.

            def write_nested_evidence() -> None:
                """Write evidence from a nested pool worker with propagated ownership."""
                _emit("misthelper", f"{menu_number}-main-after")  # Capture a nested user-facing line.
                _emit("misthelper", f"Resolving source dependency {menu_number}-debug-after")  # Capture nested debug.
                (tmp_path / result_names[menu_number]).write_text(
                    "result\n",
                    encoding="utf-8",
                )  # Track a nested result write.

            with ThreadPoolExecutor(max_workers=1) as nested_pool:  # Match threaded production exporters.
                nested_pool.submit(write_nested_evidence).result(timeout=10)  # Propagate this run context.
            continued[menu_number].set()  # Tell the test that post-release evidence reached the worker.

        return handler  # Give the executor one stable callable for this menu.

    menu_actions = {  # Use distinct safe menus so the normal conflict rule permits overlap.
        menu: _menu_entry(menu, build_handler(menu), f"Operation {menu}")  # Bind each synchronized worker.
        for menu in ("11", "12")  # Cover two independent portal operations.
    }
    executor = OperationExecutor(menu_actions, None, None, bus)  # Run through the production worker pool.
    runs = {menu: executor._create_run(menu) for menu in ("11", "12")}  # Create stable run identifiers first.
    subscribers = {menu: bus.subscribe(runs[menu]["run_id"]) for menu in ("11", "12")}  # Filter one SSE stream per run.
    original_open = builtins.open  # Save the exact process hook for final cleanup proof.
    original_path_open = Path.open  # Save the exact pathlib hook for final cleanup proof.
    original_submit = ThreadPoolExecutor.submit  # Save nested context propagation for cleanup proof.
    try:
        for menu in ("11", "12"):  # Submit both workers before the main thread joins the barrier.
            runs[menu]["_future"] = executor._pool.submit(executor._execute_operation, runs[menu], {})  # Start the run.
        barrier.wait(timeout=10)  # Confirm both workers are active at the same synchronization point.
        second_menu = "12" if first_menu == "11" else "11"  # Select the worker that must remain active.
        release[first_menu].set()  # Finish the selected first worker while the other scanner stays active.
        first_result = _wait_for_status(executor, runs[first_menu]["run_id"], "completed")  # Read first completion.
        assert OutputFileScanner._hooks_installed is True  # Keep tracking active for the remaining worker.
        assert builtins.open is not original_open and Path.open is not original_path_open  # Keep both hooks installed.
        assert ThreadPoolExecutor.submit is not original_submit  # Keep nested ownership propagation installed.
        release[second_menu].set()  # Let the remaining worker emit evidence after the first cleanup.
        assert continued[second_menu].wait(timeout=10)  # Prove the remaining worker did not lose capture.
        second_result = _wait_for_status(executor, runs[second_menu]["run_id"], "completed")  # Read final completion.
        results = {first_menu: first_result, second_menu: second_result}  # Normalize assertions across both orders.
        for menu in ("11", "12"):  # Prove each run owns every stored and streamed evidence item.
            foreign = "12" if menu == "11" else "11"  # Name the marker that must never cross into this run.
            main_messages = [entry["message"] for entry in results[menu]["log_messages"]]  # Read user-facing lines.
            debug_messages = [entry["message"] for entry in results[menu]["debug_messages"]]  # Read debug lines.
            assert all(menu in message and foreign not in message for message in main_messages)  # Reject foreign logs.
            assert all(menu in message and foreign not in message for message in debug_messages)  # Reject debug leaks.
            assert results[menu]["output_files"] == [result_names[menu], cache_names[menu]]  # Keep preview order owned.
            expected_discards = 7 if menu == "11" else 0  # Only the overflowing owner can lose bounded log entries.
            assert results[menu]["dropped_log_count"] == expected_discards  # Keep discard accounting run-specific.
            events = _drain_events(bus, subscribers[menu])  # Read the run-filtered SSE evidence.
            assert events and all(event["data"].get("run_id") == runs[menu]["run_id"] for event in events)  # Own IDs.
            event_text = " ".join(str(event["data"].get("message", "")) for event in events)  # Join message payloads.
            assert foreign not in event_text  # Reject foreign log text even when the run_id filter matches.
        assert builtins.open is original_open and Path.open is original_path_open  # Restore exact hooks last.
        assert ThreadPoolExecutor.submit is original_submit  # Restore exact nested worker submission last.
        assert OutputFileScanner._active_scanners == {}  # Remove every owner registration after final cleanup.
    finally:
        release["11"].set()  # Unblock a worker if an earlier assertion failed.
        release["12"].set()  # Unblock the other worker before executor shutdown.
        executor.shutdown(10)  # Drain the worker pool and avoid leaked test threads.
        bus.stop()  # Clear subscriber queues and any heartbeat state.


@pytest.mark.parametrize("failing_menu", ["11", "12"])
def test_failed_worker_cleanup_keeps_the_other_run_active(tmp_path, monkeypatch, failing_menu):
    """Either worker can fail first without removing the remaining owner's hooks."""
    monkeypatch.setattr(os, "cpu_count", lambda: 3)  # Guarantee two operation workers on small CI runners.
    monkeypatch.setenv("DATA_DIR", str(tmp_path))  # Keep failure-order files inside the test-owned data root.
    barrier = threading.Barrier(3)  # Hold both workers active before the selected failure.
    release = {"11": threading.Event(), "12": threading.Event()}  # Control which worker exits first.
    other_menu = "12" if failing_menu == "11" else "11"  # Name the worker that must continue after failure.

    def build_handler(menu_number: str):
        """Build one worker that fails or writes evidence after release."""

        def handler() -> None:
            barrier.wait(timeout=10)  # Prove the failing and continuing scanners overlap.
            release[menu_number].wait(timeout=10)  # Let the test choose the first terminal worker.
            if menu_number == failing_menu:  # Exercise cleanup from the executor exception path.
                raise RuntimeError(f"{menu_number}-expected-failure")  # Give the failed run a stable cause.
            _emit("misthelper", f"{menu_number}-survived")  # Prove owner log capture remains installed.
            (tmp_path / f"{menu_number}-Result.csv").write_text("result\n", encoding="utf-8")  # Prove file tracking.

        return handler  # Give the executor one stable callable for this menu.

    menu_actions = {  # Use distinct safe menus so both workers can stay active.
        menu: _menu_entry(menu, build_handler(menu), f"Operation {menu}")  # Bind the failure-order handlers.
        for menu in ("11", "12")  # Cover both possible owners.
    }
    executor = OperationExecutor(menu_actions, None, None, None)  # Run the production capture and cleanup path.
    runs = {menu: executor._create_run(menu) for menu in ("11", "12")}  # Create both run records before submission.
    original_open = builtins.open  # Save the exact builtins hook for cleanup proof.
    original_path_open = Path.open  # Save the exact pathlib hook for cleanup proof.
    original_submit = ThreadPoolExecutor.submit  # Save nested context propagation for cleanup proof.
    try:
        for menu in ("11", "12"):  # Start both workers before the test joins their barrier.
            runs[menu]["_future"] = executor._pool.submit(executor._execute_operation, runs[menu], {})  # Start capture.
        barrier.wait(timeout=10)  # Confirm both scanner owners are active together.
        release[failing_menu].set()  # Fail the selected worker while the other scanner remains registered.
        failed = _wait_for_status(executor, runs[failing_menu]["run_id"], "failed")  # Read the failed terminal record.
        assert failing_menu in str(failed["error_message"])  # Preserve the selected worker's failure cause.
        assert OutputFileScanner._hooks_installed is True  # Keep process hooks for the remaining worker.
        assert ThreadPoolExecutor.submit is not original_submit  # Keep nested ownership propagation active.
        release[other_menu].set()  # Let the remaining worker emit owner evidence after failure cleanup.
        completed = _wait_for_status(executor, runs[other_menu]["run_id"], "completed")  # Read the surviving result.
        assert completed["output_files"] == [f"{other_menu}-Result.csv"]  # Keep the surviving owner's file.
        assert [entry["message"] for entry in completed["log_messages"]] == [f"{other_menu}-survived"]  # Keep its log.
        assert builtins.open is original_open and Path.open is original_path_open  # Restore exact hooks at the end.
        assert ThreadPoolExecutor.submit is original_submit  # Restore exact nested submission at the end.
        assert OutputFileScanner._active_scanners == {}  # Remove both owner registrations after failure and success.
    finally:
        release["11"].set()  # Unblock the first worker after an early assertion failure.
        release["12"].set()  # Unblock the second worker before pool shutdown.
        executor.shutdown(10)  # Drain all worker futures and avoid leaked test threads.


def test_single_run_keeps_raw_helper_thread_evidence(tmp_path, monkeypatch):
    """A sole active run keeps legacy evidence from a raw helper thread."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))  # Keep the helper output inside the test data root.

    def handler() -> None:
        """Write one log line and file from a raw helper thread."""

        def helper() -> None:
            _emit("misthelper", "Wrote 1 rows to data/HelperResult.csv")  # Announce the helper result.
            (tmp_path / "HelperResult.csv").write_text("result\n", encoding="utf-8")  # Write the helper result.

        thread = threading.Thread(target=helper)  # Match legacy operations that do not use an executor.
        thread.start()  # Run outside the operation worker context.
        thread.join(timeout=10)  # Bound the helper so the test cannot leak it.
        assert not thread.is_alive()  # Fail with a clear cause if the helper did not finish.

    executor = OperationExecutor({"11": _menu_entry("11", handler, "Helper operation")}, None, None, None)
    run = executor._create_run("11")  # Create one run so ownerless helper evidence is unambiguous.
    try:
        run["_future"] = executor._pool.submit(executor._execute_operation, run, {})  # Start production capture.
        result = _wait_for_status(executor, run["run_id"], "completed")  # Read the terminal response.
        assert [entry["message"] for entry in result["log_messages"]] == [
            "Wrote 1 rows to data/HelperResult.csv"
        ]  # Keep the helper log.
        assert result["output_files"] == ["HelperResult.csv"]  # Keep the helper result file.
    finally:
        executor.shutdown(10)  # Drain the worker and restore every process-wide hook.


def test_snapshot_failure_removes_partial_registration(tmp_path, monkeypatch):
    """A snapshot failure must not leak a handler, scanner, context, or hook."""
    monkeypatch.setenv("DATA_DIR", str(tmp_path))  # Keep the partial scanner inside the test data root.
    original_snapshot = OutputFileScanner.snapshot  # Keep the real method shape for the injected failure.

    def failing_snapshot(scanner: OutputFileScanner) -> None:
        scanner._start_write_tracking()  # Register hooks before the simulated setup failure.
        raise RuntimeError("snapshot setup failed")  # Exercise cleanup after partial registration.

    monkeypatch.setattr(OutputFileScanner, "snapshot", failing_snapshot)  # Inject the partial setup failure.
    executor = OperationExecutor(
        {"11": _menu_entry("11", lambda: None, "Snapshot failure")},
        None,
        None,
        None,
    )
    run = executor._create_run("11")  # Create one run for the failing capture path.
    try:
        run["_future"] = executor._pool.submit(executor._execute_operation, run, {})  # Start production cleanup.
        result = _wait_for_status(executor, run["run_id"], "failed")  # Read the expected terminal failure.
        assert result["error_message"] == "snapshot setup failed"  # Preserve the original setup cause.
        assert OutputFileScanner._active_scanners == {}  # Remove the partial scanner registration.
        assert OutputFileScanner._hooks_installed is False  # Restore every process-wide hook.
        assert _RunLogHandler._active_handlers == set()  # Remove the partial handler registration.
    finally:
        monkeypatch.setattr(OutputFileScanner, "snapshot", original_snapshot)  # Restore before pool shutdown.
        executor.shutdown(10)  # Drain the failed worker without a leaked handler.
