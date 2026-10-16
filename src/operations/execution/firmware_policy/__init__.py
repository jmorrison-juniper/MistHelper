"""Configure organization firmware policies without requesting firmware execution."""

from __future__ import annotations

import logging
from typing import Any

from .sdk import PolicyApi, PolicyError

logger = logging.getLogger(__name__)


class PolicyInventory:
    """Restrict displayed model choices without changing catalog validation."""

    @classmethod
    def display(
        cls,
        api: PolicyApi,
        organizations: list[dict[str, Any]],
        catalogs: dict[str, dict[str, list[str]]],
        show_all: bool = False,
    ) -> dict[str, dict[str, list[str]]]:
        """Filter shared choices by inventory while preserving explicit all-model selection."""
        if show_all:
            return catalogs
        logger.info("Filter firmware models for %s organization inventories", len(organizations))
        owned = cls.owned(api, organizations)
        hardware = {"ap": "ap", "switch": "switch", "ssr": "gateway", "juniper_srx": "gateway"}
        result = {
            kind: {model: versions for model, versions in models.items() if (hardware[kind], model.casefold()) in owned}
            for kind, models in catalogs.items()
        }
        logger.debug("Filtered firmware catalogs contain %s models", sum(len(models) for models in result.values()))
        return result

    @staticmethod
    def owned(api: PolicyApi, organizations: list[dict[str, Any]]) -> set[tuple[str, str]]:
        """Require valid inventory identities before combining selected organization models."""
        owned: set[tuple[str, str]] = set()
        for organization in organizations:
            for row in api.inventory(organization["id"]):
                model, hardware = row.get("model"), row.get("type")
                if (
                    not isinstance(model, str)
                    or not model.strip()
                    or not isinstance(hardware, str)
                    or not hardware.strip()
                ):
                    raise PolicyError("The organization inventory contains an invalid model or device type.")
                owned.add((hardware.strip().casefold(), model.strip().casefold()))
        return owned
