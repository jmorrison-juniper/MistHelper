"""Immutable records for utility trigger requests."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UtilityTiming:
    """Hold the time limits for one utility stream."""

    first_output_seconds: float
    quiet_seconds: float
    total_seconds: float


@dataclass(frozen=True, slots=True)
class UtilityListen:
    """Hold the stream channel for one utility trigger."""

    channel: str
    channel_path: str
    timing: UtilityTiming


@dataclass(frozen=True, slots=True)
class UtilityRequest:
    """Hold one REST trigger request and its stream metadata."""

    key: str
    method: str
    path: str
    body: dict[str, object] | None
    listen: UtilityListen
