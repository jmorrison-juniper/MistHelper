"""Guard the map viewer device list against stored cross-site scripting.

The map viewer renders device records that come from the Mist cloud. A device
name is free text that an operator sets. If the template writes that name into
``innerHTML``, a crafted name runs as script in the browser of every operator
who opens the floor plan.

These tests read the template and prove that the device list builder uses
``textContent`` only. See issue #1939.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pytest

# The template under test. The test reads the shipped file, because the defect
# lives in the markup and not in Python code.
TEMPLATE_PATH = Path(__file__).resolve().parents[3] / "web_portal" / "templates" / "map_viewer.html"

# The name of the function that builds one list item for each device.
TARGET_FUNCTION = "renderDeviceList"

# A device field that an operator controls in the Mist cloud. Each one is a
# free text value, so each one is an injection source.
UNTRUSTED_FIELDS = ("d.name", "d.mac", "d.type")


def _read_template() -> str:
    """Return the text of the map viewer template."""
    logging.info("Reading the map viewer template from %s", TEMPLATE_PATH)
    # Read with an explicit encoding, because the default encoding on Windows
    # is not UTF-8 and the template carries a numeric HTML entity.
    source = TEMPLATE_PATH.read_text(encoding="utf-8")
    logging.debug("Read %d characters from the map viewer template", len(source))
    return source


def _extract_function(source: str, name: str) -> str:
    """Return the body of one JavaScript function from the template text."""
    logging.info("Extracting the body of the function %s", name)
    # Locate the declaration. The template declares every function at the top
    # level with the plain ``function name(`` form.
    start = source.find(f"function {name}(")
    # Fail loudly when the function is gone, because a rename would otherwise
    # make this guard pass without testing anything.
    assert start != -1, f"The template no longer declares {name}."
    # Find the opening brace of the body so that the brace counter starts at a
    # known position.
    brace_start = source.index("{", start)
    # Track the nesting depth, because the body contains nested blocks.
    depth = 0
    # Walk one character at a time until the depth returns to zero.
    for index in range(brace_start, len(source)):
        # Enter a nested block.
        if source[index] == "{":
            depth += 1
        # Leave a block.
        elif source[index] == "}":
            depth -= 1
            # A depth of zero marks the closing brace of the function.
            if depth == 0:
                body = source[brace_start : index + 1]
                logging.debug("Extracted %d characters for %s", len(body), name)
                return body
    # Reaching this line means the braces are unbalanced.
    pytest.fail(f"The braces of the function {name} are unbalanced.")


def _innerhtml_assignments(body: str) -> list[str]:
    """Return the right side of every ``innerHTML`` assignment in the body."""
    logging.info("Collecting the innerHTML assignments in the function body")
    # Match an assignment to innerHTML and capture the rest of the statement.
    # The statement can span lines, so capture up to the terminating semicolon.
    pattern = re.compile(r"\.innerHTML\s*=\s*([^;]*);", re.DOTALL)
    # Strip each match so that a comparison against an empty string literal is
    # not defeated by leading whitespace.
    matches = [match.group(1).strip() for match in pattern.finditer(body)]
    logging.debug("Found %d innerHTML assignments in the function body", len(matches))
    return matches


class TestDeviceListDoesNotUseInnerHtml:
    """The device list must not write untrusted device data into innerHTML."""

    def test_no_untrusted_field_reaches_innerhtml(self) -> None:
        """No device field appears on the right side of an innerHTML assignment."""
        logging.info("Checking that no device field reaches innerHTML")
        # Read the template and narrow the search to the device list builder.
        body = _extract_function(_read_template(), TARGET_FUNCTION)
        # Inspect every assignment, because one safe assignment does not make
        # the others safe.
        for assignment in _innerhtml_assignments(body):
            # Compare against each injection source in turn.
            for field in UNTRUSTED_FIELDS:
                # A device field on the right side is the defect from #1939.
                assert field not in assignment, (
                    f"{TARGET_FUNCTION} writes {field} into innerHTML. " "A crafted device name then runs as script."
                )
        logging.debug("No device field reaches innerHTML")

    def test_only_the_empty_string_clears_innerhtml(self) -> None:
        """The one allowed innerHTML assignment clears the list."""
        logging.info("Checking that innerHTML is only assigned an empty string")
        # Read the template and narrow the search to the device list builder.
        body = _extract_function(_read_template(), TARGET_FUNCTION)
        # The builder clears the previous list before it appends new rows. That
        # single assignment writes a constant, so it stays allowed.
        allowed = {"''", '""'}
        # Reject any other assignment, which catches a future concatenation
        # even when the concatenation uses a field this test does not name.
        for assignment in _innerhtml_assignments(body):
            assert assignment in allowed, (
                f"{TARGET_FUNCTION} assigns {assignment!r} to innerHTML. "
                "Build the row from DOM nodes and set textContent instead."
            )
        logging.debug("Every innerHTML assignment writes an empty string")


class TestDeviceListUsesTextContent:
    """The device list must render untrusted device data with textContent."""

    def test_the_builder_sets_textcontent(self) -> None:
        """The device list builder assigns textContent at least once."""
        logging.info("Checking that the device list builder uses textContent")
        # Read the template and narrow the search to the device list builder.
        body = _extract_function(_read_template(), TARGET_FUNCTION)
        # The browser escapes a textContent value, so this is the safe sink.
        assert "textContent" in body, (
            f"{TARGET_FUNCTION} never sets textContent. " "The device label must reach the page through a safe sink."
        )
        logging.debug("The device list builder uses textContent")

    def test_the_device_label_uses_textcontent(self) -> None:
        """The device name and the device type both reach textContent."""
        logging.info("Checking that each device field reaches textContent")
        # Read the template and narrow the search to the device list builder.
        body = _extract_function(_read_template(), TARGET_FUNCTION)
        # Match an assignment to textContent and capture the rest of the
        # statement, which mirrors the innerHTML matcher above.
        pattern = re.compile(r"\.textContent\s*=\s*([^;]*);", re.DOTALL)
        # Join the safe sinks into one blob so that a field can appear in any
        # one of them.
        safe_sinks = " ".join(match.group(1) for match in pattern.finditer(body))
        # The device name is the field an operator edits most often, so it is
        # the field an attacker reaches first.
        assert "d.name" in safe_sinks, "The device name must reach textContent."
        # The device type comes from the same API record, so it needs the same
        # treatment.
        assert "d.type" in safe_sinks, "The device type must reach textContent."
        logging.debug("Each device field reaches textContent")


class TestTheGuardStillMatchesTheFile:
    """The guard must fail when the template moves, not pass by accident."""

    def test_the_template_exists(self) -> None:
        """The template path still points at a real file."""
        logging.info("Checking that the map viewer template exists")
        # A missing file would make every other test in this module error, but
        # this test names the cause directly.
        assert TEMPLATE_PATH.is_file(), f"The template {TEMPLATE_PATH} is missing."
        logging.debug("The map viewer template exists")

    def test_the_safe_convention_holds_elsewhere(self) -> None:
        """The site list still uses the safe textContent convention."""
        logging.info("Checking the safe convention in the site list")
        # The rest of the template already uses textContent. This test pins
        # that convention so that a later edit does not spread the defect.
        source = _read_template()
        # The site list renders a site name that comes from the same API.
        assert "opt.textContent = site.name;" in source, (
            "The site list no longer uses textContent. " "Every Mist value must reach the page through a safe sink."
        )
        logging.debug("The site list still uses textContent")
