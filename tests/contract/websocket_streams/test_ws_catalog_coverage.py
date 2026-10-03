"""Contract tests for WebSocket utility catalog coverage."""

import mistapi.device_utils.ap as sdk_ap  # Import AP SDK facade.
import mistapi.device_utils.ex as sdk_ex  # Import EX SDK facade.
import mistapi.device_utils.mxedge as sdk_mxedge  # Import Mist Edge SDK facade.
import mistapi.device_utils.srx as sdk_srx  # Import SRX SDK facade.
import mistapi.device_utils.ssr as sdk_ssr  # Import SSR SDK facade.

from src.mist.realtime.websocket_streams.catalog.utilities.utility_catalog import (
    UtilityCatalog,
)  # Import the catalog leaf class.


def test_utility_catalog_covers_sdk_facades_after_exclusions() -> None:
    """The utility catalog covers every streaming SDK utility."""
    exclusions = {
        "clearBpduError",
        "clearDot1xSessions",
        "clearLearnedMac",
        "clearMacTable",
        "clearHitCount",
        "interactiveShell",
        "ShellSession",
        "Node",
        "RouteProtocol",
        "TracerouteProtocol",
        "SessionWithUrl",
    }  # Contract exclusions.
    modules = {
        "ap": sdk_ap,
        "ex": sdk_ex,
        "srx": sdk_srx,
        "ssr": sdk_ssr,
        "mxedge": sdk_mxedge,
    }  # SDK facades under contract.
    expected = {
        f"{family}.{name}"
        for family, module in modules.items()
        for name in module.__all__
        if name not in exclusions and callable(getattr(module, name, None))
    }  # Read SDK public functions.
    actual = {entry.key for entry in UtilityCatalog().entries()}  # Read catalog utility keys.
    assert actual == expected  # Catalog coverage must match the SDK after exclusions.
    assert len(actual) == 54  # The SDK-backed count must stay at 54.
