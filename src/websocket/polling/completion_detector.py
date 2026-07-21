"""Detect command-completion signals in WebSocket output streams.

Splits the original 250+ line indicator-checking block from
WebSocketManager.wait_for_command_result into small per-pattern helpers
(generic, ping, service-ping, MAC table, ARP) each with CC <= 5.
"""

from __future__ import annotations  # WHY: PEP 604 typing on 3.10+.

import logging  # WHY: Emit trace lines through the shared manager logger.
import re  # WHY: Parse MAC-table entry count header.
import time  # WHY: Compute idle time since the last message arrived.
from collections.abc import Callable  # WHY: Ruff UP035 prefers collections.abc for Callable.
from typing import Any  # WHY: Generic message dict typing.

# Completion indicator vocabularies grouped by command family.
# Preserved verbatim from manager.wait_for_command_result so existing
# device output continues to be recognised.
_PING_INDICATORS = [
    "round-trip min/avg/max",
    "round-trip min/avg/max/stddev",
    "rtt min/avg/max",
]  # WHY: ping summary phrases.
_SERVICE_PING_INDICATORS = [  # WHY: SSR service-ping completion phrases.
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
_ARP_INDICATORS = [  # WHY: ARP/MAC-table summary phrases seen at end-of-output.
    "total mac entries",
    "total flows:",
    "mac-flow hi-water",
    "arp table",
    "no arp entries",
    "arp cache",
]
_GATEWAY_INDICATORS = [  # WHY: Junos gateway route-table completion phrases.
    "connected routes",
    "total entries",
    "kernel routes",
    "bgp routes",
    "static routes",
    "route table",
]
_SWITCH_INDICATORS = [  # WHY: Switch FDB/VLAN/port summary phrases.
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
_GENERAL_INDICATORS = ["command completed", "operation complete", "finished"]  # WHY: Generic Junos completion phrases.
_ALL_INDICATORS = (  # WHY: Combined lookup for the generic substring scan.
    _PING_INDICATORS
    + _SERVICE_PING_INDICATORS
    + _ARP_INDICATORS
    + _GATEWAY_INDICATORS
    + _SWITCH_INDICATORS
    + _GENERAL_INDICATORS
)
# Generic switch indicators that must be skipped when the buffer is a MAC table
# (because the MAC-table-specific logic produces a more accurate completion).
_MAC_TABLE_SKIP_INDICATORS = {
    "ethernet switching table",
    "entries,",
    "learned",
}  # WHY: Avoid premature completion on MAC dumps.

_SERVICE_PING_MIN_OUTPUTS = 3  # WHY: Wait for a few responses before trusting the pattern.
_SERVICE_PING_MIN_PATTERNS = 2  # WHY: Both seq/ttl and bytes-from signals required.
_SERVICE_PING_MIN_IDLE = 3  # WHY: Silence window that indicates ping finished.
_COUNT_BASED_MIN_OUTPUTS = 5  # WHY: Need enough segments to see repeated responses.
_COUNT_BASED_MIN_RESPONSES = 5  # WHY: Threshold preserved from original logic.
_COUNT_BASED_MIN_IDLE = 2  # WHY: Silence gap for count-based completion.
_MAC_TAIL_SIZE = 5  # WHY: Number of trailing messages compared for repetition.
_MAC_IDLE_MIN_MESSAGES = 10  # WHY: Threshold preserved from original logic.
_MAC_IDLE_MIN_ENTRIES = 10  # WHY: Only apply idle strategy for non-trivial tables.
_MAC_IDLE_MIN_SECONDS = 3.0  # WHY: Silence window declaring MAC dump complete.
_ARP_MIN_OUTPUTS = 2  # WHY: Need at least two segments before scoring columns.
_ARP_MIN_PATTERNS = 2  # WHY: Require multiple column hits to avoid false positives.
_ARP_MIN_IDLE = 1  # WHY: Very short silence window sufficient for ARP dumps.
_TRACE_PERIOD_GENERIC = 100  # WHY: Emit generic-indicator trace every N polls.
_TRACE_PERIOD_MAC = 50  # WHY: Emit MAC-table trace every N polls.
_TRACE_PERIOD_SERVICE = 200  # WHY: Emit service-ping/ARP traces every N polls.
_MAC_HEADER_RE = re.compile(r"ethernet switching table\s*:\s*(\d+)\s+entries")  # WHY: Extract entry count from header.
_ARP_COLUMN_PATTERNS = [
    "ip address",
    "hw address",
    "interface",
    "incomplete",
    "permanent",
]  # WHY: Structural columns of ARP dump.


class CompletionDetector:  # WHY: Bundles indicator matchers + shared logger/debug state.
    """Detect command-completion indicators in collected WebSocket output."""

    def __init__(self, logger: logging.Logger, debug_mode: bool) -> None:  # WHY: Wire logger + debug once.
        """Store the shared logger and debug flag used by every matcher."""
        self.logger = logger  # WHY: Shared manager logger for trace lines.
        self.debug_mode = debug_mode  # WHY: Gate verbose prints/log lines.
        self._mac_expected_entries: int | None = None  # WHY: Cache preserved from original API.

    def detect(  # WHY: Public entry point used by result_collector.
        self,
        collected_output: list[dict[str, Any]],
        all_raw_content: str,
        last_activity: float,
        check_count: int,
    ) -> str | None:
        """Run every indicator strategy in priority order; return first match."""
        self.logger.info("Running completion-indicator scan (check #%s)", check_count)  # WHY: Pre-action observability.
        lowered = all_raw_content.lower()  # WHY: Case-insensitive matching across all strategies.
        strategies = self._build_strategies(collected_output, last_activity, check_count)  # WHY: Ordered strategy list.
        result = self._run_strategies(strategies, lowered)  # WHY: Return first non-None match.
        self.logger.debug("Completion-indicator scan result=%s", result)  # WHY: Post-action observability.
        return result  # WHY: Either an indicator-name string or None.

    def _build_strategies(  # WHY: Materialise ordered matcher closures for the run loop.
        self,
        collected_output: list[dict[str, Any]],
        last_activity: float,
        check_count: int,
    ) -> list[Callable[[str], str | None]]:
        """Return the ordered list of matcher closures the detect loop iterates."""
        return [  # WHY: Order preserves original priority sequence.
            lambda lo: self._check_generic(lo, check_count),
            self._check_ping_statistics,
            lambda lo: self._check_service_ping(lo, collected_output, last_activity, check_count),
            lambda lo: self._check_count_based(lo, collected_output, last_activity),
            lambda lo: self._check_mac_table(lo, collected_output, last_activity, check_count),
            lambda lo: self._check_arp_structure(lo, collected_output, last_activity, check_count),
        ]

    @staticmethod
    def _run_strategies(  # WHY: Walker keeps detect() below the CC ceiling.
        strategies: list[Callable[[str], str | None]], lowered: str
    ) -> str | None:
        """Return the first non-None result from the ordered strategy callables."""
        for strategy in strategies:  # WHY: Priority order was defined by caller.
            hit = strategy(lowered)  # WHY: Delegate matching to per-family helper.
            if hit is not None:  # WHY: Short-circuit on the first successful match.
                return hit  # WHY: Propagate first matching indicator upward.
        return None  # WHY: No strategy matched the current buffer.

    def _check_generic(self, lowered: str, check_count: int) -> str | None:  # WHY: Generic-indicator matcher.
        """Scan flat indicator list, skipping generic ones for MAC tables."""
        self._trace_generic_scan(lowered, check_count)  # WHY: Periodic diagnostics preserved verbatim.
        mac_mode = "ethernet switching table" in lowered  # WHY: MAC-table filter flag for skip set.
        for indicator in _ALL_INDICATORS:  # WHY: Iterate every known completion phrase.
            if mac_mode and indicator in _MAC_TABLE_SKIP_INDICATORS:  # WHY: Skip generics on MAC tables.
                continue  # WHY: Defer to the MAC-table-specific strategy instead.
            if indicator in lowered:  # WHY: Substring match against combined content.
                self._log_generic_hit(indicator)  # WHY: Preserve debug trace on match.
                return indicator  # WHY: Return matching phrase as completion reason.
        return None  # WHY: No generic indicator matched.

    def _trace_generic_scan(self, lowered: str, check_count: int) -> None:  # WHY: Diagnostic-only helper.
        """Emit the periodic generic-scan debug trace preserved verbatim."""
        if not self.debug_mode or check_count % _TRACE_PERIOD_GENERIC != 1:  # WHY: Throttle noisy debug output.
            return  # WHY: Silent path when tracing gate is closed.
        self.logger.debug("Checking %s completion indicators", len(_ALL_INDICATORS))  # WHY: Log indicator count.
        self.logger.debug("Content sample for indicator check: %s", repr(lowered[:150]))  # WHY: Log sample buffer.

    def _log_generic_hit(self, indicator: str) -> None:  # WHY: Preserve original debug messaging on hit.
        """Emit debug trace when a generic indicator matches (verbatim)."""
        if not self.debug_mode:  # WHY: Guard preserves original silent path.
            return  # WHY: Silent path when debug is off.
        self.logger.debug("FOUND completion indicator: '%s'", indicator)  # WHY: Log match through logger.

    def _check_ping_statistics(self, lowered: str) -> str | None:  # WHY: Ping-statistics matcher.
        """Detect ping completion via the 'packet loss' + round-trip/rtt block."""
        if "packet loss" not in lowered:  # WHY: Quick reject when no stats present.
            return None  # WHY: Buffer does not contain the summary line yet.
        if "round-trip" not in lowered and "rtt" not in lowered:  # WHY: Require the summary line too.
            return None  # WHY: Neither round-trip nor rtt phrase seen yet.
        line = self._find_packet_loss_line(lowered)  # WHY: Locate the stats block via line scan.
        if line is None:  # WHY: Defensive — text moved between calls.
            return None  # WHY: Line scan found nothing to report.
        self._log_ping_hit(line)  # WHY: Preserve verbatim debug output.
        return "complete statistics block"  # WHY: Signal ping completion by canonical reason string.

    @staticmethod
    def _find_packet_loss_line(lowered: str) -> str | None:  # WHY: Isolates line-walking for testability.
        """Return the first line containing 'packet loss', or None."""
        for line in lowered.split("\n"):  # WHY: Walk lines to isolate the stats block.
            if "packet loss" in line:  # WHY: Match the specific summary line.
                return line  # WHY: Caller uses this line for the debug trace.
        return None  # WHY: Line scan found nothing.

    def _log_ping_hit(self, line: str) -> None:  # WHY: Preserve original debug messaging on hit.
        """Emit debug trace when ping-completion pattern matches (verbatim)."""
        if not self.debug_mode:  # WHY: Guard preserves original silent path.
            return  # WHY: Silent path when debug is off.
        self.logger.debug("FOUND ping statistics completion pattern")  # WHY: Log detection through logger.
        self.logger.debug("Packet loss line: %s", repr(line[:100]))  # WHY: Include sample of matched line.

    def _check_service_ping(  # WHY: SSR service-ping matcher composed of pattern + idle checks.
        self,
        lowered: str,
        collected_output: list[dict[str, Any]],
        last_activity: float,
        check_count: int,
    ) -> str | None:
        """Detect SSR service-ping completion via seq/ttl/time patterns + idle."""
        if len(collected_output) < _SERVICE_PING_MIN_OUTPUTS:  # WHY: Wait for a few responses.
            return None  # WHY: Not enough segments to score yet.
        pattern_count = self._count_service_ping_patterns(lowered)  # WHY: Score signal categories present.
        self._trace_service_ping(pattern_count, lowered, check_count)  # WHY: Periodic diagnostics.
        if pattern_count < _SERVICE_PING_MIN_PATTERNS:  # WHY: Require both signals.
            return None  # WHY: Signal threshold not yet met.
        idle = time.time() - last_activity  # WHY: Silence window since last message.
        if idle <= _SERVICE_PING_MIN_IDLE:  # WHY: Need meaningful silence to declare done.
            return None  # WHY: Buffer still receiving data.
        self._log_service_ping_hit(pattern_count, idle)  # WHY: Preserve verbatim debug output.
        return "service ping pattern detected"  # WHY: Canonical reason string preserved.

    @staticmethod
    def _count_service_ping_patterns(lowered: str) -> int:  # WHY: Isolates signal counting for tests.
        """Return the number of distinct service-ping signal categories present."""
        count = 0  # WHY: Accumulator for signal hits.
        if "seq=" in lowered and ("ttl=" in lowered or "time=" in lowered):  # WHY: First signal group.
            count += 1  # WHY: Register first-signal-category hit.
        if "bytes from" in lowered:  # WHY: Second independent signal.
            count += 1  # WHY: Register second-signal-category hit.
        return count  # WHY: Caller thresholds against MIN_PATTERNS.

    def _trace_service_ping(  # WHY: Diagnostic-only helper.
        self, pattern_count: int, lowered: str, check_count: int
    ) -> None:
        """Emit the periodic service-ping debug trace preserved verbatim."""
        if not self.debug_mode or check_count % _TRACE_PERIOD_SERVICE != 1:  # WHY: Throttle noisy output.
            return  # WHY: Silent path when tracing gate is closed.
        self.logger.debug("Service ping pattern analysis: found %s service ping indicators", pattern_count)
        if "seq=" in lowered:  # WHY: Diagnostic — surface which signal fired.
            self.logger.debug("Found seq= pattern in service ping output")
        if "bytes from" in lowered:  # WHY: Diagnostic — surface which signal fired.
            self.logger.debug("Found 'bytes from' pattern in service ping output")

    def _log_service_ping_hit(self, pattern_count: int, idle: float) -> None:  # WHY: Preserve original debug messaging.
        """Emit debug trace when service-ping completion matches (verbatim)."""
        if not self.debug_mode:  # WHY: Guard preserves original silent path.
            return  # WHY: Silent path when debug is off.
        self.logger.debug("FOUND service ping completion: %s patterns detected", pattern_count)
        self.logger.debug("Service ping idle time: %.1fs", idle)

    def _check_count_based(  # WHY: Count-based service-ping fallback matcher.
        self,
        lowered: str,
        collected_output: list[dict[str, Any]],
        last_activity: float,
    ) -> str | None:
        """Count-based service-ping completion: many 'bytes from' lines + idle."""
        if len(collected_output) < _COUNT_BASED_MIN_OUTPUTS:  # WHY: Need a reasonable number of segments.
            return None  # WHY: Not enough segments to score yet.
        response_count = lowered.count("bytes from")  # WHY: Count ping responses observed.
        if response_count < _COUNT_BASED_MIN_RESPONSES:  # WHY: Threshold preserved from original logic.
            return None  # WHY: Response count under threshold.
        idle = time.time() - last_activity  # WHY: Silence window since last message.
        if idle <= _COUNT_BASED_MIN_IDLE:  # WHY: Need meaningful silence to declare done.
            return None  # WHY: Buffer still receiving data.
        self._log_count_based_hit(response_count, idle)  # WHY: Preserve verbatim debug output.
        return f"count-based completion ({response_count} responses)"  # WHY: Canonical reason string preserved.

    def _log_count_based_hit(self, response_count: int, idle: float) -> None:  # WHY: Preserve original debug messaging.
        """Emit debug trace when count-based completion matches (verbatim)."""
        if not self.debug_mode:  # WHY: Guard preserves original silent path.
            return  # WHY: Silent path when debug is off.
        self.logger.debug("FOUND count-based service ping completion: %s responses", response_count)
        self.logger.debug("Idle time since last response: %.1fs", idle)

    def _check_mac_table(  # WHY: MAC-learning-table matcher combines header parse + tail/idle strategies.
        self,
        lowered: str,
        collected_output: list[dict[str, Any]],
        last_activity: float,
        check_count: int,
    ) -> str | None:
        """Detect MAC-learning-table completion via repeated tails or idle timeout."""
        if not self._is_mac_table_buffer(lowered):  # WHY: Fast reject on non-MAC-table content.
            return None  # WHY: Buffer is not a MAC-table dump.
        entry_count = self._parse_mac_entry_count(lowered, check_count)  # WHY: Header parse or diagnostic.
        if entry_count is None:  # WHY: Header not yet received.
            return None  # WHY: Cannot score MAC completion without entry count.
        return self._try_mac_completion_strategies(collected_output, last_activity, entry_count, check_count)

    @staticmethod
    def _is_mac_table_buffer(lowered: str) -> bool:  # WHY: Header sniff with truncation tolerance.
        """Return True when the buffer looks like a MAC-learning-table dump."""
        return (
            "ethernet switching table" in lowered or "thernet switching table" in lowered
        )  # WHY: Tolerate leading truncation.

    def _parse_mac_entry_count(self, lowered: str, check_count: int) -> int | None:  # WHY: Header parser + trace.
        """Return the parsed MAC entry count or None (emitting periodic trace)."""
        match = _MAC_HEADER_RE.search(lowered)  # WHY: Extract entry count from header.
        if match is None:  # WHY: Header line not yet received.
            self._trace_mac_missing_header(lowered, check_count)  # WHY: Periodic diagnostic.
            return None  # WHY: Cannot score without entry count.
        return int(match.group(1))  # WHY: Numeric entry count for downstream thresholds.

    def _try_mac_completion_strategies(  # WHY: Ordered dispatch across MAC strategies.
        self,
        collected_output: list[dict[str, Any]],
        last_activity: float,
        entry_count: int,
        check_count: int,
    ) -> str | None:
        """Run repeated-tail then idle-timeout MAC-table strategies in order."""
        repeat_hit = self._mac_table_repeated_tail(collected_output)  # WHY: Prefer tail-repetition detection.
        if repeat_hit is not None:  # WHY: Short-circuit on success.
            return repeat_hit  # WHY: Propagate canonical reason string.
        idle_hit = self._mac_table_idle_timeout(collected_output, last_activity, entry_count)  # WHY: Fallback strategy.
        if idle_hit is not None:  # WHY: Short-circuit on success.
            return idle_hit  # WHY: Propagate canonical reason string.
        self._trace_mac_idle_pending(last_activity, entry_count, check_count)  # WHY: Periodic diagnostic.
        return None  # WHY: No MAC strategy matched.

    def _trace_mac_missing_header(self, lowered: str, check_count: int) -> None:  # WHY: Diagnostic-only helper.
        """Emit periodic trace while waiting for MAC-table header (verbatim)."""
        if self.debug_mode and check_count % _TRACE_PERIOD_MAC == 1:  # WHY: Throttle noisy output.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            self.logger.debug("MAC table: checking for completion pattern in %s chars", len(lowered))

    def _trace_mac_idle_pending(  # WHY: Diagnostic-only helper.
        self, last_activity: float, entry_count: int, check_count: int
    ) -> None:
        """Emit periodic trace while waiting for MAC-table idle timeout (verbatim)."""
        if self.debug_mode and check_count % _TRACE_PERIOD_MAC == 1:  # WHY: Throttle noisy output.
            idle = time.time() - last_activity  # WHY: Diagnostic idle window.
            # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
            self.logger.debug("MAC table: found %s entries, idle for %.1fs", entry_count, idle)

    def _mac_table_repeated_tail(self, collected_output: list[dict[str, Any]]) -> str | None:  # WHY: Tail-repetition.
        """Return completion reason when the last 5 messages are identical."""
        last_messages = self._collect_tail_messages(collected_output)  # WHY: Snapshot the trailing messages.
        if last_messages is None:  # WHY: Not enough messages or tail not uniform.
            return None  # WHY: Tail did not meet repetition criteria.
        reason = f"mac table completion (detected {len(last_messages)} repeated identical messages)"  # WHY: Canonical.
        self._log_mac_repeat_hit(last_messages)  # WHY: Preserve verbatim debug output.
        return reason  # WHY: Return canonical completion reason.

    @staticmethod
    def _collect_tail_messages(  # WHY: Isolates tail-uniformity check for tests.
        collected_output: list[dict[str, Any]],
    ) -> list[str] | None:
        """Return the trailing MAC tail if it is uniform and non-empty, else None."""
        if len(collected_output) < _MAC_TAIL_SIZE:  # WHY: Need at least the tail size to compare.
            return None  # WHY: Not enough segments to form a tail.
        tail = [msg.get("raw", "") for msg in collected_output[-_MAC_TAIL_SIZE:]]  # WHY: Slice trailing messages.
        if len(set(tail)) != 1:  # WHY: Tail must be uniform to declare completion.
            return None  # WHY: Tail differs, keep waiting.
        if not tail[0].strip():  # WHY: Skip when the repeated content is empty whitespace.
            return None  # WHY: Blank tail is not a real completion signal.
        return tail  # WHY: Caller uses length + first element for logging.

    def _log_mac_repeat_hit(self, last_messages: list[str]) -> None:  # WHY: Preserve original debug messaging.
        """Emit debug trace when MAC-table repeated-tail matches (verbatim)."""
        if not self.debug_mode:  # WHY: Guard preserves original silent path.
            return  # WHY: Silent path when debug is off.
        self.logger.debug("FOUND MAC table completion: %s repeated identical messages detected", len(last_messages))
        self.logger.debug("Repeated message: %s", repr(last_messages[0][:100]))

    def _mac_table_idle_timeout(  # WHY: Idle-based fallback for large MAC dumps.
        self,
        collected_output: list[dict[str, Any]],
        last_activity: float,
        entry_count: int,
    ) -> str | None:
        """Return completion reason when MAC table is large enough and gone quiet."""
        if len(collected_output) < _MAC_IDLE_MIN_MESSAGES or entry_count < _MAC_IDLE_MIN_ENTRIES:
            return None  # WHY: Thresholds preserved from original logic.
        idle_time = time.time() - last_activity  # WHY: Silence window in seconds.
        if idle_time < _MAC_IDLE_MIN_SECONDS:  # WHY: Require enough silence for the idle strategy.
            return None  # WHY: Buffer still receiving data.
        reason = f"mac table completion (idle timeout: {entry_count} entries, {idle_time:.1f}s idle)"  # WHY: Canonical.
        self._log_mac_idle_hit(entry_count, idle_time)  # WHY: Preserve verbatim debug output.
        return reason  # WHY: Return canonical completion reason.

    def _log_mac_idle_hit(self, entry_count: int, idle_time: float) -> None:  # WHY: Preserve original debug messaging.
        """Emit debug trace when MAC-table idle-timeout matches (verbatim)."""
        if not self.debug_mode:  # WHY: Guard preserves original silent path.
            return  # WHY: Silent path when debug is off.
        self.logger.debug("FOUND MAC table completion via idle timeout: %s entries, %.1fs idle", entry_count, idle_time)

    def _check_arp_structure(  # WHY: ARP structural-column matcher with idle gate.
        self,
        lowered: str,
        collected_output: list[dict[str, Any]],
        last_activity: float,
        check_count: int,
    ) -> str | None:
        """Detect ARP-table completion via structural columns + brief idle window."""
        if len(collected_output) < _ARP_MIN_OUTPUTS:  # WHY: Need at least two segments to score.
            return None  # WHY: Not enough segments to score yet.
        pattern_count = self._count_arp_patterns(lowered)  # WHY: Column-hit tally extracted for CC budget.
        self._trace_arp_patterns(pattern_count, lowered, check_count)  # WHY: Periodic diagnostics.
        if pattern_count < _ARP_MIN_PATTERNS:  # WHY: Require multiple columns to reduce false positives.
            return None  # WHY: Column threshold not met.
        if time.time() - last_activity <= _ARP_MIN_IDLE:  # WHY: Need brief silence window too.
            return None  # WHY: Buffer still receiving data.
        self._log_arp_hit(pattern_count)  # WHY: Preserve verbatim debug output.
        return "arp table structure detected"  # WHY: Canonical reason string preserved.

    @staticmethod
    def _count_arp_patterns(lowered: str) -> int:  # WHY: Isolates column-count so caller stays under CC ceiling.
        """Return the number of ARP column patterns present in the buffer."""
        return sum(1 for pattern in _ARP_COLUMN_PATTERNS if pattern in lowered)  # WHY: Column hits in buffer.

    def _trace_arp_patterns(  # WHY: Diagnostic-only helper.
        self, pattern_count: int, lowered: str, check_count: int
    ) -> None:
        """Emit the periodic ARP-pattern debug trace preserved verbatim."""
        if not self.debug_mode or check_count % _TRACE_PERIOD_SERVICE != 1:  # WHY: Throttle noisy output.
            return  # WHY: Silent path when tracing gate is closed.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        self.logger.debug("ARP pattern analysis: found %s/%s patterns", pattern_count, len(_ARP_COLUMN_PATTERNS))
        found_patterns = [p for p in _ARP_COLUMN_PATTERNS if p in lowered]  # WHY: Surface which columns matched.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        self.logger.debug("Found ARP patterns: %s", found_patterns)

    def _log_arp_hit(self, pattern_count: int) -> None:  # WHY: Preserve original debug messaging.
        """Emit debug trace when ARP-structure completion matches (verbatim)."""
        if not self.debug_mode:  # WHY: Guard preserves original silent path.
            return  # WHY: Silent path when debug is off.
        # WHY: preserve operator notice verbatim; route through logger for capture/redirection.
        self.logger.debug("FOUND ARP table completion: %s patterns detected", pattern_count)
