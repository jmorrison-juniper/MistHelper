"""Timestamp formatting helpers for :mod:`src.audit.renderer`.

Pure conversion utilities shared by the parent renderer facade and the
Mermaid / HTML cluster modules. Extracting them into a public module
avoids private-member access across cluster boundaries so no SLF001
suppressions are needed at call sites.
"""

from __future__ import annotations  # WHY: postponed evaluation for forward-ref type hints

from datetime import UTC, datetime  # WHY: epoch -> UTC-aware datetime conversion


def epoch_to_readable(epoch: int) -> str:  # WHY: exported for cluster + facade reuse
    """Convert an epoch timestamp to a human-readable UTC string."""
    if not epoch:  # WHY: 0/None sentinel means the caller had no timestamp
        return "N/A"  # WHY: N/A avoids leaking the sentinel into rendered output
    return datetime.fromtimestamp(epoch, tz=UTC).strftime("%Y-%m-%d %H:%M UTC")  # WHY: canonical UTC format


def epoch_to_short(epoch: int) -> str:  # WHY: compact form for dense Mermaid node labels
    """Convert an epoch timestamp to a short label suitable for Mermaid nodes."""
    if not epoch:  # WHY: 0/None sentinel means the caller had no timestamp
        return "?"  # WHY: '?' keeps mermaid node labels short when timestamp missing
    return datetime.fromtimestamp(epoch, tz=UTC).strftime("%m/%d %H:%M")  # WHY: month/day + HH:MM compact form
