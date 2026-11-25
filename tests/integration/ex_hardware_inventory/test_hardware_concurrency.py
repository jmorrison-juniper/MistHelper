"""Integration tests of the concurrency setting for the CLI menu (issue #4920).

One variable, ``PORTAL_WS_HARDWARE_CONCURRENCY``, limits the open shells. These tests run the real batch runner with a
fake shell that records the peak of open shells.
"""

from __future__ import annotations

import logging  # Prove that a bad value gives one warning that names the variable.

import pytest  # Parametrize and capture.

from tests.unit.ex_hardware_inventory.support.hardware_shells import uuid  # Invented identifiers.
from tests.unit.ex_hardware_inventory.support.hardware_world import ORG_A, SITE_1, World, run_menu  # Shared world.


def twelve_switches(world: World) -> None:
    """Script one site with twelve connected EX switches that answer slowly, so the shells overlap."""
    world.org_token()
    world.mist.add(
        ORG_A,
        (SITE_1, "Site One"),
        [(uuid(100 + index), f"ex-{index:02d}", "switch", "EX4100-48P") for index in range(1, 13)],
    )
    world.shells.hold_seconds = 0.2  # Each shell holds long enough for the others to open.
    world.answer = "RUN 12 TARGETS"


class TestPeakOfOpenShells:
    """The peak of open shells never passes the setting, and the console shows the value in use."""

    @pytest.mark.parametrize("limit", [1, 3, 5])
    def test_twelve_targets_never_open_more_shells_than_the_setting(
        self, world: World, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], limit: int
    ) -> None:
        """For limits 1, 3, and 5, all twelve switches are collected and the peak stays within the limit."""
        monkeypatch.setenv("PORTAL_WS_HARDWARE_CONCURRENCY", str(limit))
        twelve_switches(world)
        _, lines = run_menu(capsys)
        assert world.shells.opened == 12 and world.shells.open == 0  # Every switch was collected.
        assert world.shells.peak <= limit  # The limit held.
        assert limit == 1 or world.shells.peak >= 2  # And the shells did overlap when the limit allowed it.
        assert f"  Shells open at the same time: {limit}" in lines  # The console shows the value in use.

    def test_the_default_is_three(self, world: World, capsys: pytest.CaptureFixture[str]) -> None:
        """With no variable, three shells run at the same time."""
        twelve_switches(world)
        _, lines = run_menu(capsys)
        assert "  Shells open at the same time: 3" in lines and world.shells.peak <= 3

    @pytest.mark.parametrize("raw", ["0", "6", "-1", "lots", "2.5"])
    def test_a_bad_value_gives_the_default_and_one_warning_that_names_the_variable(
        self,
        world: World,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
        caplog: pytest.LogCaptureFixture,
        raw: str,
    ) -> None:
        """A value outside 1 through 5, or a non-number, gives three shells and one warning."""
        caplog.set_level(logging.WARNING)
        monkeypatch.setenv("PORTAL_WS_HARDWARE_CONCURRENCY", raw)
        twelve_switches(world)
        _, lines = run_menu(capsys)
        assert "  Shells open at the same time: 3" in lines and world.shells.peak <= 3
        assert caplog.text.count("PORTAL_WS_HARDWARE_CONCURRENCY") >= 1  # The warning names the variable.

    def test_the_session_limit_caps_the_value_in_use(
        self, world: World, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """A shared capacity of two sessions caps a setting of five, and the console shows two."""
        monkeypatch.setenv("PORTAL_WS_HARDWARE_CONCURRENCY", "5")
        monkeypatch.setenv("PORTAL_WS_MAX_SESSIONS", "2")
        twelve_switches(world)
        _, lines = run_menu(capsys)
        assert "  Shells open at the same time: 2" in lines and world.shells.peak <= 2
