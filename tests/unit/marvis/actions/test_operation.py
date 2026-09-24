"""Tests for menu operation 270, the Marvis Actions export and bulk resolve.

Each test runs the real operation through ``MarvisActionsOperation.run`` with a
scripted ``input``, a fake Mist session, and a mocked exporter. The tests prove
the three modes, every refusal before the first request, the verify step, and
the log lines that the web dashboard reads.
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import patch

import pytest

from src.config import runtime_settings
from src.marvis.actions.model import MarvisActionRecord
from src.marvis.actions.operation import (
    DEFAULT_MAX_ACTIONS,
    EXPORT_ENDPOINT_NAME,
    EXPORT_FILENAME,
    NO_ROW_KEY_MESSAGE,
    RESULTS_ENDPOINT_NAME,
    RESULTS_FILENAME,
    STOP_SIGNAL_MESSAGE,
    MarvisActionsOperation,
    MarvisResolveResult,
    MarvisResolveWorkflow,
)
from src.troubleshooting.interactive_test_runner import UnattendedInteractiveInputProvider
from src.utils.input_utils import InputUtils
from tests.unit.marvis.actions.conftest import SITE_NAME, OperationHarness, make_raw

EXPORT_DONE = "Completed the Marvis Actions export and wrote results to OrgMarvisActions.csv"
RESOLVE_DONE = "Completed the Marvis Actions resolve and wrote results to OrgMarvisActionsResolveResults.csv"
DEFAULT_FILTERS = ("", "")  # A blank category answer and a blank subcategory answer both mean all.


def only_write(built: OperationHarness) -> tuple[list[dict[str, Any]], str, dict[str, Any]]:
    """Return the rows, the file name, and the keyword arguments of the one export write."""
    calls = built.exports()
    assert len(calls) == 1, calls
    args, kwargs = calls[0]
    return args[0], args[1], kwargs


def sent_bodies(built: OperationHarness) -> list[dict[str, Any]]:
    """Return the body of each resolve request, in order."""
    return [body for _, body in built.session.puts]


def run_menu(caplog: pytest.LogCaptureFixture) -> str:
    """Run the menu at INFO level and return the captured log text."""
    with caplog.at_level(logging.INFO):
        MarvisActionsOperation.run()
    return caplog.text


class TestExport:
    """Modes 1 and 2 write the report and never send a request."""

    def test_the_default_answers_export_every_action(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Blank answers give mode 1 with all topics, the read-only report."""
        raws = [make_raw(1), make_raw(2, status="validated"), make_raw(3, category="ap", symptom="ap_disconnect")]
        built = harness(raws, "", *DEFAULT_FILTERS)
        text = run_menu(caplog)
        rows, filename, kwargs = only_write(built)
        assert filename == EXPORT_FILENAME
        assert [row["suggestion_id"] for row in rows] == ["swoff-1", "swoff-2", "swoff-3"]
        assert kwargs["api_function_name"] == EXPORT_ENDPOINT_NAME
        assert kwargs["fieldnames"] == MarvisActionRecord.column_names()
        assert built.session.puts == []
        assert EXPORT_DONE in text

    def test_the_rows_hold_the_names_that_the_mist_ui_shows(
        self, harness: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The NOC engineer reads site, category, and topic names, not keys only."""
        built = harness([make_raw(1)], "", *DEFAULT_FILTERS)
        run_menu(caplog)
        row = only_write(built)[0][0]
        assert (row["site_name"], row["category_name"], row["symptom_name"]) == (SITE_NAME, "Wired", "Switch Offline")
        assert (row["topic"], row["status_name"], row["is_open"]) == ("switch/sw_offline", "Open", True)
        assert (row["entity_names"], row["detail_reason"]) == ("SW-LAB-01", "power loss")
        assert row["start_time_iso"] == "2023-11-14T22:14:20+00:00"

    def test_the_database_documents_keep_the_raw_values(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """The database receives the raw row plus the readable columns."""
        built = harness([make_raw(1)], "", *DEFAULT_FILTERS)
        run_menu(caplog)
        documents = only_write(built)[2]["backend_options"].raw_data
        assert len(documents) == 1
        assert documents[0]["uuid"] == make_raw(1)["uuid"]
        assert documents[0]["start_time"] == make_raw(1)["start_time"]
        assert documents[0]["details"]["disconnect_reason"] == "power loss"
        assert (documents[0]["site_name"], documents[0]["topic"]) == (SITE_NAME, "switch/sw_offline")
        assert "details_json" not in documents[0]

    def test_the_status_mix_is_logged_before_the_write(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """The operator sees the status counts of the report."""
        harness([make_raw(1), make_raw(2, status="validated"), make_raw(3)], "", *DEFAULT_FILTERS)
        assert "Selected Marvis Actions by status: AI Validated=1, Open=2" in run_menu(caplog)

    def test_mode_2_exports_the_open_actions_only(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """The In Progress and Reoccurred statuses are open, as in the Mist UI."""
        raws = [
            make_raw(1),
            make_raw(2, status="validated"),
            make_raw(3, status="inprogress"),
            make_raw(4, status="reoccured"),
        ]
        built = harness(raws, "2", *DEFAULT_FILTERS)
        run_menu(caplog)
        assert [row["suggestion_id"] for row in only_write(built)[0]] == ["swoff-1", "swoff-3", "swoff-4"]
        assert built.session.puts == []

    def test_mode_2_stops_when_no_action_is_open(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """The run stops before the filter prompts, and it writes no file."""
        built = harness([make_raw(1, status="validated")], "2")
        text = run_menu(caplog)
        assert "No open Marvis Actions exist in this organization. No file was written." in text
        assert built.exports() == []
        assert built.input is not None and len(built.input.prompts) == 1

    def test_a_repeated_action_is_written_one_time(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """A page overlap can repeat an action, and the database key must stay unique."""
        built = harness([make_raw(1), make_raw(1), make_raw(2)], "", *DEFAULT_FILTERS)
        run_menu(caplog)
        assert [row["suggestion_id"] for row in only_write(built)[0]] == ["swoff-1", "swoff-2"]

    def test_every_page_of_the_list_is_read(
        self, harness: Any, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A report must hold every action, not the first page only."""
        monkeypatch.setattr(runtime_settings, "DEFAULT_API_PAGE_LIMIT", 2)
        built = harness([make_raw(number) for number in range(1, 6)], "", *DEFAULT_FILTERS)
        run_menu(caplog)
        assert [query["page"] for query in built.session.list_gets()] == ["1", "2", "3"]
        assert len(only_write(built)[0]) == 5

    def test_a_failed_write_is_reported_as_a_failure(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """The run must never report success after a failed write."""
        built = harness([make_raw(1)], "", *DEFAULT_FILTERS)
        built.resolver.DataExporter.write_with_format_selection.return_value = False
        text = run_menu(caplog)
        assert "MistHelper could not write OrgMarvisActions.csv. Read the export error above." in text
        assert EXPORT_DONE not in text

    def test_the_unattended_test_pass_runs_the_read_only_export(self, harness: Any) -> None:
        """The --testinteractive pass takes each default, so it must reach mode 1 and never mode 3."""
        built = harness([make_raw(1)])
        provider = UnattendedInteractiveInputProvider("270")
        with patch.object(InputUtils, "safe_input", provider.answer):
            MarvisActionsOperation.run()
        expected = [
            ("marvis_actions.mode", "1"),
            ("marvis_actions.category", "all"),
            ("marvis_actions.subcategory", "all"),
        ]
        assert provider.answers == expected
        assert len(built.exports()) == 1
        assert built.session.puts == []


class TestFilterStep:
    """The category and the subcategory answers decide the rows."""

    RAWS = (
        make_raw(1),
        make_raw(2),
        make_raw(3, category="ap", symptom="ap_disconnect"),
        make_raw(4, symptom="port_flap"),
    )

    def exported_ids(self, built: OperationHarness) -> list[str]:
        """Return the suggestion IDs of the one export write."""
        return [row["suggestion_id"] for row in only_write(built)[0]]

    def test_a_category_and_a_subcategory_key_narrow_the_report(
        self, harness: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The keys switch and sw_offline keep the switch offline actions only."""
        built = harness(list(self.RAWS), "", "switch", "sw_offline")
        run_menu(caplog)
        assert self.exported_ids(built) == ["swoff-1", "swoff-2"]

    def test_a_pair_answer_keeps_one_topic(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """A pair names exactly one topic."""
        built = harness(list(self.RAWS), "", "", "ap/ap_disconnect")
        run_menu(caplog)
        assert self.exported_ids(built) == ["swoff-3"]

    def test_the_numbers_follow_the_logged_tables(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Category 2 is switch, and subcategory 1 of switch is port_flap."""
        built = harness(list(self.RAWS), "", "2", "1")
        text = run_menu(caplog)
        assert self.exported_ids(built) == ["swoff-4"]
        assert "switch/port_flap" in text

    def test_an_unknown_category_writes_nothing(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """A typo must never widen the report."""
        built = harness(list(self.RAWS), "", "swich")
        text = run_menu(caplog)
        assert "MistHelper could not match the category answer 'swich'" in text
        assert text.rstrip().endswith("No file was written.")
        assert built.exports() == []

    def test_an_unknown_subcategory_writes_nothing(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """A typo in the second step stops the run too."""
        built = harness(list(self.RAWS), "", "", "sw_ofline")
        assert "MistHelper could not match the subcategory answer 'sw_ofline'" in run_menu(caplog)
        assert built.exports() == []

    def test_a_known_category_without_actions_writes_nothing(
        self, harness: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The web dashboard offers every category, so a category without actions is not a typo."""
        built = harness(list(self.RAWS), "", "security")
        text = run_menu(caplog)
        assert "No Marvis Actions match the filter. No file was written." in text
        assert "could not match" not in text
        assert built.exports() == []

    def test_a_canceled_category_prompt_writes_nothing(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """A Ctrl+C returns an empty answer, and the run must stop instead of taking all."""
        built = harness(list(self.RAWS), "", KeyboardInterrupt())
        text = run_menu(caplog)
        assert "No Marvis Actions match the filter. No file was written." in text
        assert built.exports() == []


class TestStops:
    """The run stops with one clear line when it has nothing to do."""

    def test_an_unknown_mode_stops_before_any_api_call(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """An unknown mode must not guess an action."""
        built = harness([make_raw(1)], "4")
        assert "MistHelper could not match the mode answer '4'. Enter 1, 2, or 3." in run_menu(caplog)
        assert built.session.gets == []

    def test_an_organization_without_actions_writes_nothing(
        self, harness: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An empty list is a clear answer, not a failure."""
        built = harness([], "")
        assert "No Marvis Actions exist in this organization. No file was written." in run_menu(caplog)
        assert built.exports() == []

    def test_a_refused_list_read_writes_nothing(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """A partial report must never look complete."""
        built = harness([make_raw(1)], "")
        built.session.list_statuses.append(403)
        text = run_menu(caplog)
        assert (
            "MistHelper could not read the Marvis Actions list. The API returned HTTP 403. No file was written." in text
        )
        assert built.exports() == []

    def test_mode_3_without_open_actions_asks_nothing_more(
        self, harness: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The lab organization holds no open action, so a live mode 3 run ends here."""
        built = harness([make_raw(1, status="validated"), make_raw(2, status="resolved")], "3")
        text = run_menu(caplog)
        assert "No open Marvis Actions exist in this organization. No action was changed." in text
        assert built.input is not None and len(built.input.prompts) == 1
        assert built.session.puts == []
        assert built.exports() == []


class TestResolve:
    """Mode 3 previews, confirms, resolves, verifies, and writes the results."""

    RAWS = (make_raw(1), make_raw(2), make_raw(3, status="validated"))

    def resolve_answers(self, confirmation: str = "RESOLVE 2", code: str = "", comment: str = "") -> tuple[str, ...]:
        """Return the six answers of one mode 3 run."""
        return ("3", *DEFAULT_FILTERS, code, comment, confirmation)

    def test_the_confirmed_run_resolves_each_open_action(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """Each open action gets one request, and the verify read confirms it."""
        built = harness(list(self.RAWS), *self.resolve_answers())
        text = run_menu(caplog)
        bodies = sent_bodies(built)
        assert [body["row_key"] for body in bodies] == ["synthetic-row-key-0001", "synthetic-row-key-0002"]
        assert {(body["status"], body["label"], body["comment"]) for body in bodies} == {("resolved", "suggested", "")}
        assert len({body["resolve_time"] for body in bodies}) == 1
        assert built.pacer.pace.call_count == 2
        assert "Marvis Actions resolve summary: resolved=2 sent_unverified=0 error=0 not_sent=0 skipped=0" in text
        assert text.rstrip().endswith(RESOLVE_DONE)

    def test_the_results_file_holds_one_row_for_each_action(
        self, harness: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The results rows carry the outcome, the HTTP status, and the verified status."""
        built = harness(list(self.RAWS), *self.resolve_answers())
        run_menu(caplog)
        rows, filename, kwargs = only_write(built)
        assert (filename, kwargs["api_function_name"]) == (RESULTS_FILENAME, RESULTS_ENDPOINT_NAME)
        assert kwargs["fieldnames"] == MarvisResolveResult.column_names()
        assert [(row["outcome"], row["http_status"], row["verified_status"]) for row in rows] == [
            ("resolved", 200, "resolved"),
            ("resolved", 200, "resolved"),
        ]
        resolve_time = sent_bodies(built)[0]["resolve_time"]
        assert rows[0]["result_id"] == f"{make_raw(1)['uuid']}_{resolve_time}"
        assert (rows[0]["previous_status"], rows[0]["site_name"], rows[0]["topic"]) == (
            "open",
            SITE_NAME,
            "switch/sw_offline",
        )

    def test_the_preview_lists_the_oldest_action_first(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """The operator reads each action before the confirmation, in request order."""
        built = harness([make_raw(2), make_raw(1)], *self.resolve_answers())
        text = run_menu(caplog)
        assert "Preview of the 2 open Marvis Actions that this run resolves:" in text
        assert text.index("SW-LAB-01 | Open") < text.index("SW-LAB-02 | Open")
        assert [body["row_key"] for body in sent_bodies(built)] == ["synthetic-row-key-0001", "synthetic-row-key-0002"]

    def test_the_other_method_code_sends_the_comment(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """The alias other names the nonsuggested code, and the comment reaches every request."""
        answers = self.resolve_answers(code="other", comment="Bounced the uplink port.")
        built = harness(list(self.RAWS), *answers)
        run_menu(caplog)
        pairs = {(body["label"], body["comment"]) for body in sent_bodies(built)}
        assert pairs == {("nonsuggested", "Bounced the uplink port.")}
        assert {row["comment"] for row in only_write(built)[0]} == {"Bounced the uplink port."}

    def test_the_other_method_code_without_a_comment_changes_nothing(
        self, harness: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The Mist UI requires a comment for this code, and the confirmation is never asked."""
        built = harness(list(self.RAWS), "3", *DEFAULT_FILTERS, "2", "")
        assert "No value provided for the comment" in run_menu(caplog)
        assert built.input is not None and len(built.input.prompts) == 5
        assert built.session.puts == []
        assert built.exports() == []

    def test_a_bad_code_changes_nothing(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """A code typo stops the run before the comment prompt."""
        built = harness(list(self.RAWS), "3", *DEFAULT_FILTERS, "7")
        assert "MistHelper could not match the resolution code answer '7'" in run_menu(caplog)
        assert built.session.puts == []

    @pytest.mark.parametrize("confirmation", ["RESOLVE 3", "resolve 2", "yes", ""])
    def test_a_wrong_or_blank_confirmation_changes_nothing(
        self, harness: Any, caplog: pytest.LogCaptureFixture, confirmation: str
    ) -> None:
        """Only the exact text RESOLVE 2 can start the requests."""
        built = harness(list(self.RAWS), *self.resolve_answers(confirmation=confirmation))
        text = run_menu(caplog)
        assert "No action was changed" in text or "so no action was changed" in text
        assert built.session.puts == []
        assert built.exports() == []

    def test_a_closed_stream_at_the_confirmation_changes_nothing(
        self, harness: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An SSH disconnect must never confirm a change."""
        built = harness(list(self.RAWS), "3", *DEFAULT_FILTERS, "", "")
        run_menu(caplog)
        assert built.session.puts == []

    def test_no_request_goes_to_a_closed_action(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """A closed action keeps its code, its comment, and its time."""
        built = harness([make_raw(1, status="validated"), make_raw(2)], *self.resolve_answers("RESOLVE 1"))
        run_menu(caplog)
        assert [body["row_key"] for body in sent_bodies(built)] == ["synthetic-row-key-0002"]

    def test_the_cap_resolves_the_oldest_actions_first(
        self, harness: Any, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A filter wider than the cap leaves the newest actions open for a later run."""
        built = harness([make_raw(3), make_raw(1), make_raw(2)], *self.resolve_answers())
        monkeypatch.setenv("MARVIS_RESOLVE_MAX_ACTIONS", "2")
        text = run_menu(caplog)
        assert "The filter matches 3 open actions. This run resolves the oldest 2" in text
        assert [body["row_key"] for body in sent_bodies(built)] == ["synthetic-row-key-0001", "synthetic-row-key-0002"]

    def test_a_refused_request_is_an_error_row(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """One refusal does not stop the other requests, and the run reports the failure."""
        built = harness(list(self.RAWS), *self.resolve_answers())
        built.session.put_statuses.extend([400, 200])
        text = run_menu(caplog)
        rows = only_write(built)[0]
        assert [(row["outcome"], row["http_status"]) for row in rows] == [("error", 400), ("resolved", 200)]
        assert rows[0]["message"] == 'HTTP 400 {"detail": "the request was refused"}'
        assert "resolved=1 sent_unverified=0 error=1 not_sent=0 skipped=0" in text
        assert "MistHelper could not resolve 1 of 2 Marvis Actions" in text

    def test_an_accepted_request_without_a_closed_status_is_unverified(
        self, harness: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Mist can accept a request and still report the action as open."""
        built = harness(list(self.RAWS), *self.resolve_answers())
        built.session.apply_puts = False
        text = run_menu(caplog)
        rows = only_write(built)[0]
        assert {(row["outcome"], row["verified_status"], row["message"]) for row in rows} == {
            ("sent_unverified", "open", "Mist still reports an open status.")
        }
        assert "Mist accepted 2 requests, but the verify read shows no closed status for them yet." in text

    def test_a_failed_verify_read_leaves_the_rows_unverified(
        self, harness: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Without a good list read, the run must not claim a closed status."""
        built = harness(list(self.RAWS), *self.resolve_answers())
        built.session.list_statuses.extend([200, 500])
        run_menu(caplog)
        rows = only_write(built)[0]
        assert {(row["outcome"], row["verified_status"]) for row in rows} == {("sent_unverified", "")}
        assert rows[0]["message"] == "Mist accepted the request. The API returned HTTP 500."

    def test_an_action_that_leaves_the_list_is_unverified(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """An action that is missing from the verify read has no known status."""
        built = harness(list(self.RAWS), *self.resolve_answers())
        original_put = built.session.mist_put

        def put_and_remove(uri: str, body: dict[str, Any] | None = None) -> Any:
            """Accept the request, then remove the action from the store."""
            response = original_put(uri, body)
            built.session.rows = [row for row in built.session.rows if row["row_key"] != (body or {}).get("row_key")]
            return response

        built.session.mist_put = put_and_remove
        run_menu(caplog)
        messages = {row["message"] for row in only_write(built)[0]}
        assert messages == {"The new list read shows no status for the action."}

    def test_the_stop_signal_ends_the_run_between_two_requests(
        self, harness: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The actions after the stop signal get a not_sent row and no request."""
        built = harness([make_raw(1), make_raw(2), make_raw(3)], *self.resolve_answers("RESOLVE 3"))
        built.resolver.ConfigUtils.check_stop_signal.side_effect = [False, True]
        text = run_menu(caplog)
        rows = only_write(built)[0]
        assert [row["outcome"] for row in rows] == ["resolved", "not_sent", "not_sent"]
        assert rows[1]["message"] == STOP_SIGNAL_MESSAGE
        assert len(built.session.puts) == 1
        assert "The stop signal ended the run. 2 actions stay open." in text

    def test_an_action_without_a_row_key_is_skipped(self, harness: Any, caplog: pytest.LogCaptureFixture) -> None:
        """The API finds an action by its row_key only."""
        built = harness([make_raw(1, row_key=None), make_raw(2)], *self.resolve_answers())
        run_menu(caplog)
        rows = only_write(built)[0]
        assert [(row["outcome"], row["http_status"]) for row in rows] == [("skipped", None), ("resolved", 200)]
        assert rows[0]["message"] == NO_ROW_KEY_MESSAGE
        assert built.pacer.pace.call_count == 1

    def test_no_verify_read_follows_a_run_that_mist_refused(
        self, harness: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A run without an accepted request saves the verify read."""
        built = harness(list(self.RAWS), *self.resolve_answers())
        built.session.put_statuses.extend([500, None])
        run_menu(caplog)
        assert len(built.session.list_gets()) == 1
        assert [row["outcome"] for row in only_write(built)[0]] == ["error", "error"]

    def test_a_failed_results_write_is_reported_as_a_failure(
        self, harness: Any, caplog: pytest.LogCaptureFixture
    ) -> None:
        """The summary still appears, but the run must not report success."""
        built = harness(list(self.RAWS), *self.resolve_answers())
        built.resolver.DataExporter.write_with_format_selection.return_value = False
        text = run_menu(caplog)
        assert "Marvis Actions resolve summary: resolved=2" in text
        assert "MistHelper could not write OrgMarvisActionsResolveResults.csv" in text
        assert RESOLVE_DONE not in text


class TestCap:
    """The cap comes from MARVIS_RESOLVE_MAX_ACTIONS, with a safe default."""

    @pytest.mark.parametrize(("raw", "expected"), [("", DEFAULT_MAX_ACTIONS), ("25", 25), (" 7 ", 7), ("2.0", 2)])
    def test_a_valid_value_sets_the_cap(self, monkeypatch: pytest.MonkeyPatch, raw: str, expected: int) -> None:
        """A positive whole number is the cap."""
        monkeypatch.setenv("MARVIS_RESOLVE_MAX_ACTIONS", raw)
        assert MarvisResolveWorkflow.max_actions() == expected

    @pytest.mark.parametrize("raw", ["0", "-3", "ten", "2.5"])
    def test_a_value_that_is_not_valid_keeps_the_default(
        self, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, raw: str
    ) -> None:
        """A cap below 1 would block every run, so the default stays and a warning explains why."""
        monkeypatch.setenv("MARVIS_RESOLVE_MAX_ACTIONS", raw)
        with caplog.at_level(logging.WARNING):
            assert MarvisResolveWorkflow.max_actions() == DEFAULT_MAX_ACTIONS
        assert "Ignoring MARVIS_RESOLVE_MAX_ACTIONS" in caplog.text

    def test_a_missing_value_keeps_the_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No value means the documented default."""
        monkeypatch.delenv("MARVIS_RESOLVE_MAX_ACTIONS", raising=False)
        assert MarvisResolveWorkflow.max_actions() == DEFAULT_MAX_ACTIONS
