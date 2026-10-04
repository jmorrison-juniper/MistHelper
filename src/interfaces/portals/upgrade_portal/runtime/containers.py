"""The container runtime seam that starts a dependency the operator left stopped.

Why:
    The portal refuses to work when the document store or the lock store does
    not answer. On a workstation the usual cause is not a broken service. It is
    a container that exists, holds its data, and sits in the `exited` state
    after a restart. The operator then reads a 503 and has to find the container
    name by hand.

    This module reads the state of one named container and starts it. It is the
    only place in the portal that reaches a container runtime, so every guard
    below holds for every caller.

What this module refuses to do:
    It never creates a container, never pulls an image, never creates a volume,
    and never removes anything. It starts a container that already exists and
    does nothing else. A missing container therefore stays missing, and the
    operator reads the compose command in the report instead. Creating a
    container would invent a configuration that no file in this repository
    describes. The portal would then drive a firmware upgrade against a
    store that nobody reviewed.

    It never runs inside a container. A container cannot start its sibling. A
    portal that reached the host runtime socket would hold far more power over
    the host than a firmware tool needs.

Why the name is checked against a pattern:
    Every name reaches a child process argument list. The list form passes no
    shell, so a space or a semicolon in a name cannot become a second command.
    The pattern is the second guard, and it also keeps a typo in a registry
    entry from reaching the runtime as a flag. A name that starts with a hyphen
    would read as an option, so the first character is a letter or a digit.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import logging  # Action logging per Constitution VII.
import re  # Checks that a container name holds safe characters only.
import shutil  # Finds the absolute path of the runtime, so no PATH lookup happens in the child.
import subprocess  # nosec B404  # WHY: the runtime is a command. Every call below passes a list and no shell.
from enum import StrEnum  # A reading and a template read the same state text.

logger = logging.getLogger(__name__)  # One logger for each module keeps the source visible in the log.

# WHY: Podman comes first, because the project documents Podman as the primary
# runtime. Docker follows, because the compose file also runs there.
RUNTIME_NAMES: tuple[str, ...] = ("podman", "docker")

# WHY: A name reaches a child argument list. The first character is a letter or
# a digit, so no name can read as a command option.
CONTAINER_NAME_PATTERN = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9_.-]{0,62}\Z")

STATE_FORMAT = "{{.State.Status}}"  # Both runtimes accept this Go template and print one word.

INSPECT_TIMEOUT_SECONDS = 10  # A reachable runtime answers an inspect in well under one second.
START_TIMEOUT_SECONDS = 60  # A database container needs a few seconds. One minute covers a slow disk.

RUNNING_WORD = "running"  # The one runtime word that means the service is up.


class ContainerState(StrEnum):
    """What the runtime reports about one named container."""

    RUNNING = "running"  # The container is up, so the service should answer.
    STOPPED = "stopped"  # The container exists and holds its data, so the portal may start it.
    MISSING = "missing"  # No container of that name exists, so only the operator can create it.
    UNKNOWN = "unknown"  # No runtime answered, so the portal knows nothing and claims nothing.


def valid_container_name(name: str) -> bool:
    """Report whether a name is safe to pass to the runtime.

    Args:
        name: The container name from the dependency registry.

    Returns:
        True when the name matches the pattern.
    """
    if CONTAINER_NAME_PATTERN.match(name):  # A safe name reaches the child process.
        return True
    logger.error("containers: the name %r is not a usable container name, so the portal skipped it", name)
    return False


def find_runtime() -> str | None:
    """Return the absolute path of the first container runtime on this host.

    Why:
        `shutil.which` returns an absolute path, so the child process runs the
        file this function found and never repeats the PATH search itself.

    Returns:
        The path of the runtime, or None when the host has neither one.
    """
    for name in RUNTIME_NAMES:  # Podman first, because the project documents it first.
        path = shutil.which(name)  # An absolute path, or None when the runtime is absent.
        if path:  # The first runtime found wins, so a host with both uses Podman.
            logger.debug("containers: the runtime %s answers at %s", name, path)
            return path
    logger.info("containers: this host runs neither podman nor docker, so no container can start")
    return None


def _run(runtime: str, arguments: list[str], timeout: int) -> subprocess.CompletedProcess[str] | None:
    """Run one runtime command and return the finished process.

    Why:
        Every call passes a list and never a shell, so no argument can become a
        second command. One helper holds the timeout and the error handling, so
        no caller repeats them.

    Args:
        runtime: The absolute path of the container runtime.
        arguments: The arguments that follow the runtime path.
        timeout: The wait in seconds before the portal gives up.

    Returns:
        The finished process, or None when the command could not run.
    """
    try:  # A missing binary, a dead runtime service, and a slow answer all land here.
        return subprocess.run(  # nosec B603  # WHY: a list with an absolute path, and no shell.
            [runtime, *arguments], capture_output=True, text=True, timeout=timeout, check=False, shell=False
        )
    except (OSError, subprocess.SubprocessError) as error:  # The portal reports the gap, it never raises.
        logger.warning("containers: the command %s %s did not run: %s", runtime, " ".join(arguments), error)
        return None


def read_container_state(name: str, runtime: str) -> ContainerState:
    """Read the state of one named container.

    Args:
        name: The container name from the dependency registry.
        runtime: The absolute path of the container runtime.

    Returns:
        The state the runtime reported.
    """
    if not valid_container_name(name):  # The guard already logged the refusal.
        return ContainerState.UNKNOWN
    logger.debug("containers: reading the state of %s", name)  # Action log before the call.
    finished = _run(runtime, ["inspect", "--format", STATE_FORMAT, name], INSPECT_TIMEOUT_SECONDS)
    if finished is None:  # The helper already logged why the command could not run.
        return ContainerState.UNKNOWN
    if finished.returncode != 0:  # Both runtimes answer non-zero when no container carries that name.
        logger.info("containers: no container is named %s on this host", name)
        return ContainerState.MISSING
    reported = finished.stdout.strip().lower()  # One word, such as `running` or `exited`.
    logger.debug("containers: %s reports the state %s", name, reported)  # Action log after the call.
    return ContainerState.RUNNING if reported == RUNNING_WORD else ContainerState.STOPPED


def start_container(name: str, runtime: str) -> bool:
    """Start one container that already exists.

    Why:
        The caller has already read the state and found the container stopped.
        This function therefore starts it and reports the outcome. It creates
        nothing, so a name that no container carries fails here and stays absent.

    Args:
        name: The container name from the dependency registry.
        runtime: The absolute path of the container runtime.

    Returns:
        True when the runtime reported success.
    """
    if not valid_container_name(name):  # The guard already logged the refusal.
        return False
    logger.info("containers: starting the container %s", name)  # Action log before the call.
    finished = _run(runtime, ["start", name], START_TIMEOUT_SECONDS)
    if finished is None:  # The helper already logged why the command could not run.
        return False
    if finished.returncode != 0:  # The runtime refused, so the operator needs the reason.
        logger.error("containers: the runtime refused to start %s: %s", name, finished.stderr.strip())
        return False
    logger.info("containers: the container %s started", name)  # Action log after the call.
    return True
