"""Plan policy changes and verify inheritance without changing unrelated settings."""

from __future__ import annotations

import logging
import re
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from .sdk import PolicyError

logger = logging.getLogger(__name__)
POLICY_TYPES = ("ap", "switch", "ssr", "juniper_srx")


@dataclass(frozen=True)
class FirmwarePolicy:
    """Hold one explicit policy, including a schedule only for access points."""

    kind: str
    enabled: bool
    models: dict[str, str]
    day: str = "any"
    time: str = "any"

    def __post_init__(self) -> None:
        """Reject incomplete policies before an update body can be built."""
        if self.kind not in POLICY_TYPES or not isinstance(self.enabled, bool):
            raise PolicyError("The policy type or enabled state is invalid.")
        PolicyValidation.models(self.models)  # Validate the complete map before body construction.
        PolicyValidation.schedule(self.kind, self.day, self.time)  # Validate the hardware schedule contract.

    def body(self, previous: dict[str, Any]) -> dict[str, Any]:
        """Replace firmware choices while retaining supported non-version controls."""
        result: dict[str, Any] = {"enabled": self.enabled, "custom_versions": dict(self.models)}
        if self.kind == "ap":
            result.update(version="custom", day_of_week=self.day, time_of_day=self.time)
        elif self.kind in ("switch", "juniper_srx") and "snapshot" in previous:
            result["snapshot"] = previous["snapshot"]  # Keep the existing snapshot choice.
        return result  # Do not retain a conflicting default version or channel.


class PolicyValidation:
    """Check external model maps and supported schedules with bounded validation steps."""

    @staticmethod
    def models(values: dict[str, str]) -> None:
        """Reject incomplete model choices without accessing malformed values."""
        if not isinstance(values, dict) or not values:
            raise PolicyError("Each policy needs a model and a firmware version.")
        for model, version in values.items():
            if not isinstance(model, str) or not isinstance(version, str):
                raise PolicyError("Model and firmware version values must be text.")
            if not model.strip() or not version.strip():
                raise PolicyError("Each policy needs a model and a firmware version.")

    @staticmethod
    def schedule(kind: str, day: str, time: str) -> None:
        """Allow schema days and 24-hour times, and schedule AP policies only."""
        if day not in ("any", "mon", "tue", "wed", "thu", "fri", "sat", "sun"):
            raise PolicyError("The AP upgrade day is invalid.")
        if not isinstance(time, str):
            raise PolicyError("The AP upgrade time must use HH:MM or any.")
        if time != "any" and not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", time):
            raise PolicyError("The AP upgrade time must use HH:MM or any.")
        if kind != "ap" and (day, time) != ("any", "any"):
            raise PolicyError("Only AP auto-upgrade settings support a schedule.")


class PolicyChanges:
    """Create minimal settings bodies and compare saved policies with the plan."""

    @staticmethod
    def container(settings: dict[str, Any], key: str) -> dict[str, Any]:
        """Reject malformed parent objects instead of losing their unrelated fields."""
        result = settings.get(key, {})  # An absent container is a valid unconfigured state.
        if not isinstance(result, dict):
            raise PolicyError(f"The {key} settings field is not an object.")
        return deepcopy(result)  # A plan must not change the original snapshot.

    @classmethod
    def organization(cls, settings: dict[str, Any], policies: list[FirmwarePolicy]) -> dict[str, Any]:
        """Change selected firmware policies while preserving parent-object siblings."""
        logger.info("Plan organization firmware policy fields")  # Describe the transform without the settings.
        body: dict[str, Any] = {}  # Omit all unrelated top-level settings.
        for policy in policies:
            parent = settings if policy.kind == "ap" else cls.container(settings, policy.kind)
            previous = cls.container(parent, "auto_upgrade")  # Validate any existing local policy.
            value = policy.body(previous)  # Replace version choices for the selected type.
            if policy.kind == "ap":
                body["auto_upgrade"] = value  # AP settings are top-level.
            else:
                parent["auto_upgrade"] = value  # Retain every other nested member.
                body[policy.kind] = parent  # Mist replaces the complete named parent object.
        logger.debug("Planned %s organization firmware policies", len(policies))  # Record a safe count.
        return body  # No upgrade request body is generated.

    @classmethod
    def site(cls, settings: dict[str, Any]) -> dict[str, Any]:
        """Remove all supported overrides, without creating a local disabled policy."""
        logger.info("Plan site firmware override removal")  # Record the transform without sensitive fields.
        body: dict[str, Any] = {"-auto_upgrade": ""} if "auto_upgrade" in settings else {}
        for kind in POLICY_TYPES[1:]:
            parent = cls.container(settings, kind)  # Preserve the complete nested object.
            if "auto_upgrade" in parent:
                del parent["auto_upgrade"]  # Absence restores organization inheritance.
                body[kind] = parent  # Retain conductor, proxy, gateway, and network settings.
        logger.debug("Planned %s site firmware fields", len(body))  # Report only the changed-field count.
        return body  # Empty means the site already inherits every supported policy.

    @staticmethod
    def verify_org(saved: dict[str, Any], body: dict[str, Any]) -> None:
        """Reject an organization write whose selected values or siblings did not persist."""
        for key, expected in body.items():
            actual = saved.get(key)  # Compare only the requested top-level objects.
            if not isinstance(actual, dict) or any(actual.get(name) != value for name, value in expected.items()):
                raise PolicyError(f"Organization verification failed for {key}.")

    @classmethod
    def verify_site(cls, saved: dict[str, Any], original: dict[str, Any]) -> None:
        """Prove override absence and preservation of unrelated site settings."""
        if cls.site(saved):
            raise PolicyError("Site verification failed: a local auto-upgrade override remains.")
        expected = deepcopy(original)  # Compare unrelated fields with their pre-write values.
        expected.pop("auto_upgrade", None)  # The AP field is deliberately removed.
        for kind in POLICY_TYPES[1:]:
            if kind in expected:
                expected[kind].pop("auto_upgrade", None)  # Ignore only the targeted nested override.
        for key, value in expected.items():
            if key == "modified_time":
                continue  # Mist changes this server-generated timestamp after an update.
            if saved.get(key, {} if value == {} else None) != value:
                raise PolicyError(f"Site verification failed: the {key} field changed.")
