"""Test constructor contracts and complete E2E isolation."""

from __future__ import annotations

import inspect  # Reads the real constructor signatures without invoking them.
from types import SimpleNamespace  # Builds one complete install-seam override shape.
from typing import Any  # The override map accepts every seam value.

import pytest  # The tests replace production constructors with refusal traps.
from flask import Flask  # The direct seam test needs one application config.

from src.foundation.persistence.db import DatabaseConfig  # The required real configuration boundary.
from src.foundation.persistence.db.router import DatabaseRouter  # The required real lifecycle boundary.
from src.interfaces.portals.upgrade_portal.app import factory, wiring  # The two lifecycle owners under test.


def test_real_database_constructor_signatures_match_provider_calls() -> None:
    """The provider call shape matches the real persistence constructors."""
    assert list(inspect.signature(DatabaseConfig.from_env).parameters) == []  # The class method takes no argument.
    router_parameters = inspect.signature(DatabaseRouter).parameters  # Read the supported public constructor.
    assert list(router_parameters) == ["config", "strategies"]  # Pass one configuration and use the optional map.
    assert router_parameters["strategies"].default is None  # The provider may omit the strategy argument.
    assert "database_router" in factory.REQUEST_HANDLES  # Existing teardown owns the provider router.
    assert "database_client" not in factory.REQUEST_HANDLES  # The provider adds no second database handle.


def test_complete_e2e_overrides_construct_no_provider_or_resource(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The complete override branch returns before production construction."""
    application = Flask(__name__)  # A direct seam test needs no route registration.
    supplied = object()  # One explicit E2E value proves the override map installed.
    overrides = SimpleNamespace(config_values=lambda: {"RUN_STORE": supplied})  # Match the complete override API.

    def refuse(*_args: Any, **_kwargs: Any) -> None:
        """Fail if production construction continues after the override return."""
        raise AssertionError("The E2E override path constructed a production resource.")

    monkeypatch.setattr(wiring, "PortalDependencyProvider", refuse)  # Detect provider construction.
    monkeypatch.setattr(wiring, "_install_action_repository", refuse)  # Detect existing production storage.
    monkeypatch.setattr(wiring, "prepare_storage", refuse)  # Detect existing production bootstrap.
    wiring.install_seams(application, overrides)  # Install the complete isolated dependency map.
    assert application.config["RUN_STORE"] is supplied  # The explicit override still wins.
    assert wiring.PORTAL_DEPENDENCY_PROVIDER_KEY not in application.config  # No production provider exists.
