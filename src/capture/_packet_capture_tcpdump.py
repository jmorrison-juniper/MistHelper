"""tcpdump menu + expression cluster extracted from packet_capture.py.

Owns the interactive tcpdump filter picker so the parent
``PacketCaptureManager`` does not have to carry the ~90-line menu, the
40-entry expression map, and the selection/format prompts inline.
Callers instantiate :class:`PacketCaptureTcpdump` directly so
``PacketCaptureManager`` binds an instance on itself as ``self._tcpdump``;
``__getattr__`` delegates lookups that miss on the wrapper back to the
manager so shared state (``self._mm``) remains transparent.
"""

from __future__ import annotations  # WHY: postponed evaluation for consistency with parent module

from typing import Any  # WHY: manager is treated opaquely to avoid import cycles


def _pc() -> Any:  # WHY: lazy accessor exposing packet_capture module for name lookup
    """Return the ``packet_capture`` module for test-patchable name lookup."""
    from src.capture import packet_capture as _pc_mod  # pylint: disable=import-outside-toplevel

    return _pc_mod  # WHY: resolved at call time so test patches on packet_capture take effect


def _lazy_input_utils() -> Any:  # WHY: routes InputUtils lookup through packet_capture for test patch parity
    """Return InputUtils via packet_capture so tests patch a single point."""
    return _pc()._get_input_utils()  # WHY: reroute through packet_capture module for patch parity


_MENU_SECTIONS: tuple[tuple[str, tuple[str, ...]], ...] = (  # WHY: module-level menu table drives the picker
    (
        "BASIC FILTERS",
        (
            "1.  All traffic (no filter)",
            "2.  HTTPS only (port 443)",
            "3.  HTTP/HTTPS (port 80 or 443)",
            "4.  DNS (port 53)",
            "5.  SSH (port 22)",
            "6.  FTP (port 21)",
            "7.  SMTP Email (port 25)",
            "8.  ICMP/ping",
            "9.  ARP",
        ),
    ),
    (
        "PROTOCOL FILTERS",
        (
            "10. TCP only",
            "11. UDP only",
            "12. Not ICMP (exclude ping)",
        ),
    ),
    (
        "DIRECTION FILTERS",
        (
            "13. Outbound to port 443",
            "14. Inbound from port 80",
        ),
    ),
    (
        "COMBINED FILTERS",
        (
            "15. HTTP or HTTPS or DNS (port 80 or 443 or 53)",
            "16. All except SSH (not port 22)",
            "17. TCP SYN packets (connection attempts)",
            "18. TCP SYN-ACK packets (connection replies)",
            "19. TCP RST packets (connection resets)",
            "20. TCP FIN packets (connection close)",
        ),
    ),
    (
        "ADVANCED FILTERS",
        (
            "21. Non-standard ports (>1024)",
            "22. All except ARP and DNS",
            "23. TCP traffic on non-standard ports",
            "24. Broadcast traffic",
            "25. Multicast traffic",
            "26. IPv6 only",
            "27. VLAN tagged traffic",
        ),
    ),
    (
        "APPLICATION PROTOCOLS",
        (
            "28. SMB/CIFS file sharing (port 445)",
            "29. RDP Remote Desktop (port 3389)",
            "30. NTP time sync (port 123)",
            "31. SNMP monitoring (port 161)",
            "32. Syslog (port 514)",
            "33. DHCP (port 67 or 68)",
            "34. LDAP directory (port 389)",
            "35. MySQL database (port 3306)",
        ),
    ),
    (
        "SECURITY & TROUBLESHOOTING",
        (
            "36. Port scans (SYN without ACK)",
            "37. Fragmented packets",
            "38. Large packets (>1500 bytes)",
            "39. Retransmissions (duplicate SEQ)",
            "40. Custom expression",
        ),
    ),
)


_EXPRESSIONS: dict[str, str] = {  # WHY: menu-choice-to-expression lookup keyed by user input string
    "1": "",
    "2": "port 443",
    "3": "port 80 or port 443",
    "4": "port 53",
    "5": "port 22",
    "6": "port 21",
    "7": "port 25",
    "8": "icmp",
    "9": "arp",
    "10": "tcp",
    "11": "udp",
    "12": "not icmp",
    "13": "dst port 443",
    "14": "src port 80",
    "15": "port 80 or port 443 or port 53",
    "16": "not port 22",
    "17": "tcp[tcpflags] & tcp-syn != 0",
    "18": "tcp[tcpflags] = 0x12",
    "19": "tcp[tcpflags] & tcp-rst != 0",
    "20": "tcp[tcpflags] & tcp-fin != 0",
    "21": "tcp[0:2] > 1024 or udp[0:2] > 1024",
    "22": "not arp and not port 53",
    "23": "tcp and port > 1024",
    "24": "ether broadcast",
    "25": "ether multicast",
    "26": "ip6",
    "27": "vlan",
    "28": "port 445",
    "29": "port 3389",
    "30": "port 123",
    "31": "port 161",
    "32": "port 514",
    "33": "port 67 or port 68",
    "34": "port 389",
    "35": "port 3306",
    "36": "tcp[tcpflags] & (tcp-syn) != 0 and tcp[tcpflags] & (tcp-ack) = 0",
    "37": "ip[6:2] & 0x1fff != 0",
    "38": "greater 1500",
    "39": "tcp[tcpflags] & (tcp-syn|tcp-fin|tcp-rst|tcp-push|tcp-ack|tcp-urg) = 0",
}


class PacketCaptureTcpdump:  # WHY: wraps tcpdump menu helpers extracted from PacketCaptureManager
    """Wrapper class holding the extracted tcpdump menu helpers."""

    def __init__(self, manager: Any) -> None:  # WHY: bind parent manager so __getattr__ can proxy state
        """Store the parent manager for delegate lookups."""
        self._mm = manager  # WHY: enable __getattr__ delegation back to PacketCaptureManager

    def __getattr__(self, name: str) -> Any:  # WHY: transparent proxy so callers see combined API
        """Delegate unknown attributes to the wrapped manager."""
        mm = self.__dict__.get("_mm")  # WHY: guard against half-initialized instances
        if mm is None:  # WHY: only trips during broken init; avoid infinite recursion
            raise AttributeError(name)  # WHY: signal missing attribute cleanly to callers
        return getattr(mm, name)  # WHY: transparent proxy to the parent manager

    @staticmethod
    def print_tcpdump_menu() -> None:  # WHY: renders the picker header + all filter sections
        """Print the tcpdump filter selection menu using data-driven sections."""
        separator = "=" * 80  # WHY: consistent visual boundary matching original format
        print(f"\n{separator}")  # WHY: leading newline improves terminal readability
        print(" PACKET FILTER SELECTION (tcpdump expression)")  # WHY: menu title matches prior UX
        print(separator)  # WHY: bottom border of the title band
        for header, items in _MENU_SECTIONS:  # WHY: iterate the module-level section table
            print(f"\n--- {header} ---")  # WHY: preserves original section header format
            for item in items:  # WHY: render each numbered filter line
                print(f"  {item}")  # WHY: leading spaces match legacy indentation
        print(separator)  # WHY: closes the menu block visually

    @staticmethod
    def get_tcpdump_expressions() -> dict[str, str]:  # WHY: exposes copy of choice-to-expression map
        """Return the menu-choice to tcpdump-expression mapping."""
        return dict(_EXPRESSIONS)  # WHY: return a shallow copy so callers cannot mutate the constant

    def get_tcpdump_expression_selection(self) -> str:  # WHY: interactive picker returning the chosen expression
        """Prompt user for a tcpdump expression selection.

        Returns:
            The chosen tcpdump expression, or an empty string when the user
            selects no filter, chooses an invalid entry, or supplies an empty
            custom expression.
        """
        self.print_tcpdump_menu()  # WHY: display the menu before soliciting input
        choice = _lazy_input_utils().safe_input(  # WHY: reuse project-wide input safety wrapper
            "\nEnter choice (default 1 - all traffic): ",  # WHY: mirror legacy prompt text
            default_value="1",  # WHY: default to no filter for the safest capture
            context="tcpdump_filter",  # WHY: audit-trail tag for input logging
        )
        if choice in _EXPRESSIONS:  # WHY: happy path lookup in the constant map
            return self._announce_expression(_EXPRESSIONS[choice])  # WHY: uniform user feedback
        if choice == "40":  # WHY: sentinel for custom-expression branch
            return self._prompt_custom_expression()  # WHY: isolate custom-entry logic
        print("\n! Invalid choice, using no filter")  # WHY: explicit fallback message to user
        return ""  # WHY: safe default when user enters an unknown menu number

    @staticmethod
    def _announce_expression(expr: str) -> str:  # WHY: shared user-feedback branch for happy-path selection
        """Print user feedback for a chosen expression and return it."""
        if expr:  # WHY: distinguish "no filter" from a real expression for UX clarity
            print(f"\n! Filter applied: {expr}")  # WHY: confirm to the user which filter is active
        else:  # WHY: explicit branch for "no filter" case
            print("\n! Filter: None (capturing all traffic)")  # WHY: reassure user that no filter is active
        return expr  # WHY: hand the value back to the caller unchanged

    @staticmethod
    def _prompt_custom_expression() -> str:  # WHY: isolates free-form input branch from menu-driven path
        """Prompt for and validate a custom tcpdump expression."""
        print("\nEnter custom tcpdump expression:")  # WHY: guide user into free-form input mode
        print("  Examples: 'host 192.168.1.1', 'net 10.0.0.0/8', 'port 8080'")  # WHY: help user with syntax
        custom_expr = _lazy_input_utils().safe_input(  # WHY: safe wrapper handles Ctrl-C / EOF
            "Expression: ",  # WHY: minimal prompt matches legacy behavior
            context="tcpdump_custom",  # WHY: distinct audit tag from menu selection
            allow_empty=True,  # WHY: allow user to cancel by submitting an empty line
        )
        if custom_expr:  # WHY: only echo confirmation when a real expression was supplied
            print(f"\n! Filter applied: {custom_expr}")  # WHY: confirm active filter to the user
            return str(custom_expr)  # WHY: coerce to str so return type stays uniform
        print("\n! No filter applied")  # WHY: explicit "no filter" feedback when input was empty
        return ""  # WHY: preserve legacy return type for downstream API calls

    @staticmethod
    def get_capture_format_selection() -> str:
        """Prompt user for capture format selection.

        NOTE: API documentation lists switches/gateways as stream-only, but
        pcap works in practice and yields downloadable files, so both are
        offered and the API is allowed to reject unsupported combinations.

        Returns:
            The selected format, either ``"pcap"`` or ``"stream"``.
        """
        print("\nCapture format:")  # WHY: header for the two-option selector
        print("  1. PCAP file - downloadable (default, recommended)")  # WHY: default choice for most users
        print("  2. Stream to Mist Cloud (WebSocket real-time)")  # WHY: alternate for real-time monitoring
        format_choice = _lazy_input_utils().safe_input(  # WHY: reuse safe wrapper for consistency
            "Enter choice (default 1): ",  # WHY: prompt matches legacy UX
            default_value="1",  # WHY: bias toward the downloadable pcap format
            context="format",  # WHY: audit tag for input logging
        )
        return "pcap" if format_choice == "1" else "stream"  # WHY: any non-"1" input falls through to stream
