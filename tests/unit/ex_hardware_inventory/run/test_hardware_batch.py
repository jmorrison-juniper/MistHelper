"""Tests for the batch driver: preview, just-in-time preview, start, wait, and read."""

from __future__ import annotations

from pathlib import Path  # Build the run folder under the pytest temporary folder.
from types import SimpleNamespace  # A ledger double.
from unittest.mock import patch  # Count the calls that reach the manager.

import pytest  # Parametrize and check errors.

from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError  # Refusals of the service.
from src.mist.realtime.websocket_streams.live.sessions.settings import StreamSettings  # The limits.
from src.operations.exporting.ex_hardware_inventory.run.batch import (
    BatchPreview,
    BatchRunResult,
    BatchStack,
    OrganizationBatchRun,
)  # Units.
from src.operations.exporting.ex_hardware_inventory.run.watch import BatchWatcher  # The wait helper.
from tests.unit.ex_hardware_inventory.support.hardware_fakes import Batches, FakeStack  # Fakes.
from tests.unit.ex_hardware_inventory.support.hardware_replies import HardwareReplies  # Invented replies.

ORG_NAME = "Example Org"  # An invented organization name.
PHRASE_TWO = "RUN 2 TARGETS"  # The phrase of the service for two targets.


@pytest.fixture(autouse=True)
def fast_polling(monkeypatch: pytest.MonkeyPatch) -> None:
    """Poll without sleeping, so the tests stay fast."""
    monkeypatch.setattr(BatchWatcher, "POLL_SECONDS", 0)


def make_run(tmp_path: Path, concurrency: int = 3) -> tuple[OrganizationBatchRun, FakeStack, SimpleNamespace]:
    """Build a run over a fake stack whose session holds a ledger double."""
    ledger = SimpleNamespace(org_id=None)  # The ledger the binding must set.
    stack = FakeStack(tmp_path, ledger, concurrency)  # Fake service and manager.
    return OrganizationBatchRun(stack, ORG_NAME), stack, ledger  # type: ignore[arg-type]  # Duck-typed stack.


def save_reply(tmp_path: Path, index: int, text: str | None = None) -> None:
    """Write the saved reply of one switch where the service would have saved it."""
    path = tmp_path / "run-folder-1" / "hardware" / f"ex-{index:02d}.xml"  # The recorded relative name.
    path.parent.mkdir(parents=True, exist_ok=True)  # The service creates the folder.
    path.write_bytes((text or HardwareReplies.minimal(serial=f"SER-{index}")).encode("utf-8"))  # Exact bytes.


class TestBatchPreview:
    """The preview value reads the payload of the service."""

    def test_copies_the_payload_fields(self) -> None:
        """The preview keeps the identity list, the phrase, and the counts."""
        payload = Batches.payload([1, 2], {"offline": 3, "duplicate_device": 1})
        preview = BatchPreview.from_payload(payload, Batches.ORG, ORG_NAME)
        assert preview.phrase == PHRASE_TWO and preview.preview_id == "preview-2"  # What start needs.
        assert preview.target_keys == {"key-1", "key-2"}  # One key for each switch.
        assert dict(preview.excluded) == {"offline": 3, "duplicate_device": 1}  # The left-out counts.
        payload["targets"].clear()  # A later change of the payload...
        assert len(preview.targets) == 2  # ...cannot reach the preview.

    def test_an_empty_preview_has_no_target_and_counts(self) -> None:
        """The empty preview holds the exclusion counts and nothing to start."""
        preview = BatchPreview.empty(Batches.ORG, ORG_NAME, {"offline": 2})
        assert preview.targets == () and preview.preview_id == "" and dict(preview.excluded) == {"offline": 2}

    @pytest.mark.parametrize(("minutes", "expired"), [(5.0, False), (0.2, True), (-1.0, True)])
    def test_a_preview_counts_as_expired_inside_the_margin(self, minutes: float, expired: bool) -> None:
        """A preview that ends within 20 seconds is expired for the start."""
        preview = BatchPreview.from_payload(Batches.payload([1], minutes=minutes), Batches.ORG, ORG_NAME)
        assert preview.expired() is expired

    def test_a_preview_with_no_target_is_always_expired(self) -> None:
        """An empty preview stores nothing, so it can never start a batch."""
        assert BatchPreview.empty(Batches.ORG, ORG_NAME, {}).expired() is True


class TestPreview:
    """The preview asks the service for the fixed hardware preset under the ledger binding."""

    def test_sends_the_fixed_request_with_the_ledger_bound(self, tmp_path: Path) -> None:
        """The request is the preset, XML, revision 0, and the ledger has the organization during the call."""
        run, stack, ledger = make_run(tmp_path)
        stack.service.previews.append(Batches.payload([1, 2]))
        preview = run.preview()
        assert stack.service.calls[0] == (
            "preview",
            {"preset": "ex-hardware-xml", "format": "xml", "scope_revision": 0},
        )
        assert stack.service.ledger_orgs == [Batches.ORG]  # Bound during the read.
        assert ledger.org_id is None  # Restored afterward.
        assert preview.org_name == ORG_NAME and len(preview.targets) == 2  # Parsed.

    def test_an_organization_without_a_connected_switch_gives_an_empty_preview(self, tmp_path: Path) -> None:
        """The empty-selection refusal becomes an empty preview that keeps the counts."""
        run, stack, _ = make_run(tmp_path)
        stack.service.previews.append(
            StreamRequestError(
                "bad_request", "No online EX switches.", {"excluded": {"offline": 4, "unknown_status": 1}}
            )
        )
        preview = run.preview()
        assert preview.targets == () and dict(preview.excluded) == {"offline": 4, "unknown_status": 1}

    @pytest.mark.parametrize(
        "error",
        [
            StreamRequestError("picker_incomplete", "Target discovery did not complete."),
            StreamRequestError("target_limit", "The selection exceeds the target limit."),
            StreamRequestError("bad_request", "The preview request has an unknown field."),
            StreamRequestError("picker_request_failed", "Mist refused."),
        ],
    )
    def test_any_other_refusal_is_raised_and_the_ledger_is_restored(self, tmp_path: Path, error: Exception) -> None:
        """Discovery failures reach the operation, and the ledger returns to its earlier value."""
        run, stack, ledger = make_run(tmp_path)
        stack.service.previews.append(error)
        with pytest.raises(StreamRequestError):
            run.preview()
        assert ledger.org_id is None  # The binding ended with the call.


class TestRun:
    """The run starts the confirmed preview, waits, and returns one result for each target."""

    def test_starts_with_the_service_phrase_and_the_concurrency_and_reads_the_results(self, tmp_path: Path) -> None:
        """The start body is exact, the ledger stays bound until the end, and each target has a result."""
        run, stack, ledger = make_run(tmp_path, concurrency=4)
        stack.service.previews.append(Batches.payload([1, 2]))
        confirmed = run.preview()  # The operator confirms this preview.
        save_reply(tmp_path, 1)  # Only the first switch has a saved reply.
        stack.service.rows = [Batches.row(1), Batches.row(2, "failed", "completion_unproven")]
        result = run.run(confirmed)
        start = next(argument for name, argument in stack.service.calls if name == "start")
        assert start == {
            "preview_id": "preview-2",
            "confirmation": PHRASE_TWO,
            "concurrency": 4,
            "output": {"mode": "combined", "group_by": "site"},
        }  # The exact body.
        assert [item.state for item in result.results] == ["completed", "failed"]  # One result each, in order.
        assert result.results[0].xml_text is not None and "SER-1" in result.results[0].xml_text  # The reply.
        assert result.results[1].reason == "completion_unproven" and result.results[1].xml_text is None
        assert result.run_id == "run-folder-1" and result.cancelled is False and result.reason == ""
        assert set(stack.service.ledger_orgs[1:]) == {Batches.ORG}  # Bound for every call after the preview.
        assert ledger.org_id is None  # Restored.

    def test_a_valid_preview_is_not_read_again(self, tmp_path: Path) -> None:
        """A fresh preview starts directly, and no second discovery runs."""
        run, stack, _ = make_run(tmp_path)
        stack.service.previews.append(Batches.payload([1]))
        confirmed = run.preview()
        stack.service.rows = [Batches.row(1, "skipped", "offline")]
        run.run(confirmed)
        assert [name for name, _ in stack.service.calls].count("preview") == 1  # One discovery only.

    def test_an_expired_preview_previews_again_and_starts_the_new_one(self, tmp_path: Path) -> None:
        """The just-in-time preview replaces the old one, and its phrase and identifier start the batch."""
        run, stack, _ = make_run(tmp_path)
        stack.service.previews.append(Batches.payload([1, 2], minutes=-1.0))  # Already expired.
        confirmed = run.preview()
        fresh = Batches.payload([1, 2], minutes=5.0)
        fresh["preview_id"] = "preview-fresh"
        stack.service.previews.append(fresh)
        stack.service.rows = [Batches.row(1, "skipped", "offline"), Batches.row(2, "skipped", "offline")]
        run.run(confirmed)
        start = next(argument for name, argument in stack.service.calls if name == "start")
        assert start["preview_id"] == "preview-fresh"  # The new snapshot started.
        assert [name for name, _ in stack.service.calls].count("preview") == 2  # Discovery ran again.

    def test_a_new_target_stops_the_organization_without_a_start(self, tmp_path: Path) -> None:
        """A switch that the operator never saw means no batch, and each confirmed switch is skipped."""
        run, stack, _ = make_run(tmp_path)
        stack.service.previews.append(Batches.payload([1, 2], minutes=-1.0))
        confirmed = run.preview()
        stack.service.previews.append(Batches.payload([1, 2, 3]))  # Switch 3 appeared.
        result = run.run(confirmed)
        assert not any(name == "start" for name, _ in stack.service.calls)  # No shell opened.
        assert result.reason == "new_targets" and result.run_id == ""
        assert [item.state for item in result.results] == ["skipped", "skipped"]  # The confirmed ones.
        assert {item.reason for item in result.results} == {"new_targets"}

    def test_a_smaller_set_runs_and_the_missing_switch_is_listed_as_left_out(self, tmp_path: Path) -> None:
        """A confirmed switch that is gone gets a skipped result, and the rest run."""
        run, stack, _ = make_run(tmp_path)
        stack.service.previews.append(Batches.payload([1, 2], minutes=-1.0))
        confirmed = run.preview()
        stack.service.previews.append(Batches.payload([1]))  # Switch 2 went offline.
        save_reply(tmp_path, 1)
        stack.service.rows = [Batches.row(1)]
        result = run.run(confirmed)
        assert [(item.identity["device_id"], item.state) for item in result.results] == [
            ("device-1", "completed"),
            ("device-2", "skipped"),
        ]  # The batch result, then the left-out switch.
        assert result.results[1].reason == "no_longer_connected"

    def test_nothing_left_skips_every_confirmed_switch_without_a_start(self, tmp_path: Path) -> None:
        """When the fresh preview has no connected switch, the organization is not run."""
        run, stack, _ = make_run(tmp_path)
        stack.service.previews.append(Batches.payload([1, 2], minutes=-1.0))
        confirmed = run.preview()
        stack.service.previews.append(
            StreamRequestError("bad_request", "No online EX switches.", {"excluded": {"offline": 2}})
        )
        result = run.run(confirmed)
        assert not any(name == "start" for name, _ in stack.service.calls)  # No shell opened.
        assert result.reason == "no_longer_connected" and len(result.results) == 2

    def test_a_refused_start_is_raised_and_the_ledger_is_restored(self, tmp_path: Path) -> None:
        """A service refusal at the start reaches the operation."""
        run, stack, ledger = make_run(tmp_path)
        stack.service.previews.append(Batches.payload([1]))
        confirmed = run.preview()
        stack.service.start_error = StreamRequestError("limit_reached", "The live session limit was reached.")
        with pytest.raises(StreamRequestError):
            run.run(confirmed)
        assert ledger.org_id is None  # The binding ended.

    def test_paging_reads_every_row(self, tmp_path: Path) -> None:
        """A page size of 2 still gives all five results in order."""
        run, stack, _ = make_run(tmp_path)
        stack.service.previews.append(Batches.payload([1, 2, 3, 4, 5]))
        confirmed = run.preview()
        stack.service.page_size = 2
        stack.service.rows = [Batches.row(index, "skipped", "offline") for index in range(1, 6)]
        result = run.run(confirmed)
        assert [item.identity["device_id"] for item in result.results] == [f"device-{index}" for index in range(1, 6)]


class TestCancel:
    """Ctrl+C stops the batch, and the result is partial."""

    def test_one_interrupt_stops_the_batch_once_and_marks_the_run_cancelled(self, tmp_path: Path) -> None:
        """The first interrupt calls stop, the wait ends when the batch is final, and the run is cancelled."""
        run, stack, _ = make_run(tmp_path)
        stack.service.previews.append(Batches.payload([1, 2]))
        confirmed = run.preview()
        stack.service.interrupt_on_poll = [1]  # Ctrl+C during the first poll.
        stack.service.rows = [Batches.row(1, "completed"), Batches.row(2, "stopped", "cancelled")]
        save_reply(tmp_path, 1)
        result = run.run(confirmed)
        assert stack.manager.stops == ["session-1"]  # Stopped exactly once.
        assert result.cancelled is True  # Partial.
        assert [item.state for item in result.results] == ["completed", "stopped"]

    def test_a_second_interrupt_stops_waiting_at_once(self, tmp_path: Path) -> None:
        """A second Ctrl+C ends the wait, and a target that never ended becomes cancelled."""
        run, stack, _ = make_run(tmp_path)
        stack.service.previews.append(Batches.payload([1, 2]))
        confirmed = run.preview()
        stack.service.polls_until_final = 99  # The batch would never end by itself.
        stack.service.interrupt_on_poll = [1, 2]
        stack.service.rows = [Batches.row(1, "running"), Batches.row(2, "queued")]
        result = run.run(confirmed)
        assert stack.manager.stops == ["session-1"]  # Stopped once, not twice.
        assert [item.state for item in result.results] == ["stopped", "stopped"]  # Final states.
        assert {item.reason for item in result.results} == {"cancelled"} and result.cancelled is True

    def test_a_hung_batch_is_stopped_after_the_longest_wait(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A batch that never ends is stopped when the deadline passes."""
        monkeypatch.setattr(BatchWatcher, "SECONDS_PER_TURN", 0)  # The deadline is at once.
        run, stack, _ = make_run(tmp_path)
        stack.service.previews.append(Batches.payload([1]))
        confirmed = run.preview()
        stack.service.polls_until_final = 99
        stack.service.rows = [Batches.row(1, "running")]
        result = run.run(confirmed)
        assert stack.manager.stops == ["session-1"] and result.cancelled is True
        assert result.results[0].state == "failed" or result.results[0].state == "stopped"  # Final either way.


class TestFailureReasons:
    """The CLI reads the exact cause of a failed target from the batch row."""

    def test_a_failed_save_and_an_invalid_reply_keep_their_own_reasons(self, tmp_path: Path) -> None:
        """Both causes arrive as format_failed. The XML entry says which one it was."""
        run, stack, _ = make_run(tmp_path)
        stack.service.previews.append(Batches.payload([1, 2, 3]))
        confirmed = run.preview()
        saved = {"xml": {"state": "failed", "reason_code": "output_failed"}}  # The run folder refused the file.
        invalid = {"xml": {"state": "failed", "reason_code": "invalid_output"}}  # The reply did not decode.
        stack.service.rows = [
            {**Batches.row(1, "failed", "format_failed"), "formats": saved},
            {**Batches.row(2, "failed", "format_failed"), "formats": invalid},
            Batches.row(3, "failed", "format_failed"),  # An older row has no format entry.
        ]
        result = run.run(confirmed)
        assert [item.reason for item in result.results] == ["output_failed", "format_failed", "format_failed"]


class TestRunFolderSafety:
    """The CLI reads only files that stay inside the run folder."""

    @pytest.mark.parametrize("name", ["../outside.xml", "/etc/passwd.xml", "hardware/../../outside.xml"])
    def test_a_recorded_name_that_leaves_the_folder_gives_no_reply(self, tmp_path: Path, name: str) -> None:
        """A traversal or absolute name is refused, and the report shows a missing reply."""
        (tmp_path / "outside.xml").write_text(HardwareReplies.minimal(), encoding="utf-8")  # A file to steal.
        run, stack, _ = make_run(tmp_path)
        stack.service.previews.append(Batches.payload([1]))
        confirmed = run.preview()
        stack.service.rows = [Batches.row(1, files=[name])]
        result = run.run(confirmed)
        assert result.results[0].state == "completed" and result.results[0].xml_text is None  # Refused.

    def test_an_oversized_file_gives_no_reply(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """A file above the size limit is not read."""
        from src.operations.exporting.ex_hardware_inventory.run.watch import RunFolder

        monkeypatch.setattr(RunFolder, "MAX_BYTES", 10)
        save_reply(tmp_path, 1)
        run, stack, _ = make_run(tmp_path)
        stack.service.previews.append(Batches.payload([1]))
        confirmed = run.preview()
        stack.service.rows = [Batches.row(1)]
        assert run.run(confirmed).results[0].xml_text is None

    def test_a_file_that_is_not_utf8_or_is_missing_gives_no_reply(self, tmp_path: Path) -> None:
        """A missing file and a binary file both give no reply."""
        path = tmp_path / "run-folder-1" / "hardware"
        path.mkdir(parents=True)
        (path / "ex-01.xml").write_bytes(b"\xff\xfe\x00bad")  # Not UTF-8.
        run, stack, _ = make_run(tmp_path)
        stack.service.previews.append(Batches.payload([1, 2]))
        confirmed = run.preview()
        stack.service.rows = [Batches.row(1), Batches.row(2)]  # The second file does not exist.
        result = run.run(confirmed)
        assert [item.xml_text for item in result.results] == [None, None]

    def test_a_symbolic_link_that_leaves_the_folder_gives_no_reply(self, tmp_path: Path) -> None:
        """A link inside the run folder that points outside is refused."""
        outside = tmp_path / "secret.xml"
        outside.write_text(HardwareReplies.minimal(), encoding="utf-8")  # A file outside the run folder.
        folder = tmp_path / "run-folder-1" / "hardware"
        folder.mkdir(parents=True)
        try:  # Windows can refuse a link without the privilege.
            (folder / "ex-01.xml").symlink_to(outside)
        except OSError:
            pytest.skip("This account cannot create symbolic links.")
        run, stack, _ = make_run(tmp_path)
        stack.service.previews.append(Batches.payload([1]))
        confirmed = run.preview()
        stack.service.rows = [Batches.row(1)]
        assert run.run(confirmed).results[0].xml_text is None  # The link resolves outside the folder.


class TestStack:
    """The stack caps the concurrency by the shared transport capacity."""

    @pytest.mark.parametrize(("hardware", "sessions", "expected"), [(5, 20, 5), (5, 2, 2), (1, 5, 1), (3, 3, 3)])
    def test_concurrency_is_the_setting_capped_by_the_session_limit(
        self, hardware: int, sessions: int, expected: int
    ) -> None:
        """The value in use is the smaller of the two limits."""
        settings = StreamSettings(hardware_concurrency=hardware, max_sessions=sessions)
        stack = BatchStack(SimpleNamespace(), Batches.ORG, Path("unused"), settings)  # Builds the real services.
        assert stack.concurrency == expected
        assert stack.settings.shell_enabled is True  # The CLI opens shells.

    def test_shutdown_is_safe_to_repeat(self) -> None:
        """The second shutdown call stops nothing again, because the manager ignores a repeat."""
        stack = BatchStack(SimpleNamespace(), Batches.ORG, Path("unused"), StreamSettings())
        with patch.object(stack.manager, "stop_all", wraps=stack.manager.stop_all) as stop_all:  # The real stop runs.
            stack.shutdown()
            stack.shutdown()
        stop_all.assert_called_once_with("The portal is shutting down.")  # Only the first call stopped the sessions.


def test_skipped_results_keep_the_identity_and_the_reason() -> None:
    """The skipped factory builds one result for each target."""
    result = BatchRunResult.skipped([Batches.identity(1), Batches.identity(2)], ORG_NAME, "new_targets")
    assert [item.state for item in result.results] == ["skipped", "skipped"]
    assert all(item.org_name == ORG_NAME and item.xml_text is None for item in result.results)
