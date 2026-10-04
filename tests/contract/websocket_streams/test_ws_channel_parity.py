"""Contract tests for SDK WebSocket channel parity."""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

import inspect  # The tests pin the runner constructor.
from collections.abc import Callable  # Type SDK class constructors.

from mistapi.websockets import location, orgs, sites  # Import SDK channel modules.

from src.mist.realtime.websocket_streams.catalog.channels import ChannelCatalog  # Import channel catalog.
from src.mist.realtime.websocket_streams.live.runners.channel import (
    runner as channel_module,
)  # Inspect the owned channel runner.
from src.mist.realtime.websocket_streams.live.runners.channel.runner import (
    ChannelStreamRunner,
)  # Pin the constructor interface.

ORG_ID = "11111111-1111-4111-8111-111111111111"  # Use one valid organization identifier.
SITE_ID = "22222222-2222-4222-8222-222222222222"  # Use one valid site identifier.
DEVICE_ID = "33333333-3333-4333-8333-333333333333"  # Use one valid device identifier.
MAP_ID = "44444444-4444-4444-8444-444444444444"  # Use one valid map identifier.


def test_public_sdk_channel_classes_match_catalog_paths() -> None:
    """Each public SDK channel class matches the catalog path."""
    cases: tuple[tuple[str, Callable[[], object], dict[str, tuple[str, ...]]], ...] = (
        (
            "org.pcaps",
            lambda: orgs.PcapEvents(object(), ORG_ID),
            {"org_id": (ORG_ID,)},
        ),  # Organization packet captures.
        (
            "org.insights.summary",
            lambda: orgs.InsightsEvents(object(), ORG_ID),
            {"org_id": (ORG_ID,)},
        ),  # Organization insights.
        (
            "org.stats.mxedges",
            lambda: orgs.MxEdgesStatsEvents(object(), ORG_ID),
            {"org_id": (ORG_ID,)},
        ),  # Organization Mist Edge stats.
        (
            "org.mxedges",
            lambda: orgs.MxEdgesEvents(object(), ORG_ID),
            {"org_id": (ORG_ID,)},
        ),  # Organization Mist Edges.
        (
            "site.stats.clients",
            lambda: sites.ClientsStatsEvents(object(), [SITE_ID]),
            {"site_id": (SITE_ID,)},
        ),  # Site client stats.
        (
            "site.devices.cmd",
            lambda: sites.DeviceCmdEvents(object(), SITE_ID, [DEVICE_ID]),
            {"site_id": (SITE_ID,), "device_id": (DEVICE_ID,)},
        ),  # Device command events.
        (
            "site.stats.devices",
            lambda: sites.DeviceStatsEvents(object(), [SITE_ID]),
            {"site_id": (SITE_ID,)},
        ),  # Site device stats.
        (
            "site.devices",
            lambda: sites.DeviceEvents(object(), [SITE_ID]),
            {"site_id": (SITE_ID,)},
        ),  # Site device events.
        (
            "site.stats.mxedges",
            lambda: sites.MxEdgesStatsEvents(object(), [SITE_ID]),
            {"site_id": (SITE_ID,)},
        ),  # Site Mist Edge stats.
        (
            "site.mxedges",
            lambda: sites.MxEdgesEvents(object(), [SITE_ID]),
            {"site_id": (SITE_ID,)},
        ),  # Site Mist Edge events.
        ("site.pcaps", lambda: sites.PcapEvents(object(), SITE_ID), {"site_id": (SITE_ID,)}),  # Site packet captures.
        (
            "location.assets",
            lambda: location.BleAssetsEvents(object(), SITE_ID, [MAP_ID]),
            {"site_id": (SITE_ID,), "map_id": (MAP_ID,)},
        ),  # Asset location stream.
        (
            "location.clients",
            lambda: location.ConnectedClientsEvents(object(), SITE_ID, [MAP_ID]),
            {"site_id": (SITE_ID,), "map_id": (MAP_ID,)},
        ),  # Client location stream.
        (
            "location.sdkclients",
            lambda: location.SdkClientsEvents(object(), SITE_ID, [MAP_ID]),
            {"site_id": (SITE_ID,), "map_id": (MAP_ID,)},
        ),  # SDK client location stream.
        (
            "location.unconnected_clients",
            lambda: location.UnconnectedClientsEvents(object(), SITE_ID, [MAP_ID]),
            {"site_id": (SITE_ID,), "map_id": (MAP_ID,)},
        ),  # Unconnected location stream.
        (
            "location.discovered_assets",
            lambda: location.DiscoveredBleAssetsEvents(object(), SITE_ID, [MAP_ID]),
            {"site_id": (SITE_ID,), "map_id": (MAP_ID,)},
        ),  # Discovered asset stream.
    )
    catalog = ChannelCatalog()  # Build the channel catalog.
    for key, factory, targets in cases:  # Check each public SDK class.
        entry = catalog.get(key)  # Read the matching catalog entry.
        sdk_channels = tuple(factory()._channels)  # Read the SDK channel list.
        assert entry is not None and entry.build_paths(targets) == sdk_channels  # The catalog path must match the SDK.


def test_channel_runner_uses_owned_transport_interface() -> None:
    """Pin the owned channel runner interface."""
    signature = inspect.signature(ChannelStreamRunner)  # Read the constructor signature.
    assert tuple(signature.parameters) == ("endpoint", "request", "sink")  # The lead factory calls this form.
    assert "_MistWebsocket" not in vars(channel_module)  # The runner must not depend on the private SDK client.
