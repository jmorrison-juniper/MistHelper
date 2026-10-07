"""Guard the metrics gateway container startup and shared settings."""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pytest

LOGGER = logging.getLogger(__name__)
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
START_SCRIPT = REPOSITORY_ROOT / "container" / "scripts" / "start.sh"


def read_start_script(path: Path = START_SCRIPT) -> str:
    """Read one startup script and fail when the guard has no input."""
    LOGGER.info("Reading the container startup script at %s", path)
    if not path.is_file():
        print("The metrics gateway startup guard checked 0 files.")
        raise FileNotFoundError(f"The startup script is absent: {path}")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        print("The metrics gateway startup guard checked 0 startup commands.")
        raise ValueError("The startup script has no startup commands.")
    print("The metrics gateway startup guard checked 1 file.")
    LOGGER.debug("Read %d characters from the container startup script", len(text))
    return text


class TestMetricsGatewayStartupContract:
    """Require one supervised metrics gateway process in the container."""

    def test_the_container_starts_the_metrics_gateway_mode(self) -> None:
        """The published port needs a process that starts the gateway mode."""
        text = read_start_script()
        commands = re.findall(
            r'^su misthelper -c "cd /app && exec /usr/local/bin/python3 /app/MistHelper\.py --metrics-gateway'
            r' >> /app/data/metrics_gateway\.log 2>&1" &$',
            text,
            re.MULTILINE,
        )
        assert len(commands) == 1, f"expected 1 metrics gateway startup command, found {len(commands)}"

    def test_the_container_records_the_metrics_gateway_process(self) -> None:
        """Cleanup and supervision need the process identifier from the launch."""
        text = read_start_script()
        assert text.count("METRICS_PID=$!") == 1, "the startup script does not record one metrics gateway process"

    def test_cleanup_stops_and_waits_for_the_metrics_gateway(self) -> None:
        """A container stop must not leave the gateway process behind."""
        text = read_start_script()
        cleanup = text.split("cleanup() {", maxsplit=1)[1].split("}\n", maxsplit=1)[0]
        assert 'kill "$METRICS_PID"' in cleanup, "cleanup does not stop the metrics gateway"
        assert (
            '_wait_for_pid_or_kill "$METRICS_PID" "$kill_wait"' in cleanup
        ), "cleanup does not wait for the metrics gateway"

    def test_supervision_watches_the_metrics_gateway(self) -> None:
        """A gateway exit must stop the container with a failure status."""
        text = read_start_script()
        wait_command = re.search(r"^wait -n (?P<pids>.+) 2>/dev/null$", text, re.MULTILINE)
        assert wait_command is not None, "the startup script has no service supervision wait"
        assert '"$METRICS_PID"' in wait_command.group("pids"), "service supervision omits the metrics gateway"

    def test_a_metrics_gateway_crash_has_its_own_name(self) -> None:
        """The container log must identify the gateway instead of an unknown service."""
        text = read_start_script()
        crash_branch = re.search(
            r'elif ! kill -0 "\$METRICS_PID" 2>/dev/null; then\s+' r'CRASHED_SERVICE="the metrics gateway"',
            text,
        )
        assert crash_branch is not None, "the crash classifier does not name the metrics gateway"

    def test_the_metrics_port_is_validated_before_start(self) -> None:
        """An invalid published port must stop startup with a named error."""
        text = read_start_script()
        validation = re.search(
            r'if ! \[\[ "\$METRICS_PORT" =~ \^\[0-9\]\+\$ \]\] '
            r'\|\| \[ "\$METRICS_PORT" -lt 1024 \] \|\| \[ "\$METRICS_PORT" -gt 65535 \]; then',
            text,
        )
        assert validation is not None, "the startup script does not validate METRICS_PORT"

    @pytest.mark.parametrize("source", [None, ""], ids=["missing", "empty"])
    def test_the_guard_rejects_missing_or_empty_input(self, tmp_path: Path, source: str | None) -> None:
        """A guard with no startup commands must not report success."""
        path = tmp_path / "start.sh"
        if source is not None:
            path.write_text(source, encoding="utf-8")
        expected = FileNotFoundError if source is None else ValueError
        with pytest.raises(expected, match="startup script|startup commands"):
            read_start_script(path)
        assert path.is_file() is (source is not None), "the proof input state changed during the guard"
