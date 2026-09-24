"""Tests for the topic filters and the operator prompts of menu 270.

The selector turns a filter answer into a set of topics, and the prompts ask the
mode, the filters, the resolution code, the comment, and the confirmation. These
tests prove the answer grammar, the refusals, and the prompt contract that the
web dashboard and the unattended test pass depend on.
"""

from __future__ import annotations

import logging
import re
from typing import Any
from unittest.mock import patch

import pytest

from src.marvis.actions.model import RESOLUTION_CODES, MarvisActionRecord, MarvisActionRecordBuilder, MarvisCatalog
from src.marvis.actions.selection import (
    COMMENT_MAX_LENGTH,
    MarvisFilterPrompts,
    MarvisResolvePrompts,
    MarvisResolveRequest,
    MarvisTopicSelector,
)
from src.troubleshooting.interactive_test_runner import UnattendedInteractiveInputProvider
from src.utils.input_utils import InputUtils
from tests.unit.marvis.actions.conftest import make_raw

CODES = {code.key: code for code in RESOLUTION_CODES}


def records_of(raws: list[dict[str, Any]]) -> list[MarvisActionRecord]:
    """Return the records of raw rows with the built-in catalog."""
    builder = MarvisActionRecordBuilder(MarvisCatalog([]), {}, "2026-09-23T00:00:00+00:00")
    return [builder.build(raw) for raw in raws]


def sample_records() -> list[MarvisActionRecord]:
    """Return seven actions in three categories and four topics.

    The topics are ap/ap_disconnect (1 open), ap/non_compliant (1 closed),
    gateway/non_compliant (1 open), and switch/sw_offline (2 open, 2 closed).
    """
    return records_of(
        [
            make_raw(1),
            make_raw(2),
            make_raw(3, status="validated"),
            make_raw(4, status="resolved", label="known"),
            make_raw(5, category="ap", symptom="ap_disconnect"),
            make_raw(6, category="ap", symptom="non_compliant", status="validated"),
            make_raw(7, category="gateway", symptom="non_compliant", status="inprogress"),
        ]
    )


def selector(open_only: bool = False) -> MarvisTopicSelector:
    """Return a selector over the sample records."""
    return MarvisTopicSelector(sample_records(), MarvisCatalog([]), open_only)


ALL_TOPICS = frozenset({"ap/ap_disconnect", "ap/non_compliant", "gateway/non_compliant", "switch/sw_offline"})


class TestCounts:
    """The numbered tables count every action and every open action."""

    def test_the_category_table_is_sorted_by_key(self) -> None:
        """A stable order gives stable numbers."""
        assert [row.key for row in selector().category_counts()] == ["ap", "gateway", "switch"]

    def test_the_category_table_adds_up_its_topics(self) -> None:
        """Each category row holds the totals of its topics."""
        rows = {row.key: (row.name, row.total, row.open_count) for row in selector().category_counts()}
        assert rows == {"ap": ("Wireless", 2, 1), "gateway": ("WAN", 1, 1), "switch": ("Wired", 4, 2)}

    def test_the_topic_table_is_sorted_by_key(self) -> None:
        """The subcategory numbers follow the topic keys."""
        assert [row.key for row in selector().topic_counts(ALL_TOPICS)] == sorted(ALL_TOPICS)

    def test_the_topic_table_names_each_topic(self) -> None:
        """The table shows the category name and the subcategory name."""
        rows = selector().topic_counts(frozenset({"switch/sw_offline"}))
        assert [(row.name, row.total, row.open_count) for row in rows] == [("Wired / Switch Offline", 4, 2)]

    def test_the_open_tables_hide_a_topic_without_an_open_action(self) -> None:
        """Modes 2 and 3 show only the topics that hold an open action."""
        topics = [row.key for row in selector(open_only=True).topic_counts(ALL_TOPICS)]
        assert topics == ["ap/ap_disconnect", "gateway/non_compliant", "switch/sw_offline"]

    def test_the_topic_table_shows_only_the_allowed_topics(self) -> None:
        """The subcategory table holds only the topics of the kept categories."""
        rows = selector().topic_counts(frozenset({"ap/ap_disconnect", "not/shown"}))
        assert [row.key for row in rows] == ["ap/ap_disconnect"]


class TestCategoryGrammar:
    """The category answer accepts numbers, keys, and pairs."""

    def test_all_keeps_every_topic(self) -> None:
        """The word all keeps every topic in the table."""
        assert selector().match_categories("all") == (ALL_TOPICS, "")

    def test_an_answer_without_a_token_selects_nothing(self) -> None:
        """Only a Ctrl+C gives an empty answer, and a canceled prompt must stop the run."""
        assert selector().match_categories(" , ") == (frozenset(), "")

    def test_a_number_names_a_table_row(self) -> None:
        """Row 2 of the category table is the gateway category."""
        assert selector().match_categories("2") == (frozenset({"gateway/non_compliant"}), "")

    def test_a_list_joins_the_topics_of_each_token(self) -> None:
        """A comma list adds the topics of each token."""
        topics, bad = selector().match_categories("2, switch")
        assert (topics, bad) == (frozenset({"gateway/non_compliant", "switch/sw_offline"}), "")

    def test_the_answer_ignores_case_and_spaces(self) -> None:
        """An operator can type SWITCH or add stray spaces."""
        assert selector().match_categories("  SWITCH ") == (frozenset({"switch/sw_offline"}), "")

    def test_a_subcategory_key_selects_it_in_every_category(self) -> None:
        """The key non_compliant exists in the ap and the gateway categories."""
        topics, _ = selector().match_categories("non_compliant")
        assert topics == frozenset({"ap/non_compliant", "gateway/non_compliant"})

    def test_a_pair_selects_one_topic(self) -> None:
        """A category/subcategory pair names exactly one topic."""
        assert selector().match_categories("ap/non_compliant") == (frozenset({"ap/non_compliant"}), "")

    def test_a_known_key_without_actions_selects_nothing(self) -> None:
        """The security category is known, but the sample holds no security action."""
        assert selector().match_categories("security") == (frozenset(), "")

    @pytest.mark.parametrize("token", ["0", "4", "99", "1234567", "swich", "switch/typo"])
    def test_an_unknown_token_refuses_the_answer(self, token: str) -> None:
        """A typo must never widen a resolve, so it names the bad token."""
        assert selector().match_categories(f"switch, {token}") == (frozenset(), token)

    def test_all_wins_over_the_other_tokens(self) -> None:
        """The word all anywhere in the list keeps every topic."""
        assert selector().match_categories("2, all") == (ALL_TOPICS, "")


class TestSubcategoryGrammar:
    """The subcategory answer stays inside the categories that the first step kept."""

    def test_a_number_names_a_row_of_the_subcategory_table(self) -> None:
        """Row 1 of the ap subcategory table is ap/ap_disconnect."""
        kept = frozenset({"ap/ap_disconnect", "ap/non_compliant"})
        assert selector().match_topics("1", kept) == (frozenset({"ap/ap_disconnect"}), "")

    def test_a_subcategory_key_stays_inside_the_kept_categories(self) -> None:
        """The gateway topic must not return after the ap category step."""
        kept = frozenset({"ap/ap_disconnect", "ap/non_compliant"})
        assert selector().match_topics("non_compliant", kept) == (frozenset({"ap/non_compliant"}), "")

    def test_a_pair_outside_the_kept_categories_selects_nothing(self) -> None:
        """A known pair outside the first step gives an empty result."""
        kept = frozenset({"ap/ap_disconnect"})
        assert selector().match_topics("switch/sw_offline", kept) == (frozenset(), "")

    def test_a_number_outside_the_subcategory_table_is_refused(self) -> None:
        """The table of one category has one row, so row 2 does not exist."""
        assert selector().match_topics("2", frozenset({"switch/sw_offline"})) == (frozenset(), "2")


class TestSelect:
    """The select step returns the records of the chosen topics."""

    def test_the_export_mode_keeps_every_status(self) -> None:
        """Mode 1 reports the closed actions too."""
        chosen = selector().select(frozenset({"switch/sw_offline"}))
        assert [record.suggestion_id for record in chosen] == ["swoff-1", "swoff-2", "swoff-3", "swoff-4"]

    def test_the_open_modes_keep_the_open_actions_only(self) -> None:
        """Mode 3 must never send a request for a closed action."""
        chosen = selector(open_only=True).select(frozenset({"switch/sw_offline"}))
        assert [record.suggestion_id for record in chosen] == ["swoff-1", "swoff-2"]


class TestFilterPrompts:
    """The filter prompts show the tables and use safe defaults."""

    def test_a_blank_mode_answer_gives_the_read_only_export(self, scripted_input: Any) -> None:
        """The default mode must never change Mist."""
        scripted_input("")
        assert MarvisFilterPrompts.ask_mode() == "1"

    def test_a_closed_stream_gives_the_read_only_export(self, scripted_input: Any) -> None:
        """An SSH disconnect must never start a resolve."""
        scripted_input()
        assert MarvisFilterPrompts.ask_mode() == "1"

    def test_the_mode_table_names_all_three_modes(self, scripted_input: Any, caplog: Any) -> None:
        """The operator reads the modes before the prompt."""
        scripted_input("2")
        with caplog.at_level(logging.INFO):
            MarvisFilterPrompts.ask_mode()
        assert "3. Mark the open Marvis Actions of the chosen topics as resolved" in caplog.text

    def test_a_blank_category_answer_gives_all(self, scripted_input: Any) -> None:
        """The default keeps every topic."""
        scripted_input("")
        assert MarvisFilterPrompts.ask_categories(selector().category_counts()) == "all"

    def test_the_category_table_is_logged_with_numbers(self, scripted_input: Any, caplog: Any) -> None:
        """The web dashboard shows the INFO log, so the table must be there."""
        scripted_input("")
        with caplog.at_level(logging.INFO):
            MarvisFilterPrompts.ask_categories(selector().category_counts())
        assert re.search(r"1\s+ap\s+Wireless\s+2\s+1", caplog.text)

    def test_a_blank_subcategory_answer_gives_all(self, scripted_input: Any) -> None:
        """The default keeps every topic of the kept categories."""
        scripted_input("")
        assert MarvisFilterPrompts.ask_subcategories(selector().topic_counts(ALL_TOPICS)) == "all"


class TestResolutionCode:
    """The resolution code prompt accepts a number, a key, or the alias other."""

    @pytest.mark.parametrize(
        ("answer", "expected"),
        [
            ("1", "suggested"),
            ("suggested", "suggested"),
            ("2", "nonsuggested"),
            ("nonsuggested", "nonsuggested"),
            (" OTHER ", "nonsuggested"),
            ("3", "known"),
            ("Known", "known"),
            ("4", "invalid"),
            ("invalid", "invalid"),
        ],
    )
    def test_each_form_names_its_code(self, answer: str, expected: str) -> None:
        """The number and the key of a code are equal."""
        code = MarvisResolvePrompts.parse_code(answer)
        assert code is not None
        assert code.key == expected

    @pytest.mark.parametrize("answer", ["", "0", "5", "resolved", "1,2"])
    def test_an_unknown_answer_names_no_code(self, answer: str) -> None:
        """A bad code must stop the run."""
        assert MarvisResolvePrompts.parse_code(answer) is None

    def test_a_blank_code_answer_gives_the_suggested_code(self, scripted_input: Any) -> None:
        """The Mist UI preselects the suggested code."""
        scripted_input("")
        code = MarvisResolvePrompts.ask_code()
        assert code is not None
        assert code.key == "suggested"

    def test_a_bad_code_answer_is_refused(self, scripted_input: Any, caplog: Any) -> None:
        """The web dashboard reports the refusal as a failed run."""
        scripted_input("9")
        with caplog.at_level(logging.ERROR):
            assert MarvisResolvePrompts.ask_code() is None
        assert "could not match the resolution code answer '9'" in caplog.text

    def test_the_code_table_is_logged(self, scripted_input: Any, caplog: Any) -> None:
        """The operator reads the codes before the prompt."""
        scripted_input("")
        with caplog.at_level(logging.INFO):
            MarvisResolvePrompts.ask_code()
        assert "2. nonsuggested" in caplog.text


class TestComment:
    """The comment rules follow the Mist UI."""

    def test_the_other_method_code_needs_a_comment(self, scripted_input: Any, caplog: Any) -> None:
        """The Mist UI refuses the code nonsuggested without a comment."""
        scripted_input("")
        with caplog.at_level(logging.WARNING):
            assert MarvisResolvePrompts.ask_comment(CODES["nonsuggested"]) is None
        assert "No value provided for the comment" in caplog.text

    def test_the_other_method_code_accepts_a_comment(self, scripted_input: Any) -> None:
        """The comment reaches the request body trimmed."""
        scripted_input("  Bounced the port on the uplink switch.  ")
        comment = MarvisResolvePrompts.ask_comment(CODES["nonsuggested"])
        assert comment == "Bounced the port on the uplink switch."

    def test_the_other_codes_accept_an_empty_comment(self, scripted_input: Any) -> None:
        """A comment is optional for the suggested, known, and invalid codes."""
        scripted_input("")
        assert MarvisResolvePrompts.ask_comment(CODES["suggested"]) == ""

    def test_the_prompt_states_when_a_comment_is_required(self, scripted_input: Any) -> None:
        """The operator must learn the rule before the answer."""
        scripted = scripted_input("x")
        MarvisResolvePrompts.ask_comment(CODES["nonsuggested"])
        assert "needs a comment" in scripted.prompts[0]

    def test_a_very_long_comment_is_refused(self, caplog: Any) -> None:
        """A pasted log file must not reach Mist."""
        with caplog.at_level(logging.ERROR):
            assert not MarvisResolvePrompts.comment_accepted(CODES["known"], "x" * (COMMENT_MAX_LENGTH + 1))
        assert "could not use the comment" in caplog.text

    def test_a_comment_at_the_limit_is_accepted(self) -> None:
        """The limit itself is valid."""
        assert MarvisResolvePrompts.comment_accepted(CODES["known"], "x" * COMMENT_MAX_LENGTH)


class TestConfirmation:
    """The typed confirmation guards every resolve."""

    @pytest.mark.parametrize("answer", ["RESOLVE 12", "  RESOLVE   12 ", "RESOLVE\t12"])
    def test_the_exact_text_confirms(self, answer: str) -> None:
        """Extra spaces are harmless."""
        assert MarvisResolvePrompts.confirmation_matches(answer, 12)

    @pytest.mark.parametrize("answer", ["", "resolve 12", "RESOLVE 11", "RESOLVE12", "RESOLVE 12 now", "yes"])
    def test_any_other_text_does_not_confirm(self, answer: str) -> None:
        """A wrong count or a wrong word must never change Mist."""
        assert not MarvisResolvePrompts.confirmation_matches(answer, 12)

    def test_a_blank_confirmation_is_a_missing_value(self, scripted_input: Any, caplog: Any) -> None:
        """The web dashboard reports a missing value as a missing input."""
        scripted_input("")
        with caplog.at_level(logging.WARNING):
            assert not MarvisResolvePrompts.ask_confirmation(3)
        assert "No value provided for the confirmation" in caplog.text

    def test_a_closed_stream_never_confirms(self, scripted_input: Any) -> None:
        """An SSH disconnect must never confirm a change."""
        scripted_input()
        assert not MarvisResolvePrompts.ask_confirmation(3)

    def test_a_wrong_confirmation_is_refused(self, scripted_input: Any, caplog: Any) -> None:
        """The refusal repeats the answer and the expected text."""
        scripted_input("RESOLVE 4")
        with caplog.at_level(logging.ERROR):
            assert not MarvisResolvePrompts.ask_confirmation(3)
        assert "could not confirm the resolve. The answer 'RESOLVE 4' does not match 'RESOLVE 3'" in caplog.text

    def test_the_right_confirmation_is_accepted(self, scripted_input: Any, caplog: Any) -> None:
        """The run may send the requests."""
        scripted_input("RESOLVE 3")
        with caplog.at_level(logging.WARNING):
            assert MarvisResolvePrompts.ask_confirmation(3)
        assert caplog.records[0].getMessage().startswith("Caution:")

    def test_the_prompt_names_the_expected_text(self, scripted_input: Any) -> None:
        """The operator must see exactly what to type."""
        scripted = scripted_input("")
        MarvisResolvePrompts.ask_confirmation(7)
        assert "Type RESOLVE 7 to mark these 7 Marvis Actions as resolved" in scripted.prompts[0]


class TestPromptContract:
    """The prompt texts obey the contract of the unattended test pass."""

    def test_no_prompt_holds_a_keyword_of_the_unattended_test_pass(self) -> None:
        """The --testinteractive pass answers 0 or n to these keywords, and neither answer is valid here."""
        asked: list[str] = []

        def record(prompt: str, default_value: str = "", context: str = "unknown") -> str:
            """Record the text that the provider matches, and return the default like the provider does."""
            asked.append(f"{prompt} {context}".lower())
            return default_value

        with patch.object(InputUtils, "safe_input", side_effect=record):
            MarvisFilterPrompts.ask_mode()
            MarvisFilterPrompts.ask_categories(selector().category_counts())
            MarvisFilterPrompts.ask_subcategories(selector().topic_counts(ALL_TOPICS))
            MarvisResolvePrompts.ask_code()
            MarvisResolvePrompts.ask_comment(CODES["nonsuggested"])
            MarvisResolvePrompts.ask_confirmation(1)
        rules = (
            UnattendedInteractiveInputProvider._ALL_KEYWORD_RULES
            + UnattendedInteractiveInputProvider._ANY_KEYWORD_RULES
        )
        keywords = [keyword for words, _ in rules for keyword in words]
        assert len(asked) == 6
        assert [(text, keyword) for text in asked for keyword in keywords if keyword in text] == []


class TestResolveRequest:
    """The request body matches the body that the Mist UI sends."""

    def test_the_body_holds_the_five_fields_of_the_mist_ui(self) -> None:
        """The API finds the action by row_key and stores the code in label."""
        request = MarvisResolveRequest(CODES["nonsuggested"], "Bounced the port.", 1_700_000_000_000)
        assert request.body("rk-1") == {
            "row_key": "rk-1",
            "status": "resolved",
            "label": "nonsuggested",
            "comment": "Bounced the port.",
            "resolve_time": 1_700_000_000_000,
        }

    def test_the_body_never_sends_the_suggestion_id(self) -> None:
        """The research showed that the suggestion_id field is not part of the request."""
        body = MarvisResolveRequest(CODES["known"], "", 1).body("rk-1")
        assert "suggestion_id" not in body
