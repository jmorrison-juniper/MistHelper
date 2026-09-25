"""Prove that the operations portal controls of menu 270 answer the right prompts.

Why:
    The browser sends one answer for each control, in control order. The input
    hook then hands the answers to ``input`` one at a time. A control out of
    order would answer the wrong prompt. For example, a category key would reach
    the mode prompt. A choice value that the answer grammar cannot read would
    make every portal run fail.

    These tests read the registry row, check each choice value against the real
    answer grammar, and run the real prompts through the real input hook. The
    portal status rules then classify each run, so a refused resolve can never
    appear as a completed run.

Privacy:
    Every identifier comes from the synthetic row factory in ``conftest``.
"""

from __future__ import annotations

import builtins
import logging
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Any
from unittest.mock import MagicMock

import pytest

from src.marvis.actions.model import (
    CATEGORY_NAMES,
    RESOLUTION_CODES,
    TOPIC_NAMES,
    MarvisActionRecordBuilder,
    MarvisCatalog,
)
from src.marvis.actions.operation import MarvisActionsOperation
from src.marvis.actions.selection import MODE_EXPORT_ALL, MODES, MarvisResolvePrompts, MarvisTopicSelector
from src.utils.menu_entry import MenuEntry
from tests.unit.marvis.actions.conftest import FakeResponse, OperationHarness, make_alarm, make_alarm_page, make_raw
from web_portal.services.input_hook import InputInterceptor, web_input_context
from web_portal.services.operation import PARAMETER_REGISTRY, OperationExecutor, _RunLogHandler

MENU = "270"  # The menu number of the feature.
CONTROL_NAMES = [  # The six controls, in the order of the six prompts. FR-032.
    "marvis_mode",
    "marvis_category",
    "marvis_subcategory",
    "marvis_resolution_code",
    "marvis_comment",
    "marvis_confirmation",
]
DEFAULT_ANSWERS = ("1", "all", "all", "suggested", "", "")  # The browser answers when the operator changes nothing.
EXPORT_FILE = "OrgMarvisActions.csv"  # The report of modes 1, 2, and 4.
RESULTS_FILE = "OrgMarvisActionsResolveResults.csv"  # The results file of mode 3.


def control(name: str) -> dict[str, Any]:
    """Return one control of the menu 270 row."""
    return next(param for param in PARAMETER_REGISTRY[MENU]["parameters"] if param["name"] == name)


def option_values(name: str) -> list[str]:
    """Return the values of one choice control, in the order the page shows them."""
    return [option["value"] for option in control(name)["options"]]


def every_topic_selector() -> MarvisTopicSelector:
    """Return a selector over one open action in each of the 36 known topics."""
    raws = [  # One open action for each topic, so every table row exists.
        make_raw(number, category=category, symptom=symptom)
        for number, (category, symptom) in enumerate(sorted(TOPIC_NAMES), start=1)
    ]
    builder = MarvisActionRecordBuilder(MarvisCatalog([]), {}, "2026-09-23T00:00:00+00:00")
    return MarvisTopicSelector([builder.build(raw) for raw in raws], MarvisCatalog([]), MODE_EXPORT_ALL)


def portal_rows() -> list[dict[str, Any]]:
    """Return four actions: two open switch actions, one closed AP action, and one open DHCP action."""
    return [
        make_raw(1),
        make_raw(2),
        make_raw(3, category="ap", symptom="ap_disconnect", status="validated"),
        make_raw(4, category="connectivity", symptom="dhcp_failure", status="inprogress"),
    ]


def _input_outside_the_queue(prompt: str = "") -> str:
    """Fail the test when the run reads a keyboard that the portal does not have."""
    raise AssertionError(f"The run read input outside the portal queue: {prompt!r}")


@dataclass
class PortalRun:
    """The fakes and the portal run record of one run."""

    fakes: OperationHarness
    record: dict[str, Any]
    executor: OperationExecutor

    def missing_input(self) -> str | None:
        """Return the line that the portal reports as a missing answer."""
        return self.executor._missing_input_reason(self.record)

    def handled_error(self) -> str | None:
        """Return the line that the portal reports as a failure."""
        return self.executor._handled_error_reason(self.record)

    def puts(self) -> list[dict[str, Any]]:
        """Return the body of each resolve request."""
        return [body for _, body in self.fakes.session.puts]

    def exported_rows(self) -> list[dict[str, Any]]:
        """Return the rows of the one report write."""
        calls = [call for call in self.fakes.exports() if call.args[1] == EXPORT_FILE]
        assert len(calls) == 1, calls
        return list(calls[0].args[0])


class PortalRunner:
    """Run menu 270 the way the portal runs it, with the real input hook."""

    def __init__(self, harness: Any, monkeypatch: pytest.MonkeyPatch, executor: OperationExecutor) -> None:
        """Keep the fake builder, the patch tool, and the executor."""
        self._harness = harness
        self._monkeypatch = monkeypatch
        self._executor = executor

    def run(self, rows: list[dict[str, Any]], answers: Sequence[str]) -> PortalRun:
        """Send the answers through the portal queue, and capture the log the way the portal does."""
        fakes = self._harness(rows)  # This installs a scripted input with no answers.
        self._monkeypatch.setattr(builtins, "input", InputInterceptor._patched_input)  # The portal hook.
        self._monkeypatch.setattr(InputInterceptor, "_original_input", staticmethod(_input_outside_the_queue))
        record = self._executor._build_run_record(MENU)
        handler = _RunLogHandler(record, None)
        root = logging.getLogger()
        root.addHandler(handler)
        try:
            with web_input_context(list(answers)):
                MarvisActionsOperation.run()
        finally:
            root.removeHandler(handler)
        return PortalRun(fakes, record, self._executor)


@pytest.fixture
def portal(harness: Any, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> Iterator[PortalRunner]:
    """Return a runner whose executor holds the real menu 270 row."""
    caplog.set_level(logging.DEBUG)  # The portal handler must see the INFO lines.
    entry = MenuEntry(
        menu_id=MENU,
        handler=MarvisActionsOperation.run,
        title="Export or resolve Marvis Actions by category and subcategory",
        category="interactive_safe",
        destructive=False,
        supports_fast=False,
    )
    executor = OperationExecutor({MENU: entry}, None, None, None)
    yield PortalRunner(harness, monkeypatch, executor)
    executor.shutdown(0)


class TestTheRegistryRow:
    """The row must match the six prompts of the operation."""

    def test_the_row_holds_six_controls_in_prompt_order(self) -> None:
        """FR-032. The answer order is the control order."""
        names = [param["name"] for param in PARAMETER_REGISTRY[MENU]["parameters"]]
        print(f"The menu 270 portal guard checked {len(names)} controls.")
        assert names == CONTROL_NAMES

    def test_the_page_renders_the_controls_before_run(self) -> None:
        """The interactive form shows the controls before the operator presses Run."""
        assert PARAMETER_REGISTRY[MENU]["category"] == "interactive"

    def test_the_mode_control_defaults_to_the_report(self) -> None:
        """A run that changes nothing is the safe default."""
        assert control("marvis_mode")["default"] == "1"

    def test_the_filter_controls_default_to_all(self) -> None:
        """A blank CLI answer means all, and the portal default matches it."""
        assert (control("marvis_category")["default"], control("marvis_subcategory")["default"]) == ("all", "all")

    def test_the_code_control_defaults_to_the_suggested_code(self) -> None:
        """The Mist UI preselects the suggested code."""
        assert control("marvis_resolution_code")["default"] == "suggested"

    def test_only_the_first_three_controls_are_required(self) -> None:
        """A report run must start without a code, a comment, or a confirmation."""
        required = [bool(param["required"]) for param in PARAMETER_REGISTRY[MENU]["parameters"]]
        assert required == [True, True, True, False, False, False]

    def test_the_default_answers_match_the_control_defaults(self) -> None:
        """The contract runs below use the answers that the page sends by default."""
        defaults = tuple(str(param.get("default", "")) for param in PARAMETER_REGISTRY[MENU]["parameters"])
        assert defaults == DEFAULT_ANSWERS


class TestTheChoicesMatchTheGrammar:
    """Each choice value must be an answer that the prompt accepts."""

    def test_the_mode_values_are_the_four_modes(self) -> None:
        """A mode value outside MODES makes the run stop."""
        assert option_values("marvis_mode") == sorted(MODES)

    def test_the_closed_report_label_names_the_closed_actions(self) -> None:
        """Issue #3342: the operator must see that mode 4 exports the closed actions."""
        labels = {option["value"]: option["label"] for option in control("marvis_mode")["options"]}
        assert labels["4"] == "4 - Export the closed Marvis Actions (report only)"

    def test_only_the_resolve_mode_label_warns_about_a_change(self) -> None:
        """The three report modes read only, and the label of each one says so."""
        labels = {option["value"]: option["label"] for option in control("marvis_mode")["options"]}
        assert [value for value, label in labels.items() if label.endswith("(report only)")] == ["1", "2", "4"]
        assert labels["3"].endswith("(changes Mist)")

    def test_every_category_value_is_accepted(self) -> None:
        """A category value must never read as an unknown token. FR-010."""
        choice = every_topic_selector()
        values = option_values("marvis_category")
        refused = [value for value in values if choice.match_categories(value)[1]]
        assert len(values) == len(CATEGORY_NAMES) + 1
        assert refused == []

    def test_every_category_value_selects_its_category(self) -> None:
        """A category value selects every topic of that category. The category security holds no known topic."""
        choice = every_topic_selector()
        for key in CATEGORY_NAMES:
            expected = frozenset(f"{category}/{symptom}" for category, symptom in TOPIC_NAMES if category == key)
            assert choice.match_categories(key) == (expected, "")

    def test_every_subcategory_value_names_one_topic(self) -> None:
        """A pair value must select exactly its topic, even for a key that two categories share."""
        choice = every_topic_selector()
        allowed, _ = choice.match_categories("all")
        values = option_values("marvis_subcategory")
        assert len(values) == len(TOPIC_NAMES) + 1
        assert values[0] == "all"
        for value in values[1:]:
            assert choice.match_topics(value, allowed) == (frozenset({value}), "")

    def test_the_all_values_select_everything(self) -> None:
        """The first option of each filter selects every topic."""
        choice = every_topic_selector()
        categories, _ = choice.match_categories("all")
        topics, _ = choice.match_topics("all", categories)
        assert len(topics) == len(TOPIC_NAMES)

    def test_every_code_value_parses_to_its_code(self) -> None:
        """The code values are the four Mist label values, in the order of the Mist UI."""
        values = option_values("marvis_resolution_code")
        assert values == [code.key for code in RESOLUTION_CODES]
        for value in values:
            parsed = MarvisResolvePrompts.parse_code(value)
            assert parsed is not None and parsed.key == value


class TestPortalRuns:
    """The real prompts read the portal answers, and the portal classifies each run."""

    def test_the_default_answers_export_every_action(self, portal: PortalRunner) -> None:
        """Mode 1 reads three answers, and the three unused answers change nothing."""
        run = portal.run(portal_rows(), DEFAULT_ANSWERS)
        assert [row["suggestion_id"] for row in run.exported_rows()] == ["swoff-1", "swoff-2", "swoff-3", "swoff-4"]
        assert run.puts() == []
        assert (run.missing_input(), run.handled_error()) == (None, None)
        assert EXPORT_FILE in run.record["output_files"]

    def test_a_topic_choice_exports_the_open_actions_of_that_topic(self, portal: PortalRunner) -> None:
        """Mode 2 with one category and one pair keeps the open actions of that topic only."""
        run = portal.run(portal_rows(), ("2", "switch", "switch/sw_offline", "suggested", "", ""))
        assert [row["suggestion_id"] for row in run.exported_rows()] == ["swoff-1", "swoff-2"]
        assert run.puts() == []
        assert (run.missing_input(), run.handled_error()) == (None, None)

    def test_a_category_without_open_actions_completes_with_a_reason(self, portal: PortalRunner) -> None:
        """The only AP action is closed, so mode 2 finds nothing and says so."""
        run = portal.run(portal_rows(), ("2", "ap", "all", "suggested", "", ""))
        assert run.fakes.exports() == []
        assert (run.missing_input(), run.handled_error()) == (None, None)
        message = run.executor._completion_message(run.record)
        assert message == (
            "Operation completed with no output file: No open Marvis Actions match the filter. No file was written."
        )

    def test_the_closed_report_exports_the_closed_actions(self, portal: PortalRunner) -> None:
        """Issue #3342: mode 4 reads three answers, and it exports the one closed AP action."""
        run = portal.run(portal_rows(), ("4", "all", "all", "suggested", "", ""))
        assert [row["suggestion_id"] for row in run.exported_rows()] == ["swoff-3"]
        assert run.puts() == []
        assert (run.missing_input(), run.handled_error()) == (None, None)
        assert EXPORT_FILE in run.record["output_files"]

    def test_a_category_without_closed_actions_completes_with_a_reason(self, portal: PortalRunner) -> None:
        """The switch actions are open, so mode 4 finds nothing and says so."""
        run = portal.run(portal_rows(), ("4", "switch", "all", "suggested", "", ""))
        assert run.fakes.exports() == []
        assert (run.missing_input(), run.handled_error()) == (None, None)
        message = run.executor._completion_message(run.record)
        assert message == (
            "Operation completed with no output file: No closed Marvis Actions match the filter. No file was written."
        )

    def test_a_blank_confirmation_shows_the_count_and_sends_nothing(self, portal: PortalRunner) -> None:
        """FR-033. The preview and the count reach the log, and the portal reports a missing answer."""
        run = portal.run(portal_rows(), ("3", "all", "all", "suggested", "", ""))
        assert run.puts() == []
        assert run.missing_input() == (
            "No value provided for the confirmation, so no action was changed. "
            "To resolve these 3 actions, type RESOLVE 3."
        )
        preview = [entry["message"] for entry in run.record["log_messages"] if entry["message"].startswith("  ")]
        assert len([line for line in preview if "| started " in line]) == 3

    def test_a_stale_count_fails_and_sends_nothing(self, portal: PortalRunner) -> None:
        """A count from an older report must not confirm the current targets."""
        run = portal.run(portal_rows(), ("3", "switch", "switch/sw_offline", "known", "", "RESOLVE 3"))
        assert run.puts() == []
        assert run.handled_error() == (
            "MistHelper could not confirm the resolve. The answer 'RESOLVE 3' does not match 'RESOLVE 2'. "
            "No action was changed."
        )

    def test_the_other_code_without_a_comment_sends_nothing(self, portal: PortalRunner) -> None:
        """FR-021. The code nonsuggested needs a comment, and the portal reports the missing answer."""
        run = portal.run(portal_rows(), ("3", "all", "all", "nonsuggested", "", "RESOLVE 3"))
        assert run.puts() == []
        assert run.missing_input() == (
            "No value provided for the comment. The code nonsuggested needs a comment, so no action was changed."
        )

    def test_the_typed_count_resolves_with_the_code_and_the_comment(self, portal: PortalRunner) -> None:
        """The six answers resolve the two open switch actions with the other code and its comment."""
        answers = ("3", "switch", "switch/sw_offline", "nonsuggested", "Bounced the uplink port", "RESOLVE 2")
        run = portal.run(portal_rows(), answers)
        bodies = run.puts()
        assert [body["row_key"] for body in bodies] == ["synthetic-row-key-0001", "synthetic-row-key-0002"]
        assert {(body["status"], body["label"], body["comment"]) for body in bodies} == {
            ("resolved", "nonsuggested", "Bounced the uplink port")
        }
        assert all("suggestion_id" not in body for body in bodies)
        assert (run.missing_input(), run.handled_error()) == (None, None)
        assert RESULTS_FILE in run.record["output_files"]

    def test_a_missing_answer_list_reads_the_prompt_defaults(self, portal: PortalRunner) -> None:
        """An empty queue acts as a closed stream, so each prompt takes its safe default."""
        run = portal.run(portal_rows(), ("1",))
        assert len(run.exported_rows()) == 4
        assert run.puts() == []

    def test_a_joined_report_completes_with_the_alarm_values(self, portal: PortalRunner, site_api: MagicMock) -> None:
        """Issue #3339: the two alarm count lines hold no failure word, so the portal reports a completed run."""
        site_api.api.v1.orgs.alarms.searchOrgAlarms.return_value = make_alarm_page([make_alarm(1), make_alarm(9)])
        run = portal.run(portal_rows(), DEFAULT_ANSWERS)
        assert [row["alarm_id"] for row in run.exported_rows()] == [make_alarm(1)["id"], "", "", ""]
        assert (run.missing_input(), run.handled_error()) == (None, None)
        messages = [entry["message"] for entry in run.record["log_messages"]]
        assert "Marvis alarm join: 1 of 4 exported actions have a Marvis alarm. 3 have no alarm." in messages
        assert "Marvis alarms in the search window without an action in the list: 1" in messages
        assert EXPORT_FILE in run.record["output_files"]

    def test_a_refused_alarm_search_still_completes(self, portal: PortalRunner, site_api: MagicMock) -> None:
        """Issue #3339: the report is the result, so a refused alarm search must not turn the run into a failure."""
        site_api.api.v1.orgs.alarms.searchOrgAlarms.return_value = FakeResponse(403, {"detail": "refused"})
        run = portal.run(portal_rows(), DEFAULT_ANSWERS)
        assert {row["alarm_id"] for row in run.exported_rows()} == {""}
        assert (run.missing_input(), run.handled_error()) == (None, None)
        assert EXPORT_FILE in run.record["output_files"]
