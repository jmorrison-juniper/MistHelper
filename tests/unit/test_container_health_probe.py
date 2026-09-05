"""Guard the container health probe command (issues #1863, #1881).

The Quadlet unit ran the probe with `curl`. The image installs
`ca-certificates`, `openssh-server`, and `sudo` only, so the image holds no curl
binary. The probe failed on every call, and `HealthOnFailure=restart` restarted
a healthy container in a loop.

These tests read text only. They import no application module and they start no
container, so they run in any environment.
"""

import re  # Match each probe command without a parse of the whole file format.
from pathlib import Path  # Portable paths, because the repository runs on Windows and on Linux.

import pytest  # Test framework of the repository.

REPO_ROOT = Path(__file__).resolve().parents[2]  # tests/unit/<file> sits two levels below the root.
QUADLET_UNIT = REPO_ROOT / "deploy" / "misthelper.container"  # The systemd Quadlet unit.
CONTAINERFILE = REPO_ROOT / "Containerfile"  # The Podman build file.
DOCKERFILE = REPO_ROOT / "Dockerfile"  # The Docker build file.
COMPOSE_FILE = REPO_ROOT / "compose.yml"  # The compose stack definition.

_READINESS_PATH = "/ready"  # Every probe must call the readiness endpoint, not the liveness one.
_CURL_CALL = re.compile(r"\bcurl\b")  # A word match, so the word "curled" in prose cannot trip the test.
_RUNTIME_SCRIPT_COPY = "COPY scripts/ ./scripts/"  # The Zscaler catalogue imports the city metadata helper at runtime.


def _probe_command_lines(path: Path, marker: str) -> list[str]:
    """Return every line of *path* that holds the probe *marker* and is not a comment."""
    lines = path.read_text(encoding="utf-8").splitlines()  # Read once, because each test scans the same text.
    return [line for line in lines if marker in line and not line.lstrip().startswith("#")]


class TestNoProbeCallsCurl:
    """No probe command may call curl, because the image installs no curl."""

    @pytest.mark.parametrize(
        ("path", "marker"),
        [
            (QUADLET_UNIT, "HealthCmd="),
            (CONTAINERFILE, "HEALTHCHECK"),
            (DOCKERFILE, "HEALTHCHECK"),
            (COMPOSE_FILE, "healthcheck"),
        ],
        ids=["quadlet", "containerfile", "dockerfile", "compose"],
    )
    def test_probe_command_avoids_curl(self, path: Path, marker: str):
        """The probe runs the Python interpreter, because the image holds no curl binary."""
        text = path.read_text(encoding="utf-8")  # Read the whole file, because a probe can span two lines.
        probe_region = text.split(marker, 1)[-1][:600]  # Read the text after the marker only.
        assert not _CURL_CALL.search(probe_region), f"The probe in {path.name} calls curl, which the image lacks."


class TestProbeTargetsReadiness:
    """Every probe must call the readiness endpoint."""

    def test_quadlet_unit_probe_calls_the_readiness_endpoint(self):
        """The Quadlet HealthCmd calls /ready, so a read-only data mount marks the container unhealthy."""
        commands = _probe_command_lines(QUADLET_UNIT, "HealthCmd=")
        assert commands, "The Quadlet unit defines no HealthCmd."
        assert all(_READINESS_PATH in line for line in commands)  # A liveness call cannot detect a bad mount.

    def test_containerfile_probe_calls_the_readiness_endpoint(self):
        """The Containerfile HEALTHCHECK calls /ready."""
        text = CONTAINERFILE.read_text(encoding="utf-8")  # Read the build file text.
        assert "HEALTHCHECK" in text, "The Containerfile defines no HEALTHCHECK."
        assert _READINESS_PATH in text.split("HEALTHCHECK", 1)[-1][:600]  # The command follows the instruction.

    def test_compose_service_defines_a_health_check(self):
        """The misthelper service carries a healthcheck block that calls /ready."""
        text = COMPOSE_FILE.read_text(encoding="utf-8")  # Read the compose stack text.
        assert "healthcheck:" in text, "The compose file defines no healthcheck block."
        assert _READINESS_PATH in text.split("healthcheck:", 1)[-1][:600]  # The first block is the portal one.


class TestCaptureRuntimeScripts:
    """The image must include scripts that the capture runtime imports."""

    @pytest.mark.parametrize("path", [CONTAINERFILE, DOCKERFILE], ids=["containerfile", "dockerfile"])
    def test_image_copies_the_capture_runtime_scripts(self, path: Path):
        """The image includes the city metadata helper required by the Zscaler catalogue import."""
        text = path.read_text(encoding="utf-8")  # Read the build file once for its copy instructions.
        assert _RUNTIME_SCRIPT_COPY in text, f"{path.name} omits the scripts package required at runtime."


class TestQuadletProbeKeys:
    """The Quadlet unit must keep the timing keys and the restart key."""

    @pytest.mark.parametrize(
        "key",
        ["HealthInterval=", "HealthTimeout=", "HealthRetries=", "HealthStartPeriod=", "HealthOnFailure=restart"],
    )
    def test_quadlet_unit_keeps_the_probe_key(self, key: str):
        """A missing key leaves the probe without a schedule or without a recovery action."""
        text = QUADLET_UNIT.read_text(encoding="utf-8")  # Read the unit text.
        assert key in text, f"The Quadlet unit lost the key {key}."


if __name__ == "__main__":  # Allow a direct run during local development.
    raise SystemExit(pytest.main([__file__, "-q"]))  # Run only this module.
