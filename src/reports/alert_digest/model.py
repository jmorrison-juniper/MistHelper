"""Pure data model for alert digest and alarm acknowledgement rows."""

from __future__ import annotations  # Enable modern annotations without runtime imports.

import logging  # Record model transforms for operator traceability.
from collections.abc import Iterable, Mapping  # Type raw Mist rows without a concrete SDK type.
from dataclasses import dataclass  # Define immutable row objects with clear fields.
from datetime import UTC, datetime  # Convert Mist epoch values to UTC handover text.
from typing import Any  # Accept raw API payload values from mistapi.

logger = logging.getLogger(__name__)  # Keep log records tied to this module.

UNKNOWN_TEXT = "unknown"  # Use one placeholder for missing operator-facing values.


@dataclass(slots=True, frozen=True)
class AlarmDefinition:
    """One alarm definition from the Mist constants endpoint."""

    key: str  # Match the alarm type from the search endpoint.
    group: str  # Provide the digest category from the constants endpoint.
    severity: str  # Provide the portal severity label source.
    display: str = ""  # Preserve a friendly label when Mist provides one.
    fields: tuple[str, ...] = ()  # Preserve definition fields for future samples.

    @classmethod
    def from_raw(cls, row: Mapping[str, Any]) -> AlarmDefinition:
        """Create one definition from a raw Mist constants row."""
        logger.info("Normalizing one alarm definition")  # Log before the transform.
        definition = cls(  # Build the immutable value object for downstream grouping.
            key=AlertDigestFieldReader.text(row.get("key")),  # Keep the Mist alarm key.
            group=AlertDigestFieldReader.text(row.get("group"), UNKNOWN_TEXT),  # Use definition group as category.
            severity=AlertDigestFieldReader.severity(row.get("severity")),  # Normalize severity for handover text.
            display=AlertDigestFieldReader.text(row.get("display")),  # Keep optional display text.
            fields=AlertDigestFieldReader.text_tuple(row.get("fields")),  # Keep optional field names.
        )
        logger.debug("Normalized alarm definition for key_present=%s", bool(definition.key))  # Log result shape.
        return definition  # Return the normalized definition.


@dataclass(slots=True, frozen=True)
class AlarmRecord:
    """One alarm row from the Mist alarm search endpoint."""

    alarm_id: str  # Identify the alarm for acknowledgement.
    alarm_type: str  # Group the alarm by Mist type.
    site_id: str  # Preserve the site identifier when a name is absent.
    site_name: str  # Display the site name when Mist provides one.
    severity: str  # Display the portal severity label.
    category: str  # Group the alarm by Mist category.
    count: int  # Add recurrence from repeated alarm rows.
    timestamp: float | None  # Preserve first seen source time.
    last_seen: float | None  # Preserve last seen source time.
    sample: str  # Show one related device, client, or entity.
    acked: bool | None  # Preserve acknowledgement state for candidate filtering.
    acked_time: float | None  # Preserve acknowledgement time when present.

    @classmethod
    def from_raw(cls, row: Mapping[str, Any], definitions: Mapping[str, AlarmDefinition]) -> AlarmRecord:
        """Create one alarm record from a raw Mist alarm row."""
        logger.info("Normalizing one alarm row")  # Log before the transform.
        alarm_type = AlertDigestFieldReader.text(row.get("type"), UNKNOWN_TEXT)  # Use type as the grouping key.
        definition = definitions.get(alarm_type)  # Read the definition that owns category and severity.
        record = cls(  # Build the normalized alarm row.
            alarm_id=AlertDigestFieldReader.text(row.get("id")),  # Preserve the ID for acknowledgement.
            alarm_type=alarm_type,  # Store the normalized type key.
            site_id=AlertDigestFieldReader.text(row.get("site_id")),  # Keep a fallback site value.
            site_name=AlertDigestFieldReader.site(row),  # Prefer a site name when present.
            severity=AlertDigestFieldReader.severity(definition.severity if definition else row.get("severity")),
            category=definition.group if definition else UNKNOWN_TEXT,  # Definitions own the category contract.
            count=AlertDigestFieldReader.integer(row.get("count"), 1),  # Missing count means one recurrence.
            timestamp=AlertDigestFieldReader.epoch(row.get("timestamp")),  # Convert first seen to seconds.
            last_seen=AlertDigestFieldReader.epoch(row.get("last_seen")),  # Convert last seen to seconds.
            sample=AlertDigestFieldReader.sample(row),  # Extract one related device or client value.
            acked=AlertDigestFieldReader.boolean(row.get("acked")),  # Keep a tri-state acknowledgement value.
            acked_time=AlertDigestFieldReader.epoch(row.get("acked_time")),  # Convert ack time to seconds.
        )
        logger.debug("Normalized alarm row id_present=%s category=%s", bool(record.alarm_id), record.category)
        return record  # Return the normalized alarm row.


@dataclass(slots=True, frozen=True)
class AlarmGroup:
    """One digest row grouped by category, alarm type, and site."""

    category: str  # Category from the definition map.
    severity: str  # Highest useful severity label for the group.
    alarm_type: str  # Mist alarm type key.
    site: str  # Site name, site identifier, or unknown.
    recurrence: int  # Sum of counts across the group.
    first_seen: str  # Earliest timestamp as UTC text.
    last_seen: str  # Latest timestamp as UTC text.
    sample_device_or_client: str  # First useful entity sample.
    acknowledged_state: str  # acknowledged, unacknowledged, mixed, or unknown.

    def to_row(self) -> dict[str, Any]:
        """Return the CSV row for this group."""
        return {  # Preserve the required column names and order through writer fieldnames.
            "category": self.category,
            "severity": self.severity,
            "alarm_type": self.alarm_type,
            "site": self.site,
            "recurrence": self.recurrence,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "sample_device_or_client": self.sample_device_or_client,
            "acknowledged_state": self.acknowledged_state,
        }


@dataclass(slots=True, frozen=True)
class AcknowledgementCandidate:
    """One alarm that menu 281 can acknowledge."""

    alarm_id: str  # Identify the alarm in the bulk request.
    alarm_type: str  # Show the type to the operator.
    site: str  # Show the site to the operator.
    severity: str  # Show the severity to the operator.
    last_seen: str  # Show the most recent alarm time to the operator.


@dataclass(slots=True, frozen=True)
class AcknowledgementResult:
    """One acknowledgement log row."""

    alarm_id: str  # Identify the attempted alarm.
    alarm_type: str  # Preserve the candidate type.
    site: str  # Preserve the candidate site.
    outcome: str  # State whether the alarm was acknowledged, skipped, cancelled, or failed.
    http_status: int | None  # Preserve the bulk request status when a request was sent.
    message: str  # Explain the outcome in operator text.
    run_time: str  # Record when the result was generated.

    def to_row(self) -> dict[str, Any]:
        """Return the CSV row for this result."""
        return {  # Preserve the required acknowledgement log columns.
            "alarm_id": self.alarm_id,
            "alarm_type": self.alarm_type,
            "site": self.site,
            "outcome": self.outcome,
            "http_status": self.http_status,
            "message": self.message,
            "run_time": self.run_time,
        }


class AlertDigestFieldReader:
    """Read typed values from raw Mist rows."""

    @staticmethod
    def text(value: Any, default: str = "") -> str:
        """Return stripped text, or a default when the source is blank."""
        text = str(value).strip() if value is not None else ""  # Normalize absent and non-string values.
        return text if text else default  # Return a useful default for blank values.

    @staticmethod
    def integer(value: Any, default: int = 0) -> int:
        """Return a positive integer, or a default when parsing fails."""
        try:
            parsed = int(value)  # Parse Mist counts that can arrive as strings.
        except (TypeError, ValueError):
            return default  # Use the caller default when the count is missing or malformed.
        return parsed if parsed > 0 else default  # Reject zero and negative recurrence values.

    @staticmethod
    def boolean(value: Any) -> bool | None:
        """Return a tri-state boolean for acknowledgement flags."""
        if isinstance(value, bool):  # Preserve real JSON booleans.
            return value  # Return the source state.
        if isinstance(value, str):  # Parse simple string doubles used by tests or exports.
            return {"true": True, "false": False}.get(value.strip().lower())  # Return None for unknown text.
        return None  # Missing or unrecognized state remains unknown.

    @staticmethod
    def epoch(value: Any) -> float | None:
        """Return epoch seconds, or None when the value is absent."""
        try:
            parsed = float(value)  # Parse seconds or milliseconds from the source.
        except (TypeError, ValueError):
            return None  # Missing time stays blank in the report.
        return parsed / 1000 if parsed > 10_000_000_000 else parsed  # Convert milliseconds to seconds.

    @staticmethod
    def iso(value: float | None) -> str:
        """Return UTC ISO text for an epoch value."""
        if value is None:  # Missing source time has no safe timestamp.
            return ""  # Leave the report cell blank.
        return datetime.fromtimestamp(value, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")  # Use ASCII UTC text.

    @classmethod
    def severity(cls, value: Any) -> str:
        """Return the operator-facing Mist severity label."""
        raw = cls.text(value).lower()  # Normalize raw severity text from Mist.
        labels = {"crit": "Critical", "critical": "Critical", "warn": "Warning", "warning": "Warning"}
        return labels.get(raw, "Informational" if raw in {"info", "informational"} else cls.text(value, UNKNOWN_TEXT))

    @classmethod
    def site(cls, row: Mapping[str, Any]) -> str:
        """Return the best site display value from an alarm row."""
        site_name = cls.text(row.get("site_name") or row.get("site"))  # Prefer a human-readable site name.
        return site_name or cls.text(row.get("site_id"), UNKNOWN_TEXT)  # Fall back to the site id or unknown.

    @classmethod
    def sample(cls, row: Mapping[str, Any]) -> str:
        """Return one device or client sample from known alarm entity fields."""
        for key in ("device_name", "client_name", "hostname", "mac", "entity_id"):  # Prefer simple scalar fields.
            value = cls.text(row.get(key))  # Read one candidate field.
            if value:  # The first useful field is enough for the digest.
                return value  # Return the sample.
        return cls._sample_from_lists(row)  # Read nested or list fields when scalars are absent.

    @classmethod
    def _sample_from_lists(cls, row: Mapping[str, Any]) -> str:
        """Return one sample from list-shaped entity fields."""
        for key in ("hostnames", "switches", "aps", "gateways", "clients", "entity_macs", "macs"):  # Known lists.
            value = cls._first_text(row.get(key))  # Read the first list item as text.
            if value:  # A populated list can identify one impacted entity.
                return value  # Return the sample.
        return cls._sample_from_impacted(row.get("impacted_entities"))  # Read nested impacted entity objects last.

    @classmethod
    def _first_text(cls, value: Any) -> str:
        """Return the first useful text from a scalar or list value."""
        if isinstance(value, list):  # Mist often returns entity values as lists.
            return cls.text(value[0]) if value else ""  # Use the first item only for compact output.
        return cls.text(value)  # Treat a scalar value as the sample itself.

    @classmethod
    def _sample_from_impacted(cls, value: Any) -> str:
        """Return one sample from the impacted entity list."""
        if not isinstance(value, list):  # A non-list impacted value is not a safe source.
            return ""  # Leave the sample blank.
        for item in value:  # Inspect each nested impacted entity object.
            if isinstance(item, Mapping):  # Only object rows can name fields.
                sample = cls.text(item.get("entity_name") or item.get("name") or item.get("entity_mac"))
                if sample:  # The first useful nested value is enough.
                    return sample  # Return the nested sample.
        return ""  # No useful impacted entity value exists.

    @classmethod
    def text_tuple(cls, value: Any) -> tuple[str, ...]:
        """Return a tuple of non-empty text values."""
        if not isinstance(value, list):  # Definition fields should be a list.
            return ()  # Use an empty tuple when the shape differs.
        return tuple(cls.text(item) for item in value if cls.text(item))  # Keep only useful field names.


class AlertDigestModel:
    """Build digest groups, acknowledgement candidates, and result rows."""

    @staticmethod
    def definitions_by_key(rows: Iterable[Mapping[str, Any]]) -> dict[str, AlarmDefinition]:
        """Return alarm definitions keyed by Mist alarm type."""
        logger.info("Building the alarm definition map")  # Log before the transform.
        definitions = [AlarmDefinition.from_raw(row) for row in rows]  # Normalize all definition rows.
        mapped = {definition.key: definition for definition in definitions if definition.key}  # Drop bad keys.
        logger.debug("Built %d alarm definitions", len(mapped))  # Log result count.
        return mapped  # Return the lookup table.

    @staticmethod
    def records_from_rows(
        rows: Iterable[Mapping[str, Any]], definitions: Mapping[str, AlarmDefinition]
    ) -> list[AlarmRecord]:
        """Return normalized alarm records from raw Mist rows."""
        logger.info("Normalizing alarm rows")  # Log before the transform.
        records = [AlarmRecord.from_raw(row, definitions) for row in rows]  # Normalize each row.
        logger.debug("Normalized %d alarm rows", len(records))  # Log result count.
        return records  # Return typed alarm records.

    @classmethod
    def group_records(cls, records: Iterable[AlarmRecord]) -> list[AlarmGroup]:
        """Group alarms by category, alarm type, and site."""
        logger.info("Grouping alarm records for the digest")  # Log before grouping.
        buckets: dict[tuple[str, str, str], list[AlarmRecord]] = {}  # Collect rows under the digest key.
        for record in records:  # Walk each normalized alarm.
            buckets.setdefault((record.category, record.alarm_type, record.site_name), []).append(record)  # Group row.
        groups = [cls._group_from_records(key, value) for key, value in buckets.items()]  # Build digest groups.
        ordered = sorted(groups, key=lambda group: (group.category, group.severity, group.alarm_type, group.site))
        logger.debug("Built %d alarm digest groups", len(ordered))  # Log result count.
        return ordered  # Return stable output order.

    @classmethod
    def _group_from_records(cls, key: tuple[str, str, str], records: list[AlarmRecord]) -> AlarmGroup:
        """Build one digest group from rows that share a key."""
        category, alarm_type, site = key  # Unpack the grouping key for the output row.
        first_seen = min((record.timestamp for record in records if record.timestamp is not None), default=None)
        last_seen = max((record.last_seen for record in records if record.last_seen is not None), default=None)
        sample = next((record.sample for record in records if record.sample), "")  # Keep one useful sample.
        return AlarmGroup(  # Return one CSV and Markdown row.
            category=category,
            severity=cls._highest_severity(record.severity for record in records),
            alarm_type=alarm_type,
            site=site,
            recurrence=sum(record.count for record in records),
            first_seen=AlertDigestFieldReader.iso(first_seen),
            last_seen=AlertDigestFieldReader.iso(last_seen),
            sample_device_or_client=sample,
            acknowledged_state=cls._acknowledged_state(record.acked for record in records),
        )

    @staticmethod
    def acknowledgement_candidates(records: Iterable[AlarmRecord]) -> list[AcknowledgementCandidate]:
        """Return unacknowledged alarms that have an identifier."""
        logger.info("Selecting acknowledgement candidates")  # Log before filtering.
        candidates = [  # Keep one candidate per unacknowledged alarm with an ID.
            AcknowledgementCandidate(
                alarm_id=record.alarm_id,
                alarm_type=record.alarm_type,
                site=record.site_name,
                severity=record.severity,
                last_seen=AlertDigestFieldReader.iso(record.last_seen),
            )
            for record in records
            if record.acked is not True and bool(record.alarm_id)
        ]
        logger.debug("Selected %d acknowledgement candidates", len(candidates))  # Log result count.
        return candidates  # Return candidates in source order.

    @staticmethod
    def result_rows(
        candidates: Iterable[AcknowledgementCandidate], outcome: str, status: int | None, message: str
    ) -> list[AcknowledgementResult]:
        """Return acknowledgement result objects for each candidate."""
        logger.info("Building acknowledgement result rows with outcome %s", outcome)  # Log before the transform.
        run_time = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")  # Use one timestamp for the whole operation.
        results = [  # Build one row for each alarm that the operation considered.
            AcknowledgementResult(
                candidate.alarm_id, candidate.alarm_type, candidate.site, outcome, status, message, run_time
            )
            for candidate in candidates
        ]
        logger.debug("Built %d acknowledgement result rows", len(results))  # Log result count.
        return results  # Return rows for CSV output.

    @staticmethod
    def _highest_severity(values: Iterable[str]) -> str:
        """Return the highest severity label in one group."""
        rank = {"Critical": 3, "Warning": 2, "Informational": 1, UNKNOWN_TEXT: 0}  # Define severity order.
        return max(values, key=lambda value: rank.get(value, 0), default=UNKNOWN_TEXT)  # Return highest label.

    @staticmethod
    def _acknowledged_state(values: Iterable[bool | None]) -> str:
        """Return the group acknowledgement state."""
        states = set(values)  # Compare all tri-state values in the group.
        if states == {True}:  # Every row is acknowledged.
            return "acknowledged"  # State is complete.
        if states == {False}:  # Every row is unacknowledged.
            return "unacknowledged"  # State is actionable.
        return "unknown" if states == {None} else "mixed"  # Mixed true, false, or unknown states need review.
