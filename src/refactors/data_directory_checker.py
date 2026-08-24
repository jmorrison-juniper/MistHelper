"""DataDirectoryChecker extracted from MistHelper.

Validates that the data directory used by MistHelper for logs and persisted
data is writable by the current process, providing actionable guidance
(local versus container remediation) when the check fails.

This module runs *very* early during MistHelper module initialization —
before the logging subsystem has been fully configured — so operator-visible
output is emitted through the stdlib ``logging`` module (per issue #886).
Emissions still reach the console via the root logger's default handler
even before MistHelper installs its own handlers, and they are captured
into the log file once logging comes online. Structured INFO/DEBUG traces
record the check outcome for later triage.

The class is otherwise self-contained: it depends only on the stdlib
(``os``, ``sys``) and no MistHelper globals, so it does not need the
late-import DI dance the other extracted modules use.
"""

from __future__ import annotations  # Enable postponed evaluation for forward-ref typing on 3.10+

import logging  # Structured action logging required by coding standards
import os  # File-system operations (path join, exists, remove) used by the writable check
import sys  # sys.exit() to abort early when the directory is not writable

logger = logging.getLogger(__name__)  # WHY: module-scoped logger for #886 print-to-logger migration.


class DataDirectoryChecker:
    """Check data directory write permissions and provide actionable guidance.

    This class runs very early during module initialization (before MistHelper's
    logging handlers are installed), so operator-facing output is routed through
    the stdlib ``logging`` root logger rather than raw ``print()`` calls (#886).

    Usage:
        DataDirectoryChecker(_early_log_dir).check()
    """

    def __init__(self, data_dir: str) -> None:  # Initialize checker with target data directory path
        """Initialize with the data directory path to check."""
        logging.info("DataDirectoryChecker init: target data_dir=%s", data_dir)  # Log construction start
        self.data_dir = data_dir  # Store the data directory path for later validation
        self.test_file = os.path.join(
            data_dir, ".write_test"
        )  # Define test file path (.write_test) for permission validation
        logging.debug("DataDirectoryChecker init complete: test_file=%s", self.test_file)  # Log after init

    def check(self) -> bool:  # Check if data directory is writable and handle errors
        """Check if data directory is writable.

        Returns:
            True if writable, exits program if not writable due to permissions.
        """
        logging.info("DataDirectoryChecker.check: validating write access to %s", self.data_dir)  # Pre-check log
        try:  # Attempt to validate write permission
            result = self._test_write_permission()  # Call permission test helper method
            logging.debug("DataDirectoryChecker.check: write permission ok (result=%s)", result)  # Post-check log
            return result  # Return success signal to caller
        except PermissionError:  # Catch permission errors and display actionable guidance
            self._handle_permission_error()  # Call error handler to print guidance and exit
            return False  # Never reached - _handle_permission_error exits
        except Exception:  # For non-permission errors, proceed and let them fail naturally later
            logging.debug("DataDirectoryChecker.check: non-permission exception - deferring failure")  # Log defer
            return True  # Non-permission error, let it proceed and fail naturally

    def _test_write_permission(self) -> bool:  # Validate data directory write access via test file
        """Create and remove a test file to verify write access."""
        with open(
            self.test_file, "w", encoding="utf-8"
        ) as file_handle:  # Open test file for writing (will fail if directory not writable)
            file_handle.write("test")  # Write marker content to test file
        os.remove(self.test_file)  # Delete test file to clean up
        return True  # Return success if both write and delete succeeded

    def _handle_permission_error(self) -> None:  # Display context-specific guidance and exit
        """Print error message with context-specific guidance and exit."""
        logging.error("DataDirectoryChecker: data directory %s is not writable", self.data_dir)  # Log fail
        in_container = self._is_running_in_container()  # Detect if running in container to show appropriate fix

        self._print_error_header()  # Print error banner with path information

        if in_container:  # If running in container, show container-specific fix (chmod on host)
            self._print_container_guidance()  # Print container deployment remediation steps
        else:  # If running locally, show local fix (chmod/chown)
            self._print_local_guidance()  # Print local environment remediation steps

        self._print_error_footer()  # Print closing separator
        sys.exit(1)  # Exit program with error code to prevent further execution

    def _is_running_in_container(self) -> bool:  # Detect container environment
        """Detect if running inside a container environment."""
        return os.path.exists("/.dockerenv") or os.path.exists(
            "/run/.containerenv"
        )  # Check for standard container marker files

    def _print_error_header(self) -> None:  # Display error banner with path
        """Print the error header with path information."""
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.error("\n%s", "=" * 70)  # Print separator to visually isolate error message
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.error("ERROR: Data directory is not writable!")  # Print main error message
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.error("%s", "=" * 70)  # Print closing separator
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.error("\nPath: %s", os.path.abspath(self.data_dir))  # Print absolute path
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.error("\nMistHelper cannot write logs or data to the data/ directory.")  # Explain impact

    def _print_container_guidance(self) -> None:  # Display container-specific remediation
        """Print guidance specific to container deployments."""
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("\n[CONTAINER DETECTED]")  # Indicate container environment detected
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info(
            "The container runs as non-root user 'misthelper' for security."
        )  # Explain why permissions are restricted
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("The mounted data/ directory must have write permissions.")  # State the requirement
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("\nTo fix this, run the following on your HOST machine:")  # Provide context for the fix
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("\n    chmod -R 777 data/")  # Show command to grant write permissions
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("\nThen restart the container:")  # Explain next step
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("    podman stop misthelper && podman rm misthelper")  # Show stop and remove command
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info(
            "    podman run -d --name misthelper -p 2200:2200 -p 8050:8050 \\"
        )  # Show container restart with port mapping
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info(
            '        -v "${PWD}/data:/app/data:rw" -v "${PWD}/.env:/app/.env:ro" \\'
        )  # Show volume mount with correct permissions
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("        ghcr.io/jmorrison-juniper/misthelper:latest")  # Show container image URI

    def _print_local_guidance(self) -> None:  # Display local environment remediation
        """Print guidance for local (non-container) environments."""
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("\nTo fix this, ensure the data/ directory is writable:")  # Provide context for local fix
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("\n    chmod -R 755 data/")  # Show command to set directory permissions
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("    # Or if you own the directory:")  # Provide alternative if ownership is an issue
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.info("    chown -R $(whoami) data/")  # Show command to change ownership to current user

    def _print_error_footer(self) -> None:  # Display error footer separator
        """Print the closing separator line."""
        # WHY: preserve operator notice verbatim. Route through logger for capture/redirection.
        logger.error("\n%s", "=" * 70)  # Print separator line to visually isolate error message
