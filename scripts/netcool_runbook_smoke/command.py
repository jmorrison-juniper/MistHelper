"""Logging, env file, and run report helpers of the command line entry point of the read-only smoke test.

Why: the entry point keeps the run order, and these helpers keep the logging setup, the env file rule, and the printed
report. Each helper sits here, so the entry point holds the order of the run and nothing else.
"""

from __future__ import annotations  # Postpone annotation evaluation, so the classes can name each other.

import logging  # Route the standard library records to stderr and silence the SDK logger.
import sys  # Write the structured log lines to standard error.
from collections.abc import Callable  # Type the scrub rule that the run report receives.
from dataclasses import dataclass, field  # Declare the helpers and the log setup state.
from pathlib import Path  # Build the env file path with the path library.
from typing import Any, ClassVar  # Type the processors and the class constants.

import structlog  # Configure the structured logger and its processors.
from dotenv import dotenv_values  # Read the env file without changing the process environment.
from structlog.typing import EventDict  # Type the event dictionary that each processor receives.

from scripts.netcool_runbook_smoke.checks import (  # Load the result, context, and stop types of the report.
    CheckContext,
    CheckResult,
    EvidenceBuilder,
    StopRun,
)
from scripts.netcool_runbook_smoke.documents import EvidenceRedactor  # Load the redactor that the log scrub shares.

logger = structlog.get_logger(__name__)  # Module logger, so each env file event names this module.


class TracebackFreeFormatter(logging.Formatter):  # Drop raw tracebacks, since the scrub did not cover them.
    """Write each record as its message only, so a traceback is never appended after the scrub.

    Why: the standard library appends the traceback of any record that carries exc_info. That text was not scrubbed,
    and it can hold the masked token of a 401 response. The structured processors already render and scrub each
    traceback inside the message, so the formatter drops the raw exception information.
    """

    def format(self, record: logging.LogRecord) -> str:  # Return the rendered message, with no appended traceback.
        """Return the rendered message of the record, without any appended traceback.

        Why: the message already holds the scrubbed key-value line, so nothing else is added to it.

        Args:
            record: Log record that the structured chain has rendered.

        Returns:
            The message text of the record.
        """
        record.exc_info = None  # Stop the base class from appending an unscrubbed traceback.
        record.exc_text = None  # Remove any cached traceback text as well.
        return record.getMessage()  # The rendered line is the whole output.


class StandardLogging:  # Apply the standard library handler and levels of this package.
    """Set the handler and the levels of the standard library loggers.

    Why: the SDK logger must write nowhere, because its messages can hold a masked token. The package loggers write
    each info and debug event to stderr, and third-party loggers stay at warning.
    """

    HANDLER_NAME: ClassVar[str] = "netcool-runbook-smoke"  # Name of the handler, so a second setup replaces it.
    PACKAGE_LOGGERS: ClassVar[tuple[str, ...]] = ("__main__", "scripts.netcool_runbook_smoke")  # Package loggers.

    def apply(self) -> None:  # Set the standard loggers, so the SDK writes no output.
        """Silence the SDK logger, install the stream handler, and set the level of each logger.

        Why: the root handler is replaced before the levels are set, so each record reaches exactly one handler.
        """
        self._silence_sdk()  # Discard the SDK records before any other handler is set.
        self._install_handler()  # Replace the stream handler, so a second setup does not duplicate lines.
        logging.getLogger().setLevel(logging.WARNING)  # Third-party records stay quiet unless they are warnings.
        for name in self.PACKAGE_LOGGERS:  # Each logger of this package.
            logging.getLogger(name).setLevel(logging.DEBUG)  # Every info and debug event of the package is written.

    def _silence_sdk(self) -> None:  # Keep the SDK logger silent, since its text can hold a masked token.
        """Discard the records of the SDK logger, so no SDK text reaches an output.

        Why: the SDK writes a masked token on an HTTP 401 response, so its records must not propagate.
        """
        sdk_logger = logging.getLogger("mistapi")  # The logger of the SDK.
        sdk_logger.handlers = [logging.NullHandler()]  # Discard each SDK record, so no SDK text is printed.
        sdk_logger.propagate = False  # Keep the SDK records away from the root handler.
        sdk_logger.setLevel(logging.WARNING)  # The contract level of the SDK logger.

    def _install_handler(self) -> None:  # Attach one stream handler, so each line is written once.
        """Attach the structured stream handler to the root logger, and replace an earlier one of this package.

        Why: a second configuration of the same process would otherwise print each line twice.
        """
        root = logging.getLogger()  # The root logger receives the records of the package loggers.
        root.handlers = [item for item in root.handlers if item.get_name() != self.HANDLER_NAME]  # Drop old handler.
        root.addHandler(self._stream_handler())  # Attach the handler to the root logger.

    def _stream_handler(self) -> logging.Handler:  # Build the handler that writes each line to standard error.
        """Return a stream handler on standard error, with the plain formatter and this package's name.

        Why: the name lets a later setup find and replace this handler, and the plain formatter appends no traceback.

        Returns:
            A stream handler that writes the structured lines to standard error.
        """
        stream = logging.StreamHandler(sys.stderr)  # The structured lines go to standard error.
        stream.set_name(self.HANDLER_NAME)  # Name the handler, so a second setup replaces it.
        stream.setFormatter(TracebackFreeFormatter())  # The plain formatter appends no traceback to the line.
        return stream  # The configured handler, ready to attach.


@dataclass
class LogSetup:  # Set up the logs and the scrub rules, shared by all output.
    """Configure the structured logs, silence the SDK logger, and scrub each log line and each console line.

    Why: the token and its masked form must never reach stdout, stderr, or the evidence. The SDK writes a masked token
    on HTTP 401, so its logger is silenced, and each event is scrubbed before it is rendered.
    """

    NO_VALUE: ClassVar[str] = ""  # Empty text for a redactor that holds no identifier and no token.
    secrets: list[str] = field(  # Token values and their masked forms, which no output may show.
        default_factory=list, repr=False
    )
    redactor: EvidenceRedactor = field(  # Hold a redactor with no identifiers until the run sets one.
        default_factory=lambda: EvidenceRedactor(
            organization_id=LogSetup.NO_VALUE, site_ids=(), token_value=LogSetup.NO_VALUE
        )
    )  # Identifier and contact rules of the evidence, which the logs share.

    def protect(self, value: str) -> None:  # Register one token, so each output can scrub it.
        """Add one token value and its masked form to the scrub list.

        Why: the SDK prints the first four and the last four characters of a long token.
        The masked form is therefore also removed from each output.
        A short token has no masked form in the SDK.

        Args:
            value: Token value that the lookup found. An empty value is ignored.
        """
        if not value:  # An empty value would match everywhere, so it is never added.
            return  # Nothing to protect.
        self.secrets.append(value)  # The token value itself.
        if len(value) > 16:  # The SDK masks only the tokens that are longer than 16 characters.
            self.secrets.append(f"{value[:4]}...{value[-4:]}")  # The masked form the SDK can print.

    def configure(self) -> None:  # Apply the logging chain before any step can log.
        """Route the structured logs to stderr, silence the SDK logger, and set the processor chain.

        Why: the processor chain formats the %s values, removes the traceback text into a string, scrubs each value,
        and writes one key-value line. The processors run in this order on each event.
        """
        StandardLogging().apply()  # Stream handler and levels of the standard library loggers.
        structlog.configure(  # Set processors, so each event is scrubbed before rendering.
            processors=[  # Each processor runs once for each event, in this order.
                structlog.stdlib.add_log_level,  # Adds the level name to the event.
                structlog.stdlib.PositionalArgumentsFormatter(),  # Applies the %s values to the message template.
                structlog.processors.TimeStamper(fmt="iso", utc=True),  # Adds the UTC ISO 8601 time of the event.
                structlog.processors.format_exc_info,  # Turns each traceback into text, so the scrub covers it.
                self._scrub_event,  # Scrubs each string value of the event.
                structlog.processors.KeyValueRenderer(key_order=["timestamp", "level", "event"]),  # One line per event.
            ],
            wrapper_class=structlog.stdlib.BoundLogger,  # Keeps the positional arguments of each call.
            logger_factory=structlog.stdlib.LoggerFactory(),  # Sends each event to its standard library logger.
            cache_logger_on_first_use=False,  # A later configuration must replace this one.
        )

    def scrub_text(self, text: str) -> str:  # Replace secrets and identifiers, so no output shows them.
        """Return the text with each secret, identifier, and contact value replaced, in ASCII only.

        Why: the console lines and the log lines share one scrub rule, so a secret can appear in neither.

        Args:
            text: Text to scrub.

        Returns:
            The scrubbed text, which holds ASCII characters only.
        """
        result = text  # The text that the replacements change.
        for secret in sorted(set(self.secrets), key=len, reverse=True):  # Longest first, so a masked form is not split.
            result = result.replace(secret, "[redacted]")  # Replace each occurrence of the secret.
        result = str(self.redactor.scrub(result))  # UUID, MAC, e-mail, and token-like runs, as the evidence rules say.
        return result.encode("ascii", "replace").decode(  # Keep ASCII only, since some consoles fail on other text.
            "ascii"
        )  # Replace each non-ASCII character with a question mark.

    def _scrub_event(  # Scrub each event, so the renderer receives no secret.
        self, _logger: Any, _method_name: str, event: EventDict
    ) -> EventDict:
        """Scrub each string value of one structured event.

        Why: a processor receives every event before it is rendered, so one rule covers each key and value.

        Args:
            _logger: Logger that emitted the event. Unused.
            _method_name: Level method that emitted the event. Unused.
            event: Event dictionary, which this method changes in place.

        Returns:
            The same event dictionary, with each string scrubbed.
        """
        for key in list(event):  # Each key of the event, copied so the dictionary can change.
            value = event[key]  # The value of this key.
            if isinstance(value, str):  # Only text can hold a secret or an identifier.
                event[key] = self.scrub_text(value)  # Replace the scrubbed text.
        return event  # The scrubbed event goes on to the renderer.


@dataclass
class EnvFileReader:  # Read the env file of the operator, after its location passes the rule.
    """Read the env file for the names of section 2, when the operator gave one.

    Why: an env file inside the repository can be committed by mistake, so only the root .env file may sit inside.
    Any other env file must be outside the repository. The rule sits in one class, so the settings loader only orders
    the steps of the run.
    """

    root: Path  # Repository root, which the location rule compares against.

    def read(self, value: str | None) -> dict[str, str | None]:  # Return the env values, or none when not given.
        """Return the values of the env file, or an empty dictionary when no env file was given.

        Why: only the names of section 2 are read from the mapping, and the process environment is never changed.

        Args:
            value: Value of --env-file, or None when it was not given.

        Returns:
            The values of the env file, or an empty dictionary when no env file was given.

        Raises:
            StopRun: The env file is inside the repository but is not the root .env, or it does not exist (exit code 2).
        """
        if value is None:  # No env file was given, so the process environment is the only source.
            return {}  # Nothing to read.
        resolved = self._resolve(value)  # Resolve the env path, so a dot-dot segment cannot hide it.
        self._check_location(resolved)  # Refuse a file in the repository, and a file that does not exist.
        return self._values(resolved)  # The values of the checked env file.

    def _values(self, resolved: Path) -> dict[str, str | None]:  # Read the values of a checked env file.
        """Read the values of one checked env file, with an info event before and a debug event after.

        Why: the read is an external action, so the operator sees when the file is read.
        The log gives the number of values, and the values themselves never reach a log.

        Args:
            resolved: Resolved path of an env file that passed the location rule.

        Returns:
            The values of the env file.
        """
        logger.info("Reading the env file for the section 2 names")  # Announce the file read before it starts.
        values = dict(dotenv_values(resolved))  # Only the section 2 names are read from this mapping.
        logger.debug("Read %s values from the env file", len(values))  # Record the count, never a value.
        return values  # The values of the env file.

    def _resolve(self, value: str) -> Path:  # Resolve the typed path against the repository root.
        """Return the absolute path of the typed env file, with each dot-dot segment resolved.

        Why: the location rule compares the resolved path, so a relative value and a dot-dot segment are both handled.

        Args:
            value: Value of --env-file as the operator typed it.

        Returns:
            The resolved absolute path.
        """
        candidate = Path(value)  # The value as the operator typed it.
        return (candidate if candidate.is_absolute() else self.root / candidate).resolve()  # Resolve the ".." first.

    def _check_location(self, resolved: Path) -> None:  # Refuse a file in the repository, or a missing file.
        """Raise the configuration error when the env file is in the repository or does not exist.

        Why: a secret file in the repository can be committed, and a missing file would give an empty configuration.

        Args:
            resolved: Resolved path of the env file.

        Raises:
            StopRun: The file is inside the repository but is not the root .env, or it does not exist (exit code 2).
        """
        inside = resolved.is_relative_to(self.root.resolve())  # True when the file is in the repository.
        if inside and resolved != (self.root / ".env").resolve():  # Only the root .env may sit inside the repository.
            raise StopRun(  # Stop the run, so no secret file enters the repository.
                StopRun.Outcome.CONFIGURATION_ERROR, "the env file must be outside the repository or be .env"
            )
        if not resolved.is_file():  # A missing env file gives exit code 2, before any value is read.
            raise StopRun(  # Stop the run before any value is read from a missing file.
                StopRun.Outcome.CONFIGURATION_ERROR, "the env file does not exist"
            )


@dataclass
class RunReport:  # Print the summary lines of one run, in contract order.
    """Print the check lines, the summary, the outcome, the evidence, and the cause of one run.

    Why: the console lines follow the contract order. The scrub rule applies to the check and cause lines, so the report
    receives the scrub function, not the whole log setup.
    """

    context: CheckContext | None  # Run state, or None when the settings did not load.
    results: list[CheckResult]  # Check results, in check order.
    outcome: StopRun.Outcome  # Final outcome class of the run.
    evidence_line: str  # Evidence line of the contract.
    cause_line: str  # Cause of the run, or an empty text when none exists.
    scrub: Callable[[str], str]  # Scrub rule of the run, which removes each secret and identifier.

    def print_lines(self) -> None:  # Print each line of the contract, in order.
        """Print one line for each check, then the summary, the outcome, the evidence, and the cause.

        Why: the contract fixes the order of the lines, so every outcome prints the same sequence.
        """
        for result in self.results:  # One line for each check, in check order.
            line = f"{result.check_id} {result.status.value} {result.title}: {result.detail}"  # Contract form.
            print(self.scrub(line))  # Print the scrubbed line.
        print(CheckResult.summary_line(self.results, self._requests_sent(), self._budget()))  # The summary line.
        print(f"Outcome: {self.outcome.label} (exit code {self.outcome.exit_code}).")  # The outcome line.
        print(self.evidence_line)  # The evidence line of the contract.
        if self.cause_line:  # The cause follows the required lines, so their order stays the contract order.
            print(self.scrub(f"Cause: {self.cause_line}."))  # The scrubbed cause.

    def _requests_sent(self) -> int:  # Count the requests that the run sent.
        """Return the requests that the run counted, or zero when no run state exists.

        Why: a configuration error sends no request, so the summary shows zero when no run state exists.

        Returns:
            The request count of the run.
        """
        return self.context.requests_used() if self.context is not None else 0  # Zero when no run state exists.

    def _budget(self) -> int:  # Read the request budget, or the default when no run state exists.
        """Return the request budget of the run, or the default budget when no run state exists.

        Why: the summary always shows a budget, even when the settings did not load.

        Returns:
            The request budget of the run.
        """
        if self.context is None:  # No run state, so the default budget applies.
            return EvidenceBuilder.DEFAULT_BUDGET  # The default budget of the contract.
        return self.context.settings.max_requests  # The budget of the run.
