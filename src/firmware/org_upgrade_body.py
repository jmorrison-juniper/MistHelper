"""Build a narrow request for an organization AP upgrade.

Why:
    The local OpenAPI operation limits upgrades to access points, although its
    device enumeration also names switches and gateways. This module follows
    the operation description. It never selects every site by implication.

    The contract is ``upgrade_org_devices`` in
    ``documentation/mist-api-openapi31json.json``. The service supports only
    explicit sites, AP version records, and the scheduling fields below.
    Other documented fields need a separate safety review.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from uuid import UUID

from src.firmware.upgrade_service import (
    DEVICE_TYPE_AP,
    STRATEGY_CANARY,
    STRATEGY_DEFAULT,
    STRATEGY_RRM,
    STRATEGY_SERIAL,
)

logger = logging.getLogger(__name__)


class OrgUpgradeBody:
    """Validate the supported organization upgrade fields.

    Why:
        A rejected field must not disappear from a firmware request. Silent
        removal could change the target set or the requested schedule.
    """

    _FIELDS = (
        "all_sites",
        "device_type",
        "site_ids",
        "versions",
        "strategy",
        "start_time",
        "canary_phases",
        "max_failure_percentage",
    )
    _STRATEGIES = (STRATEGY_DEFAULT, STRATEGY_CANARY, STRATEGY_RRM, STRATEGY_SERIAL)

    @classmethod
    def build(cls, request: Mapping[str, object]) -> dict[str, object]:
        """Return a new body that selects APs at explicit sites.

        Why:
            The organization schema uses ``versions``, not the site schema's
            ``version`` and ``device_ids`` fields. A fresh body also prevents
            later changes to the input from changing the request.

        Args:
            request: The supported request fields. Omit unused optional fields.

        Returns:
            The validated JSON body. The body always sets ``all_sites`` false.

        Raises:
            ValueError: If a field is unsupported, ambiguous, or malformed.
        """
        logger.info("Validate the organization AP upgrade body")
        cls._check_fields(request)
        body: dict[str, object] = {
            "all_sites": False,
            "device_type": DEVICE_TYPE_AP,
            "site_ids": cls._sites(request.get("site_ids")),
            "versions": cls._versions(request.get("versions")),
            "strategy": request.get("strategy", STRATEGY_DEFAULT),
        }
        cls._add_options(body, request)
        logger.debug("The organization AP upgrade body contains %d fields", len(body))
        return body

    @staticmethod
    def identifier(value: object, field: str) -> str:
        """Return a canonical UUID for a path or a site selection.

        Why:
            The contract requires UUIDs. String conversion must not turn an
            unrelated value into a path segment.

        Raises:
            ValueError: If the value is not a UUID string.
        """
        if not isinstance(value, str):
            raise ValueError(f"The {field} field must contain a UUID string.")
        try:
            return str(UUID(value))
        except ValueError as error:
            raise ValueError(f"The {field} field must contain a UUID string.") from error

    @classmethod
    def _check_fields(cls, request: Mapping[str, object]) -> None:
        """Reject fields that could change the approved request.

        Why:
            An AP-only request cannot use organization-wide selection or
            silently ignore options from another upgrade schema.
        """
        if not isinstance(request, Mapping):
            raise ValueError("The upgrade request must contain an object.")
        if any(key not in cls._FIELDS for key in request):
            raise ValueError("The upgrade request contains an unsupported field.")
        if request.get("all_sites", False) is not False:
            raise ValueError("The all_sites field must be false.")
        if request.get("device_type", DEVICE_TYPE_AP) != DEVICE_TYPE_AP:
            raise ValueError("The organization upgrade supports AP devices only.")
        if request.get("strategy", STRATEGY_DEFAULT) not in cls._STRATEGIES:
            raise ValueError("The strategy field must be big_bang, canary, rrm, or serial.")

    @staticmethod
    def _array(value: object, field: str) -> list[object]:
        """Copy a nonempty ordered array.

        Why:
            Strings, sets, and mappings cannot supply an explicit ordered
            selection. Python tuples can supply the same values as JSON arrays.
        """
        if not isinstance(value, (list, tuple)) or not value:
            raise ValueError(f"The {field} field must contain a nonempty array.")
        return list(value)

    @classmethod
    def _sites(cls, value: object) -> list[str]:
        """Validate each site without changing the selection order.

        Why:
            Duplicate sites could create duplicate work. The service rejects
            them instead of silently changing the operator's selection.
        """
        sites = [cls.identifier(site, "site_ids") for site in cls._array(value, "site_ids")]
        if len(set(sites)) != len(sites):
            raise ValueError("The site_ids field must not contain duplicate sites.")
        return sites

    @classmethod
    def _versions(cls, value: object) -> list[dict[str, object]]:
        """Validate the one AP firmware record."""
        records = cls._array(value, "versions")
        if len(records) != 1:
            raise ValueError("The AP upgrade needs exactly one versions record.")
        return [cls._version_record(records[0])]

    @classmethod
    def _version_record(cls, value: object) -> dict[str, object]:
        """Return one supported AP firmware record."""
        if not isinstance(value, Mapping):
            raise ValueError("Each versions record must contain supported AP firmware fields.")
        if any(key not in ("firmware_type", "version", "force") for key in value):
            raise ValueError("Each versions record must contain supported AP firmware fields.")
        if value.get("firmware_type") != DEVICE_TYPE_AP:
            raise ValueError("Each versions record must use the ap firmware_type.")
        result: dict[str, object] = {
            "firmware_type": DEVICE_TYPE_AP,
            "version": cls._version_text(value.get("version")),
        }
        cls._add_force(result, value)
        return result

    @staticmethod
    def _version_text(value: object) -> str:
        """Return a printable firmware version with no whitespace."""
        if not isinstance(value, str) or not value or not value.isprintable():
            raise ValueError("Each versions record needs a nonempty version string without whitespace.")
        if any(character.isspace() for character in value):
            raise ValueError("Each versions record needs a nonempty version string without whitespace.")
        return value

    @staticmethod
    def _add_force(result: dict[str, object], record: Mapping[str, object]) -> None:
        """Copy the optional force flag after its type check."""
        if "force" not in record:
            return
        if not isinstance(record["force"], bool):
            raise ValueError("The force field in a versions record must be a boolean.")
        result["force"] = record["force"]

    @staticmethod
    def _integer(value: object, field: str, bounds: tuple[int, int]) -> int:
        """Validate a whole number without accepting a boolean.

        Why:
            Python treats booleans as integers. The API gives these fields
            different types, so the request must keep them distinct.
        """
        if type(value) is not int or not bounds[0] <= value <= bounds[1]:
            raise ValueError(f"The {field} field must be an integer from {bounds[0]} to {bounds[1]}.")
        return value

    @classmethod
    def _add_options(cls, body: dict[str, object], request: Mapping[str, object]) -> None:
        """Add optional fields only when their strategy permits them.

        Why:
            An absent field uses the cloud default. A supplied null or invalid
            value must not silently select that default.
        """
        strategy = body["strategy"]
        if "start_time" in request:
            body["start_time"] = cls._integer(request["start_time"], "start_time", (0, 2**31 - 1))
        if "canary_phases" in request:
            if strategy != STRATEGY_CANARY:
                raise ValueError("The canary_phases field requires the canary strategy.")
            body["canary_phases"] = cls._phases(request["canary_phases"])
        if "max_failure_percentage" in request:
            if strategy == STRATEGY_DEFAULT:
                raise ValueError("The max_failure_percentage field cannot use the big_bang strategy.")
            body["max_failure_percentage"] = cls._integer(
                request["max_failure_percentage"], "max_failure_percentage", (0, 100)
            )

    @classmethod
    def _phases(cls, value: object) -> list[int]:
        """Validate increasing percentages that end at 100.

        Why:
            The documented phases are cumulative percentages. This service
            rejects an ambiguous order or a plan that omits the final devices.
        """
        phases = [cls._integer(phase, "canary_phases", (1, 100)) for phase in cls._array(value, "canary_phases")]
        if phases[-1] != 100 or any(left >= right for left, right in zip(phases, phases[1:], strict=False)):
            raise ValueError("The canary_phases percentages must increase and end at 100.")
        return phases
