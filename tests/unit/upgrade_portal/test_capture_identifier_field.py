"""Proof that the capture page can paint the capture identifier (issue #2093).

Why:
    The capture page shows one field named `Capture identifier`. A capture that
    reached the verified state left that field empty, and the field beside it
    held the true stored size. An operator then read a verified capture with no
    name, so the operator could not open that capture again from the history
    page.

    The cause was the scope of one selector. `capture.html` closes the progress
    section before it opens the result card, so the identifier field is a
    sibling of the progress region and never a child of it. `portal.js` read
    that field with `region.querySelector`. The search started at the progress
    region, found nothing, and `setText` returned without a word of warning.

    The stored size never failed, because that paint reads the document with
    the `byTestId` helper. The repair gives the identifier field the same
    document-wide read, so the two fields of one card now follow one rule.

No browser:
    No harness runs JavaScript in this suite, so these tests read the text of
    the script and the text of the page. `tests/e2e/upgrade_portal/
    test_capture_identifier_paint.py` runs the real script in a real browser
    and proves that the field fills.

    The comment removal writes one line break for each line break it drops, so
    a reported line number stays correct.
"""

from __future__ import annotations

import re
from pathlib import Path

# WHY: This file sits at tests/unit/upgrade_portal, so the root is three levels up.
REPO_ROOT = Path(__file__).resolve().parents[3]

# WHY: The two files that must agree. The page writes the field and the script repaints it.
ASSET_ROOT = REPO_ROOT / "src" / "upgrade_portal" / "app" / "assets"
SCRIPT_PATH = ASSET_ROOT / "static" / "js" / "portal.js"
PAGE_PATH = ASSET_ROOT / "templates" / "capture" / "capture.html"

# WHY: The contract that fixes every capture identifier, at contracts/ui-testids.md.
CONTRACT_PATH = REPO_ROOT / "specs" / "1823-upgrade-capture-portal" / "contracts" / "ui-testids.md"

# WHY: The new test identifier of the field. The stored size beside it already
# carries `capture-size-bytes`, so this name follows that shape.
IDENTIFIER_TESTID = "capture-identifier"

# WHY: The script must name the identifier through one constant, as it already
# does for the percent, the badge, and the stored size.
IDENTIFIER_CONSTANT = "CAPTURE_IDENTIFIER_TESTID"

# WHY: The test identifier of the progress region. The defect lived in a read
# that started at this region and searched no further.
PROGRESS_TESTID = "capture-progress"

# WHY: The selector that failed. Neither paint may hold it again.
BROKEN_SELECTOR = "'[data-capture-field=\"identifier\"]'"

# WHY: The stored size paint already reads the document. It is the model that
# the identifier paint must follow, so a test names it.
SIZE_CONSTANT = "CAPTURE_SIZE_TESTID"

# WHY: The two paints that must fill the field. The first runs after every poll
# and after the manual refresh. The second runs when the start call answers.
POLL_FUNCTION = "paintCaptureStatus"
START_FUNCTION = "startCapture"

# WHY: Each comment syntax the two files use. The scan removes a comment region
# before it reads the text, so a comment that names a selector proves nothing.
COMMENT_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    ".html": (re.compile(r"<!--.*?-->", re.DOTALL), re.compile(r"\{#.*?#\}", re.DOTALL)),
    ".js": (re.compile(r"/\*.*?\*/", re.DOTALL), re.compile(r"//[^\n]*")),
}

# WHY: Every top-level function of portal.js sits one level inside the wrapper,
# so the next line of this form ends the body of the function under test.
NEXT_FUNCTION = "\n    function "


def source(path: Path) -> str:
    """Return the text of one asset file without its comment regions.

    Why:
        A comment names the attribute and the helper that these tests pin. A
        plain text search would read that explanation as proof and would pass
        against a file that lost the real code.

    Args:
        path: The path of the asset file.

    Returns:
        The text with each comment region replaced by its line breaks.
    """
    text = path.read_text(encoding="utf-8")  # WHY: Every asset of the portal is UTF-8.
    for pattern in COMMENT_PATTERNS[path.suffix]:  # WHY: Each file type uses its own comment syntax.
        text = pattern.sub(lambda match: "\n" * match.group(0).count("\n"), text)  # WHY: Keeps the line count.
    return text


def script_function(name: str) -> str:
    """Return the text of one top-level function of portal.js.

    Why:
        A whole-file search proves nothing about which function holds a call. A
        reader needs to know that the poll path and the start path both reach
        the field, so each test below reads one function and never the file.

    Args:
        name: The function name.

    Returns:
        The text from the function line to the next top-level function.
    """
    text = source(SCRIPT_PATH)  # WHY: The comment removal keeps the line count.
    start = text.index(f"function {name}(")  # WHY: A missing function raises, which fails the test.
    end = text.find(NEXT_FUNCTION, start + 1)  # WHY: The next definition ends this body.
    return text[start:end] if end > start else text[start:]  # WHY: The last function runs to the end.


def progress_region() -> str:
    """Return the markup of the capture progress section of the page.

    Why:
        The defect was a scope mistake, so a test must know where the region
        ends. This helper reads the real page and never a copy of it.

    Returns:
        The text from the open tag of the section to its close tag.
    """
    text = source(PAGE_PATH)  # WHY: A comment inside the region must not count as markup.
    start = text.index(f'data-testid="{PROGRESS_TESTID}"')  # WHY: The one progress region of the page.
    end = text.index("</section>", start)  # WHY: The first close tag after the region opens.
    return text[start:end]  # WHY: The caller reads what the region really holds.


def test_the_identifier_field_sits_outside_the_progress_region() -> None:
    """The identifier field is a sibling of the progress region.

    Why:
        This is the shape that broke the paint. A test pins the shape, because
        a later reader could repair the paint by moving the field into the
        region instead. That move would change every test identifier of the
        result card and would break the browser tests of another suite.
    """
    assert IDENTIFIER_TESTID not in progress_region()  # The field is not a child of the region.
    assert f'data-testid="{IDENTIFIER_TESTID}"' in source(PAGE_PATH)  # The page still holds the field.


def test_the_identifier_field_carries_the_test_identifier() -> None:
    """The identifier field carries the test identifier that the script reads.

    Why:
        A document-wide read needs a stable hook. The `data-capture-field`
        attribute is a region hook, and the field sits outside every region, so
        the field needs the same kind of hook that the stored size carries.
    """
    page = source(PAGE_PATH)  # WHY: The rendered field, with no comment text.
    field = re.search(r"<dd[^>]*data-testid=\"" + IDENTIFIER_TESTID + r"\"[^>]*>", page)  # The one field.
    assert field is not None, "capture.html holds no identifier field with a test identifier."
    assert "{{ capture_identifier }}" in page  # The server still renders the value on a direct read.


def test_the_contract_names_the_identifier() -> None:
    """The identifier contract lists the new test identifier.

    Why:
        Rule 4 of contracts/ui-testids.md states that a browser test selects by
        `data-testid` only. An identifier that the contract omits is an
        identifier that a later edit may rename without warning.
    """
    contract = CONTRACT_PATH.read_text(encoding="utf-8")  # WHY: The contract is prose, so it keeps its comments.
    assert f"`{IDENTIFIER_TESTID}`" in contract  # The contract names the field.


def test_the_script_names_the_identifier_through_one_constant() -> None:
    """The script holds the test identifier in one constant.

    Why:
        Every other capture identifier of portal.js sits in a constant near the
        top of the file. A literal in two paints would drift when one paint
        changes and the other does not.
    """
    script = source(SCRIPT_PATH)  # WHY: A comment that names the value proves nothing.
    assert f'var {IDENTIFIER_CONSTANT} = "{IDENTIFIER_TESTID}";' in script  # One constant, one value.


def test_the_poll_paints_the_identifier_with_a_document_read() -> None:
    """The poll paint fills the field through the document-wide helper.

    Why:
        This is the whole repair for the poll path. An operator who reloads the
        page while a capture runs reads the field from this paint alone.
    """
    body = script_function(POLL_FUNCTION)  # WHY: The paint that every poll and every refresh reaches.
    assert f"byTestId({IDENTIFIER_CONSTANT})" in body  # The read starts at the document.
    assert BROKEN_SELECTOR not in body  # The region read that returned null is gone.


def test_the_start_opens_the_page_of_the_new_capture() -> None:
    """The start response opens the page of the returned capture identifier.

    Why:
        A new capture page has no capture identifier. It cannot load completed
        capture rows. The stored capture page carries the returned identifier
        in its path, so it loads those rows after the worker completes.
    """
    body = script_function(START_FUNCTION)  # WHY: The handler runs when the 202 answer arrives.
    assert 'window.location.assign("/captures/" + encodeURIComponent(created.capture_id))' in body


def test_no_paint_of_the_script_reads_the_field_from_a_region() -> None:
    """The broken selector is absent from the whole script.

    Why:
        Two paints held that selector. A repair of one paint alone would leave
        the other paint silent, and the defect would return on the path that
        the repair missed.
    """
    assert BROKEN_SELECTOR not in source(SCRIPT_PATH)  # No paint reads the field from a region.


def test_the_identifier_follows_the_stored_size_rule() -> None:
    """The identifier paint and the stored size paint read the document alike.

    Why:
        The stored size worked while the identifier failed, and the two fields
        sit in one card. One rule for both fields stops a later reader from
        repairing one field and leaving the other.
    """
    size_paint = script_function("loadStoredSize")  # WHY: The paint that always worked.
    assert f"byTestId({SIZE_CONSTANT})" in size_paint  # The model that the repair follows.
    poll_paint = script_function(POLL_FUNCTION)  # WHY: The paint that failed.
    assert f"byTestId({IDENTIFIER_CONSTANT})" in poll_paint  # The repair follows the same model.


def test_the_scan_reads_a_region_selector_that_is_present() -> None:
    """The scan finds a region read that the poll paint really holds.

    Why:
        A scan that found nothing at all would pass the two rules above
        against a file that lost every selector. This probe proves that a pass
        carries meaning. The state field is a true child of the region, so it
        keeps its region read.
    """
    body = script_function(POLL_FUNCTION)  # WHY: The paint under test.
    assert "region.querySelector('[data-capture-field=\"state\"]')" in body  # A real region read remains.
