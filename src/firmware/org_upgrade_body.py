"""Build a narrow request for an organization AP upgrade.

Why:
    The local OpenAPI operation limits upgrades to access points, although its
    device enumeration also names switches and gateways. This module follows
    the operation description. It never selects every site by implication.

    The contract is ``upgrade_org_devices`` in
    ``documentation/mist-api-openapi31json.json``. The service supports only
    explicit sites, AP version records, the scheduling fields below, and the
    advanced fields of issue #3383. Each advanced field keeps the rule of the
    site body. Other documented fields need a separate safety review.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from uuid import UUID

from src.firmware.upgrade_service import (
    DEVICE_TYPE_AP,
    MESH_UPGRADE_CHOICES,
    NODE_ORDER_CHOICES,
    STRATEGY_CANARY,
    STRATEGY_DEFAULT,
    STRATEGY_RRM,
    STRATEGY_SERIAL,
)

logger = logging.getLogger(__name__)

# The largest failure count of one canary phase. The body uses the same signed
# 32-bit limit for the start time, and the multi-site save refuses a larger
# count before the plan exists (issue #3383).
FAILURE_COUNT_HIGHEST = 2**31 - 1

# The largest peer download size. The site mapper accepts the same limit.
PEER_SIZE_HIGHEST = 1000

# The two sizes of the peer download. Each size acts only with the peer download
# on. The multi-site options page reads the same names (issue #3383).
PEER_SIZE_FIELDS = ("p2p_cluster_size", "p2p_parallelism")

# The five fields of the rrm strategy, in the order of the options page. The
# multi-site options page reads the same names (issue #3383).
RADIO_BATCH_FIELDS = (
    "rrm_first_batch_percentage",
    "rrm_max_batch_percentage",
    "rrm_node_order",
    "rrm_mesh_upgrade",
    "rrm_slow_ramp",
)


class OrgUpgradeBody:
    """Validate the supported organization upgrade fields.

    Why:
        A rejected field must not disappear from a firmware request. Silent
        removal could change the target set or the requested schedule.
    """

    FIELDS = (
        "all_sites",
        "device_type",
        "site_ids",
        "versions",
        "strategy",
        "start_time",
        "canary_phases",
        "max_failure_percentage",
        "max_failures",
        "enable_p2p",
        *PEER_SIZE_FIELDS,
        *RADIO_BATCH_FIELDS,
    )
    _STRATEGIES = (STRATEGY_DEFAULT, STRATEGY_CANARY, STRATEGY_RRM, STRATEGY_SERIAL)
    _PEER_SIZES = PEER_SIZE_FIELDS  # Each size acts only with the peer download on.
    _RADIO_PERCENTAGES = ("rrm_first_batch_percentage", "rrm_max_batch_percentage")  # Two radio batch shares.
    _RADIO_WORDS = {"rrm_node_order": NODE_ORDER_CHOICES, "rrm_mesh_upgrade": MESH_UPGRADE_CHOICES}  # Cloud lists.
    _RADIO_FIELDS = RADIO_BATCH_FIELDS  # Every field of the rrm strategy.

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
        if any(key not in cls.FIELDS for key in request):
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
        strategy = body["strategy"]  # The strategy decides which optional field the body may carry.
        if "start_time" in request:  # An absent start time lets the cloud start the job at once.
            body["start_time"] = cls._integer(request["start_time"], "start_time", (0, 2**31 - 1))  # The epoch.
        if "canary_phases" in request:  # An absent phase list keeps the cloud default phases.
            if strategy != STRATEGY_CANARY:  # Only the canary strategy reads a phase list.
                raise ValueError("The canary_phases field requires the canary strategy.")
            body["canary_phases"] = cls._phases(request["canary_phases"])  # Rising shares that end at 100.
        if "max_failure_percentage" in request:  # An absent limit keeps the cloud default limit.
            if strategy == STRATEGY_DEFAULT:  # One write of every device allows no partial failure.
                raise ValueError("The max_failure_percentage field cannot use the big_bang strategy.")
            body["max_failure_percentage"] = cls._integer(  # A share of the devices from 0 to 100.
                request["max_failure_percentage"], "max_failure_percentage", (0, 100)
            )
        cls._add_advanced_fields(body, request)  # Issue #3383: the counts, the peer download, and the radio fields.

    @classmethod
    def _add_advanced_fields(cls, body: dict[str, object], request: Mapping[str, object]) -> None:
        """Add the canary counts, the peer download fields, and the radio batch fields.

        Why:
            Issue #3383 gives the multi-site plan the advanced controls of the
            single-site plan. Each field keeps the rule of the site body, so a
            value outside that rule stops here and never reaches the cloud.
        """
        logger.info("Validate the advanced fields of the organization AP body")  # Log before the three checks.
        cls._add_failure_counts(body, request)  # One failure count for each canary phase.
        cls._add_peer_fields(body, request)  # The peer download flag and its two sizes.
        cls._add_radio_fields(body, request)  # The five fields of the rrm strategy.
        logger.debug("The organization AP body holds %d fields after the advanced checks", len(body))  # Log after.

    @classmethod
    def _add_failure_counts(cls, body: dict[str, object], request: Mapping[str, object]) -> None:
        """Copy one failure count for each canary phase.

        Why:
            The schema reads ``max_failures`` only for the canary strategy, and
            the list needs one count for each phase. A shorter list would leave
            a later phase with no limit, and the run would continue through a
            failure that the operator meant to stop.

        Raises:
            ValueError: If the strategy, the phase list, or a count does not
                match the rule.
        """
        if "max_failures" not in request:  # An absent list leaves the failure percentage alone in charge.
            return
        phases = body.get("canary_phases")  # The phase list that the body holds already.
        if body["strategy"] != STRATEGY_CANARY or not isinstance(phases, list):  # The counts need the phases.
            raise ValueError("The max_failures field requires the canary strategy and the canary_phases field.")
        entries = cls._array(request["max_failures"], "max_failures")  # An ordered list, never a text.
        counts = [cls._integer(count, "max_failures", (0, FAILURE_COUNT_HIGHEST)) for count in entries]  # Whole.
        if len(counts) != len(phases):  # One count for each phase, as the schema asks.
            raise ValueError("The max_failures field needs one count for each canary phase.")
        body["max_failures"] = counts  # A fresh list, so a later change of the input cannot change the body.

    @classmethod
    def _add_peer_fields(cls, body: dict[str, object], request: Mapping[str, object]) -> None:
        """Copy the peer download flag and its two sizes.

        Why:
            The two sizes act only when the peer download is on. A size without
            the flag sets a limit that the cloud never reads, so the check
            refuses the size instead of a silent drop.

        Raises:
            ValueError: If the flag is not a boolean, or a size has no flag or
                sits outside its range.
        """
        if "enable_p2p" in request:  # An absent flag keeps the cloud default.
            body["enable_p2p"] = cls._boolean(request["enable_p2p"], "enable_p2p")  # A real boolean only.
        for field in cls._PEER_SIZES:  # The two sizes share one rule.
            if field not in request:  # An absent size keeps the cloud default.
                continue
            if body.get("enable_p2p") is not True:  # A size acts only with the peer download on.
                raise ValueError(f"The {field} field requires the enable_p2p field set to true.")
            body[field] = cls._integer(request[field], field, (0, PEER_SIZE_HIGHEST))  # A whole number only.

    @classmethod
    def _add_radio_fields(cls, body: dict[str, object], request: Mapping[str, object]) -> None:
        """Copy the five radio batch fields of the rrm strategy.

        Why:
            The schema reads each field only for the rrm strategy. A field under
            another strategy sets a batch rule that the cloud never reads.

        Raises:
            ValueError: If a field sits outside the rrm strategy or outside
                its own rule.
        """
        present = [field for field in cls._RADIO_FIELDS if field in request]  # The radio fields of this request.
        if present and body["strategy"] != STRATEGY_RRM:  # Only the rrm strategy reads a radio field.
            raise ValueError("The radio batch fields require the rrm strategy.")
        for field in present:  # Each field keeps its own type rule.
            body[field] = cls._radio_value(request[field], field)  # A checked value only.

    @classmethod
    def _radio_value(cls, value: object, field: str) -> object:
        """Return one checked radio batch value.

        Raises:
            ValueError: If the value does not match the rule of its field.
        """
        if field in cls._RADIO_PERCENTAGES:  # A batch share of the access points.
            return cls._integer(value, field, (0, 100))
        if field in cls._RADIO_WORDS:  # A word from the cloud list.
            return cls._word(value, field, cls._RADIO_WORDS[field])
        return cls._boolean(value, field)  # The slow ramp flag.

    @staticmethod
    def _word(value: object, field: str, choices: tuple[str, ...]) -> str:
        """Return one word from a fixed cloud list.

        Raises:
            ValueError: If the value is not a listed word.
        """
        if not isinstance(value, str) or value not in choices:  # Only a listed word reaches the cloud.
            raise ValueError(f"The {field} field must be one of these words: {', '.join(choices)}.")
        return value

    @staticmethod
    def _boolean(value: object, field: str) -> bool:
        """Return one real boolean.

        Why:
            A text such as ``yes`` is true in Python, but the cloud reads only
            a JSON boolean. The check refuses the text instead of a guess.

        Raises:
            ValueError: If the value is not a boolean.
        """
        if not isinstance(value, bool):  # Only a real boolean reaches the cloud.
            raise ValueError(f"The {field} field must be a boolean.")
        return value

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
