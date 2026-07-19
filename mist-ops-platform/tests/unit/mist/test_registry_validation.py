"""Tests verifying all 23 registered entity types resolve valid SDK modules (T014).

For each entry in ENTITY_ENDPOINT_MAP, confirm:
1. The api_module resolves via importlib.import_module.
2. The read_method (if set) exists as a callable on the module.
3. The write_method (if set) exists as a callable on the module.
4. The list_method (if set) exists as a callable on the module.
"""

from __future__ import annotations

import importlib

import pytest

from src.shared.mist.types import ENTITY_ENDPOINT_MAP, MistEndpoint


def _resolve_module(endpoint: MistEndpoint) -> object:
    """Import the SDK module for *endpoint*."""
    parts = endpoint.api_module.split(".")
    mod_path = f"mistapi.api.v1.{'.'.join(parts)}"
    return importlib.import_module(mod_path)


ALL_ENTITY_TYPES = sorted(ENTITY_ENDPOINT_MAP.keys())


class TestRegistryModuleResolution:
    """Every api_module in the registry must be importable."""

    @pytest.mark.parametrize("entity_type", ALL_ENTITY_TYPES)
    def test_module_importable(self, entity_type: str) -> None:
        endpoint = ENTITY_ENDPOINT_MAP[entity_type]
        module = _resolve_module(endpoint)
        assert module is not None


class TestRegistryMethodResolution:
    """Every method reference in the registry must be callable."""

    @pytest.mark.parametrize("entity_type", ALL_ENTITY_TYPES)
    def test_read_method_callable(self, entity_type: str) -> None:
        endpoint = ENTITY_ENDPOINT_MAP[entity_type]
        if endpoint.read_method is None:
            pytest.skip("No read_method for this entity type")
        module = _resolve_module(endpoint)
        func = getattr(module, endpoint.read_method, None)
        assert func is not None, f"{entity_type}: {endpoint.read_method} not found"
        assert callable(func)

    @pytest.mark.parametrize("entity_type", ALL_ENTITY_TYPES)
    def test_write_method_callable(self, entity_type: str) -> None:
        endpoint = ENTITY_ENDPOINT_MAP[entity_type]
        if endpoint.write_method is None:
            pytest.skip("No write_method for this entity type")
        module = _resolve_module(endpoint)
        func = getattr(module, endpoint.write_method, None)
        assert func is not None, f"{entity_type}: {endpoint.write_method} not found"
        assert callable(func)

    @pytest.mark.parametrize("entity_type", ALL_ENTITY_TYPES)
    def test_list_method_callable(self, entity_type: str) -> None:
        endpoint = ENTITY_ENDPOINT_MAP[entity_type]
        if endpoint.list_method is None:
            pytest.skip("No list_method for this entity type")
        module = _resolve_module(endpoint)
        func = getattr(module, endpoint.list_method, None)
        assert func is not None, f"{entity_type}: {endpoint.list_method} not found"
        assert callable(func)


class TestRegistryCompleteness:
    """Verify the registry has the expected number of entries."""

    def test_entity_count(self) -> None:
        assert len(ENTITY_ENDPOINT_MAP) == 23

    def test_all_entity_types_have_at_least_one_method(self) -> None:
        for entity_type, endpoint in ENTITY_ENDPOINT_MAP.items():
            has_method = (
                endpoint.read_method is not None
                or endpoint.write_method is not None
                or endpoint.list_method is not None
            )
            assert has_method, f"{entity_type} has no read, write, or list method"
