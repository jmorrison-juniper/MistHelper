"""Combine collected WebSocket message segments into a single result dict."""

from __future__ import annotations  # PEP 563 postponed evaluation for typing forward refs

import logging  # Standard logger type used by callers
from dataclasses import dataclass  # Frozen bundle for the 6 caller inputs
from typing import Any  # Segment dicts have heterogeneous values

logger = logging.getLogger(__name__)  # WHY: route former print() diagnostics for capture/redirection (issue #886).

_RESERVED_KEYS = {"raw", "session"}  # Keys handled specially and excluded from generic merge
_VERBOSE_SEGMENT_THRESHOLD = 5  # Per-segment trace fires only when segment count exceeds this
_TRAILER_BAR = "=" * 60  # Fixed-width visual separator preserved from original output
_PREVIEW_CHARS = 150  # Head/tail preview length in verbose trailer

MergedPayload = tuple[str, dict[str, Any]]  # Return shape: (concatenated raw, extras dict)


@dataclass(frozen=True, slots=True)  # Frozen + slots keeps the bundle immutable and compact
class CombineRequest:  # Immutable transport of the six caller inputs
    """Immutable bundle of the six inputs required to combine segments."""

    final_results: list[dict[str, Any]]  # Captured message segments in arrival order
    session_id: str  # Session id echoed into the envelope
    logger: logging.Logger  # Structured logger for info/debug output
    debug_mode: bool  # Enables verbatim [DEBUG] print statements
    elapsed: float  # Wall time spent waiting on segments (seconds)
    check_count: int  # Number of poll iterations performed


def combine_segments(request: CombineRequest) -> dict[str, Any] | None:  # Public entrypoint
    """Combine message segments into a single result. Mirror original print/log output."""
    segments = request.final_results  # Local alias improves readability of guard block
    request.logger.info("Combining %s WebSocket result segments", len(segments))  # Pre-action log
    if not segments:  # Guard: nothing to combine
        request.logger.debug("combine_segments called with empty list")  # Post-action log
        return None  # Sentinel returned to caller to mirror original contract
    _emit_debug_header(request)  # Preserve verbatim diagnostic prints from original impl
    combined_raw, combined_other = _merge_segments(segments, request.debug_mode)  # Do the merge work
    final_result = _build_envelope(combined_raw, combined_other, request.session_id)  # Envelope assembly
    _emit_debug_trailer(request, combined_raw, final_result)  # Verbatim debug trailer
    request.logger.info("Command completed with %s message segments", len(segments))  # Post-action log
    return final_result  # Return the fully assembled envelope dict


def _build_envelope(  # Assemble the outbound result envelope
    combined_raw: str, combined_other: dict[str, Any], session_id: str
) -> dict[str, Any]:
    """Assemble the outbound result envelope preserving key order and merging extras."""
    envelope: dict[str, Any] = {"raw": combined_raw, "session": session_id}  # Envelope skeleton
    envelope.update(combined_other)  # Merge non-raw/non-session fields back in
    return envelope  # Fully populated envelope handed back to caller


def _emit_debug_header(request: CombineRequest) -> None:  # Verbose header emitter
    """Emit verbose logger + stdout diagnostics that mirror the pre-refactor output."""
    if not request.debug_mode:  # Guard: skip entirely when quiet mode is active
        return  # Nothing to emit when debug is off
    count = len(request.final_results)  # Cached count for the header block
    request.logger.debug("Combining %s result segments", count)  # Logger mirror line
    request.logger.debug("Total wait time: %.2f seconds", request.elapsed)  # Wall time
    request.logger.debug("Total checks performed: %s", request.check_count)  # Poll iterations
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.debug("[DEBUG] Combining %s result segments", count)
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.debug("[DEBUG] Total wait time: %.2f seconds", request.elapsed)
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.debug("[DEBUG] Total checks performed: %s", request.check_count)


def _emit_debug_trailer(  # Verbose trailer emitter
    request: CombineRequest, combined_raw: str, final_result: dict[str, Any]
) -> None:
    """Emit the trailing debug block including head/tail previews and completion banner."""
    if not request.debug_mode:  # Guard: skip entirely when quiet mode is active
        return  # Nothing to emit when debug is off
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.debug("[DEBUG] Final combined result length: %s characters", len(combined_raw))
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.debug("[DEBUG] Final result fields: %s", list(final_result.keys()))
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.debug("[DEBUG] First 150 chars of final result: %r", combined_raw[:_PREVIEW_CHARS])
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.debug("[DEBUG] Last 150 chars of final result: %r", combined_raw[-_PREVIEW_CHARS:])
    if len(combined_raw) == 0:  # Empty payload sentinel
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.warning("[DEBUG] WARNING: Final result is empty - this may indicate an issue")
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.debug("[DEBUG] Session %s result collection complete", request.session_id)
    # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
    logger.debug("[DEBUG] %s", _TRAILER_BAR)


def _merge_segments(final_results: list[dict[str, Any]], debug_mode: bool) -> MergedPayload:  # Merge driver
    """Concatenate raw chunks and accumulate auxiliary keys across segments."""
    combined_raw_parts: list[str] = []  # Buffer chunks then join once for O(n) concat
    combined_other: dict[str, Any] = {}  # Auxiliary fields accumulator
    verbose = debug_mode and len(final_results) > _VERBOSE_SEGMENT_THRESHOLD  # Precomputed trace flag
    for index, result in enumerate(final_results):  # Walk each captured segment
        _absorb_raw_chunk(result, combined_raw_parts, verbose, index)  # Handle raw + optional trace
        _absorb_extras(result, combined_other)  # Merge any extra metadata fields
    return "".join(combined_raw_parts), combined_other  # Single join keeps concat O(n)


def _absorb_raw_chunk(  # Per-segment raw handler
    result: dict[str, Any], buffer: list[str], verbose: bool, index: int
) -> None:
    """Append this segment's raw chunk to the buffer and emit an optional trace line."""
    raw_content = result.get("raw", "")  # Per-segment raw chunk
    if not raw_content:  # Guard: skip empty chunks
        return  # Empty chunk contributes nothing to buffer or trace
    buffer.append(raw_content)  # Defer join to caller for single allocation
    if verbose:  # Emit per-segment trace when verbose mode is precomputed on
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.debug("[DEBUG] Segment %s: %s chars", index + 1, len(raw_content))


def _absorb_extras(result: dict[str, Any], accumulator: dict[str, Any]) -> None:  # Extras merger
    """Merge non-reserved keys into the accumulator, concatenating on repeat keys."""
    for key, value in result.items():  # Merge any extra metadata fields
        if key in _RESERVED_KEYS:  # raw/session are handled by the envelope builder
            continue  # Skip reserved keys entirely
        accumulator[key] = _fold_extra(accumulator.get(key), value, key in accumulator)  # Table-style fold


def _fold_extra(existing: Any, incoming: Any, seen: bool) -> Any:  # Pure fold helper
    """Return the folded value: str-concat when the key was seen, otherwise the incoming value."""
    if seen:  # Repeat keys are concatenated as strings to match legacy behavior
        return str(existing) + str(incoming)  # Coerce both sides to str before concat
    return incoming  # First occurrence — store as-is
