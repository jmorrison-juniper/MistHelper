"""Move the column that names a row to the front of a preview table.

Why:
    A preview table took its column order from the file, and an exporter writes
    the keys in alphabetical order. The site export therefore opened with
    `address`, `alarmtemplate_id`, and `aptemplate_id`, and the `name` column
    sat far to the right. A reader had to scroll sideways to learn which site
    each row described. Issue #3125 records that cost.

Rule:
    Alphabetical order is a reasonable default for an unknown record. It is the
    wrong default for a record that carries a well-known identity field. This
    module moves every identity column it recognizes to the front, in the order
    the preference list states, and it keeps every other column where it was.

Scope:
    The plan reorders the column list and each row together, so a column index
    still selects the same value. The caller must apply the plan before it
    sorts, because the browser sends the index of the column a person clicked.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Iterator
from typing import Any

logger = logging.getLogger(__name__)

# The first name in this list leads the table when a record holds it. A record
# that holds none of these names keeps the order the file supplies.
IDENTITY_PREFERENCE: tuple[str, ...] = (
    "name",  # Most exports name the entity in this column.
    "hostname",  # A client record names the host instead.
    "site_name",  # A device row names its site, which orients the reader.
    "mac",  # A client or a device without a name still carries an address.
    "serial",  # A device row carries a serial when it carries no name.
    "id",  # The identifier is the last resort, because it reads poorly.
)


class ColumnOrder:
    """Hold one column arrangement and apply it to a header and to each row."""

    def __init__(self, positions: list[int]) -> None:
        """Store the source index for each display position."""
        self._positions = positions  # Display position N reads source index positions[N].

    @property
    def positions(self) -> list[int]:
        """Return the source index for each display position."""
        return list(self._positions)

    @classmethod
    def plan(cls, columns: list[str]) -> ColumnOrder | None:
        """Return an arrangement that leads with the identity columns, or None.

        A None answer means the record holds no identity column, so the caller
        keeps the order the file supplies and does no extra work.
        """
        leading = cls._leading_positions(columns)
        if not leading:  # No identity column exists, so the file order already stands.
            return None
        remaining = [index for index in range(len(columns)) if index not in set(leading)]
        positions = leading + remaining
        if positions == list(range(len(columns))):  # The file already leads with the identity column.
            return None
        logger.debug("Column order moves %d identity columns to the front", len(leading))
        return cls(positions)

    @staticmethod
    def _leading_positions(columns: list[str]) -> list[int]:
        """Return the source index of each identity column, in preference order."""
        lowered = {}
        for index, column in enumerate(columns):
            key = str(column).strip().lower()
            lowered.setdefault(key, index)  # Keep the first column when a name repeats.
        found = []
        for wanted in IDENTITY_PREFERENCE:
            if wanted in lowered:  # An exact match only, so alarmtemplate_id never matches id.
                found.append(lowered[wanted])
        return found

    def apply(self, row: Iterable[Any]) -> list[Any]:
        """Return one row arranged to match the planned column order."""
        values = list(row)
        return [values[index] if index < len(values) else "" for index in self._positions]

    def apply_to_rows(self, rows: Iterable[Iterable[Any]]) -> Iterator[list[Any]]:
        """Arrange every row of a stream without reading the whole stream."""
        for row in rows:
            yield self.apply(row)
