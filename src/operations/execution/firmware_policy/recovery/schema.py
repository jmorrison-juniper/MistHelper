"""Prove writable settings against local OpenAPI schemas and explicit deletion contracts."""

from __future__ import annotations

import json
import logging
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry

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
    """Validate complete writable projections and exact expected saved state."""

    def __init__(self) -> None:
        """Load checked-in schemas without a network resolver or secret-bearing errors."""
        path = Path(__file__).resolve().parents[5] / "documentation" / "mist-api-openapi31json.json"
        try:
            self.document = json.loads(path.read_text(encoding="utf-8"))
            self._switch_schema()  # Normalize the documented switch composition without accepting unknown fields.
            self._legacy_fields()  # Preserve fields explicitly declared by the pinned legacy settings endpoints.
            self.projection = SchemaProjection(self.document)
        except (OSError, ValueError):
            raise PolicyError("The local settings schemas could not be read.") from None

    def _switch_schema(self) -> None:
        """Combine the explicitly documented network template and switch policy properties."""
        schemas = self.document["components"]["schemas"]  # Use only the pinned public schema definitions.
        declaration = schemas["site_setting_switch"]
        expected = [
            {"$ref": "#/components/schemas/network_template"},
            {"$ref": "#/components/schemas/switch_auto_upgrade_container"},
        ]
        if declaration.get("allOf") != expected:
            raise PolicyError("The local switch settings composition cannot be verified.")
        network = schemas["network_template"]
        upgrade = schemas["switch_auto_upgrade_container"]
        if set(network["properties"]) & set(upgrade["properties"]):
            raise PolicyError("The local switch settings composition has conflicting properties.")
        schemas["site_setting_switch"] = {
            "type": "object",
            "additionalProperties": False,
            "properties": {**network["properties"], **upgrade["properties"]},
            "required": list(dict.fromkeys(network.get("required", []) + upgrade.get("required", []))),
        }  # OpenAPI 3.0 declares this same complete switch object directly rather than with allOf.

    def _legacy_fields(self) -> None:
        """Retain exact legacy writable properties without changing unrelated schema constraints."""
        schemas = self.document["components"]["schemas"]
        schemas["org_setting_marvis"]["properties"]["auto_operations"] = {
            "$ref": "#/components/schemas/marvis_auto_operations",
        }  # Pinned OpenAPI 3.0 org_setting.marvis references marvis, which declares this property.
        schemas["synthetictest_config_wan_speedtest"]["properties"]["enabled"] = {
            "type": "boolean",
        }  # Pinned OpenAPI 3.0 org/site synthetic_test declares this exact boolean beside time_of_day.

    def project(self, scope: str, settings: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        """Exclude only schema-defined top-level read-only fields and validate all others."""
        logger.info("Validate complete writable restoration settings")
        schema = self.document["components"]["schemas"][f"{scope}_setting"]
        body: dict[str, Any] = {}
        excluded: list[str] = []
        for key, value in settings.items():
            child = schema["properties"].get(key)
            if child is None:
                raise PolicyError("The settings contain a field absent from the local writable schema.")
            if self.projection.node(child).get("readOnly"):
                excluded.append(key)
            else:
                self.projection.inspect(value, child)
                body[key] = deepcopy(value)
        root = {**schema, "components": self.document["components"]}
        validator = Draft202012Validator(root, registry=Registry(), format_checker=FormatChecker())
        if not validator.is_valid(body):
            raise PolicyError("The complete writable settings do not match the local schema.")
        logger.debug("Validated %s writable fields and %s exclusions", len(body), len(excluded))
        return body, sorted(excluded)

    def body(self, scope: str, saved: dict[str, Any], current: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        """Build complete replacement values and refuse unsupported absent-field deletion."""
        desired, excluded = self.project(scope, saved)
        existing, _ = self.project(scope, current)
        absent = set(existing) - set(desired)
        if absent - ({"auto_upgrade"} if scope == "site" else set()):
            raise PolicyError("A current field is absent from the backup and has no proven deletion contract.")
        body = deepcopy(desired)
        if "auto_upgrade" in absent:
            body["-auto_upgrade"] = ""
        return body, excluded

    def verify(self, scope: str, saved: dict[str, Any], expected: dict[str, Any]) -> None:
        """Require complete writable equality without accepting an unverified update."""
        actual, _ = self.project(scope, saved)
        desired = {key: value for key, value in expected.items() if not key.startswith("-")}
        if actual != desired:
            raise PolicyError("Saved settings verification failed. Changes can remain in this scope.")
