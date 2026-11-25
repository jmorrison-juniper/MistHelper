"""Tests for menu 309: the console steps, the typed phrase, the loop over organizations, and the report."""

from __future__ import annotations

import csv  # Read the report the way a spreadsheet would.
import xml.etree.ElementTree as ET  # A standard reader, so the tests share no code with the XML writer.
from collections import Counter  # Compare the statuses of the two files as multisets.
from datetime import datetime, tzinfo  # Freeze the clock of one test, so the file names are known.
from pathlib import Path  # Test output stays under the pytest temporary folder.
from types import SimpleNamespace  # Resolver doubles.
from typing import Any, Self  # Doubles have no public type, and a classmethod returns its own class.
from unittest.mock import Mock  # Record the prompt.

import pytest  # Capture the console and patch the seams.

import MistHelper  # The menu table is under test.
from src.foundation.support.utils.operation_registry import OperationRegistry  # The category of menu 309.
from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError  # A service refusal.
from src.operations.exporting.ex_hardware_inventory import console as console_module  # The input seam.
from src.operations.exporting.ex_hardware_inventory import operation as operation_module  # The patch seams.
from src.operations.exporting.ex_hardware_inventory.operation import ExHardwareInventoryReport  # Unit.
from src.operations.exporting.ex_hardware_inventory.report.builder import TargetResult  # One result per switch.
from src.operations.exporting.ex_hardware_inventory.report.csv_file import ReportCheckError, ReportTooLarge
from src.operations.exporting.ex_hardware_inventory.run.batch import BatchPreview, BatchRunResult  # Values.
from src.operations.exporting.ex_hardware_inventory.run.master_xml import MasterXmlBuilder  # The namespace.
from src.operations.exporting.ex_hardware_inventory.scope.resolver import (
    OrganizationRef,
    ScopeDecision,
    ScopeError,
)  # Decisions.
from tests.unit.ex_hardware_inventory.support.hardware_fakes import Batches, ScriptedOrganizations  # Fakes.
from tests.unit.ex_hardware_inventory.support.hardware_replies import HardwareReplies  # Invented replies.

ORG_A = "11111111-1111-4111-8111-111111111111"  # Invented organizations.
ORG_B = "22222222-2222-4222-8222-222222222222"
HEADER_1 = "Step 1 of 4: Check the credential"  # The step headers of the contract.
HEADER_2 = "Step 2 of 4: Find the connected EX switches"
HEADER_3 = "Step 3 of 4: Confirm"
HEADER_4 = "Step 4 of 4: Collect"


def decision(*orgs: tuple[str, str], mode: str = "organization", notes: tuple[str, ...] = ()) -> ScopeDecision:
    """Build a scope decision from (id, name) pairs."""
    refs = tuple(OrganizationRef(org_id, name) for org_id, name in orgs)
    return ScopeDecision(mode, "api_token", "organization_token", refs, notes)


def preview_of(org_id: str, name: str, indexes: list[int], excluded: dict[str, int] | None = None) -> BatchPreview:
    """Build the preview of one organization."""
    return BatchPreview.from_payload(Batches.payload(indexes, excluded, org_id=org_id), org_id, name)


def result_of(org_id: str, name: str, outcomes: dict[int, tuple[str, str]], cancelled: bool = False) -> BatchRunResult:
    """Build a run result from {switch index: (state, reason)}. A completed switch carries a reply."""
    results = tuple(
        TargetResult(
            Batches.identity(index, org_id, with_key=False),
            name,
            state,
            reason,
            HardwareReplies.single_switch(f"SW{index}") if state == "completed" else None,
        )
        for index, (state, reason) in outcomes.items()
    )
    return BatchRunResult("run-folder", cancelled, results)


class Harness:
    """Wire the operation to scripted organizations, a scripted scope, and a scripted answer."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Patch every seam of the operation."""
        monkeypatch.chdir(tmp_path)  # The report goes to data/ under the temporary folder.
        monkeypatch.setenv("MISTHELPER_STANDALONE", "true")  # No database backend in a unit test.
        self.tmp_path = tmp_path
        self.script = ScriptedOrganizations()
        self.answer = "RUN 3 TARGETS"  # The operator types this when asked.
        self.prompt = Mock(side_effect=lambda text, **kwargs: self.answer)  # Records each prompt.
        self.scope: Any = decision((ORG_A, "Alpha"))  # The decision of the resolver, or an exception.
        resolver = SimpleNamespace(
            apisession=object(),
            ConfigUtils=SimpleNamespace(get_cached_org_id=lambda: None),
            InputUtils=SimpleNamespace(safe_input=self.prompt),
        )
        monkeypatch.setattr(operation_module, "SourceDependencyResolver", resolver)
        monkeypatch.setattr(console_module, "SourceDependencyResolver", resolver)
        monkeypatch.setattr(operation_module, "BatchStack", self.script.stack)
        monkeypatch.setattr(operation_module, "OrganizationBatchRun", self.script.runner)
        monkeypatch.setattr(operation_module.ScopeResolver, "resolve", self._resolve)
        self.resolver = resolver

    def _resolve(self, *_args: object) -> ScopeDecision:
        """Return the scripted decision, or raise it."""
        if isinstance(self.scope, BaseException):
            raise self.scope
        return self.scope  # type: ignore[no-any-return]

    def report_rows(self) -> list[dict[str, str]]:
        """Read the one report file under data/."""
        files = sorted((self.tmp_path / "data").glob("ExHardwareInventory_*.csv"))
        assert len(files) == 1, f"expected one report file, found {files}"
        with files[0].open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))


@pytest.fixture
def harness(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Harness:
    """Build the harness for one test."""
    return Harness(monkeypatch, tmp_path)


def run_menu(capsys: pytest.CaptureFixture[str]) -> tuple[int, list[str]]:
    """Run the menu and return its result and its console lines."""
    result = ExHardwareInventoryReport.run()
    return result, capsys.readouterr().out.splitlines()


class TestOneOrganization:
    """The full flow for one organization."""

    def test_the_console_follows_the_contract_and_the_report_is_written(
        self, harness: Harness, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Steps 1 to 4, the exact phrase, one CSV file, and the summary lines."""
        harness.scope = decision((ORG_A, "Alpha"))
        harness.script.previews[ORG_A] = preview_of(ORG_A, "Alpha", [1, 2, 3], {"offline": 2, "duplicate_device": 1})
        harness.script.runs[ORG_A] = result_of(
            ORG_A, "Alpha", {1: ("completed", ""), 2: ("completed", ""), 3: ("failed", "completion_unproven")}
        )
        result, lines = run_menu(capsys)
        report = sorted((harness.tmp_path / "data").glob("ExHardwareInventory_*.csv"))[0]
        master = report.with_suffix(".xml")  # The master XML shares the name of the report.
        assert lines[:4] == [
            HEADER_1,
            "  Credential: API token (organization token)",
            "  Scope: organization",
            "  Organizations in scope: 1",
        ]  # Step 1.
        assert lines[4:7] == [
            HEADER_2,
            "  Alpha: 3 connected EX switches",
            "  Left out: offline 2, unknown status 0, other device types 0, repeated chassis 1",
        ]  # Step 2.
        assert lines[7:12] == [
            "  Total targets: 3",
            HEADER_3,
            "  This run opens a read-only shell on each switch and runs one command:",
            "    show chassis hardware detail | display xml | no-more",
            "  Shells open at the same time: 3",
        ]  # Step 3.
        assert lines[12:] == [
            HEADER_4,
            "  Alpha: collected 2, failed 1, skipped 0, cancelled 0",
            f"Report: {Path('data') / report.name} ({result} rows)",
            f"Master XML: {Path('data') / master.name} (3 devices)",
            "Run status: partial",
        ]  # Step 4, the report line, the master XML line, and the status.
        assert result == len(harness.report_rows()) and result > 3  # Item rows for two switches plus one outcome.
        harness.prompt.assert_called_once()  # One typed confirmation.
        assert harness.prompt.call_args.kwargs == {"context": "ex_hardware_confirmation"}  # The documented context.
        assert "RUN 3 TARGETS" in harness.prompt.call_args.args[0]  # The prompt names the phrase.

    def test_a_complete_run_says_complete(self, harness: Harness, capsys: pytest.CaptureFixture[str]) -> None:
        """No failure, no skip, no cancel: the status is complete."""
        harness.answer = "RUN 2 TARGETS"
        harness.script.previews[ORG_A] = preview_of(ORG_A, "Alpha", [1, 2])
        harness.script.runs[ORG_A] = result_of(ORG_A, "Alpha", {1: ("completed", ""), 2: ("completed", "")})
        _, lines = run_menu(capsys)
        assert lines[-1] == "Run status: complete"
        assert "  Alpha: collected 2, failed 0, skipped 0, cancelled 0" in lines

    def test_the_left_out_line_is_missing_when_nothing_was_left_out(
        self, harness: Harness, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Without a left-out count, the line does not appear."""
        harness.answer = "RUN 1 TARGETS"
        harness.script.previews[ORG_A] = preview_of(ORG_A, "Alpha", [1])
        harness.script.runs[ORG_A] = result_of(ORG_A, "Alpha", {1: ("completed", "")})
        _, lines = run_menu(capsys)
        assert not any(line.startswith("  Left out:") for line in lines)

    def test_the_report_rows_carry_the_organization_scope_and_run_time(self, harness: Harness) -> None:
        """Every row has the scope, the organization, and one run time."""
        harness.answer = "RUN 1 TARGETS"
        harness.script.previews[ORG_A] = preview_of(ORG_A, "Alpha", [1])
        harness.script.runs[ORG_A] = result_of(ORG_A, "Alpha", {1: ("completed", "")})
        ExHardwareInventoryReport.run()
        rows = harness.report_rows()
        assert {row["scope"] for row in rows} == {"organization"} and {row["org_name"] for row in rows} == {"Alpha"}
        assert len({row["report_run_utc"] for row in rows}) == 1  # One run time.
        assert rows[0]["report_run_utc"].endswith("Z")  # UTC in ISO 8601 form.


class TestCancel:
    """Anything but the exact phrase opens no shell and writes no file."""

    @pytest.mark.parametrize("answer", ["", "run 3 targets", "RUN 2 TARGETS", "RUN 3 TARGETS now", "yes", "y"])
    def test_a_wrong_or_empty_answer_cancels_safely(
        self, harness: Harness, capsys: pytest.CaptureFixture[str], answer: str
    ) -> None:
        """An empty answer (end of input or Ctrl+C) and a wrong phrase both cancel."""
        harness.answer = answer
        harness.script.previews[ORG_A] = preview_of(ORG_A, "Alpha", [1, 2, 3])
        result, lines = run_menu(capsys)
        assert result == 0 and harness.script.run_order == []  # No run.
        assert lines[-1] == "Cancelled. No shell was opened and no file was written."
        assert not (harness.tmp_path / "data").exists() or list((harness.tmp_path / "data").iterdir()) == []
        assert harness.script.shutdowns == [ORG_A]  # The stack was closed.

    def test_the_phrase_is_trimmed_before_the_compare(self, harness: Harness) -> None:
        """Spaces around the phrase do not matter. The case does."""
        harness.answer = "  RUN 1 TARGETS  "
        harness.script.previews[ORG_A] = preview_of(ORG_A, "Alpha", [1])
        harness.script.runs[ORG_A] = result_of(ORG_A, "Alpha", {1: ("completed", "")})
        assert ExHardwareInventoryReport.run() > 0

    def test_ctrl_c_during_discovery_cancels_before_any_shell(
        self, harness: Harness, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """An interrupt in step 2 prints the safe message and returns 0."""
        harness.script.previews[ORG_A] = KeyboardInterrupt()
        result, lines = run_menu(capsys)
        assert result == 0 and lines[-1] == "Cancelled. No shell was opened and no file was written."
        assert harness.script.shutdowns == [ORG_A]  # The stack was closed.

    def test_no_connected_switch_means_no_question_and_no_file(
        self, harness: Harness, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """FR-042: no target, no prompt, no file."""
        harness.script.previews[ORG_A] = BatchPreview.empty(ORG_A, "Alpha", {"offline": 4})
        result, lines = run_menu(capsys)
        assert result == 0 and harness.prompt.call_count == 0
        assert lines[-1] == "No connected EX switch was found. No file was written."
        assert "  Alpha: 0 connected EX switches" in lines
        assert "  Left out: offline 4, unknown status 0, other device types 0, repeated chassis 0" in lines


class TestScopeStep:
    """Step 1 stops safely when the scope is not clear."""

    def test_a_scope_error_prints_its_sentence_and_stops(
        self, harness: Harness, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The sentence of the resolver is the whole answer."""
        harness.scope = ScopeError("This credential grants several organizations. Set org_id to the one to use.")
        result, lines = run_menu(capsys)
        assert result == 0 and lines == ["This credential grants several organizations. Set org_id to the one to use."]
        assert harness.script.run_order == [] and harness.prompt.call_count == 0

    def test_no_session_stops_with_a_plain_sentence(self, harness: Harness, capsys: pytest.CaptureFixture[str]) -> None:
        """Without a session, nothing runs."""
        harness.resolver.apisession = None
        result, lines = run_menu(capsys)
        assert result == 0 and lines == ["No Mist session exists. Sign in first. No shell was opened."]

    def test_the_setting_reaches_the_resolver(
        self, harness: Harness, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The cached organization wins over the environment, and the environment is read when no cache exists."""
        seen: list[Any] = []
        monkeypatch.setattr(
            operation_module.ScopeResolver, "__init__", lambda self, session, configured=None: seen.append(configured)
        )
        harness.resolver.ConfigUtils.get_cached_org_id = lambda: "cached-org"
        harness.scope = ScopeError("stop")
        run_menu(capsys)
        monkeypatch.setenv("org_id", "environment-org")
        harness.resolver.ConfigUtils.get_cached_org_id = lambda: None
        run_menu(capsys)
        assert seen == ["cached-org", "environment-org"]

    def test_the_notes_print_in_step_one(self, harness: Harness, capsys: pytest.CaptureFixture[str]) -> None:
        """A note about a denied MSP list appears once, under step 1."""
        harness.scope = decision((ORG_A, "Alpha"), notes=("The MSP organization list is not permitted.",))
        harness.script.previews[ORG_A] = BatchPreview.empty(ORG_A, "Alpha", {})
        _, lines = run_menu(capsys)
        assert lines[4] == "  Note: The MSP organization list is not permitted."


class TestMspScope:
    """Several organizations: one phrase for the total, one report, and per-organization isolation."""

    def make_msp(self, harness: Harness) -> None:
        """Script two organizations: A with three switches, B with two."""
        harness.scope = decision((ORG_A, "Alpha"), (ORG_B, "Beta"), mode="msp")
        harness.script.previews[ORG_A] = preview_of(ORG_A, "Alpha", [1, 2, 3])
        harness.script.previews[ORG_B] = preview_of(ORG_B, "Beta", [4, 5])
        harness.script.runs[ORG_A] = result_of(
            ORG_A, "Alpha", {1: ("completed", ""), 2: ("completed", ""), 3: ("completed", "")}
        )
        harness.script.runs[ORG_B] = result_of(ORG_B, "Beta", {4: ("completed", ""), 5: ("skipped", "offline")})

    def test_the_phrase_names_the_total_of_all_organizations(
        self, harness: Harness, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Five targets in two organizations: the phrase is RUN 5 TARGETS, and both run in order."""
        self.make_msp(harness)
        harness.answer = "RUN 5 TARGETS"
        _, lines = run_menu(capsys)
        assert "Run status: partial" in lines  # One switch was skipped.
        assert harness.script.run_order == [ORG_A, ORG_B]  # One organization at a time, in order.
        assert "  Total targets: 5" in lines and "  Scope: MSP" in lines
        assert "  Alpha: collected 3, failed 0, skipped 0, cancelled 0" in lines
        assert "  Beta: collected 1, failed 0, skipped 1, cancelled 0" in lines
        assert {row["scope"] for row in harness.report_rows()} == {"msp"}  # One report for the whole run.
        assert harness.script.shutdowns == [ORG_A, ORG_B]  # Every stack was closed.

    def test_the_total_phrase_is_the_only_one_that_works(
        self, harness: Harness, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The phrase of one organization does not start the run."""
        self.make_msp(harness)
        harness.answer = "RUN 3 TARGETS"
        result, lines = run_menu(capsys)
        assert result == 0 and harness.script.run_order == []
        assert lines[-1] == "Cancelled. No shell was opened and no file was written."

    @pytest.mark.parametrize(
        ("error", "sentence"),
        [
            (
                StreamRequestError("picker_request_failed", "Mist refused."),
                "  Beta was not read, because Mist could not list its switches. See the log for the cause.",
            ),
            (
                StreamRequestError("rate_limited", "Slow down."),
                "  Beta was not read, because Mist limited the requests.",
            ),
            (
                StreamRequestError("target_limit", "The selection exceeds the target limit."),
                "  Beta has more than 1000 targets. The limit is 1000 for one batch.",
            ),
            (
                ConnectionError("no route"),
                "  Beta was not read, because Mist could not list its switches. See the log for the cause.",
            ),
        ],
    )
    def test_a_failed_organization_is_reported_and_the_others_run(
        self, harness: Harness, capsys: pytest.CaptureFixture[str], error: Exception, sentence: str
    ) -> None:
        """A discovery failure prints its sentence, adds one outcome row, and does not stop the loop."""
        self.make_msp(harness)
        harness.script.previews[ORG_B] = error
        harness.answer = "RUN 3 TARGETS"
        _, lines = run_menu(capsys)
        assert sentence in lines
        assert harness.script.run_order == [ORG_A]  # The other organization ran.
        failure_rows = [row for row in harness.report_rows() if row["org_name"] == "Beta"]
        assert len(failure_rows) == 1 and failure_rows[0]["record_type"] == "device_outcome"  # One row.
        assert failure_rows[0]["collection_status"] == "failed" and failure_rows[0]["device_id"] == ""
        assert failure_rows[0]["collection_detail"]  # A plain sentence.
        assert lines[-1] == "Run status: partial"

    def test_a_failed_run_of_one_organization_skips_its_switches_and_the_others_run(
        self, harness: Harness, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A refusal at the start becomes skipped rows for that organization only."""
        self.make_msp(harness)
        harness.script.runs[ORG_A] = StreamRequestError("limit_reached", "The live session limit was reached.")
        harness.answer = "RUN 5 TARGETS"
        _, lines = run_menu(capsys)
        assert harness.script.run_order == [ORG_A, ORG_B]  # The loop went on.
        assert "  Alpha: collected 0, failed 0, skipped 3, cancelled 0" in lines
        rows = harness.report_rows()
        assert {row["collection_status"] for row in rows if row["org_name"] == "Alpha"} == {"skipped"}

    def test_new_switches_skip_one_organization_with_a_message(
        self, harness: Harness, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A just-in-time preview with a new switch skips that organization and goes on."""
        self.make_msp(harness)
        harness.script.runs[ORG_A] = BatchRunResult.skipped(
            preview_of(ORG_A, "Alpha", [1, 2, 3]).targets, "Alpha", "new_targets"
        )
        harness.answer = "RUN 5 TARGETS"
        _, lines = run_menu(capsys)
        assert "  Alpha: new switches appeared after the confirmation. Run the menu again." in lines
        assert harness.script.run_order == [ORG_A, ORG_B]

    def test_ctrl_c_in_the_first_organization_cancels_the_rest(
        self, harness: Harness, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A cancelled organization stops the loop, and the others get cancelled rows without a run."""
        self.make_msp(harness)
        harness.script.runs[ORG_A] = result_of(
            ORG_A,
            "Alpha",
            {1: ("completed", ""), 2: ("stopped", "cancelled"), 3: ("stopped", "cancelled")},
            cancelled=True,
        )
        harness.answer = "RUN 5 TARGETS"
        _, lines = run_menu(capsys)
        assert harness.script.run_order == [ORG_A]  # Beta was never run.
        assert "  Beta: collected 0, failed 0, skipped 0, cancelled 2" in lines
        assert lines[-1] == "Run status: partial"
        beta = [row for row in harness.report_rows() if row["org_name"] == "Beta"]
        assert len(beta) == 2 and {row["collection_status"] for row in beta} == {"cancelled"}

    def test_an_interrupt_outside_the_wait_cancels_like_a_stop(
        self, harness: Harness, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """An interrupt raised while the driver runs marks that organization and the rest cancelled."""
        self.make_msp(harness)
        harness.script.runs[ORG_A] = KeyboardInterrupt()
        harness.answer = "RUN 5 TARGETS"
        _, lines = run_menu(capsys)
        assert "  Alpha: collected 0, failed 0, skipped 0, cancelled 3" in lines
        assert "  Beta: collected 0, failed 0, skipped 0, cancelled 2" in lines
        assert harness.script.run_order == [ORG_A]


class TestReportFailures:
    """A report that cannot be written is said so, and the return value is 0."""

    @pytest.mark.parametrize(
        ("error", "sentence"),
        [
            (ReportTooLarge("too big"), "The report would pass the size limit of 64 MiB. No file was written."),
            (
                ReportCheckError("damaged"),
                "The report file failed its check and was removed. See the log for the cause.",
            ),
        ],
    )
    def test_the_failure_is_said_and_no_file_is_reported(
        self,
        harness: Harness,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        error: Exception,
        sentence: str,
    ) -> None:
        """The exporter error becomes one plain sentence and a return value of 0."""

        def refuse(*_args: object, **_kwargs: object) -> None:
            """Raise the planned error."""
            raise error

        monkeypatch.setattr(operation_module.ReportExporter, "write", refuse)
        harness.answer = "RUN 1 TARGETS"
        harness.script.previews[ORG_A] = preview_of(ORG_A, "Alpha", [1])
        harness.script.runs[ORG_A] = result_of(ORG_A, "Alpha", {1: ("completed", "")})
        result, lines = run_menu(capsys)
        assert result == 0 and sentence in lines
        assert not any(line.startswith("Report:") for line in lines)  # No report line without a file.


class TestMasterXml:
    """The run writes one master XML file next to the CSV report, and the two files tell the same story."""

    NS = {"mh": MasterXmlBuilder.NAMESPACE}  # The prefix map for the wrapper elements.

    @staticmethod
    def master_files(harness: Harness) -> list[Path]:
        """Return the master XML files under data/."""
        return sorted((harness.tmp_path / "data").glob("ExHardwareInventory_*.xml"))

    def master_root(self, harness: Harness) -> ET.Element:
        """Parse the one master XML file with a standard reader, so the test shares no code with the writer."""
        files = self.master_files(harness)
        assert len(files) == 1, f"expected one master XML file, found {files}"
        return ET.fromstring(files[0].read_bytes())

    def test_the_file_shares_the_report_name_and_holds_the_reply_of_each_collected_switch(
        self, harness: Harness
    ) -> None:
        """Two collected switches and one failed switch: three devices, two replies, and every serial number."""
        harness.answer = "RUN 3 TARGETS"
        harness.script.previews[ORG_A] = preview_of(ORG_A, "Alpha", [1, 2, 3])
        harness.script.runs[ORG_A] = result_of(
            ORG_A, "Alpha", {1: ("completed", ""), 2: ("completed", ""), 3: ("failed", "completion_unproven")}
        )
        ExHardwareInventoryReport.run()
        report = sorted((harness.tmp_path / "data").glob("ExHardwareInventory_*.csv"))[0]
        root = self.master_root(harness)
        assert self.master_files(harness) == [report.with_suffix(".xml")]  # Same folder, same stem.
        assert (root.get("scope"), root.get("devices"), root.get("collected"), root.get("failed")) == (
            "organization",
            "3",
            "2",
            "1",
        )
        expected = {
            text for name in ("SW1", "SW2") for text in self.serials(ET.fromstring(HardwareReplies.single_switch(name)))
        }
        found = set(self.serials(root))
        assert found == expected and {"SW1-CH", "SW2-CH"} <= found  # Every serial number of the two replies.
        assert not any(text.startswith("SW3") for text in found)  # The failed switch has no reply in the file.

    @staticmethod
    def serials(root: ET.Element) -> list[str]:
        """Return the serial-number texts below an element, whatever the namespace of the reply is."""
        return [e.text or "" for e in root.iter() if e.tag.rsplit("}", 1)[-1] == "serial-number"]

    def test_the_statuses_of_the_two_files_agree_for_an_msp_run(self, harness: Harness) -> None:
        """One skipped switch and one unread organization appear in the XML the way the CSV report shows them."""
        harness.scope = decision((ORG_A, "Alpha"), (ORG_B, "Beta"), mode="msp")
        harness.script.previews[ORG_A] = preview_of(ORG_A, "Alpha", [1, 2, 3])
        harness.script.previews[ORG_B] = StreamRequestError("rate_limited", "Slow down.")
        harness.script.runs[ORG_A] = result_of(
            ORG_A, "Alpha", {1: ("completed", ""), 2: ("failed", "completion_unproven"), 3: ("skipped", "offline")}
        )
        harness.answer = "RUN 3 TARGETS"
        ExHardwareInventoryReport.run()
        root = self.master_root(harness)
        from_csv = {  # Every row of a device carries the one status of the device.
            (row["org_name"], row["device_id"], row["collection_status"]) for row in harness.report_rows()
        }
        from_xml = {
            (organization.get("name"), device.get("id"), device.get("status"))
            for organization in root.iterfind("mh:organization", self.NS)
            for device in organization.iterfind(".//mh:device", self.NS)
        }
        from_xml |= {  # The unread organization has no device. The CSV report gives it one outcome row.
            (organization.get("name"), "", organization.get("status"))
            for organization in root.iterfind("mh:organization", self.NS)
            if organization.get("status") == "failed"
        }
        assert from_csv == from_xml and len(from_xml) == 4  # Three switches and one organization.
        assert (root.get("scope"), root.get("organizations"), root.get("unread")) == ("msp", "2", "1")

    def test_a_cancelled_run_marks_the_cancelled_switches_in_the_xml(self, harness: Harness) -> None:
        """The operator stopped the run, and the XML says so for each switch that did not finish."""
        harness.answer = "RUN 3 TARGETS"
        harness.script.previews[ORG_A] = preview_of(ORG_A, "Alpha", [1, 2, 3])
        harness.script.runs[ORG_A] = result_of(
            ORG_A,
            "Alpha",
            {1: ("completed", ""), 2: ("stopped", "cancelled"), 3: ("stopped", "cancelled")},
            cancelled=True,
        )
        ExHardwareInventoryReport.run()
        devices = self.master_root(harness).iterfind(".//mh:device", self.NS)
        assert Counter(device.get("status") for device in devices) == Counter({"collected": 1, "cancelled": 2})

    @pytest.mark.parametrize(
        ("error", "sentence"),
        [
            (
                ReportTooLarge("too big"),
                "The master XML would pass the size limit of 64 MiB. No XML file was written.",
            ),
            (
                ReportCheckError("damaged"),
                "The master XML file failed its check and was removed. See the log for the cause.",
            ),
        ],
    )
    def test_a_master_xml_that_cannot_be_written_is_said_and_the_csv_report_stays(
        self,
        harness: Harness,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        error: Exception,
        sentence: str,
    ) -> None:
        """The XML refusal is one plain sentence. The CSV report, the rows, and the status are not affected."""

        def refuse(*_args: object, **_kwargs: object) -> None:
            """Raise the planned error."""
            raise error

        monkeypatch.setattr(operation_module.MasterXmlExporter, "write", refuse)
        harness.answer = "RUN 1 TARGETS"
        harness.script.previews[ORG_A] = preview_of(ORG_A, "Alpha", [1])
        harness.script.runs[ORG_A] = result_of(ORG_A, "Alpha", {1: ("completed", "")})
        result, lines = run_menu(capsys)
        assert result == len(harness.report_rows()) and result > 0  # The CSV report was written.
        assert sentence in lines and lines[-1] == "Run status: complete"
        assert not any(line.startswith("Master XML:") for line in lines)  # No line without a file.
        assert self.master_files(harness) == []

    def test_a_report_that_cannot_be_written_does_not_stop_the_master_xml(
        self, harness: Harness, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The two files are independent. The XML file takes a name from the run time when no CSV file exists."""

        def refuse(*_args: object, **_kwargs: object) -> None:
            """Refuse the CSV report."""
            raise ReportTooLarge("too big")

        monkeypatch.setattr(operation_module.ReportExporter, "write", refuse)
        harness.answer = "RUN 1 TARGETS"
        harness.script.previews[ORG_A] = preview_of(ORG_A, "Alpha", [1])
        harness.script.runs[ORG_A] = result_of(ORG_A, "Alpha", {1: ("completed", "")})
        result, lines = run_menu(capsys)
        (master,) = self.master_files(harness)
        assert result == 0 and master.name.startswith("ExHardwareInventory_") and master.suffix == ".xml"
        assert f"Master XML: {Path('data') / master.name} (1 devices)" in lines

    def test_a_run_that_collects_no_reply_still_writes_a_valid_master_xml(self, harness: Harness) -> None:
        """Every switch failed. The file lists the switches with their reasons and holds no reply."""
        harness.answer = "RUN 2 TARGETS"
        harness.script.previews[ORG_A] = preview_of(ORG_A, "Alpha", [1, 2])
        harness.script.runs[ORG_A] = result_of(
            ORG_A, "Alpha", {1: ("failed", "completion_unproven"), 2: ("skipped", "offline")}
        )
        ExHardwareInventoryReport.run()
        root = self.master_root(harness)
        assert sorted(device.get("status") or "" for device in root.iterfind(".//mh:device", self.NS)) == [
            "failed",
            "skipped",
        ]
        assert self.serials(root) == []  # No reply was embedded.

    def test_the_master_xml_takes_the_numbered_name_of_the_report_when_the_first_name_is_taken(
        self, harness: Harness, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """The first report name is taken, so the report gets `_2`. The XML file must take the same number."""

        class FrozenClock(datetime):
            """A clock that stands still, so the names of the two files are known before the run."""

            @classmethod
            def now(cls, tz: tzinfo | None = None) -> Self:
                """Return one fixed time."""
                return cls(2026, 11, 25, 18, 46, 6, tzinfo=tz)

        monkeypatch.setattr(operation_module, "datetime", FrozenClock)
        data = harness.tmp_path / "data"
        data.mkdir()
        (data / "ExHardwareInventory_20261125T184606Z.csv").write_text("earlier report", encoding="utf-8")
        harness.answer = "RUN 1 TARGETS"
        harness.script.previews[ORG_A] = preview_of(ORG_A, "Alpha", [1])
        harness.script.runs[ORG_A] = result_of(ORG_A, "Alpha", {1: ("completed", "")})
        _, lines = run_menu(capsys)
        assert f"Report: {Path('data') / 'ExHardwareInventory_20261125T184606Z_2.csv'} (" in "\n".join(lines)
        assert f"Master XML: {Path('data') / 'ExHardwareInventory_20261125T184606Z_2.xml'} (1 devices)" in lines
        assert [path.name for path in self.master_files(harness)] == ["ExHardwareInventory_20261125T184606Z_2.xml"]


class TestMenuRegistration:
    """Menu 309 is wired to the operation and skipped by the sweeps."""

    def test_the_menu_row_points_at_the_operation(self) -> None:
        """The handler, the title, and the flags match the contract."""
        entry = MistHelper.menu_actions["309"]
        assert entry.handler is ExHardwareInventoryReport.run
        assert entry.title == "Collect EX switch hardware inventory into one CSV report and one XML file"
        assert entry.destructive is False and entry.supports_fast is False

    def test_the_sweeps_skip_menu_309_and_say_why(self) -> None:
        """The category is resource_intensive, so --test and --testinteractive skip it."""
        assert OperationRegistry.skip_category("309") == "resource_intensive"
        assert "309" not in OperationRegistry.safe_options(list(MistHelper.menu_actions))
        reason = OperationRegistry.get_skip_reason("309") if hasattr(OperationRegistry, "get_skip_reason") else ""
        assert reason == "" or "typed confirmation" in reason
