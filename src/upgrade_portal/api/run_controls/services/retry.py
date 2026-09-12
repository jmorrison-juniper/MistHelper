"""Validate and copy safe fields for one retry run."""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import UTC, datetime
from typing import Any

from src.upgrade_portal.upgrade.options import BadOptionError, build_options

logger = logging.getLogger(__name__)

RETRYABLE_STATES = frozenset({"failed", "stopped", "cancelled"})
OPTION_FIELDS = frozenset(
    {
        "reboot",
        "junos_file_action",
        "strategy",
        "force",
        "stable_version",
        "canary",
        "rrm",
        "peer_to_peer",
        "ssr",
        "schedule",
    }
)
NESTED_OPTION_FIELDS = {
    "canary": frozenset({"canary_phases", "max_failures", "max_failure_percentage"}),
    "rrm": frozenset(
        {
            "rrm_first_batch_percentage",
            "rrm_max_batch_percentage",
            "rrm_mesh_upgrade",
            "rrm_node_order",
            "rrm_slow_ramp",
        }
    ),
    "peer_to_peer": frozenset({"enable_p2p", "p2p_cluster_size", "p2p_parallelism"}),
    "ssr": frozenset({"channel"}),
    "schedule": frozenset({"start_time_after", "reboot_at_after"}),
}


class RetryPolicyError(ValueError):
    """Report one stable retry policy refusal."""

    def __init__(self, code: str) -> None:
        """Store one safe refusal code."""
        super().__init__(code)
        self.code = code


class RetryCopyPolicy:
    """Select the newest source and rebuild its approved options."""

    def __init__(self, now: datetime) -> None:
        """Bind one aware clock value to all retry decisions."""
        if now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("The retry clock must be aware.")
        self.now = now.astimezone(UTC)

    def newest_by_site(self, records: Sequence[Mapping[str, Any]]) -> dict[str, str]:
        """Return the newest valid source identifier for each site."""
        winners: dict[str, tuple[datetime, str]] = {}
        for record in records:
            if str(record.get("state") or "") not in RETRYABLE_STATES:
                continue
            site_id = str(record.get("site_id") or "")
            run_id = str(record.get("run_id") or "")
            if not site_id or not run_id:
                continue
            try:
                updated_at = self.source_time(record)
            except RetryPolicyError:
                continue
            candidate = (updated_at, run_id)
            if site_id not in winners or candidate > winners[site_id]:
                winners[site_id] = candidate
        return {site_id: candidate[1] for site_id, candidate in winners.items()}

    def source_time(self, source: Mapping[str, Any]) -> datetime:
        """Return one valid source update time."""
        raw = source.get("updated_at")
        if not isinstance(raw, str) or not raw.strip():
            raise RetryPolicyError("retry_source_time_unknown")
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError as error:
            raise RetryPolicyError("retry_source_time_unknown") from error
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise RetryPolicyError("retry_source_time_unknown")
        normalized = parsed.astimezone(UTC)
        if normalized > self.now:
            raise RetryPolicyError("retry_source_time_unknown")
        return normalized

    def copy_options(self, source: Mapping[str, Any]) -> dict[str, Any]:
        """Return only approved options after the existing validator accepts them."""
        raw = source.get("options") or {}
        if not isinstance(raw, Mapping):
            raise RetryPolicyError("retry_options_invalid")
        unknown = set(raw).difference(OPTION_FIELDS)
        if unknown:
            raise RetryPolicyError("retry_options_unsupported")
        copied: dict[str, Any] = {}
        for name, value in raw.items():
            if name not in NESTED_OPTION_FIELDS:
                copied[name] = value
                continue
            if not isinstance(value, Mapping):
                raise RetryPolicyError("retry_options_invalid")
            if set(value).difference(NESTED_OPTION_FIELDS[name]):
                raise RetryPolicyError("retry_options_unsupported")
            copied[name] = dict(value)
        try:
            validated = build_options(copied, now=lambda: int(self.now.timestamp()))
        except BadOptionError as error:
            logger.info("The retry policy refused one invalid stored option")
            raise RetryPolicyError("retry_options_invalid") from error
        return asdict(validated)

    def copy_targets(self, source: Mapping[str, Any]) -> list[dict[str, Any]]:
        """Return an isolated copy of each stored target."""
        targets = source.get("targets") or []
        if not isinstance(targets, Sequence) or isinstance(targets, (str, bytes, bytearray)):
            raise RetryPolicyError("retry_options_invalid")
        if any(not isinstance(target, Mapping) for target in targets):
            raise RetryPolicyError("retry_options_invalid")
        return [dict(target) for target in targets]
