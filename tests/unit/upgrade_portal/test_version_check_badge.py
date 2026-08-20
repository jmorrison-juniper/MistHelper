"""Proof that the version check badge of FR-051 survives every poll.

Why:
    FR-051 asks the run page to compare the version a device reports against
    the version the run asked for. That comparison reaches an operator through
    one badge in the run table, and two files must agree about that badge.

    `upgrade/progress.html` writes the badge at page load. `portal.js` repaints
    it on each poll. Each file holds its own copy of the three words and the
    three classes, because the page renders before the script runs. Two copies
    drift. A badge that changed its wording on the first poll would tell an
    operator that a device changed state when nothing changed.

    One rule matters more than the wording. `paintRunTargets` replaces the whole
    text of every cell that carries `data-run-device` and `data-run-field`. The
    badge is a span inside a cell. A cell that carried those two attributes
    would lose the span on the first poll. The version check would then leave
    the page for the rest of the run. The badge therefore carries
    `data-run-version-check` and carries neither field attribute, and
    `paintRunVersionChecks` reads that hook instead.

    No harness runs JavaScript in this suite, so these tests read the text of
    the two files. The comment removal writes one line break for each line break
    it drops, so a reported line number stays correct.
"""

from __future__ import annotations

import re
from pathlib import Path

from src.upgrade_portal.upgrade import gate

# WHY: This file sits at tests/unit/upgrade_portal, so the root is three levels up.
REPO_ROOT = Path(__file__).resolve().parents[3]

# WHY: The two files that hold the badge. The page writes it and the script repaints it.
ASSET_ROOT = REPO_ROOT / "src" / "upgrade_portal" / "app" / "assets"
SCRIPT_PATH = ASSET_ROOT / "static" / "js" / "portal.js"
PAGE_PATH = ASSET_ROOT / "templates" / "upgrade" / "progress.html"

# WHY: The contract that fixes the three words, at contracts/ui-testids.md line 160.
CONTRACT_PATH = REPO_ROOT / "specs" / "1823-upgrade-capture-portal" / "contracts" / "ui-testids.md"

# WHY: The three words an operator reads. WCAG 1.4.1 refuses color as the only
# signal, so the badge always carries a word and a test reads the word.
BADGE_WORDS = {
    "version_match": "Version matches",
    "version_mismatch": "Version mismatch",
    "version_pending": "Awaiting version",
}

# WHY: The three classes that portal.css already serves to the capture page.
BADGE_CLASSES = {
    "version_match": "badge-verified",
    "version_mismatch": "badge-failed",
    "version_pending": "badge-partial",
}

# WHY: The hook of the badge, and the two attributes that must never join it.
# paintRunTargets needs both of those two before it reaches a cell.
BADGE_HOOK = "data-run-version-check"
FIELD_ATTRS = ("data-run-field", "data-run-device")

# WHY: The test identifier of the cell that holds the badge, from ui-testids.md.
BADGE_CELL_TESTID = "upgrade-device-version-check-"

# WHY: Each comment syntax the two files use. The scan removes a comment region
# before it reads the text, so a comment that names an attribute proves nothing.
COMMENT_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    ".html": (re.compile(r"<!--.*?-->", re.DOTALL), re.compile(r"\{#.*?#\}", re.DOTALL)),
    ".js": (re.compile(r"/\*.*?\*/", re.DOTALL), re.compile(r"//[^\n]*")),
}

# WHY: One HTML open tag. A Jinja expression inside an attribute holds no `>`,
# so the pattern reads the whole tag even when a line break splits it.
OPEN_TAG = re.compile(r"<[a-zA-Z][^>]*>", re.DOTALL)

# WHY: The run page holds nine cells that carry a field attribute today. A floor
# proves that the scan reads the markup, and leaves room for a later cell.
MINIMUM_FIELD_CELLS = 5

# WHY: Every top-level function of portal.js sits one level inside the wrapper,
# so the next line of this form ends the body of the function under test.
NEXT_FUNCTION = "\n    function "


def source(path: Path) -> str:
    """Return the text of one asset file without its comment regions.

    Why:
        A comment names the attributes and the words that these tests pin. A
        plain text search would read that explanation as proof and would pass
        against a file that lost the real markup.

    Args:
        path: The path of the asset file.

    Returns:
        The text with each comment region replaced by its line breaks.
    """
    text = path.read_text(encoding="utf-8")  # WHY: Every asset of the portal is UTF-8.
    for pattern in COMMENT_PATTERNS[path.suffix]:  # WHY: Each file type uses its own comment syntax.
        text = pattern.sub(lambda match: "\n" * match.group(0).count("\n"), text)  # WHY: Keeps the line count.
    return text


def script_map(name: str) -> dict[str, str]:
    """Return one object literal of portal.js as a mapping.

    Args:
        name: The variable name of the object literal.

    Returns:
        Each key of the literal with its string value.
    """
    found = re.search(rf"var {name} = \{{(.*?)\}};", source(SCRIPT_PATH), re.DOTALL)  # WHY: The one definition.
    assert found is not None, f"portal.js holds no map named {name}."  # WHY: A rename must fail loudly.
    return dict(re.findall(r"(\w+):\s*\"([^\"]*)\"", found.group(1)))  # WHY: Each key and its word.


def page_map(name: str) -> dict[str, str]:
    """Return one Jinja map of the run page as a mapping.

    Args:
        name: The name the page sets the map under.

    Returns:
        Each key of the map with its string value.
    """
    found = re.search(rf"set {name} = \{{(.*?)\}}", source(PAGE_PATH), re.DOTALL)  # WHY: The one definition.
    assert found is not None, f"progress.html holds no map named {name}."  # WHY: A rename must fail loudly.
    return dict(re.findall(r"'(\w+)':\s*'([^']*)'", found.group(1)))  # WHY: Jinja writes single quotes.


def tags_with(attribute: str) -> list[str]:
    """Return every open tag of the run page that carries one attribute.

    Args:
        attribute: The attribute name, or any text inside the open tag.

    Returns:
        Each matching open tag, in the order the page writes them.
    """
    return [tag for tag in OPEN_TAG.findall(source(PAGE_PATH)) if attribute in tag]  # WHY: Comments are gone.


def script_function(name: str) -> str:
    """Return the text of one top-level function of portal.js.

    Why:
        A whole-file search proves nothing about which function holds a call. A
        reader needs to know that the poll path reaches the painter, so each
        test below reads one function and never the file.

    Args:
        name: The function name.

    Returns:
        The text from the function line to the next top-level function.
    """
    text = source(SCRIPT_PATH)  # WHY: The comment removal keeps the line count.
    start = text.index(f"function {name}(")  # WHY: A missing function raises, which fails the test.
    end = text.find(NEXT_FUNCTION, start + 1)  # WHY: The next definition ends this body.
    return text[start:end] if end > start else text[start:]  # WHY: The last function runs to the end.


def test_the_three_words_agree_between_the_page_and_the_script() -> None:
    """The page and the script hold the same three words for the badge.

    Why:
        The page renders the word, and the first poll replaces it. Two files
        that held different words would change the badge 30 seconds after the
        page opened, with no change on any device.
    """
    assert page_map("version_check_text") == BADGE_WORDS  # The page writes these words at load.
    assert script_map("RUN_VERSION_CHECK_WORDS") == BADGE_WORDS  # The poll writes the same words.


def test_the_three_classes_agree_between_the_page_and_the_script() -> None:
    """The page and the script hold the same three classes for the badge."""
    assert page_map("version_check_class") == BADGE_CLASSES  # The page picks the class at load.
    assert script_map("RUN_VERSION_CHECK_CLASSES") == BADGE_CLASSES  # The poll picks the same class.


def test_the_three_tokens_match_the_gate_module() -> None:
    """The page, the script, and the gate name the three states alike.

    Why:
        The gate writes one of these tokens onto a target row, and the row
        reaches the browser. A token the page does not know would read as a
        pending check for ever, and no operator would learn about a mismatch.
    """
    tokens = {gate.OUTCOME_VERSION_MATCH, gate.OUTCOME_VERSION_MISMATCH, gate.OUTCOME_VERSION_PENDING}
    assert set(BADGE_WORDS) == tokens  # The words answer every token the gate writes.
    assert set(page_map("version_check_class")) == tokens  # The page maps every token.
    assert set(script_map("RUN_VERSION_CHECK_CLASSES")) == tokens  # The script maps every token.


def test_the_contract_holds_the_three_words() -> None:
    """The contract file names each word the badge shows.

    Why:
        contracts/ui-testids.md fixes the words, because an end-to-end test
        reads the word and never the class. A reworded badge would break that
        test in another suite, which this suite never runs.
    """
    contract = CONTRACT_PATH.read_text(encoding="utf-8")  # WHY: The contract is prose, so it keeps its comments.
    for word in BADGE_WORDS.values():  # WHY: Each of the three words in turn.
        assert word in contract, f"contracts/ui-testids.md names no badge word {word}."


def test_the_badge_carries_the_script_hook() -> None:
    """The badge carries the hook with the MAC address of its device."""
    assert f'{BADGE_HOOK}="{{{{ mac }}}}"' in source(PAGE_PATH)  # The hook holds the address of one device.
    assert tags_with(BADGE_HOOK), "progress.html holds no badge for the version check."


def test_the_badge_carries_no_field_attribute() -> None:
    """The badge carries neither attribute that the field paint reads.

    Why:
        This is the defect that would hide the whole check. The field paint
        replaces the text of every cell it reaches, and the badge is a span
        inside a cell. A badge with a field attribute would leave the page on
        the first poll, and it would never return.
    """
    for tag in tags_with(BADGE_HOOK):  # WHY: Every badge on the page, and not the first alone.
        for attribute in FIELD_ATTRS:  # WHY: The field paint needs both of these.
            assert attribute not in tag, f"The version check badge carries {attribute}."


def test_the_badge_cell_carries_no_field_attribute() -> None:
    """The cell around the badge carries neither field attribute either.

    Why:
        The field paint reaches a cell, never a span. A cell that carried the
        two attributes would replace its own text. The paint would drop the
        badge with that text, and the column would read as empty.
    """
    cells = tags_with(BADGE_CELL_TESTID)  # WHY: The cell carries the test identifier of the contract.
    assert cells, "progress.html holds no cell for the version check."
    for tag in cells:  # WHY: One cell for each device row.
        for attribute in FIELD_ATTRS:  # WHY: The same two attributes as the badge test.
            assert attribute not in tag, f"The version check cell carries {attribute}."


def test_the_scan_finds_a_field_attribute_that_is_present() -> None:
    """The scan reads a field attribute on the cells that really carry one.

    Why:
        A scan that found no attribute at all would pass the two rules above
        against a page that lost every attribute. This probe proves that a pass
        carries meaning.
    """
    carriers = tags_with(FIELD_ATTRS[0])  # WHY: The device cells of the run table carry this one.
    assert len(carriers) >= MINIMUM_FIELD_CELLS  # The page really holds field cells.
    assert not [tag for tag in carriers if BADGE_HOOK in tag]  # And no field cell is the badge.


def test_the_poll_paints_the_badge() -> None:
    """The run paint calls the badge painter, so each poll repaints the badge.

    Why:
        The painter can exist and still never run. The manual refresh and the
        30-second poll both reach `paintRunStatus`, so the call must sit there.
    """
    body = script_function("paintRunStatus")  # WHY: The one function both paths reach.
    assert "paintRunVersionChecks(region, status);" in body  # The poll repaints the badge.


def test_the_painter_reads_the_badge_hook_alone() -> None:
    """The badge painter selects on the hook and on no field attribute.

    Why:
        `paintVerified` selects the capture badge by its test identifier and
        writes a class and a word. This painter follows that shape with its own
        attribute, so the run page keeps one pattern and not two.
    """
    body = script_function("paintRunVersionChecks")  # WHY: The painter of FR-051.
    assert f'[{BADGE_HOOK}="' in body  # The painter selects the badge by its own hook.
    assert "data-run-field" not in body  # The painter never reaches a field cell.


def test_the_field_painter_needs_both_attributes() -> None:
    """The field paint reaches a cell only through both field attributes.

    Why:
        The badge is safe because it carries neither attribute. That safety
        holds only while the field paint keeps needing both, so this test reads
        the other side of the same rule.
    """
    body = script_function("paintRunTargets")  # WHY: The paint that would drop the badge.
    assert '[data-run-device="' in body  # The field paint needs the device attribute.
    assert '[data-run-field="' in body  # The field paint needs the field attribute.
    assert gate.FIELD_VERSION_OUTCOME not in script_map("RUN_DEVICE_FIELDS")  # The badge is no field cell.


def test_an_unknown_token_reads_as_a_pending_check() -> None:
    """Both files fall back to the pending word, and never to a match.

    Why:
        A token that neither map knows must never read as a match. A wrong
        match would tell an operator that a device carries firmware it does not
        carry. The operator would then leave that device on its old version.
    """
    pending_class = BADGE_CLASSES["version_pending"]  # WHY: The neutral class of the three.
    pending_word = BADGE_WORDS["version_pending"]  # WHY: The neutral word of the three.
    page = source(PAGE_PATH)  # WHY: The page picks a default inside each `get` call.
    assert f"'{pending_class}'" in page  # The page falls back to the neutral class.
    assert f"'{pending_word}'" in page  # The page falls back to the neutral word.
    painter = script_function("paintRunVersionChecks")  # WHY: The painter picks its own default.
    assert f'"{pending_class}"' in painter  # The painter falls back to the neutral class.
    assert "RUN_VERSION_CHECK_WORDS.version_pending" in painter  # The painter falls back to the neutral word.
