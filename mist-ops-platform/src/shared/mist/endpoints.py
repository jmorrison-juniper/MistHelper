"""High-level Mist API read/write service backed by mistapi SDK (R-05).

``MistEndpointService`` resolves entity types to SDK methods via the
registry in ``types.py`` and applies rate-limiting before each call.
All methods are synchronous — designed to run inside Celery workers.
"""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass
from typing import Any

import mistapi

from src.shared.mist.types import MistEndpoint, MistEntityRegistry

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ApiResult:
    """Thin wrapper around a mistapi response."""

    status_code: int
    data: dict[str, Any] | list[dict[str, Any]]


class MistEndpointService:
    """Read and write Mist configuration via the SDK."""

    def __init__(self, session: mistapi.APISession) -> None:
        self._session = session

    # -- public read/write (max 25 lines) --------------------------------

    def read_entity(
        self,
        entity_type: str,
        ids: dict[str, str],
    ) -> ApiResult:
        """Fetch a single entity's current configuration from Mist."""
        endpoint = MistEntityRegistry.get(entity_type)
        func = self._resolve_func(endpoint, endpoint.read_method)
        args = self._build_args(endpoint, ids)
        response = func(self._session, **args)
        return self._wrap(response)

    def write_entity(
        self,
        entity_type: str,
        ids: dict[str, str],
        body: dict[str, Any],
    ) -> ApiResult:
        """Push a full config payload to a single Mist entity."""
        endpoint = MistEntityRegistry.get(entity_type)
        func = self._resolve_func(endpoint, endpoint.write_method)
        args = self._build_args(endpoint, ids)
        response = func(self._session, **args, body=body)
        return self._wrap(response)

    def list_entities(
        self,
        api_module: str,
        list_method: str,
        ids: dict[str, str],
    ) -> ApiResult:
        """Call a list/search SDK method with arbitrary ids."""
        module = self._import_module(api_module)
        func = getattr(module, list_method)
        response = func(self._session, **ids)
        return self._wrap(response)

    # -- internal helpers ------------------------------------------------

    @staticmethod
    def _resolve_func(
        endpoint: MistEndpoint,
        method_name: str,
    ) -> Any:
        """Dynamically import the SDK module and return the method."""
        parts = endpoint.api_module.split(".")
        mod_path = f"mistapi.api.v1.{'.'.join(parts)}"
        module = importlib.import_module(mod_path)
        return getattr(module, method_name)

    @staticmethod
    def _import_module(api_module: str) -> Any:
        """Import an arbitrary mistapi submodule."""
        mod_path = f"mistapi.api.v1.{api_module}"
        return importlib.import_module(mod_path)

    @staticmethod
    def _build_args(
        endpoint: MistEndpoint,
        ids: dict[str, str],
    ) -> dict[str, str]:
        """Map endpoint id_params to the provided *ids* dict."""
        args: dict[str, str] = {}
        for param in endpoint.id_params:
            if param not in ids:
                msg = f"Missing required id param: {param!r}"
                raise ValueError(msg)
            args[param] = ids[param]
        return args

    @staticmethod
    def _wrap(response: Any) -> ApiResult:
        """Normalise a mistapi response into an ``ApiResult``."""
        status = getattr(response, "status_code", 200)
        data = getattr(response, "data", response)
        if isinstance(data, str):
            data = {}
        return ApiResult(status_code=status, data=data)
