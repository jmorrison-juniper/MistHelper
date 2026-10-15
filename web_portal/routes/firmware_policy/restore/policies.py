"""Project only validated firmware fields so inspection cannot disclose private settings."""

from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any

from src.operations.execution.firmware_policy.recovery.schema import RestoreSchema
from src.operations.execution.firmware_policy.sdk import PolicyError

logger = logging.getLogger(__name__)


class PolicyCells:
    """Keep field presence separate from values and effective policy assumptions."""

    paths = ("auto_upgrade", "switch.auto_upgrade", "ssr.auto_upgrade", "juniper_srx.auto_upgrade")

    @staticmethod
    def state(scope: str, value: dict[str, Any] | None) -> str:
        """Distinguish absent policy, empty policy, and explicit enablement."""
        if value is None:
            return "Inherited from organization" if scope == "site" else "Missing organization policy"
        if not value:
            return "Empty policy"
        if "enabled" not in value:
            return "Enablement not specified"
        return "Enabled" if value["enabled"] else "Disabled"

    @classmethod
    def project(cls, scope: str, settings: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Validate policy shapes before retaining raw known fields without normalization."""
        RestoreSchema().project(scope, settings)
        result: dict[str, dict[str, Any]] = {}
        for path in cls.paths:
            parent = settings if path == "auto_upgrade" else settings.get(path.split(".", maxsplit=1)[0], {})
            policy = parent.get("auto_upgrade")
            result[path + ".state"] = {"present": True, "value": cls.state(scope, policy)}
            if policy is not None:
                result.update(cls.fields(path, policy))
        return result

    @staticmethod
    def fields(path: str, policy: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Flatten only schema-approved scalar fields and per-model versions."""
        result = {path: {"present": True, "value": "Present"}}
        for name, value in policy.items():
            if name == "custom_versions":
                if len(value) > 500:
                    raise PolicyError("The firmware policy exceeds the 500-model inspection limit.")
                result[path + ".custom_versions"] = {"present": True, "value": "Empty" if not value else "Present"}
                result.update(
                    {
                        f"{path}.custom_versions.{model}": {"present": True, "value": version}
                        for model, version in value.items()
                    }
                )
            else:
                result[f"{path}.{name}"] = {"present": True, "value": value}
        return result


class PolicyComparison:
    """Build bounded firmware-only differences without modifying any private snapshot."""

    @staticmethod
    def effect(original: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
        """Apply the exact prepared field effects to a copy for inspection only."""
        result = deepcopy(original)
        for key, value in body.items():
            if key.startswith("-"):
                result.pop(key[1:], None)
            else:
                result[key] = deepcopy(value)
        return result

    @staticmethod
    def build(scope: str, sources: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Compare presence and values without persisting full settings or field values."""
        logger.info("Project firmware policy comparison for %s scope", scope)
        projected = {label: PolicyCells.project(scope, settings) for label, settings in sources.items()}
        paths = sorted({path for fields in projected.values() for path in fields})
        fields = [PolicyComparison.row(path, projected) for path in paths]
        logger.debug("Projected %s firmware comparison fields", len(fields))
        return {"columns": list(sources), "fields": fields}

    @staticmethod
    def row(path: str, sources: dict[str, dict[str, Any]]) -> dict[str, Any]:
        """Report current drift and proposed differences using explicit absent cells."""
        cells = {label: fields.get(path, {"present": False}) for label, fields in sources.items()}
        reference = cells.get("current", cells["saved"])
        return {
            "path": path,
            "cells": cells,
            "current_changed": "current" in cells and cells["current"] != cells["saved"],
            "proposed_changed": "proposed" in cells and cells["proposed"] != reference,
        }
