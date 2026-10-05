"""Verify operation-scoped client assistance metadata."""

import pytest

from src.mist.realtime.websocket_streams.catalog.model import FieldKind, FieldSpec
from src.mist.realtime.websocket_streams.catalog.utilities.utility_fields import UtilityFieldFactory


@pytest.mark.parametrize(
    ("family", "function_name", "parameter_name", "expected"),
    [
        ("ex", "releaseDhcpLeases", "macs", "multiple"),
        ("srx", "releaseDhcpLeases", "macs", "manual"),
        ("ssr", "releaseDhcpLeases", "macs", "manual"),
        ("ex", "retrieveMacTable", "mac_address", "single"),
        ("ap", "releaseDhcpLeases", "macs", None),
    ],
)
def test_client_picker_modes_are_operation_scoped(
    family: str, function_name: str, parameter_name: str, expected: str | None
) -> None:
    """Only the reviewed operation and field combinations receive client modes."""
    assert UtilityFieldFactory.client_picker_mode(family, function_name, parameter_name) == expected


def test_client_picker_metadata_does_not_change_sdk_field_name() -> None:
    """Client assistance is additive to the optional SDK field contract."""
    field = FieldSpec("macs", "MAC addresses", FieldKind.MAC_LIST, client_picker="multiple")
    payload = field.to_payload()
    assert payload["name"] == "macs"
    assert payload["required"] is False
    assert payload["client_picker"] == "multiple"
