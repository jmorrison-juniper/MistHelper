"""Unit tests for ``src.websocket.polling.result_combiner``.

Why:
    ``combine_segments`` is the terminal step of the WebSocket poll loop —
    it assembles the final envelope handed back to callers. Legacy debug
    output (verbatim ``[DEBUG]`` prints and logger lines) must remain
    byte-identical so operational tooling that greps against the trace
    keeps working. These tests pin every helper, every verbose branch,
    and every documented edge case (empty input, empty raw chunk,
    repeated auxiliary keys, verbose per-segment trace threshold).
"""

from __future__ import annotations

import logging
from typing import Any

import pytest

import src.websocket.polling.result_combiner as rc_mod
from src.websocket.polling.result_combiner import (
    CombineRequest,
    _absorb_extras,
    _absorb_raw_chunk,
    _build_envelope,
    _emit_debug_header,
    _emit_debug_trailer,
    _fold_extra,
    _merge_segments,
    combine_segments,
)


def _make_request(
    *,
    segments: list[dict[str, Any]] | None = None,
    session_id: str = "sess-1",
    debug: bool = False,
    elapsed: float = 1.25,
    check_count: int = 7,
) -> CombineRequest:
    """Build a ``CombineRequest`` with sensible test defaults.

    Why:
        Every test needs a fresh request; keeping the constructor here
        lets the individual test bodies stay focused on the branch they
        exercise instead of restating field defaults.

    Args:
        segments: Segment dicts. Defaults to a single-raw-chunk list.
        session_id: Envelope session id.
        debug: Toggles the verbose header/trailer output.
        elapsed: Wall time reported in the debug header.
        check_count: Poll iteration count reported in the debug header.

    Returns:
        Fully populated ``CombineRequest`` ready to hand to the module.
    """
    if segments is None:
        segments = [{"raw": "hello"}]
    return CombineRequest(
        final_results=segments,
        session_id=session_id,
        logger=logging.getLogger("test.result_combiner"),
        debug_mode=debug,
        elapsed=elapsed,
        check_count=check_count,
    )


class TestCombineSegmentsEmpty:
    """Guard behavior for empty segment lists.

    Why:
        The empty-list guard is the only reason ``combine_segments``
        can ever return ``None``; if it silently returned an empty
        envelope the poll loop would treat "no data" as "done".
    """

    def test_returns_none_and_logs_when_empty(self, caplog: pytest.LogCaptureFixture) -> None:
        req = _make_request(segments=[])
        caplog.set_level(logging.DEBUG, logger="test.result_combiner")

        assert combine_segments(req) is None

        assert any("Combining 0 WebSocket result segments" in r.message for r in caplog.records)
        assert any("combine_segments called with empty list" in r.message for r in caplog.records)


class TestCombineSegmentsHappyPath:
    """End-to-end assembly path with non-empty input.

    Why:
        This is the contract-defining test — envelope keys, key order,
        and info-level log messages are all part of the public API.
    """

    def test_single_segment_returns_expected_envelope(self) -> None:
        req = _make_request(segments=[{"raw": "abc", "session": "IGNORED", "extra": "x"}])
        result = combine_segments(req)
        assert result == {"raw": "abc", "session": "sess-1", "extra": "x"}

    def test_multi_segment_concatenates_raw_and_folds_extras(self) -> None:
        req = _make_request(
            segments=[
                {"raw": "aa", "meta": "one"},
                {"raw": "bb", "meta": "two"},
                {"raw": "cc"},
            ]
        )
        result = combine_segments(req)
        assert result is not None
        assert result["raw"] == "aabbcc"
        assert result["session"] == "sess-1"
        assert result["meta"] == "onetwo"

    def test_emits_info_logs(self, caplog: pytest.LogCaptureFixture) -> None:
        req = _make_request(segments=[{"raw": "x"}, {"raw": "y"}])
        caplog.set_level(logging.INFO, logger="test.result_combiner")

        combine_segments(req)

        messages = [r.message for r in caplog.records]
        assert any("Combining 2 WebSocket result segments" in m for m in messages)
        assert any("Command completed with 2 message segments" in m for m in messages)


class TestBuildEnvelope:
    """``_build_envelope`` key ordering + extras merge."""

    def test_envelope_key_order_and_merge(self) -> None:
        env = _build_envelope("payload", {"a": 1, "b": 2}, "SID")
        assert list(env.keys())[:2] == ["raw", "session"]
        assert env == {"raw": "payload", "session": "SID", "a": 1, "b": 2}

    def test_empty_extras_yields_only_reserved_keys(self) -> None:
        env = _build_envelope("", {}, "S")
        assert env == {"raw": "", "session": "S"}


class TestEmitDebugHeader:
    """Debug-header verbatim output.

    Why:
        Field ops grep on the ``[DEBUG] Combining ... result segments``
        prefix — reordering, reformatting, or dropping the block would
        silently break their tooling.
    """

    def test_silent_when_debug_off(self, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture) -> None:
        req = _make_request(debug=False)
        caplog.set_level(logging.DEBUG, logger="test.result_combiner")

        _emit_debug_header(req)

        assert capsys.readouterr().out == ""
        assert caplog.records == []

    def test_emits_three_lines_when_debug_on(
        self, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture
    ) -> None:
        req = _make_request(segments=[{"raw": "x"}, {"raw": "y"}], debug=True, elapsed=2.5, check_count=42)
        caplog.set_level(logging.DEBUG, logger="test.result_combiner")

        _emit_debug_header(req)

        out = capsys.readouterr().out
        assert "[DEBUG] Combining 2 result segments" in out
        assert "[DEBUG] Total wait time: 2.50 seconds" in out
        assert "[DEBUG] Total checks performed: 42" in out
        debug_msgs = [r.message for r in caplog.records if r.levelno == logging.DEBUG]
        assert any("Combining 2 result segments" in m for m in debug_msgs)
        assert any("Total wait time: 2.50 seconds" in m for m in debug_msgs)
        assert any("Total checks performed: 7" not in m for m in debug_msgs)  # sanity: uses request value


class TestEmitDebugTrailer:
    """Trailer emitter branches (non-empty, empty warning)."""

    def test_silent_when_debug_off(self, capsys: pytest.CaptureFixture[str]) -> None:
        req = _make_request(debug=False)
        _emit_debug_trailer(req, "abc", {"raw": "abc", "session": "sess-1"})
        assert capsys.readouterr().out == ""

    def test_emits_all_lines_for_non_empty_payload(self, capsys: pytest.CaptureFixture[str]) -> None:
        req = _make_request(debug=True, session_id="SID")
        payload = "x" * 300
        _emit_debug_trailer(req, payload, {"raw": payload, "session": "SID", "extra": "e"})

        out = capsys.readouterr().out
        assert f"[DEBUG] Final combined result length: {len(payload)} characters" in out
        assert "[DEBUG] Final result fields: ['raw', 'session', 'extra']" in out
        assert "[DEBUG] First 150 chars of final result:" in out
        assert "[DEBUG] Last 150 chars of final result:" in out
        assert "[DEBUG] Session SID result collection complete" in out
        assert "[DEBUG] " + ("=" * 60) in out
        assert "WARNING" not in out

    def test_emits_warning_when_payload_empty(self, capsys: pytest.CaptureFixture[str]) -> None:
        req = _make_request(debug=True)
        _emit_debug_trailer(req, "", {"raw": "", "session": "sess-1"})
        out = capsys.readouterr().out
        assert "[DEBUG] WARNING: Final result is empty" in out


class TestMergeSegments:
    """``_merge_segments`` driver behavior and verbose threshold."""

    def test_returns_empty_pair_for_empty_input(self) -> None:
        raw, extras = _merge_segments([], debug_mode=True)
        assert raw == ""
        assert extras == {}

    def test_concatenates_raw_in_order(self) -> None:
        raw, extras = _merge_segments([{"raw": "a"}, {"raw": "b"}, {"raw": "c"}], debug_mode=False)
        assert raw == "abc"
        assert extras == {}

    def test_folds_extras_with_repeat_keys(self) -> None:
        raw, extras = _merge_segments(
            [
                {"raw": "1", "note": "hello ", "count": 1},
                {"raw": "2", "note": "world", "count": 2},
            ],
            debug_mode=False,
        )
        assert raw == "12"
        assert extras == {"note": "hello world", "count": "12"}

    def test_verbose_off_when_debug_off(self, capsys: pytest.CaptureFixture[str]) -> None:
        segments = [{"raw": "x"}] * 10  # would trip threshold if debug were on
        _merge_segments(segments, debug_mode=False)
        assert capsys.readouterr().out == ""

    def test_verbose_off_when_at_or_below_threshold(self, capsys: pytest.CaptureFixture[str]) -> None:
        segments = [{"raw": "x"}] * 5  # threshold is `> 5`, so 5 is off
        _merge_segments(segments, debug_mode=True)
        assert capsys.readouterr().out == ""

    def test_verbose_on_when_debug_on_and_above_threshold(self, capsys: pytest.CaptureFixture[str]) -> None:
        segments = [{"raw": "ab"}] * 6  # trips the > 5 threshold
        _merge_segments(segments, debug_mode=True)
        out = capsys.readouterr().out
        assert "[DEBUG] Segment 1: 2 chars" in out
        assert "[DEBUG] Segment 6: 2 chars" in out


class TestAbsorbRawChunk:
    """Per-segment raw handler branches."""

    def test_appends_non_empty_chunk(self) -> None:
        buf: list[str] = []
        _absorb_raw_chunk({"raw": "abc"}, buf, verbose=False, index=0)
        assert buf == ["abc"]

    def test_missing_raw_key_treated_as_empty(self, capsys: pytest.CaptureFixture[str]) -> None:
        buf: list[str] = []
        _absorb_raw_chunk({"other": 1}, buf, verbose=True, index=0)
        assert buf == []
        assert capsys.readouterr().out == ""

    def test_empty_raw_string_skipped(self, capsys: pytest.CaptureFixture[str]) -> None:
        buf: list[str] = []
        _absorb_raw_chunk({"raw": ""}, buf, verbose=True, index=3)
        assert buf == []
        assert capsys.readouterr().out == ""

    def test_verbose_trace_uses_one_based_index(self, capsys: pytest.CaptureFixture[str]) -> None:
        buf: list[str] = []
        _absorb_raw_chunk({"raw": "abcd"}, buf, verbose=True, index=4)
        assert buf == ["abcd"]
        out = capsys.readouterr().out
        assert "[DEBUG] Segment 5: 4 chars" in out

    def test_verbose_off_suppresses_trace(self, capsys: pytest.CaptureFixture[str]) -> None:
        buf: list[str] = []
        _absorb_raw_chunk({"raw": "abcd"}, buf, verbose=False, index=0)
        assert buf == ["abcd"]
        assert capsys.readouterr().out == ""


class TestAbsorbExtras:
    """Extras accumulator: reserved keys skipped, repeats folded."""

    def test_reserved_keys_are_skipped(self) -> None:
        acc: dict[str, Any] = {}
        _absorb_extras({"raw": "IGN", "session": "IGN", "other": 1}, acc)
        assert acc == {"other": 1}

    def test_first_occurrence_stored_as_is(self) -> None:
        acc: dict[str, Any] = {}
        _absorb_extras({"count": 5}, acc)
        assert acc == {"count": 5}

    def test_repeat_keys_are_folded_as_string_concat(self) -> None:
        acc: dict[str, Any] = {"count": 5}
        _absorb_extras({"count": 7}, acc)
        assert acc == {"count": "57"}


class TestFoldExtra:
    """Pure fold helper: first occurrence returns incoming, repeats concat."""

    def test_first_occurrence_returns_incoming(self) -> None:
        assert _fold_extra(existing=None, incoming="a", seen=False) == "a"

    def test_repeat_stringifies_and_concats(self) -> None:
        assert _fold_extra(existing=1, incoming=2, seen=True) == "12"

    def test_repeat_with_string_existing(self) -> None:
        assert _fold_extra(existing="foo", incoming="bar", seen=True) == "foobar"


class TestCombineRequestDataclass:
    """``CombineRequest`` immutability guarantees.

    Why:
        The class is declared frozen + slotted precisely so that helpers
        cannot mutate the bundle mid-flight; regressing that would allow
        subtle state-sharing bugs across polling iterations.
    """

    def test_frozen_disallows_mutation(self) -> None:
        req = _make_request()
        with pytest.raises((AttributeError, Exception)):
            req.debug_mode = True  # type: ignore[misc]

    def test_slots_disallow_new_attributes(self) -> None:
        req = _make_request()
        with pytest.raises((AttributeError, TypeError)):
            req.new_field = "nope"  # type: ignore[attr-defined]


class TestModuleConstants:
    """Sanity checks on module-level knobs.

    Why:
        Changing these values changes user-visible debug output. Pinning
        them here forces any change to be a deliberate PR touching the
        tests rather than a silent refactor.
    """

    def test_reserved_keys(self) -> None:
        assert rc_mod._RESERVED_KEYS == {"raw", "session"}

    def test_verbose_segment_threshold(self) -> None:
        assert rc_mod._VERBOSE_SEGMENT_THRESHOLD == 5

    def test_preview_chars(self) -> None:
        assert rc_mod._PREVIEW_CHARS == 150

    def test_trailer_bar_width(self) -> None:
        assert rc_mod._TRAILER_BAR == "=" * 60
