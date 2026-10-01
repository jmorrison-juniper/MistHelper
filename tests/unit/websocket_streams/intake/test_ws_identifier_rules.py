"""Tests for WebSocket identifier rules."""

from src.websocket_streams.intake.identifiers import IdentifierRules  # Import the identifier checker.


def test_identifier_rules_accept_valid_values() -> None:
    """The identifier rules accept each valid supported shape."""
    assert IdentifierRules.is_uuid("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")  # A Mist UUID is accepted.
    assert IdentifierRules.is_mac("aa:bb:cc:dd:ee:ff")  # A separated MAC address is accepted.
    assert IdentifierRules.is_host("switch.example.com")  # A DNS host is accepted.
    assert IdentifierRules.is_ip("192.0.2.1")  # An IPv4 address is accepted.
    assert IdentifierRules.is_prefix("192.0.2.0/24")  # A CIDR prefix is accepted.
    assert IdentifierRules.is_port("ge-0/0/1.0")  # A Junos port is accepted.
    assert IdentifierRules.is_name("blue network")  # A plain name is accepted.
    assert IdentifierRules.is_filter("udp port 67 or udp port 68")  # A safe filter is accepted.


def test_identifier_rules_reject_invalid_values() -> None:
    """The identifier rules reject malformed values."""
    assert not IdentifierRules.is_uuid("not-a-uuid")  # A random string is not a UUID.
    assert not IdentifierRules.is_mac("zz:bb:cc:dd:ee:ff")  # A non-hex MAC is invalid.
    assert not IdentifierRules.is_host("bad host")  # DNS names cannot contain spaces.
    assert not IdentifierRules.is_ip("example.com")  # DNS text is not an IP address.
    assert not IdentifierRules.is_prefix("192.0.2.0")  # A network without a prefix is not accepted here.
    assert not IdentifierRules.is_port("ethernet1")  # Non-Junos port text is invalid.
    assert not IdentifierRules.is_name("bad/name")  # A slash is not allowed in a plain name.
    assert not IdentifierRules.is_filter("x" * 257)  # A filter above the limit is invalid.
