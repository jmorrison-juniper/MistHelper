"""Command line entry point of the read-only smoke test of the NOC runbook.

Why: one command reads the options, the environment, and the env file in one fixed order.
The command then runs the checks in order, prints one summary for every outcome, and writes the evidence record.
The checks never read the environment or print a line themselves, so the operator sees one consistent output.
"""

from __future__ import annotations  # Postpone annotation evaluation, so the classes can name each other.

import argparse  # Parse the options of the command line.
import contextlib  # Keep argparse text out of stderr while it rejects an option.
import io  # Hold the discarded argparse text in memory.
import os  # Read the process environment, which is the default source of the command.
import re  # Check the UUID form of the organization and the site identifiers.
import sys  # Write the console lines and the structured logs to the standard streams.
from collections.abc import Mapping, Sequence  # Type the environment and the command line arguments.
from dataclasses import dataclass, field  # Declare the settings, the loader, and the command state.
from datetime import UTC, datetime  # Compute the default evidence name and the collection window in UTC.
from pathlib import Path  # Build every path with the path library.
from typing import Any, ClassVar  # Type the session factory, the processors, and the class constants.

import mistapi  # The Mist SDK. The command builds the API session with its class after SMK-01 passes.
import structlog  # Configure the module logger, so each event names this module.

from scripts.netcool_runbook_smoke.checks import (  # Load the check types, so each check reports one shape.
    CheckContext,
    CheckResult,
    CheckStatus,
    EvidenceBuilder,
    StopRun,
)
from scripts.netcool_runbook_smoke.checks.catalogs import CatalogChecks  # Load the catalog checks, which SMK-05 runs.
from scripts.netcool_runbook_smoke.checks.identity import (  # Load the identity checks, which run SMK-01 to SMK-04.
    IdentityChecks,
)
from scripts.netcool_runbook_smoke.checks.scope import (  # Load the scope and inventory checks for SMK-08 to SMK-10.
    InventoryChecks,
    ScopeChecks,
)
from scripts.netcool_runbook_smoke.checks.searches import (  # Load the search checks, which run SMK-06 and SMK-07.
    SearchChecks,
)
from scripts.netcool_runbook_smoke.command import (  # Load the logging and report helpers.
    EnvFileReader,
    LogSetup,
    RunReport,
)
from scripts.netcool_runbook_smoke.documents import EvidenceWriter  # Load the evidence writer for the default path.

logger = structlog.get_logger(__name__)  # Module logger, so each event names this module.


@dataclass(frozen=True)
class SmokeSettings:  # Hold the checked options, so the checks never reparse them.
    """Validated options of one smoke run, with no token value.

    Why: the checks read one object whose options already passed their rules, so no check repeats a rule. The
    token is not a field, because the contract keeps each token value out of the settings.
    """

    UUID_PATTERN: ClassVar[re.Pattern[str]] = re.compile(  # Match a UUID, so each identifier has one accepted form.
        r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
    )  # The 8-4-4-4-12 form of a UUID, with hexadecimal digits in either case.

    host: str  # Regional host, a bare host name from the OpenAPI servers list.
    org_id: str  # Organization identifier in lower case.
    site_id: str | None  # Site identifier in lower case, or None when SMK-08 reads the first site.
    runbook_path: Path  # Runbook file under the repository root.
    runbook_explicit: bool  # True when the operator gave --runbook.
    openapi_path: Path  # OpenAPI file under the repository root.
    window_minutes: int  # Length of the collection window.
    delay_minutes: int  # End lag of the collection window.
    max_pages: int  # Page ceiling of each paged query.
    max_requests: int  # Request budget of the run.
    max_retries: int  # Retries for HTTP 5xx responses and connection failures.
    call_timeout_seconds: int  # Longest wait for one SDK call.
    output_path: Path  # Evidence file under test-artifacts.
    env_file_given: bool  # True when the operator gave --env-file.
    root: Path  # Repository root, so each path is written relative to it.

    OPTION_SPECS: ClassVar[tuple[tuple[str, dict[str, Any]], ...]] = (  # Options of the contract, in help order.
        ("--env-file", {"default": None, "help": "env file outside the repository, read for section 2 names"}),
        ("--org-id", {"default": None, "help": "organization identifier, a UUID"}),
        ("--site-id", {"default": None, "help": "site identifier for SMK-08, a UUID"}),
        ("--runbook", {"default": None, "help": "runbook path under the repository root"}),
        ("--openapi", {"default": None, "help": "OpenAPI path under the repository root"}),
        ("--window-minutes", {"type": int, "default": 60, "help": "collection window length in minutes"}),
        ("--delay-minutes", {"type": int, "default": 2, "help": "collection window end lag in minutes"}),
        ("--max-pages", {"type": int, "default": 3, "help": "page ceiling of each paged query"}),
        ("--max-requests", {"type": int, "default": 60, "help": "request budget of the run"}),
        ("--max-retries", {"type": int, "default": 2, "help": "retries for HTTP 5xx and connection failures"}),
        ("--call-timeout", {"type": int, "default": 30, "help": "seconds to wait for each SDK call"}),
        ("--output", {"default": None, "help": "evidence file under test-artifacts"}),
    )  # Each row is one option name with its argparse keyword arguments.

    @staticmethod
    def option_parser() -> argparse.ArgumentParser:  # Define the options once, so help and parsing match.
        """Return the parser of the command line options of the contract.

        Why: the options are defined in one place, so the help text and the parsing cannot drift apart.

        Returns:
            The argument parser with each option of the contract.
        """
        parser = argparse.ArgumentParser(  # Name the module call, so help shows the right command.
            prog="python -m scripts.netcool_runbook_smoke", description="Read-only smoke test."
        )
        for flag, keyword_arguments in SmokeSettings.OPTION_SPECS:  # Register each option in contract order.
            parser.add_argument(flag, **keyword_arguments)  # Apply the default, type, and help of the option.
        return parser  # Return the parser, so the loader reads the same options.

    @classmethod
    def uuid_text(cls, value: str, name: str) -> str:  # Validate each UUID, so paths and comparisons use one form.
        """Return the identifier in lower case when it has the UUID form, or raise the configuration error.

        Why: each identifier is used in a path and in a comparison, so one form is kept for both.

        Args:
            value: Identifier text from an option or from the environment.
            name: Name of the identifier in the message, for example organization ID.

        Returns:
            The identifier in lower case.

        Raises:
            StopRun: The value is missing or is not a UUID (exit code 2).
        """
        if cls.UUID_PATTERN.fullmatch(value) is None:  # Only the 8-4-4-4-12 form is an identifier.
            raise StopRun(  # Stop the run when the ID is not a UUID, before any request.
                StopRun.Outcome.CONFIGURATION_ERROR, f"the {name} is missing or is not a UUID"
            )
        return value.lower()  # Paths and comparisons use the lower-case form.

    @staticmethod
    def token_from(candidates: Sequence[str]) -> str:  # Pick the one token, so two names cannot give two values.
        """Return the one token value of the token variables, or raise the configuration error.

        Why: the two token names may both be set, but only one value is allowed. A value with a comma is a list that the
        SDK would split and rotate, so the run refuses it before the first request.

        Args:
            candidates: Values of the token variables, in lookup order. An empty value means that the variable is unset.

        Returns:
            The one token value.

        Raises:
            StopRun: No value, two different values, or a value with a comma (exit code 2).
        """
        values = {value for value in candidates if value}  # The distinct token values that were found.
        token = SmokeSettings._one_value(values)  # The one value, or the configuration error.
        if "," in token:  # The SDK splits a comma list, so one token value cannot hold a comma.
            raise StopRun(  # Stop the run, since the SDK would split a comma list.
                StopRun.Outcome.CONFIGURATION_ERROR, "the token value holds a comma"
            )
        return token  # The token value, which no output may show.

    @staticmethod
    def _one_value(values: set[str]) -> str:  # Refuse no value and two values, so one token identity is used.
        """Return the one token value of the distinct values, or raise the configuration error.

        Why: the two token names may both be set, but only one value is allowed. Two values would let one run use two
        token identities, so the run stops before the first request.

        Args:
            values: Distinct non-empty token values that the lookup found.

        Returns:
            The one token value.

        Raises:
            StopRun: No value, or two different values (exit code 2).
        """
        if not values:  # No token variable has a value.
            raise StopRun(  # Stop the run, since every API call needs a token value.
                StopRun.Outcome.CONFIGURATION_ERROR, "no token variable has a value"
            )
        if len(values) > 1:  # Two variables with different values are a conflict.
            raise StopRun(  # Stop the run, so one run uses one token identity.
                StopRun.Outcome.CONFIGURATION_ERROR, "MIST_API_TOKEN and MIST_APITOKEN have different values"
            )
        return values.pop()  # The one token value of the run.

    @staticmethod
    def check_ranges(args: argparse.Namespace) -> None:  # Refuse each number outside its contract range.
        """Raise the configuration error for each number that is outside its contract range.

        Why: three inputs give an empty or reversed run.
        These inputs are a count below its minimum and a retry count above the contract cap.
        A third input is a lag that does not end before the window.
        The run stops before the first request instead.

        Args:
            args: Parsed options of the run.

        Raises:
            StopRun: An option is below its minimum, or the retry or lag rule fails (exit code 2).
        """
        minimums = (  # Each option with its smallest accepted value.
            ("--window-minutes", args.window_minutes, 1),
            ("--delay-minutes", args.delay_minutes, 0),
            ("--max-pages", args.max_pages, 1),
            ("--max-requests", args.max_requests, 1),
            ("--call-timeout", args.call_timeout, 1),
            ("--max-retries", args.max_retries, 0),
        )
        for name, value, minimum in minimums:  # Check each option in turn.
            if value < minimum:  # The value is below its range.
                raise StopRun(  # Stop the run, since a count below its minimum cannot work.
                    StopRun.Outcome.CONFIGURATION_ERROR, f"{name} must be {minimum} or more"
                )
        if args.max_retries > 2:  # The contract allows at most two retries.
            raise StopRun(  # Stop the run, since the contract caps retries at two.
                StopRun.Outcome.CONFIGURATION_ERROR, "--max-retries must be from 0 to 2"
            )
        if args.delay_minutes >= args.window_minutes:  # The lag must end before the window starts.
            raise StopRun(  # Stop the run, since the window would be empty or reversed.
                StopRun.Outcome.CONFIGURATION_ERROR, "--delay-minutes must be less than --window-minutes"
            )


@dataclass
class SettingsLoader:  # Load settings in contract order, and hold the token value.
    """Read the options, the env file, and the environment, and return the validated settings.

    Why: the source order and the path rules of the contract decide each value. A rule that fails stops the run
    before the first request, so no request ever uses a value that the contract refused.
    """

    RUNBOOK_DEFAULT: ClassVar[str] = "documentation/noc-runbooks/MIST_NETCOOL_ALARM_INTEGRATION.md"  # Default runbook.
    OPENAPI_DEFAULT: ClassVar[str] = "documentation/mist-api-openapi31json.json"  # Default OpenAPI file.

    root: Path  # Repository root, which the path rules compare against.
    environment: Mapping[str, str] = field(  # Process environment, which wins over the env file for each name.
        repr=False
    )
    token: str = field(  # Token value after the lookup. It is never written to the settings or to a log.
        default="", repr=False
    )
    secrets: list[str] = field(  # Every token value that the lookup found, for the scrub list.
        default_factory=list, repr=False
    )
    output_path: Path | None = None  # Evidence path, kept so the evidence can be written after a configuration error.

    def load(self, argv: Sequence[str]) -> SmokeSettings:  # Check every input before any request is sent.
        """Read the options, the env file, and the environment, and return the validated settings.

        Why: the output path is resolved first, so a later configuration error can still write the evidence record.

        Args:
            argv: Command line arguments, without the program name.

        Returns:
            The validated settings. The token stays on this loader.

        Raises:
            StopRun: An option, a path, the env file, or an identifier breaks its rule (exit code 2).
        """
        args = self._options(argv)  # Parse the options and check each range.
        output_path, runbook_path, openapi_path = self._resolve_paths(args)  # The three paths, in contract order.
        host, org_id, site_id = self._identity(args)  # Env file, token, host, organization, and site rules.
        return SmokeSettings(  # Return the checked values, frozen so no check edits them.
            host=host,  # Regional host, lower case.
            org_id=org_id,  # Organization identifier, lower case.
            site_id=site_id,  # Site identifier, or None.
            runbook_path=runbook_path,  # Runbook path under the repository root.
            runbook_explicit=args.runbook is not None,  # True when --runbook was given.
            openapi_path=openapi_path,  # OpenAPI path under the repository root.
            window_minutes=args.window_minutes,  # Collection window length.
            delay_minutes=args.delay_minutes,  # Collection window end lag.
            max_pages=args.max_pages,  # Page ceiling of each query.
            max_requests=args.max_requests,  # Request budget of the run.
            max_retries=args.max_retries,  # Retries for server errors.
            call_timeout_seconds=args.call_timeout,  # Longest wait for one SDK call.
            output_path=output_path,  # Evidence path, which is inside test-artifacts.
            env_file_given=args.env_file is not None,  # True when --env-file was given.
            root=self.root,  # Repository root.
        )

    def _options(  # Parse options quietly, since argparse echoes typed values.
        self, argv: Sequence[str]
    ) -> argparse.Namespace:
        """Parse the command line and check each numeric option.

        Why: argparse prints its own error text, which can echo a value that the operator typed. The text is captured
        and dropped, and the run reports a fixed message, so no typed value reaches the console.

        Args:
            argv: Command line arguments, without the program name.

        Returns:
            The parsed options, with each number in its range.

        Raises:
            StopRun: An option is not valid, or a number is out of its range (exit code 2).
            SystemExit: The help option was given, which ends the command with status 0.
        """
        sink = io.StringIO()  # Captures the argparse text, which is then discarded.
        try:  # argparse exits with status 2 for a rejected option, and with status 0 for help.
            with contextlib.redirect_stderr(sink):  # Keep the usage text and the rejected value off stderr.
                args = SmokeSettings.option_parser().parse_args(list(argv))  # Parse the arguments.
        except SystemExit as request:  # argparse ended the parse.
            if request.code == 0:  # The help option ends the command, and its text stays on stdout.
                raise  # Let the help exit stand.
            raise StopRun(  # Stop the run with a fixed message, so no typed value shows.
                StopRun.Outcome.CONFIGURATION_ERROR, "an option is not valid"
            ) from None
        SmokeSettings.check_ranges(args)  # Check each number against its range before the run uses it.
        return args  # Return the checked options, so the loader reads each one.

    def _resolve_paths(self, args: argparse.Namespace) -> tuple[Path, Path, Path]:  # The output, runbook, and OpenAPI.
        """Resolve the output, runbook, and OpenAPI paths, in the contract order.

        Why: the output path is set first, so a later path error still leaves the evidence path for the record.

        Args:
            args: Parsed options of the run.

        Returns:
            The output, runbook, and OpenAPI paths.

        Raises:
            StopRun: A path leaves its allowed folder (exit code 2).
        """
        output_path = self._path(  # Resolve the output first, so a later error can still write evidence.
            args.output,
            EvidenceWriter.default_path(self.root, datetime.now(UTC)),
            self.root / "test-artifacts",
            "--output",
        )
        self.output_path = output_path  # Keep the evidence path, which a later configuration error still needs.
        runbook_path = self._path(args.runbook, self.root / self.RUNBOOK_DEFAULT, self.root, "--runbook")  # Runbook.
        openapi_path = self._path(args.openapi, self.root / self.OPENAPI_DEFAULT, self.root, "--openapi")  # OpenAPI.
        return output_path, runbook_path, openapi_path  # Each path, in contract order.

    def _path(  # Resolve a path option, so no path leaves its folder.
        self, value: str | None, default: Path, base: Path, name: str
    ) -> Path:
        """Resolve one path option, and refuse a path that leaves its allowed folder.

        Why: the outputs and the inputs are confined to fixed folders. The path is resolved before the test, so a
        `..` segment cannot leave the folder.

        Args:
            value: Value of the option, or None when the option was not given.
            default: Path that applies when the option was not given.
            base: Folder that the resolved path must stay inside.
            name: Name of the option, for the message.

        Returns:
            The resolved path, or the default when the option was not given.

        Raises:
            StopRun: The resolved path is outside the folder, or is the folder itself (exit code 2).
        """
        if value is None:  # The option was not given, so the default applies.
            return default  # The default path is inside its folder by construction.
        candidate = Path(value)  # The value as the operator typed it.
        resolved = (  # Resolve the typed path, so a dot-dot segment cannot escape.
            candidate if candidate.is_absolute() else self.root / candidate
        ).resolve()  # Resolve the ".." first.
        if resolved == base.resolve() or not resolved.is_relative_to(base.resolve()):  # Outside, or the folder itself.
            raise StopRun(  # Stop the run, since the path leaves its allowed folder.
                StopRun.Outcome.CONFIGURATION_ERROR, f"the path of {name} is outside its allowed folder"
            )
        return resolved  # The path stays inside its folder.

    def _identity(  # Resolve the token, host, organization, and site, in order.
        self, args: argparse.Namespace
    ) -> tuple[str, str, str | None]:
        """Apply the source order and the rules of the token, the host, the organization, and the site.

        Why: the env file is read first, and each value takes its first source in the contract order. A token that
        conflicts with another token stops the run. The secrets are kept before the conflict check, so the scrub list
        already holds each token value when the run stops.

        Args:
            args: Parsed options of the run.

        Returns:
            The host, the organization identifier, and the site identifier, or None for the site.

        Raises:
            StopRun: A token, host, or identifier breaks its rule (exit code 2).
        """
        rules = IdentityRules(self.environment, EnvFileReader(self.root).read(args.env_file))  # Env file read first.
        candidates = rules.token_candidates()  # Both token names, in lookup order.
        self.secrets = [value for value in candidates if value]  # Keep each token value before the conflict check.
        self.token = SmokeSettings.token_from(candidates)  # The one token value, or the configuration error.
        return rules.host(), rules.organization_id(args.org_id), rules.site_id(args.site_id)  # Host, org, and site.


@dataclass
class IdentityRules:  # Apply the lookup order and the rules of the token, host, organization, and site.
    """Look up the identity values of one run, and apply the rule of each value.

    Why: each value takes its first source in the contract order, and each rule stays with its value. The settings
    loader only orders the steps, so a change to one rule does not touch the order of the run.
    """

    HOST_DEFAULT: ClassVar[str] = "api.mist.com"  # Default regional host of the contract.

    environment: Mapping[str, str] = field(  # Process environment, which wins over the env file for each name.
        repr=False
    )
    env_values: Mapping[str, str | None] = field(repr=False)  # Values of the env file, or an empty mapping.

    def lookup(self, name: str) -> str:  # Process environment first, then the env file, then empty.
        """Return the text of one name, from the process environment first and then from the env file.

        Why: the process environment wins over the env file, so an operator can override a file value for one run.

        Args:
            name: Name of the variable.

        Returns:
            The stripped text of the variable, or an empty text when no source sets it.
        """
        return str(self.environment.get(name) or self.env_values.get(name) or "").strip()  # Empty counts as not set.

    def token_candidates(self) -> list[str]:  # Both token names, in lookup order.
        """Return the values of both token names, in lookup order, with an empty text for an unset name.

        Why: the two token names may both be set, so the caller checks every candidate before it picks one value.

        Returns:
            The two candidate values, MIST_API_TOKEN first.
        """
        return [self.lookup("MIST_API_TOKEN"), self.lookup("MIST_APITOKEN")]  # Both token names, in lookup order.

    def host(self) -> str:  # Regional host, a bare host name in lower case.
        """Return the regional host in lower case, and refuse a value that holds a scheme or a path.

        Why: the host is joined to a URL by the SDK, so a scheme or a path would send a request to a different address.

        Returns:
            The regional host in lower case.

        Raises:
            StopRun: The host holds a slash or a colon (exit code 2).
        """
        host = self.lookup("MIST_HOST") or self.HOST_DEFAULT  # The regional host, or the default host.
        if "/" in host or ":" in host:  # A scheme or a path is not a bare host name.
            raise StopRun(  # Stop the run, since a URL or path breaks the host value.
                StopRun.Outcome.CONFIGURATION_ERROR, "the host must be a bare host name"
            )
        return host.lower()  # Lower case, so host comparisons match.

    def organization_id(self, option: str | None) -> str:  # Organization identifier from the option or the sources.
        """Return the organization identifier in lower case, from the option or the first source that has it.

        Why: the option wins over each source, and the first source with a value is used in the contract order.

        Args:
            option: Value of --org-id, or None when the option was not given.

        Returns:
            The organization identifier in lower case.

        Raises:
            StopRun: The identifier is missing or is not a UUID (exit code 2).
        """
        text = option or next(  # Take the organization ID from the first source that has it.
            (value for value in (self.lookup("MIST_ORG_ID"), self.lookup("org_id"), self.lookup("ORG_ID")) if value),
            "",
        )
        return SmokeSettings.uuid_text(text, "organization ID")  # The organization identifier, lower case.

    def site_id(self, option: str | None) -> str | None:  # Optional site identifier from the option.
        """Return the site identifier in lower case when the option was given, or None.

        Why: SMK-08 reads the first site when no site identifier is given, so None is a valid answer.

        Args:
            option: Value of --site-id, or None when the option was not given.

        Returns:
            The site identifier in lower case, or None.

        Raises:
            StopRun: The identifier is not a UUID (exit code 2).
        """
        if not option:  # The option was not given, so SMK-08 reads the first site.
            return None  # No site identifier.
        return SmokeSettings.uuid_text(option, "site ID")  # The site identifier, lower case.


@dataclass
class CheckSequence:  # Run the checks in contract order, and record a result for each one.
    """Run SMK-01 to SMK-10 in order, record each result, and mark each check that did not run as SKIP.

    Why: SMK-01 runs before any session exists, and a run stop ends the checks at once. The results always hold ten
    check items, so the evidence record has the same shape for every outcome.
    """

    context: CheckContext  # Run state of the checks, with the session once it opens.
    results: list[CheckResult]  # Check results, shared with the command, in check order.
    current: str | None = None  # Identifier of the check that runs now, or None while the session opens.
    before: int = 0  # Number of attempts before the current check, so its own attempts can be read.

    def run(self) -> StopRun | None:  # Run every check, and return the run stop that ended them.
        """Run the checks, and return the run stop that ended them, or None when every check ran.

        Why: a run stop or an unexpected fault ends the checks. The stopped check keeps its own result, and each check
        after the stop gets a SKIP result with its cause.

        Returns:
            The run stop that ended the checks, or None when every check ran.
        """
        stop: StopRun | None = None  # The run stop, or None when no stop applies.
        try:  # A run stop or an unexpected fault ends the checks, and each path is recorded below.
            self._run_all()  # SMK-01 to SMK-10 in order, with the session opened after SMK-01.
        except StopRun as caught:  # A run stop ends the checks. The stopped check keeps its own result.
            stop = caught  # The outcome of the run.
            if self.current is not None:  # A check was running, so it has a result.
                fallback = CheckResult.from_calls(  # Build a FAIL result for a stop that has none.
                    self.current, CheckStatus.FAIL, caught.message, self.context.calls[self.before :]
                )
                self.results.append(caught.result or fallback)  # Keep the stopped check in the evidence.
        except Exception as error:  # An unexpected fault is an internal error, and its traceback is logged.
            logger.exception("Unexpected fault in check %s: %s", self.current, type(error).__name__)  # Traceback.
            stop = StopRun(StopRun.Outcome.INTERNAL_ERROR, f"unexpected {type(error).__name__}")  # Exit code 6.
        if stop is not None:  # A stop leaves some checks without a result, so each one gets a SKIP result.
            self._fill_skipped(stop)  # Keep the place of each check that did not run.
        return stop  # The run stop, or None.

    def _run_all(self) -> None:  # Run SMK-01, open the session, then SMK-02 to SMK-10.
        """Run SMK-01, open the API session, and run SMK-02 to SMK-10 in order.

        Why: the session opens after SMK-01 passes, so the configuration check runs with no session and no request.
        """
        self.current = "SMK-01"  # SMK-01 runs now, before any session exists.
        self.results.append(IdentityChecks(self.context).smk_01())  # The configuration check.
        self.current = None  # Opening the session is not a check, so a stop there adds no check result.
        self.context.open_client()  # Build the session, and count the token validation request.
        self._run_steps()  # SMK-02 to SMK-10 in order.

    def _run_steps(self) -> None:  # Run SMK-02 to SMK-10 in order, so a stop names its check.
        """Run SMK-02 to SMK-10 in order, and record which check is running.

        Why: the order of the checks is part of the contract.
        The record of the running check lets a run stop name the check that caused it.
        """
        steps = [  # Each check of the contract, in order, with its entry point.
            ("SMK-02", IdentityChecks(self.context).smk_02),
            ("SMK-03", IdentityChecks(self.context).smk_03),
            ("SMK-04", IdentityChecks(self.context).smk_04),
            ("SMK-05", CatalogChecks(self.context).smk_05),
            ("SMK-06", SearchChecks(self.context).smk_06),
            ("SMK-07", SearchChecks(self.context).smk_07),
            ("SMK-08", ScopeChecks(self.context).smk_08),
            ("SMK-09", ScopeChecks(self.context).smk_09),
            ("SMK-10", InventoryChecks(self.context).smk_10),
        ]
        for check_id, step in steps:  # Run each check in the contract order.
            self.current = check_id  # The check that runs now, for a stop or a fault.
            self.before = len(self.context.calls)  # Attempts before this check, so its own attempts can be read.
            self.results.append(step())  # The check returns its result, or raises a run stop.

    def _fill_skipped(self, stop: StopRun) -> None:  # Mark each check that did not run as SKIP, with its cause.
        """Append a SKIP result for each check that has no result, with the cause of the run stop.

        Why: the evidence record holds ten check items, so a check that did not run keeps its place with its cause.

        Args:
            stop: Run stop that ended the checks, which gives the cause of each SKIP result.
        """
        cause = f"not run: {stop.outcome.label.lower()}"  # The cause in the contract form.
        done = {result.check_id for result in self.results}  # Checks that already have a result.
        for check_id in CheckResult.TITLES:  # SMK-01 to SMK-10 in order.
            if check_id not in done:  # This check did not run.
                self.results.append(CheckResult.skipped(check_id, cause))  # Keep its place in the evidence.


@dataclass
class SmokeCommand:  # Own the run order, so every outcome gives one summary.
    """Run the smoke test for one command line, print its lines, write the evidence, and return the exit code.

    Why: every outcome, including a configuration error and an unexpected fault, ends in the same summary, outcome,
    and evidence lines. The command owns the order of the checks and the mapping from a run stop to an exit code.
    """

    root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2])  # Repository root of this package.
    environment: Mapping[str, str] = field(  # Process environment of the run. It can hold the token.
        default_factory=lambda: os.environ, repr=False
    )
    session_factory: Any = mistapi.APISession  # Builds the API session. Tests replace it with a fake.
    log_setup: LogSetup = field(default_factory=LogSetup)  # Logs and console scrub rules of the run.
    loader: SettingsLoader | None = None  # Loader of the run, which holds the token value after the lookup.
    context: CheckContext | None = None  # Run state, which exists once the settings are valid.
    results: list[CheckResult] = field(default_factory=list)  # Check results, in check order.
    stop: StopRun | None = None  # The run stop that ended the run, or None when no stop applied.
    output_path: Path | None = None  # Valid evidence path, or None when the output option was refused.

    def run(self, argv: Sequence[str]) -> int:  # Run the checks, so the console always shows the summary.
        """Run the smoke test for the arguments, and return the exit code of its outcome.

        Why: the entry point needs one call that always leaves the console with the summary and the outcome lines.

        Args:
            argv: Command line arguments, without the program name.

        Returns:
            The exit code of the outcome class, from 0 to 6.
        """
        self.log_setup.configure()  # Route the logs before any step that can log.
        loaded = self._load_settings(argv)  # Validate the options and the environment before any request.
        if loaded is not None:  # A valid configuration starts the checks.
            settings, token = loaded  # The validated options and the token value of this run.
            self._execute(settings, token)  # Run SMK-01 to SMK-10 in order.
        return self._finish()  # Write the evidence record and print the lines.

    def _load_settings(  # Load the settings, so a bad value stops the run early.
        self, argv: Sequence[str]
    ) -> tuple[SmokeSettings, str] | None:
        """Load the settings, and record a configuration error as the run stop.

        Why: a configuration error stops the run before SMK-01 with zero requests. The token candidates are protected
        before any later output, and the output path is kept for the evidence record.

        Args:
            argv: Command line arguments, without the program name.

        Returns:
            The validated settings, or None when the configuration stopped the run.
        """
        self.loader = SettingsLoader(root=self.root, environment=self.environment)  # Loader for this run only.
        try:  # A rule that fails raises the run stop of the configuration error.
            settings = self.loader.load(argv)  # Read the options, the environment, and the env file.
        except StopRun as stop:  # The configuration error ends the run before any check.
            self.stop = stop  # Keep the outcome for the summary.
            for secret in self.loader.secrets:  # Protect the token values that the lookup found.
                self.log_setup.protect(secret)  # Add each value and its masked form to the scrub list.
            self.output_path = self.loader.output_path  # Write the evidence only when this path is valid.
            logger.error("Configuration error before SMK-01: %s", stop.message)  # Log the cause, which holds no value.
            return None  # The checks do not run.
        except Exception as error:  # An unexpected fault while reading the configuration is an internal error.
            logger.exception("Unexpected fault while reading the configuration: %s", type(error).__name__)  # Traceback.
            self.stop = StopRun(  # Record an unexpected config fault as an internal error.
                StopRun.Outcome.INTERNAL_ERROR, f"unexpected {type(error).__name__} in the configuration"
            )
            return None  # The checks do not run.
        for secret in self.loader.secrets:  # Protect the token values before any check logs.
            self.log_setup.protect(secret)  # Add each value and its masked form to the scrub list.
        self.output_path = settings.output_path  # The evidence path of a valid configuration.
        return settings, self.loader.token  # The validated settings and the token value of this run.

    def _execute(  # Run the checks, so each check ends with one result.
        self, settings: SmokeSettings, token: str
    ) -> None:
        """Run the checks of the validated settings, and keep the run stop that ended them, if any.

        Why: the command keeps the run state for the evidence and the summary.
        The check sequence owns the order of the checks.
        It also owns the SKIP results of the checks that did not run.

        Args:
            settings: Validated settings of the run.
            token: Token value of the run, which only the session constructor receives.
        """
        context = CheckContext.for_run(settings, token, self.session_factory)  # The run state of the checks.
        self.log_setup.redactor = context.redactor  # The log lines use the same identifier rules as the evidence.
        self.context = context  # The command keeps the run state for the evidence and the summary.
        self.stop = CheckSequence(context, self.results).run()  # Run SMK-01 to SMK-10, and keep the run stop.

    def _write_evidence(self, outcome: StopRun.Outcome) -> tuple[StopRun.Outcome, str, str]:  # Record and its lines.
        """Write the evidence record when the output path is valid, and return the outcome and the two lines.

        Why: the evidence can fail to write, and that failure changes the outcome.
        The outcome does not change when an internal error already ended the run with exit code 6.

        Args:
            outcome: Outcome class of the run before the evidence write.

        Returns:
            The final outcome class, the evidence line, and the cause line.
        """
        evidence_line = "Evidence: not written"  # The line when no record exists.
        cause_line = self.stop.message if self.stop is not None else ""  # Cause of the run stop, when one exists.
        if self.output_path is not None:  # A valid output path gets an evidence record.
            try:  # The write can fail, and the failure changes the outcome.
                builder = EvidenceBuilder(  # Build the record, using the same rules as the logs.
                    self.context, self.log_setup.redactor, outcome, self.results
                )  # Record builder.
                written = builder.write(self.output_path)  # Filter, scrub, and write the record.
                evidence_line = f"Evidence: {written.relative_to(self.root).as_posix()}"  # Relative path in the output.
            except OSError as error:  # The file cannot be written, so the evidence is missing.
                logger.exception("The evidence file cannot be written: %s", type(error).__name__)  # Traceback.
                cause_line = f"the evidence file cannot be written ({type(error).__name__})"  # Second cause.
                if outcome is not StopRun.Outcome.INTERNAL_ERROR:  # An internal error keeps exit code 6.
                    outcome = StopRun.Outcome.CONFIGURATION_ERROR  # The contract maps this failure to exit code 2.
        return outcome, evidence_line, cause_line  # The final outcome and the two lines.

    def _finish(self) -> int:  # Print the summary and outcome, so every run ends the same.
        """Write the evidence record, print the summary, the outcome, and the evidence lines, and return the exit code.

        Why: the summary and outcome lines are printed for every run. An evidence failure changes the outcome, except
        when an internal error already ended the run with exit code 6.

        Returns:
            The exit code of the final outcome class.
        """
        outcome = self.stop.outcome if self.stop is not None else StopRun.Outcome.verdict(self.results)  # Verdict.
        outcome, evidence_line, cause_line = self._write_evidence(outcome)  # Record, and the outcome it can change.
        report = RunReport(  # The printed lines of the run, in contract order.
            context=self.context,  # Run state, for the sent count and the budget.
            results=self.results,  # Check results, in check order.
            outcome=outcome,  # Final outcome class.
            evidence_line=evidence_line,  # Evidence line of the contract.
            cause_line=cause_line,  # Cause of the run, or an empty text.
            scrub=self.log_setup.scrub_text,  # Scrub rule of the run, applied to the check and cause lines.
        )
        report.print_lines()  # Print each line in contract order.
        return outcome.exit_code  # The exit code of the outcome class.


if __name__ == "__main__":  # Run the command when Python executes the package as a module.
    raise SystemExit(SmokeCommand().run(sys.argv[1:]))  # The exit code comes from the outcome class.
