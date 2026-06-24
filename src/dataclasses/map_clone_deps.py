"""Dataclasses that pack MapsManager clone helpers into the 5-Item Rule.

Refs issue #433 phase C tranche 3 (STRUCT-PARAMS sweep on maps_manager.py).
Each frozen, slots-enabled dataclass groups related arguments so the
``_print_clone_summary`` / ``_clone_zones`` flow stays within the
agents.md 5-parameter-per-function limit.
"""

from __future__ import annotations  # PEP 604 unions on Python 3.10+ codebases.

from dataclasses import dataclass  # Standard library dataclass factory.


@dataclass(frozen=True, slots=True)
class MapCloneSummary:
    """Identity + payload of a freshly cloned map for summary printing."""

    source_map: dict  # The original map dict as returned by the Mist API.
    new_name: str  # The name the user chose for the clone.
    cloned_map_id: str  # The UUID Mist assigned to the newly created clone.
    clone_payload: dict  # The body that was actually POSTed (walls, ppm, etc).
    had_image: bool  # True when an image file was uploaded as part of the clone.


@dataclass(frozen=True, slots=True)
class ZoneCloneResult:
    """Counts of zones successfully cloned vs failed during a clone."""

    cloned: int  # Number of zones the API accepted on the clone target.
    failed: int  # Number of zones that the API rejected or that errored out.
