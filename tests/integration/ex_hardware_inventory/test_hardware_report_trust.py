"""Integration tests of the trust rules of the report (issue #4920).

The report must show every attempted switch, hold no credential, and run no formula. These tests run the whole CLI
flow with the real batch services, and they check the report file, the run folder, and the console.
"""

from __future__ import annotations

import pytest  # Parametrize and patch.

from src.operations.exporting.ex_hardware_inventory.report.export import ReportExporter  # The size limit.
from src.operations.exporting.ex_hardware_inventory.run.watch import BatchWatcher  # Simulate a cancel.
from tests.unit.ex_hardware_inventory.support.hardware_replies import HardwareReplies, ReplyItem  # Replies.
from tests.unit.ex_hardware_inventory.support.hardware_shells import make_uuid  # Invented identifiers.
from tests.unit.ex_hardware_inventory.support.hardware_world import ORG_A, SITE_1, World, run_menu  # Shared world.

SECRET = "SYNTHETIC-SECRET-VALUE"  # A value that must never reach the report.


def two_switches(world: World) -> None:
    """Script one site with two connected EX switches, and an answer that names the total."""
    world.org_token()
    world.mist.add(
        ORG_A,
        (SITE_1, "Site One"),
        [(make_uuid(101), "ex-01", "switch", "EX4100-48P"), (make_uuid(102), "ex-02", "switch", "EX4100-48P")],
    )
    world.answer = "RUN 2 TARGETS"


def reply_with(description: str) -> str:
    """Build a reply whose chassis holds the given description text."""
    chassis = ReplyItem(
        "chassis", [("name", "Chassis"), ("serial-number", "SER-1"), ("description", description)], attributes=""
    )
    return HardwareReplies.document(chassis)


class TestNoCredentialInTheReport:
    """A reply that holds a credential never becomes a row."""

    def test_the_reply_is_refused_and_its_value_is_in_no_file(
        self, world: World, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The decoder refuses the reply. The switch gets an outcome row, and no file holds the secret."""
        two_switches(world)
        world.shells.replies[make_uuid(101)] = reply_with(f"api_token={SECRET}")
        _, lines = run_menu(capsys)
        rows = world.rows()
        refused = [row for row in rows if row["device_name"] == "ex-01"]
        assert [row["record_type"] for row in refused] == ["device_outcome"] and refused[0][
            "collection_status"
        ] == "failed"
        assert refused[0]["collection_detail"] == "The reply was not a valid chassis inventory."
        assert {row["device_name"] for row in rows if row["record_type"] == "hardware_item"} == {"ex-02"}
        everything = "".join(path.read_text(encoding="utf-8") for path in world.tmp_path.rglob("*") if path.is_file())
        assert SECRET not in everything and SECRET not in "\n".join(
            lines
        )  # Not in the report, the folder, or the console.


class TestNoFormulaInTheReport:
    """A cell that a spreadsheet could read as a formula is neutralized end to end."""

    @pytest.mark.parametrize("text", ['=HYPERLINK("http://x.example.invalid")', "+SUM(1,2)", "-2+3", "@SUM(1)"])
    def test_a_cell_that_starts_with_a_formula_character_gets_an_apostrophe(
        self, world: World, capsys: pytest.CaptureFixture[str], text: str
    ) -> None:
        """The description of the chassis keeps its text, with a leading apostrophe."""
        two_switches(world)
        world.shells.replies[make_uuid(101)] = reply_with(text)
        run_menu(capsys)
        chassis = [row for row in world.rows() if row["device_name"] == "ex-01" and row["item_level"] == "0"]
        assert chassis and chassis[0]["item_description"] == "'" + text


class TestWriteFailures:
    """A report that cannot be published leaves no file and says so, and the saved replies stay."""

    def test_a_failed_write_leaves_no_report_and_keeps_the_run_folder(
        self, world: World, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The exporter reports failure: the console says so, no CSV exists, and the replies are kept."""
        two_switches(world)
        from src.foundation.runtime.config.source_dependency_resolver import SourceDependencyResolver

        monkeypatch.setattr(SourceDependencyResolver.DataExporter, "write_with_format_selection", lambda *a, **k: False)
        result, lines = run_menu(capsys)
        assert result == 0
        assert "The report file failed its check and was removed. See the log for the cause." in lines
        assert not list((world.tmp_path / "data").glob("ExHardwareInventory_*.csv"))
        assert len(list((world.tmp_path / "data" / "websocket-streams").rglob("*.xml"))) == 2

    @pytest.mark.parametrize("limit_bytes", [100, 0, -1])
    def test_a_report_over_the_size_limit_is_refused_and_the_replies_stay(
        self,
        world: World,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        limit_bytes: int,
    ) -> None:
        """A report that would pass the limit writes no file, and a limit of zero or less passes no report."""
        two_switches(world)
        monkeypatch.setattr(ReportExporter, "LIMIT_BYTES", limit_bytes)
        result, lines = run_menu(capsys)
        assert result == 0 and "The report would pass the size limit of 64 MiB. No file was written." in lines
        assert not list((world.tmp_path / "data").glob("ExHardwareInventory_*.csv"))
        assert len(list((world.tmp_path / "data" / "websocket-streams").rglob("*.xml"))) == 2


class TestCancelledRun:
    """A cancelled run gives cancelled rows, a partial status, and no open shell."""

    def test_ctrl_c_during_the_wait_cancels_the_queue_and_marks_the_run_partial(
        self, world: World, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """One interrupt stops the batch. The queued switches are cancelled rows, and every shell closes."""
        world.org_token()
        world.mist.add(
            ORG_A,
            (SITE_1, "Site One"),
            [(make_uuid(100 + index), f"ex-{index:02d}", "switch", "EX4100-48P") for index in range(1, 7)],
        )
        world.shells.hold_seconds = 0.4  # The first shell is still busy when the interrupt comes.
        world.answer = "RUN 6 TARGETS"
        monkeypatch.setenv("PORTAL_WS_HARDWARE_CONCURRENCY", "1")  # One shell at a time, so five are queued.
        original = BatchWatcher._final
        calls = {"count": 0}

        def interrupt_once(self: BatchWatcher) -> bool:
            """Raise the interrupt on the first poll, and behave normally afterward."""
            calls["count"] += 1
            if calls["count"] == 1:
                raise KeyboardInterrupt
            return original(self)

        monkeypatch.setattr(BatchWatcher, "_final", interrupt_once)
        _, lines = run_menu(capsys)
        rows = world.rows()
        statuses = [row["collection_status"] for row in rows if row["record_type"] == "device_outcome"]
        assert statuses.count("cancelled") >= 4  # The queued switches.
        assert lines[-1] == "Run status: partial" and world.shells.open == 0
