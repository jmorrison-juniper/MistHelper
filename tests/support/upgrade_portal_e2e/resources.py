"""Allocate unique process resources for one E2E portal server."""

from __future__ import annotations  # Keep annotations independent from import order.

import logging  # Record resource allocation without exposing credentials.
import socket  # Ask the operating system for an unused loopback port.
from dataclasses import dataclass  # Group the five paths and identifiers.
from pathlib import Path  # Build Windows-compatible artifact paths.
from uuid import uuid4  # Create one unpredictable test run identifier.

logger = logging.getLogger(__name__)  # Keep allocation records tied to this module.


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
    reservation = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Reserve one TCP loopback endpoint.
    reservation.bind(("127.0.0.1", 0))  # Ask the operating system for an unused port.
    port = int(reservation.getsockname()[1])  # Pass the exact reserved port to the child.
    log_path = artifact_directory / "server.log"  # Keep one log inside this server artifact directory.
    owner_path = artifact_directory / "server.pid"  # Keep one process owner record beside the log.
    resources = E2EResources(  # Join the allocated values and the live reservation.
        test_run_id, port, artifact_directory, log_path, owner_path, reservation
    )
    logger.debug("Allocated E2E server resources for port %s", port)  # Report no credential or record data.
    return resources  # The caller owns cleanup after the server stops.
