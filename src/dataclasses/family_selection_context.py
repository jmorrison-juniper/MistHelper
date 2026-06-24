"""Frozen dataclass that bundles the inputs for the firmware model-family version-selection prompt.

The original ``_apply_family_selection`` function in ``src/firmware/site_auto_upgrade.py``
took 7 positional parameters which exceeded the 5-Item Rule's max-5 limit. The 5 fields
here group the immutable inputs (family name, model list, available + current versions,
version map) leaving the 2 mutable outputs (user's choice + the dict being populated)
as direct parameters of the function.

Issue: https://github.com/jmorrison-juniper/MistHelper/issues/433 (Phase B)
"""

from __future__ import annotations  # Enable PEP 604 union syntax on Python 3.13.

from dataclasses import dataclass  # Standard-library dataclass decorator.
from typing import Any  # Type alias for the heterogenous version-entry list.


@dataclass(frozen=True, slots=True)
class FamilySelectionContext:
    """Immutable inputs for one model-family version-selection iteration.

    Five fields fit within the 5-Item Rule. The function receiving this context
    also takes the operator's ``choice`` string and the mutable ``custom_versions``
    output dict as direct parameters, keeping its signature at 3 total params.
    """

    family: str  # Human-readable model-family name (e.g. "AP43"); used only for log/print output.
    models: list[str]  # List of concrete model SKUs that belong to this family.
    sorted_versions: list[str]  # Operator-visible numbered choices, sorted newest-first.
    current_version: str | None  # The version currently configured on this family (None when unset).
    model_version_map: dict[str, list[Any]]  # Per-model raw API entries; used to validate the selection.
