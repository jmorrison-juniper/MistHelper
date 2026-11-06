"""Match AP trouble codes to the live LED dictionary without inferred meanings."""

from __future__ import annotations

import logging
import math
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger(__name__)


class TroubleCode:
    """Normalize documented numeric trouble evidence and its observation time."""

    RECENT_WINDOW = timedelta(minutes=15)  # WHY: The user wants to exclude old AP trouble observations.

    @staticmethod
    def normalize(value: object) -> str:
        """Keep zero-padded numeric codes and exclude absent or zero evidence."""
        if value is None or value == "":
            return ""
        if isinstance(value, str) and not value.strip():
            return ""
        if isinstance(value, bool) or not isinstance(value, (str, int)):
            raise ValueError("Invalid AP trouble code type")
        text = str(value).strip()
        if not text.isascii() or not text.isdecimal():
            raise ValueError("Invalid AP trouble code value")
        number = int(text)
        return str(number).zfill(2) if number else ""

    @staticmethod
    def timestamp(value: object) -> str:
        """Convert an available epoch time to UTC without inventing missing time."""
        if value is None:
            return ""
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Invalid AP trouble timestamp type")
        try:
            if not math.isfinite(value) or value < 0:
                raise ValueError("Invalid AP trouble timestamp value")
            return datetime.fromtimestamp(value, tz=UTC).isoformat()
        except (OverflowError, OSError, ValueError):
            raise ValueError("Invalid AP trouble timestamp value") from None

    @staticmethod
    def is_recent(timestamp: str, reported_at: str) -> bool:
        """Accept only trouble timestamps inside the prior 15 minutes."""
        if not timestamp:  # WHY: An untimed code cannot be placed inside the required window.
            return False  # WHY: Do not invent a current observation time.
        try:
            trouble_time = datetime.fromisoformat(timestamp)  # WHY: Compare the reported instant, not its text.
            report_time = datetime.fromisoformat(reported_at)  # WHY: Use the report creation time as the window end.
        except ValueError:
            raise ValueError("Invalid AP report timestamp") from None  # WHY: Invalid time must fail the report.
        if trouble_time.tzinfo is None or report_time.tzinfo is None:  # WHY: Naive times cannot be compared safely.
            raise ValueError("AP report timestamps must include a time zone")  # WHY: Require unambiguous UTC instants.
        return (
            report_time - TroubleCode.RECENT_WINDOW <= trouble_time <= report_time
        )  # WHY: Exclude stale and future codes.


class CodeDefinitions:
    """Validate one live dictionary and retain unknown trouble codes explicitly."""

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        """Index definitions once so every AP uses the same dictionary."""
        logger.info("Indexing AP trouble definitions")
        if not rows:
            raise ValueError("The AP definition dictionary is empty")
        self._definitions: dict[str, dict[str, str]] = {}
        for row in rows:
            self._add(row)
        logger.debug("Indexed AP trouble definitions records=%d", len(self._definitions))

    def _add(self, row: dict[str, Any]) -> None:
        """Refuse duplicate or incomplete definitions rather than inventing text."""
        if row.get("code") is None or not str(row["code"]).strip():
            raise ValueError("The AP definition dictionary contains a definition without a code")
        code = TroubleCode.normalize(row.get("code"))
        if any(
            not isinstance(row.get(field), str) or not row[field].strip() for field in ("key", "name", "description")
        ):
            raise ValueError("The AP definition dictionary contains an incomplete definition")
        if code in self._definitions:
            raise ValueError("The AP definition dictionary contains a duplicate definition")
        if code:
            self._definitions[code] = {
                "code": code,
                "definition_status": "known",
                "code_key": row["key"],
                "code_name": row["name"],
                "code_description": row["description"],
            }

    def describe(self, code: str) -> dict[str, str]:
        """Return live definition text or an explicit unknown-code indication."""
        if code in self._definitions:
            return dict(self._definitions[code])
        logger.warning("AP trouble code %s has no returned definition", code)
        return {
            "code": code,
            "definition_status": "unknown",
            "code_key": "",
            "code_name": "",
            "code_description": "No definition returned by Mist",
        }


class RecoveryClassifier:
    """Clear only verified cloud-connectivity warnings with complete ordered evidence."""

    CONNECTIVITY_KEYS = {
        "02": "NO_ETHERNET_LINK",
        "03": "NO_IP_ADDRESS",
        "04": "NO_DEFAULT_GW",
        "05": "DEFAULT_GW_UNREACHABLE",
        "06": "NO_DNS",
        "07": "NO_DNS_RESPONSE",
        "08": "EMPTY_DNS_RESPONSE",
        "12": "CLOUD_UNREACHABLE",
        "13": "NO_CLOUD_RESPONSE",
        "14": "CLOUD_CERT_TIME_CHECK_FAILED",
        "15": "CLOUD_CERT_INVALID",
        "16": "MUTUAL_AUTH_FAILED",
    }

    @classmethod
    def classify(cls, candidate: dict[str, Any], evidence: dict[str, Any]) -> dict[str, Any]:
        """Return audit fields for retained, repeated, and recovered candidates."""
        result = cls._result(evidence)
        try:
            fresh_trouble = evidence["statistics"].get("last_trouble")
            fresh_trouble = fresh_trouble if isinstance(fresh_trouble, dict) else {}
            result.update(
                fresh_connection_status=evidence["statistics"].get("status", ""),
                fresh_trouble_code=TroubleCode.normalize(fresh_trouble.get("code")),
                fresh_trouble_timestamp=TroubleCode.timestamp(fresh_trouble.get("timestamp")),
            )
            events = RecoveryFacts.events(candidate["mac"], evidence)
            interruptions, connected = cls._transitions(events)
            result.update(interruptions_60m=interruptions, recovery_connection_at=TroubleCode.timestamp(connected))
            result["statistics_observed_at"] = TroubleCode.timestamp(evidence["statistics"].get("last_seen"))
            reason = cls._reason(candidate, evidence, (events, interruptions, connected))
        except (ValueError, TypeError, KeyError) as error:
            logger.error("Invalid AP recovery evidence for %s (%s)", candidate["mac"], type(error).__name__)
            result.update(evidence_status="invalid_evidence", recovery_reason="invalid_evidence")
            return result
        result["recovery_reason"] = reason
        result["recovery_status"] = {"verified_recovery": "recovered", "repeated_interruptions": "repeated"}.get(
            reason, "retained"
        )
        return result

    @staticmethod
    def _result(evidence: dict[str, Any]) -> dict[str, Any]:
        """Initialize explicit absent audit values without claiming recovery."""
        return {
            "recovery_status": "retained",
            "recovery_reason": "",
            "interruptions_60m": "",
            "evidence_status": evidence["evidence_status"],
            "recovery_connection_at": "",
            "history_start": TroubleCode.timestamp(evidence["history_start"]),
            "history_end": TroubleCode.timestamp(evidence["history_end"]),
            "statistics_observed_at": "",
            "fresh_connection_status": "",
            "fresh_trouble_code": "",
            "fresh_trouble_timestamp": "",
        }

    @staticmethod
    def _transitions(events: list[tuple[float, str]]) -> tuple[int, float | None]:
        """Count disconnection state changes rather than event copies or durations."""
        previous, count, connected = "", 0, None
        for timestamp, event_type in events:
            if event_type not in ("AP_CONNECTED", "AP_DISCONNECTED"):
                continue
            if event_type == "AP_DISCONNECTED" and previous != event_type:
                count += 1
            if event_type == "AP_CONNECTED":
                connected = timestamp
            previous = event_type
        return count, connected

    @classmethod
    def _reason(
        cls,
        candidate: dict[str, Any],
        evidence: dict[str, Any],
        timeline: tuple[list[tuple[float, str]], int, float | None],
    ) -> str:
        """Apply conservative recovery conditions in an explicit order."""
        events, interruptions, connected = timeline
        if interruptions >= 3:
            return "repeated_interruptions"
        if candidate["code"] not in cls.CONNECTIVITY_KEYS or cls.CONNECTIVITY_KEYS[candidate["code"]] != candidate.get(
            "code_key"
        ):
            return "code_not_verified_connectivity"
        if evidence["evidence_status"] != "complete" or not evidence["catalogue_verified"]:
            return "incomplete_history_or_catalogue"
        if not candidate["trouble_timestamp"] or connected is None:
            return "missing_trouble_time_or_connection"
        return RecoveryFacts.connection_reason(candidate, evidence, (events, connected))


class RecoveryFacts:
    """Validate independent identity, connection, and trouble conditions for recovery."""

    @staticmethod
    def events(mac: str, evidence: dict[str, Any]) -> list[tuple[float, str]]:
        """Validate identity and time, then collapse duplicate state records."""
        events: set[tuple[float, str]] = set()
        for event in evidence["events"]:
            RecoveryFacts.validate_event(event, mac)
            timestamp = TroubleCode.timestamp(event.get("timestamp"))
            if not timestamp:
                raise ValueError("An AP history record has no timestamp")
            instant = float(event["timestamp"])  # Preserve validated epoch precision at the history boundary.
            if not evidence["history_start"] <= instant <= evidence["history_end"]:
                raise ValueError("An AP history record is outside the requested window")
            events.add((instant, event["type"]))
        return sorted(events)

    @staticmethod
    def validate_event(event: dict[str, Any], mac: str) -> None:
        """Reject foreign or unidentified records before using their state changes."""
        identities = [event[key] for key in ("mac", "ap") if event.get(key)]
        if not identities or any(str(value).replace(":", "").lower() != mac for value in identities):
            raise ValueError("An AP history record has a different or missing identity")
        if not isinstance(event.get("type"), str) or not event["type"]:
            raise ValueError("An AP history record has no event type")

    @staticmethod
    def connection_reason(
        candidate: dict[str, Any], evidence: dict[str, Any], timeline: tuple[list[tuple[float, str]], float]
    ) -> str:
        """Require strict event ordering before consulting the fresh device snapshot."""
        events, connected = timeline
        trouble = datetime.fromisoformat(candidate["trouble_timestamp"]).timestamp()
        if connected <= trouble:
            return "connection_not_after_trouble"
        blockers = {"AP_DISCONNECTED", "AP_CONFIG_FAILED", "AP_RESTARTED", "AP_UNASSIGNED", "AP_UNCLAIMED"}
        if any(timestamp >= connected and event_type in blockers for timestamp, event_type in events):
            return "later_connection_blocker"
        return RecoveryFacts.fresh_reason(candidate, evidence, connected)

    @staticmethod
    def fresh_reason(candidate: dict[str, Any], evidence: dict[str, Any], connected: float) -> str:
        """Require fresh matching statistics and reject any newer trouble observation."""
        statistics = evidence["statistics"]
        mac = str(statistics.get("mac", "")).replace(":", "").lower()
        if mac != candidate["mac"] or statistics.get("site_id") != candidate["site_id"]:
            return "missing_or_mismatched_fresh_statistics"
        last_seen = TroubleCode.timestamp(statistics.get("last_seen"))
        if statistics.get("status") != "connected" or not last_seen:
            return "not_confirmed_connected"
        observed = float(statistics["last_seen"])  # Keep validated epoch precision at the evidence boundary.
        if not max(connected, evidence["history_end"] - 300) <= observed <= evidence["history_end"]:
            return "stale_or_future_statistics"
        return RecoveryFacts.trouble_reason(candidate, statistics, connected)

    @staticmethod
    def trouble_reason(candidate: dict[str, Any], statistics: dict[str, Any], connected: float) -> str:
        """A missing or newer trouble record must not become proof of recovery."""
        trouble = statistics.get("last_trouble")
        if not isinstance(trouble, dict) or trouble.get("code") is None:
            return "missing_fresh_trouble_evidence"
        code = TroubleCode.normalize(trouble["code"])
        if not code:
            return "verified_recovery"
        timestamp = TroubleCode.timestamp(trouble.get("timestamp"))
        if not timestamp:
            return "missing_fresh_trouble_time"
        if code != candidate["code"] or datetime.fromisoformat(timestamp).timestamp() >= connected:
            return "newer_or_changed_trouble"
        return "verified_recovery"
