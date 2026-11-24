"""Guardrail: the Observium sensor script runs after the image's first-run script.

Why:
    The Observium image runs `my_init`, which executes every file in
    `/etc/my_init.d/` in name order. The image script `firstrun.sh` creates
    `/config/config.php`. The repository's sensor script exits 1 while that file
    is missing, and `my_init` then stops every process in the container. A mount
    name that sorts before `firstrun.sh` therefore restarts the container on every
    first boot, and the container never reaches a working state.

    A comment cannot hold this ordering rule for a later edit. These tests read
    the compose file and fail when the sensor script is mounted under a name that
    sorts before, or equal to, the first-run script.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")  # PyYAML ships with the project requirements.

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
COMPOSE_PATH = REPOSITORY_ROOT / "compose.yml"

OBSERVIUM_SERVICE = "misthelper-observium"  # The compose service that runs the Observium image.
INIT_FOLDER = "/etc/my_init.d/"  # The folder that my_init runs in name order.
FIRST_RUN_SCRIPT = "firstrun.sh"  # The image script that creates /config/config.php.
SENSOR_SCRIPT_NAME = "add-mist-static-sensors"  # Finds the sensor script among the mounts.


@pytest.fixture(scope="module")
def compose() -> dict[str, Any]:
    """Read the compose file once for every test in this module.

    Returns:
        The parsed document.
    """
    return dict(yaml.safe_load(COMPOSE_PATH.read_text(encoding="utf-8")))


def runs_after_first_run(file_name: str) -> bool:
    """Tell whether `my_init` runs a file name after the first-run script.

    Why:
        `my_init` sorts names byte by byte. Python compares ASCII strings by code
        point, and for ASCII names that order is the same.

    Args:
        file_name: The base name of a file inside `/etc/my_init.d/`.

    Returns:
        True when the name sorts strictly after `firstrun.sh`.
    """
    return file_name > FIRST_RUN_SCRIPT


def init_mount_names(compose: dict[str, Any]) -> list[str]:
    """Return the base name of each sensor-script mount inside `/etc/my_init.d/`.

    Why:
        The mount target sets the run order, and the host file keeps its own name.
        The guard therefore reads the target column of each volume string.

    Args:
        compose: The parsed compose document.

    Returns:
        One base name for each sensor-script mount. The list is empty when no such
        mount exists, so the caller must check for that case.
    """
    volumes = compose["services"][OBSERVIUM_SERVICE].get("volumes", [])
    names: list[str] = []
    for volume in volumes:
        parts = str(volume).split(":")
        if len(parts) >= 2 and SENSOR_SCRIPT_NAME in parts[0] and parts[1].startswith(INIT_FOLDER):
            names.append(parts[1].removeprefix(INIT_FOLDER))
    return names


class TestSensorScriptOrder:
    """The sensor script runs after the first-run script, so the container starts."""

    def test_the_sensor_script_is_mounted_once(self, compose: dict[str, Any]) -> None:
        """A missing mount would hide the defect, so the guard also requires one mount."""
        names = init_mount_names(compose)
        assert len(names) == 1, f"Expected one sensor-script mount in {INIT_FOLDER}, found {names}"

    def test_the_sensor_script_sorts_after_the_first_run_script(self, compose: dict[str, Any]) -> None:
        """The first-run script creates config.php, and the sensor script needs that file."""
        for name in init_mount_names(compose):
            assert runs_after_first_run(
                name
            ), f"{name} does not sort after {FIRST_RUN_SCRIPT}, so my_init runs it before config.php exists"


class TestOrderRule:
    """The ordering rule accepts the fixed name and rejects the name that failed."""

    @pytest.mark.parametrize(
        ("file_name", "expected"),
        [
            ("20-add-mist-static-sensors.sh", False),  # The name that caused the restart loop.
            (FIRST_RUN_SCRIPT, False),  # An equal name collides with the first-run script.
            ("zz-add-mist-static-sensors.sh", True),  # The name that compose.yml mounts now.
        ],
    )
    def test_rule_classifies_each_name(self, file_name: str, expected: bool) -> None:
        """Each name has one expected answer, so a change to the rule shows up at once."""
        assert runs_after_first_run(file_name) is expected

    def test_guard_detects_the_old_mount(self) -> None:
        """A compose document with the old mount must fail the guard, so the guard can fail."""
        old_compose = {
            "services": {
                OBSERVIUM_SERVICE: {
                    "volumes": [
                        "./container/observium/20-add-mist-static-sensors.sh:"
                        "/etc/my_init.d/20-add-mist-static-sensors.sh:ro",
                    ]
                }
            }
        }
        assert init_mount_names(old_compose) == ["20-add-mist-static-sensors.sh"]
        assert not runs_after_first_run("20-add-mist-static-sensors.sh")
