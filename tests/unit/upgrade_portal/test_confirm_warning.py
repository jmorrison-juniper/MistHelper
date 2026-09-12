"""The tests of the confirmation warning of the upgrade capture portal.

Why:
    The confirmation warning is the last sentence an operator reads before a
    destructive act. Issue #2099 records the first build of that sentence. It
    said "the upgrade writes new firmware to 1 devices and reboots each one" on
    every plan. The sentence never read the saved reboot option. It therefore
    contradicted the plan block on the same screen. It also wrote a plural noun
    for a count of one.

    A warning that states the reboot without reading it teaches an operator to
    ignore the warning. The operator then reads "reboots each one" on every
    plan and learns that the sentence carries no information.

    Issue #2007 records why the opposite promise is worse. On 2026-08-24 one
    EX4100-F-12P rebooted four seconds after the write, although the request
    carried ``reboot: false``. The switch carried power over Ethernet for six
    access points, and the site lost service for about six minutes. A warning
    that promised no outage was false on that day. The sentence for a disabled
    reboot therefore names the residual risk and promises nothing.

    These tests render the real template with Jinja and the strict undefined
    type. No test opens a socket, and no test names a real credential.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from src.upgrade_portal.app.routes import upgrade

# WHY: This file sits at tests/unit/upgrade_portal, so the root is three levels up.
_REPO_ROOT = Path(__file__).resolve().parents[3]

# WHY: The template folder of the portal, beside the routes package.
_TEMPLATE_ROOT = Path(upgrade.__file__).resolve().parents[1] / "assets" / "templates"

# WHY: The page under test. The route names the same value in CONFIRM_TEMPLATE.
_TEMPLATE_NAME = "upgrade/confirm.html"

# WHY: The stable hook that a browser test reads to find the warning sentence.
_WARNING_TEST_ID = "upgrade-confirm-warning"

# WHY: The two controls that already carry a contract identifier. A change to
#      the warning must never move either one, or every browser test breaks.
_KEPT_TEST_IDS = ("upgrade-confirm-input", "upgrade-start-button", "upgrade-warning-list")

# WHY: The element that holds the warning. The paragraph spans several lines in
#      the template, so the pattern reads across a newline.
_WARNING_PATTERN = re.compile(
    rf'<p[^>]*data-testid="{_WARNING_TEST_ID}"[^>]*>(.*?)</p>',
    re.DOTALL,
)

# WHY: ASD-STE100 asks a warning to lead with a signal word. Both branches keep it.
_SIGNAL_WORD = "Warning:"

# WHY: The claim that issue #2099 reported. A plan that disables the reboot must
#      never print it, because the plan block prints "No" on the same screen.
_EVERY_DEVICE_REBOOT_CLAIM = "reboots each one"

# WHY: The sentence a plan with the reboot enabled must carry. It names the two
#      device kinds the portal reboots, which matches the plan block wording.
_REBOOT_ON_SENTENCE = "The portal reboots each switch and each gateway."

# WHY: The three sentences a plan with the reboot disabled must carry. The first
#      states the plan. The second and the third state the residual risk of
#      issue #2007 and the cost of a device that never reboots.
_REBOOT_OFF_SENTENCES = (
    "The portal does not ask for a reboot.",
    "A device can still reboot on its own after the write.",
    "A device that does not reboot keeps the old firmware until its next reboot.",
)

# WHY: The shared consequence. One term for one concept, so both branches reuse
#      the same sentence instead of a synonym.
_OFFLINE_SENTENCE = "A device is offline while it reboots."

# WHY: Words that would turn the warning into a promise. Issue #2007 proves the
#      portal cannot make any of them, because a device rebooted on its own.
_FORBIDDEN_PROMISES = (
    "no outage",
    "stays up",
    "stays online",
    "remains online",
    "no device reboots",
    "no reboot happens",
    "without any interruption",
)


def _static_url(endpoint: str, **values: Any) -> str:
    """Return a stand-in path for a static asset.

    Why:
        The base page asks ``url_for`` for its stylesheets and its scripts.
        Flask supplies that helper, and this test renders without Flask, so the
        environment needs a helper of its own.

    Args:
        endpoint: The endpoint name. Always ``static`` on this page.
        **values: The endpoint arguments. Holds ``filename``.

    Returns:
        A path that stands in for the real asset path.
    """
    return f"/{endpoint}/{values.get('filename', '')}"


@pytest.fixture(scope="module")
def environment() -> Environment:
    """Return a Jinja environment that loads the real portal templates.

    Why:
        The page under test extends the real base page, so a stub loader would
        prove nothing. The strict undefined type turns a missing value into a
        failure instead of an empty string. The page claims that state in its
        own header comment.

    Returns:
        The environment.
    """
    built = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_ROOT)),
        autoescape=True,
        undefined=StrictUndefined,
    )
    built.globals["url_for"] = _static_url  # Flask supplies this name, and this render has no Flask.
    built.globals["request"] = None  # The navigation partial reads the path through a guard.
    return built


def _targets(count: int) -> list[dict[str, str]]:
    """Return one target row for each device the plan names.

    Why:
        The page counts the rows itself, so the count of the list is the only
        field that matters to the warning. The other fields keep the row
        readable beside a real run record.

    Args:
        count: The number of device rows to build.

    Returns:
        The rows, with an obviously fake address on each one.
    """
    return [{"mac": f"0011220000{index:02x}", "model": "EX4100-F-12P"} for index in range(count)]


def _render(environment: Environment, *, reboot: bool, count: int) -> str:
    """Render the confirmation page for one reboot choice and one device count.

    Args:
        environment: The Jinja environment.
        reboot: The saved reboot option of the plan.
        count: The number of devices the plan names.

    Returns:
        The rendered page.
    """
    context = {
        "run_id": "run-2099",  # An obviously fake run key.
        "site_name": "Fake Site",  # The heading of the page.
        "targets": _targets(count),  # The page counts these rows for the warning.
        "options": {"reboot": reboot, "junos_file_action": False, "strategy": "big_bang"},
        "pre_capture_id": "capture-2099",  # A saved pre-check unlocks the confirmation field.
        "pre_capture_verified": True,  # FR-035 opens the gate on this value only.
    }
    return environment.get_template(_TEMPLATE_NAME).render(**context)


def _warning(environment: Environment, *, reboot: bool, count: int) -> str:
    """Return the warning sentence of one rendered page, on one line.

    Why:
        The paragraph sits on several source lines, so a raw read would carry a
        newline in the middle of every sentence. A reindent of the template
        would then break a test that proved nothing about the wording.

    Args:
        environment: The Jinja environment.
        reboot: The saved reboot option of the plan.
        count: The number of devices the plan names.

    Returns:
        The warning text, with every run of white space replaced by one space.

    Raises:
        AssertionError: When the page carries no warning element.
    """
    found = _WARNING_PATTERN.search(_render(environment, reboot=reboot, count=count))
    assert found is not None, f"The page carries no element with the test identifier {_WARNING_TEST_ID}."
    return " ".join(found.group(1).split())


# ---------------------------------------------------------------------------
# The warning reads the saved reboot option
# ---------------------------------------------------------------------------


class TestTheWarningReadsTheSavedRebootOption:
    """The sentence states what the saved plan will really do."""

    def test_a_disabled_reboot_never_claims_a_reboot_of_every_device(self, environment: Environment) -> None:
        """Issue #2099 reported this exact contradiction on one screen."""
        assert _EVERY_DEVICE_REBOOT_CLAIM not in _warning(environment, reboot=False, count=1)

    def test_a_disabled_reboot_states_that_the_portal_asks_for_none(self, environment: Environment) -> None:
        """The operator must read the plan, and not a fixed sentence."""
        assert _REBOOT_OFF_SENTENCES[0] in _warning(environment, reboot=False, count=2)

    def test_an_enabled_reboot_names_the_switch_and_the_gateway(self, environment: Environment) -> None:
        """The plan block names both kinds, so the warning names both kinds."""
        assert _REBOOT_ON_SENTENCE in _warning(environment, reboot=True, count=2)

    def test_an_enabled_reboot_states_the_outage(self, environment: Environment) -> None:
        """A reboot drops the link, and the operator must expect that."""
        assert _OFFLINE_SENTENCE in _warning(environment, reboot=True, count=2)

    def test_the_two_reboot_states_read_differently(self, environment: Environment) -> None:
        """A sentence that never changes carries no information."""
        enabled = _warning(environment, reboot=True, count=2)
        assert enabled != _warning(environment, reboot=False, count=2)

    def test_a_missing_reboot_option_reads_as_an_enabled_reboot(self, environment: Environment) -> None:
        """The saved default is a reboot, so the safe read repeats it."""
        page = environment.get_template(_TEMPLATE_NAME).render(
            run_id="run-2099",
            site_name="Fake Site",
            targets=_targets(1),
            options={},  # An older record holds no reboot field at all.
            pre_capture_id="capture-2099",
            pre_capture_verified=True,
        )
        found = _WARNING_PATTERN.search(page)
        assert found is not None
        assert _REBOOT_ON_SENTENCE in " ".join(found.group(1).split())


# ---------------------------------------------------------------------------
# The warning never promises that a device stays up
# ---------------------------------------------------------------------------


class TestTheWarningPromisesNoDeviceStaysUp:
    """Issue #2007 proves a device can reboot although the plan forbids it."""

    def test_a_disabled_reboot_still_warns_about_a_reboot_of_its_own(self, environment: Environment) -> None:
        """One EX4100-F-12P did exactly this and dropped six access points."""
        assert _REBOOT_OFF_SENTENCES[1] in _warning(environment, reboot=False, count=1)

    def test_a_disabled_reboot_states_the_cost_of_no_reboot(self, environment: Environment) -> None:
        """A device that never reboots runs the old firmware, and looks upgraded."""
        assert _REBOOT_OFF_SENTENCES[2] in _warning(environment, reboot=False, count=1)

    def test_a_disabled_reboot_still_states_the_outage(self, environment: Environment) -> None:
        """The reboot can still happen, so the consequence still applies."""
        assert _OFFLINE_SENTENCE in _warning(environment, reboot=False, count=1)

    def test_no_branch_promises_that_a_device_stays_up(self, environment: Environment) -> None:
        """A promise the portal cannot keep is worse than no warning."""
        for reboot in (True, False):
            text = _warning(environment, reboot=reboot, count=2).lower()
            for promise in _FORBIDDEN_PROMISES:
                assert promise not in text, f"The warning promises {promise!r}."

    def test_every_branch_states_that_a_write_cannot_be_undone(self, environment: Environment) -> None:
        """The write is the irreversible half, and it happens either way."""
        for reboot in (True, False):
            assert "The portal cannot undo a write." in _warning(environment, reboot=reboot, count=2)


# ---------------------------------------------------------------------------
# The count reads as a number a person writes
# ---------------------------------------------------------------------------


class TestTheCountUsesTheRightNoun:
    """Issue #2099 reported the text ``1 devices`` on the live portal."""

    @pytest.mark.parametrize("reboot", [True, False])
    def test_one_device_reads_as_one_device(self, environment: Environment, reboot: bool) -> None:
        """The singular form proves the sentence counted, and did not guess."""
        text = _warning(environment, reboot=reboot, count=1)
        assert "1 device" in text
        assert "1 devices" not in text

    @pytest.mark.parametrize("reboot", [True, False])
    def test_two_devices_read_as_two_devices(self, environment: Environment, reboot: bool) -> None:
        """A count above one keeps the plural form."""
        assert "2 devices" in _warning(environment, reboot=reboot, count=2)

    def test_no_device_reads_as_the_plural_form(self, environment: Environment) -> None:
        """An empty plan renders a locked page, and English writes ``0 devices``."""
        assert "0 devices" in _warning(environment, reboot=True, count=0)


# ---------------------------------------------------------------------------
# The page keeps every hook a browser test already reads
# ---------------------------------------------------------------------------


class TestThePageKeepsEveryTestIdentifier:
    """A wording change must never move a control a browser test selects."""

    @pytest.mark.parametrize("identifier", _KEPT_TEST_IDS)
    def test_the_page_keeps_the_named_identifier(self, environment: Environment, identifier: str) -> None:
        """These three names come from contracts/ui-testids.md."""
        assert f'data-testid="{identifier}"' in _render(environment, reboot=True, count=1)

    def test_the_warning_carries_a_stable_identifier(self, environment: Environment) -> None:
        """A browser test reads the two texts and proves they differ."""
        assert f'data-testid="{_WARNING_TEST_ID}"' in _render(environment, reboot=False, count=1)

    @pytest.mark.parametrize("reboot", [True, False])
    def test_every_branch_leads_with_the_signal_word(self, environment: Environment, reboot: bool) -> None:
        """ASD-STE100 asks a warning to name itself before it states the risk."""
        assert _warning(environment, reboot=reboot, count=1).startswith(_SIGNAL_WORD)

    @pytest.mark.parametrize("reboot", [True, False])
    def test_the_plan_block_and_the_warning_agree(self, environment: Environment, reboot: bool) -> None:
        """The screen showed ``No`` beside ``reboots each one`` before this fix."""
        page = _render(environment, reboot=reboot, count=1)
        planned = "Yes, for each switch and each gateway" in page
        assert planned is reboot  # The plan block still reports the saved option.
        assert (_REBOOT_ON_SENTENCE in _warning(environment, reboot=reboot, count=1)) is reboot
