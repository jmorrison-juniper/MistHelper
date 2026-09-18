"""Scan one Mist organization for a rogue DHCP server on a switch.

The package answers one question for a NOC engineer: does any switch in this
organization report a rogue DHCP server now, or did one report it inside the
scan window? It reads alarms, switch events, and Marvis config actions, and it
merges every source into one table.

Modules:
    ``signals``   holds every literal Mist type string and the match rule.
    ``records``   holds the row shape, the normalizer, and the merge rule.
    ``scanner``   holds the organization to site fan-out.
    ``operation`` holds the menu entry point and the export call.
"""

from src.security.rogue_dhcp.operation import RogueDhcpScanOperation  # Re-export the menu entry point.
from src.security.rogue_dhcp.records import RogueDhcpFinding, RogueDhcpFindingMerger  # Re-export the row shape.
from src.security.rogue_dhcp.scanner import RogueDhcpScanner, RogueDhcpScanResult  # Re-export the scanner.
from src.security.rogue_dhcp.signals import RogueDhcpSignalMatcher  # Re-export the match rule.

__all__ = [  # Name the supported import surface for a reader and for a linter.
    "RogueDhcpFinding",
    "RogueDhcpFindingMerger",
    "RogueDhcpScanOperation",
    "RogueDhcpScanResult",
    "RogueDhcpScanner",
    "RogueDhcpSignalMatcher",
]
