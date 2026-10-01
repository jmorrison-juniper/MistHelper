"""Data models and pure validation helpers for client session control."""

from __future__ import annotations  # WHY: keep dataclass type references simple on Python 3.13.

import logging  # WHY: required before and after validation and transformation actions.
import re  # WHY: strict MAC and BSSID validation uses one compiled expression.
from dataclasses import dataclass  # WHY: request, target, and audit rows are structured records.

from src.device.client_session_control.actions import ActionDefinition  # WHY: requests include action metadata.

logger = logging.getLogger(__name__)  # WHY: module logger supports focused troubleshooting.
_HEX_12_RE = re.compile(r"^[0-9a-f]{12}$")  # WHY: Mist expects exactly 12 lowercase hex characters.
_SEPARATOR_RE = re.compile(r"[:\-\.\s]")  # WHY: accept common MAC separators and pasted whitespace.


@dataclass(frozen=True)
class TargetIdentifier:  # WHY: normalized target data moves between prompts and requests.
    """Represent a normalized client MAC or rogue BSSID target."""

    target_type: str  # WHY: distinguishes client MAC from rogue BSSID in prompts and logs.
    raw_value: str  # WHY: original operator text helps validation messages.
    normalized_value: str  # WHY: Mist request path and confirmation compare use this value.
    display_value: str  # WHY: operator must type this exact normalized value to approve.


@dataclass(frozen=True)
class Confirmation:  # WHY: confirmation result is a first class safety record.
    """Represent the typed destructive confirmation."""

    prompt_target: str  # WHY: target shown to the operator before confirmation.
    raw_confirmation: str  # WHY: raw operator confirmation text.
    normalized_confirmation: str  # WHY: comparison uses normalized form only.
    matched: bool  # WHY: only a true match allows dry run or live execution.


@dataclass(frozen=True)
class ClientSessionControlLogRow:  # WHY: one object maps directly to one CSV audit row.
    """Represent one audit row for a client session control attempt."""

    timestamp_utc: str  # WHY: UTC timestamp lets teams correlate events across systems.
    site_id: str  # WHY: site scope is required to identify the Mist request.
    site_name: str  # WHY: site name makes audits readable.
    action_key: str  # WHY: stable action key supports filtering.
    action_label: str  # WHY: operator label supports human review.
    target_type: str  # WHY: audit distinguishes client MAC and rogue BSSID.
    target: str  # WHY: normalized target identifies what was requested.
    dry_run: bool  # WHY: dry run attempts must be easy to separate.
    confirmed: bool  # WHY: failed confirmations must be traceable.
    operation_id: str  # WHY: operation ID ties the row to the Mist endpoint.
    result: str  # WHY: success, dry run, or failure state is required.
    message: str  # WHY: short safe summary helps operator review.

    def as_dict(self) -> dict[str, str]:
        """Return the CSV ready representation for this audit row."""
        logger.info("Converting client session control log row to CSV fields")  # WHY: before transformation.
        row = {  # WHY: DictWriter needs string keyed values with a stable column order.
            "timestamp_utc": self.timestamp_utc,  # WHY: preserve UTC time.
            "site_id": self.site_id,  # WHY: preserve selected site ID.
            "site_name": self.site_name,  # WHY: preserve selected site name.
            "action_key": self.action_key,  # WHY: preserve stable action key.
            "action_label": self.action_label,  # WHY: preserve readable action label.
            "target_type": self.target_type,  # WHY: preserve target kind.
            "target": self.target,  # WHY: preserve normalized target.
            "dry_run": str(self.dry_run),  # WHY: CSV stores booleans as text.
            "confirmed": str(self.confirmed),  # WHY: CSV stores booleans as text.
            "operation_id": self.operation_id,  # WHY: preserve endpoint name.
            "result": self.result,  # WHY: preserve final result.
            "message": self.message,  # WHY: preserve safe summary text.
        }
        logger.debug("Converted log row with result %s", self.result)  # WHY: after transformation summary.
        return row  # WHY: audit writer consumes this dictionary.


@dataclass(frozen=True)
class ClientSessionControlRequest:  # WHY: request data travels as one immutable record.
    """Represent one validated client session control request attempt."""

    site_id: str  # WHY: Mist endpoint requires site scope.
    site_name: str  # WHY: operator preview and audit need readable site context.
    action: ActionDefinition  # WHY: selected action controls prompt, API function, and audit fields.
    target: TargetIdentifier  # WHY: normalized target controls confirmation and API path.
    dry_run: bool  # WHY: run mode decides whether to send or preview only.

    def log_row(self, confirmed: bool, result: str, message: str, timestamp_utc: str) -> ClientSessionControlLogRow:
        """Build the audit row for this request attempt."""
        logger.info("Building client session control audit row")  # WHY: before row transformation.
        row = ClientSessionControlLogRow(  # WHY: centralize row construction for consistent fields.
            timestamp_utc=timestamp_utc,  # WHY: caller supplies deterministic or real UTC time.
            site_id=self.site_id,  # WHY: selected Mist site ID.
            site_name=self.site_name,  # WHY: selected Mist site name.
            action_key=self.action.action_key,  # WHY: stable action key.
            action_label=self.action.label,  # WHY: readable action label.
            target_type=self.action.target_type,  # WHY: target type from action contract.
            target=self.target.normalized_value,  # WHY: normalized MAC or BSSID.
            dry_run=self.dry_run,  # WHY: capture dry run mode.
            confirmed=confirmed,  # WHY: capture destructive confirmation status.
            operation_id=self.action.operation_id,  # WHY: Mist operation ID.
            result=result,  # WHY: final result value.
            message=message,  # WHY: safe result summary.
        )
        logger.debug("Built audit row for result %s", result)  # WHY: after row transformation.
        return row  # WHY: caller sends row to the audit writer.


def normalize_target(raw_value: str) -> str:
    """Normalize a MAC or BSSID to lowercase colon-free form."""
    logger.info("Normalizing client session control target")  # WHY: before validation and transformation.
    compact_value = _SEPARATOR_RE.sub("", str(raw_value)).lower()  # WHY: remove accepted separators and lower case.
    if not _HEX_12_RE.fullmatch(compact_value):  # WHY: reject anything Mist cannot accept as a target.
        logger.debug("Rejected target after normalization with length %s", len(compact_value))  # WHY: after failure.
        raise ValueError("Enter a valid 12 digit hexadecimal MAC or BSSID.")  # WHY: stop before confirmation.
    logger.debug("Normalized client session control target to %s", compact_value)  # WHY: after transformation.
    return compact_value  # WHY: caller uses this in previews, confirmation, API paths, and audit rows.


def build_target(target_type: str, raw_value: str) -> TargetIdentifier:
    """Build a normalized target identifier from operator input."""
    logger.info("Building client session control target identifier")  # WHY: before target construction.
    normalized_value = normalize_target(raw_value)  # WHY: validate and convert the operator input.
    target = TargetIdentifier(target_type, raw_value, normalized_value, normalized_value)  # WHY: display equals normal.
    logger.debug("Built target identifier for type %s", target_type)  # WHY: after target construction.
    return target  # WHY: handler carries target as structured data.


def build_confirmation(prompt_target: str, raw_confirmation: str) -> Confirmation:
    """Build a normalized confirmation result for a destructive request."""
    logger.info("Building client session control confirmation")  # WHY: before confirmation normalization.
    try:
        normalized_confirmation = normalize_target(raw_confirmation)  # WHY: support equivalent confirmation formats.
    except ValueError:
        logger.debug("Confirmation normalization failed")  # WHY: after failed normalization.
        normalized_confirmation = ""  # WHY: invalid confirmation can never match the prompt target.
    matched = normalized_confirmation == prompt_target  # WHY: exact normalized comparison is the safety gate.
    confirmation = Confirmation(  # WHY: record the full confirmation state for audits and tests.
        prompt_target,
        raw_confirmation,
        normalized_confirmation,
        matched,
    )
    logger.debug("Built confirmation with matched=%s", matched)  # WHY: after confirmation build.
    return confirmation  # WHY: handler uses matched flag to continue or stop.


def confirmation_matches(prompt_target: str, raw_confirmation: str) -> bool:
    """Return True when confirmation matches the normalized prompt target."""
    logger.info("Checking client session control confirmation match")  # WHY: before safety check.
    confirmation = build_confirmation(prompt_target, raw_confirmation)  # WHY: normalize and compare once.
    logger.debug("Confirmation match result is %s", confirmation.matched)  # WHY: after safety check.
    return confirmation.matched  # WHY: tests and handler need a simple boolean result.
