"""Unit tests for the WebSocket CompletionDetector.

Covers src/websocket/polling/completion_detector.py: the six-strategy priority
chain (generic → ping-stats → service-ping → count-based → MAC-table →
ARP-structure), plus every trace/log helper gated by ``debug_mode`` and the
periodic ``check_count`` modulos. The detector is the sole authority that
decides "did the device stop talking?", so silent regressions here manifest as
hangs or premature completions in production polling. These tests pin each
branch (threshold met vs not, idle window met vs not, header parsed vs not,
tail uniform vs not) so refactors of the strategy chain cannot change the
observable contract.
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import patch

from src.websocket.polling import completion_detector as cd_mod
from src.websocket.polling.completion_detector import CompletionDetector


def _make_detector(debug: bool = False) -> CompletionDetector:
    """Return a CompletionDetector wired with a stdlib logger + debug flag."""
    return CompletionDetector(logging.getLogger("test.completion_detector"), debug)


def _seg(raw: str) -> dict[str, Any]:
    """Return a minimal collected_output segment carrying a raw string."""
    return {"raw": raw}


# ---------------------------------------------------------------------------
# __init__ + detect (integration)
# ---------------------------------------------------------------------------


def test_init_stores_logger_debug_and_default_cache() -> None:
    """Constructor stores logger + debug flag and initialises MAC entry cache to None."""
    logger = logging.getLogger("x")
    det = CompletionDetector(logger, True)
    assert det.logger is logger
    assert det.debug_mode is True
    assert det._mac_expected_entries is None


def test_detect_returns_first_matching_strategy(caplog) -> None:
    """detect() returns the first non-None strategy result (generic indicator wins first)."""
    det = _make_detector()
    caplog.set_level(logging.DEBUG, logger="test.completion_detector")
    # "command completed" is a _GENERAL_INDICATOR → first strategy hits.
    result = det.detect([], "some text: command completed", last_activity=0.0, check_count=1)
    assert result == "command completed"


def test_detect_returns_none_when_no_strategy_matches() -> None:
    """detect() returns None when no strategy scores a hit."""
    det = _make_detector()
    assert det.detect([], "nothing to see", last_activity=0.0, check_count=1) is None


# ---------------------------------------------------------------------------
# _build_strategies / _run_strategies
# ---------------------------------------------------------------------------


def test_build_strategies_returns_six_callables() -> None:
    """_build_strategies returns the six ordered matcher closures."""
    det = _make_detector()
    strategies = det._build_strategies([], last_activity=0.0, check_count=1)
    assert len(strategies) == 6
    for strategy in strategies:
        assert callable(strategy)


def test_run_strategies_short_circuits_on_first_hit() -> None:
    """_run_strategies returns the first non-None hit and does not call later strategies."""
    called: list[str] = []

    def a(_: str) -> str | None:
        called.append("a")
        return None

    def b(_: str) -> str | None:
        called.append("b")
        return "hit"

    def c(_: str) -> str | None:
        called.append("c")
        return "not reached"

    assert CompletionDetector._run_strategies([a, b, c], "buffer") == "hit"
    assert called == ["a", "b"]


def test_run_strategies_returns_none_when_all_miss() -> None:
    """_run_strategies returns None if every strategy returns None."""
    assert CompletionDetector._run_strategies([lambda _: None, lambda _: None], "buf") is None


# ---------------------------------------------------------------------------
# _check_generic + trace/log helpers
# ---------------------------------------------------------------------------


def test_check_generic_hits_on_indicator() -> None:
    """Any indicator string present in the buffer is returned verbatim."""
    det = _make_detector()
    assert det._check_generic("... finished ...", check_count=1) == "finished"


def test_check_generic_skips_generic_when_mac_mode() -> None:
    """When the buffer looks like a MAC table, generic MAC-related indicators are skipped."""
    det = _make_detector()
    # "learned" and "entries," would normally hit, but "ethernet switching table"
    # triggers mac_mode → all three are in _MAC_TABLE_SKIP_INDICATORS → skipped.
    # No other _SWITCH_INDICATORS entry (e.g. "entries, 40 learned") is present here.
    text = "ethernet switching table has some entries, X learned"
    assert det._check_generic(text, check_count=1) is None


def test_check_generic_returns_none_when_nothing_matches() -> None:
    """No indicator hit → returns None."""
    det = _make_detector()
    assert det._check_generic("plain buffer", check_count=1) is None


def test_trace_generic_scan_silent_when_debug_off(capsys) -> None:
    """Debug OFF → no stdout trace even when the modulo would fire."""
    det = _make_detector(debug=False)
    det._trace_generic_scan("buf", check_count=1)
    assert capsys.readouterr().out == ""


def test_trace_generic_scan_silent_when_modulo_off(capsys) -> None:
    """Debug ON but check_count % 100 != 1 → no trace."""
    det = _make_detector(debug=True)
    det._trace_generic_scan("buf", check_count=2)
    assert capsys.readouterr().out == ""


def test_trace_generic_scan_prints_when_debug_and_modulo(capsys) -> None:
    """Debug ON + check_count % 100 == 1 → indicator count + sample printed."""
    det = _make_detector(debug=True)
    det._trace_generic_scan("sample-buf-here", check_count=1)
    out = capsys.readouterr().out
    assert "Checking" in out and "completion indicators" in out
    assert "Content sample" in out
    assert "sample-buf-here" in out


def test_log_generic_hit_silent_when_debug_off(capsys) -> None:
    """Debug OFF → _log_generic_hit prints nothing."""
    _make_detector(debug=False)._log_generic_hit("finished")
    assert capsys.readouterr().out == ""


def test_log_generic_hit_prints_when_debug_on(capsys) -> None:
    """Debug ON → indicator name is echoed to stdout."""
    _make_detector(debug=True)._log_generic_hit("finished")
    assert "FOUND completion indicator: 'finished'" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# _check_ping_statistics + helpers
# ---------------------------------------------------------------------------


def test_check_ping_statistics_returns_none_without_packet_loss() -> None:
    """Buffer without 'packet loss' → early return None."""
    assert _make_detector()._check_ping_statistics("round-trip 1/2/3") is None


def test_check_ping_statistics_returns_none_without_rtt_or_roundtrip() -> None:
    """Buffer with 'packet loss' but no round-trip/rtt phrase → None."""
    assert _make_detector()._check_ping_statistics("0% packet loss") is None


def test_check_ping_statistics_hits_when_both_present_roundtrip() -> None:
    """packet loss + round-trip → returns canonical reason string."""
    text = "0% packet loss\nround-trip min/avg/max = 1/2/3"
    assert _make_detector()._check_ping_statistics(text) == "complete statistics block"


def test_check_ping_statistics_hits_when_both_present_rtt() -> None:
    """packet loss + rtt → returns canonical reason string."""
    text = "0% packet loss\nrtt min/avg/max = 1/2/3"
    assert _make_detector()._check_ping_statistics(text) == "complete statistics block"


def test_check_ping_statistics_returns_none_when_line_missing(monkeypatch) -> None:
    """Defensive branch: _find_packet_loss_line returns None → returns None."""
    monkeypatch.setattr(CompletionDetector, "_find_packet_loss_line", staticmethod(lambda _: None))
    text = "packet loss round-trip"
    assert _make_detector()._check_ping_statistics(text) is None


def test_find_packet_loss_line_returns_matching_line() -> None:
    """Line containing 'packet loss' is returned verbatim (first match)."""
    text = "hdr\nno match here\n5% packet loss detected\nanother line"
    assert CompletionDetector._find_packet_loss_line(text) == "5% packet loss detected"


def test_find_packet_loss_line_returns_none_when_absent() -> None:
    """No matching line → None."""
    assert CompletionDetector._find_packet_loss_line("nothing\nrelevant") is None


def test_log_ping_hit_silent_when_debug_off(capsys) -> None:
    """Debug OFF → no ping-hit trace."""
    _make_detector(debug=False)._log_ping_hit("some line")
    assert capsys.readouterr().out == ""


def test_log_ping_hit_prints_when_debug_on(capsys) -> None:
    """Debug ON → pattern-hit + sample line printed."""
    _make_detector(debug=True)._log_ping_hit("some line")
    out = capsys.readouterr().out
    assert "FOUND ping statistics completion pattern" in out
    assert "Packet loss line" in out


# ---------------------------------------------------------------------------
# _check_service_ping + helpers
# ---------------------------------------------------------------------------


def test_check_service_ping_returns_none_when_too_few_outputs() -> None:
    """Fewer than _SERVICE_PING_MIN_OUTPUTS segments → None."""
    det = _make_detector()
    assert det._check_service_ping("seq=1 ttl=64 bytes from x", [_seg("a")], 0.0, 1) is None


def test_check_service_ping_returns_none_when_patterns_below_threshold() -> None:
    """Not enough distinct signal categories → None."""
    det = _make_detector()
    # Only "bytes from" (one pattern), no seq+ttl/time → count == 1 < 2.
    outputs = [_seg("x"), _seg("y"), _seg("z")]
    assert det._check_service_ping("bytes from host", outputs, 0.0, 1) is None


def test_check_service_ping_returns_none_when_idle_too_short() -> None:
    """Patterns present but idle window too short → None."""
    det = _make_detector()
    outputs = [_seg("a"), _seg("b"), _seg("c")]
    text = "seq=1 ttl=64 bytes from host"
    with patch.object(cd_mod.time, "time", return_value=100.0):
        # Idle == 0.0 → not > 3.0 → miss.
        assert det._check_service_ping(text, outputs, last_activity=100.0, check_count=1) is None


def test_check_service_ping_hits_when_all_conditions_met() -> None:
    """3+ outputs + both signals + idle > 3s → canonical reason string."""
    det = _make_detector()
    outputs = [_seg("a"), _seg("b"), _seg("c")]
    text = "seq=1 ttl=64 bytes from host"
    with patch.object(cd_mod.time, "time", return_value=200.0):
        got = det._check_service_ping(text, outputs, last_activity=100.0, check_count=1)
    assert got == "service ping pattern detected"


def test_count_service_ping_patterns_zero_when_none_present() -> None:
    """No matching phrases → count 0."""
    assert CompletionDetector._count_service_ping_patterns("plain") == 0


def test_count_service_ping_patterns_seq_ttl_only() -> None:
    """seq= + ttl= → 1 signal category."""
    assert CompletionDetector._count_service_ping_patterns("seq=1 ttl=64") == 1


def test_count_service_ping_patterns_seq_time_only() -> None:
    """seq= + time= → 1 signal category (time= is alt for ttl=)."""
    assert CompletionDetector._count_service_ping_patterns("seq=1 time=0.5") == 1


def test_count_service_ping_patterns_seq_without_ttl_or_time_is_zero() -> None:
    """seq= alone (no ttl/time) → no first-category hit."""
    assert CompletionDetector._count_service_ping_patterns("seq=1 alone") == 0


def test_count_service_ping_patterns_both_categories() -> None:
    """seq+ttl AND bytes-from → count 2."""
    assert CompletionDetector._count_service_ping_patterns("seq=1 ttl=64 bytes from host") == 2


def test_trace_service_ping_silent_when_debug_off(capsys) -> None:
    """Debug OFF → no service-ping trace."""
    _make_detector(debug=False)._trace_service_ping(2, "seq=1", check_count=1)
    assert capsys.readouterr().out == ""


def test_trace_service_ping_silent_when_modulo_off(capsys) -> None:
    """Debug ON but check_count % 200 != 1 → no trace."""
    _make_detector(debug=True)._trace_service_ping(2, "seq=1", check_count=2)
    assert capsys.readouterr().out == ""


def test_trace_service_ping_prints_when_debug_and_modulo_and_seq(capsys) -> None:
    """Debug ON + modulo hit + seq= present → seq= trace printed."""
    _make_detector(debug=True)._trace_service_ping(2, "seq=1 ttl=64", check_count=1)
    out = capsys.readouterr().out
    assert "Service ping pattern analysis" in out
    assert "Found seq= pattern" in out


def test_trace_service_ping_prints_bytes_from(capsys) -> None:
    """Debug ON + modulo hit + bytes from present → bytes-from trace printed."""
    _make_detector(debug=True)._trace_service_ping(1, "bytes from host", check_count=1)
    out = capsys.readouterr().out
    assert "Found 'bytes from' pattern" in out


def test_log_service_ping_hit_silent_when_debug_off(capsys) -> None:
    """Debug OFF → no service-ping hit trace."""
    _make_detector(debug=False)._log_service_ping_hit(2, 3.5)
    assert capsys.readouterr().out == ""


def test_log_service_ping_hit_prints_when_debug_on(capsys) -> None:
    """Debug ON → pattern count + idle time printed."""
    _make_detector(debug=True)._log_service_ping_hit(2, 3.5)
    out = capsys.readouterr().out
    assert "FOUND service ping completion" in out
    assert "3.5s" in out


# ---------------------------------------------------------------------------
# _check_count_based + log helper
# ---------------------------------------------------------------------------


def test_check_count_based_returns_none_when_too_few_outputs() -> None:
    """Fewer than _COUNT_BASED_MIN_OUTPUTS segments → None."""
    det = _make_detector()
    assert det._check_count_based("bytes from x", [_seg("a")] * 2, 0.0) is None


def test_check_count_based_returns_none_when_too_few_responses() -> None:
    """Under _COUNT_BASED_MIN_RESPONSES 'bytes from' occurrences → None."""
    det = _make_detector()
    outputs = [_seg("a")] * 5
    # Only 4 responses, below threshold of 5.
    text = "bytes from " * 4
    assert det._check_count_based(text, outputs, 0.0) is None


def test_check_count_based_returns_none_when_idle_too_short() -> None:
    """Meets output/response thresholds but idle window too short → None."""
    det = _make_detector()
    outputs = [_seg("a")] * 5
    text = "bytes from " * 5
    with patch.object(cd_mod.time, "time", return_value=100.0):
        # Idle == 0.0 → not > 2 → miss.
        assert det._check_count_based(text, outputs, last_activity=100.0) is None


def test_check_count_based_hits_when_all_conditions_met() -> None:
    """5+ outputs, 5+ 'bytes from', idle > 2s → canonical reason with count."""
    det = _make_detector()
    outputs = [_seg("a")] * 5
    text = "bytes from " * 5
    with patch.object(cd_mod.time, "time", return_value=200.0):
        got = det._check_count_based(text, outputs, last_activity=100.0)
    assert got == "count-based completion (5 responses)"


def test_log_count_based_hit_silent_when_debug_off(capsys) -> None:
    """Debug OFF → no count-based-hit trace."""
    _make_detector(debug=False)._log_count_based_hit(5, 2.5)
    assert capsys.readouterr().out == ""


def test_log_count_based_hit_prints_when_debug_on(capsys) -> None:
    """Debug ON → response count + idle time printed."""
    _make_detector(debug=True)._log_count_based_hit(5, 2.5)
    out = capsys.readouterr().out
    assert "FOUND count-based service ping completion" in out
    assert "5 responses" in out
    assert "2.5s" in out


# ---------------------------------------------------------------------------
# _check_mac_table + subhelpers
# ---------------------------------------------------------------------------


def test_check_mac_table_returns_none_when_not_mac_buffer() -> None:
    """Non-MAC-table content → early return None."""
    det = _make_detector()
    assert det._check_mac_table("plain", [], 0.0, check_count=1) is None


def test_check_mac_table_returns_none_when_header_missing() -> None:
    """MAC-table content but no entry-count header → None (header parser returns None)."""
    det = _make_detector()
    text = "ethernet switching table but no header line"
    assert det._check_mac_table(text, [], 0.0, check_count=1) is None


def test_check_mac_table_dispatches_to_strategies_when_header_present() -> None:
    """MAC content + header parses → delegates to _try_mac_completion_strategies."""
    det = _make_detector()
    text = "ethernet switching table: 40 entries, blah"
    outputs = [_seg("row")] * 5  # Uniform tail of 5 → repeated-tail strategy hits.
    got = det._check_mac_table(text, outputs, 0.0, check_count=1)
    assert got is not None and "mac table completion" in got


def test_is_mac_table_buffer_direct_header() -> None:
    """'ethernet switching table' → True."""
    assert CompletionDetector._is_mac_table_buffer("ethernet switching table x") is True


def test_is_mac_table_buffer_truncated_header() -> None:
    """Leading-truncated 'thernet switching table' → True (tolerated)."""
    assert CompletionDetector._is_mac_table_buffer("thernet switching table x") is True


def test_is_mac_table_buffer_false_when_absent() -> None:
    """Neither variant present → False."""
    assert CompletionDetector._is_mac_table_buffer("nothing") is False


def test_parse_mac_entry_count_returns_int_when_header_matches() -> None:
    """Header matches regex → integer entry count returned."""
    det = _make_detector()
    assert det._parse_mac_entry_count("ethernet switching table: 42 entries", 1) == 42


def test_parse_mac_entry_count_returns_none_when_header_missing() -> None:
    """No header line → None."""
    det = _make_detector()
    assert det._parse_mac_entry_count("ethernet switching table", 1) is None


def test_try_mac_completion_strategies_returns_repeat_hit_first() -> None:
    """Uniform 5-message tail → repeated-tail strategy short-circuits idle strategy."""
    det = _make_detector()
    outputs = [_seg("row")] * 5
    got = det._try_mac_completion_strategies(outputs, 0.0, entry_count=40, check_count=1)
    assert got is not None and "repeated identical messages" in got


def test_try_mac_completion_strategies_falls_through_to_idle() -> None:
    """No uniform tail but enough entries + idle → idle-timeout strategy hits."""
    det = _make_detector()
    outputs = [_seg(f"row-{i}") for i in range(10)]  # 10 non-uniform messages.
    with patch.object(cd_mod.time, "time", return_value=200.0):
        got = det._try_mac_completion_strategies(outputs, last_activity=100.0, entry_count=15, check_count=1)
    assert got is not None and "idle timeout" in got


def test_try_mac_completion_strategies_returns_none_when_all_miss() -> None:
    """Non-uniform tail + entry count below idle-threshold → None."""
    det = _make_detector()
    outputs = [_seg(f"row-{i}") for i in range(5)]
    with patch.object(cd_mod.time, "time", return_value=100.0):
        # entry_count 5 < 10 → idle miss; tail non-uniform → repeat miss.
        assert det._try_mac_completion_strategies(outputs, 0.0, entry_count=5, check_count=1) is None


def test_trace_mac_missing_header_silent_when_debug_off(capsys) -> None:
    """Debug OFF → no missing-header trace."""
    _make_detector(debug=False)._trace_mac_missing_header("buf", check_count=1)
    assert capsys.readouterr().out == ""


def test_trace_mac_missing_header_silent_when_modulo_off(capsys) -> None:
    """Debug ON but check_count % 50 != 1 → no trace."""
    _make_detector(debug=True)._trace_mac_missing_header("buf", check_count=2)
    assert capsys.readouterr().out == ""


def test_trace_mac_missing_header_prints_when_debug_and_modulo(capsys) -> None:
    """Debug ON + check_count % 50 == 1 → char-count trace printed."""
    _make_detector(debug=True)._trace_mac_missing_header("some buffer text", check_count=1)
    out = capsys.readouterr().out
    assert "MAC table" in out and "chars" in out


def test_trace_mac_idle_pending_silent_when_debug_off(capsys) -> None:
    """Debug OFF → no idle-pending trace."""
    _make_detector(debug=False)._trace_mac_idle_pending(0.0, 5, check_count=1)
    assert capsys.readouterr().out == ""


def test_trace_mac_idle_pending_silent_when_modulo_off(capsys) -> None:
    """Debug ON but check_count % 50 != 1 → no trace."""
    _make_detector(debug=True)._trace_mac_idle_pending(0.0, 5, check_count=2)
    assert capsys.readouterr().out == ""


def test_trace_mac_idle_pending_prints_when_debug_and_modulo(capsys) -> None:
    """Debug ON + check_count % 50 == 1 → entry count + idle trace printed."""
    with patch.object(cd_mod.time, "time", return_value=200.0):
        _make_detector(debug=True)._trace_mac_idle_pending(last_activity=100.0, entry_count=5, check_count=1)
    out = capsys.readouterr().out
    assert "MAC table: found 5 entries" in out
    assert "100.0s" in out


def test_mac_table_repeated_tail_hits_on_uniform_tail() -> None:
    """5 identical non-empty messages → canonical reason string."""
    det = _make_detector()
    outputs = [_seg("row-content")] * 5
    got = det._mac_table_repeated_tail(outputs)
    assert got == "mac table completion (detected 5 repeated identical messages)"


def test_mac_table_repeated_tail_returns_none_when_tail_short() -> None:
    """Fewer than 5 messages → None."""
    assert _make_detector()._mac_table_repeated_tail([_seg("row")] * 4) is None


def test_mac_table_repeated_tail_returns_none_when_tail_not_uniform() -> None:
    """Non-uniform trailing tail → None."""
    outputs = [_seg("row1"), _seg("row2"), _seg("row1"), _seg("row1"), _seg("row1")]
    assert _make_detector()._mac_table_repeated_tail(outputs) is None


def test_mac_table_repeated_tail_returns_none_when_tail_blank() -> None:
    """Uniform tail of whitespace-only content → None (blank tail rejected)."""
    outputs = [_seg("   ")] * 5
    assert _make_detector()._mac_table_repeated_tail(outputs) is None


def test_collect_tail_messages_returns_uniform_tail() -> None:
    """5 identical non-empty tail entries → the tail list."""
    outputs = [_seg("x")] * 5
    assert CompletionDetector._collect_tail_messages(outputs) == ["x"] * 5


def test_collect_tail_messages_none_when_too_few() -> None:
    """Fewer than 5 messages → None."""
    assert CompletionDetector._collect_tail_messages([_seg("x")] * 4) is None


def test_collect_tail_messages_none_when_non_uniform() -> None:
    """Non-uniform tail → None."""
    outputs = [_seg("x")] * 4 + [_seg("y")]
    assert CompletionDetector._collect_tail_messages(outputs) is None


def test_collect_tail_messages_none_when_blank() -> None:
    """Uniform whitespace tail → None."""
    assert CompletionDetector._collect_tail_messages([_seg("")] * 5) is None


def test_log_mac_repeat_hit_silent_when_debug_off(capsys) -> None:
    """Debug OFF → no repeat-hit trace."""
    _make_detector(debug=False)._log_mac_repeat_hit(["row"] * 5)
    assert capsys.readouterr().out == ""


def test_log_mac_repeat_hit_prints_when_debug_on(capsys) -> None:
    """Debug ON → repeat count + sample message printed."""
    _make_detector(debug=True)._log_mac_repeat_hit(["row-content"] * 5)
    out = capsys.readouterr().out
    assert "FOUND MAC table completion" in out
    assert "Repeated message" in out


def test_mac_table_idle_timeout_returns_none_when_few_messages() -> None:
    """Below _MAC_IDLE_MIN_MESSAGES threshold → None."""
    assert _make_detector()._mac_table_idle_timeout([_seg("x")] * 5, 0.0, entry_count=20) is None


def test_mac_table_idle_timeout_returns_none_when_few_entries() -> None:
    """entry_count below threshold → None."""
    outputs = [_seg("x")] * 15
    assert _make_detector()._mac_table_idle_timeout(outputs, 0.0, entry_count=5) is None


def test_mac_table_idle_timeout_returns_none_when_idle_too_short() -> None:
    """Meets counts but idle < 3.0s → None."""
    outputs = [_seg("x")] * 10
    with patch.object(cd_mod.time, "time", return_value=100.0):
        assert _make_detector()._mac_table_idle_timeout(outputs, last_activity=100.0, entry_count=15) is None


def test_mac_table_idle_timeout_hits_when_all_conditions_met() -> None:
    """Meets messages/entries/idle → canonical reason string."""
    outputs = [_seg("x")] * 10
    with patch.object(cd_mod.time, "time", return_value=104.0):
        got = _make_detector()._mac_table_idle_timeout(outputs, last_activity=100.0, entry_count=15)
    assert got is not None
    assert "idle timeout: 15 entries" in got and "4.0s idle" in got


def test_log_mac_idle_hit_silent_when_debug_off(capsys) -> None:
    """Debug OFF → no idle-hit trace."""
    _make_detector(debug=False)._log_mac_idle_hit(15, 4.0)
    assert capsys.readouterr().out == ""


def test_log_mac_idle_hit_prints_when_debug_on(capsys) -> None:
    """Debug ON → entry count + idle trace printed."""
    _make_detector(debug=True)._log_mac_idle_hit(15, 4.0)
    out = capsys.readouterr().out
    assert "FOUND MAC table completion via idle timeout" in out
    assert "15 entries" in out and "4.0s" in out


# ---------------------------------------------------------------------------
# _check_arp_structure + helpers
# ---------------------------------------------------------------------------


def test_check_arp_structure_returns_none_when_too_few_outputs() -> None:
    """Fewer than _ARP_MIN_OUTPUTS segments → None."""
    det = _make_detector()
    assert det._check_arp_structure("ip address hw address", [_seg("a")], 0.0, 1) is None


def test_check_arp_structure_returns_none_when_patterns_below_threshold() -> None:
    """Only 1 column match → below _ARP_MIN_PATTERNS → None."""
    det = _make_detector()
    outputs = [_seg("a"), _seg("b")]
    assert det._check_arp_structure("ip address only", outputs, 0.0, 1) is None


def test_check_arp_structure_returns_none_when_idle_too_short() -> None:
    """Meets pattern count but idle window <= 1s → None."""
    det = _make_detector()
    outputs = [_seg("a"), _seg("b")]
    text = "ip address hw address interface"
    with patch.object(cd_mod.time, "time", return_value=100.0):
        assert det._check_arp_structure(text, outputs, last_activity=100.0, check_count=1) is None


def test_check_arp_structure_hits_when_all_conditions_met() -> None:
    """2+ outputs, 2+ column patterns, idle > 1s → canonical reason."""
    det = _make_detector()
    outputs = [_seg("a"), _seg("b")]
    text = "ip address hw address interface"
    with patch.object(cd_mod.time, "time", return_value=200.0):
        got = det._check_arp_structure(text, outputs, last_activity=100.0, check_count=1)
    assert got == "arp table structure detected"


def test_count_arp_patterns_zero_when_none_present() -> None:
    """No ARP column patterns → 0."""
    assert CompletionDetector._count_arp_patterns("nothing") == 0


def test_count_arp_patterns_counts_each_hit() -> None:
    """Each column pattern hit contributes 1."""
    text = "ip address hw address interface incomplete permanent"
    assert CompletionDetector._count_arp_patterns(text) == 5


def test_trace_arp_patterns_silent_when_debug_off(capsys) -> None:
    """Debug OFF → no ARP pattern trace."""
    _make_detector(debug=False)._trace_arp_patterns(2, "ip address", check_count=1)
    assert capsys.readouterr().out == ""


def test_trace_arp_patterns_silent_when_modulo_off(capsys) -> None:
    """Debug ON but check_count % 200 != 1 → no trace."""
    _make_detector(debug=True)._trace_arp_patterns(2, "ip address", check_count=2)
    assert capsys.readouterr().out == ""


def test_trace_arp_patterns_prints_when_debug_and_modulo(capsys) -> None:
    """Debug ON + modulo hit → pattern count + found patterns printed."""
    _make_detector(debug=True)._trace_arp_patterns(2, "ip address hw address", check_count=1)
    out = capsys.readouterr().out
    assert "ARP pattern analysis" in out
    assert "ip address" in out and "hw address" in out


def test_log_arp_hit_silent_when_debug_off(capsys) -> None:
    """Debug OFF → no ARP hit trace."""
    _make_detector(debug=False)._log_arp_hit(2)
    assert capsys.readouterr().out == ""


def test_log_arp_hit_prints_when_debug_on(capsys) -> None:
    """Debug ON → pattern-count trace printed."""
    _make_detector(debug=True)._log_arp_hit(2)
    assert "FOUND ARP table completion" in capsys.readouterr().out
