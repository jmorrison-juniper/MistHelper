"""Prove current WIP target metadata and presentation without changing safety gates."""

from collections.abc import Iterator
from copy import deepcopy
from dataclasses import replace
from unittest.mock import Mock

import pytest

from src.utils.operation_registry import OperationRegistry
from tests.support.wip_target_controls.browser import TargetAcceptance
from web_portal.menu_registry import build_static_menu_actions
from web_portal.services.operation import CATEGORY_OVERRIDES, OperationExecutor


@pytest.fixture
def executor() -> Iterator[OperationExecutor]:
    """Use the shipped menu titles and real parameter registry without a run."""
    built = OperationExecutor(build_static_menu_actions(), None, None, None)
    try:
        yield built
    finally:
        built.shutdown()


class TestRequiredTargetMetadata:
    """Each current row must match its actual prompt sequence."""

    def test_menu_63_has_the_required_switch_after_the_site(self, executor: OperationExecutor) -> None:
        """The original registry fails this exact two-answer decision."""
        metadata = executor.get_operation_parameters("63")
        assert metadata["category"] == "interactive"
        TargetAcceptance.require_switch(metadata["parameters"])
        assert [parameter["label"] for parameter in metadata["parameters"]] == ["Site", "Switch"]
        print("Checked 1 menu 63 row and 2 required target descriptors.")

    @pytest.mark.parametrize("number", ["64", "65"])
    def test_client_rows_keep_one_required_site(self, executor: OperationExecutor, number: str) -> None:
        """Do not duplicate controls that already exist."""
        metadata = executor.get_operation_parameters(number)
        assert metadata["parameters"] == [{"name": "site_id", "label": "Site", "param_type": "site", "required": True}]
        assert metadata["category"] == "interactive"

    def test_normal_row_keeps_its_original_scalar_metadata(self, executor: OperationExecutor) -> None:
        """Caution metadata must not add target controls or change ordinary categories."""
        metadata = executor.get_operation_parameters("11")
        assert metadata == {
            "menu_number": "11",
            "description": executor._menu_actions["11"].title,
            "category": "non_interactive",
            "parameters": [],
        }


class TestDisplayedCategoryCaution:
    """The displayed category supplies guidance, never execution permission."""

    def test_current_wip_rows_have_warning_metadata(self, executor: OperationExecutor) -> None:
        """Check all three current rows and one normal row."""
        actions = {number: executor._menu_actions[number] for number in ("63", "64", "65", "11")}
        categories = executor.build_category_list(actions)
        by_category = {category["name"]: category["operations"] for category in categories}
        assert set(by_category) == {"Organization Exports", "Work In Progress"}
        assert [row["menu_number"] for row in by_category["Work In Progress"]] == ["63", "64", "65"]
        for row in by_category["Work In Progress"]:
            TargetAcceptance.require_caution(row)
            assert row["category"] == "interactive"
        normal = by_category["Organization Exports"][0]
        assert normal == dict(menu_number="11", description=actions["11"].title, category="non_interactive")
        print("Checked 3 WIP rows, 3 caution properties, and 1 unchanged normal row.")

    def test_warning_follows_actual_category_overrides(
        self, executor: OperationExecutor, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A future category change must not leave a range-based warning behind."""
        monkeypatch.setitem(CATEGORY_OVERRIDES, 63, "Organization Exports")
        monkeypatch.setitem(CATEGORY_OVERRIDES, 11, "Work In Progress")
        actions = {number: executor._menu_actions[number] for number in ("63", "11")}
        categories = executor.build_category_list(actions)
        rows = {row["menu_number"]: row for category in categories for row in category["operations"]}
        assert "work_in_progress" not in rows["63"]
        TargetAcceptance.require_caution(rows["11"])
        assert rows["63"]["category"] == "interactive"
        assert rows["11"]["category"] == "non_interactive"


class TestCountedNegativeGuards:
    """Both acceptance decisions must fail with their required input removed."""

    def test_removing_the_switch_descriptor_fails_acceptance(self, executor: OperationExecutor) -> None:
        """The guard checks real metadata before its direct negative case."""
        parameters = deepcopy(executor.get_operation_parameters("63")["parameters"])
        TargetAcceptance.require_switch(parameters)
        parameters.pop()
        with pytest.raises(AssertionError, match="Checked 1 row and 1 descriptors"):
            TargetAcceptance.require_switch(parameters)
        assert [parameter["name"] for parameter in parameters] == ["site_id"]
        print("Checked 1 removed switch descriptor. The target acceptance guard failed.")

    def test_removing_warning_metadata_fails_acceptance(self, executor: OperationExecutor) -> None:
        """The exact WIP row is the guard input, without any network requirement."""
        categories = executor.build_category_list({"63": executor._menu_actions["63"]})
        row = deepcopy(categories[0]["operations"][0])
        TargetAcceptance.require_caution(row)
        assert row.pop("work_in_progress") is True
        with pytest.raises(AssertionError, match="Checked 1 WIP row"):
            TargetAcceptance.require_caution(row)
        assert row["menu_number"] == "63"
        print("Checked 1 removed caution property. The warning acceptance guard failed.")


class TestRegistrySafetyRemainsAuthoritative:
    """Misleading presentation flags must never make an unsafe operation runnable."""

    @pytest.mark.parametrize("number", ["0", "14", "102", "151", "154", "999", "x1"])
    def test_wip_metadata_does_not_admit_unsafe_rows(
        self, executor: OperationExecutor, monkeypatch: pytest.MonkeyPatch, number: str
    ) -> None:
        """The real start gate must refuse before any handler or worker runs."""
        handler = Mock(side_effect=AssertionError("An unsafe handler must never execute."))
        entry = replace(executor._menu_actions["11"], menu_id=number, handler=handler)
        executor._menu_actions[number] = entry
        if number.isdigit():
            monkeypatch.setitem(CATEGORY_OVERRIDES, int(number), "Work In Progress")
        category = OperationRegistry.skip_category(number)
        result = executor.start_operation(number, {"work_in_progress": True, "input_answers": ["Lab Site"]})
        assert result == {
            "error": (
                f"Menu number {number} is not a safe operation, so the portal cannot run it. "
                f"The safety category is '{category}'. Connect over SSH to run this operation."
            )
        }
        assert executor.build_category_list({number: entry}) == []
        assert handler.call_count == 0
        assert executor._runs == {}
