"""Reads the Mist OpenAPI file and answers a question about one operation.

Why:
    The generator needs three facts from the OpenAPI file: the version, the GET
    operation behind an `operationId`, and the response schema of that
    operation. This module owns those three answers, so no other module needs
    to know the shape of an OpenAPI document.

    The whole file loads in one `json.load` call. The measured cost on the real
    16.6 MB file is 0.26 s to 0.49 s and 69.7 MB of traced Python memory. The
    budget is 30 s and 1 GB, so a streaming parser would buy nothing and would
    cost a dependency.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

LOG_PREFIX = "MIB_GENERATOR:"  # Every log line of this package carries this prefix.
SUPPORTED_VERSION_PREFIX = "3.1"  # The generator reads OpenAPI 3.1 only, because 3.0 spells null differently.
REF_DEPTH_LIMIT = 12  # A `$ref` chain deeper than this is a cycle, not a real Mist schema.
JSON_MEDIA_TYPE = "application/json"  # Mist answers every statistics call with this media type.
OK_STATUS = "200"  # The generator reads the success response only.
REF_KEY = "$ref"  # The OpenAPI keyword that points at a component schema.
REF_PREFIX = "#/components/schemas/"  # Every reference in the Mist file is local and points here.


class OpenApiVersionError(ValueError):
    """The file parses, but it is not an OpenAPI 3.1 document."""


class OperationNotFoundError(LookupError):
    """The document holds no GET operation with the wanted `operationId`."""


class OpenApiDocument:
    """The parsed Mist OpenAPI file, indexed by `operationId`."""

    def __init__(self, path: Path) -> None:
        """Record the path of the file. This call reads nothing.

        Args:
            path: The local path of the OpenAPI JSON file.
        """
        self._path = path  # `load` reads this path, so a caller can build the object and choose later.
        self._document: dict[str, Any] = {}  # The parsed file. It stays empty until `load` runs.
        self._operations: dict[str, tuple[str, str, dict[str, Any]]] = {}  # The method, the path, and the operation.

    def load(self) -> OpenApiDocument:
        """Read the file, prove the version, and index every operation.

        Returns:
            This document, so a caller can chain the call.

        Raises:
            ValueError: If the file holds no valid JSON. The message names the
                path and the position of the JSON error.
            OpenApiVersionError: If the `openapi` field is not a 3.1 version.
        """
        logger.info("%s Reading the OpenAPI file at %s", LOG_PREFIX, self._path)  # Log before the read.
        raw = self._path.read_text(encoding="utf-8")  # An explicit encoding keeps Windows and Linux in agreement.
        try:  # A broken file must name its own defect, because an operator cannot guess a byte offset.
            self._document = json.loads(raw)
        except json.JSONDecodeError as error:  # Re-raise with the path, which the JSON error never carries.
            raise ValueError(
                f"The file {self._path} holds no valid JSON at line {error.lineno}, column {error.colno}: {error.msg}"
            ) from error
        self._check_version()  # A 3.0 file spells a nullable type differently, so it must stop here.
        self._index_operations()  # One pass builds the `operationId` index that every later lookup reads.
        logger.info(
            "%s Read %d paths and %d schemas",  # Log the result count after the read.
            LOG_PREFIX,
            len(self._document.get("paths") or {}),
            len(self._schemas()),
        )
        return self

    def _check_version(self) -> None:
        """Stop the run when the file is not an OpenAPI 3.1 document.

        Raises:
            OpenApiVersionError: If the `openapi` field is missing or not 3.1.
        """
        version = str(self._document.get("openapi", ""))  # A missing field gives an empty string, which fails below.
        if not version.startswith(SUPPORTED_VERSION_PREFIX):  # Only 3.1 spells a nullable type as a type list.
            raise OpenApiVersionError(
                f"The file {self._path} reports OpenAPI version {version!r}, and 3.1 is required."
            )

    def _index_operations(self) -> None:
        """Record the method, the path, and the body of every operation."""
        for path, item in (self._document.get("paths") or {}).items():  # One entry for each URL of the API.
            for method, operation in (item or {}).items():  # An entry holds one child for each HTTP method.
                if isinstance(operation, dict) and operation.get("operationId"):  # A parameter list carries no id.
                    self._operations[str(operation["operationId"])] = (str(method).lower(), str(path), operation)

    def _schemas(self) -> dict[str, Any]:
        """Return the component schema map of the document.

        Returns:
            The schemas, keyed by name. The map is empty when the file holds none.
        """
        return dict((self._document.get("components") or {}).get("schemas") or {})

    def get_operation(self, operation_id: str) -> tuple[str, str, dict[str, Any]]:
        """Return the method, the path, and the body of one operation.

        Args:
            operation_id: The `operationId` the allow list names.

        Returns:
            The lowercase HTTP method, the URL path, and the operation body.

        Raises:
            OperationNotFoundError: If the document holds no such `operationId`.
        """
        if operation_id not in self._operations:  # The allow list names an endpoint the file lost or never held.
            raise OperationNotFoundError(f"The OpenAPI file holds no operationId {operation_id!r}.")
        return self._operations[operation_id]

    def operations(self) -> dict[str, tuple[str, str, dict[str, Any]]]:
        """Return every indexed operation.

        Returns:
            The method, the path, and the body of each operation, by `operationId`.
        """
        return dict(self._operations)  # A copy stops a caller from changing the index of this document.

    def response_schema(self, operation_id: str) -> dict[str, Any]:
        """Return the success response schema of one operation.

        Why:
            Two Mist shapes reach this call. A scalar endpoint returns one
            object, and a table endpoint returns an array of objects. The MIB
            needs the column set in both cases, so an array unwraps to its item
            schema here.

        Args:
            operation_id: The `operationId` the allow list names.

        Returns:
            The schema of one record. The map is empty when the operation
            declares no JSON success body.
        """
        _method, _path, operation = self.get_operation(operation_id)  # The method check belongs to the allow list.
        responses = (operation.get("responses") or {}).get(OK_STATUS) or {}  # Only the success body makes readings.
        schema = ((responses.get("content") or {}).get(JSON_MEDIA_TYPE) or {}).get("schema") or {}
        resolved = self.resolve(schema)  # A response schema is often a bare `$ref`, so resolve it first.
        if resolved.get("type") == "array":  # A table endpoint wraps its record in an array.
            return self.resolve(dict(resolved.get("items") or {}))
        return resolved

    def resolve(self, schema: dict[str, Any], depth: int = 0, chain: tuple[str, ...] = ()) -> dict[str, Any]:
        """Follow a `$ref` chain until it reaches a real schema.

        Why:
            A `$ref` can point at itself, directly or through a chain. An
            unbounded walk ends in a `RecursionError` that tells an operator
            nothing. This walk stops at a fixed limit and it logs the chain it
            cut, so an engineer can act.

        Args:
            schema: The schema to resolve.
            depth: The count of references already followed on this chain.
            chain: The reference names already followed, for the log line.

        Returns:
            The resolved schema, or the partial schema at the depth limit.
        """
        target = schema.get(REF_KEY)  # A schema without this key is already a real schema.
        if not isinstance(target, str):  # Nothing to follow, so return the schema as it stands.
            return schema
        name = target.removeprefix(REF_PREFIX)  # The Mist file holds local references only.
        if depth >= REF_DEPTH_LIMIT:  # The chain is a cycle, or it is deeper than SNMP can ever represent.
            logger.warning("%s Cut the $ref chain at %s after %s", LOG_PREFIX, name, " -> ".join(chain))
            return {}
        return self.resolve(dict(self._schemas().get(name) or {}), depth + 1, (*chain, name))
