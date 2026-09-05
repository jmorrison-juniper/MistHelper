"""The dependency preflight that the sign-in page shows to the operator.

Why:
    The portal used to start, report "ready for the port 8056", and serve the
    sign-in form while the document store answered nothing. The operator learned
    of the gap only after signing in and picking a site, because
    `acquire_site_lock` fails closed and answers 503. The failure appeared three
    pages after its cause.

    This module probes every service the portal needs and returns one report
    that the sign-in page renders. The operator therefore reads the state, and
    the remedy, on the first page and before choosing a site.

What the probe tests:
    Each probe opens a TCP connection and closes it. That answers one question:
    does a service listen on that address. It is deliberately not an
    authenticated probe, because the sign-in page must render fast and must
    render before the portal holds any credential.

    A deeper reading already exists. `GET /readyz` writes to both stores and
    therefore also catches a store that listens, refuses the password, or
    refuses a write. The banner names that route, so an operator who needs the
    deeper answer knows where it lives.

Why auto-start sits behind a switch:
    Starting a container is a change to the host. A firmware tool should not
    change a host by surprise. `CAPTURE_AUTOSTART` holds the choice. The default
    is on for a workstation, because that is the case this feature repairs. The
    action also reaches no further than a container that already exists.
"""

from __future__ import annotations  # Postponed annotations keep every hint a plain string.

import logging  # Action logging per Constitution VII.
import os  # Reads the auto-start switch by name.
import socket  # The reachability probe opens one TCP connection.
from dataclasses import dataclass  # Builds the frozen registry and reading records.
from enum import StrEnum  # A reading and a template read the same state text.
from urllib.parse import urlsplit  # Splits the ArangoDB URL into a host and a port.

from ..app.config import ArangoSettings, RedisSettings
from .containers import ContainerState, find_runtime, read_container_state, start_container

logger = logging.getLogger(__name__)  # One logger for each module keeps the source visible in the log.

AUTOSTART_VARIABLE = "CAPTURE_AUTOSTART"  # Names the switch that allows a container start.
FALSE_WORDS = ("0", "false", "no", "off")  # Every spelling of "do not start a container".

PROBE_TIMEOUT_SECONDS = 2.0  # A local service answers at once. Two seconds keeps a dead host off the page.

DOCUMENT_STORE_KEY = "document_store"  # The registry key of the capture and run store.
LOCK_STORE_KEY = "lock_store"  # The registry key of the site lock store.

DEFAULT_ARANGO_PORT = 9529  # The project port. Not 8529, which every other project also publishes.

READINESS_ROUTE = "/readyz"  # The deeper, authenticated reading that this preflight does not repeat.


class DependencyState(StrEnum):
    """What the portal knows about one dependency after the preflight."""

    UP = "up"  # The service answered, so the portal can use it.
    STARTED = "started"  # The service was down, the portal started its container, and it answered.
    DOWN = "down"  # The service did not answer, and the portal could not repair it.


@dataclass(frozen=True, slots=True)
class Dependency:
    """One service the portal needs, and the container that carries it.

    Attributes:
        key: The stable name the page and a test read.
        label: The operator-facing name of the service.
        container: The container name that carries the service.
        host: The host that the probe reaches.
        port: The port that the probe reaches.
    """

    key: str  # The stable name, never shown to the operator.
    label: str  # The name the operator reads on the page.
    container: str  # The container the portal may start when the service is down.
    host: str  # The address of the service.
    port: int  # The port of the service.


@dataclass(frozen=True, slots=True)
class DependencyReading:
    """The state of one dependency and the sentence the operator reads.

    Attributes:
        dependency: The service this reading describes.
        state: What the portal found.
        detail: The sentence the page shows. It names the next action.
    """

    dependency: Dependency  # The service this reading describes.
    state: DependencyState  # What the portal found after the probe and any start.
    detail: str  # The operator-facing sentence, which never holds a credential.

    @property
    def healthy(self) -> bool:
        """Report whether this dependency is usable now.

        Returns:
            True when the service answered, whether or not the portal started it.
        """
        return self.state in (DependencyState.UP, DependencyState.STARTED)


@dataclass(frozen=True, slots=True)
class PreflightReport:
    """Every dependency reading, and one summary the page reads.

    Attributes:
        readings: One reading for each dependency, in registry order.
    """

    readings: tuple[DependencyReading, ...]  # One reading for each dependency.

    @property
    def healthy(self) -> bool:
        """Report whether every dependency answered.

        Returns:
            True when no reading is down.
        """
        return all(reading.healthy for reading in self.readings)

    @property
    def failures(self) -> tuple[DependencyReading, ...]:
        """Return the readings the operator has to repair.

        Returns:
            Every reading that is down, in registry order.
        """
        return tuple(reading for reading in self.readings if not reading.healthy)


def autostart_allowed() -> bool:
    """Report whether the portal may start a stopped container.

    Why:
        The default is on, because a stopped container is the fault this feature
        repairs. An operator who wants no change to the host sets the variable
        to a false word.

    Returns:
        True when the portal may start a container.
    """
    raw = os.environ.get(AUTOSTART_VARIABLE, "").strip().lower()  # An unset value takes the default.
    if raw in FALSE_WORDS:  # The operator turned the behavior off on purpose.
        logger.info("preflight: %s is off, so the portal starts no container", AUTOSTART_VARIABLE)
        return False
    return True


def split_arango_address(host_url: str) -> tuple[str, int]:
    """Split the ArangoDB URL into a host name and a port.

    Why:
        The settings record holds a full URL, because the driver needs one. The
        probe opens a socket, so it needs the two parts separately.

    Args:
        host_url: The URL from the settings record.

    Returns:
        The host name and the port. A URL with no port takes the ArangoDB port.
    """
    parts = urlsplit(host_url if "//" in host_url else f"//{host_url}")  # A bare host still splits.
    name = parts.hostname or host_url  # A URL the parser cannot read falls back to the raw value.
    port = parts.port or DEFAULT_ARANGO_PORT  # A URL with no port means the standard port.
    logger.debug("preflight: the store URL %s reads as host %s port %s", host_url, name, port)
    return name, port


def build_registry(arango: ArangoSettings, redis: RedisSettings) -> tuple[Dependency, ...]:
    """Name every service the portal needs, with the address the settings give.

    Why:
        The registry reads the same settings that the portal itself uses. The
        probe can therefore never test a different address from the one the
        portal calls.

    Args:
        arango: The document store settings.
        redis: The lock store settings.

    Returns:
        One entry for each dependency, in the order the page shows them.
    """
    store_host, store_port = split_arango_address(arango.host)  # The URL splits into two probe values.
    return (
        Dependency(
            key=DOCUMENT_STORE_KEY,
            label="Document store (ArangoDB)",
            container="misthelper-arangodb",
            host=store_host,
            port=store_port,
        ),
        Dependency(
            key=LOCK_STORE_KEY,
            label="Site lock store (Redis)",
            container="misthelper-redis",
            host=redis.host,
            port=redis.port,
        ),
    )


def service_answers(host: str, port: int) -> bool:
    """Report whether a service listens on one address.

    Why:
        The probe carries a timeout, so a host that drops packets cannot hold
        the sign-in page open.

    Args:
        host: The host name or the address.
        port: The port.

    Returns:
        True when a TCP connection opened.
    """
    try:  # A refused connection, an unknown name, and a silent host all land here.
        with socket.create_connection((host, port), timeout=PROBE_TIMEOUT_SECONDS):
            return True  # The socket opened, so a service listens.
    except OSError as error:  # The portal reports the gap, it never raises into the page.
        logger.debug("preflight: nothing answered at %s port %s: %s", host, port, error)
        return False


def _down_reading(dependency: Dependency, detail: str) -> DependencyReading:
    """Build the reading of a dependency the portal could not repair.

    Args:
        dependency: The service that did not answer.
        detail: The sentence that names the next action.

    Returns:
        The reading.
    """
    logger.warning("preflight: %s is down at %s port %s", dependency.label, dependency.host, dependency.port)
    return DependencyReading(dependency=dependency, state=DependencyState.DOWN, detail=detail)


def _repair(dependency: Dependency) -> DependencyReading:
    """Try to start the container of a dependency that did not answer.

    Why:
        A stopped container is the common case on a workstation, and it is the
        one case the portal can repair on its own.

    Args:
        dependency: The service that did not answer.

    Returns:
        The reading after the repair attempt.
    """
    runtime = find_runtime()  # None when the host runs no container runtime.
    if runtime is None:  # Nothing to start with, so the operator starts the service.
        return _down_reading(dependency, f"Start the service on {dependency.host} port {dependency.port}.")
    state = read_container_state(dependency.container, runtime)  # Missing, stopped, running, or unknown.
    if state is not ContainerState.STOPPED:  # Only a stopped container is safe to start.
        return _down_reading(dependency, _missing_container_detail(dependency, state))
    if not start_container(dependency.container, runtime):  # The runtime already logged the reason.
        return _down_reading(dependency, f"The container {dependency.container} refused to start. Read the log.")
    if not service_answers(dependency.host, dependency.port):  # Started, but still not listening yet.
        return _down_reading(dependency, f"The container {dependency.container} started but answers no client yet.")
    logger.info("preflight: the portal started %s and %s now answers", dependency.container, dependency.label)
    return DependencyReading(
        dependency=dependency,
        state=DependencyState.STARTED,
        detail=f"The portal started the container {dependency.container}.",
    )


def _missing_container_detail(dependency: Dependency, state: ContainerState) -> str:
    """Build the sentence for a dependency whose container the portal cannot start.

    Args:
        dependency: The service that did not answer.
        state: What the runtime reported about its container.

    Returns:
        The sentence that names the next action.
    """
    if state is ContainerState.MISSING:  # No container exists, so the operator creates one.
        return f"No container is named {dependency.container}. Run: podman compose up -d {dependency.container}"
    if state is ContainerState.RUNNING:  # The container runs, so the fault is inside it or on the port.
        return f"The container {dependency.container} runs but answers no client. Read its log."
    return f"The portal could not read the state of {dependency.container}."  # No runtime answered.


def check_dependency(dependency: Dependency, *, allow_start: bool) -> DependencyReading:
    """Probe one dependency, and repair it when the caller allows a start.

    Args:
        dependency: The service to probe.
        allow_start: True when the portal may start a stopped container.

    Returns:
        The reading of that dependency.
    """
    logger.debug("preflight: probing %s at %s port %s", dependency.label, dependency.host, dependency.port)
    if service_answers(dependency.host, dependency.port):  # The common path, and the fastest one.
        return DependencyReading(dependency=dependency, state=DependencyState.UP, detail="The service answers.")
    if not allow_start:  # The operator turned auto-start off, so the portal only reports.
        return _down_reading(dependency, f"Start the container {dependency.container}.")
    return _repair(dependency)  # The one case the portal can repair on its own.


def run_preflight(arango: ArangoSettings, redis: RedisSettings, *, allow_start: bool | None = None) -> PreflightReport:
    """Probe every dependency and return the report the sign-in page reads.

    Why:
        One entry point keeps the page, the launcher, and the tests on the same
        path. The operator and a test therefore never read a different answer.

    Args:
        arango: The document store settings.
        redis: The lock store settings.
        allow_start: True to start a stopped container, False to report only.
            None reads the `CAPTURE_AUTOSTART` switch.

    Returns:
        One reading for each dependency.
    """
    permitted = autostart_allowed() if allow_start is None else allow_start  # The caller wins over the switch.
    logger.info("preflight: checking the portal dependencies, container start allowed=%s", permitted)
    readings = tuple(
        check_dependency(dependency, allow_start=permitted) for dependency in build_registry(arango, redis)
    )
    report = PreflightReport(readings=readings)  # One record holds every reading.
    logger.info("preflight: %d of %d dependencies answer", len(readings) - len(report.failures), len(readings))
    return report


def reading_rows(report: PreflightReport) -> list[dict[str, str]]:
    """Flatten the report into the rows the template renders.

    Why:
        A template reads a plain mapping far more simply than a nested record.
        The flat form also keeps the markup free of any settings object.

    Args:
        report: The report that `run_preflight` returned.

    Returns:
        One row for each reading, in registry order.
    """
    return [
        {
            "key": reading.dependency.key,
            "label": reading.dependency.label,
            "address": f"{reading.dependency.host}:{reading.dependency.port}",
            "state": reading.state.value,
            "detail": reading.detail,
        }
        for reading in report.readings
    ]
