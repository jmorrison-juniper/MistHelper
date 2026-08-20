"""Server choice for the upgrade capture portal.

Why:
    The customer asked for Gunicorn, so Gunicorn stays the server for the Linux
    target and for the container. Gunicorn cannot run on Windows at all, because
    `gunicorn.util` imports `fcntl` and Windows ships no such module. A bare
    `import gunicorn` still passes, so the fault stays hidden until a worker
    class loads. A developer on Windows therefore needs a second server, and
    Waitress fills that role.

    This module holds the choice in one place. A launcher and the browser test
    fixture both read it, so both start the same server on the same platform and
    neither one repeats the platform test.
"""

from __future__ import annotations

import importlib
import logging
import sys

logger = logging.getLogger(__name__)

WINDOWS_PLATFORM = "win32"  # `sys.platform` reports this text on every Windows build, 32-bit and 64-bit.

GUNICORN_NAME = "gunicorn"  # The server for the Linux target and for the container.
WAITRESS_NAME = "waitress"  # The Windows stand-in. Pure Python, so it needs no `fcntl`.

# WHY: A bare `import gunicorn` passes on Windows and the fault appears later,
# inside a worker class. The probe loads the worker class instead, so an unusable
# server shows here and not halfway through a test run.
GUNICORN_PROBE = "gunicorn.workers.sync"
WAITRESS_PROBE = "waitress"

HOST_VARIABLE = "CAPTURE_HOST"  # The setting that names the bind address. An operator value always wins.

DEFAULT_HOST = "127.0.0.1"  # Loopback only. A local server never accepts an outside client.

# WHY: A container reaches its portal through a published port. A bind to
# loopback inside a container answers no client at all, so the container needs
# this address. A workstation must never take it. `resolve_host` is the one
# function that may return it.
ALL_INTERFACES_HOST = "0.0.0.0"  # nosec B104  # Container only, because a published port needs it.

WORKER_COUNT = "1"  # One worker keeps the log order and the site lock state simple.
WORKER_TIMEOUT_SECONDS = "30"  # The same budget the container start script gives each worker.
THREAD_COUNT = "4"  # Waitress runs one process, so it needs a thread count instead of a worker count.


def resolve_host(requested: str | None, *, in_container: bool) -> str:
    """Choose the address that the capture portal binds.

    Why:
        This portal writes firmware to production hardware. It asks for a work
        email, but that email holds the site lock and names the operator. It is
        not a password, so the portal refuses nobody. A bind to every address
        therefore offers the upgrade controls to every computer that can reach
        the host, and a workstation on a customer network reaches many. Loopback
        is the safe default for a workstation.

        A container is the opposite case. It reaches its portal through a
        published port, and a bind to loopback inside a container answers no
        client at all. A container therefore takes every address, because the
        container boundary already holds the published port.

        An operator who names an address always wins, because a reverse proxy
        or a laboratory host needs a bind that neither default describes.

    Args:
        requested: The address from `CAPTURE_HOST`, or None when it is unset.
        in_container: True when the portal runs inside a container.

    Returns:
        The address that the server binds.
    """
    named = (requested or "").strip()  # An unset value and a blank value are the same.
    if named:  # The operator named an address, so no default applies.
        logger.info("The setting %s names the bind address %s", HOST_VARIABLE, named)
        return named
    if in_container:  # A published port cannot reach a loopback bind.
        return ALL_INTERFACES_HOST
    logger.info("No %s value is set, so the portal binds loopback only", HOST_VARIABLE)
    return DEFAULT_HOST  # A workstation keeps the upgrade controls on the computer that runs them.


def select_server_name() -> str:
    """Name the WSGI server that this platform can run.

    Why:
        Gunicorn stays the server for every target that can run it, because the
        customer asked for Gunicorn. Windows is the one platform that cannot run
        it, so Windows alone takes the stand-in.

    Returns:
        The module name of the server for this platform.
    """
    if sys.platform == WINDOWS_PLATFORM:  # Windows ships no `fcntl`, which `gunicorn.util` imports.
        return WAITRESS_NAME
    return GUNICORN_NAME  # Every other platform keeps the server the customer asked for.


def server_is_available(name: str) -> bool:
    """Report whether the named server can load on this platform.

    Why:
        A spec lookup would pass for Gunicorn on Windows, because the fault lives
        in the module body and not in the file name. A real import is the only
        honest test.

    Args:
        name: The server module name, `gunicorn` or `waitress`.

    Returns:
        True when the caller can start that server.
    """
    probe = GUNICORN_PROBE if name == GUNICORN_NAME else WAITRESS_PROBE
    try:  # An absent server and an absent `fcntl` both raise ImportError here.
        importlib.import_module(probe)
    except ImportError:  # The server cannot run, so the caller must choose another path.
        logger.debug("The server %s cannot load on this platform", name)
        return False
    return True  # The server loaded, so the caller may start it.


def _gunicorn_arguments(target: str, host: str, port: int) -> list[str]:
    """Build the Gunicorn arguments for the capture portal.

    Why:
        One worker and a 30-second timeout match the container start script, so
        a local run and a container run behave alike.

    Args:
        target: The WSGI target, such as `wsgi_capture:app`.
        host: The bind address.
        port: The listen port.

    Returns:
        The argument strings in the order Gunicorn reads them.
    """
    return [
        "--bind",
        f"{host}:{port}",
        "--timeout",
        WORKER_TIMEOUT_SECONDS,
        "--workers",
        WORKER_COUNT,
        target,
    ]


def _waitress_arguments(target: str, host: str, port: int) -> list[str]:
    """Build the Waitress arguments for the capture portal.

    Why:
        Waitress runs one process and takes a thread count, so it has no worker
        option. Four threads match the `gthread` worker the container starts.

    Args:
        target: The WSGI target, such as `wsgi_capture:app`.
        host: The bind address.
        port: The listen port.

    Returns:
        The argument strings in the order Waitress reads them.
    """
    return [
        f"--listen={host}:{port}",
        f"--threads={THREAD_COUNT}",
        target,
    ]


def build_server_command(target: str, port: int, host: str = DEFAULT_HOST) -> list[str]:
    """Build the command that starts the capture portal on this platform.

    Why:
        The caller runs this command as a child process. The same interpreter
        runs the caller and the server, so the server reads the same packages.

    Args:
        target: The WSGI target, such as `wsgi_capture:app`.
        port: The listen port.
        host: The bind address. The default is loopback only.

    Returns:
        The interpreter, the module flag, the server name, and its arguments.

    Raises:
        RuntimeError: If the server for this platform cannot load.
    """
    name = select_server_name()
    if not server_is_available(name):  # A caller turns this into a skip, because it describes the workstation.
        raise RuntimeError(f"The server {name} cannot load on this platform, so the portal cannot start.")
    logger.info("Start the capture portal with %s on %s port %s", name, host, port)
    if name == WAITRESS_NAME:  # Windows takes the stand-in, which reads a different option set.
        return [sys.executable, "-m", name, *_waitress_arguments(target, host, port)]
    return [sys.executable, "-m", name, *_gunicorn_arguments(target, host, port)]
