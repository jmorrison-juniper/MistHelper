"""Tests for WebSocket field value checks."""

import pytest  # Pytest checks refusal paths.

from src.websocket_streams.catalog.model import FieldKind, FieldSpec  # Import field records.
from src.websocket_streams.intake.fields import FieldValueChecker, StreamRequestError  # Import the checker under test.


def test_field_checker_converts_valid_values() -> None:
    """The field checker returns JSON-safe checked values."""
    checker = FieldValueChecker()  # Build the field checker.
    assert (
        checker.check(FieldSpec("count", "Count", FieldKind.INTEGER, minimum=1, maximum=100), "5") == 5
    )  # Integer text becomes an int.
    assert (
        checker.check(FieldSpec("enabled", "Enabled", FieldKind.BOOLEAN), "yes") is True
    )  # Boolean text becomes a bool.
    assert (
        checker.check(FieldSpec("mac", "MAC", FieldKind.MAC), "AA:BB:CC:DD:EE:FF") == "aabbccddeeff"
    )  # MAC text becomes compact lowercase.
    assert checker.check(FieldSpec("ports", "Ports", FieldKind.PORT_LIST), "ge-0/0/1, ge-0/0/2") == [
        "ge-0/0/1",
        "ge-0/0/2",
    ]  # Comma text becomes a list.
    assert checker.check(FieldSpec("vlan", "VLAN", FieldKind.VLAN), "20") == "20"  # VLAN values stay text.


def test_field_checker_omits_empty_optional_value() -> None:
    """An empty optional field returns None."""
    checker = FieldValueChecker()  # Build the field checker.
    assert checker.check(FieldSpec("vrf", "VRF", FieldKind.NAME), "") is None  # Empty optional text is absent.


def test_field_checker_refuses_bad_values() -> None:
    """The field checker raises bad_request for invalid values."""
    checker = FieldValueChecker()  # Build the field checker.
    with pytest.raises(StreamRequestError) as error:  # Capture the refusal.
        checker.check(
            FieldSpec("count", "Count", FieldKind.INTEGER, minimum=1, maximum=10), "50"
        )  # Send an out-of-range value.
    assert error.value.code == "bad_request" and error.value.extra["field"] == "count"  # The refusal names the field.


def test_field_checker_refuses_duplicate_list_values() -> None:
    """A list field must hold unique values."""
    checker = FieldValueChecker()  # Build the field checker.
    with pytest.raises(StreamRequestError):  # Capture the refusal.
        checker.check(FieldSpec("ports", "Ports", FieldKind.PORT_LIST), ["ge-0/0/1", "ge-0/0/1"])  # Send duplicates.


def test_field_checker_refuses_bad_boolean_and_list_shape() -> None:
    """The field checker refuses bad booleans and non-list values."""
    checker = FieldValueChecker()  # Build the field checker.
    with pytest.raises(StreamRequestError):  # Capture the boolean refusal.
        checker.check(FieldSpec("enabled", "Enabled", FieldKind.BOOLEAN), "maybe")  # Send invalid boolean text.
    with pytest.raises(StreamRequestError):  # Capture the list refusal.
        checker.check(FieldSpec("ports", "Ports", FieldKind.PORT_LIST), 42)  # Send a non-list value.


def test_field_checker_refuses_bad_list_item_and_choice() -> None:
    """The field checker refuses bad list items and bad choices."""
    checker = FieldValueChecker()  # Build the field checker.
    with pytest.raises(StreamRequestError):  # Capture the list item refusal.
        checker.check(FieldSpec("ports", "Ports", FieldKind.PORT_LIST), ["bad"])  # Send an invalid port item.
    with pytest.raises(StreamRequestError):  # Capture the choice refusal.
        checker.check(
            FieldSpec("node", "Node", FieldKind.CHOICE, choices=("node0", "node1")), "node2"
        )  # Send an invalid choice.


@pytest.mark.parametrize(
    ("code", "status"),
    [
        ("not_terminal", 409),  # A session with no terminal refuses the terminal routes.
        ("read_only", 409),  # A screen command takes no input.
        ("input_full", 409),  # The queue before the first output is full.
        ("too_large", 413),  # One input request holds too much text.
        ("rate_limited", 429),  # The session received too many requests in one second.
    ],
)
def test_terminal_refusal_codes_map_to_contract_status(code: str, status: int) -> None:
    """Each terminal refusal code sends the HTTP status of the terminal contract (issue #3671)."""
    refusal = StreamRequestError(code, "The terminal refused the request.")  # Build one terminal refusal.
    assert refusal.status == status  # The blueprint sends the contract status.
    assert refusal.to_payload()["code"] == code  # The page reads the same code from the JSON answer.


def test_unknown_refusal_code_stays_a_bad_request() -> None:
    """A code outside the table keeps the 400 status, so a new code cannot pass silently."""
    refusal = StreamRequestError("no_such_code", "An unknown refusal.")  # Build a refusal with an unknown code.
    assert refusal.status == 400  # The default status is a bad request.
