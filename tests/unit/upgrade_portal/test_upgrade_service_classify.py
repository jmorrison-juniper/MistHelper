"""Unit tests for ``classify_gateway`` in ``src/firmware/upgrade_service.py``.

Why:
    A Junos gateway and a session smart router need different cloud calls, so a
    wrong family sends the wrong firmware to real hardware. The one existing
    discriminator is ``_is_ssr_inventory_row`` at
    ``src/firmware/firmware_manager.py:2291``. That predicate is a method of a
    class, and its module binds four mutable globals at lines 34 to 37. These
    tests call the legacy predicate directly and prove that ``classify_gateway``
    returns the same family for every row, and that it reads none of that
    module state.

    The file ``tests/unit/upgrade_portal/test_upgrade_service.py`` already
    proves the four literal rules of the task at its class
    ``TestClassifyGateway``. No test below repeats one of those five cases.
"""

from __future__ import annotations

import inspect
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import pytest

from src.firmware import firmware_manager, upgrade_service
from src.firmware.firmware_manager import FirmwareManager

# Every row that the legacy predicate can read without an error, with the family
# that the legacy predicate reports. The new function must agree on each row.
CANONICAL_ROWS: tuple[tuple[dict[str, Any], bool], ...] = (
    ({"type": "ssr", "model": ""}, True),
    ({"type": "gateway", "model": "SSR120"}, True),
    ({"type": "gateway", "model": "SSR-100"}, True),
    ({"type": "gateway", "model": "128T-Router"}, True),
    ({"type": "gateway", "model": " SSR120 "}, True),
    ({"type": "gateway", "model": "SRX345"}, False),
    ({"type": "switch", "model": "EX4100-48P"}, False),
    ({"type": "ap", "model": "AP45"}, False),
    ({"type": "", "model": ""}, False),
)

# Rows that the legacy predicate reports as another family. The legacy predicate
# compares the type value for equality, and it reads the model with a test that
# obeys the case. The new function trims each value and folds the case first.
WIDER_ROWS: tuple[dict[str, Any], ...] = (
    {"type": "SSR", "model": ""},
    {"type": " ssr ", "model": ""},
    {"type": "gateway", "model": "ssr120"},
    {"type": "gateway", "model": "128t-1000"},
)


def legacy_family(row: dict[str, Any]) -> bool:
    """Return the answer of the legacy predicate for one inventory row.

    Why:
        The legacy predicate reads no member of its object, so a call through
        the class needs no built manager and touches no module global. The
        stand-in object below fills the first parameter and nothing else.

    Args:
        row: One inventory row with a type value and a model value.

    Returns:
        True when the legacy predicate reports a session smart router.
    """
    return bool(FirmwareManager._is_ssr_inventory_row(object(), row))


class TestAgreementWithTheLegacyPredicate:
    """Tests that compare the new function against the one existing discriminator."""

    @pytest.mark.parametrize(("row", "expected"), CANONICAL_ROWS)
    def test_returns_the_family_that_the_legacy_predicate_reports(self, row: dict[str, Any], expected: bool) -> None:
        """The new function repeats the legacy test for every canonical row.

        Args:
            row: One inventory row.
            expected: True when the legacy predicate reports a session smart router.
        """
        assert legacy_family(row) is expected
        is_session_router = upgrade_service.classify_gateway(row) is upgrade_service.GatewayFamily.SSR
        assert is_session_router is expected

    @pytest.mark.parametrize("row", WIDER_ROWS)
    def test_catches_a_row_that_the_legacy_predicate_misses(self, row: dict[str, Any]) -> None:
        """The new function folds the case and trims the value, so it catches more rows.

        The legacy predicate compares the raw text, so it reports another family
        for each row below. The new function never reports another family for a
        row that the legacy predicate accepts, so the change adds devices and
        removes none.

        Args:
            row: One inventory row that the legacy predicate misses.
        """
        assert legacy_family(row) is False
        assert upgrade_service.classify_gateway(row) is upgrade_service.GatewayFamily.SSR

    def test_reads_a_model_value_of_none_where_the_legacy_predicate_raises(self) -> None:
        """A model value of ``None`` returns the Junos family instead of an error.

        The legacy predicate applies the ``in`` operator to the raw value, so a
        model value of ``None`` raises. The portal reads a cloud record that may
        hold that value, so the new function converts the value to text first.
        """
        row: dict[str, Any] = {"type": "gateway", "model": None}
        with pytest.raises(TypeError):
            legacy_family(row)
        assert upgrade_service.classify_gateway(row) is upgrade_service.GatewayFamily.JUNOS

    def test_reads_a_model_value_that_is_a_number(self) -> None:
        """A numeric model value returns the Junos family."""
        assert upgrade_service.classify_gateway({"type": 7, "model": 128}) is upgrade_service.GatewayFamily.JUNOS


class TestFreedomFromModuleState:
    """Tests that prove the new function carries none of the legacy module state."""

    def test_needs_no_object_where_the_legacy_predicate_needs_one(self) -> None:
        """The legacy predicate is a method, and the new function is a plain function.

        A method belongs to a class, and that class binds the four globals of
        its module during construction. The new function takes one device record
        and nothing else, so a caller needs no manager object.
        """
        assert list(inspect.signature(upgrade_service.classify_gateway).parameters) == ["device"]
        assert list(inspect.signature(FirmwareManager._is_ssr_inventory_row).parameters) == ["self", "gw"]

    def test_returns_the_same_family_after_every_legacy_global_changes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """A change to the four globals of the legacy module changes no answer.

        Args:
            monkeypatch: The pytest patch helper.
        """
        row = {"type": "gateway", "model": "SSR120"}
        before = upgrade_service.classify_gateway(row)
        monkeypatch.setattr(firmware_manager, "apisession", object())
        monkeypatch.setattr(firmware_manager, "org_id", "another-org")
        monkeypatch.setattr(firmware_manager, "msp_privileges", [{"scope": "org"}])
        monkeypatch.setattr(firmware_manager, "PROGRESS_EMITTER", object())
        after = upgrade_service.classify_gateway(row)
        assert before is upgrade_service.GatewayFamily.SSR
        assert after is before

    def test_returns_the_same_family_from_many_threads(self) -> None:
        """Several threads may classify at once, because the function holds no state."""
        rows = [row for row, _ in CANONICAL_ROWS] * 8
        expected = [
            upgrade_service.GatewayFamily.SSR if is_session_router else upgrade_service.GatewayFamily.JUNOS
            for _, is_session_router in CANONICAL_ROWS
        ] * 8
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(upgrade_service.classify_gateway, rows))
        assert results == expected

    def test_returns_the_same_family_whatever_the_call_order(self) -> None:
        """One call changes no later call, because the function keeps no history."""
        session_router = {"type": "gateway", "model": "SSR120"}
        junos = {"type": "gateway", "model": "SRX345"}
        forward = [upgrade_service.classify_gateway(device) for device in (session_router, junos, session_router)]
        backward = [upgrade_service.classify_gateway(device) for device in (junos, session_router, junos)]
        assert forward == [
            upgrade_service.GatewayFamily.SSR,
            upgrade_service.GatewayFamily.JUNOS,
            upgrade_service.GatewayFamily.SSR,
        ]
        assert backward == [
            upgrade_service.GatewayFamily.JUNOS,
            upgrade_service.GatewayFamily.SSR,
            upgrade_service.GatewayFamily.JUNOS,
        ]


class TestDiscriminatorReach:
    """Tests for the values that decide the family."""

    def test_lets_the_model_value_decide_for_any_device_type(self) -> None:
        """A model that names a session smart router wins over the type value."""
        family = upgrade_service.classify_gateway({"type": "switch", "model": "SSR120"})
        assert family is upgrade_service.GatewayFamily.SSR

    def test_reports_the_junos_family_for_a_gateway_with_no_model(self) -> None:
        """A gateway with a type value alone stays in the Junos family."""
        assert upgrade_service.classify_gateway({"type": "gateway"}) is upgrade_service.GatewayFamily.JUNOS

    def test_returns_a_member_whose_value_travels_through_json(self) -> None:
        """The family value is plain text, so a browser reads it with no conversion."""
        assert upgrade_service.classify_gateway({"type": "ssr"}).value == "ssr"
        assert upgrade_service.classify_gateway({"type": "gateway"}).value == "junos"
