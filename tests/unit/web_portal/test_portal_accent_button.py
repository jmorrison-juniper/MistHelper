"""Guard the accent button fill in the hover state and in the disabled state.

Issue #3658: ``.btn-accent`` in ``web_portal/static/css/portal.css`` set plain
``background-color``, ``border-color``, and ``color`` declarations. Bootstrap
5.3.3 paints ``.btn:hover``, ``.btn:active``, and ``.btn:disabled`` from its
``--bs-btn-*`` custom properties, and those properties win over a plain
declaration. The accent button therefore lost its fill when the operator
pointed at it and when the page disabled it.

One page carried a scoped copy of the repair in
``src/mist/realtime/websocket_streams/web/static/websockets.css``. The shared
rule now holds every state variable, so the scoped copy must stay removed. A
returned copy means the repair drifted back into one page.

These tests read the two stylesheets and report the number of declarations and
rules that they examined.
"""

import re
from pathlib import Path

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]  # The guard reads product files, not fixtures.

PORTAL_STYLESHEET = REPOSITORY_ROOT / "web_portal" / "static" / "css" / "portal.css"
WEBSOCKET_STYLESHEET = (
    REPOSITORY_ROOT / "src" / "mist" / "realtime" / "websocket_streams" / "web" / "static" / "websockets.css"
)

# Bootstrap reads one variable for each button state. A state that names no
# variable falls back to the Bootstrap default, which is gray.
REQUIRED_FILL_VARIABLES = (
    "--bs-btn-bg",
    "--bs-btn-hover-bg",
    "--bs-btn-active-bg",
    "--bs-btn-disabled-bg",
)

# Each fill variable carries a border variable, so the outline keeps the accent
# with the fill. A border that stays gray draws a visible gray ring.
REQUIRED_BORDER_VARIABLES = (
    "--bs-btn-border-color",
    "--bs-btn-hover-border-color",
    "--bs-btn-active-border-color",
    "--bs-btn-disabled-border-color",
)

ACCENT_VALUE = "var(--portal-accent, #0077B6)"  # The one accent value that each state must use.

SCOPED_DUPLICATE = ".ws-page .btn-accent"  # The scoped copy that the shared rule replaced.

DECLARATION = re.compile(r"(--[a-z0-9-]+)\s*:\s*([^;]+);")  # One custom property declaration in a rule body.


def _read(stylesheet: Path) -> str:
    """Return the text of one stylesheet, and fail when the file is absent."""
    # A guard that reads nothing reports green over an empty set. Issue #2689
    # recorded that failure mode, so this helper fails on an unreadable input.
    if not stylesheet.is_file():
        pytest.fail(f"the guard cannot read {stylesheet}, so it proves nothing")
    return stylesheet.read_text(encoding="utf-8")


def _rule_body(text: str, selector: str) -> str | None:
    """Return the declaration block of one selector, or None when it is absent."""
    # The search anchors on a line start, so `.ws-page .btn-accent` never
    # matches when the test looks for the bare `.btn-accent` selector.
    match = re.search(rf"^{re.escape(selector)}\s*\{{(.*?)\}}", text, re.MULTILINE | re.DOTALL)
    return match.group(1) if match else None


@pytest.fixture(scope="module")
def accent_declarations() -> dict[str, str]:
    """Return the custom properties that the shared `.btn-accent` rule sets."""
    body = _rule_body(_read(PORTAL_STYLESHEET), ".btn-accent")
    if body is None:
        pytest.fail(f"{PORTAL_STYLESHEET} holds no `.btn-accent` rule, so the accent button has no style")
    declarations = {name: value.strip() for name, value in DECLARATION.findall(body)}
    print(f"accent_scope: checked 1 rule with {len(declarations)} custom property declarations")
    return declarations


def test_the_guard_reads_a_useful_number_of_declarations(accent_declarations):
    """The rule holds enough declarations, so the later tests mean something."""
    # Measured on 2026-10-06: the rule sets 14 custom properties. This floor
    # sits at the 12 that the two required groups need, so a rule that loses
    # most of its body fails here rather than in one named-variable test.
    assert len(accent_declarations) >= 12, f"the rule sets only {len(accent_declarations)} custom properties"


@pytest.mark.parametrize("variable", REQUIRED_FILL_VARIABLES + REQUIRED_BORDER_VARIABLES)
def test_each_button_state_keeps_the_accent(variable, accent_declarations):
    """Each state variable names the accent, so no state falls back to gray."""
    # Bootstrap reads one variable for each state. An absent variable gives that
    # state the Bootstrap default fill, which is the defect of issue #3658.
    assert variable in accent_declarations, f"`.btn-accent` sets no {variable}, so that state loses the accent fill"
    assert (
        accent_declarations[variable] == ACCENT_VALUE
    ), f"{variable} is {accent_declarations[variable]}, and the accent value is {ACCENT_VALUE}"


def test_the_shared_rule_sets_no_plain_fill_declaration():
    """The rule drops the plain declarations that the variables replaced."""
    # A plain `background-color` loses to the Bootstrap variables in the hover
    # state and in the disabled state, so it gives a reader a false promise.
    body = _rule_body(_read(PORTAL_STYLESHEET), ".btn-accent")
    overridden = re.compile(r"\s*(background-color|border-color):")  # The two declarations the variables replaced.
    plain = [line.strip() for line in (body or "").splitlines() if overridden.match(line)]
    assert not plain, f"`.btn-accent` keeps {len(plain)} plain declarations that Bootstrap overrides: {plain}"


def test_the_scoped_duplicate_stays_removed():
    """One page holds no copy of the shared accent rule."""
    # Issue #3658 moved the repair into the shared rule. A returned copy makes
    # two sources of truth, and the next accent change then repairs only one.
    text = _read(WEBSOCKET_STYLESHEET)
    rules = [line for line in text.splitlines() if SCOPED_DUPLICATE in line]
    print(f"duplicate_scope: checked {len(text.splitlines())} lines of {WEBSOCKET_STYLESHEET.name}")
    assert not rules, f"{WEBSOCKET_STYLESHEET.name} holds the scoped duplicate again: {rules}"
