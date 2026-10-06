"""Tests for the WebSocket channel catalog."""

from src.mist.realtime.websocket_streams.catalog.channels import ChannelCatalog  # Import the catalog under test.


def test_channel_catalog_has_16_entries_in_page_order() -> None:
    """The channel catalog holds each channel from the contract."""
    catalog = ChannelCatalog()  # Build the channel catalog.
    entries = catalog.entries()  # Read all entries.
    assert len(entries) == 16  # The contract requires 16 channels.
    assert entries[0].key == "org.pcaps"  # The first entry follows the page order.
    assert entries[-1].key == "diag.sdkclient"  # The last entry follows the page order.
    assert catalog.get("org.mxedges") is None  # Deprecated organization events are absent.
    assert catalog.get("site.mxedges") is None  # Deprecated site events are absent.
    org_stats = catalog.get("org.stats.mxedges")  # Read the retained organization statistics channel.
    site_stats = catalog.get("site.stats.mxedges")  # Read the retained site statistics channel.
    assert (
        org_stats is not None and org_stats.path_template == "/orgs/{org_id}/stats/mxedges"
    )  # The organization statistics channel keeps its working path.
    assert (
        site_stats is not None and site_stats.path_template == "/sites/{site_id}/stats/mxedges"
    )  # The site statistics channel keeps its working path.


def test_channel_catalog_lookup_and_repeatable_path() -> None:
    """A channel key resolves and builds repeated device command paths."""
    catalog = ChannelCatalog()  # Build the channel catalog.
    entry = catalog.get("site.devices.cmd")  # Read the repeated device channel.
    assert entry is not None and entry.key == "site.devices.cmd"  # The key resolves to its own entry.
    paths = entry.build_paths(
        {
            "site_id": ("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",),
            "device_id": ("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb", "cccccccc-cccc-4ccc-8ccc-cccccccccccc"),
        }
    )  # Build repeated device paths.
    assert paths == (
        "/sites/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa/devices/bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb/cmd",
        "/sites/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa/devices/cccccccc-cccc-4ccc-8ccc-cccccccccccc/cmd",
    )  # Each device gives one path.


def test_channel_catalog_unknown_key_returns_none() -> None:
    """An unknown channel key returns None."""
    catalog = ChannelCatalog()  # Build the channel catalog.
    assert catalog.get("path") is None  # Raw path names must not resolve.
