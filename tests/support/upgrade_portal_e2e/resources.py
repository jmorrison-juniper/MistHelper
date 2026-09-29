"""Allocate unique process resources for one E2E portal server."""

from __future__ import annotations  # Keep annotations independent from import order.

import logging  # Record resource allocation without exposing credentials.
import os  # Read the optional fixed port list for local journey checks.
import socket  # Ask the operating system for an unused loopback port.
from dataclasses import dataclass  # Group the five paths and identifiers.
from pathlib import Path  # Build Windows-compatible artifact paths.
from uuid import uuid4  # Create one unpredictable test run identifier.

logger = logging.getLogger(__name__)  # Keep allocation records tied to this module.
PORT_LIST_VARIABLE = "UPGRADE_PORTAL_E2E_PORTS"  # Let a local harness run stay in an approved port range.


@dataclass(slots=True)
class E2EResources:  # Hold one unique resource set for one E2E server.
    """Hold the unique resources of one E2E server process."""

    test_run_id: str  # Identify records and response headers for this server.
    port: int  # Bind the child server to one unique loopback port.
    artifact_directory: Path  # Hold only artifacts from this server.
    log_path: Path  # Receive the child server log without a blocking pipe.
    process_owner_path: Path  # Name the child process for safe stale-process cleanup.
    _reservation: socket.socket  # Keep the port reserved until the child starts.

    def release_port(self) -> None:  # Hand the reserved port to the child process.
        """Release the port reservation immediately before child process start."""
        logger.info("Release the E2E server port reservation")  # Record the handoff to the child.
        self._reservation.close()  # Let the child bind the exact allocated port.
        logger.debug("Released the E2E server port reservation")  # Confirm the local handoff.


def allocate_resources(root: Path) -> E2EResources:  # Allocate one collision-resistant server resource set.
    """Allocate one unique identifier, port, artifact directory, log, and owner file."""
    logger.info("Allocate resources for one E2E portal server")  # Record the allocation before it starts.
    test_run_id = f"e2e-{uuid4().hex}"  # Give every server and record graph a unique owner.
    artifact_directory = root / test_run_id  # Keep all artifacts below the caller-approved root.
    artifact_directory.mkdir(parents=True, exist_ok=False)  # Refuse a reused artifact path.
    reservation = reserve_loopback_port()  # Use a requested local port range when the runner sets one.
    port = int(reservation.getsockname()[1])  # Pass the exact reserved port to the child.
    log_path = artifact_directory / "server.log"  # Keep one log inside this server artifact directory.
    owner_path = artifact_directory / "server.pid"  # Keep one process owner record beside the log.
    resources = E2EResources(  # Join the allocated values and the live reservation.
        test_run_id, port, artifact_directory, log_path, owner_path, reservation
    )
    logger.debug("Allocated E2E server resources for port %s", port)  # Report no credential or record data.
    return resources  # The caller owns cleanup after the server stops.


def reserve_loopback_port() -> socket.socket:
    """Reserve one loopback port from the optional list, or from the system."""
    requested = os.environ.get(PORT_LIST_VARIABLE, "")  # Empty means the default operating system choice.
    if requested:  # A local harness can set an approved bounded port list.
        return reserve_requested_port(requested)  # Keep the harness inside the caller-approved ports.
    reservation = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Reserve one TCP loopback endpoint.
    reservation.bind(("127.0.0.1", 0))  # Ask the operating system for an unused port.
    return reservation  # The caller owns the reserved socket.


def reserve_requested_port(requested: str) -> socket.socket:
    """Reserve the first available loopback port from a comma-separated list."""
    logger.info("Reserve E2E server port from %s", PORT_LIST_VARIABLE)  # Record the bounded allocation mode.
    failures: list[str] = []  # Keep one readable reason for each refused port.
    for value in requested.split(","):  # Try the caller-approved ports in order.
        port = int(value.strip())  # Fail early when the input is not a port number.
        reservation = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Build a reservation for this port.
        try:  # Another journey process can reserve the same list concurrently.
            reservation.bind(("127.0.0.1", port))  # Keep the child inside the approved loopback range.
            logger.debug("Reserved requested E2E server port %s", port)  # Confirm the bounded port.
            return reservation  # Keep the successful reservation open.
        except OSError as error:  # Try the next approved port before failing the run.
            reservation.close()  # Release the failed socket handle immediately.
            failures.append(f"{port}: {error}")  # Keep the refusal for the final error.
    raise RuntimeError(f"No requested E2E port was available: {', '.join(failures)}")  # Fail with every reason.
