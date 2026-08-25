"""Unit tests for the server choice of the upgrade capture portal.

Why:
    ``runtime/server.py`` decides which WSGI server starts the portal. menu 239
    and the browser test fixture both read that decision, so a wrong answer
    stops the portal on a whole platform. The module needs a test, and the test
    must never start a server.

    No test in this file starts a process, binds a port, or reaches the cloud.
    ``build_server_command`` returns a list of strings and runs nothing, so a
    test asserts on that list alone. The tests reach the code through the
    module object, because the functions read ``sys``, ``importlib``, and each
    other at call time, and ``monkeypatch`` must replace those module members.
"""

from __future__ import annotations

import logging
import sys
from types import SimpleNamespace
from typing import Any

import pytest

from src.upgrade_portal.runtime import server

# WHY: The WSGI target the browser fixture passes. A realistic value shows a
# reader where the target sits inside the command.
WSGI_TARGET = "wsgi_capture:app"

# WHY: The listen port of the portal. A test writes this number into a string
# only, so no test binds it.
SAMPLE_PORT = 8056

# WHY: A host that is not the default. It proves that a caller host reaches the
# command in place of the default host. The address belongs to a reserved
# documentation range, so it names no real computer.
OTHER_HOST = "192.0.2.10"

# WHY: The platform names of the targets that run Gunicorn. Cygwin runs on
# Windows hardware and still reports its own name, so it belongs here.
OTHER_PLATFORMS = ("linux", "darwin", "freebsd13", "cygwin")

# WHY: An ImportError message that names a path. A caught fault must never
# reach a log record, and this text makes such a leak visible.
PROBE_FAULT_TEXT = "No module named 'fcntl' at /private/path"


def _set_platform(monkeypatch: pytest.MonkeyPatch, platform: str) -> None:
    """Report one platform name to the module under test.

    Why:
        A test must read the branch of a platform that this computer is not.
        The helper replaces the ``sys`` member of the module alone, so the real
        ``sys.platform`` of the test run stays untouched.

    Args:
        monkeypatch: The pytest patch helper.
        platform: The platform name the module must read.
    """
    stand_in = SimpleNamespace(platform=platform, executable=sys.executable)
    monkeypatch.setattr(server, "sys", stand_in)  # The module member only, never the real `sys`.


def _record_probes(monkeypatch: pytest.MonkeyPatch, fault: ImportError | None = None) -> list[str]:
    """Replace the import probe and record every probed module name.

    Why:
        A real import ties the result to the packages of one computer. A
        recorded stand-in proves which module name the code probes and returns
        the same answer on every platform.

    Args:
        monkeypatch: The pytest patch helper.
        fault: The fault the probe raises, or None when the probe passes.

    Returns:
        The list that collects each probed module name.
    """
    probed: list[str] = []

    def _probe(name: str) -> Any:
        """Record one probe, then raise the fault the test asked for.

        Args:
            name: The module name the code probes.

        Returns:
            A stand-in module object when the test asked for no fault.

        Raises:
            ImportError: When the test asked for a fault.
        """
        probed.append(name)
        if fault is not None:
            raise fault
        return SimpleNamespace(__name__=name)

    monkeypatch.setattr(server, "importlib", SimpleNamespace(import_module=_probe))
    return probed


def _force_server(monkeypatch: pytest.MonkeyPatch, name: str, available: bool = True) -> None:
    """Fix the server choice and the load answer of the module.

    Why:
        ``build_server_command`` reads both seams at call time. A Windows
        computer can never load Gunicorn, so the Gunicorn command needs these
        two stand-ins to stay testable on every platform.

    Args:
        monkeypatch: The pytest patch helper.
        name: The server name that the choice returns.
        available: The answer that the load test returns.
    """
    monkeypatch.setattr(server, "select_server_name", lambda: name)
    monkeypatch.setattr(server, "server_is_available", lambda _name: available)


def test_select_server_name_names_waitress_on_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    """Windows takes the Waitress stand-in.

    Why:
        Gunicorn cannot load on Windows, because `gunicorn.util` imports
        `fcntl`. The test states the platform text and the server name as
        literals, so a typo in either constant fails the test.

    Args:
        monkeypatch: The pytest patch helper.
    """
    _set_platform(monkeypatch, "win32")
    assert server.select_server_name() == "waitress"


@pytest.mark.parametrize("platform", OTHER_PLATFORMS)
def test_select_server_name_names_gunicorn_on_every_other_platform(
    monkeypatch: pytest.MonkeyPatch, platform: str
) -> None:
    """Every platform except Windows keeps Gunicorn.

    Why:
        The customer asked for Gunicorn. Windows is the single exception, so
        each other platform must still name the server the customer chose.

    Args:
        monkeypatch: The pytest patch helper.
        platform: One platform name that is not Windows.
    """
    _set_platform(monkeypatch, platform)
    assert server.select_server_name() == "gunicorn"


def test_server_is_available_probes_the_gunicorn_worker_class(monkeypatch: pytest.MonkeyPatch) -> None:
    """The Gunicorn test imports the worker class, not the package.

    Why:
        A bare `import gunicorn` passes on Windows and the fault appears later,
        inside a worker class. The probe must therefore load the worker class,
        or the module reports an unusable server as usable.

    Args:
        monkeypatch: The pytest patch helper.
    """
    probed = _record_probes(monkeypatch)
    server.server_is_available("gunicorn")
    assert probed == ["gunicorn.workers.sync"]


def test_server_is_available_probes_the_waitress_package(monkeypatch: pytest.MonkeyPatch) -> None:
    """The Waitress test imports the package itself.

    Why:
        Waitress is pure Python and needs no `fcntl`, so the package import
        already proves that the server can run.

    Args:
        monkeypatch: The pytest patch helper.
    """
    probed = _record_probes(monkeypatch)
    server.server_is_available("waitress")
    assert probed == ["waitress"]


def test_server_is_available_reports_true_when_the_probe_loads(monkeypatch: pytest.MonkeyPatch) -> None:
    """A probe that loads reports an available server.

    Why:
        The caller starts the server from this answer. A false negative leaves
        an operator with no portal on a computer that can run one.

    Args:
        monkeypatch: The pytest patch helper.
    """
    _record_probes(monkeypatch)
    assert server.server_is_available("waitress") is True


def test_server_is_available_reports_false_when_the_probe_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """A probe that raises ImportError reports an unavailable server.

    Why:
        An absent package and an absent `fcntl` both raise ImportError. The
        module must answer False rather than raise, because the caller turns
        the answer into a skip or into a clear fault.

    Args:
        monkeypatch: The pytest patch helper.
    """
    _record_probes(monkeypatch, ImportError(PROBE_FAULT_TEXT))
    assert server.server_is_available("gunicorn") is False


def test_server_is_available_logs_the_name_and_never_the_fault_text(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The failure record holds the server name alone.

    Why:
        A fault message can carry a file path or another private value. The
        record must name the server and nothing more, and it must hold the
        value as a lazy `%s` argument.

    Args:
        monkeypatch: The pytest patch helper.
        caplog: The pytest log capture fixture.
    """
    _record_probes(monkeypatch, ImportError(PROBE_FAULT_TEXT))
    with caplog.at_level(logging.DEBUG, logger=server.logger.name):
        server.server_is_available("gunicorn")
    record = caplog.records[-1]
    assert record.args == ("gunicorn",)
    assert PROBE_FAULT_TEXT not in caplog.text


@pytest.mark.skipif(sys.platform != "win32", reason="The test states the Windows result of a real import.")
def test_a_windows_computer_loads_waitress_and_never_gunicorn() -> None:
    """A real import on Windows accepts Waitress and refuses Gunicorn.

    Why:
        This is the premise of the whole module. Every other test replaces the
        probe, so one test must run the real import and prove that the premise
        still holds on the platform it describes. The import loads a module and
        opens no port.
    """
    assert server.server_is_available("waitress") is True
    assert server.server_is_available("gunicorn") is False


def test_build_server_command_builds_the_whole_waitress_command(monkeypatch: pytest.MonkeyPatch) -> None:
    """The Waitress command holds the listen address, the threads, and the target.

    Why:
        Waitress runs one process and reads a thread count, so it accepts no
        worker option. The test compares the whole list, because one wrong or
        missing argument stops the portal.

    Args:
        monkeypatch: The pytest patch helper.
    """
    _force_server(monkeypatch, "waitress")
    command = server.build_server_command(WSGI_TARGET, SAMPLE_PORT, OTHER_HOST)
    assert command == [
        sys.executable,
        "-m",
        "waitress",
        f"--listen={OTHER_HOST}:{SAMPLE_PORT}",
        "--threads=4",
        WSGI_TARGET,
    ]


def test_build_server_command_builds_the_whole_gunicorn_command(monkeypatch: pytest.MonkeyPatch) -> None:
    """The Gunicorn command holds the bind address, the timeout, the workers, and the target.

    Why:
        One worker and a 30-second timeout match the container start script, so
        a local run and a container run behave alike. The test compares the
        whole list, because Gunicorn reads these arguments in order.

    Args:
        monkeypatch: The pytest patch helper.
    """
    _force_server(monkeypatch, "gunicorn")
    command = server.build_server_command(WSGI_TARGET, SAMPLE_PORT, OTHER_HOST)
    assert command == [
        sys.executable,
        "-m",
        "gunicorn",
        "--bind",
        f"{OTHER_HOST}:{SAMPLE_PORT}",
        "--timeout",
        "30",
        "--workers",
        "1",
        WSGI_TARGET,
    ]


@pytest.mark.parametrize("name", ["waitress", "gunicorn"])
def test_build_server_command_binds_loopback_when_the_caller_names_no_host(
    monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    """The default host is loopback for both servers.

    Why:
        A local portal must never accept a client from outside the computer.
        The test reads the default that the code holds today and states it as a
        literal, so a change of that default fails here and reaches a reviewer.

    Args:
        monkeypatch: The pytest patch helper.
        name: The server name the choice returns.
    """
    _force_server(monkeypatch, name)
    command = server.build_server_command(WSGI_TARGET, SAMPLE_PORT)
    assert any(f"127.0.0.1:{SAMPLE_PORT}" in argument for argument in command)


def test_build_server_command_raises_when_the_server_cannot_load(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unusable server raises RuntimeError and builds no command.

    Why:
        The browser fixture turns this fault into a skip, and the skip message
        must name the server. A silent command would start nothing and leave
        the caller with an empty port.

    Args:
        monkeypatch: The pytest patch helper.
    """
    _force_server(monkeypatch, "gunicorn", available=False)
    with pytest.raises(RuntimeError) as failure:
        server.build_server_command(WSGI_TARGET, SAMPLE_PORT)
    assert "gunicorn" in str(failure.value)


def test_build_server_command_logs_the_name_the_host_and_the_port(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """The start record holds three named scalar values.

    Why:
        An operator reads this record to find the address of the portal. The
        record must hold the three values as lazy `%s` arguments, so no whole
        dictionary and no credential can ever reach a log file.

    Args:
        monkeypatch: The pytest patch helper.
        caplog: The pytest log capture fixture.
    """
    _force_server(monkeypatch, "waitress")
    with caplog.at_level(logging.INFO, logger=server.logger.name):
        server.build_server_command(WSGI_TARGET, SAMPLE_PORT, OTHER_HOST)
    record = caplog.records[-1]
    assert record.args == ("waitress", OTHER_HOST, SAMPLE_PORT)
    assert "%s" in record.msg


def test_build_server_command_starts_no_process_and_binds_no_port(monkeypatch: pytest.MonkeyPatch) -> None:
    """The module builds a command and runs nothing.

    Why:
        This seam must stay pure. The caller owns the child process, so the
        module imports no process module and no socket module. A later edit
        that starts the server here fails this test.

    Args:
        monkeypatch: The pytest patch helper.
    """
    _force_server(monkeypatch, "waitress")
    command = server.build_server_command(WSGI_TARGET, SAMPLE_PORT)
    assert all(isinstance(argument, str) for argument in command)
    assert not hasattr(server, "subprocess")
    assert not hasattr(server, "socket")


@pytest.mark.parametrize("in_container", [True, False])
def test_resolve_host_keeps_the_address_the_operator_named(in_container: bool) -> None:
    """A named address wins in a container and on a workstation.

    Why:
        A reverse proxy or a laboratory host needs a bind that neither default
        describes. The operator value must therefore beat both defaults, and
        the container must never overrule it.

    Args:
        in_container: The container answer that the test states.
    """
    assert server.resolve_host(OTHER_HOST, in_container=in_container) == OTHER_HOST


def test_resolve_host_binds_loopback_on_a_workstation() -> None:
    """A workstation with no setting binds loopback only.

    Why:
        This portal writes firmware to production hardware and refuses nobody,
        because the work email holds the site lock and is not a password. The
        test states the address as a literal, so a change of this default fails
        here and reaches a reviewer.
    """
    assert server.resolve_host(None, in_container=False) == "127.0.0.1"


def test_resolve_host_binds_every_address_in_a_container() -> None:
    """A container with no setting binds every address.

    Why:
        A container reaches its portal through a published port, and a
        published port cannot reach a loopback bind. The test states the
        address as a literal, so a change here fails and reaches a reviewer.
    """
    assert server.resolve_host(None, in_container=True) == "0.0.0.0"


@pytest.mark.parametrize("blank", ["", "   ", "\t"])
def test_resolve_host_treats_a_blank_setting_as_no_setting(blank: str) -> None:
    """Blank text falls back to the default of the platform.

    Why:
        An operator who clears the value in a compose file leaves an empty
        string, not an absent one. A bind to empty text would raise at start
        time and leave the operator with no portal.

    Args:
        blank: One text value that holds no address.
    """
    assert server.resolve_host(blank, in_container=False) == server.DEFAULT_HOST
    assert server.resolve_host(blank, in_container=True) == server.ALL_INTERFACES_HOST


def test_resolve_host_never_binds_every_address_on_a_workstation() -> None:
    """No workstation answer returns the container address.

    Why:
        This is the whole point of the function. A workstation that binds every
        address offers the upgrade controls to every computer that can reach
        it. The test reads the unset case and the blank case together, because
        both reach the default branch.
    """
    for value in (None, "", "  "):
        assert server.resolve_host(value, in_container=False) != server.ALL_INTERFACES_HOST


def test_resolve_host_logs_the_setting_name_when_it_falls_back(caplog: pytest.LogCaptureFixture) -> None:
    """The fallback record names the setting as a lazy argument.

    Why:
        An operator who expected a portal on the network needs the name of the
        setting that changes the bind. The record must hold the name as a lazy
        `%s` argument, so no whole dictionary can ever reach a log file.

    Args:
        caplog: The pytest log capture fixture.
    """
    with caplog.at_level(logging.INFO, logger=server.logger.name):
        server.resolve_host(None, in_container=False)
    record = caplog.records[-1]
    assert record.args == ("CAPTURE_HOST",)
    assert "%s" in record.msg


def test_resolve_host_reads_no_environment_of_its_own(monkeypatch: pytest.MonkeyPatch) -> None:
    """The function takes its input from the caller alone.

    Why:
        The launcher owns the environment read, so this seam stays pure and a
        test needs no environment patch. A later edit that reads the
        environment here would make the answer depend on the computer.

    Args:
        monkeypatch: The pytest patch helper.
    """
    monkeypatch.setenv("CAPTURE_HOST", OTHER_HOST)
    assert server.resolve_host(None, in_container=False) == server.DEFAULT_HOST
    assert not hasattr(server, "os")
