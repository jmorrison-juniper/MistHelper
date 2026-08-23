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
        self._db = db  # WHY: keep the DB session for future checks that need it.
        self._mist = mist  # WHY: shared Mist client used for the one inventory fetch.

    def run_all(
        self,
        org_id: str,
        target_ids: list[str],
    ) -> list[CheckResult]:
        """Execute all post-checks for a deployment."""
        logger.info(
            "Running post-checks for org %s on %d targets",
            org_id,
            len(target_ids),
        )  # WHY: log before the check run starts.
        # WHY: one shared fetch for every check.
        device_index, fetch_error = self._fetch_device_index(org_id, target_ids)
        results: list[CheckResult] = []  # WHY: collect results from every check kind.
        results.extend(
            self._check_service_health(target_ids, device_index, fetch_error),
        )  # WHY: health check now reads the shared index, not a per-device fetch.
        results.extend(self._check_client_connectivity(org_id, target_ids))
        logger.debug(
            "Post-checks for org %s produced %d results",
            org_id,
            len(results),
        )  # WHY: summarize the outcome after the run.
        return results

    def _fetch_device_index(
        self,
        org_id: str,
        target_ids: list[str],
    ) -> tuple[dict[str, dict[str, Any]], str | None]:
        """Fetch the org device inventory once, indexed by device id.

        Returns an empty index and no error when there are no targets,
        so a run with zero devices makes zero inventory calls.
        """
        if not target_ids:
            return {}, None  # WHY: skip the network call when there is nothing to check.
        logger.info("Fetching device inventory once for org %s", org_id)  # WHY: log before the single shared call.
        try:
            api_result = self._mist.list_all_entities(
                "org_device_list",
                ids={"org_id": org_id},
            )  # WHY: exactly one call regardless of target device count. Fixes #1886.
            # WHY: guard a non-list payload.
            data_list = api_result.data if isinstance(api_result.data, list) else []
            # WHY: key by device id for O(1) lookup.
            index = {d.get("id"): d for d in data_list if d.get("id")}
            logger.debug(
                "Indexed %d devices for org %s",
                len(index),
                org_id,
            )  # WHY: confirm the fetch result size after the call.
            return index, None
        except Exception as exc:
            # WHY: preserve the failure detail.
            logger.exception("Device inventory fetch failed for org %s", org_id)
            return {}, str(exc)

    def _check_service_health(
        self,
        target_ids: list[str],
        device_index: dict[str, dict[str, Any]],
        fetch_error: str | None,
    ) -> list[CheckResult]:
        """Verify each device reports healthy status, using the shared index."""
        results: list[CheckResult] = []  # WHY: one result per target device.
        for device_id in target_ids:  # WHY: no per-device API call, only a dict lookup.
            # WHY: evaluate against the shared index.
            result = self._get_device_health(device_id, device_index, fetch_error)
            results.append(result)  # WHY: preserve per-device isolation in the result list.
        return results

    @staticmethod
    def _get_device_health(
        device_id: str,
        device_index: dict[str, dict[str, Any]],
        fetch_error: str | None,
    ) -> CheckResult:
        """Check one device's health from the shared inventory index."""
        if fetch_error is not None:  # WHY: the shared fetch failed, so no device can be verified.
            return CheckResult(
                name=f"health:{device_id}",
                passed=False,
                message=f"Inventory fetch failed: {fetch_error}",
            )
        # WHY: same default-empty-dict lookup as before.
        device_data: dict[str, Any] = device_index.get(device_id, {})
        status_val = device_data.get("status", "unknown")  # WHY: read the cached status field.
        is_healthy = status_val == "connected"  # WHY: connected is the only healthy state.
        return CheckResult(
            name=f"health:{device_id}",
            passed=is_healthy,
            message=f"Post-deploy status: {status_val}",
            details={"status": status_val},
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
            results.append(
                CheckResult(
                    name=f"client_connectivity:{device_id}",
                    passed=True,
                    message="Client connectivity check passed (basic)",
                )
            )
        return results
