"""Guard the documents that say the portal hardware action needs the shell unlock (issue #4938).

Why:
    The Multi Site action Collect EX hardware inventory opens one shell on each switch, so the portal
    setting PORTAL_WS_ENABLE_SHELL gates it. The default keeps shells locked. The preview then answers
    HTTP 403 with one sentence that does not name the setting, so an operator finds the setting only in a
    document. These checks hold the operator guide and the web portal wiki page to the variable name, the
    sentence, and the status that the code produces. A change of the code or of a document that makes the
    text wrong fails here, and each check prints what it examined.
"""

from __future__ import annotations

import logging  # Record each read and each decision for the trace.
import re  # Find the next heading and fold the punctuation of an anchor.
from pathlib import Path  # Build the document paths from the repository root.

import pytest  # Expect the refusals of the helpers and of the real validator.

from src.mist.realtime.websocket_streams.catalog.channels import ChannelCatalog  # The channel half of the catalog.
from src.mist.realtime.websocket_streams.catalog.registry.stream_catalog import StreamCatalog  # Names the flag.
from src.mist.realtime.websocket_streams.catalog.utilities.utility_catalog import UtilityCatalog  # The shells.
from src.mist.realtime.websocket_streams.intake.fields.error import StreamRequestError  # The refusal of the code.
from src.mist.realtime.websocket_streams.intake.start_request.validation import RequestValidator  # The real check.

LOGGER = logging.getLogger(__name__)  # Name the logger after this module so each line carries its source.
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]  # The folder that holds documentation/.
OPERATOR_GUIDE = REPOSITORY_ROOT / "documentation" / "operator-guide.md"  # The guide that tells the steps.
WEB_PORTAL_WIKI = REPOSITORY_ROOT / "documentation" / "wiki" / "Web-Portal.md"  # The page with the settings table.
ACTION_HEADING = "### Collect EX chassis hardware as one CSV report or one XML file"  # The guide section of the action.
ACTION_NAME = "EX hardware inventory"  # The words that the wiki row uses for the action.
SHELL_UTILITY_KEY = "ex.createShellSession"  # The shell utility that the hardware preset starts on each switch.


def read_document(path: Path) -> str:
    """Read one document and fail when the guard has no input.

    Args:
        path: The document to read.

    Returns:
        The text of the document.

    Raises:
        FileNotFoundError: When the document is absent.
        ValueError: When the document holds only white space.
    """
    LOGGER.info("Reading the document at %s", path)  # Log before the read.
    if not path.is_file():  # An absent document cannot be checked.
        print(f"The hardware shell lock guard checked 0 documents ({path.name} is absent).")  # Say what was examined.
        raise FileNotFoundError(f"The document is absent: {path}")  # Fail closed.
    text = path.read_text(encoding="utf-8")  # Read the document as UTF-8 text.
    if not text.strip():  # An empty document holds nothing to check.
        print(f"The hardware shell lock guard checked 0 lines of {path.name}.")  # Say what was examined.
        raise ValueError(f"The document is empty: {path}")  # Fail closed.
    LOGGER.debug("Read %d characters from %s", len(text), path.name)  # Log the size, never the text.
    return text  # Hand the text to the check.


def section_after(text: str, heading: str) -> str:
    """Return the text under one heading, up to the next heading of the same or a higher level.

    Args:
        text: The whole document.
        heading: The exact heading line, such as ``### Name``.

    Returns:
        The text of the section, with each run of white space folded to one space.

    Raises:
        ValueError: When the heading is absent or the section holds no text.
    """
    marker = f"\n{heading}\n"  # A heading is a whole line.
    start = f"\n{text}".find(marker)  # The leading newline lets the first line match.
    if start < 0:  # The guard must not pass when the heading moved or changed.
        raise ValueError(f"The heading is absent: {heading}")  # Fail closed.
    rest = f"\n{text}"[start + len(marker) :]  # Everything after the heading line.
    level = len(heading) - len(heading.lstrip("#"))  # The depth of this heading.
    following = re.search(rf"^#{{1,{level}}} ", rest, re.MULTILINE)  # The next heading of the same or a higher level.
    body = " ".join((rest[: following.start()] if following else rest).split())  # Fold the line breaks of Markdown.
    if not body:  # A heading with no text proves nothing.
        raise ValueError(f"The section is empty: {heading}")  # Fail closed.
    return body  # Hand the text to the check.


def absent_from(text: str, needles: tuple[str, ...]) -> tuple[str, ...]:
    """Return each needle that the text does not hold.

    Args:
        text: The text to search.
        needles: The facts that the text must hold.

    Returns:
        The needles that the text lacks, in the order given. An empty tuple means that the text holds every needle.
    """
    return tuple(needle for needle in needles if needle not in text)  # Keep the order for the failure message.


def github_anchor(heading: str) -> str:
    """Return the anchor that GitHub builds from one heading line.

    Args:
        heading: The heading line, such as ``### Name of the section``.

    Returns:
        The lower case words, with punctuation removed and spaces replaced by hyphens.
    """
    words = heading.lstrip("#").strip().lower()  # The rule starts from the lower case title.
    return re.sub(r"[^\w\- ]", "", words).replace(" ", "-")  # Drop punctuation, then join with hyphens.


def locked_refusal() -> StreamRequestError:
    """Return the refusal that the real request validator gives for the shell utility of the hardware action.

    Returns:
        The refusal for a catalog whose shell class is locked.
    """
    catalog = StreamCatalog(ChannelCatalog(), UtilityCatalog(), changes_enabled=False, shell_enabled=False)  # Locked.
    definition = catalog.find("shell", SHELL_UTILITY_KEY)  # The utility that the preset starts on each switch.
    assert definition is not None, f"the catalog holds no shell utility {SHELL_UTILITY_KEY}"  # The premise of the text.
    with pytest.raises(StreamRequestError) as refusal:  # The lock must refuse.
        RequestValidator(catalog).check_lock(definition)  # The same check that the preview route runs.
    return refusal.value  # Hand the code, the message, the status, and the flag to the check.


class TestOperatorGuide:
    """The operator guide section of the action tells the operator how to unlock shells."""

    def test_the_section_names_the_setting_the_sentence_and_the_status_of_the_code(self) -> None:
        """The guide quotes the flag, the message, and the status that the real validator produces."""
        refusal = locked_refusal()  # The facts come from the code, not from this file.
        body = section_after(read_document(OPERATOR_GUIDE), ACTION_HEADING)  # The text of the one section.
        facts = (str(refusal.extra["flag"]), refusal.message, f"HTTP {refusal.status}")  # What the text must say.
        print(f"The hardware shell lock guard checked 1 section of {OPERATOR_GUIDE.name} for {len(facts)} facts.")
        assert absent_from(body, facts) == (), f"the section lacks these facts of the code: {absent_from(body, facts)}"

    def test_the_section_gives_the_two_steps_of_the_fix(self) -> None:
        """The guide tells the operator to set the value and then to recreate the container."""
        body = section_after(read_document(OPERATOR_GUIDE), ACTION_HEADING)  # The text of the one section.
        steps = ("PORTAL_WS_ENABLE_SHELL=true", "podman rm -f misthelper-app", "up -d --no-deps misthelper")
        print(f"The hardware shell lock guard checked 1 section of {OPERATOR_GUIDE.name} for {len(steps)} steps.")
        assert absent_from(body, steps) == (), f"the section lacks these steps: {absent_from(body, steps)}"

    def test_the_section_keeps_the_warning_about_the_free_form_shell(self) -> None:
        """The unlock also opens the free-form shell, so the guide must say who can use it."""
        body = section_after(read_document(OPERATOR_GUIDE), ACTION_HEADING)  # The text of the one section.
        warning = ("Warning:", "Remote shell", "no user login", "PORTAL_ALLOWED_IPS")  # The words of the warning.
        print(f"The hardware shell lock guard checked 1 section of {OPERATOR_GUIDE.name} for {len(warning)} words.")
        assert absent_from(body, warning) == (), f"the warning lacks these words: {absent_from(body, warning)}"

    def test_the_section_says_that_the_cli_needs_no_setting(self) -> None:
        """Menu 309 does not read the portal setting, and the guide must not suggest that it does."""
        body = section_after(read_document(OPERATOR_GUIDE), ACTION_HEADING)  # The text of the one section.
        print(f"The hardware shell lock guard checked 1 section of {OPERATOR_GUIDE.name} for 1 sentence.")
        assert "Menu 309 in the CLI needs no setting" in body  # The CLI path has no lock.


class TestWebPortalWiki:
    """The settings table of the web portal page connects the setting to the action."""

    def test_the_setting_row_names_the_action_and_links_to_the_guide_section(self) -> None:
        """The row for the shell setting names the action and links to a heading that exists."""
        flag = str(locked_refusal().extra["flag"])  # The variable name that the code uses.
        rows = [line for line in read_document(WEB_PORTAL_WIKI).splitlines() if line.startswith(f"| `{flag}` |")]
        print(f"The hardware shell lock guard checked {len(rows)} settings row of {WEB_PORTAL_WIKI.name}.")
        assert len(rows) == 1, f"expected 1 settings row for {flag}, found {len(rows)}"  # One row, no repeats.
        link = f"../operator-guide.md#{github_anchor(ACTION_HEADING)}"  # The anchor that GitHub builds.
        assert (
            absent_from(rows[0], (ACTION_NAME, link)) == ()
        ), f"the row lacks: {absent_from(rows[0], (ACTION_NAME, link))}"


class TestGuardHelpers:
    """The helpers can fail, so a pass of the checks above means something."""

    def test_absent_from_names_each_missing_fact_in_order(self) -> None:
        """A text that lacks a fact gives that fact back, and a text that holds every fact gives nothing."""
        assert absent_from("one two", ("one", "three", "two", "four")) == ("three", "four")  # Order is kept.
        assert absent_from("one two", ("one", "two")) == ()  # Every fact is present.
        assert absent_from("", ("x",)) == ("x",)  # An empty text holds nothing.
        assert absent_from("anything", ()) == ()  # No fact means no failure.

    def test_section_after_stops_at_the_next_heading_of_the_same_level_and_folds_white_space(self) -> None:
        """A deeper heading stays inside the section, and a same-level heading ends it."""
        text = "### A\nline one\nline\ntwo\n#### Deeper\ninside\n### B\nother\n"  # Two sections of one level.
        assert section_after(text, "### A") == "line one line two #### Deeper inside"  # B is not part of A.
        assert section_after(text, "### B") == "other"  # The last section runs to the end.

    def test_section_after_refuses_a_missing_heading_and_an_empty_section(self) -> None:
        """A moved heading and a heading with no text both fail, so the guard cannot pass on nothing."""
        with pytest.raises(ValueError, match="heading is absent"):
            section_after("### A\ntext\n", "### Missing")  # The heading is not in the text.
        with pytest.raises(ValueError, match="section is empty"):
            section_after("### A\n### B\ntext\n", "### A")  # Nothing sits between the two headings.

    def test_read_document_refuses_an_absent_and_an_empty_document(self, tmp_path: Path) -> None:
        """A guard with no input fails, and it prints that it checked nothing."""
        with pytest.raises(FileNotFoundError):
            read_document(tmp_path / "absent.md")  # The file does not exist.
        empty = tmp_path / "empty.md"  # A file with white space only.
        empty.write_text("  \n\n", encoding="utf-8")  # Write it as UTF-8.
        with pytest.raises(ValueError, match="empty"):
            read_document(empty)  # No text means no check.

    def test_github_anchor_follows_the_rule_of_the_link_check(self) -> None:
        """Punctuation drops out, and spaces become hyphens, as in the link of the wiki row."""
        assert (
            github_anchor(ACTION_HEADING) == "collect-ex-chassis-hardware-as-one-csv-report-or-one-xml-file"
        )  # The anchor that the wiki row uses.
        assert github_anchor("## What's new? (v2)") == "whats-new-v2"  # Punctuation is removed.
