"""Dry-run validation logic (T065).

Validates a configuration change without applying it.
Computes risk score, blast radius, policy violations,
and schema warnings per FR-036 / SC-013 (<10s).
"""

from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.deploy import (
    BlastRadius,
    DryRunRequest,
    DryRunResponse,
)
from src.shared.models.governance import NetworkPolicy
from src.shared.models.inventory import Device, Site

logger = logging.getLogger(__name__)

# Risk thresholds
HIGH_DEVICE_THRESHOLD = 50
MEDIUM_DEVICE_THRESHOLD = 10
HIGH_RISK_KEYS = frozenset(
    {
        "firmware_version",
        "radio_config",
        "ip_config",
        "port_config",
        "vlan_config",
        "routing",
    }
)


class DryRunValidator:
    """Stateless validator for dry-run change assessment.

    Runs schema checks, policy checks, and blast radius
    estimation against the database state.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def validate(self, request: DryRunRequest) -> DryRunResponse:
        """Run all validation checks and return combined result."""
        schema_errors = _check_schema(request)
        blast = await self._estimate_blast_radius(request)
        violations = await self._check_policies(request)
        warnings = _check_warnings(request)

        risk_score = _compute_risk_score(blast, violations, warnings)
        risk_level = _score_to_level(risk_score)

        valid = len(schema_errors) == 0 and len(violations) == 0
        return DryRunResponse(
            valid=valid,
            risk_score=risk_score,
            risk_level=risk_level,
            blast_radius=blast,
            warnings=warnings,
            policy_violations=violations,
            schema_errors=schema_errors,
        )

    async def _estimate_blast_radius(
        self,
        request: DryRunRequest,
    ) -> BlastRadius:
        """Count affected devices, sites, and estimated clients."""
        device_ids: list[UUID] = []
        site_ids: list[UUID] = []

        for target in request.target_entities:
            if target.entity_type == "device":
                device_ids.append(target.entity_id)
            elif target.entity_type == "site":
                site_ids.append(target.entity_id)

        devices_affected = len(device_ids)
        sites_affected = len(site_ids)

        if site_ids:
            count = await self._count_devices_in_sites(site_ids)
            devices_affected += count

        if device_ids:
            extra_sites = await self._count_distinct_sites(device_ids)
            sites_affected += extra_sites

        estimated_clients = devices_affected * 15

        return BlastRadius(
            devices_affected=devices_affected,
            sites_affected=sites_affected,
            estimated_clients_affected=estimated_clients,
        )

    async def _count_devices_in_sites(
        self,
        site_ids: list[UUID],
    ) -> int:
        """Count devices belonging to given sites."""
        stmt = select(func.count()).select_from(Device).where(Device.site_id.in_(site_ids))
        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def _count_distinct_sites(
        self,
        device_ids: list[UUID],
    ) -> int:
        """Count distinct sites for given devices."""
        stmt = select(func.count(func.distinct(Device.site_id))).where(Device.device_id.in_(device_ids))
        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def _check_policies(
        self,
        request: DryRunRequest,
    ) -> list[str]:
        """Check change payload against active network policies."""
        stmt = select(NetworkPolicy).where(
            NetworkPolicy.org_id == request.org_id,
            NetworkPolicy.status == "active",
        )
        policies = (await self._db.execute(stmt)).scalars().all()
        violations: list[str] = []

        for policy in policies:
            rules = policy.rules or {}
            _evaluate_policy(rules, request.change_payload, violations)

        return violations


# -- Pure functions (no DB) ---


def _check_schema(request: DryRunRequest) -> list[str]:
    """Validate the change payload structure."""
    errors: list[str] = []
    if not request.change_payload:
        errors.append("change_payload must not be empty")
    if not request.target_entities:
        errors.append("target_entities must contain at least one entry")
    return errors


def _check_warnings(request: DryRunRequest) -> list[str]:
    """Generate human-readable warnings for risky settings."""
    warnings: list[str] = []
    payload = request.change_payload

    radio_cfg = payload.get("radio_config", {})
    for band_key in ("band_24", "band_5", "band_6"):
        band = radio_cfg.get(band_key, {})
        power = band.get("power")
        if isinstance(power, int) and power > 20:
            warnings.append(f"Power level {power} exceeds recommended maximum " f"(20) for indoor APs on {band_key}")

    if "firmware_version" in payload:
        warnings.append("Firmware changes carry elevated risk; " "consider a phased rollout")

    return warnings


def _compute_risk_score(
    blast: BlastRadius,
    violations: list[str],
    warnings: list[str],
) -> float:
    """Compute a 0.0-1.0 risk score."""
    score = 0.0

    if blast.devices_affected >= HIGH_DEVICE_THRESHOLD:
        score += 0.4
    elif blast.devices_affected >= MEDIUM_DEVICE_THRESHOLD:
        score += 0.2
    else:
        score += 0.05

    score += len(violations) * 0.2
    score += len(warnings) * 0.05
    return min(score, 1.0)


def _score_to_level(score: float) -> str:
    """Convert numeric risk score to a human label."""
    if score >= 0.7:
        return "high"
    if score >= 0.4:
        return "medium"
    return "low"


def _evaluate_policy(
    rules: dict,
    payload: dict,
    violations: list[str],
) -> None:
    """Evaluate a single policy's rules against the payload."""
    blocked_keys = rules.get("blocked_keys", [])
    for key in blocked_keys:
        if key in payload:
            violations.append(f"Policy violation: key '{key}' is blocked")

    max_devices = rules.get("max_devices_per_change")
    if max_devices is not None:
        targets = payload.get("target_count", 0)
        if isinstance(targets, int) and targets > max_devices:
            violations.append(f"Exceeds max devices per change ({max_devices})")
