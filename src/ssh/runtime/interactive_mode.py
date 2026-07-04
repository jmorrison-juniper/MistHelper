"""Interactive REPL mode for the SSH runner (T013d).

Decomposed from EnhancedSSHRunner._interactive_mode (was CC=C). Each prompt
helper has CC <= 10. Real call, not a façade.
"""

from __future__ import annotations  # PEP 563: postpone annotation evaluation for forward refs.

import getpass  # Standard-library secure password prompt
import logging  # Action logging for every interactive step

from src.ssh.command.command_runner import (  # Real single-command executor (no façade)
    SingleCommandRequest,
    SingleCommandRunner,
)
from src.ssh.config.validators import (  # Shared input validators
    validate_command,
    validate_hostname,
    validate_username,
)
from src.ssh.connection.connector import SshConnector  # Exposes _validate_port classmethod
from src.utils.input_utils import InputUtils  # EOF-safe input wrapper (issue #452: replace raw input()).


class InteractiveMode:  # Groups the interactive REPL prompt helpers under one namespace.
    """Run the SSH runner in interactive REPL mode with input validation."""

    @staticmethod
    def _prompt_hostname() -> str:  # Public prompt entry-point for the hostname phase.
        """Loop until the user enters a syntactically valid hostname/IP."""
        logging.info("Prompting user for SSH hostname")  # Before-action log
        while True:  # Validation loop
            hostname = InputUtils.safe_input(
                "- Enter hostname or IP address: ", context="ssh_hostname"
            )  # EOF-safe read.
            if not hostname:  # Empty -> reprompt
                print("X  Hostname is required")  # User-facing required-field message.
                continue  # Re-enter the validation loop.
            if not validate_hostname(hostname):  # Reject invalid syntax
                print("X  Invalid hostname or IP address format")  # User-facing format error.
                continue  # Re-enter the validation loop.
            logging.debug("Hostname accepted: %s", hostname)  # After-action log
            return hostname  # Hand the validated hostname back to the caller.

    @staticmethod
    def _prompt_username() -> str:  # Public prompt entry-point for the username phase.
        """Loop until the user enters a syntactically valid username."""
        logging.info("Prompting user for SSH username")  # Before-action log
        while True:  # Validation loop
            username = InputUtils.safe_input("X  Enter username: ", context="ssh_username")  # EOF-safe read.
            if not username:  # Empty -> reprompt
                print("X  Username is required")  # User-facing required-field message.
                continue  # Re-enter the validation loop.
            if not validate_username(username):  # Reject invalid chars
                print("X  Invalid username format (alphanumeric, underscore, hyphen, dot only)")  # Format error.
                continue  # Re-enter the validation loop.
            logging.debug("Username accepted: %s", username)  # After-action log
            return username  # Hand the validated username back to the caller.

    @staticmethod
    def _prompt_password() -> str:  # Public prompt entry-point for the password phase.
        """Prompt securely for the SSH password (no validation loop)."""
        logging.info("Prompting user for SSH password (hidden input)")  # Before-action log
        password = getpass.getpass("!? Enter password: ")  # Hidden input via getpass
        logging.debug("Password received (length=%d)", len(password))  # After-action log w/o secret
        return password  # Hand the raw password back to the caller.

    @staticmethod
    def _prompt_port() -> int:  # Public prompt entry-point for the port phase.
        """Prompt for SSH port number with validation, default 22."""
        logging.info("Prompting user for SSH port")  # Before-action log
        while True:  # Validation loop
            try:  # Catch non-numeric input
                port_input = InputUtils.safe_input(
                    ">> Enter SSH port (default 22): ", context="ssh_port"
                )  # EOF-safe read.
                if not port_input:  # Default port path
                    logging.debug("Port defaulted to 22")  # Trace default-branch decision.
                    return 22  # Return the documented default port.
                port = int(port_input)  # Parse user-provided integer
                if not SshConnector._validate_port(port):  # Range check 1..65535
                    print("X  Port must be between 1 and 65535")  # User-facing range-error message.
                    continue  # Re-enter the validation loop.
                logging.debug("Port accepted: %d", port)  # After-action log
                return port  # Hand the validated port back to the caller.
            except ValueError:  # Non-numeric input
                print("X  Port must be a valid number")  # User-facing parse-error message.

    @staticmethod
    def _prompt_timeout() -> int:
        """Prompt for connection timeout with validation, default 30."""
        logging.info("Prompting user for SSH timeout")  # Before-action log
        while True:  # Validation loop
            timeout = InteractiveMode._read_bounded_timeout()  # Delegate parse+range check to helper.
            if timeout is not None:  # Helper returned an accepted value.
                logging.debug("Timeout accepted: %d", timeout)  # After-action log
                return timeout  # Hand the validated timeout back to the caller.

    @staticmethod
    def _read_bounded_timeout() -> int | None:
        """Read one timeout entry; return validated int, or None to re-prompt."""
        # WHY: extracting parse/validate drops _prompt_timeout CC from 6 to 3.
        try:  # Catch non-numeric input from the user.
            timeout_input = InputUtils.safe_input(
                "- Enter timeout in seconds (default 30): ", context="ssh_timeout"
            )  # EOF-safe read.
        except ValueError:  # Defensive; safe_input can raise on non-str contexts.
            print("X  Timeout must be a valid number")  # User-facing parse-error message.
            return None  # Signal caller to re-prompt.
        if not timeout_input:  # Empty entry selects the default timeout.
            logging.debug("Timeout defaulted to 30")  # Trace default-branch decision.
            return 30  # Return the documented default.
        try:  # int() raises ValueError on non-numeric strings.
            timeout = int(timeout_input)  # Parse user-provided integer.
        except ValueError:  # Non-numeric input entered.
            print("X  Timeout must be a valid number")  # User-facing parse-error message.
            return None  # Signal caller to re-prompt.
        if not 1 <= timeout <= 3600:  # Bounded range check.
            print("X  Timeout must be between 1 and 3600 seconds")  # User-facing range-error message.
            return None  # Signal caller to re-prompt.
        return timeout  # Validated, in-range timeout value.

    @staticmethod
    def _prompt_shell_mode() -> bool:
        """Prompt whether to use interactive shell mode (y/N)."""
        logging.info("Prompting user for shell-mode preference")  # Before-action log
        shell_mode = InputUtils.safe_input(
            "X  Use interactive shell mode? (y/N - recommended for network devices): ",
            context="ssh_shell_mode",
        ).lower()  # EOF-safe read, lowercased for affirmative comparison.
        use_shell = shell_mode in ["y", "yes", "true", "1"]  # Treat affirmative answers as true
        logging.debug("Shell mode selected: %s", use_shell)  # After-action log
        return use_shell

    @staticmethod
    def _prompt_command() -> str:
        """Loop until the user enters a syntactically valid command."""
        logging.info("Prompting user for command to execute")  # Before-action log
        while True:  # Validation loop
            command = InputUtils.safe_input("!? Enter command to execute: ", context="ssh_command")  # EOF-safe read.
            if not command:  # Empty -> reprompt
                print("X  Command is required")
                continue
            if not validate_command(command):  # Reject too-long or NUL bytes
                print("X  Invalid command (too long or contains null bytes)")
                continue
            logging.debug("Command accepted (length=%d)", len(command))  # After-action log
            return command

    @staticmethod
    def run() -> bool:
        """Orchestrate the interactive REPL and dispatch a single SSH command."""
        logging.info("Entering SSH runner interactive mode")  # Before-action log
        print("- Enhanced SSH Command Runner v2 - Interactive Mode")  # Banner (verbatim preserved)
        print("=" * 60)  # Banner separator (verbatim preserved)
        hostname = InteractiveMode._prompt_hostname()  # Phase 1: hostname
        username = InteractiveMode._prompt_username()  # Phase 2: username
        password = InteractiveMode._prompt_password()  # Phase 3: password
        if not password:  # Reject empty passwords explicitly
            print("X  Password is required")
            logging.debug("Interactive mode aborted: empty password")
            return False
        port = InteractiveMode._prompt_port()  # Phase 4: port
        timeout = InteractiveMode._prompt_timeout()  # Phase 5: timeout
        use_shell = InteractiveMode._prompt_shell_mode()  # Phase 6: shell mode
        command = InteractiveMode._prompt_command()  # Phase 7: command
        print(f"\n>> Starting SSH session (shell_mode={use_shell})...")  # Status line (verbatim preserved)
        logging.debug("Dispatching interactive SSH command to SingleCommandRunner.run")  # After-action log
        interactive_request = SingleCommandRequest(  # WHY: dataclass keeps SingleCommandRunner.run at 1 param.
            hostname=hostname,
            username=username,
            password=password,
            command=command,
            port=port,
            timeout=timeout,
            use_shell=use_shell,
        )
        return SingleCommandRunner.run(interactive_request)
