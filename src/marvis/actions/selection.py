"""Topic filters and operator prompts for menu 270, the Marvis Actions export and bulk resolve.

Why:
    The operator narrows the Marvis Actions in two steps: first by category,
    then by subcategory. The same answers must work in the SSH menu, in the
    local terminal, and in the operations web dashboard. This module holds the
    numbered tables, the answer grammar, and every prompt, so all three paths
    share one set of rules.

Prompt contract:
    The prompts run in this order: mode, category, subcategory, resolution
    code, comment, and confirmation. The web dashboard sends its answers in the
    same order. No prompt text holds a word that makes the unattended
    ``--testinteractive`` pass answer "0", so that pass takes the defaults and
    runs a read-only export.
"""

from __future__ import annotations  # WHY: enable PEP 604 unions in the annotations of this module.

import logging  # WHY: log each table, each prompt, and each refusal.
from collections import Counter, defaultdict  # WHY: count the actions of each topic in one pass.
from collections.abc import Sequence  # WHY: type the record lists without a concrete class.
from dataclasses import dataclass  # WHY: small immutable value objects for counts and requests.
from typing import Any  # WHY: the request body holds values of mixed JSON types.

from src.marvis.actions.model import (  # WHY: the catalogs, the codes, and the record type of this feature.
    CATEGORY_NAMES,
    RESOLUTION_ALIASES,
    RESOLUTION_CODES,
    MarvisActionRecord,
    MarvisCatalog,
    ResolutionCode,
)
from src.utils.input_utils import InputUtils  # WHY: the EOF-safe prompt that every menu uses.

logger = logging.getLogger(__name__)  # WHY: name the logger for this module so a reader filters by source.

MODE_EXPORT_ALL = "1"  # WHY: mode 1 exports every action.
MODE_EXPORT_OPEN = "2"  # WHY: mode 2 exports the open actions only.
MODE_RESOLVE = "3"  # WHY: mode 3 marks the open actions of the chosen topics as resolved.
MODES = (MODE_EXPORT_ALL, MODE_EXPORT_OPEN, MODE_RESOLVE)  # WHY: the only answers that the mode prompt accepts.
ALL_KEYWORD = "all"  # WHY: the answer that keeps every topic. The name avoids a false Bandit B105 match.
COMMENT_MAX_LENGTH = 1000  # WHY: a guard against a pasted log file in the comment field.
MAX_NUMBER_DIGITS = 6  # WHY: a longer number cannot name a table row, and int() refuses very long text.
ANSWER_ECHO_LIMIT = 40  # WHY: a refusal message repeats the start of a bad answer only.
# Issue #886 Phase 2: the container .env sets CONSOLE_LOG_LEVEL=30, so the SSH menu console hides
# every INFO line. The tables, the preview, and the summaries are operator output, so they log at
# WARNING, as the site menu of PromptUtils does. script.log and the web dashboard keep every line.
DISPLAY_LEVEL = logging.WARNING  # WHY: the lowest level that the SSH menu console shows.


@dataclass(frozen=True, slots=True)
class MarvisTopicCount:
    """One row of a numbered filter table.

    Attributes:
        key: The category key, such as ``switch``, or the topic key, such as ``switch/sw_offline``.
        name: The readable name, such as ``Wired`` or ``Wired / Switch Offline``.
        category: The category key of the row.
        total: The number of actions that the row covers.
        open_count: The number of those actions that are open.
    """

    key: str  # WHY: the key that a filter answer accepts.
    name: str  # WHY: the name that the table shows.
    category: str  # WHY: the category key of the row.
    total: int  # WHY: the Actions column of the table.
    open_count: int  # WHY: the Open column of the table.


class MarvisTopicSelector:
    """Count the topics and turn a filter answer into a set of topic keys.

    Why:
        A filter answer can hold table numbers, category keys, subcategory
        keys, and category/subcategory pairs. One class reads all four forms,
        so the category step and the subcategory step follow the same rules.
    """

    def __init__(self, records: Sequence[MarvisActionRecord], catalog: MarvisCatalog, open_only: bool) -> None:
        """Count the topics of the records.

        Args:
            records: Every action of the organization.
            catalog: The catalog that names the known topics.
            open_only: True when the tables and the result must hold open actions only.
        """
        self._records = records  # WHY: the select step filters these records.
        self._open_only = open_only  # WHY: modes 2 and 3 work on open actions only.
        self._topics = self._count_topics(records, open_only)  # WHY: the rows of the subcategory table.
        pairs = catalog.known_pairs() | {(record.category, record.symptom) for record in records}  # WHY: all keys.
        self._known_pairs = frozenset(f"{category}/{symptom}" for category, symptom in pairs)  # WHY: pair tokens.
        pair_categories = frozenset(category for category, _ in pairs)  # WHY: the categories that hold a topic.
        self._known_categories = frozenset(CATEGORY_NAMES) | pair_categories  # WHY: a category without topics.
        self._known_symptoms = frozenset(symptom for _, symptom in pairs)  # WHY: subcategory tokens.

    def category_counts(self) -> list[MarvisTopicCount]:
        """Return one row for each category that the table shows, sorted by key.

        Returns:
            The category rows.
        """
        grouped: defaultdict[str, list[MarvisTopicCount]] = defaultdict(list)  # WHY: collect the topics of each.
        for topic in self._topics.values():  # WHY: a category row adds up its topic rows.
            grouped[topic.category].append(topic)  # WHY: group by the category key.
        return [  # WHY: one row for each category, with the totals of its topics.
            MarvisTopicCount(
                category,
                CATEGORY_NAMES.get(category, category),  # WHY: an unknown category still shows its key.
                category,
                sum(topic.total for topic in topics),
                sum(topic.open_count for topic in topics),
            )
            for category, topics in sorted(grouped.items())  # WHY: a stable order gives stable numbers.
        ]

    def topic_counts(self, allowed: frozenset[str]) -> list[MarvisTopicCount]:
        """Return one row for each allowed topic that the table shows, sorted by key.

        Args:
            allowed: The topic keys that the category step kept.

        Returns:
            The topic rows.
        """
        return [self._topics[key] for key in sorted(allowed) if key in self._topics]  # WHY: stable numbers.

    def match_categories(self, answer: str) -> tuple[frozenset[str], str]:
        """Turn the category answer into topic keys.

        Args:
            answer: The operator answer.

        Returns:
            The topic keys, and the first token that matched nothing. An empty token means success.
        """
        groups = [self._category_topics(row.key) for row in self.category_counts()]  # WHY: a number names a row.
        return self._match(answer, groups, frozenset(self._topics))  # WHY: all shown topics are allowed.

    def match_topics(self, answer: str, allowed: frozenset[str]) -> tuple[frozenset[str], str]:
        """Turn the subcategory answer into topic keys.

        Args:
            answer: The operator answer.
            allowed: The topic keys that the category step kept.

        Returns:
            The topic keys, and the first token that matched nothing. An empty token means success.
        """
        groups = [frozenset({row.key}) for row in self.topic_counts(allowed)]  # WHY: a number names one topic.
        return self._match(answer, groups, allowed)  # WHY: the result stays inside the category step.

    def select(self, topics: frozenset[str]) -> list[MarvisActionRecord]:
        """Return the records of the chosen topics, in the order of the API.

        Args:
            topics: The topic keys to keep.

        Returns:
            The matching records. In the open-only modes, the open records only.
        """
        return [
            record
            for record in self._records
            if record.topic in topics and (record.is_open or not self._open_only)  # WHY: honor the mode.
        ]

    @staticmethod
    def _count_topics(records: Sequence[MarvisActionRecord], open_only: bool) -> dict[str, MarvisTopicCount]:
        """Return one count row for each topic that the table shows, keyed and sorted by topic key."""
        totals = Counter(record.topic for record in records)  # WHY: the Actions column.
        opens = Counter(record.topic for record in records if record.is_open)  # WHY: the Open column.
        shown = sorted(opens if open_only else totals)  # WHY: the open-only modes hide a closed topic.
        first = {record.topic: record for record in reversed(records)}  # WHY: the first record names each topic.
        return {  # WHY: one count row for each shown topic, keyed by the topic key.
            key: MarvisTopicCount(
                key,
                f"{first[key].category_name} / {first[key].symptom_name}",
                first[key].category,
                totals[key],
                opens[key],
            )
            for key in shown
        }

    def _category_topics(self, category: str) -> frozenset[str]:
        """Return the shown topic keys of one category."""
        return frozenset(key for key, topic in self._topics.items() if topic.category == category)  # WHY: one row.

    def _match(self, answer: str, groups: list[frozenset[str]], allowed: frozenset[str]) -> tuple[frozenset[str], str]:
        """Apply the answer grammar to one prompt answer."""
        tokens = self._tokens(answer)  # WHY: split the comma list into clean tokens.
        if not tokens:  # WHY: only a Ctrl+C gives an empty answer, because the prompt default fills a blank one.
            return frozenset(), ""  # WHY: a canceled prompt selects nothing, so the run stops.
        if ALL_KEYWORD in tokens:  # WHY: "all" keeps every allowed topic.
            return allowed, ""  # WHY: no token failed.
        selected: set[str] = set()  # WHY: the union of every token.
        for token in tokens:  # WHY: each token adds its topics.
            keys = self._token_keys(token, groups, allowed)  # WHY: read one token.
            if keys is None:  # WHY: an unknown token must stop the run, because a typo must not widen a resolve.
                return frozenset(), token  # WHY: name the token in the refusal.
            selected.update(keys)  # WHY: add the topics of this token.
        return frozenset(selected), ""  # WHY: every token matched.

    @staticmethod
    def _tokens(answer: str) -> list[str]:
        """Split an answer at each comma, and return the trimmed lowercase tokens."""
        return [token.strip().lower() for token in answer.split(",") if token.strip()]  # WHY: skip empty tokens.

    def _token_keys(self, token: str, groups: list[frozenset[str]], allowed: frozenset[str]) -> frozenset[str] | None:
        """Return the allowed topic keys of one token, or None when the token names nothing known."""
        if token.isdecimal():  # WHY: a number names a table row.
            return self._numbered_group(token, groups)  # WHY: the row holds its topic keys.
        if token in self._known_pairs:  # WHY: a category/subcategory pair names one topic.
            return frozenset({token}) & allowed  # WHY: a known topic without actions selects nothing.
        part = self._key_part(token)  # WHY: the part of the topic key that the token names.
        if part is None:  # WHY: the token names nothing that Mist knows.
            return None  # WHY: the caller refuses the answer.
        return frozenset(key for key in allowed if key.partition("/")[part] == token)  # WHY: the same key part.

    def _key_part(self, token: str) -> int | None:
        """Return the position of a token in a partitioned topic key, or None for an unknown token."""
        if token in self._known_categories:  # WHY: a category key names every topic of the category.
            return 0  # WHY: the category is the first item of the partition result.
        if token in self._known_symptoms:  # WHY: a subcategory key can exist in more than one category.
            return 2  # WHY: the subcategory is the third item of the partition result.
        return None  # WHY: the token is not a known key.

    @staticmethod
    def _numbered_group(token: str, groups: list[frozenset[str]]) -> frozenset[str] | None:
        """Return the topic keys of a numbered table row, or None for a number off the table."""
        number = int(token) if len(token) <= MAX_NUMBER_DIGITS else 0  # WHY: a long number names no row.
        return groups[number - 1] if 1 <= number <= len(groups) else None  # WHY: refuse a number off the table.


class MarvisFilterPrompts:
    """Show the numbered tables and ask the mode and the two filter prompts.

    Why:
        The tables go to the log at ``DISPLAY_LEVEL``, which is WARNING. The
        SSH menu console hides INFO lines, because the container sets
        ``CONSOLE_LOG_LEVEL=30``. The web dashboard and ``script.log`` keep
        every line, so one call reaches every operator.
    """

    @staticmethod
    def ask_mode() -> str:
        """Show the modes and ask for one.

        Returns:
            The trimmed answer. The default is mode 1, the read-only export of every action.
        """
        logger.log(DISPLAY_LEVEL, "Marvis Actions modes:")  # WHY: the heading of the mode table.
        logger.log(DISPLAY_LEVEL, "  1. Export every Marvis Action")  # WHY: mode 1 reads only.
        logger.log(DISPLAY_LEVEL, "  2. Export the open Marvis Actions only")  # WHY: mode 2 reads only.
        logger.log(  # WHY: mode 3 changes Mist.
            DISPLAY_LEVEL, "  3. Mark the open Marvis Actions of the chosen topics as resolved"
        )
        answer = InputUtils.safe_input(  # WHY: the EOF-safe prompt returns the default on a closed stream.
            "Enter the mode number (1, 2, or 3) [1]: ",
            default_value=MODE_EXPORT_ALL,  # WHY: the safe default reads only.
            context="marvis_actions.mode",  # WHY: name the prompt in the input log.
        )
        logger.debug("The mode prompt returned %s", answer)  # WHY: result summary.
        return answer.strip()  # WHY: the caller compares the exact mode text.

    @staticmethod
    def ask_categories(rows: Sequence[MarvisTopicCount]) -> str:
        """Show the category table and ask the category filter.

        Args:
            rows: The category rows.

        Returns:
            The answer. The default is ``all``.
        """
        MarvisFilterPrompts._log_table("Marvis Action categories", rows)  # WHY: show the numbers first.
        # The prompt call stays in this method, so tools/prompt_audit.py counts it as its own prompt.
        answer = InputUtils.safe_input(  # WHY: the EOF-safe prompt returns the default on a closed stream.
            "Enter the categories to include, as numbers or keys separated by commas [all]: ",
            default_value=ALL_KEYWORD,  # WHY: a blank answer keeps every category.
            context="marvis_actions.category",  # WHY: name the prompt in the input log.
        )
        logger.debug("The category prompt returned %s", answer)  # WHY: result summary.
        return answer  # WHY: the selector reads the answer.

    @staticmethod
    def ask_subcategories(rows: Sequence[MarvisTopicCount]) -> str:
        """Show the subcategory table and ask the subcategory filter.

        Args:
            rows: The subcategory rows of the kept categories.

        Returns:
            The answer. The default is ``all``.
        """
        MarvisFilterPrompts._log_table("Marvis Action subcategories", rows)  # WHY: show the numbers first.
        # The prompt call stays in this method, so tools/prompt_audit.py counts it as its own prompt.
        answer = InputUtils.safe_input(  # WHY: the EOF-safe prompt returns the default on a closed stream.
            "Enter the subcategories to include, as numbers, keys, or category/subcategory pairs [all]: ",
            default_value=ALL_KEYWORD,  # WHY: a blank answer keeps every subcategory of the kept categories.
            context="marvis_actions.subcategory",  # WHY: name the prompt in the input log.
        )
        logger.debug("The subcategory prompt returned %s", answer)  # WHY: result summary.
        return answer  # WHY: the selector reads the answer.

    @staticmethod
    def _log_table(title: str, rows: Sequence[MarvisTopicCount]) -> None:
        """Log one numbered table of topic counts."""
        logger.log(DISPLAY_LEVEL, "%s:", title)  # WHY: the heading of the table.
        logger.log(  # WHY: the column headings.
            DISPLAY_LEVEL, "  %-4s %-34s %-48s %7s %5s", "No.", "Key", "Name", "Actions", "Open"
        )
        for number, row in enumerate(rows, start=1):  # WHY: the numbers start at 1, as in every MistHelper menu.
            logger.log(  # WHY: one line for each row.
                DISPLAY_LEVEL, "  %-4d %-34s %-48s %7d %5d", number, row.key, row.name, row.total, row.open_count
            )


@dataclass(frozen=True, slots=True)
class MarvisResolveRequest:
    """The resolution code, the comment, and the time of one bulk resolve.

    Attributes:
        code: The resolution code for every action of the run.
        comment: The comment for every action of the run. It can be empty for most codes.
        resolve_time: The epoch millisecond time of the run, the same on every request.
    """

    code: ResolutionCode  # WHY: one code for every action of the run.
    comment: str  # WHY: one comment for every action of the run.
    resolve_time: int  # WHY: one epoch millisecond time for every action of the run.

    def body(self, row_key: str) -> dict[str, Any]:
        """Return the request body for one action.

        Args:
            row_key: The ``row_key`` of the action.

        Returns:
            The body that the Mist UI sends to resolve one action.
        """
        return {
            "row_key": row_key,  # WHY: the API finds the action by this key.
            "status": "resolved",  # WHY: the status that the Mist UI sets.
            "label": self.code.key,  # WHY: the API stores the resolution code in the label field.
            "comment": self.comment,  # WHY: the operator explanation.
            "resolve_time": self.resolve_time,  # WHY: one time for the whole run.
        }


class MarvisResolvePrompts:
    """Ask the resolution code, the comment, and the typed confirmation.

    Why:
        A bulk resolve changes many Mist records. Each answer is checked
        before the first request, and every refusal states what the operator
        must type instead.
    """

    @staticmethod
    def ask_code() -> ResolutionCode | None:
        """Show the resolution codes and ask for one.

        Returns:
            The code, or None when the answer names no code.
        """
        logger.log(DISPLAY_LEVEL, "Resolution codes:")  # WHY: the heading of the code table.
        for number, listed_code in enumerate(RESOLUTION_CODES, start=1):  # WHY: the numbers match the Mist UI order.
            logger.log(  # WHY: one line for each code.
                DISPLAY_LEVEL, "  %d. %-13s %s", number, listed_code.key, listed_code.name
            )
        answer = InputUtils.safe_input(  # WHY: the EOF-safe prompt.
            "Enter the resolution code number or key [1 suggested]: ",
            default_value=RESOLUTION_CODES[0].key,  # WHY: the Mist UI preselects the suggested code.
            context="marvis_actions.resolution_code",  # WHY: name the prompt in the input log.
        )
        code = MarvisResolvePrompts.parse_code(answer)  # WHY: accept a number, a key, or an alias.
        if code is None:  # WHY: a bad code must stop the run before any request.
            logger.error(  # WHY: the handled refusal that the web dashboard reports as failed.
                "MistHelper could not match the resolution code answer '%s'. Enter 1, 2, 3, 4, a code key, "
                "or other. No action was changed.",
                answer.strip()[:ANSWER_ECHO_LIMIT],
            )
        logger.debug("The resolution code prompt returned %s", code.key if code else None)  # WHY: result summary.
        return code  # WHY: None tells the caller to stop.

    @staticmethod
    def parse_code(answer: str) -> ResolutionCode | None:
        """Return the resolution code that an answer names.

        Args:
            answer: A number from 1 to 4, a code key, or the alias ``other``. Case does not matter.

        Returns:
            The code, or None when the answer names no code.
        """
        token = answer.strip().lower()  # WHY: accept any case and stray spaces.
        token = RESOLUTION_ALIASES.get(token, token)  # WHY: "other" names the nonsuggested code.
        for number, code in enumerate(RESOLUTION_CODES, start=1):  # WHY: try the number and the key of each code.
            if token in (str(number), code.key):  # WHY: both forms name the same code.
                return code  # WHY: the first match wins.
        return None  # WHY: the answer names no code.

    @staticmethod
    def ask_comment(code: ResolutionCode) -> str | None:
        """Ask the comment for the resolve.

        Args:
            code: The chosen resolution code.

        Returns:
            The trimmed comment, or None when the comment is missing or too long for the code.
        """
        hint = "the code nonsuggested needs a comment" if code.needs_comment else "optional"  # WHY: set expectations.
        answer = InputUtils.safe_input(  # WHY: the EOF-safe prompt.
            f"Enter a comment for the resolve ({hint}): ",
            default_value="",  # WHY: most codes need no comment.
            context="marvis_actions.comment",  # WHY: name the prompt in the input log.
        )
        comment = answer.strip()  # WHY: stray spaces carry no meaning.
        logger.debug("The comment prompt returned %d characters", len(comment))  # WHY: result summary.
        if not MarvisResolvePrompts.comment_accepted(code, comment):  # WHY: check the comment before any request.
            return None  # WHY: a refused comment stops the run.
        return comment  # WHY: the request body carries the comment.

    @staticmethod
    def ask_confirmation(count: int) -> bool:
        """Ask the typed confirmation for the resolve.

        Args:
            count: The number of actions that the run changes.

        Returns:
            True only when the answer is ``RESOLVE <count>``.
        """
        expected = f"RESOLVE {count}"  # WHY: the count proves that the operator read the preview.
        logger.warning(  # WHY: the signal word and the consequence come before the prompt.
            "Caution: Mist stores the resolution code and the comment on each of these %d actions. "
            "You can set an action back to Open in the Mist UI.",
            count,
        )
        answer = InputUtils.safe_input(  # WHY: the EOF-safe prompt returns an empty string on a closed stream.
            f"Type {expected} to mark these {count} Marvis Actions as resolved: ",
            default_value="",  # WHY: an empty answer must never confirm a change.
            context="marvis_actions.confirmation",  # WHY: name the prompt in the input log.
        )
        return MarvisResolvePrompts._confirmation_accepted(answer, count)  # WHY: check and log the answer.

    @staticmethod
    def confirmation_matches(answer: str, count: int) -> bool:
        """Return True when an answer is exactly ``RESOLVE <count>``.

        Args:
            answer: The operator answer.
            count: The number of actions that the run changes.

        Returns:
            True when the answer matches after the spaces are collapsed. Case matters.
        """
        return " ".join(answer.split()) == f"RESOLVE {count}"  # WHY: extra spaces are harmless, a wrong count is not.

    @staticmethod
    def comment_accepted(code: ResolutionCode, comment: str) -> bool:
        """Check a comment against the rules of its code, and log a refusal.

        Args:
            code: The chosen resolution code.
            comment: The trimmed comment.

        Returns:
            True when the run may use the comment.
        """
        if code.needs_comment and not comment:  # WHY: the Mist UI requires a comment for this code.
            logger.warning(  # WHY: the portal reports a missing value as a missing input.
                "No value provided for the comment. The code %s needs a comment, so no action was changed.",
                code.key,
            )
            return False  # WHY: never send this code without the explanation.
        if len(comment) > COMMENT_MAX_LENGTH:  # WHY: a very long comment is a paste mistake.
            logger.error(  # WHY: the handled refusal that the web dashboard reports as failed.
                "MistHelper could not use the comment, because it holds %d characters. "
                "The limit is %d. No action was changed.",
                len(comment),
                COMMENT_MAX_LENGTH,
            )
            return False  # WHY: never send a comment that Mist can refuse.
        return True  # WHY: the comment is valid for the code.

    @staticmethod
    def _confirmation_accepted(answer: str, count: int) -> bool:
        """Log the result of the confirmation check and return it."""
        expected = f"RESOLVE {count}"  # WHY: the text that the operator must type.
        if not answer.strip():  # WHY: an empty answer is a missing value, not a typo.
            logger.warning(  # WHY: the portal reports a missing value as a missing input.
                "No value provided for the confirmation, so no action was changed. "
                "To resolve these %d actions, type %s.",
                count,
                expected,
            )
            return False  # WHY: never change Mist without the typed confirmation.
        if not MarvisResolvePrompts.confirmation_matches(answer, count):  # WHY: a wrong text or a wrong count.
            logger.error(  # WHY: the handled refusal that the web dashboard reports as failed.
                "MistHelper could not confirm the resolve. The answer '%s' does not match '%s'. "
                "No action was changed.",
                answer.strip()[:ANSWER_ECHO_LIMIT],
                expected,
            )
            return False  # WHY: never change Mist without the exact confirmation.
        logger.info("The confirmation matches %s", expected)  # WHY: record the accepted confirmation.
        return True  # WHY: the run may send the requests.
