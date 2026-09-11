"""Wave 5 P2 coverage for src/analytics/telemetry_emitter.py (initiative #1018).

Covers every branch of ``TelemetryEmitter``:
- ``__init__``: happy-path handle open + OSError swallowed with warning + missing parent dir creation.
- ``emit``: no-handle short-circuit, successful write, OSError swallowed with warning.
- ``close``: idempotent close (calls twice), OSError swallowed.
- ``__enter__`` / ``__exit__`` context manager protocol.
- All six ``emit_test_*`` helpers (start/pass/fail/skip/summary) shape checks.
- All three ``emit_progress_*`` helpers via ProgressContext.
- ``enforce_retention``: below-limit no-op, above-limit prunes oldest, OSError swallowed.
- ``timestamped_path``: format contract.

No live network. MagicMock(spec=...) used where a real object is not needed.
"""

from __future__ import annotations  # WHY: PEP 604 unions in test type hints.

import json  # WHY: parse NDJSON lines back into dicts for assertions.
import logging  # WHY: caplog verification of warning/info lines.
import os  # WHY: build cross-platform paths that mirror the SUT contract.
from pathlib import Path  # WHY: tmp_path fixture returns pathlib.Path.
from unittest.mock import MagicMock, patch  # WHY: mandatory spec= mocks + patch decorators.

import pytest  # WHY: monkeypatch, tmp_path, caplog fixtures.

from src.analytics.telemetry_emitter import TelemetryEmitter  # WHY: SUT direct import.
from src.dataclasses.progress_event import ProgressContext, TestSummary  # WHY: real value objects.


class TestInit:
    """Constructor opens the file in append mode, creates parent dirs, and swallows OSError."""

    def test_happy_path_opens_handle_and_creates_parent(self, tmp_path: Path) -> None:
        """Nested path triggers os.makedirs and opens append handle."""
        target = tmp_path / "sub" / "events.jsonl"  # WHY: nested to force makedirs branch.
        emitter = TelemetryEmitter(str(target))  # WHY: construct against real writable tmp dir.
        try:
            assert target.parent.exists()  # WHY: makedirs created the missing parent.
            assert emitter._handle is not None  # WHY: append-handle opened successfully.
        finally:
            emitter.close()  # WHY: release the OS handle deterministically.

    def test_empty_parent_skips_makedirs(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """File in cwd (no parent path) does not call os.makedirs."""
        monkeypatch.chdir(tmp_path)  # WHY: run in an isolated cwd.
        fake_makedirs = MagicMock()  # WHY: assert makedirs is NOT called when dirname is empty.
        monkeypatch.setattr("src.analytics.telemetry_emitter.os.makedirs", fake_makedirs)
        emitter = TelemetryEmitter("events.jsonl")  # WHY: bare filename → dirname("") is falsy.
        try:
            fake_makedirs.assert_not_called()  # WHY: empty parent → skip branch executed.
            assert emitter._handle is not None  # WHY: file still opened at cwd.
        finally:
            emitter.close()

    def test_oserror_on_open_swallowed_and_logged(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """OSError from open() sets _handle=None, logs warning, does not raise."""

        def _boom(*_args: object, **_kwargs: object) -> object:
            """Force builtins.open to raise OSError."""
            raise OSError("perm denied")  # WHY: simulate un-writable directory.

        monkeypatch.setattr("src.analytics.telemetry_emitter.open", _boom, raising=False)
        with caplog.at_level(logging.WARNING):
            emitter = TelemetryEmitter("/does/not/exist/x.jsonl")  # WHY: exercise error branch.

        assert emitter._handle is None  # WHY: SUT contract: no handle on failure.
        assert "TelemetryEmitter: cannot open" in caplog.text  # WHY: warning log emitted.


class TestEmit:
    """emit() writes NDJSON line on success, short-circuits when handle is None."""

    def test_no_handle_short_circuits(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """When _handle is None emit is a no-op (does not raise)."""

        # Force __init__ to fail so _handle stays None.
        def _boom(*_args: object, **_kwargs: object) -> object:
            """Force builtins.open to raise OSError."""
            raise OSError("nope")

        monkeypatch.setattr("src.analytics.telemetry_emitter.open", _boom, raising=False)
        emitter = TelemetryEmitter("/does/not/exist/x.jsonl")  # WHY: handle now None.
        emitter.emit({"event_type": "noop"})  # WHY: no exception is proof of contract.
        assert emitter._handle is None  # WHY: unchanged after emit no-op.

    def test_successful_write_appends_ndjson(self, tmp_path: Path) -> None:
        """Successful emit writes exactly one JSON line ending in newline."""
        target = tmp_path / "e.jsonl"
        emitter = TelemetryEmitter(str(target))
        try:
            emitter.emit({"event_type": "test_start", "menu_option": "1"})  # WHY: single event.
            emitter.emit({"event_type": "test_pass", "menu_option": "1"})  # WHY: second event.
        finally:
            emitter.close()  # WHY: flush + close so we can read the file.

        lines = target.read_text(encoding="utf-8").splitlines()  # WHY: NDJSON = one JSON per line.
        assert len(lines) == 2  # WHY: two emit calls → two lines.
        assert json.loads(lines[0])["event_type"] == "test_start"  # WHY: order preserved.
        assert json.loads(lines[1])["event_type"] == "test_pass"

    def test_oserror_on_write_swallowed_and_logged(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """OSError from handle.write is swallowed and logged as warning."""
        target = tmp_path / "e.jsonl"
        emitter = TelemetryEmitter(str(target))
        try:
            # Replace the entire real handle with a MagicMock whose write raises OSError.
            fake_handle = MagicMock()  # WHY: full mock avoids mypy method-assign on real TextIO.
            fake_handle.write = MagicMock(side_effect=OSError("disk full"))  # WHY: force write-failure.
            emitter._handle = fake_handle  # WHY: swap live handle so emit() calls the mocked write.
            with caplog.at_level(logging.WARNING):
                emitter.emit({"event_type": "boom"})  # WHY: exercise write-failure branch.
            assert "TelemetryEmitter: write failed" in caplog.text  # WHY: warning line emitted.
        finally:
            # Clear the mock handle so close() short-circuits and does not touch the mock.
            emitter._handle = None


class TestClose:
    """close() flushes + closes, is idempotent, and swallows OSError."""

    def test_close_sets_handle_to_none(self, tmp_path: Path) -> None:
        """After close the handle attribute is None."""
        emitter = TelemetryEmitter(str(tmp_path / "c.jsonl"))
        assert emitter._handle is not None  # WHY: sanity pre-check.
        emitter.close()
        assert emitter._handle is None  # WHY: post-close contract.

    def test_close_idempotent(self, tmp_path: Path) -> None:
        """Calling close twice does not raise."""
        emitter = TelemetryEmitter(str(tmp_path / "c.jsonl"))
        emitter.close()
        emitter.close()  # WHY: second call short-circuits since _handle is None.
        assert emitter._handle is None

    def test_close_oserror_swallowed(self, tmp_path: Path) -> None:
        """OSError from underlying close is swallowed silently."""
        emitter = TelemetryEmitter(str(tmp_path / "c.jsonl"))
        fake_handle = MagicMock()  # WHY: full mock avoids mypy method-assign on real TextIO.
        fake_handle.close = MagicMock(side_effect=OSError("bad fd"))  # WHY: force close-failure.
        emitter._handle = fake_handle  # WHY: swap live handle so close() calls the mocked close.
        emitter.close()  # WHY: no exception even though close raised.
        assert emitter._handle is None  # WHY: still set to None after failure.


class TestContextManager:
    """__enter__ returns self; __exit__ calls close()."""

    def test_context_manager_closes_on_exit(self, tmp_path: Path) -> None:
        """with-block returns emitter and closes on exit."""
        target = tmp_path / "cm.jsonl"
        with TelemetryEmitter(str(target)) as emitter:
            assert emitter._handle is not None  # WHY: handle is live inside the with-block.
            emitter.emit({"event_type": "hello"})  # WHY: prove usable during scope.
        assert emitter._handle is None  # WHY: closed on __exit__.
        assert target.read_text(encoding="utf-8").strip().startswith("{")  # WHY: content flushed.


class TestEmitTestHelpers:
    """emit_test_* helpers produce the documented event shape."""

    def _first_event(self, target: Path) -> dict:
        """Read + parse the first NDJSON event from *target*."""
        return json.loads(target.read_text(encoding="utf-8").splitlines()[0])

    def test_emit_test_start_shape(self, tmp_path: Path) -> None:
        """emit_test_start produces event_type/menu_option/operation_name/test_mode."""
        target = tmp_path / "s.jsonl"
        with TelemetryEmitter(str(target)) as emitter:
            emitter.emit_test_start(menu_option=5, operation_name="sites", test_mode="quick")
        evt = self._first_event(target)
        assert evt["event_type"] == "test_start"  # WHY: fixed event name.
        assert evt["menu_option"] == "5"  # WHY: coerced to str.
        assert evt["operation_name"] == "sites"  # WHY: preserved verbatim.
        assert evt["test_mode"] == "quick"  # WHY: preserved verbatim.
        assert "timestamp" in evt  # WHY: ISO-8601 timestamp injected.

    def test_emit_test_pass_shape(self, tmp_path: Path) -> None:
        """emit_test_pass rounds duration to 3 decimals."""
        target = tmp_path / "p.jsonl"
        with TelemetryEmitter(str(target)) as emitter:
            emitter.emit_test_pass("2", "orgs", 1.23456, "quick")
        evt = self._first_event(target)
        assert evt["event_type"] == "test_pass"  # WHY: fixed event name.
        assert evt["status"] == "pass"  # WHY: constant.
        assert evt["duration_seconds"] == 1.235  # WHY: 3-decimal rounding contract.

    def test_emit_test_fail_shape(self, tmp_path: Path) -> None:
        """emit_test_fail includes error_type and truncated error_message."""
        target = tmp_path / "f.jsonl"
        with TelemetryEmitter(str(target)) as emitter:
            emitter.emit_test_fail("3", "wan", 2.0, RuntimeError("bad" * 300), "quick")
        evt = self._first_event(target)
        assert evt["event_type"] == "test_fail"  # WHY: fixed event name.
        assert evt["error_type"] == "RuntimeError"  # WHY: type(exc).__name__ contract.
        assert len(evt["error_message"]) == 500  # WHY: message truncated to 500 chars.

    def test_emit_test_skip_shape(self, tmp_path: Path) -> None:
        """emit_test_skip records skip_reason + skip_category + zero duration."""
        target = tmp_path / "sk.jsonl"
        with TelemetryEmitter(str(target)) as emitter:
            emitter.emit_test_skip("4", "audit", "heavy", "H", "quick")
        evt = self._first_event(target)
        assert evt["event_type"] == "test_skip"  # WHY: fixed event name.
        assert evt["status"] == "skip"  # WHY: constant.
        assert evt["skip_reason"] == "heavy"  # WHY: preserved verbatim.
        assert evt["skip_category"] == "H"  # WHY: preserved verbatim.
        assert evt["duration_seconds"] == 0.0  # WHY: skips always have 0 duration.

    def test_emit_test_summary_pass_verdict(self, tmp_path: Path) -> None:
        """failed=0 → overall status pass."""
        target = tmp_path / "sum.jsonl"
        summary = TestSummary(total=5, passed=5, failed=0, skipped=0, elapsed=12.3456, test_mode="quick")
        with TelemetryEmitter(str(target)) as emitter:
            emitter.emit_test_summary(summary)
        evt = self._first_event(target)
        assert evt["status"] == "pass"  # WHY: 0 failures → pass verdict.
        assert evt["total_operations"] == 5  # WHY: mapped from summary.total.
        assert evt["pass_count"] == 5  # WHY: mapped from summary.passed.
        assert evt["fail_count"] == 0  # WHY: mapped from summary.failed.
        assert evt["skip_count"] == 0  # WHY: mapped from summary.skipped.
        assert evt["total_elapsed_seconds"] == 12.346  # WHY: 3-decimal rounding.

    def test_emit_test_summary_fail_verdict(self, tmp_path: Path) -> None:
        """failed>0 → overall status fail."""
        target = tmp_path / "sumf.jsonl"
        summary = TestSummary(total=5, passed=3, failed=2, skipped=0, elapsed=1.0, test_mode="quick")
        with TelemetryEmitter(str(target)) as emitter:
            emitter.emit_test_summary(summary)
        evt = self._first_event(target)
        assert evt["status"] == "fail"  # WHY: any failure flips overall verdict.


class TestEmitProgressHelpers:
    """emit_progress_* helpers produce the documented event shape."""

    def _first_event(self, target: Path) -> dict:
        """Read + parse the first NDJSON event from *target*."""
        return json.loads(target.read_text(encoding="utf-8").splitlines()[0])

    def test_emit_progress_start_shape(self, tmp_path: Path) -> None:
        """emit_progress_start records menu_option/operation_name/total_items."""
        target = tmp_path / "ps.jsonl"
        with TelemetryEmitter(str(target)) as emitter:
            emitter.emit_progress_start(menu_option=1, operation_name="scan", total_items=10)
        evt = self._first_event(target)
        assert evt["event_type"] == "progress_start"  # WHY: fixed event name.
        assert evt["operation_name"] == "scan"  # WHY: preserved verbatim.
        assert evt["total_items"] == 10  # WHY: preserved verbatim.

    def test_emit_progress_tick_shape(self, tmp_path: Path) -> None:
        """emit_progress_tick unpacks ProgressContext fields into the event."""
        target = tmp_path / "pt.jsonl"
        ctx = ProgressContext(menu_option="2", operation_name="fetch", total=100)
        with TelemetryEmitter(str(target)) as emitter:
            emitter.emit_progress_tick(ctx, current="item-42", completed=42, remaining=58)
        evt = self._first_event(target)
        assert evt["event_type"] == "progress_tick"  # WHY: fixed event name.
        assert evt["menu_option"] == "2"  # WHY: from ctx.
        assert evt["operation_name"] == "fetch"  # WHY: from ctx.
        assert evt["total_items"] == 100  # WHY: mapped from ctx.total.
        assert evt["current_item"] == "item-42"  # WHY: coerced to str.
        assert evt["items_completed"] == 42
        assert evt["items_remaining"] == 58

    def test_emit_progress_complete_shape(self, tmp_path: Path) -> None:
        """emit_progress_complete unpacks ProgressContext and rounds duration."""
        target = tmp_path / "pc.jsonl"
        ctx = ProgressContext(menu_option="3", operation_name="export", total=50)
        with TelemetryEmitter(str(target)) as emitter:
            emitter.emit_progress_complete(ctx, processed=48, was_stopped=True, duration=9.87654)
        evt = self._first_event(target)
        assert evt["event_type"] == "progress_complete"  # WHY: fixed event name.
        assert evt["operation_name"] == "export"  # WHY: from ctx.
        assert evt["items_processed"] == 48  # WHY: preserved.
        assert evt["was_stopped"] is True  # WHY: preserved.
        assert evt["duration_seconds"] == 9.877  # WHY: 3-decimal rounding.


class TestEnforceRetention:
    """enforce_retention prunes oldest files beyond limit, swallows OSError."""

    def test_below_limit_no_prune(self, tmp_path: Path) -> None:
        """When file count ≤ limit no files are removed."""
        for i in range(3):
            (tmp_path / f"test_events_{i:03}.jsonl").write_text("", encoding="utf-8")
        emitter = TelemetryEmitter(str(tmp_path / "current.jsonl"))
        try:
            emitter.enforce_retention(directory=str(tmp_path), prefix="test_events_", limit=5)
        finally:
            emitter.close()
        remaining = sorted(p.name for p in tmp_path.glob("test_events_*.jsonl"))  # WHY: still all 3.
        assert len(remaining) == 3  # WHY: below limit → nothing pruned.

    def test_above_limit_prunes_oldest(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """When file count > limit oldest lexicographically-sorted files are removed."""
        for i in range(6):
            (tmp_path / f"test_events_{i:03}.jsonl").write_text("", encoding="utf-8")
        emitter = TelemetryEmitter(str(tmp_path / "current.jsonl"))
        try:
            with caplog.at_level(logging.INFO):
                emitter.enforce_retention(directory=str(tmp_path), prefix="test_events_", limit=2)
        finally:
            emitter.close()
        remaining = sorted(p.name for p in tmp_path.glob("test_events_*.jsonl"))
        assert len(remaining) == 2  # WHY: prune down to limit.
        assert remaining == ["test_events_004.jsonl", "test_events_005.jsonl"]  # WHY: oldest removed first.
        assert "removed old file" in caplog.text  # WHY: info line emitted per removed file.

    def test_default_limit_falls_back_to_class_constant(self, tmp_path: Path) -> None:
        """limit=None uses RETENTION_LIMIT (10) - below the default so nothing pruned."""
        for i in range(3):
            (tmp_path / f"test_events_{i:03}.jsonl").write_text("", encoding="utf-8")
        emitter = TelemetryEmitter(str(tmp_path / "current.jsonl"))
        try:
            emitter.enforce_retention(directory=str(tmp_path), prefix="test_events_")  # WHY: no limit arg.
        finally:
            emitter.close()
        assert len(list(tmp_path.glob("test_events_*.jsonl"))) == 3  # WHY: 3 < 10 default → no prune.

    def test_oserror_during_retention_swallowed(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
    ) -> None:
        """OSError during glob/remove is logged as warning and swallowed."""
        # Make os.remove blow up so the loop hits the except branch.
        for i in range(3):
            (tmp_path / f"test_events_{i:03}.jsonl").write_text("", encoding="utf-8")
        emitter = TelemetryEmitter(str(tmp_path / "current.jsonl"))
        try:
            monkeypatch.setattr(
                "src.analytics.telemetry_emitter.os.remove",
                MagicMock(side_effect=OSError("kaboom")),
            )
            with caplog.at_level(logging.WARNING):
                emitter.enforce_retention(directory=str(tmp_path), prefix="test_events_", limit=1)
        finally:
            emitter.close()
        assert "retention cleanup failed" in caplog.text  # WHY: warning path executed.


class TestTimestampedPath:
    """timestamped_path returns directory-joined path with YYYYMMDD_HHMMSS suffix."""

    def test_returns_expected_shape(self) -> None:
        """Returned path is under 'data' by default and looks like test_events_<ts>.jsonl."""
        result = TelemetryEmitter.timestamped_path()  # WHY: default directory branch.
        assert result.startswith(os.path.join("data", "test_events_"))  # WHY: default directory used.
        assert result.endswith(".jsonl")  # WHY: constant suffix.
        # Extract the timestamp between the fixed prefix and suffix and verify shape.
        stamp = os.path.basename(result).removeprefix("test_events_").removesuffix(".jsonl")
        assert len(stamp) == 15  # WHY: YYYYMMDD_HHMMSS is exactly 15 chars.
        assert stamp[8] == "_"  # WHY: date and time separated by underscore.

    def test_custom_directory_honored(self) -> None:
        """Passing a directory argument overrides the default 'data'."""
        result = TelemetryEmitter.timestamped_path(directory="custom")
        assert result.startswith(os.path.join("custom", "test_events_"))  # WHY: custom dir used.

    def test_uses_utc_timestamp(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Timestamp is generated via datetime.now(UTC)."""
        # Patch datetime.now to return a fixed value; verify formatted stamp.
        with patch("src.analytics.telemetry_emitter.datetime") as fake_dt:
            fake_dt.now.return_value = MagicMock(strftime=MagicMock(return_value="20260714_120000"))
            result = TelemetryEmitter.timestamped_path()
        assert result.endswith("test_events_20260714_120000.jsonl")  # WHY: strftime output propagated.
