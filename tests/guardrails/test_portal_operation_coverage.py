"""Guard the portal operation list against the registry (issue #3082).

Why:
    The operations dashboard listed 86 operations while ``OperationRegistry``
    called 165 of them safe to run. A second gate compared the menu number
    against 90, and a menu number states when an operation was added, not what
    the operation does. That bound hid 79 operations.

    Warning: the bound also created a silent trap. A new safe operation above it
    never appeared in the portal, and no test reported the absence. The operator
    saw a shorter list and could not tell that it was incomplete.

    These tests compare the portal against the registry directly, so a future
    numeric bound, a stale description map, or a forgotten operation all fail
    here instead of reaching an operator.
"""

from __future__ import annotations

import pytest

from src.utils.menu_entry import MenuEntry
from src.utils.operation_registry import OperationRegistry
from web_portal.menu_registry import MENU_DESCRIPTIONS
from web_portal.services.operation import CATEGORY_RANGES, PORTAL_RUNNABLE_CATEGORIES, OperationExecutor

# WHY: the two classes the portal may run. Every other class stays out.
ELIGIBLE_CATEGORIES = ("safe", "interactive_safe")

# WHY: a class the portal must always refuse, whatever the menu number is.
REFUSED_CATEGORIES = (
    "destructive",
    "websocket",
    "interactive",
    "resource_intensive",
    "continuous_loop",
    "unregistered",
)


def eligible_options() -> set[str]:
    """Return every option the registry calls safe or interactive safe."""
    return {
        option
        for option in OperationRegistry.registered_options()
        if OperationRegistry.skip_category(option) in ELIGIBLE_CATEGORIES
    }


def options_by_category(category: str) -> set[str]:
    """Return every registered option of one safety class."""
    return {
        option
        for option in OperationRegistry.registered_options()
        if OperationRegistry.skip_category(option) == category
    }


def build_executor(options: set[str]) -> OperationExecutor:
    """Return an executor whose menu holds one row for each supplied option."""
    menu_actions = {
        option: MenuEntry(
            menu_id=option,
            handler=lambda: None,  # The gate decides before it ever calls the handler.
            title=f"Operation {option}",
            category="safe",  # OperationRegistry supplies the real verdict, not this field.
            destructive=False,
            supports_fast=False,
        )
        for option in options
    }
    return OperationExecutor(menu_actions, None, None, None)


@pytest.fixture
def executor():
    """Build an executor over every registered option, then release its pool."""
    built = build_executor(set(OperationRegistry.registered_options()))
    yield built
    built._pool.shutdown(wait=False)  # Release the worker threads, so the test leaves none.


class TestThePortalAdmitsEverySafeOperation:
    """The registry is the single source of truth, so the portal must match it."""

    def test_the_guard_measured_the_registry(self) -> None:
        """State the measured counts, so an empty registry cannot pass in silence."""
        eligible = eligible_options()
        total = len(OperationRegistry.registered_options())
        print(f"The portal guard checked {len(eligible)} eligible options out of {total} registered.")
        assert len(eligible) > 100, "The registry reports too few safe options for this guard to mean anything."

    def test_the_portal_admits_every_eligible_option(self, executor) -> None:
        """Issue #3082. This is the assertion the numeric bound failed."""
        refused = sorted(
            (option for option in eligible_options() if not executor._is_portal_runnable(option)),
            key=lambda value: float(value.replace("a", ".1")),
        )
        assert refused == [], (
            f"The portal refuses {len(refused)} operations that the registry calls safe: "
            f"{', '.join(refused)}. A menu number must not decide what the portal may run. Issue #3082."
        )

    def test_the_listing_shows_every_eligible_option(self, executor) -> None:
        """A runnable operation that the page never lists is unreachable."""
        listed = {
            operation["menu_number"]
            for category in executor.build_category_list(executor._menu_actions)
            for operation in category["operations"]
        }
        missing = sorted(eligible_options() - listed, key=lambda value: float(value.replace("a", ".1")))
        assert missing == [], f"The page lists none of these safe operations: {', '.join(missing)}."

    def test_no_numeric_bound_remains(self) -> None:
        """A reintroduced threshold would hide a new safe operation in silence."""
        from web_portal.services import operation as module

        assert not hasattr(module, "DESTRUCTIVE_THRESHOLD"), (
            "A numeric menu bound returned to the portal gate. The registry decides the safety class, "
            "and a menu number states only when an operation was added. Issue #3082."
        )
        assert not hasattr(
            module, "PORTAL_EXPLICIT_ALLOWLIST"
        ), "An explicit allowlist returned. It existed only to work around the numeric bound. Issue #3082."


class TestThePortalStillRefusesEveryUnsafeClass:
    """Widening the portal must not weaken it."""

    @pytest.mark.parametrize("category", REFUSED_CATEGORIES)
    def test_the_portal_refuses_the_class(self, executor, category: str) -> None:
        """Every class outside the two eligible ones must stay out, at any number."""
        options = options_by_category(category)
        if not options:  # A class with no member cannot prove anything here.
            pytest.skip(f"The registry holds no option of the class {category}.")
        admitted = sorted(option for option in options if executor._is_portal_runnable(option))
        assert admitted == [], f"The portal admits these {category} operations: {', '.join(admitted)}."

    def test_the_portal_refuses_an_unparseable_key(self, executor) -> None:
        """The gate must stay fail-closed on a key the page cannot place."""
        assert executor._is_portal_runnable("x1") is False

    def test_the_runnable_categories_stay_narrow(self) -> None:
        """Widening this set would admit every destructive operation at once."""
        assert PORTAL_RUNNABLE_CATEGORIES == frozenset({"safe", "interactive_safe"})

    def test_a_destructive_operation_is_refused_at_the_run_path(self, executor) -> None:
        """The listing and the run path must agree, or a hidden row could still run."""
        destructive = sorted(options_by_category("destructive"))
        assert len(destructive) > 0, "The registry holds no destructive option, so this guard proves nothing."
        refusal = executor._validate_operation(destructive[0])
        assert isinstance(refusal, dict), "The run path accepted a destructive operation."
        assert "error" in refusal, f"The refusal names no reason for the operator: {refusal}."


class TestTheDescriptionMapMatchesTheRegistry:
    """The portal reads this map when it cannot import MistHelper."""

    def test_the_map_holds_every_eligible_option(self) -> None:
        """A missing row leaves an operation invisible on the fallback path."""
        missing = sorted(eligible_options() - set(MENU_DESCRIPTIONS), key=lambda v: float(v.replace("a", ".1")))
        assert missing == [], (
            f"The static description map names none of these safe operations: {', '.join(missing)}. "
            "Run python scripts/generate_portal_menu_registry.py. Issue #3082."
        )

    def test_the_map_holds_no_ineligible_option(self) -> None:
        """A stale row offers an operation the portal then refuses to run."""
        stale = sorted(set(MENU_DESCRIPTIONS) - eligible_options(), key=lambda v: float(v.replace("a", ".1")))
        assert stale == [], (
            f"The static description map names these operations that the portal cannot run: {', '.join(stale)}. "
            "Run python scripts/generate_portal_menu_registry.py. Issue #3082."
        )

    def test_every_description_carries_text(self) -> None:
        """An empty description leaves a blank row that an operator cannot read."""
        blank = sorted(key for key, text in MENU_DESCRIPTIONS.items() if not str(text).strip())
        assert blank == [], f"These rows hold no description: {', '.join(blank)}."


class TestEveryOperationLandsInANamedGroup:
    """An operation outside every range falls into the generic Other group."""

    def test_no_eligible_option_falls_outside_the_ranges(self) -> None:
        """A named group helps an operator find the operation they need."""
        homeless = []
        for option in eligible_options():
            number = int(float(option.replace("a", ".1")))
            if not any(low <= number <= high for low, high, _ in CATEGORY_RANGES):
                homeless.append(option)
        assert sorted(homeless, key=float) == [], (
            f"These safe operations land in the generic group: {', '.join(sorted(homeless, key=float))}. "
            "Add a range to CATEGORY_RANGES."
        )

    def test_the_ranges_never_overlap(self) -> None:
        """Two ranges that cover one number make the group order decide the name."""
        overlaps = []
        ordered = sorted(CATEGORY_RANGES, key=lambda row: row[0])
        for first, second in zip(ordered, ordered[1:], strict=False):
            if second[0] <= first[1]:
                overlaps.append(f"{first[2]} and {second[2]}")
        assert overlaps == [], f"These category ranges overlap: {'; '.join(overlaps)}."
