"""The reading that the gateway holds between two polls.

Why:
    The upstream `mist_snmp_gateway` writes each Mist reading into MongoDB and
    reads it back on every SNMP poll. A database is a heavy answer to a small
    question, because the gateway never queries the reading, never joins it, and
    never keeps it after the next refresh. It only needs the last reading.

    This module holds that reading in memory instead. A snapshot is frozen, so a
    poll that reads one snapshot cannot see a half-finished refresh, and the
    refresh thread cannot change a snapshot that a poll is already rendering.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from src.metrics_gateway.catalog import MetricDefinition, MetricScope

logger = logging.getLogger(__name__)

# WHY: A label pair is a tuple and not a dict, because a frozen dataclass with
# `slots=True` must hold hashable fields for a set or a dict key to work.
LabelPairs = tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class MetricSample:
    """One number that the gateway serves, with the labels that identify it.

    Attributes:
        definition: The catalog entry that names and describes the reading.
        labels: The label pairs, in the order the renderer prints them.
        value: The number. An informational reading always carries 1.
        row_key: The identity of the table row, such as a site identifier or a
            device MAC address. An organization scalar carries an empty string.
        text: The text that the SNMP responder returns for this cell. It is None
            for a plain number, and it is set for an informational reading,
            because SNMP has no label and must carry the text in the value.
    """

    definition: MetricDefinition
    labels: LabelPairs
    value: float
    row_key: str = ""
    text: str | None = None


@dataclass(frozen=True, slots=True)
class MetricSnapshot:
    """Every reading from one pass over Mist Cloud.

    Attributes:
        samples: The readings, in catalog order within each scope.
        collected_at: The moment the pass finished, in seconds since the epoch.
        duration_seconds: The seconds the pass took.
        ok: True when every Mist call in the pass answered.
        error: The reason the pass failed, or an empty string after a good pass.
    """

    samples: tuple[MetricSample, ...] = ()
    collected_at: float = 0.0
    duration_seconds: float = 0.0
    ok: bool = False
    error: str = ""

    def row_keys(self, scope: MetricScope) -> tuple[str, ...]:
        """Return the row identity of one table, in first-seen order.

        Why:
            An SNMP table needs a stable row number. The collector emits the
            rows in a sorted order, so first-seen order gives the same row
            number to the same site on every refresh, and `snmpwalk` therefore
            returns a table that a NOC can read twice and compare.

        Args:
            scope: The table whose rows the caller needs.

        Returns:
            The row identities, without a repeat.
        """
        seen: dict[str, None] = {}  # A dict keeps insertion order, which a set does not.
        for sample in self.samples:  # One pass finds every row of the wanted table.
            if sample.definition.scope is scope and sample.row_key:  # An org scalar has no row, so skip it.
                seen.setdefault(sample.row_key, None)  # `setdefault` keeps the first position of a repeated key.
        return tuple(seen)

    def is_empty(self) -> bool:
        """Report whether the snapshot holds no reading at all.

        Why:
            The cache starts empty. A caller must be able to tell an empty start
            from a failed refresh, because an empty start has no last good
            reading to serve.

        Returns:
            True when the snapshot holds no sample.
        """
        return not self.samples


@dataclass
class SampleBuilder:
    """Collects samples during one pass and freezes them into a snapshot.

    Why:
        The collector builds the samples over several calls, one for the
        organization and one for each site. A mutable builder keeps that work
        simple, and the freeze at the end gives the reader an object it cannot
        change by accident.
    """

    samples: list[MetricSample] = field(default_factory=list)

    def add(self, definition: MetricDefinition, value: float, labels: LabelPairs = (), row_key: str = "") -> None:
        """Record one number.

        Args:
            definition: The catalog entry for the reading.
            value: The number to record.
            labels: The label pairs that identify the reading.
            row_key: The identity of the table row, empty for a scalar.
        """
        self.samples.append(MetricSample(definition=definition, labels=labels, value=value, row_key=row_key))

    def add_info(self, definition: MetricDefinition, labels: LabelPairs, row_key: str, text: str) -> None:
        """Record one informational reading.

        Why:
            Prometheus carries text in a label and holds the value at 1. SNMP
            has no label, so the same reading must carry the text in the value.
            One call records both shapes, so the two paths cannot drift.

        Args:
            definition: The catalog entry for the reading.
            labels: The label pairs that carry the text for Prometheus.
            row_key: The identity of the table row.
            text: The text that SNMP returns for this cell.
        """
        self.samples.append(MetricSample(definition=definition, labels=labels, value=1.0, row_key=row_key, text=text))

    def freeze(self, collected_at: float, duration_seconds: float, ok: bool, error: str = "") -> MetricSnapshot:
        """Turn the recorded samples into a snapshot that no caller can change.

        Args:
            collected_at: The moment the pass finished, in seconds since the epoch.
            duration_seconds: The seconds the pass took.
            ok: True when every Mist call in the pass answered.
            error: The reason the pass failed, empty after a good pass.

        Returns:
            The frozen snapshot.
        """
        logger.debug("Freeze a snapshot of %d samples", len(self.samples))  # Log the count the pass produced.
        return MetricSnapshot(
            samples=tuple(self.samples),
            collected_at=collected_at,
            duration_seconds=duration_seconds,
            ok=ok,
            error=error,
        )
