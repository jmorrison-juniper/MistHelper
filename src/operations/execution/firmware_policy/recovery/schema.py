"""Validate firmware policy restoration while preserving current unrelated settings."""

from __future__ import annotations

import json
import logging
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry

from ..changes import PolicyValidation
from ..sdk import PolicyError

logger = logging.getLogger(__name__)


class SchemaProjection:
    """Inspect local schema structure without silently accepting unknown settings."""

    def __init__(self, document: dict[str, Any]) -> None:
        """Keep the checked-in schema document as the only reference source."""
        self.document = document

    def node(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Resolve local references and refuse external schema retrieval."""
        reference = schema.get("$ref")
        if not reference:
            return schema
        if not reference.startswith("#/components/schemas/"):
            raise PolicyError("The settings schema has an unsupported reference.")
        return {
            **self.document["components"]["schemas"][reference.rsplit("/", 1)[1]],
            **{key: value for key, value in schema.items() if key != "$ref"},
        }

    def inspect(self, value: Any, schema: dict[str, Any], depth: int = 0) -> None:
        """Reject unknown structure, nested read-only fields, and masked secrets."""
        if depth > 40:
            raise PolicyError("The settings exceed the supported nesting limit.")
        schema = self.node(schema)
        if schema.get("readOnly"):
            raise PolicyError("Nested server-managed settings cannot be restored safely.")
        if isinstance(value, str) and (
            re.fullmatch(r"\*{3,}", value.strip())
            or value.strip().lower() in {"<redacted>", "redacted", "<hidden>", "[redacted]", "******** (hidden)"}
        ):
            raise PolicyError("The backup contains a secret placeholder. A complete original value is required.")
        self.children(value, schema, depth)

    def children(self, value: Any, schema: dict[str, Any], depth: int) -> None:
        """Apply declared object and array shapes, rejecting ambiguous schema branches."""
        if "oneOf" in schema or "anyOf" in schema:
            self.branches(value, schema, depth)  # Enforce documented unions without accepting unknown object fields.
            return
        if any(key in schema for key in ("allOf", "patternProperties")):
            raise PolicyError("These settings use a schema shape that cannot be restored safely.")
        if isinstance(value, dict):
            for key, item in value.items():
                child = schema.get("properties", {}).get(key, schema.get("additionalProperties"))
                if not isinstance(child, dict):
                    raise PolicyError("The backup contains an unknown or unproven settings field.")
                self.inspect(item, child, depth + 1)
        if isinstance(value, list):
            for item in value:
                self.inspect(item, schema.get("items", {}), depth + 1)

    def branches(self, value: Any, schema: dict[str, Any], depth: int) -> None:
        """Select validated public schema alternatives without changing their constraints."""
        key = "oneOf" if "oneOf" in schema else "anyOf"
        matches = []
        for branch in schema[key]:
            root = {**branch, "components": self.document["components"]}
            validator = Draft202012Validator(root, registry=Registry(), format_checker=FormatChecker())
            if validator.is_valid(value):
                matches.append(branch)
        if not matches or (key == "oneOf" and len(matches) != 1):
            raise PolicyError("The settings do not match a supported schema alternative.")
        for branch in matches:  # Every matched shape still rejects unproven fields and secret placeholders.
            self.inspect(value, branch, depth + 1)


class RestoreSchema:
    """Validate only firmware policies and preserve complete current snapshots."""

    def __init__(self) -> None:
        """Load checked-in schemas without a network resolver or secret-bearing errors."""
        path = Path(__file__).resolve().parents[5] / "documentation" / "mist-api-openapi31json.json"
        try:
            self.document = json.loads(path.read_text(encoding="utf-8"))
            self.projection = SchemaProjection(self.document)
        except (OSError, ValueError):
            raise PolicyError("The local settings schemas could not be read.") from None

    def project(self, scope: str, settings: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        """Select four policy paths without inspecting or disclosing unrelated settings."""
        logger.info("Validate firmware policy restoration settings")
        if scope not in ("org", "site") or not isinstance(settings, dict):
            raise PolicyError("The firmware policy scope or settings object is invalid.")
        body: dict[str, Any] = {}
        notices = ["outside_firmware_policy_scope"]  # Report the deliberate scope without private key names.
        for kind in ("ap", "switch", "ssr", "juniper_srx"):
            parent = settings if kind == "ap" else settings.get(kind, {})
            if not isinstance(parent, dict):
                raise PolicyError("A firmware policy parent is not an object.")
            if "auto_upgrade" in parent:
                value = self._policy(scope, kind, parent["auto_upgrade"], notices)
                body.update({"auto_upgrade": value} if kind == "ap" else {kind: {"auto_upgrade": value}})
        logger.debug("Validated %s firmware policy fields", len(body))
        return body, notices

    def _policy(self, scope: str, kind: str, value: Any, notices: list[str]) -> dict[str, Any]:
        """Validate supported historical policy values without requiring a current catalog."""
        if not isinstance(value, dict):
            raise PolicyError("A firmware auto-upgrade policy is not an object.")
        result: dict[str, Any] = deepcopy(value)  # Preserve the source while normalizing documented AP defaults.
        if kind == "ap":
            self._schedule(result, notices)
        properties = self.document["components"]["schemas"][f"{scope}_setting"]["properties"]
        child = properties["auto_upgrade"] if kind == "ap" else self._nested_policy(kind)
        self.projection.inspect(result, child)  # Unknown policy fields and masked policy values still fail.
        validator = Draft202012Validator(
            {**child, "components": self.document["components"]}, registry=Registry(), format_checker=FormatChecker()
        )
        if not validator.is_valid(result):
            raise PolicyError("The firmware policy does not match the supported schema.")
        return result

    @staticmethod
    def _schedule(value: dict[str, Any], notices: list[str]) -> None:
        """Report menu 168 AP schedule defaults and reject other invalid schedules."""
        for key, default in (("day_of_week", "any"), ("time_of_day", "02:00")):
            if key not in value or value[key] == "":
                value[key] = default
                notices.append(f"normalized:auto_upgrade.{key}={default}")
        PolicyValidation.schedule("ap", value["day_of_week"], value["time_of_day"])

    def _nested_policy(self, kind: str) -> dict[str, Any]:
        """Use the shared documented hardware policy schema, not its unrelated parent schema."""
        parent = self.document["components"]["schemas"]["org_setting"]["properties"][kind]
        child: dict[str, Any] = self.projection.node(parent)["properties"]["auto_upgrade"]
        return child

    def body(self, scope: str, saved: dict[str, Any], current: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        """Replace policies while retaining only current unrelated parent values."""
        desired, excluded = self.project(scope, saved)
        existing, _ = self.project(scope, current)
        if scope == "org" and "auto_upgrade" in existing and "auto_upgrade" not in desired:
            raise PolicyError("The absent organization AP policy has no proven deletion contract.")
        body = {key: value for key, value in desired.items() if key == "auto_upgrade"}
        if scope == "site" and "auto_upgrade" in existing and "auto_upgrade" not in desired:
            body["-auto_upgrade"] = ""
        self._parents(body, current, desired, existing)
        return body, excluded

    @staticmethod
    def _parents(
        body: dict[str, Any], current: dict[str, Any], desired: dict[str, Any], existing: dict[str, Any]
    ) -> None:
        """Use complete current parents to preserve unrelated siblings during nested policy replacement."""
        for kind in ("switch", "ssr", "juniper_srx"):
            if kind in desired or kind in existing:
                parent = deepcopy(current.get(kind, {}))
                parent.pop("auto_upgrade", None)
                parent.update(desired.get(kind, {}))
                body[kind] = parent

    def verify(self, scope: str, saved: dict[str, Any], expected: dict[str, Any], original: dict[str, Any]) -> None:
        """Prove policy values and every unrelated current value except the modification timestamp."""
        self.project(scope, saved)  # Retain strict validation of the policy values returned by the server.
        desired = deepcopy(original)
        for key, value in expected.items():
            if key == "-auto_upgrade":
                desired.pop("auto_upgrade", None)
            else:
                desired[key] = value
        desired.pop("modified_time", None)
        actual = {key: value for key, value in saved.items() if key != "modified_time"}
        if actual != desired:
            raise PolicyError("Saved settings verification failed. Changes can remain in this scope.")
