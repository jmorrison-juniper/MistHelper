"""Guard the operations page against the hidden-panel defect of issue #3030.

Why:
    ``web_portal/templates/operations.html`` marks every collapsible panel with
    the Bootstrap class ``d-none``. Bootstrap declares that class with an
    ``!important`` rule.

    ``.d-none { display: none !important; }``

    An ``!important`` rule in a stylesheet outranks an inline style. Code that
    writes ``element.style.display`` therefore can never reveal such a panel.

    Issue #3030 records the result. Every panel of the operations page stayed
    invisible, so no user could reach the Run button of any of the 86 listed
    operations. The page looked empty after a click, and no test reported it.

    These tests read the shipped template and the shipped script, so they run in
    continuous integration with no browser and no server.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]  # A fixture moves the working folder, so use an absolute path.
TEMPLATE_PATH = REPO_ROOT / "web_portal" / "templates" / "operations.html"
SCRIPT_PATH = REPO_ROOT / "web_portal" / "static" / "js" / "operations.js"

# WHY: the class that Bootstrap declares with `!important`, which no inline style can beat.
HIDDEN_CLASS = "d-none"

# WHY: an element that carries the class must be toggled through this helper.
VISIBILITY_HELPER = "setElementVisible"

# WHY: these ids are the controls a user needs to run an operation and read its result.
REQUIRED_PANEL_IDS = (
    "selectedOp",
    "parameterForm",
    "executionPanel",
    "outputFiles",
    "stopBtn",
)


def read_template() -> str:
    """Return the operations page template."""
    assert TEMPLATE_PATH.is_file(), f"The guard cannot read {TEMPLATE_PATH}."
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def read_script() -> str:
    """Return the operations page script."""
    assert SCRIPT_PATH.is_file(), f"The guard cannot read {SCRIPT_PATH}."
    return SCRIPT_PATH.read_text(encoding="utf-8")


def hidden_element_ids() -> set[str]:
    """Return every element id that carries the hidden class in the template.

    Returns:
        The ids of the elements that start hidden, in any attribute order.
    """
    template = read_template()
    found: set[str] = set()
    for tag in re.findall(r"<[^>]+>", template):  # Read each opening tag one time.
        if HIDDEN_CLASS not in tag:  # The tag does not start hidden, so no rule applies.
            continue
        match = re.search(r'id="([A-Za-z0-9_-]+)"', tag)  # An id is what the script addresses.
        if match:  # A hidden tag without an id cannot be toggled by id, so skip it.
            found.add(match.group(1))
    return found


def inline_display_targets() -> dict[str, int]:
    """Return every element id that the script toggles with an inline display value.

    Returns:
        A map of the element id to the 1-based line that writes the value.
    """
    script = read_script()
    targets: dict[str, int] = {}
    pattern = re.compile(r"getElementById\('([A-Za-z0-9_-]+)'\)\s*\.style\.display\s*=")
    for number, line in enumerate(script.splitlines(), start=1):  # Report the line, so a repair is quick.
        match = pattern.search(line)
        if match:  # This line writes an inline display value on a named element.
            targets.setdefault(match.group(1), number)
    return targets


class TestTheTemplateAndScriptAgree:
    """Prove that no hidden panel is toggled through an inline display value."""

    def test_the_guard_measured_the_template_and_the_script(self) -> None:
        """State the measured counts, so an empty read cannot pass in silence."""
        hidden = hidden_element_ids()
        script = read_script()
        print(f"The operations guard checked {len(hidden)} hidden element ids against {len(script)} script characters.")
        assert len(hidden) > 0, "The template holds no hidden element, so this guard measures nothing."
        assert len(script) > 1000, "The script is too small to be the real operations controller."

    @pytest.mark.parametrize("panel_id", REQUIRED_PANEL_IDS)
    def test_each_required_panel_is_never_revealed_by_an_inline_style(self, panel_id: str) -> None:
        """Issue #3030. An inline display value cannot beat the `!important` class rule."""
        if panel_id not in hidden_element_ids():  # The panel no longer starts hidden, so the rule does not apply.
            return
        offenders = inline_display_targets()
        assert panel_id not in offenders, (
            f"{SCRIPT_PATH.name}:{offenders.get(panel_id)} sets style.display on '{panel_id}', "
            f"and operations.html marks that element with '{HIDDEN_CLASS}'. "
            f"Bootstrap declares that class with 'display: none !important', so the panel stays hidden. "
            f"Call {VISIBILITY_HELPER}('{panel_id}', true) instead. Issue #3030."
        )

    def test_no_hidden_element_is_toggled_by_an_inline_style(self) -> None:
        """Cover every hidden element, including one that a later change adds."""
        hidden = hidden_element_ids()
        offenders = {element_id: line for element_id, line in inline_display_targets().items() if element_id in hidden}
        listed = "\n".join(f"  {SCRIPT_PATH.name}:{line} -> {name}" for name, line in sorted(offenders.items()))
        assert offenders == {}, (
            f"These elements start hidden with the class '{HIDDEN_CLASS}', and the script still "
            f"reveals them with an inline style:\n{listed}\n"
            f"Call {VISIBILITY_HELPER} instead. Issue #3030."
        )

    def test_the_script_defines_the_visibility_helper(self) -> None:
        """The repair depends on one shared helper, so pin its presence."""
        assert (
            f"function {VISIBILITY_HELPER}(" in read_script()
        ), f"{SCRIPT_PATH.name} defines no {VISIBILITY_HELPER}. Every panel toggle depends on it. Issue #3030."

    def test_the_helper_removes_the_hidden_class(self) -> None:
        """A helper that only wrote an inline style would repair nothing."""
        script = read_script()
        start = script.index(f"function {VISIBILITY_HELPER}(")  # Read the helper body only.
        body = script[start : start + 900]
        assert (
            f"classList.remove('{HIDDEN_CLASS}')" in body
        ), f"{VISIBILITY_HELPER} never removes '{HIDDEN_CLASS}', so it cannot reveal a panel. Issue #3030."
        assert (
            f"classList.add('{HIDDEN_CLASS}')" in body
        ), f"{VISIBILITY_HELPER} never adds '{HIDDEN_CLASS}', so it cannot hide a panel. Issue #3030."


class TestTheRunControlsStayReachable:
    """Prove that the template still holds the controls a user needs."""

    @pytest.mark.parametrize(
        ("test_id", "purpose"),
        [
            ("selected-op-panel", "the panel that holds the Run button"),
            ("run-btn", "the control that starts an operation"),
            ("stop-btn", "the control that stops an operation"),
            ("execution-panel", "the live log of one run"),
            ("log-viewer", "the text of the live log"),
        ],
    )
    def test_the_template_holds_the_stable_test_id(self, test_id: str, purpose: str) -> None:
        """A renamed hook would make every browser test silently stop covering the page."""
        assert f'data-testid="{test_id}"' in read_template(), f"The template holds no hook for {purpose}."
