"""Identity checks SMK-01 to SMK-04: configuration, runbook structure, token access, and the hourly budget.

Why: a run must prove the host, the runbook structure, the token grant, and the request budget before a data check
reads the API. A wrong host or a read-write token would otherwise reach the organization without any notice.
"""

from __future__ import annotations  # Postpone annotation evaluation, so the classes can name each other.

from collections.abc import Sequence  # Type the privilege entries and the problem lists.
from dataclasses import replace  # Copy a result with the field names that the check confirmed.
from pathlib import Path  # Type the OpenAPI and runbook paths that the loader reads.
from typing import TYPE_CHECKING, Any, ClassVar, TypeIs  # Type the JSON values, the class constants, and the settings.

import structlog  # Structured logging of each file read and each request.

from scripts.netcool_runbook_smoke.checks import (  # Import the check types that build results and stop runs.
    CheckContext,
    CheckResult,
    CheckStatus,
    StopRun,
)
from scripts.netcool_runbook_smoke.documents import (  # Import the document types that the loader returns.
    OpenApiIndex,
    RunbookClaims,
)

if TYPE_CHECKING:  # Skip the type-only imports at run time, so no import cycle forms.
    from scripts.netcool_runbook_smoke.__main__ import SmokeSettings  # Type only, so the import forms no cycle.
    from scripts.netcool_runbook_smoke.client import CallRecord  # Type only, the record of one request attempt.

logger = structlog.get_logger(__name__)  # Module logger, so each event names this module.


class DocumentLoader:  # Read input files, and decide which failure stops the run.
    """Read the OpenAPI file and the runbook of one run, and stop the run when a required file is unreadable.

    Why: a run cannot compare the runbook or check the host without the OpenAPI file. A missing default runbook
    is a skip, but a missing explicit runbook is a configuration error, so the two cases are decided here once.
    """

    def load(  # Read both files, and allow an absent default runbook.
        self, settings: SmokeSettings
    ) -> tuple[OpenApiIndex, RunbookClaims | None]:
        """Read the OpenAPI file, and read the runbook when it exists.

        Why: the OpenAPI file is always required. The runbook is required only when the operator named it.

        Args:
            settings: Validated options of the run, with the OpenAPI and runbook paths.

        Returns:
            The OpenAPI index, and the runbook facts or None when the default runbook is absent.

        Raises:
            StopRun: The OpenAPI file cannot be read, or an explicit runbook is missing or unreadable (exit code 2).
        """
        openapi = self._openapi(settings.openapi_path)  # Index of the OpenAPI file, or a stop when it fails to load.
        if not settings.runbook_path.is_file():  # The runbook is absent, which is an error only with --runbook.
            if settings.runbook_explicit:  # An explicit runbook must exist.
                message = "the runbook given by --runbook does not exist"  # Cause in the contract words.
                raise StopRun.failed_check(  # Stop the run, since an explicit runbook must exist.
                    "SMK-01", StopRun.Outcome.CONFIGURATION_ERROR, message
                )
            return openapi, None  # The default runbook is absent, so SMK-02 and the name checks skip.
        return openapi, self._runbook(settings.runbook_path)  # The OpenAPI index and the runbook facts.

    def _openapi(self, path: Path) -> OpenApiIndex:  # Read the OpenAPI file, which every run needs.
        """Index the OpenAPI file, or stop the run when the file cannot be read.

        Why: the OpenAPI file gives the GET operations and the regional servers, so no run can proceed without it.

        Args:
            path: Path of the OpenAPI file under the repository root.

        Returns:
            The index of the GET operations and the servers.

        Raises:
            StopRun: The OpenAPI file cannot be read or parsed (exit code 2).
        """
        logger.info("Reading the OpenAPI file for SMK-01")  # Log before the file read.
        try:  # A missing, unreadable, or invalid file stops the run before any request.
            openapi = OpenApiIndex.from_path(path)  # Index the GET operations and the servers.
        except ValueError as error:  # The message names the file only, never a folder of the user.
            logger.exception("The OpenAPI file cannot be read")  # Keep the traceback for the operator.
            raise StopRun.failed_check(  # Stop the run when the OpenAPI file fails to load.
                "SMK-01", StopRun.Outcome.CONFIGURATION_ERROR, "the OpenAPI file cannot be read"
            ) from error
        logger.debug("OpenAPI file indexed with %s servers", len(openapi.server_hosts()))  # Log the server count.
        return openapi  # The index that the run shares.

    def _runbook(self, path: Path) -> RunbookClaims:  # Parse the runbook, which SMK-01 and SMK-02 compare.
        """Parse the runbook headings, paths, and tables, or stop the run when the file cannot be read.

        Why: the runbook is the operator procedure. Its facts are parsed once, so each check reads the same values.

        Args:
            path: Path of the runbook under the repository root.

        Returns:
            The runbook facts.

        Raises:
            StopRun: The runbook is not UTF-8 Markdown that the parser can read (exit code 2).
        """
        logger.info("Reading the runbook for SMK-01")  # Log before the runbook read.
        try:  # The runbook must be UTF-8 Markdown that the parser can read.
            claims = RunbookClaims.from_path(path)  # Parse the headings, the paths, and the tables once.
        except ValueError as error:  # The message names the file only.
            logger.exception("The runbook cannot be read")  # Keep the traceback for the operator.
            raise StopRun.failed_check(  # Stop the run when the runbook fails to parse as Markdown.
                "SMK-01", StopRun.Outcome.CONFIGURATION_ERROR, "the runbook cannot be read"
            ) from error
        logger.debug("Runbook parsed with %s headings", len(claims.headings))  # Log the heading count.
        return claims  # The runbook facts that the run shares.


class RunbookStructure:  # Find runbook defects, so the operator can repair them.
    """Compare the runbook with the required headings, Appendix A paths, Appendix B tables, and regional hosts.

    Why: the runbook is the operator procedure.
    A missing section is a defect.
    A path with no GET operation is a defect.
    A host list that differs from the OpenAPI servers is a defect.
    SMK-02 names each defect before the live checks run.
    """

    REQUIRED_H1: ClassVar[str] = "MIST_NETCOOL_ALARM_INTEGRATION"  # The document title, from runbook-structure.md.
    REQUIRED_H2: ClassVar[tuple[str, ...]] = (  # The level-2 headings of the runbook, in document order.
        "1. Overview",
        "2. How to Use This Runbook",
        "3. Purpose and Scope",
        "4. Architecture",
        "5. Prerequisites",
        "6. Mist Data Sources",
        "7. Alarm and Event Selection",
        "8. Collection Design",
        "9. Netcool Integration",
        "10. AP Warning Report (Menu 307)",
        "11. NOC Operating Procedures",
        "12. Troubleshooting",
        "13. Verification and Smoke Test",
        "14. Acceptance Criteria and UAT Plan",
        "15. Open Decisions",
        "Appendix A. Endpoint Reference",
        "Appendix B. Verified Catalog Names",
        "Appendix C. Sample Payloads",
        "Appendix D. Glossary",
        "Appendix E. Revision History",
    )
    REQUIRED_H3: ClassVar[tuple[str, ...]] = (  # The level-3 headings that the checks read. B.4 is optional.
        "5.5 Regional API Hosts",
        "6.1 Alarm Search",
        "6.2 Device Event Search",
        "6.3 Mist Edge Event Search",
        "6.4 System Event Search",
        "6.5 Definition Catalogs",
        "6.6 Webhook Topics",
        "B.1 Alarm Types",
        "B.2 Device Event Types",
        "B.3 Mist Edge Event Types",
        "B.5 Webhook Topics",
    )
    REQUIRED_TABLES: ClassVar[tuple[str, ...]] = (  # Appendix B tables that must hold a name. B.4 is optional.
        "alarm_defs",
        "device_events",
        "mxedge_events",
        "webhook_topics",
    )

    def problems(  # Collect all defects, so one run lists each repair.
        self, claims: RunbookClaims, openapi: OpenApiIndex
    ) -> list[str]:
        """Return one text for each defect of the runbook against the contract and the OpenAPI file.

        Why: each defect is named, so the operator repairs the runbook from one run.

        Args:
            claims: Parsed facts of the runbook.
            openapi: Index of the OpenAPI file.

        Returns:
            The defect texts. An empty list means that the structure matches the contract.
        """
        logger.info("Comparing the runbook structure with the contract")  # Log before the comparison.
        found = [  # Missing headings, then paths and empty tables, then regional hosts.
            *self._heading_problems(claims),
            *self._path_and_table_problems(claims, openapi),
            *self._host_problems(claims, openapi),
        ]
        logger.debug("Runbook structure comparison found %s defects", len(found))  # Log the defect count.
        return found  # The defect texts, in check order.

    def _heading_problems(  # Report missing headings, since each one names a section.
        self, claims: RunbookClaims
    ) -> list[str]:
        """Return one text for each required heading that the runbook lacks.

        Why: a heading names a section of the procedure, so an absent heading leaves the operator without it.

        Args:
            claims: Parsed facts of the runbook.

        Returns:
            One text for each missing heading, with its level markers.
        """
        present = set(claims.headings)  # Each heading as its (level, text) pair.
        required = [(1, self.REQUIRED_H1)]  # The title is the only level-1 heading.
        required += [(2, text) for text in self.REQUIRED_H2]  # The level-2 headings.
        required += [(3, text) for text in self.REQUIRED_H3]  # The level-3 headings.
        return [  # List each required heading that the runbook lacks.
            f"missing heading {'#' * level} {text}" for level, text in required if (level, text) not in present
        ]

    def _path_and_table_problems(  # Check the paths and tables that the live checks need.
        self, claims: RunbookClaims, openapi: OpenApiIndex
    ) -> list[str]:
        """Return one text for each Appendix A path without a GET operation, and each empty required table.

        Why: an endpoint path without a GET operation cannot be read, and an empty table holds no names to check.

        Args:
            claims: Parsed facts of the runbook.
            openapi: Index of the OpenAPI file.

        Returns:
            The defect texts for the paths and the tables.
        """
        found = [  # Collect each path without GET, since no GET call can run.
            f"no GET operation for {path}" for path in claims.endpoint_paths if not openapi.has_get(path)
        ]  # Paths.
        if not claims.endpoint_paths:  # An empty Appendix A table gives no proof for any path.
            found.append("Appendix A has no endpoint rows")  # The table must hold rows.
        for key in self.REQUIRED_TABLES:  # Each Appendix B table that must hold a name.
            if not claims.catalog_names.get(key):  # The table holds no backticked name.
                found.append(f"empty Appendix B table for {key}")  # Name the empty table.
        return found  # Return the path and table defects, in check order.

    def _host_problems(  # Report a host mismatch, which would mislead the operator.
        self, claims: RunbookClaims, openapi: OpenApiIndex
    ) -> list[str]:
        """Return the regional hosts that differ between the runbook and the OpenAPI servers.

        Why: the runbook must name every regional host that the API serves, and no other host.

        Args:
            claims: Parsed facts of the runbook.
            openapi: Index of the OpenAPI file.

        Returns:
            One text for the hosts that are missing from the runbook, and one for the extra hosts.
        """
        openapi_hosts = set(openapi.server_hosts())  # Hosts of the OpenAPI servers list.
        runbook_hosts = set(claims.regional_hosts)  # Hosts of the section 5.5 table.
        differences = (  # Each mismatch with its message, in the order of the defect list.
            ("regional hosts missing from the runbook: ", sorted(openapi_hosts - runbook_hosts)),  # File only.
            ("regional hosts not in the OpenAPI servers: ", sorted(runbook_hosts - openapi_hosts)),  # Runbook only.
        )
        return [message + ", ".join(hosts) for message, hosts in differences if hosts]  # Name each differing host.


class PrivilegeReader:  # Decide the token grant, which SMK-03 uses to stop or warn.
    """Decide from the privilege entries of the token whether the token grants the organization, and with which role.

    Why: the token must grant the organization with the read role. Another role gives a warning, and an entry
    that grants nothing does not count. A token that grants nothing stops the run before any data request.
    """

    def read(  # Build the SMK-03 result from the self response, or fail when it has no privilege list.
        self, attempts: Sequence[CallRecord], org_id: str
    ) -> CheckResult:
        """Return the SMK-03 result of the self response, and stop the run when no entry grants the organization.

        Why: a response without a readable privilege list proves no grant, so SMK-03 fails and the run reports the
        defect. A readable list goes through the grant rule, which stops the run when nothing grants the organization.

        Args:
            attempts: Every attempt of the self request. The last attempt decides the answer.
            org_id: Lower-case organization identifier of the run.

        Returns:
            The PASS, WARN, or FAIL result of SMK-03.

        Raises:
            StopRun: No privilege entry grants the organization (exit code 2).
        """
        final = attempts[-1]  # The last attempt decides the answer.
        body = final.data if isinstance(final.data, dict) else {}  # Only an object can hold the privileges.
        privileges = body.get("privileges")  # Privilege entries of the token owner.
        if final.status_code != 200 or not isinstance(privileges, list):  # Only HTTP 200 with a list is readable.
            status_text = "no response" if final.status_code is None else f"HTTP {final.status_code}"  # Status words.
            text = f"{status_text}: the self response has no privilege list."  # Cause of the failure.
            logger.debug("SMK-03 could not read the privileges")  # Log the failed read.
            return CheckResult.from_calls("SMK-03", CheckStatus.FAIL, text, attempts)  # Fail without a stop.
        return self._decided(privileges, attempts, org_id)  # Judge the readable privilege list.

    def _decided(  # Judge a readable privilege list, and stop the run when nothing grants the organization.
        self, privileges: list[Any], attempts: Sequence[CallRecord], org_id: str
    ) -> CheckResult:
        """Return the SMK-03 result of a readable privilege list, and raise the stop when no entry grants.

        Why: the grant rule gives PASS, WARN, or FAIL. A FAIL stops the run before any data request, and the
        result names the confirmed field names, never their values.

        Args:
            privileges: Privilege entries of the self response.
            attempts: Every attempt of the self request, which the result keeps as evidence.
            org_id: Lower-case organization identifier of the run.

        Returns:
            The PASS or WARN result, so the run continues.

        Raises:
            StopRun: No privilege entry grants the organization (exit code 2).
        """
        status, text = self.decide(privileges, org_id, "org-1")  # The grant rule, with the organization label.
        logger.debug("SMK-03 privilege rule gave %s", status.value)  # Log the decision.
        result = replace(  # Keep the confirmed field names, never their values.
            CheckResult.from_calls("SMK-03", status, text, attempts),
            field_names=tuple(sorted({key for entry in privileges if isinstance(entry, dict) for key in entry})),
        )
        if status is CheckStatus.FAIL:  # No entry grants the organization, so the run stops.
            raise StopRun(StopRun.Outcome.CONFIGURATION_ERROR, text, result)  # Stop with the result as evidence.
        return result  # Return the PASS or WARN result, so the run continues.

    def decide(  # Decide the SMK-03 status, so one rule gives each outcome.
        self, privileges: Sequence[Any], org_id: str, org_label: str
    ) -> tuple[CheckStatus, str]:
        """Return the status and the text of the privilege rule of SMK-03.

        Why: the rule keeps one answer for each case.
        A read role gives PASS, and another role gives WARN.
        An MSP scope gives WARN, and no grant gives FAIL.

        Args:
            privileges: Privilege entries of the self response.
            org_id: Lower-case organization identifier of the run.
            org_label: Label of the organization in the output.

        Returns:
            The status and the text. FAIL means that no entry grants the organization.
        """
        entries = [entry for entry in privileges if isinstance(entry, dict)]  # Entries that are objects can grant.
        org_grants = [  # Keep only grants that name this organization, since other grants do not cover it.
            entry for entry in entries if entry.get("scope") == "org" and str(entry.get("org_id", "")).lower() == org_id
        ]
        has_msp = any(entry.get("scope") == "msp" for entry in entries)  # MSP scope can cover the organization.
        status, text = self._grant(org_grants, has_msp, org_label)  # The grant rule.
        return self._unconfirmed(status, text, entries)  # Adjust the result when an entry names no organization.

    def _unconfirmed(  # Handle organization entries that lack an identifier.
        self, status: CheckStatus, text: str, entries: Sequence[Any]
    ) -> tuple[CheckStatus, str]:
        """Return the status and the text after the rule for an org entry that names no organization.

        Why: an org entry without an org_id never grants the organization. With no grant the run stops and both causes
        are named. With a grant the entry only warns.

        Args:
            status: Status of the grant rule.
            text: Text of the grant rule.
            entries: Privilege entries that are objects.

        Returns:
            The status and the text of the check.
        """
        unconfirmed = any(entry.get("scope") == "org" and not entry.get("org_id") for entry in entries)  # No org_id.
        if not unconfirmed:  # Every org entry names its organization, so the grant rule stands.
            return status, text  # Keep the result if organization entries have identifiers.
        if status is CheckStatus.FAIL:  # No grant at all, so the run stops, and the text names both causes.
            return (  # Keep the failure, so the operator sees both causes.
                status,
                f"{text}; organization scope not confirmed",
            )
        return CheckStatus.WARN, "organization scope not confirmed"  # A grant exists, so the entry only warns.

    def _grant(  # Choose the grant status, since only read gives a pass.
        self, org_grants: list[Any], has_msp: bool, org_label: str
    ) -> tuple[CheckStatus, str]:
        """Return the status and the text of the grant rule for the organization.

        Why: read gives PASS. Another role gives WARN, because a collector must use a read-only token. An MSP scope
        gives WARN, because its role is not visible. No grant gives FAIL.

        Args:
            org_grants: Privilege entries that grant the target organization.
            has_msp: True when an MSP entry exists.
            org_label: Label of the organization in the output.

        Returns:
            The status and the text of the rule.
        """
        roles = sorted({str(entry.get("role")) for entry in org_grants})  # The role names of the grants.
        if "read" in roles:  # Read is the only role that a collector may hold.
            return (  # Pass with the read role, the one role a collector may hold.
                CheckStatus.PASS,
                f"role read, organization {org_label} in the privileges.",
            )
        if org_grants:  # The organization is granted with another role.
            role_text = ", ".join(roles)  # The role names only.
            return (  # Warn when another role grants access, which is not read.
                CheckStatus.WARN,
                f"role {role_text}, but a production collector must use a read-only token.",
            )
        if has_msp:  # An MSP privilege can cover the organization, but its role is not visible.
            msp_text = (  # Name the MSP case, whose organization role is not visible.
                "organization access can come from an MSP privilege, so the role for the organization is "
            )
            return CheckStatus.WARN, msp_text + "unknown"  # Warn with the MSP text, since the role is unknown.
        return CheckStatus.FAIL, "the token does not grant the organization"  # No entry grants the organization.


class UsageReader:  # Read usage values, and refuse a value of the wrong type.
    """Read the hourly usage values of the self usage response, when each value has its contract type.

    Why: the remaining budget decides whether the run can finish. A value of another type cannot prove the budget,
    so the reader refuses it, and the check reports the usage as unreadable.
    """

    def values(  # Give SMK-04 the budget values, or None when unreadable.
        self, status_code: int | None, body: Any
    ) -> tuple[int, int, float] | None:
        """Return the requests, the request limit, and the seconds, or None when a value is unreadable.

        Why: the contract types requests and request_limit as integers and seconds as a number.

        Args:
            status_code: HTTP status of the usage request, or None when no response exists.
            body: Parsed body of the usage request.

        Returns:
            The three values, or None when the status is not 200 or a value has the wrong type.
        """
        if status_code != 200 or not isinstance(body, dict):  # A readable usage needs HTTP 200 and an object.
            return None  # The usage is unreadable.
        requests_used, limit, seconds = (  # The three usage values of the hour.
            body.get("requests"),  # Requests used in the hour.
            body.get("request_limit"),  # Requests allowed in the hour.
            body.get("seconds"),  # Seconds until the hour resets.
        )
        if not (self._is_count(requests_used) and self._is_count(limit) and self._is_number(seconds)):  # Types.
            return None  # The usage is unreadable.
        return requests_used, limit, float(seconds)  # The three readable values, typed by the checks above.

    def result_of(  # Build the SMK-04 result from the usage response, or warn when it is unreadable.
        self, attempts: Sequence[CallRecord], budget: int
    ) -> CheckResult:
        """Return the SMK-04 result of the usage response, and raise the stop when the hour is nearly spent.

        Why: an unreadable usage cannot prove the remaining budget, so it warns and the run goes on. A readable usage
        that leaves fewer than two budgets stops the run with the rate-limit exit code.

        Args:
            attempts: Every attempt of the usage request. The last attempt decides the answer.
            budget: Request budget of the run.

        Returns:
            The PASS or WARN result of SMK-04.

        Raises:
            StopRun: The remaining budget is below twice the request budget (exit code 3).
        """
        final = attempts[-1]  # The last attempt decides the answer.
        usage = self.values(final.status_code, final.data)  # None when a value is unreadable.
        if usage is None:  # An unreadable usage is a warning, and the run goes on.
            logger.debug("SMK-04 could not read the hourly usage")  # Log the warning.
            text = "the hourly usage was not readable"  # The contract wording of the warning.
            return CheckResult.from_calls("SMK-04", CheckStatus.WARN, text, attempts)  # Warn, the run goes on.
        return self._verdict(usage, attempts, budget)  # Judge the readable values.

    def _verdict(  # Judge the readable usage, and stop the run when fewer than two budgets remain.
        self, usage: tuple[int, int, float], attempts: Sequence[CallRecord], budget: int
    ) -> CheckResult:
        """Return the SMK-04 result of readable usage values, and raise the stop when fewer than two budgets remain.

        Why: a run that starts with fewer than two budgets would be throttled in the middle. The documented request
        limit is 5000, so another limit gives a warning that names the value.

        Args:
            usage: Requests used, request limit, and seconds until the hour resets.
            attempts: Every attempt of the usage request, which the result keeps as evidence.
            budget: Request budget of the run.

        Returns:
            The PASS or WARN result of SMK-04.

        Raises:
            StopRun: The remaining budget is below twice the request budget (exit code 3).
        """
        used, limit, seconds = usage  # The three readable values.
        summary = (  # Facts of the hour, with the used and the remaining requests.
            f"{used} of {limit} requests used, {limit - used} remaining, seconds {seconds:g}."
        )
        if limit - used < 2 * budget:  # Fewer than two budgets would throttle the run before it ends.
            text = f"{summary} Fewer than two budgets remain."  # Cause of the stop.
            result = CheckResult.from_calls("SMK-04", CheckStatus.FAIL, text, attempts)  # The failed result.
            raise StopRun(StopRun.Outcome.RATE_LIMIT_STOP, "the hourly usage is low", result)  # Stop the run.
        status, text = (  # The documented limit passes, and any other limit warns with its value.
            (CheckStatus.PASS, summary)
            if limit == 5000
            else (CheckStatus.WARN, f"{summary} The request limit is {limit}, not 5000.")
        )
        return replace(  # Name the usage fields that the check confirmed.
            CheckResult.from_calls("SMK-04", status, text, attempts),
            field_names=("request_limit", "requests", "seconds"),
        )

    @staticmethod
    def _is_count(value: Any) -> TypeIs[int]:  # Accept an integer count, and refuse a boolean that Python reads as int.
        """Return True when the value is an integer count and not a boolean.

        Why: the contract types the request counts as integers. Python treats a boolean as an integer, so a
        boolean must be refused here.

        Args:
            value: Value read from the usage body.

        Returns:
            True when the value is an integer count.
        """
        return isinstance(value, int) and not isinstance(value, bool)  # A boolean is not a count.

    @staticmethod
    def _is_number(value: Any) -> TypeIs[int | float]:  # Accept an integer or a float, and refuse a boolean.
        """Return True when the value is a number and not a boolean.

        Why: the contract types the seconds as a number. A boolean is refused for the same reason as a count.

        Args:
            value: Value read from the usage body.

        Returns:
            True when the value is an integer or a float.
        """
        return isinstance(value, (int, float)) and not isinstance(value, bool)  # A boolean is not a number here.


class IdentityChecks:  # Run SMK-01 to SMK-04, before any data check runs.
    """Run SMK-01 to SMK-04: configuration, runbook structure, token access, and the hourly request budget.

    Why: these checks read two small endpoints and no data. They prove that the run uses the intended host,
    runbook, organization, token grant, and budget before any data check runs.
    """

    def __init__(self, context: CheckContext) -> None:  # Keep the run context, so all four checks share one state.
        """Keep the run context that the checks share.

        Args:
            context: Run state of the smoke test.
        """
        self._context: CheckContext = context  # Run state that the checks read and write.

    def smk_01(self) -> CheckResult:  # Check the host and files first, before any API request.
        """Check the OpenAPI file, the host, and an explicit runbook before the API session is built.

        Why: a wrong host or a missing OpenAPI file would make every later check meaningless.
        The run therefore stops before the token validation request is sent.

        Returns:
            The PASS result of SMK-01.

        Raises:
            StopRun: The OpenAPI file, the host, or an explicit runbook fails its rule (exit code 2).
        """
        openapi, claims = DocumentLoader().load(self._context.settings)  # Read the OpenAPI file and the runbook.
        self._context.openapi, self._context.claims = openapi, claims  # Share both with the later checks.
        if self._context.settings.host not in openapi.server_hosts():  # The host must be one of the regional servers.
            message = "the host is not in the OpenAPI servers list"  # Cause in the contract words.
            raise StopRun.failed_check(  # Stop the run when the host is not a regional server.
                "SMK-01", StopRun.Outcome.CONFIGURATION_ERROR, message
            )
        logger.debug("SMK-01 accepted host %s", self._context.settings.host)  # Log the accepted host name.
        return CheckResult.from_calls(  # Pass with no API call, since SMK-01 reads only files.
            "SMK-01", CheckStatus.PASS, "token present, host in the server list, organization ID valid.", ()
        )

    def smk_02(self) -> CheckResult:  # Check the runbook structure, since operators rely on it.
        """Check the runbook headings, the Appendix A paths, the Appendix B tables, and the regional hosts.

        Why: the operator reads the runbook as the procedure, so each required part must exist before the
        live checks compare its names.

        Returns:
            The PASS or FAIL result, or SKIP when the default runbook is absent.
        """
        claims, openapi = self._context.claims, self._context.openapi  # Runbook and OpenAPI index from SMK-01.
        if claims is None or openapi is None:  # No runbook means no structure to compare.
            logger.info("Runbook structure skipped, the runbook is not found")  # Log the skip.
            return CheckResult.skipped("SMK-02", "runbook not found")  # The cause in the contract words.
        problems = RunbookStructure().problems(claims, openapi)  # Compare the runbook with the contract.
        if problems:  # At least one defect was found.
            return CheckResult.from_calls("SMK-02", CheckStatus.FAIL, "; ".join(problems), ())  # Name each defect.
        return CheckResult.from_calls(  # Pass when the runbook has no defect, with no API call.
            "SMK-02", CheckStatus.PASS, "all headings found, each path has a GET operation.", ()
        )

    def smk_03(self) -> CheckResult:  # Read the token grant, which decides if the run stops.
        """Read the token owner with GET /api/v1/self, and decide whether the token grants the organization.

        Why: a token that does not grant the organization, or that is not read-only, must not run the collector.

        Returns:
            The PASS, WARN, or FAIL result of SMK-03.

        Raises:
            StopRun: The token does not grant the organization (exit code 2). HTTP 401 also gives exit code 2.
        """
        logger.info("Reading the token privileges for SMK-03")  # Log before the request.
        attempts = self._context.get("/api/v1/self", {}, {})  # One request, counted by the budget.
        reader = PrivilegeReader()  # Decide the grant from the privilege entries.
        return reader.read(attempts, self._context.settings.org_id)  # Judge the grant, stop on none.

    def smk_04(self) -> CheckResult:  # Check the hourly budget, before the API throttles the run.
        """Read the hourly usage once, and stop the run when the remaining budget is below two budgets.

        Why: the collector needs the remaining hourly requests. A run that starts with too few would be throttled
        in the middle, so the smoke test stops with the rate-limit exit code instead.

        Returns:
            The PASS, WARN, or FAIL result of SMK-04.

        Raises:
            StopRun: The remaining budget is below twice the request budget (exit code 3).
        """
        logger.info("Reading the hourly usage for SMK-04")  # Log before the request.
        attempts = self._context.get("/api/v1/self/usage", {}, {})  # One usage request for each run.
        reader = UsageReader()  # Read the usage values with their contract types.
        return reader.result_of(attempts, self._context.settings.max_requests)  # Judge the hour, stop when low.
