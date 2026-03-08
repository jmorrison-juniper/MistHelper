"""DiffService — field-level config comparison using deepdiff (T047, R-03).

Computes structural diffs between two JSON config blobs and normalizes
the output into a list of ``DiffChange`` items with path, old/new values,
and change type.
"""

from __future__ import annotations

import logging
from typing import Any

from deepdiff import DeepDiff

logger = logging.getLogger(__name__)


class DiffChange:
    """Single field-level change record."""

    __slots__ = ("path", "old_value", "new_value", "change_type")

    def __init__(
        self,
        path: str,
        old_value: Any,
        new_value: Any,
        change_type: str,
    ) -> None:
        self.path = path
        self.old_value = old_value
        self.new_value = new_value
        self.change_type = change_type

    def to_dict(self) -> dict[str, Any]:
        """Serialize for API response."""
        return {
            "path": self.path,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "change_type": self.change_type,
        }


class DiffSummary:
    """Aggregate counts for a diff result."""

    __slots__ = ("fields_changed", "fields_added", "fields_removed")

    def __init__(self) -> None:
        self.fields_changed = 0
        self.fields_added = 0
        self.fields_removed = 0

    def to_dict(self) -> dict[str, int]:
        """Serialize for API response."""
        return {
            "fields_changed": self.fields_changed,
            "fields_added": self.fields_added,
            "fields_removed": self.fields_removed,
        }


class DiffResult:
    """Complete diff output with changes and summary."""

    __slots__ = ("changes", "summary")

    def __init__(
        self,
        changes: list[DiffChange],
        summary: DiffSummary,
    ) -> None:
        self.changes = changes
        self.summary = summary


class DiffService:
    """Compute field-level diffs between config revisions (R-03).

    Uses deepdiff 8.x with ``ignore_order=True`` and ``verbose_level=2``
    to produce old/new value pairs.
    """

    def compute_diff(
        self,
        old_config: dict[str, Any],
        new_config: dict[str, Any],
    ) -> DiffResult:
        """Compare two config blobs and return normalized diff."""
        raw = DeepDiff(
            old_config,
            new_config,
            ignore_order=True,
            verbose_level=2,
            view="tree",
        )
        return self._normalize(raw)

    # -- normalization ---------------------------------------------------

    def _normalize(self, raw: DeepDiff) -> DiffResult:
        """Convert deepdiff tree output to flat DiffChange list."""
        changes: list[DiffChange] = []
        summary = DiffSummary()

        self._collect_values_changed(raw, changes, summary)
        self._collect_added(raw, changes, summary)
        self._collect_removed(raw, changes, summary)
        self._collect_type_changes(raw, changes, summary)

        return DiffResult(changes=changes, summary=summary)

    @staticmethod
    def _collect_values_changed(
        raw: DeepDiff,
        changes: list[DiffChange],
        summary: DiffSummary,
    ) -> None:
        """Extract value_changed items."""
        for item in raw.get("values_changed", []):
            changes.append(DiffChange(
                path=_tree_path(item),
                old_value=item.t1,
                new_value=item.t2,
                change_type="value_changed",
            ))
            summary.fields_changed += 1

    @staticmethod
    def _collect_added(
        raw: DeepDiff,
        changes: list[DiffChange],
        summary: DiffSummary,
    ) -> None:
        """Extract dictionary_item_added and iterable_item_added."""
        for key in ("dictionary_item_added", "iterable_item_added"):
            for item in raw.get(key, []):
                changes.append(DiffChange(
                    path=_tree_path(item),
                    old_value=None,
                    new_value=item.t2,
                    change_type="item_added",
                ))
                summary.fields_added += 1

    @staticmethod
    def _collect_removed(
        raw: DeepDiff,
        changes: list[DiffChange],
        summary: DiffSummary,
    ) -> None:
        """Extract dictionary_item_removed and iterable_item_removed."""
        for key in ("dictionary_item_removed", "iterable_item_removed"):
            for item in raw.get(key, []):
                changes.append(DiffChange(
                    path=_tree_path(item),
                    old_value=item.t1,
                    new_value=None,
                    change_type="item_removed",
                ))
                summary.fields_removed += 1

    @staticmethod
    def _collect_type_changes(
        raw: DeepDiff,
        changes: list[DiffChange],
        summary: DiffSummary,
    ) -> None:
        """Extract type_changes items."""
        for item in raw.get("type_changes", []):
            changes.append(DiffChange(
                path=_tree_path(item),
                old_value=item.t1,
                new_value=item.t2,
                change_type="type_changed",
            ))
            summary.fields_changed += 1


def _tree_path(item: Any) -> str:
    """Convert a deepdiff tree item path to a dot-notation string.

    Example: ``root['radio_config']['band_24']['power']``
    becomes:  ``radio_config.band_24.power``
    """
    raw_path = item.path(output_format="list")
    parts: list[str] = []
    for segment in raw_path:
        if isinstance(segment, int):
            parts.append(f"[{segment}]")
        else:
            parts.append(str(segment))
    return ".".join(parts).replace(".[", "[")
