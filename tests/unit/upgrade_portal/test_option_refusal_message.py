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

# The multi-site page. Issue #3273 records the drift. That page names three
# controls differently from the single-site page, and it holds one target
# version control for each device type.
ORG_OPTIONS_TEMPLATE = OPTIONS_TEMPLATE.with_name("org_options.html")

# The form field that carries the request forgery token. It names no option.
FORGERY_TOKEN_FIELD = "csrf_token"

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


def org_page_text() -> str:
    """Return the multi-site options page with every run of whitespace collapsed.

    Returns:
        The page text on one line.
    """
    return re.sub(r"\s+", " ", ORG_OPTIONS_TEMPLATE.read_text(encoding="utf-8"))


def posted_org_fields() -> set[str]:
    """Return the name of each option field that the multi-site form posts.

    Why:
        The multi-site form posts a plain form body, so each `name` attribute is
        one option that the route can refuse. The single-site page posts through
        its script, so its `name` attributes do not list its options.

    Returns:
        The posted field names, without the request forgery token.
    """
    names = set(re.findall(r'name="([a-z_]+)"', ORG_OPTIONS_TEMPLATE.read_text(encoding="utf-8")))  # Read each field.
    return names - {FORGERY_TOKEN_FIELD}  # The token names no option, so no refusal can name it.


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


@pytest.mark.parametrize("field", sorted(options.ORG_OPTION_HELP))
def test_every_multisite_label_matches_the_page(field: str) -> None:
    """Issue #3273: a multi-site label must name a control that the multi-site page paints.

    Args:
        field: The cloud field name under test.
    """
    assert options.ORG_OPTION_HELP[field][0] in org_page_text()  # The multi-site page paints this exact label.


@pytest.mark.parametrize("field", sorted(options.ORG_OPTION_HELP))
def test_a_multisite_refusal_names_the_label_and_the_rule(field: str) -> None:
    """A multi-site refusal names the multi-site label, states its rule, and repeats no typed value.

    Args:
        field: The cloud field name under test.
    """
    label, rule = options.ORG_OPTION_HELP[field]  # The label and the rule of the multi-site control.
    message = str(options.BadOptionError(field, labels=options.ORG_OPTION_HELP))  # Build the multi-site refusal.
    assert f'"{label}"' in message  # The message names the control that the operator sees.
    assert rule in message  # The message states the rule that the value broke.
    assert TYPED_VALUE not in message  # No value reaches the page or the log.


def test_every_posted_multisite_field_has_a_label() -> None:
    """Issue #3273: each field that the multi-site form posts has a multi-site label.

    Why:
        A posted field with no entry gives a refusal that names the internal
        field. Issue #3206 forbids that text on the multi-site page.
    """
    posted = posted_org_fields()  # Read the option fields from the template.
    assert "version_switch" in posted  # Prove that the parse reads the real form, not an empty file.
    missing = sorted(posted - set(options.ORG_OPTION_HELP))  # Find each posted field with no label.
    assert not missing, f"The form posts {len(posted)} fields. These fields have no label: {missing}"


def test_the_label_table_parameter_changes_only_the_label() -> None:
    """The multi-site table changes the label, and the field and the code stay the same."""
    error = options.BadOptionError("max_failure_percentage", labels=options.ORG_OPTION_HELP)  # A multi-site refusal.
    assert error.field == "max_failure_percentage"  # A caller still reads the field name.
    assert error.code == "bad_option"  # The contract code does not change.
    assert '"Maximum failure percentage"' in str(error)  # The multi-site page paints this label.
    assert "Failures allowed across the whole run" not in str(error)  # The single-site label is absent.
