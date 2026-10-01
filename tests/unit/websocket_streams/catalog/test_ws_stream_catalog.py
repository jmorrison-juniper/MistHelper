"""Tests for the joined WebSocket stream catalog."""

from src.websocket_streams.catalog.channels import ChannelCatalog  # Import channel catalog.
from src.websocket_streams.catalog.model import Safety, UtilityDefinition  # Check the class of the shell entry.
from src.websocket_streams.catalog.registry import StreamCatalog  # Import the registry under test.
from src.websocket_streams.catalog.utilities import UtilityCatalog  # Import utility catalog.


def build_catalog(changes: bool = False, shell: bool = False) -> StreamCatalog:
    """Build a registry for tests."""
    return StreamCatalog(
        ChannelCatalog(), UtilityCatalog(), changes_enabled=changes, shell_enabled=shell
    )  # Build with test flags.


def test_stream_catalog_find_separates_shell_kind() -> None:
    """The registry keeps shell entries separate from utility starts."""
    catalog = build_catalog()  # Build the joined catalog.
    channel = catalog.find("channel", "site.devices")  # Look up one channel entry.
    utility = catalog.find("utility", "ex.ping")  # Look up one read utility entry.
    shell = catalog.find("shell", "ex.createShellSession")  # Look up the shell entry with its own kind.
    assert channel is not None and channel.key == "site.devices"  # Channel lookup returns the named entry.
    assert utility is not None and utility.key == "ex.ping"  # Utility lookup returns the named entry.
    assert catalog.find("utility", "ex.createShellSession") is None  # Shell entries do not start as utilities.
    assert isinstance(shell, UtilityDefinition) and shell.safety == Safety.SHELL  # Shell lookup returns a shell entry.


def test_stream_catalog_payload_hides_paths_and_marks_locks() -> None:
    """The page payload hides channel paths and marks locked entries."""
    payload = build_catalog().page_payload()  # Build the public payload.
    assert "path_template" not in str(payload)  # The payload must not expose channel paths.
    assert payload["flags"]["changes"]["enabled"] is False  # The default change flag is off.
    assert any(
        item["locked"] for item in payload["utilities"] if item["safety"] == "change"
    )  # Change entries are locked.


def test_stream_catalog_lock_flag_respects_flags() -> None:
    """The registry returns a lock flag only while a class is disabled."""
    locked = build_catalog().find("utility", "ex.bouncePort")  # Read a change utility with flag off.
    unlocked = build_catalog(changes=True).find("utility", "ex.bouncePort")  # Read the same utility with flag on.
    assert (
        locked is not None and build_catalog().lock_flag(locked) == StreamCatalog.CHANGES_FLAG
    )  # The disabled flag is named.
    assert (
        unlocked is not None and build_catalog(changes=True).lock_flag(unlocked) is None
    )  # The enabled flag gives no lock.
