"""Pre-check implementations — reachability and safety gates (T058).

Run before scheduled deployments to verify target devices are
reachable and configuration is compatible with the target firmware.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from packaging.version import InvalidVersion, Version

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from src.shared.mist.endpoints import MistEndpointService

logger = logging.getLogger(__name__)

HTTP_OK = 200  # WHY: name the lower bound for a successful API response.
HTTP_MULTIPLE_CHOICES = 300  # WHY: name the upper bound for a successful API response.
HTTP_FORBIDDEN = 403  # WHY: name the permission failure status that needs a clear message.


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
        check_defs: list[dict[str, Any]] | None = None,
    ) -> list[CheckResult]:
        """Execute all pre-checks for a deployment."""
        logger.info(
            "Running pre-checks for org %s on %d targets",
            org_id,
            len(target_ids),
        )  # WHY: log before the check run starts.
        if not target_ids:  # WHY: a safety gate cannot pass when it evaluates no device.
            logger.warning(
                "Pre-checks for org %s received zero targets",
                org_id,
            )  # WHY: a missing target set is an operator signal.
            result = CheckResult(
                name="target_selection",
                passed=False,
                message="No target devices were supplied for the pre-check",
                details={"target_count": 0},
            )  # WHY: return explicit evidence instead of an empty success.
            logger.debug(
                "Pre-checks for org %s stopped with %s",
                org_id,
                result.message,
            )  # WHY: summarize the fail-closed result.
            return [result]  # WHY: the caller must store one failed checkpoint.
        # WHY: one shared fetch for every check.
        device_index, fetch_error = self._fetch_device_index(org_id, target_ids)
        results: list[CheckResult] = []  # WHY: collect results from every check kind.
        results.extend(
            self._check_reachability(target_ids, device_index, fetch_error),
        )  # WHY: reachability now reads the shared index, not a per-device fetch.
        results.extend(
            self._check_version_compat(org_id, target_ids, device_index, check_defs)
        )  # WHY: compare firmware only after the inventory fetch supplies versions.
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
            status_error = self._read_status_error(org_id, api_result)  # WHY: verify success.
            if status_error is not None:  # WHY: failed API status cannot prove safety.
                return {}, status_error  # WHY: carry the status error to every target result.
            # WHY: guard a non-list payload.
            data_list = api_result.data if isinstance(api_result.data, list) else []
            index: dict[str, dict[str, Any]] = {}  # WHY: key rows for O(1) lookup.
            for row in data_list:  # WHY: keep only rows with a stable device id.
                device_id = row.get("id")  # WHY: Mist stores the device id in this field.
                if device_id:  # WHY: rows without ids cannot match a target.
                    index[str(device_id)] = row  # WHY: normalize keys before lookup.
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

    @staticmethod
    def _read_status_error(org_id: str, api_result: object) -> str | None:
        """Return an inventory status error, if the API call failed."""
        raw_status = getattr(api_result, "status_code", HTTP_OK)  # WHY: old tests omit status.
        status_code = int(raw_status)  # WHY: compare status values as numbers.
        if status_code == HTTP_FORBIDDEN:  # WHY: a permission failure is not a missing device.
            logger.warning(
                "Device inventory fetch for org %s returned permission denied",
                org_id,
            )  # WHY: tell the operator that access blocked the safety gate.
            return "Permission denied while fetching device inventory"  # WHY: fail closed.
        if not HTTP_OK <= status_code < HTTP_MULTIPLE_CHOICES:  # WHY: success proves safety.
            logger.warning(
                "Device inventory fetch for org %s returned status %s",
                org_id,
                status_code,
            )  # WHY: tell the operator that the API call did not succeed.
            return f"Inventory fetch returned status {status_code}"  # WHY: fail closed.
        return None  # WHY: success status permits inventory evaluation.

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
            result = self._safe_ping_device(device_id, device_index, fetch_error)
            results.append(result)  # WHY: preserve per-device isolation in the result list.
        return results

    def _safe_ping_device(
        self,
        device_id: str,
        device_index: dict[str, dict[str, Any]],
        fetch_error: str | None,
    ) -> CheckResult:
        """Return one reachability result, even when a target check fails."""
        logger.info("Checking reachability for device %s", device_id)  # WHY: log before work.
        try:
            result = self._ping_device(device_id, device_index, fetch_error)  # WHY: run gate.
        except Exception as exc:
            logger.exception(
                "Reachability check failed for device %s",
                device_id,
            )  # WHY: keep the traceback for the failed target.
            return CheckResult(
                name=f"reachability:{device_id}",
                passed=False,
                message=f"Reachability check failed: {exc}",
            )  # WHY: a raised target check must fail closed.
        if result is None:  # WHY: a missing verdict cannot prove that the device is safe.
            logger.warning("Reachability check returned no result for device %s", device_id)
            return CheckResult(
                name=f"reachability:{device_id}",
                passed=False,
                message="Reachability check returned no result",
            )  # WHY: an absent verdict must fail closed.
        logger.debug(
            "Reachability check for device %s returned passed=%s",
            device_id,
            result.passed,
        )  # WHY: summarize the per-device verdict.
        return result  # WHY: give the caller the checked verdict.

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
        device_index: dict[str, dict[str, Any]],
        check_defs: list[dict[str, Any]] | None,
    ) -> list[CheckResult]:
        """Verify each target meets the requested minimum firmware version."""
        min_version = self._read_min_version(check_defs)  # WHY: use the operator's safety gate.
        if min_version is None:
            logger.warning(
                "Version compatibility check skipped for org %s because min_version is missing",
                org_id,
            )  # WHY: tell the operator why no comparison can run.
            return []  # WHY: an absent gate must not block jobs that did not request it.
        results: list[CheckResult] = []  # WHY: return one compatibility verdict per target.
        for device_id in target_ids:  # WHY: each device can run a different firmware version.
            result = self._check_device_version(
                device_id,
                device_index,
                min_version,
            )  # WHY: isolate one comparison.
            results.append(result)  # WHY: preserve the per-device compatibility result.
        return results  # WHY: give the caller all comparison results.

    @staticmethod
    def _read_min_version(check_defs: list[dict[str, Any]] | None) -> str | None:
        """Read the minimum version from the pre-check definitions."""
        for check_def in check_defs or []:  # WHY: an absent list means no version gate.
            check_type = str(check_def.get("type", ""))  # WHY: normalize the operator input.
            if check_type not in {
                "version_compat",
                "version_compatibility",
            }:  # WHY: ignore other check types.
                continue  # WHY: another pre-check definition owns this entry.
            min_version = check_def.get("min_version")  # WHY: this value defines the safe floor.
            if min_version is None:  # WHY: a blank floor is not a real gate.
                return None  # WHY: no value means no comparison can run.
            return str(min_version)  # WHY: normalize the floor to text for parsing.
        return None  # WHY: no version gate was configured.

    @staticmethod
    def _check_device_version(
        device_id: str,
        device_index: dict[str, dict[str, Any]],
        min_version: str,
    ) -> CheckResult:
        """Compare one device firmware version with the configured floor."""
        logger.info("Checking firmware version for device %s", device_id)  # WHY: log first.
        device_data = device_index.get(device_id)  # WHY: use the shared inventory page.
        current_version = PreCheckService._read_device_version(device_data)  # WHY: read version.
        passed, message = PreCheckService._compare_versions(
            current_version,
            min_version,
        )  # WHY: one helper owns parsing.
        logger.debug(
            "Firmware version check for device %s returned passed=%s",
            device_id,
            passed,
        )  # WHY: summarize the comparison without logging secrets.
        return CheckResult(
            name=f"version_compat:{device_id}",
            passed=passed,
            message=message,
            details={"current_version": current_version, "min_version": min_version},
        )  # WHY: return the evidence that supports the verdict.

    @staticmethod
    def _read_device_version(device_data: dict[str, Any] | None) -> str | None:
        """Read the device firmware version from an inventory row."""
        if device_data is None:  # WHY: a missing device cannot prove compatibility.
            return None  # WHY: the caller reports a failed compatibility check.
        version_value = device_data.get("firmware_version")  # WHY: prefer the DB field name.
        if version_value is None:  # WHY: Mist inventory can use a shorter field name.
            version_value = device_data.get("version")  # WHY: read the Mist field name.
        if version_value is None:  # WHY: no value means no proof.
            return None  # WHY: the comparison must fail closed.
        return str(version_value)  # WHY: normalize the version before parsing.

    @staticmethod
    def _compare_versions(current_version: str | None, min_version: str) -> tuple[bool, str]:
        """Return the compatibility verdict for two version strings."""
        if current_version is None:  # WHY: no firmware value blocks proof.
            return False, "Device firmware version is not available"  # WHY: fail closed.
        try:
            passed = Version(current_version) >= Version(min_version)  # WHY: compare by segment.
        except InvalidVersion:
            return False, "Device firmware version could not be parsed"  # WHY: fail closed.
        message = f"Device version {current_version} is at least {min_version}"  # WHY: prove pass.
        if not passed:  # WHY: a lower version blocks the deployment.
            message = f"Device version {current_version} is below {min_version}"  # WHY: fail.
        return passed, message  # WHY: the caller needs both the verdict and the reason.
