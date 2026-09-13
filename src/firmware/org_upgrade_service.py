"""Submit, read, and cancel organization AP upgrade jobs.

Why:
    The organization response contains separate site upgrade entries. The
    existing site service cannot preserve that structure. This isolated service
    keeps those entries and every target array without deriving a final state.
    Both ``site_upgrades`` and ``upgrades`` retain their original names.

    The local contract names ``upgradeOrgDevices``, ``getOrgDeviceUpgrade``,
    and ``cancelOrgDeviceUpgrade`` in ``mistapi.api.v1.orgs.devices``.
    Cancellation is best effort. It does not reverse a completed upgrade.
    The caller owns authorization, confirmation, and the authenticated session.
    Transport exceptions propagate. The service never retries an uncertain write.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass

from mistapi import APISession
from mistapi.api.v1.orgs import devices as org_devices
from requests.adapters import HTTPAdapter

from src.firmware.org_upgrade_body import OrgUpgradeBody

logger = logging.getLogger(__name__)


class OrgUpgradeSession(APISession):  # type: ignore[misc]
    """Disable the SDK retry loop for an isolated upgrade session.

    Why:
        The installed mistapi 0.63.3 SDK retries POST requests after HTTP 429.
        This session disables that loop without changing another caller's
        session or the SDK class. Keep transport-level retries disabled too.
        The SDK has no typing marker, so mypy needs the local base-class exception.
    """

    _MAX_429_RETRIES = 0


@dataclass(frozen=True, slots=True)
class OrgUpgradeResult:
    """Keep the request outcome separate from each site's upgrade state.

    Why:
        HTTP 200 does not prove that a device completed an upgrade. The data
        retains the cloud structure, including absent fields and empty arrays.
        A response error must not look like an empty successful job.

    Attributes:
        org_id: The organization that the caller selected.
        upgrade_id: The job identifier, or None when the identifier is unknown.
        raw_status: The HTTP status code, or zero when no valid code exists.
        data: A detached copy of the response object, including both site fields.
        error: The response error, or None for a valid HTTP 200 response.
    """

    org_id: str
    upgrade_id: str | None
    raw_status: int
    data: Mapping[str, object]
    error: str | None


class _OrgUpgradeResponse:
    """Normalize the SDK response without collapsing site results.

    Why:
        A failed request and a malformed successful response need explicit
        errors. Both must retain any response object that the SDK supplied.
    """

    _TARGET_ARRAYS = (
        "download_requested",
        "downloaded",
        "downloading",
        "failed",
        "reboot_in_progress",
        "rebooted",
        "scheduled",
        "skipped",
        "upgraded",
    )

    @classmethod
    def normalize(
        cls, response: object, org_id: str, upgrade_id: str | None = None, *, cancel: bool = False
    ) -> OrgUpgradeResult:
        """Return the HTTP outcome and a detached response object.

        Why:
            The read and cancel paths already identify the requested job.
            A mismatched response identifier must not replace that identity.
        """
        code: object = getattr(response, "status_code", None)
        raw_status = code if type(code) is int and 100 <= code <= 599 else 0
        raw_data: object = getattr(response, "data", None)
        data = cls._copy_data(raw_data)
        error = None
        try:
            cls._check_http(response, raw_status, raw_data, cancel)
            upgrade_id = cls._response_id(data, upgrade_id, cancel)
            cls._check_sites(data)
        except ValueError as problem:
            error = str(problem)
        return OrgUpgradeResult(org_id, upgrade_id, raw_status, data, error)

    @staticmethod
    def _copy_data(raw_data: object) -> dict[str, object]:
        """Detach a response object that has string keys."""
        if not isinstance(raw_data, Mapping) or any(not isinstance(key, str) for key in raw_data):
            return {}
        return deepcopy(dict(raw_data))

    @staticmethod
    def _response_id(data: Mapping[str, object], expected: str | None, cancel: bool) -> str | None:
        """Return the response identifier and reject a mismatch."""
        if cancel and "id" not in data:
            return expected
        received = OrgUpgradeBody.identifier(data.get("id"), "response id")
        if expected is not None and received != expected:
            raise ValueError("The response names a different upgrade job.")
        return received

    @classmethod
    def _check_http(cls, response: object, status: int, data: object, cancel: bool) -> None:
        """Reject HTTP errors and invalid successful response bodies.

        Why:
            The SDK can retain an empty object after a JSON parse failure.
            A proxy response must not look like a successful cancellation.
        """
        cls._check_status(status)
        raw_text: object = getattr(response, "raw_data", "")
        empty_cancel = cancel and (data is None or data == {}) and raw_text in ("", None)
        if not isinstance(data, Mapping) and not empty_cancel:
            raise ValueError("The upgrade response must contain a JSON object.")
        cls._check_content(response, empty_cancel)
        cls._check_response_object(data)

    @staticmethod
    def _check_status(status: int) -> None:
        """Reject a missing or unsuccessful HTTP status."""
        if status == 0:
            raise ValueError("The cloud returned no valid HTTP status. The request outcome is unknown.")
        if status != 200:
            raise ValueError(f"The cloud returned HTTP {status}.")

    @staticmethod
    def _check_response_object(data: object) -> None:
        """Reject non-string keys and explicit cloud errors."""
        if not isinstance(data, Mapping):
            return
        if any(not isinstance(key, str) for key in data) or data.get("error"):
            raise ValueError("The cloud returned an invalid upgrade object or an error.")

    @staticmethod
    def _check_content(response: object, empty_cancel: bool) -> None:
        """Check available content metadata and raw JSON.

        Why:
            A JSON parse failure can leave the SDK data field empty. A valid
            empty JSON object must remain distinct from that failure.
        """
        if empty_cancel:
            return
        headers: object = getattr(response, "headers", None)
        if isinstance(headers, Mapping):
            media_type = headers.get("Content-Type", headers.get("content-type"))
            if media_type is not None and (
                not isinstance(media_type, str)
                or media_type.split(";", 1)[0].strip().lower() not in ("application/json", "application/vnd.api+json")
            ):
                raise ValueError("The upgrade response has an unsupported content type.")
        raw_text: object = getattr(response, "raw_data", "")
        if raw_text not in ("", None):
            if not isinstance(raw_text, str):
                raise ValueError("The upgrade response must contain JSON text.")
            try:
                parsed = json.loads(raw_text)
            except json.JSONDecodeError as error:
                raise ValueError("The upgrade response contains invalid JSON.") from error
            if not isinstance(parsed, Mapping):
                raise ValueError("The upgrade response must contain a JSON object.")

    @classmethod
    def _check_sites(cls, data: Mapping[str, object]) -> None:
        """Validate site entries without removing fields or reordering arrays.

        Why:
            The OpenAPI ``upgrade_org_devices_item`` schema uses ``site_upgrades``.
            The saved guide uses ``upgrades``. If both fields exist, validate both.
        """
        for field in ("site_upgrades", "upgrades"):
            if field not in data:
                continue
            entries = data[field]
            if not isinstance(entries, list):
                raise ValueError(f"The {field} response field must contain an array.")
            for entry in entries:
                cls._check_site_entry(entry)

    @classmethod
    def _check_site_entry(cls, entry: object) -> None:
        """Validate a site reference or a nested site upgrade record.

        Why:
            The sources contain references with ``upgrade_id`` and full records
            with ``upgrade``. An invalid identifier or target array must not
            bypass validation.
        """
        if not isinstance(entry, Mapping):
            raise ValueError("Each site upgrade entry must contain an object.")
        OrgUpgradeBody.identifier(entry.get("site_id"), "response site_id")
        if "upgrade_id" in entry:
            OrgUpgradeBody.identifier(entry["upgrade_id"], "site upgrade_id")
            if "upgrade" not in entry:
                return
        upgrade = entry.get("upgrade")
        if not isinstance(upgrade, Mapping):
            raise ValueError("Each site upgrade entry needs an upgrade_id or an upgrade object.")
        OrgUpgradeBody.identifier(upgrade.get("id"), "site upgrade id")
        cls._check_site_state(upgrade)

    @classmethod
    def _check_site_state(cls, upgrade: Mapping[str, object]) -> None:
        """Check known state fields while preserving unknown state words.

        Why:
            A new cloud state must remain visible. The service does not infer
            completion from a state word, a missing field, or an HTTP status.
        """
        cls._check_state_scalars(upgrade)
        if "targets" not in upgrade:
            return
        targets = upgrade["targets"]
        if not isinstance(targets, Mapping):
            raise ValueError("The site upgrade targets must contain an object.")
        cls._check_target_arrays(targets)
        cls._check_target_total(targets)

    @staticmethod
    def _check_state_scalars(upgrade: Mapping[str, object]) -> None:
        """Validate the optional site status and start time."""
        if "status" in upgrade and not isinstance(upgrade["status"], str):
            raise ValueError("The site upgrade status must contain a string.")
        start_time = upgrade.get("start_time")
        if "start_time" in upgrade and (type(start_time) is not int or start_time < 0):
            raise ValueError("The site upgrade start_time must contain a nonnegative integer.")

    @classmethod
    def _check_target_arrays(cls, targets: Mapping[str, object]) -> None:
        """Validate each optional target-state array."""
        for field in cls._TARGET_ARRAYS:
            if field not in targets:
                continue
            values = targets[field]
            if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
                raise ValueError(f"The targets field {field} must contain an array of strings.")

    @staticmethod
    def _check_target_total(targets: Mapping[str, object]) -> None:
        """Validate the optional total target count."""
        total = targets.get("total")
        if "total" in targets and (type(total) is not int or total < 0):
            raise ValueError("The targets total must contain a nonnegative integer.")


class OrgUpgradeService:
    """Run one documented SDK operation for each service call.

    Why:
        The service shares no job state and does not change the caller's
        session. Use ``OrgUpgradeSession`` or disable SDK retries before a write.
        The caller can preview a request with ``OrgUpgradeBody.build``.
    """

    @staticmethod
    def check_write_session(session: APISession) -> None:
        """Reject sessions that can retry an SDK write.

        Why:
            A service-level call count alone cannot prove that the SDK sent
            one HTTP request. The SDK retry setting must also be zero.
        """
        retries: object = getattr(session, "_MAX_429_RETRIES", None)
        if type(retries) is not int or retries != 0:
            raise ValueError("Use an OrgUpgradeSession with SDK write retries disabled.")
        for adapter in session._session.adapters.values():
            if not isinstance(adapter, HTTPAdapter) or adapter.max_retries.total not in (0, False):
                raise ValueError("Use an upgrade session with HTTP transport retries disabled.")

    @classmethod
    def submit(cls, session: APISession, org_id: str, request: Mapping[str, object]) -> OrgUpgradeResult:
        """Submit one validated organization AP upgrade request.

        Why:
            Validation runs again at the write boundary. A caller cannot
            bypass it with a changed preview body.

        Args:
            session: The caller's authenticated session with retries disabled.
            org_id: The approved organization UUID.
            request: The supported fields for an explicit site selection.

        Returns:
            The request outcome and the site entries that the cloud returned.
        """
        identifier = OrgUpgradeBody.identifier(org_id, "org_id")
        body = OrgUpgradeBody.build(request)
        cls.check_write_session(session)
        logger.info("Submit the organization AP upgrade for organization %s", identifier)
        response = org_devices.upgradeOrgDevices(session, identifier, body=body)
        result = _OrgUpgradeResponse.normalize(response, identifier)
        logger.debug(
            "The organization upgrade submission returned HTTP %s and error %s", result.raw_status, result.error
        )
        return result

    @staticmethod
    def status(session: APISession, org_id: str, upgrade_id: str) -> OrgUpgradeResult:
        """Read one organization upgrade job without deriving a final state.

        Why:
            The organization job and its site jobs have different identifiers.
            The read must use the organization job identifier in the path.
        """
        identifier = OrgUpgradeBody.identifier(org_id, "org_id")
        job_id = OrgUpgradeBody.identifier(upgrade_id, "upgrade_id")
        logger.info("Read organization upgrade %s for organization %s", job_id, identifier)
        response = org_devices.getOrgDeviceUpgrade(session, identifier, job_id)
        result = _OrgUpgradeResponse.normalize(response, identifier, job_id)
        logger.debug("The organization upgrade read returned HTTP %s and error %s", result.raw_status, result.error)
        return result

    @classmethod
    def cancel(cls, session: APISession, org_id: str, upgrade_id: str) -> OrgUpgradeResult:
        """Request cancellation once without claiming that devices stopped.

        Why:
            The documented cancel response can be empty. HTTP 200 confirms
            the request only, not rollback or a final state for each device.
        """
        identifier = OrgUpgradeBody.identifier(org_id, "org_id")
        job_id = OrgUpgradeBody.identifier(upgrade_id, "upgrade_id")
        cls.check_write_session(session)
        logger.info("Cancel organization upgrade %s for organization %s", job_id, identifier)
        response = org_devices.cancelOrgDeviceUpgrade(session, identifier, job_id)
        result = _OrgUpgradeResponse.normalize(response, identifier, job_id, cancel=True)
        logger.debug("The organization upgrade cancel returned HTTP %s and error %s", result.raw_status, result.error)
        return result
