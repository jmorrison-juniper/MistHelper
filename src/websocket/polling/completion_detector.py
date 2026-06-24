"""Detect command-completion signals in WebSocket output streams.

Splits the original 250+ line indicator-checking block from
WebSocketManager.wait_for_command_result into small per-pattern helpers
(generic, ping, service-ping, MAC table, ARP) each with CC <= 10.
"""

from __future__ import annotations

import logging  # Standard library logger
import re  # Regex used for MAC-table entry-count parsing
import time  # Used to compute idle time since last activity
from typing import Any  # Generic dict type for stored message segments

# Completion indicator vocabularies grouped by command family.
# Preserved verbatim from manager.wait_for_command_result so existing
# device output continues to be recognised.
_PING_INDICATORS = ["round-trip min/avg/max", "round-trip min/avg/max/stddev", "rtt min/avg/max"]
_SERVICE_PING_INDICATORS = [
    "service ping completed",
    "service-ping",
    "packet transmitted",
    "packets transmitted",
    "received",
    "packet loss",
    "transmission failure",
    "service path",
    "tenant context",
    "service route",
]
_ARP_INDICATORS = [
    "total mac entries",
    "total flows:",
    "mac-flow hi-water",
    "arp table",
    "no arp entries",
    "arp cache",
]
_GATEWAY_INDICATORS = [
    "connected routes",
    "total entries",
    "kernel routes",
    "bgp routes",
    "static routes",
    "route table",
]
_SWITCH_INDICATORS = [
    "learning table",
    "fdb entries",
    "vlan information",
    "port statistics",
    "interface status",
    "ethernet switching table",
    "entries, 40 learned",
    "entries,",
    "learned",
]
_GENERAL_INDICATORS = ["command completed", "operation complete", "finished"]
_ALL_INDICATORS = (
    _PING_INDICATORS
    + _SERVICE_PING_INDICATORS
    + _ARP_INDICATORS
    + _GATEWAY_INDICATORS
    + _SWITCH_INDICATORS
    + _GENERAL_INDICATORS
)
# Generic switch indicators that must be skipped when the buffer is a MAC table
# (because the MAC-table-specific logic produces a more accurate completion).
_MAC_TABLE_SKIP_INDICATORS = {"ethernet switching table", "entries,", "learned"}


class CompletionDetector:
    """Detect command-completion indicators in collected WebSocket output."""

    def __init__(self, logger: logging.Logger, debug_mode: bool) -> None:
        self.logger = logger  # Shared manager logger for trace lines
        self.debug_mode = debug_mode  # Whether to emit verbose prints
        self._mac_expected_entries: int | None = None  # MAC-table dedup cache

    def detect(
        self,
        collected_output: list[dict[str, Any]],
        all_raw_content: str,
        last_activity: float,
        check_count: int,
    ) -> str | None:
        """Run every indicator strategy in priority order; return first match."""
        self.logger.info("Running completion-indicator scan (check #%s)", check_count)  # Pre-action log
        lowered = all_raw_content.lower()  # Lower-cased copy used by every matcher
        result = self._check_generic(lowered, check_count)  # Try plain substring indicators first
        if result is None:  # Fall through if no generic match
            result = self._check_ping_statistics(lowered)  # Then ping summary fallback
        if result is None:  # Then service-ping pattern detection
            result = self._check_service_ping(lowered, collected_output, last_activity, check_count)
        if result is None:  # Then count-based service-ping completion
            result = self._check_count_based(lowered, collected_output, last_activity)
        if result is None:  # Then MAC-table specific completion
            result = self._check_mac_table(lowered, collected_output, last_activity, check_count)
        if result is None:  # Finally ARP structure detection
            result = self._check_arp_structure(lowered, collected_output, last_activity, check_count)
        self.logger.debug("Completion-indicator scan result=%s", result)  # Post-action log
        return result  # Either an indicator-name string or None

    def _check_generic(self, lowered: str, check_count: int) -> str | None:
        """Scan flat indicator list, skipping generic ones for MAC tables."""
        if self.debug_mode and check_count % 100 == 1:  # Periodic debug trace preserved verbatim
            self.logger.debug("Checking %s completion indicators", len(_ALL_INDICATORS))
            self.logger.debug("Content sample for indicator check: %s", repr(lowered[:150]))
            print(f"[DEBUG] Checking {len(_ALL_INDICATORS)} completion indicators")
            print(f"[DEBUG] Content sample for indicator check: {repr(lowered[:150])}")
        mac_mode = "ethernet switching table" in lowered  # MAC-table-specific filter flag
        for indicator in _ALL_INDICATORS:  # Iterate every known phrase
            if mac_mode and indicator in _MAC_TABLE_SKIP_INDICATORS:  # Skip generics for MAC tables
                continue
            if indicator in lowered:  # Substring match against the combined content
                if self.debug_mode:
                    self.logger.debug("FOUND completion indicator: '%s'", indicator)
                    print(f"[DEBUG] FOUND completion indicator: '{indicator}'")
                return indicator  # Return the matching phrase as the completion reason
        return None  # No generic indicator matched

    def _check_ping_statistics(self, lowered: str) -> str | None:
        """Detect ping completion via the 'packet loss' + round-trip/rtt block."""
        if "packet loss" not in lowered:  # Quick reject when no stats present
            return None
        has_summary = "round-trip" in lowered or "rtt" in lowered  # Summary line present
        if not has_summary:  # Require both packet loss and timing summary
            return None
        for line in lowered.split("\n"):  # Walk each line to locate the stats block
            if "packet loss" in line:  # Found the packet-loss line within the block
                if self.debug_mode:
                    self.logger.debug("FOUND ping statistics completion pattern")
                    self.logger.debug("Packet loss line: %s", repr(line[:100]))
                    print("[DEBUG] FOUND ping statistics completion pattern")
                    print(f"[DEBUG] Packet loss line: {repr(line[:100])}")
                return "complete statistics block"
        return None  # Defensive — line scan found nothing

    def _check_service_ping(
        self, lowered: str, collected_output: list[dict[str, Any]], last_activity: float, check_count: int
    ) -> str | None:
        """Detect SSR service-ping completion via seq/ttl/time patterns + idle."""
        if len(collected_output) < 3:  # Need a few responses before we trust the pattern
            return None
        pattern_count = self._count_service_ping_patterns(lowered)  # Count signal hits
        self._trace_service_ping(pattern_count, lowered, check_count)  # Periodic trace
        if pattern_count < 2:  # Both signals must be present
            return None
        idle = time.time() - last_activity  # Time since the last message arrived
        if idle <= 3:  # Need >3 s of silence to call it done
            return None
        if self.debug_mode:
            self.logger.debug("FOUND service ping completion: %s patterns detected", pattern_count)
            self.logger.debug("Service ping idle time: %.1fs", idle)
            print(f"[DEBUG] FOUND service ping completion: {pattern_count} patterns detected")
            print(f"[DEBUG] Service ping idle time: {idle:.1f}s")
        return "service ping pattern detected"

    @staticmethod
    def _count_service_ping_patterns(lowered: str) -> int:
        """Return the number of distinct service-ping signal categories present."""
        count = 0  # Accumulator for signal hits
        if "seq=" in lowered and ("ttl=" in lowered or "time=" in lowered):
            count += 1  # seq= combined with ttl=/time= is one signal
        if "bytes from" in lowered:
            count += 1  # 'bytes from' is the second signal
        return count

    def _trace_service_ping(self, pattern_count: int, lowered: str, check_count: int) -> None:
        """Emit the periodic service-ping debug trace preserved verbatim."""
        if not self.debug_mode or check_count % 200 != 1:
            return
        self.logger.debug("Service ping pattern analysis: found %s service ping indicators", pattern_count)
        print(f"[DEBUG] Service ping pattern analysis: found {pattern_count} service ping indicators")
        if "seq=" in lowered:
            self.logger.debug("Found seq= pattern in service ping output")
            print("[DEBUG] Found seq= pattern in service ping output")
        if "bytes from" in lowered:
            self.logger.debug("Found 'bytes from' pattern in service ping output")
            print("[DEBUG] Found 'bytes from' pattern in service ping output")

    def _check_count_based(
        self, lowered: str, collected_output: list[dict[str, Any]], last_activity: float
    ) -> str | None:
        """Count-based service-ping completion: many 'bytes from' lines + idle."""
        if len(collected_output) < 5:  # Need a reasonable number of responses first
            return None
        response_count = lowered.count("bytes from")  # How many ping responses arrived
        if response_count < 5:  # Threshold preserved from original logic
            return None
        idle = time.time() - last_activity  # Silence window
        if idle <= 2:  # Require >2 s of silence to declare done
            return None
        if self.debug_mode:
            self.logger.debug("FOUND count-based service ping completion: %s responses", response_count)
            self.logger.debug("Idle time since last response: %.1fs", idle)
            print(f"[DEBUG] FOUND count-based service ping completion: {response_count} responses")
            print(f"[DEBUG] Idle time since last response: {idle:.1f}s")
        return f"count-based completion ({response_count} responses)"

    def _check_mac_table(
        self,
        lowered: str,
        collected_output: list[dict[str, Any]],
        last_activity: float,
        check_count: int,
    ) -> str | None:
        """Detect MAC-learning-table completion via repeated tails or idle timeout."""
        if "ethernet switching table" not in lowered and "thernet switching table" not in lowered:
            return None  # Buffer is not a MAC-table dump
        match = re.search(r"ethernet switching table\s*:\s*(\d+)\s+entries", lowered)  # Entry-count line
        if match is None:  # Header line not yet received
            if self.debug_mode and check_count % 50 == 1:
                print(f"[DEBUG] MAC table: checking for completion pattern in {len(lowered)} chars")
            return None
        entry_count = int(match.group(1))  # Parsed entry count for diagnostics
        repeat_hit = self._mac_table_repeated_tail(collected_output)  # Last 5 messages identical?
        if repeat_hit is not None:
            return repeat_hit  # Repeated-tail strategy succeeded
        idle_hit = self._mac_table_idle_timeout(collected_output, last_activity, entry_count)
        if idle_hit is not None:
            return idle_hit  # Idle-timeout strategy succeeded
        if self.debug_mode and check_count % 50 == 1:
            idle = time.time() - last_activity
            print(f"[DEBUG] MAC table: found {entry_count} entries, idle for {idle:.1f}s")
        return None

    def _mac_table_repeated_tail(self, collected_output: list[dict[str, Any]]) -> str | None:
        """Return completion reason when the last 5 messages are identical."""
        if len(collected_output) < 5:  # Need at least 5 messages to compare
            return None
        last_messages = [msg.get("raw", "") for msg in collected_output[-5:]]  # Tail snapshot
        if len(set(last_messages)) != 1:  # Tail not uniform
            return None
        if not last_messages[0].strip():  # Skip if the repeated content is empty
            return None
        reason = f"mac table completion (detected {len(last_messages)} repeated identical messages)"
        if self.debug_mode:
            self.logger.debug("FOUND MAC table completion: %s repeated identical messages detected", len(last_messages))
            self.logger.debug("Repeated message: %s", repr(last_messages[0][:100]))
            print(f"[DEBUG] FOUND MAC table completion: {len(last_messages)} repeated identical messages detected")
            print(f"[DEBUG] Repeated message: {repr(last_messages[0][:100])}")
        return reason

    def _mac_table_idle_timeout(
        self,
        collected_output: list[dict[str, Any]],
        last_activity: float,
        entry_count: int,
    ) -> str | None:
        """Return completion reason when MAC table is large enough and gone quiet."""
        if len(collected_output) < 10 or entry_count < 10:  # Thresholds preserved from original
            return None
        idle_time = time.time() - last_activity  # Silence window in seconds
        if idle_time < 3.0:  # Require 3 s of silence for the idle strategy
            return None
        reason = f"mac table completion (idle timeout: {entry_count} entries, {idle_time:.1f}s idle)"
        if self.debug_mode:
            self.logger.debug(
                "FOUND MAC table completion via idle timeout: %s entries, %.1fs idle", entry_count, idle_time
            )
            print(f"[DEBUG] FOUND MAC table completion via idle timeout: {entry_count} entries, {idle_time:.1f}s idle")
        return reason

    def _check_arp_structure(
        self,
        lowered: str,
        collected_output: list[dict[str, Any]],
        last_activity: float,
        check_count: int,
    ) -> str | None:
        """Detect ARP-table completion via structural columns + brief idle window."""
        if len(collected_output) < 2:  # Need at least two segments
            return None
        arp_patterns = ["ip address", "hw address", "interface", "incomplete", "permanent"]  # Columns
        pattern_count = sum(1 for pattern in arp_patterns if pattern in lowered)  # Hits in buffer
        self._trace_arp_patterns(arp_patterns, pattern_count, lowered, check_count)  # Periodic trace
        if pattern_count < 2 or time.time() - last_activity <= 1:  # Need columns + silence
            return None
        if self.debug_mode:
            print(f"[DEBUG] FOUND ARP table completion: {pattern_count} patterns detected")
        return "arp table structure detected"

    def _trace_arp_patterns(self, arp_patterns: list[str], pattern_count: int, lowered: str, check_count: int) -> None:
        """Emit the periodic ARP-pattern debug trace preserved verbatim."""
        if not self.debug_mode or check_count % 200 != 1:
            return
        print(f"[DEBUG] ARP pattern analysis: found {pattern_count}/{len(arp_patterns)} patterns")
        found_patterns = [p for p in arp_patterns if p in lowered]
        print(f"[DEBUG] Found ARP patterns: {found_patterns}")
