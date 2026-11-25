"""Shared fixtures of the integration tests of the CLI flow."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.unit.ex_hardware_inventory.support.hardware_world import World


@pytest.fixture
def world(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> World:
    """Build the world for one test."""
    return World(monkeypatch, tmp_path)
