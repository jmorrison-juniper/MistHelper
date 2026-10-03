"""Tests for the WebSocket utility catalog."""

from collections import Counter  # Count families and safety classes.

from src.websocket_streams.catalog.model import Safety  # Import safety enum values.
from src.websocket_streams.catalog.utilities.utility_catalog import UtilityCatalog  # Import the catalog leaf class.


def test_utility_catalog_counts_match_contract() -> None:
    """The utility catalog matches the SDK-backed contract counts."""
    entries = UtilityCatalog().entries()  # Build and read the catalog.
    assert len(entries) == 54  # The contract requires 54 utilities.
    assert Counter(entry.family for entry in entries) == {
        "ap": 5,
        "ex": 13,
        "srx": 18,
        "ssr": 16,
        "mxedge": 2,
    }  # Each family count must match.
    assert Counter(entry.safety for entry in entries) == {
        Safety.READ: 36,
        Safety.CAPTURE: 7,
        Safety.CHANGE: 9,
        Safety.SHELL: 2,
    }  # Each safety count must match.


def test_utility_catalog_fields_and_outputs() -> None:
    """The utility catalog assigns fields and output views from SDK names."""
    catalog = UtilityCatalog()  # Build the utility catalog.
    ping = catalog.get("ex.ping")  # Read a read-only utility.
    capture = catalog.get("srx.remotePcap")  # Read a gateway capture.
    shell = catalog.get("srx.createShellSession")  # Read a shell entry.
    assert ping is not None and [field.name for field in ping.fields][:2] == [
        "host",
        "count",
    ]  # Ping uses host and count fields.
    assert (
        capture is not None and capture.output == "packets" and capture.fields[0].name == "port_ids"
    )  # Gateway captures derive port_ids.
    assert (
        shell is not None and shell.output == "terminal" and shell.safety is Safety.SHELL
    )  # Shell entries use terminal output.


def test_utility_catalog_unknown_key_returns_none() -> None:
    """An unknown utility key returns None."""
    assert UtilityCatalog().get("ex.clearMacTable") is None  # REST-only calls must stay excluded.
