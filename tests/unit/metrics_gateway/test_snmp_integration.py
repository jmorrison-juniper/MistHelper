"""Tests that hold the Net-SNMP pass_persist integration contract.

Why:
    A real `snmpd` found three faults that every in-memory test had passed.
    `snmpd` starts the responder as a child process, reads the replies from a
    pipe, and merges the child standard error into that same pipe. The net-snmp
    source states the merge in `get_exec_pipes`:

        netsnmp_close_fds(STDOUT_FILENO);
        dup2(STDOUT_FILENO, STDERR_FILENO);

    A test that hands the responder an in-memory stream can model none of that.
    These tests run the responder in a real child process with the two streams
    merged, which is the shape `snmpd` builds.
"""

from __future__ import annotations

import logging
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

from src.metrics_gateway.snmp import protect_protocol_streams

REPO_ROOT = Path(__file__).resolve().parents[3]  # The folder that holds `src`.

PROCESS_TIMEOUT_SECONDS = 90  # A generous bound. A deadlock must fail the test and never hang the run.

# WHY: This mirrors the real entry point. It configures logging to write to
# standard error at DEBUG, which is the worst case, then takes the two streams
# away from logging before it builds anything. The catalog logs while it builds,
# so the order matters and this script proves the order.
HELPER_SOURCE = """
import logging, sys
sys.path.insert(0, {root!r})
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

from src.metrics_gateway.snmp import SnmpPassPersistResponder, protect_protocol_streams
protect_protocol_streams()

from src.metrics_gateway.cache import MetricsCache
from src.metrics_gateway.collector import MistMetricsCollector, MistStatsReader

class R:
    def __init__(self, data):
        self.data = data
        self.status_code = 200

ORG = {{"name": "Test Org", "num_sites": 2}}
OVERRIDES = {{
    "getOrgStats": lambda s, o: R(ORG),
    "listOrgSiteStats": lambda s, o, **k: R([]),
    "listOrgDevicesStats": lambda s, o, **k: R([]),
}}
cache = MetricsCache(MistMetricsCollector(MistStatsReader(None, OVERRIDES), "org-1"))
SnmpPassPersistResponder(cache, ".1.3.6.1.4.1.8072.9999.9999").run(sys.stdin, sys.stdout)
"""


def _write_helper(tmp_path: Path) -> Path:
    """Write the helper script that the child process runs.

    Args:
        tmp_path: The folder pytest gave this test.

    Returns:
        The path of the script.
    """
    script = tmp_path / "helper.py"
    script.write_text(textwrap.dedent(HELPER_SOURCE).format(root=str(REPO_ROOT)), encoding="utf-8")
    return script


def _run_protocol(script: Path, requests: str) -> str:
    """Run the helper as `snmpd` runs it and return everything the pipe carried.

    Why:
        `stderr=subprocess.STDOUT` is the point of this helper. It reproduces the
        `dup2` that net-snmp performs, so a stray log record lands in the reply
        stream here exactly as it does under a real `snmpd`.

    Args:
        script: The helper script path.
        requests: The request lines, already ending in line breaks.

    Returns:
        The text the child wrote to the merged stream.
    """
    child = subprocess.Popen(  # The command is this interpreter and a file this test wrote.
        [sys.executable, str(script)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # The merge that net-snmp performs.
        text=True,
    )
    try:
        output, _ = child.communicate(requests, timeout=PROCESS_TIMEOUT_SECONDS)
        return output
    finally:
        if child.poll() is None:  # A deadlock must not leave a process behind.
            child.kill()
            child.wait(timeout=10)


@pytest.mark.timeout(PROCESS_TIMEOUT_SECONDS + 30)
class TestPassPersistAgainstARealPipe:
    """The reply stream must carry the protocol and nothing else."""

    def test_a_ping_answers_pong_and_nothing_else(self, tmp_path: Path) -> None:
        """`snmpd` closes the pipe when the first line it reads is not PONG.

        A real `snmpd` reported `Got DEBUG:...Build the metric catalog instead of
        PONG!` before this was fixed, and the whole subtree answered nothing.
        """
        output = _run_protocol(_write_helper(tmp_path), "PING\n")
        assert output == "PONG\n", f"The pipe carried more than the protocol: {output!r}"

    def test_no_log_record_reaches_the_reply_stream(self, tmp_path: Path) -> None:
        """The helper logs at DEBUG to standard error, which `snmpd` merges into the pipe."""
        output = _run_protocol(_write_helper(tmp_path), "PING\nget\n.1.3.6.1.4.1.8072.9999.9999.1.2.0\n")
        for marker in ("DEBUG", "INFO", "WARNING", "No handlers could be found"):
            assert marker not in output, f"The text {marker!r} corrupted the reply stream: {output!r}"

    def test_a_get_returns_the_three_protocol_lines(self, tmp_path: Path) -> None:
        """`snmpd` reads the OID, then the type, then the value."""
        output = _run_protocol(_write_helper(tmp_path), "PING\nget\n.1.3.6.1.4.1.8072.9999.9999.1.2.0\n")
        assert output.splitlines() == ["PONG", ".1.3.6.1.4.1.8072.9999.9999.1.2.0", "gauge", "2"]

    def test_a_walk_step_moves_forward(self, tmp_path: Path) -> None:
        """A walk depends on `getnext` returning a strictly larger OID."""
        output = _run_protocol(_write_helper(tmp_path), "getnext\n.1.3.6.1.4.1.8072.9999.9999\n")
        assert output.splitlines()[0].startswith(".1.3.6.1.4.1.8072.9999.9999.")

    def test_the_responder_serves_many_requests_in_one_session(self, tmp_path: Path) -> None:
        """`snmpd` keeps one child alive and sends every request down the same pipe."""
        requests = "PING\n" + "get\n.1.3.6.1.4.1.8072.9999.9999.1.2.0\n" * 5
        output = _run_protocol(_write_helper(tmp_path), requests)
        assert output.splitlines().count("gauge") == 5


class TestStreamProtection:
    """The guard must take both protocol streams away from logging."""

    def test_it_removes_a_handler_that_writes_to_the_reply_stream(self) -> None:
        """A handler on standard output would put a log record inside the protocol."""
        root = logging.getLogger()
        handler = logging.StreamHandler(sys.stdout)
        root.addHandler(handler)
        try:
            protect_protocol_streams()
            assert handler not in root.handlers
        finally:
            root.removeHandler(handler)  # Leave the logging configuration as this test found it.

    def test_it_removes_a_handler_that_writes_to_standard_error(self) -> None:
        """net-snmp merges standard error into the reply pipe, so it is just as dangerous."""
        root = logging.getLogger()
        handler = logging.StreamHandler(sys.stderr)
        root.addHandler(handler)
        try:
            protect_protocol_streams()
            assert handler not in root.handlers
        finally:
            root.removeHandler(handler)

    def test_the_last_resort_discards_instead_of_writing(self) -> None:
        """A `lastResort` of None makes CPython write its own warning to standard error.

        The first attempt at this guard used None. A real `snmpd` then reported
        `Got No handlers could be found for logger ... instead of PONG!`.
        """
        protect_protocol_streams()
        assert isinstance(logging.lastResort, logging.NullHandler)

    def test_a_file_handler_survives(self, tmp_path: Path) -> None:
        """The audit trail must keep working, because only the two streams are unsafe."""
        root = logging.getLogger()
        handler = logging.FileHandler(tmp_path / "audit.log", encoding="utf-8")
        root.addHandler(handler)
        try:
            protect_protocol_streams()
            assert handler in root.handlers
        finally:
            root.removeHandler(handler)
            handler.close()


class TestTheSnmpPathNeedsNoWebFramework:
    """`snmpd` may run on a host whose Python holds no Flask."""

    def test_the_responder_imports_without_flask(self) -> None:
        """An eager import of the web layer once broke the whole SNMP path.

        A real `snmpd` on a container without Flask reported
        `ModuleNotFoundError: No module named 'flask'`, because the package
        `__init__` imported the web layer for every caller.
        """
        program = textwrap.dedent(f"""
            import sys
            sys.path.insert(0, {str(REPO_ROOT)!r})


            class Block:
                def find_module(self, name, path=None):
                    return self if name == "flask" or name.startswith("flask.") else None

                def load_module(self, name):
                    raise ImportError("flask is not installed on this host")


            sys.meta_path.insert(0, Block())
            import src.metrics_gateway.snmp as module

            assert module.SnmpPassPersistResponder is not None
            assert "flask" not in sys.modules
            print("OK")
            """)
        result = subprocess.run(  # The command is this interpreter and a literal program.
            [sys.executable, "-c", program],
            capture_output=True,
            text=True,
            timeout=PROCESS_TIMEOUT_SECONDS,
            check=False,
        )
        assert result.returncode == 0, f"The SNMP path needs Flask: {result.stderr}"
        assert "OK" in result.stdout

    def test_the_web_layer_is_still_reachable(self) -> None:
        """A lazy export must still answer, or the Prometheus path would break."""
        import src.metrics_gateway as package

        assert package.create_app is not None

    def test_an_unknown_name_still_raises(self) -> None:
        """The lazy lookup must not hide an ordinary mistake."""
        import src.metrics_gateway as package

        with pytest.raises(AttributeError):
            _ = package.not_a_real_name
