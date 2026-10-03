"""Tests for WebSocket identifier rules."""

import json  # Structured intake logs must parse as JSON.
import logging  # Caplog captures the shared standard logging target.

import pytest  # The logging test uses the typed capture fixture.

from src.websocket_streams.intake.identifiers.identity_rules import IdentityIdentifierRules  # UUID and MAC checks.
from src.websocket_streams.intake.identifiers.network_rules import NetworkIdentifierRules  # Host and network checks.
from src.websocket_streams.intake.identifiers.text_rules import TextIdentifierRules  # Port and plain text checks.


def test_identifier_rules_accept_valid_values() -> None:
    """The identifier rules accept each valid supported shape."""
    assert IdentityIdentifierRules.is_uuid("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")  # A Mist UUID is accepted.
    assert IdentityIdentifierRules.is_mac("aa:bb:cc:dd:ee:ff")  # A separated MAC address is accepted.
    assert NetworkIdentifierRules.is_host("switch.example.com")  # A DNS host is accepted.
    assert NetworkIdentifierRules.is_ip("192.0.2.1")  # An IPv4 address is accepted.
    assert NetworkIdentifierRules.is_prefix("192.0.2.0/24")  # A CIDR prefix is accepted.
    assert TextIdentifierRules.is_port("ge-0/0/1.0")  # A Junos port is accepted.
    assert TextIdentifierRules.is_name("blue network")  # A plain name is accepted.
    assert TextIdentifierRules.is_filter("udp port 67 or udp port 68")  # A safe filter is accepted.


def test_identifier_rules_reject_invalid_values() -> None:
    """The identifier rules reject malformed values."""
    assert not IdentityIdentifierRules.is_uuid("not-a-uuid")  # A random string is not a UUID.
    assert not IdentityIdentifierRules.is_mac("zz:bb:cc:dd:ee:ff")  # A non-hex MAC is invalid.
    assert not NetworkIdentifierRules.is_host("bad host")  # DNS names cannot contain spaces.
    assert not NetworkIdentifierRules.is_ip("example.com")  # DNS text is not an IP address.
    assert not NetworkIdentifierRules.is_prefix("192.0.2.0")  # A network without a prefix is not accepted here.
    assert not TextIdentifierRules.is_port("ethernet1")  # Non-Junos port text is invalid.
    assert not TextIdentifierRules.is_name("bad/name")  # A slash is not allowed in a plain name.
    assert not TextIdentifierRules.is_filter("x" * 257)  # A filter above the limit is invalid.


def test_identifier_logs_use_bounded_json_without_identifier_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Identifier checks log safe structured metadata only."""
    identifier = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"  # Use recognizable text for the leak check.
    logger_name = "src.websocket_streams.intake.identifiers.identity_rules"  # Capture the production logger.
    with caplog.at_level(logging.DEBUG, logger=logger_name):  # Capture one identifier check.
        assert IdentityIdentifierRules.is_uuid(identifier)  # Run the real structured logging path.
    record = json.loads(caplog.records[-1].message)  # Parse the exact emitted JSON record.
    assert identifier not in caplog.records[-1].message  # Never log an identifier value.
    assert record == {"detail": "uuid", "event": "intake_identifier_checked", "status": True}  # Safe fields.
