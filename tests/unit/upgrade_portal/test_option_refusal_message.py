"""Unit tests for the refusal message of one upgrade option.

Why:
    Issue #2195 records the earlier message. A refused value answered `the
    upgrade option start_time holds a value that the portal refuses`, and the
    word `start_time` appeared on no control of the page.

    The audience of this project is a junior engineer of a network operations
    center. That message asked the engineer to map a cloud field name onto a
    control label with no table to read, and it never stated the rule that the
    value broke.

    The drift test below matters most. A label that no longer matches the page
    sends the operator to a control that does not exist, which is worse than the
    field name it replaced.
"""

from __future__ import annotations

import pathlib
import re

import pytest

from src.upgrade_portal.upgrade import options

# The page that paints every control named in the message map.
OPTIONS_TEMPLATE = (
    pathlib.Path(__file__).resolve().parents[3]
    / "src"
    / "upgrade_portal"
    / "app"
    / "assets"
    / "templates"
    / "upgrade"
    / "options.html"
)

# One value that the operator typed and that the portal refused. No message may
# repeat it, because the value arrives straight from the browser.
TYPED_VALUE = "300"


def page_text() -> str:
    """Return the options page with every run of whitespace collapsed.

    Why:
        A template wraps a label across two lines, so a plain substring test
        fails against text that the browser paints as one line.

    Returns:
        The page text on one line.
    """
    return re.sub(r"\s+", " ", OPTIONS_TEMPLATE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("field", sorted(options.OPTION_HELP))
def test_a_refusal_names_the_control_label(field: str) -> None:
    """Every refusal names the control that the operator sees.

    Args:
        field: The cloud field name under test.
    """
    label = options.OPTION_HELP[field][0]  # The label that the page paints.
    assert label in str(options.BadOptionError(field))  # The message names that label.


@pytest.mark.parametrize("field", sorted(options.OPTION_HELP))
def test_a_refusal_states_the_rule(field: str) -> None:
    """Every refusal states the rule that the value broke.

    Args:
        field: The cloud field name under test.
    """
    rule = options.OPTION_HELP[field][1]  # The rule of that control.
    assert rule in str(options.BadOptionError(field))  # The message states it.


@pytest.mark.parametrize("field", sorted(options.OPTION_HELP))
def test_every_label_matches_the_page(field: str) -> None:
    """A label that drifts from the page names a control that does not exist.

    Why:
        The message exists to send the operator to one control. A stale label is
        worse than the cloud field name it replaced, because the operator then
        searches the page for text that no control carries.

    Args:
        field: The cloud field name under test.
    """
    assert options.OPTION_HELP[field][0] in page_text()  # The page paints this exact label.


@pytest.mark.parametrize("field", sorted(options.OPTION_HELP))
def test_a_refusal_repeats_no_typed_value(field: str) -> None:
    """A refused value arrives from the browser, so no message may echo it.

    Args:
        field: The cloud field name under test.
    """
    assert TYPED_VALUE not in str(options.BadOptionError(field))  # No value reaches the page or the log.


def test_the_error_code_does_not_change() -> None:
    """The contract fixes `bad_option`, so every existing client keeps working."""
    assert options.BadOptionError("start_time").code == "bad_option"


def test_an_unmapped_field_still_reads_plainly() -> None:
    """A field with no entry still names itself and points at the note.

    Why:
        A later writer may add a control and forget the entry. A message with no
        name at all would help nobody, so the field name stays as the fallback.
    """
    message = str(options.BadOptionError("nonesuch"))
    assert "nonesuch" in message  # The reader still learns which option failed.
    assert options.UNKNOWN_OPTION_RULE in message  # The reader learns where to find the rule.
