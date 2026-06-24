"""Combine collected WebSocket message segments into a single result dict."""

from __future__ import annotations

import logging  # Standard logger
from typing import Any  # Used for the segment dict shape

# Keys that are merged specially or excluded from the generic combiner.
_RESERVED_KEYS = {"raw", "session"}


def combine_segments(
    final_results: list[dict[str, Any]],
    session_id: str,
    logger: logging.Logger,
    debug_mode: bool,
    elapsed: float,
    check_count: int,
) -> dict[str, Any] | None:
    """Combine message segments into a single result; mirror original print/log output."""
    logger.info("Combining %s WebSocket result segments", len(final_results))  # Pre-action log
    if not final_results:  # Nothing to combine
        logger.debug("combine_segments called with empty list")  # Post-action log
        return None
    if debug_mode:  # Verbatim diagnostic prints preserved from original implementation
        logger.debug("Combining %s result segments", len(final_results))
        logger.debug("Total wait time: %.2f seconds", elapsed)
        logger.debug("Total checks performed: %s", check_count)
        print(f"[DEBUG] Combining {len(final_results)} result segments")
        print(f"[DEBUG] Total wait time: {elapsed:.2f} seconds")
        print(f"[DEBUG] Total checks performed: {check_count}")
    combined_raw, combined_other = _merge_segments(final_results, debug_mode)  # Do the merge work
    final_result: dict[str, Any] = {"raw": combined_raw, "session": session_id}  # Build envelope
    final_result.update(combined_other)  # Merge non-raw/non-session fields back in
    if debug_mode:  # Verbatim debug trailer
        print(f"[DEBUG] Final combined result length: {len(combined_raw)} characters")
        print(f"[DEBUG] Final result fields: {list(final_result.keys())}")
        print(f"[DEBUG] First 150 chars of final result: {repr(combined_raw[:150])}")
        print(f"[DEBUG] Last 150 chars of final result: {repr(combined_raw[-150:])}")
        if len(combined_raw) == 0:
            print("[DEBUG] WARNING: Final result is empty - this may indicate an issue")
        print(f"[DEBUG] Session {session_id} result collection complete")
        print("[DEBUG] " + "=" * 60)
    logger.info("Command completed with %s message segments", len(final_results))  # Post-action log
    return final_result


def _merge_segments(
    final_results: list[dict[str, Any]],
    debug_mode: bool,
) -> tuple[str, dict[str, Any]]:
    """Concatenate raw chunks and accumulate auxiliary keys across segments."""
    combined_raw = ""  # Final concatenated raw payload
    combined_other: dict[str, Any] = {}  # Auxiliary fields accumulator
    for index, result in enumerate(final_results):  # Walk each captured segment
        raw_content = result.get("raw", "")  # Per-segment raw chunk
        if raw_content:  # Skip empty chunks
            combined_raw += raw_content  # Append to combined buffer
            if debug_mode and len(final_results) > 5:  # Verbose per-segment trace
                print(f"[DEBUG] Segment {index + 1}: {len(raw_content)} chars")
        for key, value in result.items():  # Merge any extra metadata fields
            if key in _RESERVED_KEYS:  # raw/session handled above
                continue
            if key in combined_other:  # If we've seen this key before, concatenate as string
                combined_other[key] = str(combined_other[key]) + str(value)
            else:
                combined_other[key] = value  # First occurrence — store as-is
    return combined_raw, combined_other
