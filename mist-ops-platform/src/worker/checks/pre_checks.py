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
        self._db = db  # WHY: keep the DB session for future checks that need it.
        self._mist = mist  # WHY: shared Mist client used for the one inventory fetch.

    def run_all(
        self,
        org_id: str,
        target_ids: list[str],
    ) -> list[CheckResult]:
        """Execute all pre-checks for a deployment."""
        logger.info(
            "Running pre-checks for org %s on %d targets",
            org_id,
            len(target_ids),
        )  # WHY: log before the check run starts.
        # WHY: one shared fetch for every check.
        device_index, fetch_error = self._fetch_device_index(org_id, target_ids)
        results: list[CheckResult] = []  # WHY: collect results from every check kind.
        results.extend(
            self._check_reachability(target_ids, device_index, fetch_error),
        )  # WHY: reachability now reads the shared index, not a per-device fetch.
        results.extend(self._check_version_compat(org_id, target_ids))
        logger.debug(
            "Pre-checks for org %s produced %d results",
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
        # WHY: log before the single shared call.
        logger.info("Fetching device inventory once for org %s", org_id)
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

    def _check_reachability(
        self,
        target_ids: list[str],
        device_index: dict[str, dict[str, Any]],
        fetch_error: str | None,
    ) -> list[CheckResult]:
        """Verify all target devices are online, using the shared index."""
        results: list[CheckResult] = []  # WHY: one result per target device.
        for device_id in target_ids:  # WHY: no per-device API call, only a dict lookup.
            # WHY: evaluate against the shared index.
            result = self._ping_device(device_id, device_index, fetch_error)
            results.append(result)  # WHY: preserve per-device isolation in the result list.
        return results

    @staticmethod
    def _ping_device(
        device_id: str,
        device_index: dict[str, dict[str, Any]],
        fetch_error: str | None,
    ) -> CheckResult:
        """Check one device's connectivity from the shared inventory index."""
        if fetch_error is not None:  # WHY: the shared fetch failed, so no device can be verified.
            return CheckResult(
                name=f"reachability:{device_id}",
                passed=False,
                message=f"Inventory fetch failed: {fetch_error}",
            )
        # WHY: O(1) lookup instead of a per-device API call.
        device_data = device_index.get(device_id)
        if device_data is None:
            return CheckResult(
                name=f"reachability:{device_id}",
                passed=False,
                message=f"Device {device_id} not found",
            )
        status_val = device_data.get("status", "unknown")  # WHY: read the cached status field.
        is_connected = status_val == "connected"  # WHY: connected is the only passing state.
        return CheckResult(
            name=f"reachability:{device_id}",
            passed=is_connected,
            message=f"Device status: {status_val}",
            details={"status": status_val},
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
            results.append(
                CheckResult(
                    name=f"version_compat:{device_id}",
                    passed=True,
                    message="Version compatibility check passed (basic)",
                )
            )
        return results
