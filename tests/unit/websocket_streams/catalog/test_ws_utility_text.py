"""Tests for the WebSocket utility text and the SDK enum choices.

Why:
    Issue #3551. The live browser check found raw names such as "Retrieve arp
    table" and the traceroute protocol values on the routes utility. These
    tests keep the plain text and the per-function enum values correct.
"""

from __future__ import annotations  # Keep annotations lazy for Python 3.13.

from enum import Enum  # The annotation tests need a small enum.

from src.websocket_streams.catalog.model import FieldKind, Safety  # Field kinds and safety classes.
from src.websocket_streams.catalog.sdk_annotation import SdkAnnotation  # The class under test.
from src.websocket_streams.catalog.utilities import UtilityCatalog  # The catalog reads the SDK signatures.
from src.websocket_streams.catalog.utility_text import UtilityText  # The class under test.


class SampleMode(Enum):
    """A small enum that stands in for an SDK enum."""

    FAST = "fast"  # The first value keeps its SDK order.
    SLOW = "slow"  # The second value keeps its SDK order.


def sample_function(mode: SampleMode | None = None, name: str = "") -> None:
    """Stand in for an SDK function with one optional enum parameter."""
    return None  # The tests read only the annotations.


def unreadable_function(session: object) -> None:
    """Stand in for an SDK function that names a type the module does not import."""
    return None  # The tests read only the annotations.


unreadable_function.__annotations__ = {"session": "MissingSessionType"}  # Name a type that no module defines.


class TestUtilityText:
    """Verify the plain names, sentences, and hints."""

    def test_label_fixes_acronyms_and_uses_curated_names(self) -> None:
        """A label keeps each acronym in capitals and uses a curated name first."""
        assert UtilityText.label("retrieveArpTable") == "Retrieve ARP table"  # Camel case with an acronym.
        assert UtilityText.label("vlan_id") == "VLAN ID"  # Snake case with two acronyms.
        assert UtilityText.label("service_ids") == "Service IDs"  # The plural acronym keeps its lower-case s.
        assert UtilityText.label("remotePcapWired") == "Wired packet capture"  # A curated name wins.
        assert UtilityText.label("network") == "Network"  # A plain word gets a capital first letter.

    def test_sentence_uses_safety_curated_text_and_retrieve_rule(self) -> None:
        """A sentence states the result of the utility in plain words."""
        capture = UtilityText.sentence("remotePcap", Safety.CAPTURE)  # A capture shares one sentence.
        assert capture == "Capture packets for 60 to 3600 seconds and show each packet record."
        assert UtilityText.sentence("retrieveArpTable", Safety.READ) == "Get the ARP table from the device."  # Read.
        assert UtilityText.sentence("ping", Safety.READ).startswith("Send ping packets")  # A curated sentence.
        fallback = UtilityText.sentence("newThing", Safety.READ)  # A future SDK utility gets safe text.
        assert fallback == "Run New thing on the device and show the output."  # The fallback names the label.

    def test_hint_returns_list_help_and_empty_text(self) -> None:
        """A list field tells the operator to put a comma between the items."""
        assert "comma" in UtilityText.hint("port_ids")  # A list field explains the separator.
        assert UtilityText.hint("count") == ""  # Most fields need no extra text.


class TestSdkAnnotation:
    """Verify the SDK annotation reader."""

    def test_enum_choices_unwrap_optional_enum(self) -> None:
        """An optional enum annotation gives the enum values in SDK order."""
        hints = SdkAnnotation.hints(sample_function)  # Resolve the text annotations.
        assert SdkAnnotation.enum_type(hints["mode"]) is SampleMode  # The optional enum unwraps.
        assert SdkAnnotation.enum_choices(hints["mode"]) == ("fast", "slow")  # The values keep their order.
        assert SdkAnnotation.enum_choices(hints["name"]) == ()  # A plain text parameter has no fixed values.

    def test_unreadable_annotations_give_empty_hints(self) -> None:
        """A missing type name gives no enum information instead of an error."""
        assert SdkAnnotation.hints(unreadable_function) == {}  # The shell functions behave like this.


class TestUtilityChoices:
    """Verify that each utility reads its own enum values."""

    def test_routes_and_traceroute_use_their_own_protocol_values(self) -> None:
        """The routes protocol and the traceroute protocol use different SDK enums."""
        catalog = UtilityCatalog()  # Build the catalog from the installed SDK.
        routes = catalog.get("srx.retrieveRoutes")  # A gateway routes utility.
        trace = catalog.get("ex.traceroute")  # A switch traceroute utility.
        assert routes is not None and trace is not None  # Both entries exist in the SDK.
        route_fields = {field.name: field for field in routes.fields}  # Look up the fields by name.
        assert route_fields["protocol"].choices == ("any", "bgp", "direct", "evpn", "ospf", "static")  # Route enum.
        assert route_fields["route_type"].kind is FieldKind.NAME  # The SDK types this value as free text.
        assert route_fields["node"].choices == ("node0", "node1")  # The node enum comes from the SDK.
        trace_protocol = next(field for field in trace.fields if field.name == "protocol")  # The traceroute field.
        assert trace_protocol.choices == ("icmp", "udp")  # The traceroute enum comes from the SDK.
