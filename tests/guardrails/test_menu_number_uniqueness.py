"""Guardrail: one menu number never carries two different actions (issue #2065).

Why:
    `main` allocated menu 238 to the MSP license export, which is
    `interactive_safe`. The upgrade capture portal branch allocated menu 238 to
    the portal, which is `destructive`. Each branch passed
    `tests/guardrails/test_operation_registry_menu_coverage.py` on its own,
    because that test compares `menu_actions` against the registry inside one
    branch and never looks at the merge base.

    The two entries disagreed on the safety category, and the category decides
    whether an automated run may execute the option. Had the merge kept the
    portal action under the `interactive_safe` row, `--testinteractive` would
    have started a firmware upgrade portal during a normal test pass.

    The tests below hold the invariants that survive any branch: every menu
    number is unique, every number maps to exactly one action, and the number
    that starts the upgrade portal stays `destructive`.
"""

from __future__ import annotations

import MistHelper  # WHY: menu_actions is the authoritative runtime mapping.
from src.utils.operation_registry import OperationRegistry

CAPTURE_PORTAL_MENU = "239"  # The portal moved here when 238 reached main as the MSP export.
MSP_LICENSE_MENU = "238"  # `listMspLicenses`, merged to main first, so it keeps the number.

# WHY: menus 151 and 152 both called `DataCollectionManager.continuous_loop`
# with no argument that told them apart, yet each advertised different work.
# Issue #2066 resolved the pair: 152 was a plain duplicate of 151, so 152 is
# retired instead of given a fake second behavior. `RETIRED_MENU_NUMBERS`
# below records the resulting gap, so `test_the_numbers_run_without_a_gap`
# still catches a NEW unexplained gap while this recorded one stays quiet.
KNOWN_SHARED_ACTIONS: frozenset[tuple[str, str]] = frozenset()

# WHY: a retired number must never return to service, because a reused number
# could carry an operator's old habit into a new, different action. Each
# member of this set names the issue that retired it, in the comment beside
# the literal, so a later reader finds the reason without a git blame.
RETIRED_MENU_NUMBERS: frozenset[str] = frozenset(
    {
        "152",  # Issue #2066: a plain duplicate of 151's continuous_loop call.
    }
)


class TestMenuNumbersAreUnique:
    """No menu number is defined twice, and none is skipped."""

    def test_every_menu_key_is_unique(self) -> None:
        """A dict cannot hold a duplicate key, so a repeat would already be lost.

        Why:
            A second literal entry for one number silently replaces the first
            when Python builds the dict. The count comparison below is the only
            way to see that loss from inside the running program, because the
            duplicate leaves no trace in `menu_actions` itself.
        """
        keys = list(MistHelper.menu_actions)
        assert len(keys) == len(set(keys)), "menu_actions lost an entry to a duplicate key"

    def test_the_numbers_run_without_a_gap(self) -> None:
        """A gap means a number was retired, and a retired number invites reuse."""
        numbers = sorted(int(key) for key in MistHelper.menu_actions)
        expected = list(range(numbers[0], numbers[-1] + 1))
        missing = sorted(set(expected) - set(numbers))
        unexplained = [number for number in missing if str(number) not in RETIRED_MENU_NUMBERS]
        assert not unexplained, f"The menu numbering holds a gap at {unexplained}"

    def test_a_retired_number_never_returns_to_service(self) -> None:
        """Each retired number stays out of `menu_actions` for good."""
        reused = sorted(RETIRED_MENU_NUMBERS & set(MistHelper.menu_actions))
        assert not reused, f"A retired menu number is back in service: {reused}"

    def test_no_two_numbers_share_one_action(self) -> None:
        """Two numbers that call one function mean a rename left a stale row.

        Why:
            Issue #2065 produced the opposite fault, one number for two actions.
            This test covers the mirror case, which a careless renumber creates:
            the old number is left behind and both run the same code.
        """
        seen: dict[str, str] = {}  # WHY: maps the action name to the first number that used it.
        duplicates: list[str] = []
        for number, entry in MistHelper.menu_actions.items():
            action = getattr(entry[0], "__qualname__", "")  # A lambda shares one name, so skip it.
            if not action or "<lambda>" in action:
                continue  # WHY: every menu lambda is a distinct object with the same name.
            if action in seen:
                pair = (seen[action], number)
                if pair in KNOWN_SHARED_ACTIONS:
                    continue  # WHY: a recorded defect, tracked by its own issue.
                duplicates.append(f"{action} at {seen[action]} and {number}")
                continue
            seen[action] = number
        assert not duplicates, f"One action answers two menu numbers: {duplicates}"


class TestTheUpgradePortalStaysDestructive:
    """The number that starts the firmware upgrade portal never runs unattended."""

    def test_the_portal_menu_is_destructive(self) -> None:
        """`interactive_safe` would let `--testinteractive` start the portal."""
        entry = OperationRegistry.get(CAPTURE_PORTAL_MENU)
        assert entry["category"] == "destructive", (
            f"Menu {CAPTURE_PORTAL_MENU} starts the upgrade capture portal and drives a firmware "
            f"upgrade. It reads {entry['category']!r}, and only 'destructive' keeps it out of "
            "every automated run."
        )

    def test_the_portal_menu_never_runs_in_an_automated_pass(self) -> None:
        """The two automated sets must both exclude the portal."""
        options = list(MistHelper.menu_actions)
        assert CAPTURE_PORTAL_MENU not in OperationRegistry.safe_options(options)
        assert CAPTURE_PORTAL_MENU not in OperationRegistry.interactive_safe_options(options)

    def test_the_msp_license_menu_keeps_its_number(self) -> None:
        """`listMspLicenses` reached main first, so 238 belongs to it.

        Why:
            A later branch that takes 238 back would recreate issue #2065. This
            test names the owner of the number so the clash is visible at once.
        """
        entry = OperationRegistry.get(MSP_LICENSE_MENU)
        assert entry["category"] == "interactive_safe"
        action = getattr(MistHelper.menu_actions[MSP_LICENSE_MENU][0], "__qualname__", "")
        assert "MSPLicenseExporter" in action, f"Menu {MSP_LICENSE_MENU} no longer runs the MSP license export"
