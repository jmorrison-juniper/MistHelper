"""Verify the independent guest review projection without a Mist connection."""

import json
import logging

import pytest

from src.interfaces.portals.guest_authorizations import GuestAuthorizationReadModel


@pytest.mark.parametrize("mac", ["02aabbccddee", "02:aa:bb:cc:dd:ee", "02-AA-BB-CC-DD-EE"])
def test_public_projection_excludes_private_fields(mac: str, caplog: pytest.LogCaptureFixture) -> None:
    """Keep only review fields and mask the identifier before serialization."""
    record = {  # Use fictional private values to detect accidental disclosure.
        "mac": mac,
        "authorized": True,
        "authorized_expiring_time": 1893456000,
        "name": "Fictional guest",
        "email": "fictional@example.invalid",
        "access_code_email": "code@example.invalid",
        "field1": "private detail",
    }
    original = record.copy()  # Detect changes to caller-owned data.
    with caplog.at_level(logging.DEBUG):  # Inspect the complete projection log.
        result = GuestAuthorizationReadModel.project(record)
    assert result == {  # An exact shape prevents new private fields from passing.
        "masked_mac": "xx:xx:xx:xx:dd:ee",
        "authorized": True,
        "expires_at": "2030-01-01T00:00:00+00:00",
    }
    assert record == original  # The projection must not change an authorization.
    serialized = json.dumps(result) + caplog.text  # Check both disclosure surfaces.
    for private_value in (
        mac,
        "Fictional guest",
        "fictional@example.invalid",
        "code@example.invalid",
        "private detail",
    ):
        assert private_value not in serialized  # Private values must not escape.


@pytest.mark.parametrize("authorized", [True, False, None])
def test_missing_values_remain_unknown(authorized: bool | None) -> None:
    """Do not infer authorization or expiry from missing cloud values."""
    result = GuestAuthorizationReadModel.project({"mac": "02aabbccddee", "authorized": authorized})
    assert result["authorized"] is authorized  # Preserve false and unknown distinctly.
    assert result["expires_at"] is None  # An absent time is not an invented expiry.
    missing = GuestAuthorizationReadModel.project({"mac": "02aabbccddee"})
    assert missing["authorized"] is None  # Absence must not grant access in the read model.


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("mac", None),
        ("mac", "02:aa-bb:cc:dd:ee"),
        ("mac", "02aabbccddee<script>"),
        ("mac", 123456789012),
        ("authorized", "false"),
        ("authorized", 1),
        ("authorized_expiring_time", True),
        ("authorized_expiring_time", "1893456000"),
        ("authorized_expiring_time", float("nan")),
        ("authorized_expiring_time", float("inf")),
        ("authorized_expiring_time", -1),
        ("authorized_expiring_time", 10**100),
    ],
)
def test_invalid_fields_fail_without_payload_logging(
    field: str, value: object, caplog: pytest.LogCaptureFixture
) -> None:
    """Reject malformed fields without including their contents in an error."""
    record = {"mac": "02aabbccddee", field: value, "email": "private@example.invalid"}  # Keep test data fictional.
    with caplog.at_level(logging.DEBUG), pytest.raises(ValueError) as error:
        GuestAuthorizationReadModel.project(record)
    assert str(error.value).startswith("Invalid guest authorization ")  # Require an actionable error category.
    assert "private@example.invalid" not in str(error.value) + caplog.text  # Never log the source record.
    assert "02aabbccddee" not in caplog.text  # Never log the unmasked identifier.
    assert any(entry.levelno == logging.ERROR for entry in caplog.records)  # A rejection must be observable.


@pytest.mark.parametrize("value", [None, [], "private@example.invalid"])
def test_invalid_records_fail(value: object, caplog: pytest.LogCaptureFixture) -> None:
    """Reject a non-record input without echoing its content."""
    with pytest.raises(ValueError, match="Invalid guest authorization record"):
        GuestAuthorizationReadModel.project(value)
    assert "private@example.invalid" not in caplog.text  # Keep rejected input private.


def test_projection_is_safe_for_existing_template_and_json_consumers() -> None:
    """Integrate the projection with existing libraries without a route or session."""
    from flask import Flask, jsonify, render_template_string  # Use only an offline application context.

    application = Flask(__name__)  # This context exposes no server or guest route.
    with application.app_context():  # Serialization requires no credentials or API client.
        row = GuestAuthorizationReadModel.project({"mac": "02aabbccddee", "authorized": False})
        response = jsonify(row)  # Exercise Flask's actual JSON encoder.
        html = render_template_string("{{ row.masked_mac }} {{ row.authorized }}", row=row)
    assert response.get_json() == {"masked_mac": "xx:xx:xx:xx:dd:ee", "authorized": False, "expires_at": None}
    assert html == "xx:xx:xx:xx:dd:ee False"  # A consumer sees only the masked identifier.
    assert [rule.endpoint for rule in application.url_map.iter_rules()] == ["static"]  # No guest endpoint is installed.
