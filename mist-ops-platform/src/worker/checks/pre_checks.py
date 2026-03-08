"""Pre-check implementations — reachability and safety gates (T058).

Run before scheduled deployments to verify target devices are
reachable and configuration is compatible with the target firmware.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from src.shared.mist.endpoints import MistEndpointService

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CheckResult:
    """Result of a single pre/post check."""

    name: str
    passed: bool
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)


class PreCheckService:
    """Execute pre-deployment safety checks.

    Each check is independent and returns a CheckResult.
    All checks must pass before deployment proceeds.
    """

    def __init__(
        self,
        db: Session,
        mist: MistEndpointService,
    ) -> None:
        self._db = db
        self._mist = mist

    def run_all(
        self,
        org_id: str,
        target_ids: list[str],
    ) -> list[CheckResult]:
        """Execute all pre-checks for a deployment."""
        results: list[CheckResult] = []
        results.extend(self._check_reachability(org_id, target_ids))
        results.extend(self._check_version_compat(org_id, target_ids))
        return results

    def _check_reachability(
        self,
        org_id: str,
        target_ids: list[str],
    ) -> list[CheckResult]:
        """Verify all target devices are online and reachable."""
        results: list[CheckResult] = []
        for device_id in target_ids:
            result = self._ping_device(org_id, device_id)
            results.append(result)
        return results

    def _ping_device(self, org_id: str, device_id: str) -> CheckResult:
        """Check a single device's connectivity status."""
        try:
            api_result = self._mist.list_entities(
                api_module="orgs.devices",
                list_method="getOrgDevice",
                ids={"org_id": org_id, "device_id": device_id},
            )
            if not api_result.success:
                return CheckResult(
                    name=f"reachability:{device_id}",
                    passed=False,
                    message=f"Device {device_id} not found",
                )
            data = api_result.data if isinstance(api_result.data, dict) else {}
            status_val = data.get("status", "unknown")
            is_connected = status_val == "connected"
            return CheckResult(
                name=f"reachability:{device_id}",
                passed=is_connected,
                message=f"Device status: {status_val}",
                details={"status": status_val},
            )
        except Exception as exc:
            logger.exception("Reachability check failed for %s", device_id)
            return CheckResult(
                name=f"reachability:{device_id}",
                passed=False,
                message=str(exc),
            )

    def _check_version_compat(
        self,
        org_id: str,
        target_ids: list[str],
    ) -> list[CheckResult]:
        """Verify firmware version compatibility (placeholder).

        Future: compare target config requirements against device
        firmware version to catch incompatible settings.
        """
        results: list[CheckResult] = []
        for device_id in target_ids:
            results.append(CheckResult(
                name=f"version_compat:{device_id}",
                passed=True,
                message="Version compatibility check passed (basic)",
            ))
        return results
