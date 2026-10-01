"""Tests for WebSocket start request checks."""

from collections.abc import Mapping  # Type the fake directory store.

import pytest  # Pytest checks refusal paths.

from src.websocket_streams.catalog.channels import ChannelCatalog  # Build the channel catalog.
from src.websocket_streams.catalog.registry import StreamCatalog  # Build the joined catalog.
from src.websocket_streams.catalog.utilities import UtilityCatalog  # Build the utility catalog.
from src.websocket_streams.intake.fields import StreamRequestError  # Check refusal codes.
from src.websocket_streams.intake.start_request import DeviceFacts, StartRequestChecker  # Import checker types.

ORG_ID = "11111111-1111-4111-8111-111111111111"  # Use one valid organization identifier.
SITE_ID = "22222222-2222-4222-8222-222222222222"  # Use one valid site identifier.
DEVICE_ID = "33333333-3333-4333-8333-333333333333"  # Use one valid device identifier.
OTHER_ID = "44444444-4444-4444-8444-444444444444"  # Use one second valid identifier.


class FakeDirectory:
    """Return device facts from an in-memory map."""

    def __init__(self, facts: Mapping[tuple[str, str], DeviceFacts | None]) -> None:
        """Store fake device facts."""
        self.facts = dict(facts)  # Copy the map so tests cannot mutate it later.
        self.calls: list[tuple[str, str]] = []  # Record lookups for lock ordering tests.

    def describe_device(self, site_id: str, device_id: str) -> DeviceFacts | None:
        """Return the fake device facts."""
        self.calls.append((site_id, device_id))  # Record that the checker asked for this device.
        return self.facts.get((site_id, device_id))  # Return the configured fake answer.


def build_checker(
    changes: bool = False, shell: bool = False, family: str | None = "ex", name: str = "HQ-SW-01"
) -> tuple[StartRequestChecker, FakeDirectory]:
    """Build a start request checker and fake directory."""
    directory = FakeDirectory(
        {(SITE_ID, DEVICE_ID): DeviceFacts(name, family) if family is not None else None}
    )  # Configure one device.
    catalog = StreamCatalog(
        ChannelCatalog(), UtilityCatalog(), changes_enabled=changes, shell_enabled=shell
    )  # Build the catalog with flags.
    return StartRequestChecker(catalog, directory, ORG_ID), directory  # Return both test objects.


def channel_body() -> dict[str, object]:
    """Return a valid channel start body."""
    return {
        "kind": "channel",
        "key": "site.devices",
        "targets": {"site_id": SITE_ID},
        "parameters": {},
        "confirmation": None,
        "labels": {SITE_ID: "HQ"},
    }  # Valid channel body.


def utility_body(
    key: str = "ex.ping", parameters: object | None = None, confirmation: object | None = None
) -> dict[str, object]:
    """Return a valid utility start body."""
    return {
        "kind": "utility",
        "key": key,
        "targets": {"site_id": SITE_ID, "device_id": DEVICE_ID},
        "parameters": parameters if parameters is not None else {"host": "192.0.2.1"},
        "confirmation": confirmation,
        "labels": {SITE_ID: "HQ", DEVICE_ID: "Switch"},
    }  # Valid utility body.


def shell_body(confirmation: object | None = None) -> dict[str, object]:
    """Return a valid shell start body."""
    return {
        "kind": "shell",
        "key": "ex.createShellSession",
        "targets": {"site_id": SITE_ID, "device_id": DEVICE_ID},
        "parameters": {},
        "confirmation": confirmation,
        "labels": {DEVICE_ID: "Switch"},
    }  # Valid shell body.


def assert_error(
    body: object,
    code: str,
    field: str | None = None,
    changes: bool = False,
    shell: bool = False,
    family: str | None = "ex",
) -> StreamRequestError:
    """Check that a body raises one refusal."""
    checker, _directory = build_checker(changes=changes, shell=shell, family=family)  # Build the checker for this case.
    with pytest.raises(StreamRequestError) as error:  # Capture the refusal.
        checker.check(body)  # Check the invalid body.
    assert error.value.code == code  # The refusal code must match.
    if field is not None:  # Some refusals name a field.
        assert error.value.extra.get("field") == field  # The refusal must name the field.
    return error.value  # Let callers check extra values.


def test_start_request_accepts_channel_and_adds_org_id() -> None:
    """A valid channel request becomes a checked StartRequest."""
    checker, _directory = build_checker()  # Build a checker.
    request = checker.check(channel_body())  # Check a valid channel body.
    assert request.kind == "channel" and request.key == "site.devices"  # The request keeps its kind and key.
    assert request.target("org_id") == ORG_ID  # The checker adds the organization from settings.
    assert request.title == "Device events - HQ"  # The title uses the provided label.


def test_start_request_accepts_utility_and_checks_device() -> None:
    """A valid utility request checks parameters and device facts."""
    checker, directory = build_checker()  # Build a checker.
    request = checker.check(utility_body(parameters={"host": "192.0.2.1", "count": 5}))  # Check a valid ping body.
    assert request.parameters == {"host": "192.0.2.1", "count": 5}  # The parameters are checked and converted.
    assert request.device_name == "HQ-SW-01"  # The device name comes from the directory.
    assert directory.calls == [(SITE_ID, DEVICE_ID)]  # The checker does one device lookup.


def test_start_request_refuses_unknown_top_level_key() -> None:
    """A raw path key is refused."""
    body = channel_body() | {"path": "/sites/x/devices"}  # Add a forbidden raw path.
    error = assert_error(body, "bad_request", "path")  # The checker refuses the unknown key.
    assert error.status == 400  # A field refusal gives the page HTTP 400.


def test_start_request_refuses_unknown_catalog_key() -> None:
    """An unknown catalog key is refused."""
    body = channel_body() | {"key": "site.unknown"}  # Use an unknown channel key.
    error = assert_error(body, "unknown_key")  # The checker refuses the key.
    assert error.status == 404  # An unknown catalog key gives the page HTTP 404.


def test_start_request_refuses_unknown_target_and_org_id_body() -> None:
    """Unknown targets and body org_id values are refused."""
    body = channel_body()  # Build a valid body.
    body["targets"] = {"site_id": SITE_ID, "org_id": ORG_ID}  # Add an invalid body org_id.
    error = assert_error(body, "bad_request", "org_id")  # The checker refuses the target.
    assert error.to_payload()["field"] == "org_id"  # The JSON answer names the field for the page.


def test_start_request_refuses_bad_uuid_and_repeat_errors() -> None:
    """Targets must be valid UUIDs, unique, and within the limit."""
    bad_uuid = channel_body()  # Build a valid body.
    bad_uuid["targets"] = {"site_id": "bad"}  # Put a bad UUID in the target.
    uuid_error = assert_error(bad_uuid, "bad_request", "site_id")  # The checker refuses the UUID.
    duplicate = channel_body() | {
        "key": "site.stats.devices",
        "targets": {"site_id": [SITE_ID, SITE_ID]},
    }  # Duplicate repeat values are invalid.
    duplicate_error = assert_error(duplicate, "bad_request", "site_id")  # The checker refuses duplicates.
    too_many = channel_body() | {
        "key": "site.stats.devices",
        "targets": {"site_id": [SITE_ID] * 11},
    }  # More than 10 values are invalid.
    limit_error = assert_error(too_many, "bad_request", "site_id")  # The checker refuses too many values.
    statuses = {uuid_error.status, duplicate_error.status, limit_error.status}  # Collect each HTTP status.
    assert statuses == {400}  # Each target refusal gives the page HTTP 400.


def test_start_request_refuses_unknown_and_missing_parameters() -> None:
    """Utility parameters must match the catalog and required fields."""
    unknown = utility_body(parameters={"host": "192.0.2.1", "bad": "x"})  # Add an unknown parameter.
    unknown_error = assert_error(unknown, "bad_request", "bad")  # The checker refuses the parameter.
    missing = utility_body(parameters={})  # Omit the required host parameter.
    missing_error = assert_error(missing, "bad_request", "host")  # The checker refuses the missing parameter.
    assert {unknown_error.status, missing_error.status} == {400}  # Each parameter refusal gives the page HTTP 400.


def test_start_request_refuses_bad_host_and_count_range() -> None:
    """The checker applies field value checks to parameters."""
    bad_host = utility_body(parameters={"host": "bad host"})  # Use a host with a space.
    host_error = assert_error(bad_host, "bad_request", "host")  # The checker refuses the host.
    bad_count = utility_body(parameters={"host": "192.0.2.1", "count": 101})  # Use a count above the limit.
    count_error = assert_error(bad_count, "bad_request", "count")  # The checker refuses the count.
    assert {host_error.status, count_error.status} == {400}  # Each value refusal gives the page HTTP 400.


def test_start_request_refuses_device_lookup_and_family_errors() -> None:
    """The checker refuses unknown devices and wrong families."""
    unknown = assert_error(utility_body(), "bad_request", "device_id", family=None)  # An unknown device is refused.
    other = assert_error(utility_body(), "bad_request", "device_id", family="ap")  # Another device family is refused.
    assert unknown.message == "The device is unknown."  # The operator reads the cause of the refusal.
    assert other.message == "The device family cannot run this utility."  # The operator reads the family cause.


def test_start_request_locks_change_before_device_lookup() -> None:
    """No change entry starts while the flag is off."""
    checker, directory = build_checker(changes=False)  # Build a checker with changes locked.
    for key in [
        entry.key for entry in UtilityCatalog().entries() if entry.safety.value == "change"
    ]:  # Check each change entry.
        body = utility_body(
            key=key, parameters={"port_ids": ["ge-0/0/1"]} if key.endswith("bouncePort") else {"port_id": "ge-0/0/1"}
        )  # Build a body before lock refusal.
        with pytest.raises(StreamRequestError) as error:  # Capture the refusal.
            checker.check(body)  # Try to start the locked entry.
        assert error.value.code == "locked"  # The flag must refuse the request.
    assert directory.calls == []  # The checker must not reach the device lookup while locked.


def test_start_request_locks_shell_and_checks_confirmation() -> None:
    """Shell entries need the shell flag and the correct device name."""
    locked = assert_error(shell_body("HQ-SW-01"), "locked")  # The default shell flag is off.
    assert locked.extra["flag"] == StreamCatalog.SHELL_FLAG  # The error names the shell flag.
    assert_error(shell_body("wrong"), "confirmation", shell=True)  # A wrong confirmation is refused when unlocked.
    checker, _directory = build_checker(shell=True)  # Build a checker with shell enabled.
    request = checker.check(shell_body("  HQ-SW-01  "))  # Check a correct confirmation with spaces.
    assert (
        request.confirmation == "HQ-SW-01" and request.kind == "shell"
    )  # The request stores the stripped confirmation.


def test_start_request_sanitizes_labels_and_limits_title_parts() -> None:
    """The title uses safe labels and abbreviates long target lists."""
    checker, _directory = build_checker()  # Build a checker.
    labels = {SITE_ID: "HQ\x00" + "A" * 80, OTHER_ID: "Remote"}  # Add unsafe and long label text.
    body = {
        "kind": "channel",
        "key": "site.stats.devices",
        "targets": {
            "site_id": [
                SITE_ID,
                OTHER_ID,
                "55555555-5555-4555-8555-555555555555",
                "66666666-6666-4666-8666-666666666666",
            ]
        },
        "parameters": {},
        "labels": labels,
    }  # Build a multi-target body.
    request = checker.check(body)  # Check the request.
    assert (
        "\x00" not in request.title and "(+1)" in request.title
    )  # The title drops unsafe text and shows an overflow count.
    assert len(request.title.split(" - ", 1)[1].split(", ")[0]) == 64  # The first label is capped at 64 characters.
