"""Operator-facing text for the WebSocket utility catalog.

Why:
    Issue #3551. The live browser check showed names such as "Retrieve arp
    table" and sentences such as "Run retrieve arp table and stream the
    output". The page needs plain names, correct acronyms, and one clear
    sentence for each utility, so that a junior engineer can pick the correct
    entry.
"""

from __future__ import annotations  # Postponed annotations keep each hint import-safe.

import logging  # The portal uses standard logging for each action.

from src.websocket_streams.catalog.model import Safety  # The sentence depends on the safety class.

logger = logging.getLogger(__name__)  # Keep text log records under this module name.


class UtilityText:
    """Build the names, the sentences, and the hints that the page shows."""

    _ACRONYMS = {
        "ap": "AP",
        "arp": "ARP",
        "bgp": "BGP",
        "dhcp": "DHCP",
        "id": "ID",
        "ids": "IDs",
        "ip": "IP",
        "mac": "MAC",
        "ospf": "OSPF",
        "ssid": "SSID",
        "vlan": "VLAN",
        "vrf": "VRF",
    }
    _NAMES = {
        "band": "Radio band",
        "createShellSession": "Remote shell",
        "interfaces": "Interfaces",
        "ip": "IP address",
        "macs": "MAC addresses",
        "max_pkt_len": "Maximum packet length",
        "num_packets": "Number of packets",
        "orgRemotePcap": "Organization packet capture",
        "port_id": "Port",
        "port_ids": "Ports",
        "remotePcap": "Packet capture",
        "remotePcapWired": "Wired packet capture",
        "remotePcapWireless": "Wireless packet capture",
        "self_originate": "Self-originated entries only",
        "siteRemotePcap": "Site packet capture",
        "size": "Packet size",
        "tcpdump_expression": "Capture filter",
        "topCommand": "Top processes",
    }
    _SENTENCES = {
        "bouncePort": "Turn the selected ports off and on again. Traffic on the ports stops for a short time.",
        "cableTest": "Test the cable on one port. Traffic on the port can stop during the test.",
        "clearSessions": "Clear the matching sessions on the device. The active connections stop.",
        "createShellSession": "Open a remote command shell on the device.",
        "monitorTraffic": "Show the live traffic counters of one port. The view changes as the device sends output.",
        "ping": "Send ping packets from the device to one host.",
        "releaseDhcpLeases": "Release DHCP leases on the device. Each client must then ask for a new address.",
        "showServicePath": "Show the path that one service takes through the router.",
        "topCommand": "Show the busiest processes on the device. The view changes as the device sends output.",
        "traceroute": "Trace the network path from the device to one host.",
    }
    _HINTS = {
        "host": "Type a host name or an IP address.",
        "interfaces": "Type one or more Mist Edge interface names. Put a comma between the names.",
        "macs": "Type one or more MAC addresses. Put a comma between the addresses.",
        "node": "Choose a node only for a two-node cluster.",
        "port_id": "Type one port name. Example: ge-0/0/1",
        "port_ids": "Type one or more port names. Put a comma between the names. Example: ge-0/0/1, ge-0/0/2",
        "prefix": "Type a network prefix. Example: 10.0.0.0/8",
        "service_ids": "Type one or more service IDs. Put a comma between the IDs.",
        "tcpdump_expression": "Type a tcpdump filter of 256 characters or fewer. Example: port 53",
    }

    @classmethod
    def label(cls, name: str) -> str:
        """Return the plain label for one SDK function name or field name.

        Args:
            name: The SDK function name or the SDK parameter name.

        Returns:
            The label with correct acronyms and a capital first letter.
        """
        logger.debug("Building the WebSocket label for %s", name)  # Debug level: the catalog builds many labels.
        if name in cls._NAMES:  # A curated name is clearer than a split identifier.
            return cls._NAMES[name]  # Return the curated name.
        spaced = "".join((" " + char if char.isupper() else char) for char in name)  # Split camel case.
        words = [cls._ACRONYMS.get(word, word) for word in spaced.replace("_", " ").lower().split()]  # Fix acronyms.
        text = " ".join(words)  # Join the words with single spaces.
        return text[:1].upper() + text[1:]  # Capitalize only the first letter, so acronyms stay intact.

    @classmethod
    def sentence(cls, name: str, safety: Safety) -> str:
        """Return one plain sentence that tells what a utility does.

        Args:
            name: The SDK function name.
            safety: The safety class of the utility.

        Returns:
            One or two short sentences for the page.
        """
        logger.debug("Building the WebSocket sentence for %s", name)  # Debug level: the catalog builds many texts.
        if safety is Safety.CAPTURE:  # All captures share one limit and one output.
            return "Capture packets for 60 seconds and show each packet record."  # Describe the capture result.
        if name in cls._SENTENCES:  # A curated sentence states the effect of the utility.
            return cls._SENTENCES[name]  # Return the curated sentence.
        if name.startswith("retrieve"):  # A retrieve utility reads one table or one summary.
            subject = cls.label(name).split(" ", 1)[-1]  # Drop the word "Retrieve" from the label.
            return f"Get the {subject} from the device."  # State the read result.
        return f"Run {cls.label(name)} on the device and show the output."  # Safe text for a new SDK utility.

    @classmethod
    def hint(cls, name: str) -> str:
        """Return the input hint for one field.

        Args:
            name: The SDK parameter name.

        Returns:
            One short hint, or an empty text when the field needs no hint.
        """
        logger.debug("Building the WebSocket hint for %s", name)  # Debug level: the catalog builds many hints.
        return cls._HINTS.get(name, "")  # Most fields need no extra text.
