"""Limit logs from listing operations and retain evidence of run validation."""

import logging
from collections.abc import Iterator
from copy import deepcopy
from dataclasses import replace
from unittest.mock import Mock

import pytest

from src.foundation.support.utils.menu_entry import MenuEntry
from src.foundation.support.utils.operation_registry import OperationRegistry
from web_portal.menu_registry import build_static_menu_actions
from web_portal.services.operation import OperationExecutor

PORTAL_LOGGER = OperationExecutor.__module__
REFUSED_MENU_NUMBERS = ("0", "14", "102", "151", "154", "x1", "999")


@pytest.fixture
def executor() -> Iterator[OperationExecutor]:
    """Use real menu entries without an API session or executed handler."""
    actions = {number: replace(entry, handler=lambda: None) for number, entry in build_static_menu_actions().items()}
    actions.update(
        {number: MenuEntry(number, lambda: None, f"Operation {number}", "safe") for number in REFUSED_MENU_NUMBERS}
    )  # Misleading row metadata must not override the authoritative registry.
    built = OperationExecutor(actions, None, None, None)
    try:
        yield built
    finally:
        built.shutdown()  # Release the pool even when a record assertion fails.


class TestCategoryListLogging:
    """Prove that INFO volume stays constant and list evidence stays complete."""

    @pytest.mark.parametrize(
        ("listed_count", "refused_count"),
        [(0, 0), (1, 0), (12, 0), (70, 0), (1, 7), (12, 7), (70, 7), (0, 7)],
    )
    def test_listing_records_have_fixed_info_and_exact_counts(
        self, executor: OperationExecutor, caplog: pytest.LogCaptureFixture, listed_count: int, refused_count: int
    ) -> None:
        """Each menu size must produce exactly one INFO record and exact counts."""
        safe_numbers = OperationRegistry.safe_options(executor._menu_actions)[:listed_count]
        numbers = safe_numbers + list(REFUSED_MENU_NUMBERS[:refused_count])
        actions = {number: executor._menu_actions[number] for number in numbers}
        with caplog.at_level(logging.DEBUG, logger=PORTAL_LOGGER):
            categories = executor.build_category_list(actions)
        records = [record for record in caplog.record_tuples if record[0] == PORTAL_LOGGER]
        assert sum(len(category["operations"]) for category in categories) == listed_count
        assert [record for record in records if record[1] == logging.INFO] == [
            (PORTAL_LOGGER, logging.INFO, "Portal builds the operation category list")
        ]
        assert [record for record in records if record[2].startswith("Portal operation list:")] == [
            (PORTAL_LOGGER, logging.DEBUG, f"Portal operation list: listed={listed_count} refused={refused_count}")
        ]
        assert sum(record[2].startswith("Portal verdict for operation ") for record in records) == len(actions)

    @pytest.mark.parametrize("listed_count", [0, 1, 70])
    def test_info_level_listing_emits_no_row_records(
        self, executor: OperationExecutor, caplog: pytest.LogCaptureFixture, listed_count: int
    ) -> None:
        """At INFO, listing must report the action without any record for each row."""
        numbers = OperationRegistry.safe_options(executor._menu_actions)[:listed_count]
        actions = {number: executor._menu_actions[number] for number in numbers}
        with caplog.at_level(logging.INFO, logger=PORTAL_LOGGER):
            executor.build_category_list(actions)
        assert [record for record in caplog.record_tuples if record[0] == PORTAL_LOGGER] == [
            (PORTAL_LOGGER, logging.INFO, "Portal builds the operation category list")
        ]

    def test_category_structure_titles_parameters_and_order_stay_unchanged(self, executor: OperationExecutor) -> None:
        """The logging repair must preserve the full returned list and parameter metadata."""
        numbers = ("60", "11", "9", "3", "2", "10", "14", "154", "x1")
        actions = {number: executor._menu_actions[number] for number in numbers}
        parameters_before = deepcopy(executor.get_operation_parameters("60"))
        expected_rows = (
            ("Core Organization", ("2", "3"), "non_interactive"),
            ("Organization Exports", ("9", "10", "11"), "non_interactive"),
            ("Site Config & Monitoring", ("60",), "interactive"),
        )
        expected = [
            {
                "name": name,
                "operations": [
                    dict(menu_number=number, description=actions[number].title, category=operation_category)
                    for number in ordered_numbers
                ],
            }
            for name, ordered_numbers, operation_category in expected_rows
        ]
        assert executor.build_category_list(actions) == expected
        assert executor.get_operation_parameters("60") == parameters_before

    def test_unregistered_rows_keep_registry_warnings(
        self, executor: OperationExecutor, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A smaller INFO log must not remove warnings for unregistered rows."""
        actions = {number: executor._menu_actions[number] for number in ("x1", "999")}
        with caplog.at_level(logging.DEBUG, logger=PORTAL_LOGGER):
            categories = executor.build_category_list(actions)
        assert categories == []
        assert [record for record in caplog.record_tuples if record[1] == logging.WARNING] == [
            (
                OperationRegistry.__module__,
                logging.WARNING,
                f"OperationRegistry: option {number} not registered, failing closed as 'unregistered' (not run)",
            )
            for number in ("x1", "999")
        ]

    def test_registry_failure_does_not_report_a_completed_list(
        self, executor: OperationExecutor, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A registry failure must propagate instead of reporting an empty successful list."""
        monkeypatch.setattr(OperationRegistry, "skip_category", Mock(side_effect=RuntimeError("Registry unavailable")))
        with caplog.at_level(logging.DEBUG, logger=PORTAL_LOGGER):
            with pytest.raises(RuntimeError, match="Registry unavailable"):
                executor.build_category_list({"11": executor._menu_actions["11"]})
        assert [record for record in caplog.record_tuples if record[0] == PORTAL_LOGGER] == [
            (PORTAL_LOGGER, logging.INFO, "Portal builds the operation category list")
        ]


class TestOperationValidationLogging:
    """Keep gate evidence and exact errors for actual-run validation."""

    @pytest.mark.parametrize(
        "gate_case",
        [
            ("11", "safe", True),
            ("60", "interactive_safe", True),
            ("0", "interactive", False),
            ("14", "resource_intensive", False),
            ("102", "websocket", False),
            ("151", "continuous_loop", False),
            ("154", "destructive", False),
            ("x1", "unregistered", False),
            ("999", "unregistered", False),
        ],
    )
    def test_validation_keeps_gate_and_verdict(
        self,
        executor: OperationExecutor,
        caplog: pytest.LogCaptureFixture,
        gate_case: tuple[str, str, bool],
    ) -> None:
        """Allowed and refused operations must retain exactly one INFO record for the gate."""
        menu_number, category, allowed = gate_case
        with caplog.at_level(logging.DEBUG, logger=PORTAL_LOGGER):
            result = executor._validate_operation(menu_number)
        expected_error = {
            "error": (
                f"Menu number {menu_number} is not a safe operation, so the portal cannot run it. "
                f"The safety category is '{category}'. Connect over SSH to run this operation."
            )
        }
        assert result == (None if allowed else expected_error)
        verdict = f"Portal verdict for operation {menu_number}: category={category} allowed={allowed}"
        assert [record for record in caplog.record_tuples if record[0] == PORTAL_LOGGER] == [
            (PORTAL_LOGGER, logging.INFO, f"Portal checks whether it may run operation {menu_number}"),
            (PORTAL_LOGGER, logging.DEBUG, verdict),
        ]

    def test_absent_operation_keeps_not_found_error_and_gate(
        self, executor: OperationExecutor, caplog: pytest.LogCaptureFixture
    ) -> None:
        """An absent operation must retain its exact error and gate INFO record."""
        with caplog.at_level(logging.DEBUG, logger=PORTAL_LOGGER):
            result = executor._validate_operation("missing")
        assert result == {"error": "Operation missing not found"}
        assert [record for record in caplog.record_tuples if record[0] == PORTAL_LOGGER] == [
            (PORTAL_LOGGER, logging.INFO, "Portal checks whether it may run operation missing")
        ]

    def test_missing_handler_keeps_authentication_error_and_gate(
        self, executor: OperationExecutor, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A safe operation without a handler must retain its authentication error."""
        executor._menu_actions["11"] = replace(executor._menu_actions["11"], handler=None)
        with caplog.at_level(logging.DEBUG, logger=PORTAL_LOGGER):
            result = executor._validate_operation("11")
        assert result == {"error": "API not authenticated. Connect via SSH to run operations."}
        assert [record for record in caplog.record_tuples if record[0] == PORTAL_LOGGER] == [
            (PORTAL_LOGGER, logging.INFO, "Portal checks whether it may run operation 11"),
            (PORTAL_LOGGER, logging.DEBUG, "Portal verdict for operation 11: category=safe allowed=True"),
        ]

    def test_registry_failure_keeps_gate_and_propagates(
        self, executor: OperationExecutor, caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """An unexpected registry error must not disappear after the INFO record moves."""
        monkeypatch.setattr(OperationRegistry, "skip_category", Mock(side_effect=RuntimeError("Registry unavailable")))
        with caplog.at_level(logging.DEBUG, logger=PORTAL_LOGGER):
            with pytest.raises(RuntimeError, match="Registry unavailable"):
                executor._validate_operation("11")
        assert [record for record in caplog.record_tuples if record[0] == PORTAL_LOGGER] == [
            (PORTAL_LOGGER, logging.INFO, "Portal checks whether it may run operation 11")
        ]

    def test_prior_listing_does_not_silence_a_refused_run(
        self, executor: OperationExecutor, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Listing must not change the shared logger level or hide the next run gate."""
        with caplog.at_level(logging.DEBUG, logger=PORTAL_LOGGER):
            executor.build_category_list({"11": executor._menu_actions["11"], "14": executor._menu_actions["14"]})
            caplog.clear()
            result = executor.start_operation("14", {})
        assert result == {
            "error": (
                "Menu number 14 is not a safe operation, so the portal cannot run it. "
                "The safety category is 'resource_intensive'. Connect over SSH to run this operation."
            )
        }
        assert [record for record in caplog.record_tuples if record[0] == PORTAL_LOGGER] == [
            (PORTAL_LOGGER, logging.INFO, "Portal checks whether it may run operation 14"),
            (
                PORTAL_LOGGER,
                logging.DEBUG,
                "Portal verdict for operation 14: category=resource_intensive allowed=False",
            ),
        ]
        assert executor.get_active_runs() == []
