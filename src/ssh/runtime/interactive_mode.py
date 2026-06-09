"""Interactive REPL mode for the SSH runner (T013d).

Decomposed from EnhancedSSHRunner._interactive_mode (was CC=C). Each prompt
helper has CC <= 10. Real call, not a façade.
"""

from __future__ import annotations

import getpass  # Standard-library secure password prompt
import logging  # Action logging for every interactive step

from src.ssh.command.command_runner import SingleCommandRunner  # Real single-command executor (no façade)
from src.ssh.config.validators import (  # Shared input validators
    validate_command,
    validate_hostname,
    validate_username,
)
from src.ssh.connection.connector import SshConnector  # Exposes _validate_port classmethod


class InteractiveMode:
    """Run the SSH runner in interactive REPL mode with input validation."""

    @staticmethod
    def _prompt_hostname() -> str:
        """Loop until the user enters a syntactically valid hostname/IP."""
        logging.info("Prompting user for SSH hostname")  # Before-action log
        while True:  # Validation loop
            hostname = input("- Enter hostname or IP address: ").strip()  # Read raw input
            if not hostname:  # Empty -> reprompt
                print("X  Hostname is required")
                continue
            if not validate_hostname(hostname):  # Reject invalid syntax
                print("X  Invalid hostname or IP address format")
                continue
            logging.debug("Hostname accepted: %s", hostname)  # After-action log
            return hostname

    @staticmethod
    def _prompt_username() -> str:
        """Loop until the user enters a syntactically valid username."""
        logging.info("Prompting user for SSH username")  # Before-action log
        while True:  # Validation loop
            username = input("X  Enter username: ").strip()  # Read raw input
            if not username:  # Empty -> reprompt
                print("X  Username is required")
                continue
            if not validate_username(username):  # Reject invalid chars
                print("X  Invalid username format (alphanumeric, underscore, hyphen, dot only)")
                continue
            logging.debug("Username accepted: %s", username)  # After-action log
            return username

    @staticmethod
    def _prompt_password() -> str:
        """Prompt securely for the SSH password (no validation loop)."""
        logging.info("Prompting user for SSH password (hidden input)")  # Before-action log
        password = getpass.getpass("!? Enter password: ")  # Hidden input via getpass
        logging.debug("Password received (length=%d)", len(password))  # After-action log w/o secret
        return password

    @staticmethod
    def _prompt_port() -> int:
        """Prompt for SSH port number with validation, default 22."""
        logging.info("Prompting user for SSH port")  # Before-action log
        while True:  # Validation loop
            try:  # Catch non-numeric input
                port_input = input(">> Enter SSH port (default 22): ").strip()
                if not port_input:  # Default port path
                    logging.debug("Port defaulted to 22")
                    return 22
                port = int(port_input)  # Parse user-provided integer
                if not SshConnector._validate_port(port):  # Range check 1..65535
                    print("X  Port must be between 1 and 65535")
                    continue
                logging.debug("Port accepted: %d", port)  # After-action log
                return port
            except ValueError:  # Non-numeric input
                print("X  Port must be a valid number")

    @staticmethod
    def _prompt_timeout() -> int:
        """Prompt for connection timeout with validation, default 30."""
        logging.info("Prompting user for SSH timeout")  # Before-action log
        while True:  # Validation loop
            try:  # Catch non-numeric input
                timeout_input = input("- Enter timeout in seconds (default 30): ").strip()
                if not timeout_input:  # Default timeout path
                    logging.debug("Timeout defaulted to 30")
                    return 30
                timeout = int(timeout_input)  # Parse user-provided integer
                if not (isinstance(timeout, int) and 1 <= timeout <= 3600):  # Bounded
                    print("X  Timeout must be between 1 and 3600 seconds")
                    continue
                logging.debug("Timeout accepted: %d", timeout)  # After-action log
                return timeout
            except ValueError:  # Non-numeric input
                print("X  Timeout must be a valid number")

    @staticmethod
    def _prompt_shell_mode() -> bool:
        """Prompt whether to use interactive shell mode (y/N)."""
        logging.info("Prompting user for shell-mode preference")  # Before-action log
        shell_mode = (
            input("X  Use interactive shell mode? (y/N - recommended for network devices): ").strip().lower()
        )  # Read raw input
        use_shell = shell_mode in ["y", "yes", "true", "1"]  # Treat affirmative answers as true
        logging.debug("Shell mode selected: %s", use_shell)  # After-action log
        return use_shell

    @staticmethod
    def _prompt_command() -> str:
        """Loop until the user enters a syntactically valid command."""
        logging.info("Prompting user for command to execute")  # Before-action log
        while True:  # Validation loop
            command = input("!? Enter command to execute: ").strip()  # Read raw input
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
        return SingleCommandRunner.run(hostname, username, password, command, port, timeout, use_shell)
