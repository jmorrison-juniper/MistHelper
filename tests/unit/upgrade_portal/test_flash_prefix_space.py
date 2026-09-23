"""Guard the space after the signal word of each alert level in the portal stylesheet.

Why:
    Section 12 of ``portal.css`` prints a signal word before each alert, so the
    level reads without color. ``portal.js`` writes the alert sentence as plain
    text with no leading space. A signal word without a trailing space then
    touches the first word of the sentence. Issue #3277 records the sign-in
    alert that read "Warning:The portal could not sign you in".

What the tests read:
    The tests read the stylesheet text only. The browser proof is in
    ``tests/e2e/upgrade_portal/test_alert_prefix_space.py``.
"""

from __future__ import annotations

import logging  # Record each rule that a test reads.
import re  # Find one rule body and its content value in the stylesheet text.
from pathlib import Path  # Build the stylesheet path without a hard-coded separator.

import pytest  # The test framework and its parameter helper.

logger = logging.getLogger(__name__)  # The log of this test module.

# The stylesheet that holds section 12, the flash region.
CSS_PATH = (
    Path(__file__).resolve().parents[3] / "src" / "upgrade_portal" / "app" / "assets" / "static" / "css" / "portal.css"
)

# The signal word of each alert level. ASD-STE100 fixes "Warning" and "Caution".
SIGNAL_WORDS = {"info": "Note:", "success": "Done:", "warning": "Caution:", "danger": "Warning:"}

# The pattern of the content value inside one rule body.
CONTENT_PATTERN = re.compile(r'content:\s*"([^"]*)"')


def _prefix_content(level: str) -> str:
    """Return the generated text of the signal word rule for one alert level.

    Args:
        level: The alert level, such as ``danger``.

    Returns:
        The text of the ``content`` value, without the quotation marks.
    """
    logger.info("Reading the signal word rule of the level %s from %s", level, CSS_PATH.name)  # Before the read.
    css_text = CSS_PATH.read_text(encoding="utf-8")  # The stylesheet that the portal serves.
    rule = re.search(r"\.flash-" + level + r"::before\s*\{([^}]*)\}", css_text)  # The one rule of this level.
    assert rule is not None, f"portal.css holds no rule .flash-{level}::before."  # The level must name itself.
    content = CONTENT_PATTERN.search(rule.group(1))  # The generated text inside the rule body.
    assert content is not None, f"The rule .flash-{level}::before sets no content value."  # A rule with no text.
    logger.debug("The level %s prints %r", level, content.group(1))  # After the read, with the exact value.
    return content.group(1)  # The caller compares the text with the signal word.


@pytest.mark.parametrize("level", sorted(SIGNAL_WORDS))
def test_each_signal_word_ends_with_one_space(level: str) -> None:
    """Prove that each signal word ends with exactly one space.

    Why:
        The space must come from the rule, because the script writes the
        sentence with no leading space. A browser removes a space at the end of
        a line, so the space does not change a prefix that sits on its own line.

    Args:
        level: The alert level under test.
    """
    expected = SIGNAL_WORDS[level] + " "  # The signal word, then one space before the sentence.
    assert _prefix_content(level) == expected, f"The level {level} must print {expected!r}."
