"""Turns one response schema into a flat list of scalar fields.

Why:
    SNMP has no nested table. A MIB column must therefore name one scalar
    value. This module walks one Mist response schema and it returns one record
    for each scalar leaf, with the dotted path that the metric catalog already
    uses in its `source` field.

    The walk joins `allOf`, `oneOf`, and `anyOf` as a union of property sets.
    The union is the only choice that works for `stats_device`, which is
    `oneOf: [stats_ap, stats_switch, stats_gateway]` and holds no property of
    its own. The agent serves the access point, the switch, and the gateway
    from one table, so the union is exactly the column set that table needs.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.metrics_gateway.catalog import MetricScope
from src.mib_generator.document import LOG_PREFIX, OpenApiDocument

logger = logging.getLogger(__name__)

SCALAR_TYPES = frozenset({"integer", "number", "string", "boolean"})  # The four types a MIB column can carry.
NULL_TYPE = "null"  # OpenAPI 3.1 spells a nullable field as a type list that holds this name.
OBJECT_TYPE = "object"  # A container. The walk enters it, but it never becomes a column.
ARRAY_TYPE = "array"  # A repeated value. SNMP has no nested table, so the walk marks it and enters it.
ARRAY_MARKER = "[]"  # The path part that tells a reader the next name sits inside a repeated record.
NESTING_LIMIT = 4  # The deepest real Mist statistics schema nests 4 levels. Below that, SNMP cannot address it.
MERGE_KEYWORDS = ("allOf", "oneOf", "anyOf")  # The three keywords that the walk joins into one property set.


@dataclass(frozen=True, slots=True)
class FieldRecord:
    """One scalar field of one selected schema.

    Attributes:
        scope: The Mist object the field describes.
        path: The dotted path into the Mist reading, such as
            `user_minutes.total`. This is the join key against the `source`
            field of a metric definition.
        json_type: The non-null JSON type. It is one of `integer`, `number`,
            `string`, or `boolean`.
        description: The OpenAPI description, or an empty string.
        branch: The `oneOf` or `anyOf` branch that gave the field, or an empty
            string when the field came from a plain property set.
        format_hint: The OpenAPI `format`, such as `int64`. It is empty when the
            schema names no format.
    """

    scope: MetricScope
    path: str
    json_type: str
    description: str = ""
    branch: str = ""
    format_hint: str = ""

    def __post_init__(self) -> None:
        """Prove that the record can name a MIB column.

        Raises:
            ValueError: If the path is empty, or the type is not a scalar type.
        """
        if not self.path:  # A column with no path can never join the catalog, so it must not exist.
            raise ValueError("A field record needs a non-empty path.")
        if self.json_type not in SCALAR_TYPES:  # A container can never become one MIB column.
            raise ValueError(f"The field {self.path} carries the type {self.json_type!r}, which is not a scalar.")


@dataclass(frozen=True, slots=True)
class _WalkCursor:
    """The position of the walk inside one schema.

    Attributes:
        prefix: The dotted path of the container the walk is inside.
        branch: The name of the `oneOf` or `anyOf` branch the walk is inside.
        depth: The count of containers the walk already entered.
    """

    prefix: str = ""
    branch: str = ""
    depth: int = 0

    def descend(self, name: str, marker: str = "") -> _WalkCursor:
        """Return the cursor of one child of the current container.

        Args:
            name: The property name of the child.
            marker: The array marker, when the child is a repeated record.

        Returns:
            The cursor that names the child.
        """
        return _WalkCursor(prefix=f"{self.prefix}{name}{marker}.", branch=self.branch, depth=self.depth + 1)


class SchemaFlattener:
    """Turns one schema into the scalar fields that a MIB can name."""

    def __init__(self, document: OpenApiDocument) -> None:
        """Record the document that answers a `$ref`.

        Args:
            document: The loaded OpenAPI document.
        """
        self._document = document  # Every `$ref` in a property set resolves against this document.

    def flatten(self, scope: MetricScope, schema: dict[str, Any]) -> tuple[FieldRecord, ...]:
        """Return one record for each scalar leaf of one schema.

        Args:
            scope: The Mist object the readings of this schema describe.
            schema: The response schema of one selected operation.

        Returns:
            The records, in the order the schema declares its properties.
        """
        logger.debug("%s Flattening the %s schema", LOG_PREFIX, scope)  # Log before the walk.
        found: dict[str, FieldRecord] = {}  # A dict keeps the first definition of a repeated property name.
        self._walk(scope, schema, _WalkCursor(), found)
        logger.debug("%s The %s schema gave %d fields", LOG_PREFIX, scope, len(found))  # Log the result count.
        return tuple(found.values())

    def _walk(
        self,
        scope: MetricScope,
        schema: dict[str, Any],
        cursor: _WalkCursor,
        found: dict[str, FieldRecord],
    ) -> None:
        """Add every scalar leaf of one schema to the result map.

        Args:
            scope: The Mist object the readings describe.
            schema: The schema to walk.
            cursor: The path, the branch, and the depth of this position.
            found: The result map, keyed by the dotted path.
        """
        if cursor.depth > NESTING_LIMIT:  # A deeper leaf cannot reach a poller, so the walk stops here.
            logger.warning("%s Stopped the walk below %s at the nesting limit", LOG_PREFIX, cursor.prefix)
            return
        for branch, properties in self._property_sets(schema, cursor.branch):  # One pass over every joined branch.
            for name, child in properties.items():  # The declaration order fixes the order of the output.
                self._add(scope, name, child, _WalkCursor(cursor.prefix, branch, cursor.depth), found)

    def _property_sets(self, schema: dict[str, Any], branch: str) -> list[tuple[str, dict[str, Any]]]:
        """Return the property set of each branch of one schema.

        Args:
            schema: The schema to read.
            branch: The branch name the caller is already inside.

        Returns:
            One pair of a branch name and a property map for each branch.
        """
        resolved = self._document.resolve(schema)  # A branch is often a bare `$ref`, so resolve it first.
        sets = [(branch, dict(resolved.get("properties") or {}))]  # The own properties come first, so they win.
        for keyword in MERGE_KEYWORDS:  # `allOf`, `oneOf`, and `anyOf` all join into one column set.
            for member in resolved.get(keyword) or []:  # A branch order fixes which definition of a name wins.
                sets.extend(self._property_sets(dict(member), self._branch_name(member) or branch))
        return sets

    @staticmethod
    def _branch_name(member: dict[str, Any]) -> str:
        """Return the schema name of one branch of a merge keyword.

        Args:
            member: The branch schema, which is often a bare `$ref`.

        Returns:
            The component schema name, or an empty string for an inline branch.
        """
        target = member.get("$ref")  # Only a reference carries a name that a reader can act on.
        return str(target).rsplit("/", maxsplit=1)[-1] if isinstance(target, str) else ""

    def _add(
        self,
        scope: MetricScope,
        name: str,
        child: dict[str, Any],
        cursor: _WalkCursor,
        found: dict[str, FieldRecord],
    ) -> None:
        """Add one property as a record, or walk into it as a container.

        Args:
            scope: The Mist object the readings describe.
            name: The property name.
            child: The property schema.
            cursor: The path, the branch, and the depth of the parent.
            found: The result map, keyed by the dotted path.
        """
        resolved = self._document.resolve(child)  # The type of a property often hides behind a `$ref`.
        json_type = self._scalar_type(resolved)
        path = f"{cursor.prefix}{name}"  # The dotted path is the key that the catalog uses for a source field.
        if json_type in SCALAR_TYPES and path in found:  # A `oneOf` repeats a column, and the first branch wins.
            logger.debug("%s Branch %s repeats the field %s", LOG_PREFIX, cursor.branch, path)
            return
        if json_type in SCALAR_TYPES:  # A scalar leaf is the only shape that becomes a MIB column.
            found[path] = self._record(scope, path, json_type, resolved, cursor)
            return
        if json_type == ARRAY_TYPE:  # A repeated record holds its own leaves, and the marker names the repeat.
            item = self._document.resolve(dict(resolved.get("items") or {}))
            self._walk(scope, item, cursor.descend(name, ARRAY_MARKER), found)
            return
        if json_type == OBJECT_TYPE:  # A nested object holds leaves that the catalog names with a dotted path.
            self._walk(scope, resolved, cursor.descend(name), found)

    @staticmethod
    def _record(
        scope: MetricScope,
        path: str,
        json_type: str,
        resolved: dict[str, Any],
        cursor: _WalkCursor,
    ) -> FieldRecord:
        """Return one scalar leaf as a record.

        Args:
            scope: The Mist object the readings describe.
            path: The dotted path of the leaf.
            json_type: The non-null JSON type of the leaf.
            resolved: The resolved property schema.
            cursor: The branch the leaf came from.

        Returns:
            The record.
        """
        return FieldRecord(
            scope=scope,
            path=path,
            json_type=json_type,
            description=str(resolved.get("description") or ""),
            branch=cursor.branch,
            format_hint=str(resolved.get("format") or ""),
        )

    @staticmethod
    def _scalar_type(resolved: dict[str, Any]) -> str:
        """Return the non-null type name of one resolved schema.

        Why:
            OpenAPI 3.1 spells a nullable field as `type: ["string", "null"]`.
            SNMP has no null value, and the agent answers `NONE` for an absent
            reading, so the MIB needs the non-null type only.

        Args:
            resolved: The resolved schema of one property.

        Returns:
            The type name, or an empty string when no type remains.
        """
        declared = resolved.get("type")  # A Mist schema states the type, or it states a merge keyword instead.
        if isinstance(declared, list):  # The 3.1 nullable form. Drop the null name and take the first type left.
            names = [str(item) for item in declared if str(item) != NULL_TYPE]
            return names[0] if names else ""
        if declared:  # A plain string type needs no further work.
            return str(declared)
        has_children = any(resolved.get(key) for key in ("properties", *MERGE_KEYWORDS))  # A container with no type.
        return OBJECT_TYPE if has_children else ""
