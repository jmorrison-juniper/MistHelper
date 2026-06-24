"""Dataclasses that pack the Intelligent Map Replacement Wizard arguments.

Refs issue #433 phase C tranche 3 (STRUCT-PARAMS sweep on maps_manager.py).
The wizard's preview/apply/summary helpers are kept under the agents.md
5-parameter limit by grouping current_map / map_name / assets / errors /
backup_file into purpose-specific dataclasses.
"""

from __future__ import annotations  # PEP 604 unions on Python 3.10+ codebases.

from dataclasses import dataclass  # Standard library dataclass factory.
from typing import Any  # Wildcard inner type for the loosely-typed Mist asset dicts.


@dataclass(frozen=True, slots=True)
class MapWizardPreviewContext:
    """Inputs the preview step needs to render the upcoming changes."""

    current_map: dict[str, Any]  # Existing map record so original PPM/dimensions show in the preview.
    map_name: str  # Human-readable map name printed at the top of the preview.
    assets: dict[str, Any]  # Asset bundle (devices, zones, beacons) used to show a coord-translation sample.


@dataclass(frozen=True, slots=True)
class MapWizardApplyTarget:
    """Identifies the map being replaced and the image file going into it."""

    site_id: str  # Mist site UUID that owns the map being updated.
    map_id: str  # Mist map UUID being modified by the wizard.
    file_path: str  # Local path to the new image file being uploaded to Mist.


@dataclass(frozen=True, slots=True)
class MapWizardApplyContext:
    """Mutable state the apply step uses to scale assets and record failures."""

    current_map: dict[str, Any]  # Pre-replacement record (drives wall/wayfinding path scaling).
    assets: dict[str, Any]  # Asset bundle, scaled in-place when in "proportional" mode.
    errors: list[str]  # Out-parameter list the helper appends failure descriptions to.


@dataclass(frozen=True, slots=True)
class MapWizardSummaryContext:
    """Inputs the final wizard summary printer needs to display results."""

    map_name: str  # Human-readable map name printed in the summary header.
    backup_file: str  # Path to the JSON backup written before any changes were applied.
    errors: list[str]  # Accumulated apply-step failures; empty means a clean run.
