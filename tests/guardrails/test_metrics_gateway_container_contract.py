"""Guard the metrics gateway container startup and shared settings."""

from __future__ import annotations

import logging
import re
from pathlib import Path

import pytest

LOGGER = logging.getLogger(__name__)
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
START_SCRIPT = REPOSITORY_ROOT / "container" / "scripts" / "start.sh"
SERVICE_MODULE = REPOSITORY_ROOT / "src" / "interfaces" / "monitoring" / "metrics_gateway" / "service.py"
COMPOSE_FILE = REPOSITORY_ROOT / "compose.yml"
ENV_TEMPLATE = REPOSITORY_ROOT / "deploy" / ".env.example"
OPERATOR_GUIDE = REPOSITORY_ROOT / "documentation" / "operator-guide.md"
OID_SOURCE_PATHS = (START_SCRIPT, SERVICE_MODULE, COMPOSE_FILE, ENV_TEMPLATE, OPERATOR_GUIDE)
CANONICAL_OID_VARIABLE = "METRICS_SNMP_BASE_OID"
LEGACY_OID_VARIABLE = "SNMP_BASE_OID"


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


def read_oid_sources(paths: tuple[Path, ...] = OID_SOURCE_PATHS) -> dict[Path, str]:
    """Read each current OID setting surface and reject an empty scope."""
    LOGGER.info("Reading %d SNMP base OID setting files", len(paths))
    if not paths:
        print("The SNMP base OID variable guard checked 0 files.")
        raise ValueError("The SNMP base OID variable guard received 0 files.")
    sources: dict[Path, str] = {}
    for path in paths:
        if not path.is_file():
            print(f"The SNMP base OID variable guard checked {len(sources)} file(s).")
            raise FileNotFoundError(f"The SNMP base OID setting file is absent: {path}")
        sources[path] = path.read_text(encoding="utf-8")
    print(f"The SNMP base OID variable guard checked {len(sources)} file(s).")
    LOGGER.debug("Read %d SNMP base OID setting files", len(sources))
    return sources


def legacy_oid_assignments(sources: dict[Path, str]) -> tuple[str, ...]:
    """Return each current assignment that uses the retired variable name."""
    findings: list[str] = []
    pattern = re.compile(rf"(?m)^(?:\s*-\s*|\s*#\s*)?{LEGACY_OID_VARIABLE}=")
    for path, text in sources.items():
        for match in pattern.finditer(text):
            line_number = text.count("\n", 0, match.start()) + 1
            display_path = path.relative_to(REPOSITORY_ROOT) if path.is_relative_to(REPOSITORY_ROOT) else path
            findings.append(f"{display_path}:{line_number}")
    LOGGER.debug("Found %d legacy SNMP base OID assignments", len(findings))
    return tuple(findings)


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
        wait_commands = re.findall(r"^wait -n (.+) 2>/dev/null$", text, re.MULTILINE)
        expected = '"$GUNICORN_PID" "$CAPTURE_PID" "$METRICS_PID" "$SSHD_PID" "$SNMPD_PID"'
        assert wait_commands == [expected], f"service supervision has unexpected process identifiers: {wait_commands}"

    def test_a_metrics_gateway_crash_has_its_own_name(self) -> None:
        """The container log must identify the gateway instead of an unknown service."""
        text = read_start_script()
        crash_branches = re.findall(
            r'elif ! kill -0 "\$METRICS_PID" 2>/dev/null; then\s+' r'CRASHED_SERVICE="(the metrics gateway)"',
            text,
        )
        assert crash_branches == [
            "the metrics gateway"
        ], f"the crash classifier has unexpected metrics gateway branches: {crash_branches}"

    def test_the_metrics_port_is_validated_before_start(self) -> None:
        """An invalid published port must stop startup with a named error."""
        text = read_start_script()
        validations = re.findall(
            r'if ! \[\[ "\$METRICS_PORT" =~ \^\[0-9\]\+\$ \]\] '
            r'\|\| \[ "\$METRICS_PORT" -lt 1024 \] \|\| \[ "\$METRICS_PORT" -gt 65535 \]; then',
            text,
        )
        assert len(validations) == 1, f"expected 1 METRICS_PORT validation, found {len(validations)}"

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


class TestSnmpBaseOidVariableContract:
    """Require one SNMP base OID variable across every current setting surface."""

    def test_current_configuration_has_no_legacy_oid_assignment(self) -> None:
        """An old assignment lets the shell and Python select different OID trees."""
        sources = read_oid_sources()
        findings = legacy_oid_assignments(sources)
        assert findings == (), f"current files still assign {LEGACY_OID_VARIABLE}: {findings}"

    def test_the_shell_routes_snmp_with_the_canonical_variable(self) -> None:
        """The Net-SNMP route must use the same variable that Python reads."""
        text = read_oid_sources((START_SCRIPT,))[START_SCRIPT]
        expected = (
            f'"pass_persist ${{{CANONICAL_OID_VARIABLE}}} ' '/usr/local/bin/python3 /app/MistHelper.py --metrics-snmp"'
        )
        assert expected in text, f"start.sh does not route pass_persist with {CANONICAL_OID_VARIABLE}"

    def test_the_python_service_names_the_canonical_variable(self) -> None:
        """The Python setting remains the authority for the canonical name."""
        text = read_oid_sources((SERVICE_MODULE,))[SERVICE_MODULE]
        assert (
            f'BASE_OID_VARIABLE = "{CANONICAL_OID_VARIABLE}"' in text
        ), "the Python service no longer names the canonical SNMP base OID variable"

    def test_compose_supplies_one_canonical_oid_setting(self) -> None:
        """Compose must not inject two independently configurable OID values."""
        text = read_oid_sources((COMPOSE_FILE,))[COMPOSE_FILE]
        assignments = re.findall(r"(?m)^\s*-\s+((?:METRICS_)?SNMP_BASE_OID)=", text)
        assert assignments == [
            CANONICAL_OID_VARIABLE
        ], f"compose.yml has unexpected SNMP base OID settings: {assignments}"

    def test_the_environment_template_names_only_the_canonical_setting(self) -> None:
        """An operator must receive one setting name in the deployment template."""
        text = read_oid_sources((ENV_TEMPLATE,))[ENV_TEMPLATE]
        assignments = re.findall(r"(?m)^# ((?:METRICS_)?SNMP_BASE_OID)=", text)
        assert assignments == [
            CANONICAL_OID_VARIABLE
        ], f"the environment template has unexpected SNMP base OID settings: {assignments}"

    def test_the_operator_guide_names_only_the_canonical_setting(self) -> None:
        """The operator guide must not tell an operator to keep two values equal."""
        text = read_oid_sources((OPERATOR_GUIDE,))[OPERATOR_GUIDE]
        rows = re.findall(r"(?m)^\| `((?:METRICS_)?SNMP_BASE_OID)` \|", text)
        assert rows == [CANONICAL_OID_VARIABLE], f"the operator guide has unexpected SNMP base OID rows: {rows}"

    def test_a_mismatched_variable_name_fails_with_its_path(self) -> None:
        """The guard must name a current file that assigns the retired variable."""
        path = Path("temporary") / "start.sh"
        findings = legacy_oid_assignments({path: f"{LEGACY_OID_VARIABLE}=.1.3.6.1\n"})
        assert findings == (f"{path}:1",), "the mismatch proof did not name the retired variable assignment"

    def test_a_zero_file_scan_fails_instead_of_reporting_green(self) -> None:
        """A guard with no setting surface proves no variable-name contract."""
        with pytest.raises(ValueError, match="0 files"):
            read_oid_sources(())
        assert len(OID_SOURCE_PATHS) == 5, "the production guard scope changed without a contract update"
