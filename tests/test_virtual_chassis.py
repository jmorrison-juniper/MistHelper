"""Tests for VirtualChassisManager.convert_single option 92 behavior."""

from __future__ import annotations  # Keep type annotations cheap during test collection.

from unittest.mock import ANY, MagicMock  # Assert control flow without touching the Mist API.

import pytest  # Provide the monkeypatch fixture used by the flow test.

import MistHelper  # Use the public menu surface that option 92 exposes.
from src.device.virtual_chassis import VCIODeps  # Build the dependency bundle used by the manager.


def test_convert_virtual_chassis_requires_preflight_and_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify dry-run conversion reaches preflight but never executes the API call."""
    selected = {"id": "dev-1", "name": "switch-a"}  # Supply the row that the switch picker returns.
    io_deps = VCIODeps(  # Build required collaborators without reading local CSV files.
        get_csv_path_fn=lambda name: name,  # Keep path resolution inert for this flow test.
        check_and_generate_csv_fn=lambda name, generator: True,  # Avoid cache generation side effects.
        inventory_generator=lambda: None,  # Provide the required callback without doing work.
        sites_generator=lambda: None,  # Provide the required callback without doing work.
    )
    dry_run_printer = MagicMock()  # Record that dry-run output replaced the API call.
    executor = MagicMock()  # Record whether the destructive conversion path ran.
    validator = MagicMock(return_value="dev-1")  # Prove the preflight gate executed.
    manager = MistHelper.VirtualChassisManager  # Exercise the public class reached from MistHelper menu code.
    monkeypatch.setattr(  # Replace site selection so the test can focus on conversion flow.
        manager,  # Patch the real manager under test.
        "_resolve_site",  # Patch the helper that owns user interaction.
        lambda session, selector: ("site-1", "Site One"),  # Return a stable selected site for the flow test.
    )
    monkeypatch.setattr(manager, "_pick_switch", lambda *args: selected)  # Bypass CSV selection.
    monkeypatch.setattr(manager, "_validate_switch", validator)  # Observe the preflight gate.
    monkeypatch.setattr(manager, "_print_dry_run", dry_run_printer)  # Observe dry-run output.
    monkeypatch.setattr(manager, "_execute_conversion", executor)  # Guard the real API call.

    manager.convert_single(  # Exercise the real branch structure under dry-run mode.
        apisession=object(),  # Use an inert session because the dry-run path must not call the API.
        io_deps=io_deps,  # Provide the dependencies required by the public method.
        safe_input_fn=lambda *args, **kwargs: "CONVERT",  # Keep prompts deterministic if reached.
        select_site_fn=lambda: "site-1",  # Keep site selection deterministic if reached.
        dry_run=True,  # Request the non-destructive path that the menu exposes.
    )

    validator.assert_called_once_with(selected, ANY)  # Preflight must run before any conversion decision.
    dry_run_printer.assert_called_once_with(selected, "Site One", "dev-1", "site-1")  # Dry-run must show target data.
    executor.assert_not_called()  # Dry-run must not execute the destructive API call.
