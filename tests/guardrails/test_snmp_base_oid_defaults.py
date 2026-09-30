"""Keep the container SNMP fallback aligned with the responder (issue #3417).

Read only the OID assignment. Never start the container or the SNMP service.
The guard reports its measured count and fails if it cannot read its input.
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
from pathlib import Path

import pytest

from src.metrics_gateway.snmp import DEFAULT_BASE_OID

LOGGER = logging.getLogger(__name__)
START_SCRIPT = Path(__file__).resolve().parents[2] / "container" / "scripts" / "start.sh"


class TestSnmpBaseOidDefaults:
    """Check the defaults and preserve the shell override order without networking."""

    @staticmethod
    def _assignment() -> re.Match[str]:
        """Read one restricted assignment without executing the startup script."""
        LOGGER.info("Reading the container SNMP base OID assignment")
        script = START_SCRIPT.read_text(encoding="utf-8")
        matches = list(
            re.finditer(
                r'^SNMP_BASE_OID="\$\{SNMP_BASE_OID:-\$\{METRICS_SNMP_BASE_OID:-(\.[0-9.]+)\}\}"(?:[ \t]+#.*)?$',
                script,
                re.MULTILINE,
            )
        )
        LOGGER.debug("Read %d SNMP base OID assignments", len(matches))
        assert len(matches) == 1, f"Expected 1 SNMP base OID assignment, found {len(matches)}."
        return matches[0]

    @staticmethod
    def _compare_defaults(container_default: str, responder_default: str) -> None:
        """Report the measured count before rejecting different defaults."""
        LOGGER.info("Comparing 2 SNMP base OID defaults")
        print("Compared 2 SNMP base OID defaults.")
        assert container_default == responder_default, (
            f"Compared 2 SNMP base OID defaults: container {container_default!r} "
            f"differs from responder {responder_default!r}."
        )
        LOGGER.debug("Compared 2 SNMP base OID defaults with no differences")

    def test_defaults_match(self) -> None:
        """The shipped startup fallback matches the responder constant."""
        assignment = self._assignment()
        self._compare_defaults(assignment.group(1), DEFAULT_BASE_OID)

    @pytest.mark.parametrize(
        ("container_default", "responder_default"),
        [
            (".1.3.6.1.4.1.11.2147483646", DEFAULT_BASE_OID),
            (DEFAULT_BASE_OID, ".1.3.6.1.4.1.8072.9999.9998"),
        ],
    )
    def test_mismatches_fail(self, container_default: str, responder_default: str) -> None:
        """Either default can change, and the same guard must reject the difference."""
        with pytest.raises(AssertionError, match="Compared 2 SNMP base OID defaults"):
            self._compare_defaults(container_default, responder_default)

    @pytest.mark.parametrize(
        ("snmp_override", "metrics_override", "expected"),
        [
            (None, None, DEFAULT_BASE_OID),
            ("", "", DEFAULT_BASE_OID),
            ("", None, DEFAULT_BASE_OID),
            (None, "", DEFAULT_BASE_OID),
            (".1.3.6.1.4.1.123.1", None, ".1.3.6.1.4.1.123.1"),
            (None, ".1.3.6.1.4.1.123.2", ".1.3.6.1.4.1.123.2"),
            ("", ".1.3.6.1.4.1.123.2", ".1.3.6.1.4.1.123.2"),
            (".1.3.6.1.4.1.123.1", "", ".1.3.6.1.4.1.123.1"),
            (".1.3.6.1.4.1.123.1", ".1.3.6.1.4.1.123.2", ".1.3.6.1.4.1.123.1"),
        ],
    )
    def test_shell_overrides(self, snmp_override: str | None, metrics_override: str | None, expected: str) -> None:
        """Evaluate only the restricted assignment to preserve unset, empty, and explicit values."""
        assignment = self._assignment().group(0).split('"', 2)[1]
        environment = os.environ.copy()
        for name, value in (("SNMP_BASE_OID", snmp_override), ("METRICS_SNMP_BASE_OID", metrics_override)):
            environment.pop(name, None)
            if value is not None:
                environment[name] = value
        LOGGER.info("Evaluating 1 restricted SNMP base OID assignment")
        result = subprocess.run(
            ["/bin/bash", "-c", f'SNMP_BASE_OID="{assignment}"\nprintf "%s" "$SNMP_BASE_OID"'],
            env=environment,
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        LOGGER.debug("Evaluated 1 SNMP base OID assignment with status %d", result.returncode)
        assert result.stdout == expected
