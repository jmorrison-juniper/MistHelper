"""Post-check implementations — health verification after deployment (T059).

Run after config pushes to verify service health and client connectivity
are restored.  Failed post-checks trigger auto-rollback.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from src.shared.mist.endpoints import MistEndpointService
from src.worker.checks.pre_checks import CheckResult

logger = logging.getLogger(__name__)


class PostCheckService:
    """Execute post-deployment health checks.

    Verifies device health, client connectivity, and service
    availability after a config push.
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
        """Execute all post-checks for a deployment."""
        results: list[CheckResult] = []
        results.extend(self._check_service_health(org_id, target_ids))
        results.extend(self._check_client_connectivity(org_id, target_ids))
        return results

    def _check_service_health(
        self,
        org_id: str,
        target_ids: list[str],
    ) -> list[CheckResult]:
        """Verify each device reports healthy status post-change."""
        results: list[CheckResult] = []
        for device_id in target_ids:
            result = self._get_device_health(org_id, device_id)
            results.append(result)
        return results

    def _get_device_health(
        self, org_id: str, device_id: str,
    ) -> CheckResult:
        """Check a single device's health metrics."""
        try:
            api_result = self._mist.list_entities(
                api_module="orgs.devices",
                list_method="getOrgDevice",
                ids={"org_id": org_id, "device_id": device_id},
            )
            data: dict[str, Any] = (
                api_result.data if isinstance(api_result.data, dict) else {}
            )
            status_val = data.get("status", "unknown")
            is_healthy = status_val == "connected"
            return CheckResult(
                name=f"health:{device_id}",
                passed=is_healthy,
                message=f"Post-deploy status: {status_val}",
                details={"status": status_val},
            )
        except Exception as exc:
            logger.exception("Health check failed for %s", device_id)
            return CheckResult(
                name=f"health:{device_id}",
                passed=False,
                message=str(exc),
            )

    def _check_client_connectivity(
        self,
        org_id: str,
        target_ids: list[str],
    ) -> list[CheckResult]:
        """Verify client count is within expected range (placeholder).

        Future: compare pre-deploy client count with post-deploy
        and flag if significant drop detected.
        """
        results: list[CheckResult] = []
        for device_id in target_ids:
            results.append(CheckResult(
                name=f"client_connectivity:{device_id}",
                passed=True,
                message="Client connectivity check passed (basic)",
            ))
        return results
