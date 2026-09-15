"""Storage privacy tests for the performance recorder."""

from __future__ import annotations  # Keep annotations lazy during test collection.

from pathlib import Path  # Build JSON Lines paths without hardcoded separators.

from src.utils.performance import EventSource, Recorder, RecorderSettings  # Build one isolated recorder per test.


def _stored_output(tmp_path: Path, forbidden_value: str) -> str:
    """Return the JSON Lines output for one adversarial label."""
    recorder = Recorder(RecorderSettings(level="base"))  # Enable the basic sink for this storage test.
    source = EventSource(file=forbidden_value, symbol="execute", class_name="ApiFetcher")  # Try to leak through source.
    with recorder.span(source, family="operation") as span:  # Emit one event through the normal privacy path.
        span.label("operation", forbidden_value)  # Try to leak through an allowlisted label key.
        span.label("route", forbidden_value)  # Try to leak through a route label.
        span.count("items_total", 4)  # Add work size without private data.
    target = tmp_path / "data" / "performance" / "events.jsonl"  # Keep the test output under a data directory.
    recorder.sink.flush_to(target)  # Persist the line so the assertion reads stored output.
    return target.read_text(encoding="utf-8")  # Return the exact stored JSON Lines content.


def test_storage_does_not_contain_a_secret(tmp_path: Path) -> None:
    """A secret value does not reach the JSON Lines output."""
    output = _stored_output(tmp_path, "password=CorrectHorseBatteryStaple")  # Store an adversarial secret label.
    assert "CorrectHorseBatteryStaple" not in output  # Prove the secret content did not reach disk.


def test_storage_does_not_contain_personal_data(tmp_path: Path) -> None:
    """A personal data value does not reach the JSON Lines output."""
    output = _stored_output(tmp_path, "alice.operator@example.com")  # Store an adversarial email label.
    assert "alice.operator@example.com" not in output  # Prove the personal data did not reach disk.


def test_storage_does_not_contain_a_raw_path(tmp_path: Path) -> None:
    """A raw file path does not reach the JSON Lines output."""
    raw_path = "C:\\Users\\jmorrison\\data\\capture.json"  # Use a Windows path with a user folder.
    output = _stored_output(tmp_path, raw_path)  # Store an adversarial path label.
    assert "jmorrison" not in output  # Prove the user path segment did not reach disk.


def test_storage_does_not_contain_a_url(tmp_path: Path) -> None:
    """A URL does not reach the JSON Lines output."""
    url = "https://api.mist.com/api/v1/orgs?token=abcdef"  # Use a URL with a token query.
    output = _stored_output(tmp_path, url)  # Store an adversarial URL label.
    assert "api.mist.com" not in output  # Prove the host and path did not reach disk.


def test_storage_does_not_contain_sql_text(tmp_path: Path) -> None:
    """SQL text does not reach the JSON Lines output."""
    sql_text = "SELECT password FROM users WHERE email='alice@example.com'"  # Use SQL with private columns.
    output = _stored_output(tmp_path, sql_text)  # Store an adversarial SQL label.
    assert "SELECT password" not in output  # Prove the SQL text did not reach disk.


def test_storage_does_not_contain_an_ip_address(tmp_path: Path) -> None:
    """An IP address does not reach the JSON Lines output."""
    ip_address = "192.0.2.44"  # Use a documentation IPv4 address as adversarial input.
    output = _stored_output(tmp_path, ip_address)  # Store an adversarial IP address label.
    assert ip_address not in output  # Prove the IP address did not reach disk.


def test_storage_does_not_contain_a_mac_address(tmp_path: Path) -> None:
    """A MAC address does not reach the JSON Lines output."""
    mac_address = "aa:bb:cc:dd:ee:ff"  # Use a MAC address shape that Mist records use often.
    output = _stored_output(tmp_path, mac_address)  # Store an adversarial MAC address label.
    assert mac_address not in output  # Prove the MAC address did not reach disk.


def test_storage_does_not_contain_a_uuid(tmp_path: Path) -> None:
    """A UUID does not reach the JSON Lines output."""
    uuid_value = "3f2504e0-4f89-11d3-9a0c-0305e82c3301"  # Use a tenant-like object identifier.
    output = _stored_output(tmp_path, uuid_value)  # Store an adversarial UUID label.
    assert uuid_value not in output  # Prove the UUID did not reach disk.


def test_storage_does_not_contain_a_token(tmp_path: Path) -> None:
    """A token value does not reach the JSON Lines output."""
    token_value = "Bearer abcdefghijklmnopqrstuvwxyz123456"  # Use an opaque bearer token shape.
    output = _stored_output(tmp_path, token_value)  # Store an adversarial token label.
    assert "abcdefghijklmnopqrstuvwxyz123456" not in output  # Prove the token did not reach disk.
