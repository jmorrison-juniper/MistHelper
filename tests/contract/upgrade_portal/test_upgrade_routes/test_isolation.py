"""Prove that the factory installs E2E isolation before route registration.

Why:
    The test portal holds its records in the stores of the test process, and
    the factory installs those stores before the first route registers. Issue
    #3501 removed the connector traps, the audit store, and the fixed test
    headers, because no code read them. An isolated response now carries the
    run owner header only.
"""

from __future__ import annotations  # Keep annotations independent from import order.

from typing import Any, cast  # Build one deliberate invalid value for validation.

import pytest  # Check fail-closed construction.

from src.upgrade_portal.api.run_controls import (  # Import the explicit factory value groups.
    E2EActionOverrides,
    E2EExternalOverrides,
    E2EFactoryOverrides,
    E2ERecordOverrides,
    E2ESecurityOverrides,
)
from src.upgrade_portal.app import factory, wiring  # Test the real construction order.
from tests.support.upgrade_portal_e2e import (  # Import the process stores and the owner check.
    ActionRecordStore,
    PortalRecordStore,
    RunOwnerHeaderCheck,
    ScriptedCloudStore,
)


def _callable(*_arguments: object, **_options: object) -> object:  # Provide one harmless callable seam.
    """Return one harmless stand-in result."""
    return {}  # The contract tests inspect construction, not route data.


def _overrides(test_run_id: str = "e2e-contract-owner") -> E2EFactoryOverrides:  # Build one complete test value.
    """Build one complete process-owned override value."""
    portal = PortalRecordStore(test_run_id)  # Own run, capture, lock, and access records.
    actions = ActionRecordStore(test_run_id)  # Own action records.
    cloud = ScriptedCloudStore(test_run_id)  # Own scripted cloud evidence.
    records = E2ERecordOverrides(  # Bind all run and capture seams.
        portal, portal, _callable, portal.load_capture, portal.list_captures, portal.list_runs, portal.list_operations
    )
    action_values = E2EActionOverrides(  # Bind all action and upgrade seams.
        actions, _callable, _callable, _callable, _callable, _callable, portal
    )
    security = E2ESecurityOverrides(_callable, portal, portal.authorization)  # Bind the lock and access seams.
    external = E2EExternalOverrides(cloud, cloud.read, _callable)  # Bind the scripted cloud seams.
    return E2EFactoryOverrides(test_run_id, records, action_values, security, external)  # Complete value.


def test_factory_installs_overrides_before_blueprint_registration(  # Prove safe construction order.
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every required override exists before the first blueprint registers."""
    overrides = _overrides()  # Build the complete dependency set.
    observed: list[bool] = []  # Record whether the route boundary saw the installed values.

    def record_registration(app: Any) -> None:  # Inspect the route registration boundary.
        """Record the configuration state at the route registration boundary."""
        expected = overrides.config_values()  # Read the same explicit map that wiring installs.
        observed.append(all(app.config.get(key) is value for key, value in expected.items()))  # Check identity.

    monkeypatch.setattr(factory, "register_blueprints", record_registration)  # Observe the exact boundary.
    factory.create_app(overrides)  # Construct the real application with no production fallback.
    assert observed == [True]  # The dependency set must exist before route registration starts.


def test_factory_does_not_start_production_storage_for_e2e(
    monkeypatch: pytest.MonkeyPatch,
) -> None:  # Prove E2E construction skips the production bootstrap.
    """E2E construction returns before the production storage bootstrap."""
    calls: list[str] = []  # Record any unsafe bootstrap attempt.
    monkeypatch.setattr(wiring, "prepare_storage", lambda: calls.append("prepare"))  # Trap the bootstrap call.
    factory.create_app(_overrides())  # Construct the real isolated application.
    assert calls == []  # E2E construction must not start production storage.


def test_factory_rejects_missing_overrides_before_blueprints(  # Prove fail-closed construction.
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An incomplete E2E value fails before route registration."""
    overrides = _overrides()  # Start from one complete value.
    broken = E2EExternalOverrides(  # Replace one required cloud read with an invalid value.
        overrides.external.cloud_evidence,
        overrides.external.cloud_reader,
        cast(Any, None),  # Supply one deliberate missing required cloud read.
    )
    registrations: list[str] = []  # Record any route registration attempt.
    monkeypatch.setattr(  # Record any unsafe route registration attempt.
        factory, "register_blueprints", lambda _app: registrations.append("registered")
    )
    with pytest.raises(ValueError, match="external.device_reader"):  # Name the missing boundary.
        factory.create_app(  # Attempt construction with one missing required cloud read.
            E2EFactoryOverrides(
                overrides.test_run_id,
                overrides.records,
                overrides.actions,
                overrides.security,
                broken,
            )
        )
    assert registrations == []  # No blueprint can exist after failed validation.


def test_e2e_header_is_present_only_for_overrides(  # Prove the response header stays test-only.
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only an E2E application returns a test header, and it returns the run owner header only."""
    monkeypatch.setattr(wiring, "prepare_storage", lambda: None)  # Keep production construction offline.
    isolated = factory.create_app(_overrides("e2e-header-owner"))  # Build the isolated application.
    production = factory.create_app()  # Build the compatible no-argument production form.
    isolated_answer = isolated.test_client().get("/healthz")  # Read a route that needs no session.
    production_answer = production.test_client().get("/healthz")  # Read the same production route.
    assert isolated_answer.headers["X-MistHelper-E2E-Run-ID"] == "e2e-header-owner"  # Bind the response.
    assert "X-MistHelper-E2E-Run-ID" not in production_answer.headers  # Keep production responses clean.
    isolated_names = RunOwnerHeaderCheck.e2e_header_names(isolated_answer.headers)  # Issue #3501: each test header.
    assert isolated_names == ("x-misthelper-e2e-run-id",)  # Issue #3501: no header holds a fixed count.
    assert RunOwnerHeaderCheck.e2e_header_names(production_answer.headers) == ()  # Production sends no test header.
