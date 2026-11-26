"""Unit tests of the smoke checks SMK-01 to SMK-10, their run stops, and their observations.

The tests build the real client and call governor of the smoke test, with a scripted fake SDK session. No test
sends a request to the network, and each token value is the fake value fake-token-for-tests.
"""

from __future__ import annotations  # Postpone annotation evaluation, as the package does.

import json  # Write the OpenAPI fixture of the SMK-01 tests.
import re  # Normalize the placeholders of the fixture paths, as the OpenAPI index does.
import threading  # Block one fake SDK call, so the timeout rule can be exercised.
from dataclasses import dataclass, field  # Declare the fake response.
from pathlib import Path  # Build paths with pathlib, so tests run on Windows, macOS, and Linux.
from typing import Any  # Type the fake payloads and the scripted replies.

import pytest  # Parametrize the cases and assert the raised run stops.

from scripts.netcool_runbook_smoke.__main__ import SmokeSettings  # Build the settings that the checks read.
from scripts.netcool_runbook_smoke.checks import (  # Import the check context, the results, and the run stop.
    CheckContext,
    CheckResult,
    CheckStatus,
    StopRun,
)
from scripts.netcool_runbook_smoke.checks.catalogs import CatalogChecks  # Import the catalog checks under test.
from scripts.netcool_runbook_smoke.checks.identity import (  # Import the identity checks and the runbook contract.
    IdentityChecks,
    RunbookStructure,
)
from scripts.netcool_runbook_smoke.checks.scope import (  # Import the scope and inventory checks under test.
    InventoryChecks,
    ScopeChecks,
)
from scripts.netcool_runbook_smoke.checks.searches import SearchChecks  # Import the search checks under test.
from scripts.netcool_runbook_smoke.client import (  # Import the governor and the client that the checks call through.
    CallGovernor,
    CallRecord,
    ReadOnlyMistClient,
)
from scripts.netcool_runbook_smoke.documents import (  # Import the document readers and the evidence redactor.
    EvidenceRedactor,
    OpenApiIndex,
    RunbookClaims,
)

ORG = "11111111-2222-4333-8444-555555555555"  # Fake organization identifier, never a real one.
SITE = "66666666-7777-4888-8999-aaaaaaaaaaaa"  # Fake site identifier, never a real one.
TOKEN = "fake-token-for-tests"  # nosec B105 - a fake test value, never a credential.
HOST = "api.mist.com"  # Approved host of the test runs.
STOP = StopRun.Outcome  # Short name of the outcome classes.


@dataclass
class FakeResponse:  # Stand in for the SDK response with only the fields that the client reads.
    """Scripted SDK response with the attributes that the client reads.

    Why: the client reads status_code, data, raw_data, headers, and next, so a fake with those names exercises the
    same classification as a real SDK response.
    """

    status_code: int | None  # HTTP status of the fake response, or None for a connection failure.
    data: Any  # Parsed body of the fake response, which the client reads first.
    raw_data: str = ""  # Body text, which tells an empty body from a malformed one.
    headers: dict[str, str] = field(default_factory=dict)  # Response headers, with any case.
    next: Any = None  # The next link the client follows, or None at the end.


def reply(  # One builder keeps every scripted response shaped the same way.
    status: int = 200, data: Any = None, headers: dict[str, str] | None = None, next_value: Any = None
) -> FakeResponse:
    """Return a scripted response whose body text is the JSON of its data.

    Why: the client reads the raw text to tell an empty body from a malformed one, so the text follows the data.

    Args:
        status: HTTP status of the response.
        data: Parsed body of the response.
        headers: Response headers, or None for none.
        next_value: Next link of a paged response, or None.

    Returns:
        The scripted response.
    """
    raw = json.dumps(data) if data is not None else ""  # The body text, empty when the body is missing.
    body = data if data is not None else {}  # A missing body is an empty object.
    return FakeResponse(  # Return the scripted reply to the client under test.
        status_code=status, data=body, raw_data=raw, headers=headers or {}, next=next_value
    )


class FakeSession:  # Replace the SDK session with a scripted list of replies.
    """Scripted SDK session. Each mist_get returns the next reply whose suffix ends the request path.

    Why: the client calls only mist_get, so one method is enough. The request list lets each test count the requests.
    """

    def __init__(self) -> None:  # Start with no scripted replies and no recorded paths.
        """Start with no script and no request."""
        self.script: list[tuple[str, FakeResponse | BaseException | threading.Event]] = []  # Suffix and reply.
        self.uris: list[str] = []  # Each path that the session received, in order.

    def add(  # Queue replies for each path that ends with the suffix.
        self, suffix: str, *replies: FakeResponse | BaseException | threading.Event
    ) -> None:
        """Queue replies for requests whose path ends with the suffix.

        Args:
            suffix: End of the request path, for example /api/v1/self.
            replies: Replies to return in the order of the requests.
        """
        self.script.extend((suffix, item) for item in replies)  # Keep the order of each suffix.

    def mist_get(  # Answer each SDK call with the next scripted reply for its path.
        self, uri: str, query: dict[str, str]
    ) -> FakeResponse:
        """Return the next scripted reply for the path, or raise when none was queued.

        Why: a missing script is a test mistake, so it fails at once instead of returning an empty success.

        Args:
            uri: Path of the request, without the query.
            query: Query of the request, which these tests do not check.

        Returns:
            The scripted response.

        Raises:
            LookupError: The test did not script a reply for this path.
        """
        self.uris.append(uri)  # Record the path before any answer.
        for index, (suffix, item) in enumerate(self.script):  # The first queued reply for this path.
            if uri.endswith(suffix):  # The path ends with the scripted suffix.
                del self.script[index]  # Each reply is used once.
                if isinstance(item, threading.Event):  # A blocked call waits until the test releases it.
                    item.wait(timeout=10)  # The timeout keeps a broken test from hanging forever.
                    return reply(data=[])  # The late answer is never used by the timeout test.
                if isinstance(item, BaseException):  # A scripted fault is raised in the worker thread.
                    raise item  # A scripted fault must reach the governor like a real SDK error.
                return item  # The scripted response.
        raise LookupError(f"no scripted reply for {uri}")  # A missing script is a test mistake.


def normal(path: str) -> str:  # Mirror the OpenAPI index rule for placeholders, so the fixture paths match.
    """Return the path with each placeholder replaced by {}, as the OpenAPI index stores it.

    Args:
        path: Path with placeholders.

    Returns:
        The normalized path.
    """
    return re.sub(r"\{[^{}/]*\}", "{}", path)  # The same rule as the OpenAPI index.


def make_openapi(  # Build an OpenAPI index with a GET operation for each path and the given servers.
    paths: tuple[str, ...], servers: tuple[str, ...] = (HOST,)
) -> OpenApiIndex:
    """Return an OpenAPI index with a GET operation for each path and the given servers.

    Args:
        paths: Paths that have a GET operation.
        servers: Host names of the servers list.

    Returns:
        The OpenAPI index.
    """
    operations: dict[str, tuple[str, list[Any]]] = {  # Map each normalized path to one GET operation.
        normal(path): ("op", []) for path in paths
    }  # One GET operation for each path.
    urls = tuple(f"https://{host}" for host in servers)  # The server URLs of the file.
    return OpenApiIndex(  # Return the fixture index that the checks read.
        path=Path("openapi.json"), operations=operations, references={}, servers=urls
    )


def make_settings(  # Build validated settings for one test, with its paths under the test root.
    root: Path, **overrides: Any
) -> SmokeSettings:
    """Return validated settings for one test, with the paths under the test root.

    Args:
        root: Test root folder.
        overrides: Fields to change from the defaults.

    Returns:
        The settings of the test.
    """
    values: dict[str, Any] = {  # Each test starts here and changes only the fields it names.
        "host": HOST,
        "org_id": ORG,
        "site_id": None,
        "runbook_path": root / "runbook.md",
        "runbook_explicit": False,
        "openapi_path": root / "openapi.json",
        "window_minutes": 60,
        "delay_minutes": 2,
        "max_pages": 3,
        "max_requests": 60,
        "max_retries": 2,
        "call_timeout_seconds": 30,
        "output_path": root / "test-artifacts" / "out.json",
        "env_file_given": False,
        "root": root,
    }
    values.update(overrides)  # Each test changes only the fields it names.
    return SmokeSettings(**values)  # Create the settings, which validate every field.


def make_context(  # Build a check context with the fake session and the real governor.
    session: FakeSession,
    settings: SmokeSettings,
    *,
    claims: RunbookClaims | None = None,
    openapi: OpenApiIndex | None = None,
    wait: Any = None,
    budget: int | None = None,
) -> CheckContext:
    """Return a run context whose client drives the fake session through the real governor.

    Args:
        session: Fake SDK session.
        settings: Validated settings of the test.
        claims: Runbook facts, or None.
        openapi: OpenAPI index, or None.
        wait: Replacement for the thread wait of the governor, or None for the default.
        budget: Request budget, or None to use the settings value.

    Returns:
        The run context, with the client already open.
    """
    governor_options: dict[str, Any] = {"sleep": lambda seconds: None, "requests_sent": 1}  # No real waits in tests.
    if wait is not None:  # A timeout test replaces the thread wait.
        governor_options["wait_for_thread"] = wait  # The replacement wait decides the timeout.
    governor = CallGovernor(  # Create the governor that counts each request and enforces the budget.
        session=session,
        request_budget=settings.max_requests if budget is None else budget,
        call_timeout_seconds=float(settings.call_timeout_seconds),
        max_retries=settings.max_retries,
        **governor_options,
    )
    redactor = EvidenceRedactor(organization_id=ORG, site_ids=(SITE,), token_value=TOKEN)  # Evidence rules.
    context = CheckContext(  # Create the check context that holds the settings and the results.
        settings=settings,
        token=TOKEN,
        redactor=redactor,
        session_factory=lambda **kwargs: session,  # The fake session stands in for the SDK class.
        window_query={"start": "1000", "end": "2000"},
        claims=claims,
        openapi=openapi,
    )
    context.client = ReadOnlyMistClient(  # Attach the real client, as the open client step does.
        approved_host=HOST, governor=governor
    )  # The real client, as open_client sets it.
    return context  # Return the context with its client already attached.


def runbook_claims(  # Build runbook facts that pass the structure rules.
    endpoints: tuple[str, ...] = (),
    hosts: tuple[str, ...] = (HOST,),
    catalogs: dict[str, tuple[str, ...]] | None = None,
) -> RunbookClaims:
    """Return runbook facts that satisfy the structure rules, with the given endpoints and catalog names.

    Args:
        endpoints: Appendix A paths.
        hosts: Regional hosts of section 5.5.
        catalogs: Appendix B names per catalog key, or None for the names that script_catalogs serves.

    Returns:
        The runbook facts.
    """
    headings = ((1, RunbookStructure.REQUIRED_H1),) + tuple(  # List the required headings in the order of the contract.
        (2, text) for text in RunbookStructure.REQUIRED_H2
    )
    headings += tuple((3, text) for text in RunbookStructure.REQUIRED_H3)  # Every required heading, in order.
    names = (  # Serve the default names that the structure check expects, unless a test sets its own.
        catalogs
        if catalogs is not None
        else {  # One name per required table, which script_catalogs serves.
            "alarm_defs": ("alarm_defs-key",),
            "device_events": ("device_events-key",),
            "mxedge_events": ("mxedge_events-key",),
            "webhook_topics": ("webhook_topics-key",),
            "system_events": (),
        }
    )
    return RunbookClaims(  # Return the facts with the endpoints, the hosts, and the identifier fields.
        path=Path("runbook.md"),
        headings=headings,
        h2_headings=RunbookStructure.REQUIRED_H2,
        api_paths=endpoints,
        endpoint_paths=endpoints,
        catalog_names=names,
        regional_hosts=hosts,
        identifier_fields={
            "6.1 Alarm Search": ("id",),
            "6.2 Device Event Search": ("type",),
            "6.3 Mist Edge Event Search": ("mxedge_id",),
            "6.4 System Event Search": ("type",),
        },
    )


def script_searches(  # Script the four organization searches that SMK-06 and SMK-07 read.
    session: FakeSession, alarm_total: int = 1, device_next: Any = None
) -> None:
    """Queue one page of each organization search, with records that hold each identifier field.

    Args:
        session: Fake SDK session.
        alarm_total: Total of the alarm search, and the number of alarm records.
        device_next: Next link of the device event search, or None for a complete search.
    """
    alarms = [  # Each record holds the identifier fields that SMK-06 checks.
        {"id": f"a{i}", "status": "open", "severity": "critical", "group": "security", "acked": i % 2 == 0}
        for i in range(alarm_total)
    ]
    session.add(  # Script the alarm search reply, with its total and its time window.
        "/alarms/search", reply(data={"results": alarms, "total": alarm_total, "start": 1000, "end": 2000})
    )
    devices = {  # Build one device event record with its type and its device type.
        "results": [{"type": "device-key", "device_type": "ap", "ev_type": "warn"}],
        "total": 1,
    }
    session.add(  # Script the device event search reply, with the optional next link.
        "/devices/events/search", reply(data=devices, next_value=device_next)
    )
    mxedges = {  # Build one Mist Edge event record with its identifier.
        "results": [{"mxedge_id": "m1", "severity": "critical"}],
        "start": 1000,
        "end": 2000,
    }
    session.add("/mxedges/events/search", reply(data=mxedges))  # Script the Mist Edge event search reply.
    system = {  # Build one system event record with its type.
        "results": [{"type": "system-key"}],
        "total": 1,
        "start": 1000,
        "end": 2000,
    }
    session.add("/events/system/search", reply(data=system))  # Script the system event search reply.


def script_counts(  # Script the four organization counts that SMK-07 compares with the totals.
    session: FakeSession, alarm: int = 1, device: int = 1, system: int = 1
) -> None:
    """Queue one count reply for each organization count endpoint.

    Args:
        session: Fake SDK session.
        alarm: Count value of the alarm bucket.
        device: Count value of the device event bucket.
        system: Count value of the system event bucket.
    """
    session.add(  # Script the alarm count reply that SMK-07 sums.
        "/alarms/count", reply(data={"results": [{"count": alarm}], "total": 1})
    )
    session.add(  # Script the device event count reply that SMK-07 sums.
        "/devices/events/count", reply(data={"results": [{"count": device}], "total": 1})
    )
    session.add(  # Script an empty Mist Edge count, because Mist Edge events have no total.
        "/mxedges/events/count", reply(data={"results": [{"count": 0}], "total": 0})
    )
    session.add(  # Script the system event count reply that SMK-07 sums.
        "/events/system/count", reply(data={"results": [{"count": system}], "total": 1})
    )


def openapi_file(  # Write a small OpenAPI file that the identity check can read.
    root: Path, servers: tuple[str, ...] = (HOST,)
) -> Path:
    """Write a small OpenAPI file with the self endpoint and the given servers.

    Args:
        root: Folder to write into.
        servers: Host names of the servers list.

    Returns:
        The path of the written file.
    """
    document = {  # Build an OpenAPI document with the self path and the given servers.
        "openapi": "3.1.0",
        "paths": {"/api/v1/self": {"get": {"operationId": "getSelf"}}},
        "servers": [{"url": f"https://{host}"} for host in servers],
    }
    path = root / "openapi.json"  # The fixture file of the test.
    path.write_text(json.dumps(document), encoding="utf-8")  # Write the JSON text.
    return path  # Return the path of the fixture file.


# SMK-01: configuration and the OpenAPI file, before any session exists.


def test_smk_01_passes_with_a_readable_openapi_and_a_listed_host(  # Confirm that SMK-01 passes for a listed host.
    tmp_path: Path,
) -> None:
    """SMK-01 passes when the host is in the servers list and the OpenAPI file reads."""
    settings = make_settings(tmp_path, openapi_path=openapi_file(tmp_path))  # Real fixture file.
    context = make_context(FakeSession(), settings)  # Context with no client yet.
    result = IdentityChecks(context).smk_01()  # Run the configuration check.
    assert result.status is CheckStatus.PASS  # The configuration is valid.
    assert result.request_count == 0  # SMK-01 sends no request.
    assert result.detail == "token present, host in the server list, organization ID valid."  # Pin the contract text.


def test_smk_01_stops_when_the_host_is_not_in_the_servers_list(  # Confirm SMK-01 stops when the host is not listed.
    tmp_path: Path,
) -> None:
    """SMK-01 stops the run with exit code 2 when the host is outside the OpenAPI servers."""
    settings = make_settings(  # Build settings whose host is missing from the servers list.
        tmp_path, openapi_path=openapi_file(tmp_path, servers=("api.gc1.mist.com",))
    )
    with pytest.raises(StopRun) as caught:  # The host rule fails.
        IdentityChecks(make_context(FakeSession(), settings)).smk_01()  # Run SMK-01, which must stop on the host rule.
    assert caught.value.outcome is STOP.CONFIGURATION_ERROR  # A setup error exits 2, so the operator fixes the input.
    assert caught.value.result is not None and caught.value.result.status is CheckStatus.FAIL  # Named FAIL result.


def test_smk_01_stops_when_the_openapi_file_is_not_valid_json(  # Confirm that SMK-01 stops when the file is not JSON.
    tmp_path: Path,
) -> None:
    """SMK-01 stops the run with exit code 2 when the OpenAPI file cannot be read as JSON."""
    bad = tmp_path / "openapi.json"  # A file that is not JSON.
    bad.write_text("{not json", encoding="utf-8")  # Invalid text for the parser.
    with pytest.raises(StopRun) as caught:  # The file rule fails.
        IdentityChecks(  # Run SMK-01 on the broken file, which must stop the run.
            make_context(FakeSession(), make_settings(tmp_path, openapi_path=bad))
        ).smk_01()
    assert caught.value.outcome is STOP.CONFIGURATION_ERROR  # A setup error exits 2, so the operator fixes the input.


def test_smk_01_stops_when_an_explicit_runbook_is_missing(  # Confirm that SMK-01 stops for a missing named runbook.
    tmp_path: Path,
) -> None:
    """SMK-01 stops the run when the operator named a runbook that does not exist."""
    settings = make_settings(tmp_path, openapi_path=openapi_file(tmp_path), runbook_explicit=True)  # Missing.
    with pytest.raises(StopRun) as caught:  # The explicit runbook is required.
        IdentityChecks(make_context(FakeSession(), settings)).smk_01()  # Run SMK-01 with the missing explicit runbook.
    assert caught.value.outcome is STOP.CONFIGURATION_ERROR  # A setup error exits 2, so the operator fixes the input.


def test_smk_01_keeps_the_run_when_the_default_runbook_is_missing(  # Confirm a missing default runbook is not fatal.
    tmp_path: Path,
) -> None:
    """SMK-01 passes without runbook facts when the default runbook does not exist, so SMK-02 skips."""
    context = make_context(  # Build a context with no runbook, so the default case runs.
        FakeSession(), make_settings(tmp_path, openapi_path=openapi_file(tmp_path))
    )
    assert IdentityChecks(context).smk_01().status is CheckStatus.PASS  # The run goes on.
    assert context.claims is None  # No runbook facts exist, so the structure check skips.


def test_smk_01_parses_an_existing_runbook_into_the_context(  # Confirm that SMK-01 reads an existing runbook.
    tmp_path: Path,
) -> None:
    """SMK-01 reads an existing runbook once and shares its facts with the later checks."""
    (tmp_path / "runbook.md").write_text(  # Write a minimal runbook, so SMK-01 has one to read.
        "# MIST_NETCOOL_ALARM_INTEGRATION\n\n## 1. Overview\n", encoding="utf-8"
    )
    context = make_context(  # Build a context that points at the new runbook.
        FakeSession(), make_settings(tmp_path, openapi_path=openapi_file(tmp_path))
    )
    IdentityChecks(context).smk_01()  # Read the runbook.
    assert context.claims is not None and (1, "MIST_NETCOOL_ALARM_INTEGRATION") in context.claims.headings  # Shared.


# SMK-02: runbook structure, offline.


def test_smk_02_skips_when_the_runbook_is_absent() -> None:  # Confirm that SMK-02 skips without a runbook.
    """SMK-02 skips with the cause runbook not found, and sends no request."""
    context = make_context(  # Build a context with no runbook facts, so SMK-02 must skip.
        FakeSession(), make_settings(Path("."))
    )
    result = IdentityChecks(context).smk_02()  # Run SMK-02 on the context that has no facts.
    assert result.status is CheckStatus.SKIP and result.detail == "runbook not found"  # The contract cause.


def test_smk_02_passes_for_a_complete_runbook() -> None:  # Confirm that SMK-02 passes for a complete runbook.
    """SMK-02 passes when every heading, path, table, and host matches the contract and the OpenAPI file."""
    openapi = make_openapi(("/api/v1/self",))  # The OpenAPI file lists one GET path.
    claims = runbook_claims(("/api/v1/self",))  # Build runbook facts with one path that has a GET operation.
    context = make_context(  # Build a context with the complete facts and the matching OpenAPI index.
        FakeSession(), make_settings(Path(".")), claims=claims, openapi=openapi
    )
    result = IdentityChecks(context).smk_02()  # Run SMK-02 on the complete runbook.
    assert result.status is CheckStatus.PASS  # Every rule passed.
    assert result.detail == "all headings found, each path has a GET operation."  # Pin the contract text.


def test_smk_02_names_each_defect() -> None:  # Confirm that SMK-02 names each defect in its detail.
    """SMK-02 fails and names each defect: a missing heading, a path with no GET, an empty table, and a host."""
    base = runbook_claims(  # Build facts that are valid before each defect is added.
        ("/api/v1/self", "/api/v1/unknown")
    )
    broken_headings = tuple(  # Remove the first required H2 heading, so the facts hold one defect.
        item for item in base.headings if item[1] != RunbookStructure.REQUIRED_H2[0]
    )
    broken = RunbookClaims(  # Build facts with a missing heading, an empty table, and a host mismatch.
        path=base.path,
        headings=broken_headings,
        h2_headings=base.h2_headings,
        api_paths=base.api_paths,
        endpoint_paths=base.endpoint_paths,
        catalog_names={**base.catalog_names, "alarm_defs": ()},  # An empty required table.
        regional_hosts=("api.gc1.mist.com",),  # A host set that does not match the servers.
        identifier_fields=base.identifier_fields,
    )
    context = make_context(  # Build a context with the defective facts and an OpenAPI file with one path.
        FakeSession(), make_settings(Path(".")), claims=broken, openapi=make_openapi(("/api/v1/self",))
    )
    result = IdentityChecks(context).smk_02()  # Run SMK-02 on the defective facts.
    assert result.status is CheckStatus.FAIL  # At least one defect was found.
    for text in (  # Check that the detail names each expected defect.
        "missing heading ## 1. Overview",
        "no GET operation for /api/v1/unknown",
    ):
        assert text in result.detail  # Each heading and path defect is named in the detail.
    assert "empty Appendix B table for alarm_defs" in result.detail  # The empty table is named.
    assert "regional hosts missing from the runbook: api.mist.com" in result.detail  # The host mismatch is named.


# SMK-03: token access and the privilege rule.


def self_reply(privileges: list[dict[str, Any]]) -> FakeResponse:  # Return a self reply with the given privileges.
    """Return a HTTP 200 self response with the given privileges.

    Args:
        privileges: Privilege entries of the response.

    Returns:
        The scripted response.
    """
    return reply(  # Return the self reply with the privileges and an email field.
        data={"privileges": privileges, "email": "x"}
    )


def run_smk_03(session: FakeSession) -> CheckResult:  # Run SMK-03 with a fresh context and return its result.
    """Run SMK-03 with a fresh context and return its result.

    Args:
        session: Fake SDK session with the self reply queued.

    Returns:
        The result of SMK-03.
    """
    return IdentityChecks(  # Run the privilege check on the session that the test scripted.
        make_context(session, make_settings(Path(".")))
    ).smk_03()


def test_smk_03_passes_for_a_read_role_on_the_organization() -> None:  # Confirm that SMK-03 passes for a read role.
    """SMK-03 passes when an org-scope entry with the target org_id has the role read."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    session.add(  # Script the self reply with a read grant on the organization.
        "/api/v1/self", self_reply([{"scope": "org", "org_id": ORG, "role": "read"}])
    )
    result = run_smk_03(session)  # Run SMK-03 against the scripted self reply.
    assert (  # Confirm that the check passes and names the role and the organization.
        result.status is CheckStatus.PASS and result.detail == "role read, organization org-1 in the privileges."
    )
    assert result.http_statuses == (200,) and result.request_count == 1  # One counted request.


@pytest.mark.parametrize(
    ("privileges", "status", "text"),
    [
        ([{"scope": "org", "org_id": ORG, "role": "admin"}], CheckStatus.WARN, "role admin"),
        ([{"scope": "msp", "msp_id": "m"}], CheckStatus.WARN, "organization access can come from an MSP privilege"),
        (
            [{"scope": "org", "org_id": ORG, "role": "read"}, {"scope": "org", "role": "read"}],
            CheckStatus.WARN,
            "organization scope not confirmed",
        ),
    ],
)
def test_smk_03_warns_for_a_non_read_role_an_msp_scope_or_an_unconfirmed_scope(  # SMK-03 warns and the run goes on.
    privileges: list[dict[str, Any]], status: CheckStatus, text: str
) -> None:
    """SMK-03 gives WARN with the role or the reason, and the run goes on."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    session.add("/api/v1/self", self_reply(privileges))  # Script the self reply with the privileges of this case.
    result = run_smk_03(session)  # Run SMK-03 with the privileges of this case.
    assert result.status is status  # The warning status.
    assert text in result.detail  # The role name or the reason.


def test_smk_03_stops_when_only_an_unconfirmed_scope_exists_and_names_both_causes() -> None:  # Both causes are named.
    """An org entry without an org_id does not grant the organization, so the run stops with both causes named."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    session.add(  # Script an org grant that has no org identifier.
        "/api/v1/self", self_reply([{"scope": "org", "role": "read"}])
    )
    with pytest.raises(StopRun) as caught:  # No grant, so the run stops.
        run_smk_03(session)  # Run SMK-03, which must stop because no grant is confirmed.
    assert caught.value.outcome is STOP.CONFIGURATION_ERROR  # A setup error exits 2, so the operator fixes the input.
    assert (  # Confirm that the stop message names both causes.
        caught.value.message == "the token does not grant the organization; organization scope not confirmed"
    )


def test_smk_03_stops_with_exit_code_2_when_no_entry_grants_the_organization() -> (  # Confirm exit code 2 for no grant.
    None
):
    """SMK-03 stops the run with exit code 2 when no privilege grants the organization."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    session.add(  # Script a site-only grant, which does not grant the organization.
        "/api/v1/self", self_reply([{"scope": "site", "site_id": SITE, "role": "read"}])
    )
    with pytest.raises(StopRun) as caught:  # No grant.
        run_smk_03(session)  # Run SMK-03, which must stop on the site-only grant.
    assert caught.value.outcome is STOP.CONFIGURATION_ERROR  # A setup error exits 2, so the operator fixes the input.
    assert (  # Confirm that the stop carries the no-grant detail.
        caught.value.result is not None and caught.value.result.detail == "the token does not grant the organization"
    )


def test_smk_03_stops_on_http_401() -> None:  # Confirm that SMK-03 stops the run on an HTTP 401.
    """SMK-03 stops the run with exit code 2 when the API rejects the token with HTTP 401."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    session.add(  # Script an HTTP 401 for the self request.
        "/api/v1/self", reply(status=401, data={"detail": "unauthorized"})
    )
    with pytest.raises(StopRun) as caught:  # The request rule ends the run.
        run_smk_03(session)  # Run SMK-03, which must stop on the 401.
    assert caught.value.outcome is STOP.CONFIGURATION_ERROR  # A setup error exits 2, so the operator fixes the input.


def test_smk_03_fails_without_a_stop_on_http_403() -> None:  # Confirm that SMK-03 fails on HTTP 403, without a stop.
    """SMK-03 gives FAIL for HTTP 403, and the run goes on."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    session.add(  # Script an HTTP 403 for the self request.
        "/api/v1/self", reply(status=403, data={"detail": "forbidden"})
    )
    result = run_smk_03(session)  # Run SMK-03 on the 403, which must return a result.
    assert result.status is CheckStatus.FAIL and "HTTP 403" in result.detail  # FAIL without a stop.


# SMK-04: the hourly budget.


def run_smk_04(  # Run SMK-04 with a fresh context and the given request budget.
    session: FakeSession, max_requests: int = 60
) -> CheckResult:
    """Run SMK-04 with a fresh context and return its result.

    Args:
        session: Fake SDK session with the usage reply queued.
        max_requests: Request budget of the test run.

    Returns:
        The result of SMK-04.
    """
    return IdentityChecks(  # Run the budget check with the settings of the test.
        make_context(session, make_settings(Path("."), max_requests=max_requests))
    ).smk_04()


def usage(  # Build a usage reply with the given counts and limit.
    requests_used: Any = 100, limit: Any = 5000, seconds: Any = 1234
) -> FakeResponse:
    """Return a HTTP 200 usage response with the given values.

    Args:
        requests_used: Requests used in the hour.
        limit: Requests allowed in the hour.
        seconds: Seconds until the hour resets.

    Returns:
        The scripted response.
    """
    return reply(  # Return the usage reply in the form that the API sends.
        data={"requests": requests_used, "request_limit": limit, "seconds": seconds}
    )


def test_smk_04_passes_with_the_documented_limit_and_enough_budget() -> (  # Confirm that SMK-04 passes with limit 5000.
    None
):
    """SMK-04 passes when the limit is 5000 and the remaining budget is at least two runs."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    session.add("/api/v1/self/usage", usage())  # Script the default usage reply, which has the documented limit.
    result = run_smk_04(session)  # Run SMK-04 against the default usage reply.
    assert result.status is CheckStatus.PASS  # Enough budget.
    assert result.detail == "100 of 5000 requests used, 4900 remaining, seconds 1234."  # Facts of the hour.


def test_smk_04_warns_for_a_different_limit_and_names_both_values() -> (  # Confirm that SMK-04 warns for another limit.
    None
):
    """SMK-04 gives WARN with both values when the request limit is not 5000."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    session.add("/api/v1/self/usage", usage(limit=1000))  # Script a usage reply with a limit of 1000.
    result = run_smk_04(session)  # Run SMK-04 against the 1000 limit.
    assert result.status is CheckStatus.WARN and "limit is 1000, not 5000" in result.detail  # Both values.


def test_smk_04_warns_when_the_usage_values_are_not_readable() -> None:  # Confirm SMK-04 warns for an unreadable value.
    """SMK-04 gives WARN, and the run goes on, when a usage value has the wrong type."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    session.add(  # Script a usage reply with a text count, which is not readable.
        "/api/v1/self/usage", usage(requests_used="many")
    )
    result = run_smk_04(session)  # Run SMK-04 on the unreadable usage reply.
    assert result.status is CheckStatus.WARN and result.detail == "the hourly usage was not readable"  # Contract text.


def test_smk_04_stops_with_exit_code_3_when_the_remaining_budget_is_low() -> (  # Confirm SMK-04 stops on a low budget.
    None
):
    """SMK-04 stops the run with exit code 3 when fewer than two budgets remain."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    session.add("/api/v1/self/usage", usage(requests_used=4950))  # 50 remaining, below 2 * 60.
    with pytest.raises(StopRun) as caught:  # The low budget ends the run.
        run_smk_04(session)  # Run SMK-04 with 50 requests left, which must stop the run.
    assert caught.value.outcome is STOP.RATE_LIMIT_STOP  # Rate limit exits 3, so the operator waits before rerun.
    assert caught.value.result is not None and caught.value.result.status is CheckStatus.FAIL  # The FAIL result.


def test_smk_04_stops_with_exit_code_3_on_a_final_http_429() -> None:  # Confirm that SMK-04 stops on a final HTTP 429.
    """SMK-04 stops the run with exit code 3 when the final attempt is HTTP 429."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    session.add(  # Script an HTTP 429 for the usage request.
        "/api/v1/self/usage", reply(status=429, data={"detail": "slow down"})
    )
    with pytest.raises(StopRun) as caught:  # The throttle ends the run.
        run_smk_04(session)  # Run SMK-04, which must stop on the final 429.
    assert caught.value.outcome is STOP.RATE_LIMIT_STOP  # Rate limit exits 3, so the operator waits before rerun.


# SMK-05: definition catalogs and the Appendix B names.


CATALOG_PATHS = (  # List the six catalog paths in the order of the contract.
    "/api/v1/const/alarm_defs",
    "/api/v1/const/device_events",
    "/api/v1/const/mxedge_events",
    "/api/v1/const/system_events",
    "/api/v1/const/ap_led_status",
    "/api/v1/const/webhook_topics",
)


def script_catalogs(  # Keep each catalog non-empty, so only a test change fails SMK-05.
    session: FakeSession, keys: dict[str, tuple[str, ...]] | None = None
) -> None:
    """Queue one non-empty catalog array for each of the six catalog paths.

    Args:
        session: Fake SDK session.
        keys: Item keys per catalog name, or None for one key each.
    """
    for path in CATALOG_PATHS:  # Each catalog in the contract order.
        name = path.rsplit("/", 1)[-1]  # The catalog key is the last path segment.
        held = (keys or {}).get(name, (f"{name}-key",))  # The keys that this catalog holds.
        items = [{"key": key, "display": key, "example": {"secret": "x"}} for key in held]  # Items with an example.
        session.add(path, reply(data=items))  # Script the catalog reply for this path.


def test_smk_05_passes_when_each_runbook_name_is_a_live_key() -> None:  # Confirm that SMK-05 passes with live names.
    """SMK-05 passes, names the fields, and keeps the item count of each catalog for the evidence."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    script_catalogs(session)  # Script one key for each catalog, which matches the runbook names.
    names: dict[str, tuple[str, ...]] = {  # Every Appendix B table holds one name, so none is absent.
        "alarm_defs": ("alarm_defs-key",),
        "device_events": ("device_events-key",),
        "mxedge_events": ("mxedge_events-key",),
        "webhook_topics": ("webhook_topics-key",),
        "system_events": ("system_events-key",),
    }
    context = make_context(  # Build the context, so SMK-05 matches the live keys.
        session, make_settings(Path(".")), claims=runbook_claims(catalogs=names)
    )
    result = CatalogChecks(context).smk_05()  # Run SMK-05 on the matching names.
    assert result.status is CheckStatus.PASS and result.request_count == 6  # Six catalog requests.
    assert result.detail == "6 catalogs not empty, all runbook names found."  # Pin the contract text.
    assert result.field_names == ("display", "key")  # Field names only, without the example member.
    assert context.catalogs["alarm_defs"]["item_count"] == 1  # The count of the catalog is kept for the evidence.


def test_smk_05_fails_and_names_a_runbook_name_that_is_not_a_live_key() -> (  # Confirm SMK-05 names each missing name.
    None
):
    """SMK-05 gives FAIL and names the missing value when a runbook name is not in its catalog."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    script_catalogs(  # Script an alarm catalog that lacks the runbook name.
        session, keys={"alarm_defs": ("other-key",)}
    )
    result = CatalogChecks(  # Run SMK-05 against the mismatched catalog.
        make_context(session, make_settings(Path(".")), claims=runbook_claims())
    ).smk_05()
    assert (  # Confirm that the detail names the missing runbook name.
        result.status is CheckStatus.FAIL and "missing runbook names: alarm_defs alarm_defs-key" in result.detail
    )


def test_smk_05_fails_on_an_empty_catalog() -> None:  # Confirm that SMK-05 fails on an empty catalog.
    """SMK-05 gives FAIL when a catalog is an empty array."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    script_catalogs(session)  # Script the default catalogs before the empty one replaces one.
    session.script = [item for item in session.script if not item[0].endswith("device_events")]  # Drop one reply.
    session.add("/api/v1/const/device_events", reply(data=[]))  # An empty catalog.
    result = CatalogChecks(  # Run SMK-05 with the empty catalog.
        make_context(session, make_settings(Path(".")))
    ).smk_05()
    assert result.status is CheckStatus.FAIL and "device_events is empty" in result.detail  # Named empty catalog.


def test_smk_05_skips_the_name_comparison_without_a_runbook() -> None:  # Confirm that SMK-05 skips only the name check.
    """SMK-05 still requests the six catalogs, and skips only the name comparison."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    script_catalogs(session)  # Script the six catalogs, which SMK-05 still requests.
    result = CatalogChecks(  # Run SMK-05 with no runbook facts.
        make_context(session, make_settings(Path(".")))
    ).smk_05()
    assert result.status is CheckStatus.SKIP and result.request_count == 6  # Requests run, names skip.
    assert "runbook not found" in result.detail  # The skip cause.


def test_smk_05_reports_info_when_appendix_b4_is_absent() -> None:  # Confirm that SMK-05 gives INFO without B.4.
    """SMK-05 gives INFO, not FAIL, when the runbook has no Appendix B.4 names."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    script_catalogs(session)  # Script the six catalogs for the Appendix B.4 case.
    result = CatalogChecks(  # Run SMK-05 with facts that have no B.4 names.
        make_context(session, make_settings(Path(".")), claims=runbook_claims())
    ).smk_05()
    assert result.status is CheckStatus.INFO and "Appendix B.4 is absent" in result.detail  # Observation only.


def test_smk_05_fails_on_an_http_error_status() -> (  # Confirm that SMK-05 fails on a catalog that answers HTTP 404.
    None
):
    """SMK-05 gives FAIL with the class of a catalog that answers HTTP 404, and keeps its status in order."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    script_catalogs(session)  # Script the six catalogs before one of them is replaced with a 404.
    session.script = [  # Remove the default reply of the led status catalog.
        item for item in session.script if not item[0].endswith("ap_led_status")
    ]
    session.add(  # Script an HTTP 404 for the led status catalog.
        "/api/v1/const/ap_led_status", reply(status=404, data={"detail": "gone"})
    )
    result = CatalogChecks(make_context(session, make_settings(Path(".")))).smk_05()  # Run SMK-05 on the 404 catalog.
    assert result.status is CheckStatus.FAIL and "ap_led_status returned HttpError" in result.detail  # The class.
    assert result.http_statuses[4] == 404  # The status is kept in request order.


def test_smk_05_fails_on_an_empty_body_and_names_the_error_class() -> None:  # HTTP 200 with no body text.
    """SMK-05 gives FAIL with EmptyBody when a 200 catalog answer holds no body text, and it does not retry."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    script_catalogs(session)  # Script the six catalogs before one of them is replaced with an empty body.
    session.script = [item for item in session.script if not item[0].endswith("ap_led_status")]  # Drop default reply.
    empty_reply = FakeResponse(status_code=200, data={}, raw_data="")  # HTTP 200 with no body text.
    session.add("/api/v1/const/ap_led_status", empty_reply)  # The catalog answers with the empty reply.
    result = CatalogChecks(make_context(session, make_settings(Path(".")))).smk_05()  # Run the catalog part.
    assert result.status is CheckStatus.FAIL  # The catalog part fails on the empty body.
    assert "ap_led_status returned EmptyBody" in result.detail  # The error class is named in the detail.
    assert result.http_statuses[4] == 200  # The status is kept, so the defect is the body and not the status.
    assert result.request_count == 6  # Each catalog is requested once, because EmptyBody is never retried.


def test_smk_05_fails_on_a_malformed_body_and_names_the_error_class() -> None:  # HTTP 200, text not JSON.
    """SMK-05 gives FAIL with MalformedJson for a 200 catalog answer whose text is not JSON."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    script_catalogs(session)  # Script the six catalogs before one of them is replaced with a malformed body.
    session.script = [item for item in session.script if not item[0].endswith("ap_led_status")]  # Drop default reply.
    malformed_reply = FakeResponse(status_code=200, data={}, raw_data="bad json")  # HTTP 200, body text not JSON.
    session.add("/api/v1/const/ap_led_status", malformed_reply)  # The catalog answers with the malformed reply.
    result = CatalogChecks(make_context(session, make_settings(Path(".")))).smk_05()  # Run the catalog part.
    assert result.status is CheckStatus.FAIL  # The catalog part fails on the malformed body.
    assert "ap_led_status returned MalformedJson" in result.detail  # The error class is named in the detail.
    assert result.http_statuses[4] == 200  # The status is kept, so the defect is the body and not the status.
    assert result.request_count == 6  # Each catalog is requested once, because MalformedJson is never retried.


# SMK-06, SMK-07: organization searches and counts.


def test_smk_06_passes_with_records_and_identifier_fields() -> (  # Confirm that SMK-06 passes with identifier records.
    None
):
    """SMK-06 passes when each family returns records that hold its identifier field."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    script_searches(session)  # Script one record for each organization search.
    context = make_context(  # Build the context, so the check reads each identifier field.
        session, make_settings(Path(".")), claims=runbook_claims()
    )
    result = SearchChecks(context).smk_06()  # Run SMK-06 on the scripted searches.
    assert result.status is CheckStatus.PASS and result.request_count == 4  # Four family queries.
    assert result.record_count == 4 and result.page_count == 4  # One record and one page for each family.
    assert context.observations["q1_device_type_default"] == {"device_types_seen": ["ap"], "only_ap": True}  # q1.
    assert context.observations["q8_alarm_status_values"]["alarms"]["acked"] == {"true": 1, "false": 0}  # q8.
    assert context.observations["q2_mist_edge_window"]["echoes_start_end"] is True  # q2, with the window sent.


def test_smk_06_warns_for_zero_records_and_says_so() -> None:  # Confirm that SMK-06 warns for zero alarm records.
    """SMK-06 gives WARN with the zero-record text, which does not prove that no event exists."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    session.add("/alarms/search", reply(data={"results": [], "total": 0}))  # Script an alarm search with no records.
    session.add(  # Script one device event row, so the device family has data.
        "/devices/events/search", reply(data={"results": [{"type": "d", "device_type": "ap"}], "total": 1})
    )
    session.add(  # Keep this family valid, so the case under test is the only defect.
        "/mxedges/events/search", reply(data={"results": [{"mxedge_id": "m"}]})
    )
    session.add(  # Script one system event row, so the system family has data.
        "/events/system/search", reply(data={"results": [{"type": "s"}], "total": 1})
    )
    result = SearchChecks(  # Run SMK-06 with the zero-record alarm search.
        make_context(session, make_settings(Path(".")), claims=runbook_claims())
    ).smk_06()
    assert result.status is CheckStatus.WARN  # Confirm that the zero-record case warns.
    assert result.detail.startswith("zero records for alarms in the collection window")  # The first warning.
    assert result.detail.endswith("do not prove that no event exists.")  # The contract note.


def test_smk_06_fails_when_an_identifier_field_is_in_no_record() -> (  # Confirm SMK-06 fails for a missing id field.
    None
):
    """SMK-06 gives FAIL when the alarm records lack the runbook identifier field."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    session.add(  # Script an alarm record that lacks the id field.
        "/alarms/search", reply(data={"results": [{"status": "open"}], "total": 1})
    )
    session.add(  # Script one device event row, so the device family has data.
        "/devices/events/search", reply(data={"results": [{"type": "d"}], "total": 1})
    )
    session.add(  # Keep this family valid, so the case under test is the only defect.
        "/mxedges/events/search", reply(data={"results": [{"mxedge_id": "m"}]})
    )
    session.add(  # Script one system event row, so the system family has data.
        "/events/system/search", reply(data={"results": [{"type": "s"}], "total": 1})
    )
    result = SearchChecks(  # Run SMK-06 on the alarm record without the id field.
        make_context(session, make_settings(Path(".")), claims=runbook_claims())
    ).smk_06()
    assert (  # Confirm that the detail names the missing identifier field.
        result.status is CheckStatus.FAIL and "alarms identifier field id is in no record." in result.detail
    )


def test_smk_06_warns_with_the_page_ceiling_and_keeps_the_stop_reason() -> None:  # SMK-06 warns at the page ceiling.
    """SMK-06 gives WARN with the PageCeiling reason when a next link remains after the last allowed page."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    link = "/api/v1/orgs/x/alarms/search?search_after={}"  # Build the next link template that the alarm pages follow.
    session.add(  # Script the first alarm page, with a next link.
        "/alarms/search", reply(data={"results": [{"id": "a"}], "total": 9}, next_value=link.format(1))
    )
    session.add(  # Script the second alarm page, with a next link.
        "/alarms/search", reply(data={"results": [{"id": "b"}], "total": 9}, next_value=link.format(2))
    )
    session.add(  # Script the third alarm page, with a next link.
        "/alarms/search", reply(data={"results": [{"id": "c"}], "total": 9}, next_value=link.format(3))
    )
    session.add(  # Script one device event row, so the device family has data.
        "/devices/events/search", reply(data={"results": [{"type": "d"}], "total": 1})
    )
    session.add(  # Keep this family valid, so the case under test is the only defect.
        "/mxedges/events/search", reply(data={"results": [{"mxedge_id": "m"}]})
    )
    session.add(  # Script one system event row, so the system family has data.
        "/events/system/search", reply(data={"results": [{"type": "s"}], "total": 1})
    )
    context = make_context(  # Build a context that allows three pages per query.
        session, make_settings(Path("."), max_pages=3), claims=runbook_claims()
    )
    result = SearchChecks(context).smk_06()  # Run SMK-06, which must stop at the page ceiling.
    assert result.status is CheckStatus.WARN and result.stop_reason == "PageCeiling"  # The ceiling warning.
    assert result.page_count == 3 + 1 + 1 + 1  # Three alarm pages, then one page for each other family.


def test_smk_06_stops_the_run_on_a_foreign_next_link() -> None:  # Confirm that SMK-06 stops on a foreign next link.
    """SMK-06 stops the run with exit code 5 when a next link leaves the approved origin."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    foreign = "https://evil.example/api/v1/x"  # Build a next link that leaves the approved origin.
    session.add(  # Script an alarm page whose next link is foreign.
        "/alarms/search", reply(data={"results": [{"id": "a"}], "total": 1}, next_value=foreign)
    )
    with pytest.raises(StopRun) as caught:  # The foreign link ends the run.
        SearchChecks(  # Run SMK-06, which must stop on the foreign link.
            make_context(session, make_settings(Path(".")), claims=runbook_claims())
        ).smk_06()
    assert caught.value.outcome is STOP.UNSAFE_PAGING_STOP  # Exit code 5.
    assert len(session.uris) == 1  # No request used the foreign link.


def test_smk_07_passes_when_each_total_equals_its_count_sum() -> (  # Confirm that SMK-07 passes with matching totals.
    None
):
    """SMK-07 passes for the three families with totals, and gives INFO for Mist Edge events."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    script_searches(session)  # Script the four organization searches with matching totals.
    script_counts(session)  # Script the four counts that sum to the totals.
    context = make_context(  # Build the context, so SMK-07 reads each count and total.
        session, make_settings(Path(".")), claims=runbook_claims()
    )
    SearchChecks(context).smk_06()  # The search pages that SMK-07 compares.
    result = SearchChecks(context).smk_07()  # Run SMK-07 after SMK-06 has read the searches.
    assert result.status is CheckStatus.INFO  # Mist Edge events have no total.
    assert "Mist Edge events have no total." in result.detail and "alarms equal" in result.detail  # Both parts.
    expected = {  # Name the expected count sum of each family.
        "alarms": 200,
        "device_events": 200,
        "mxedge_events": 200,
        "system_events": 200,
    }
    assert context.observations["q5_distinct_type"] == expected  # The count status of each family.


def test_smk_07_warns_when_a_total_differs_from_its_count_sum() -> (  # Confirm that SMK-07 warns for a total mismatch.
    None
):
    """SMK-07 gives WARN with both values when the alarm total and the count sum differ."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    script_searches(session, alarm_total=1)  # Script an alarm search with a total of one.
    script_counts(session, alarm=5)  # The count sum is 5, the search total is 1.
    context = make_context(  # Build the context, so SMK-07 reads each count and total.
        session, make_settings(Path(".")), claims=runbook_claims()
    )
    SearchChecks(context).smk_06()  # Run SMK-06 first, so SMK-07 has the searches to compare.
    result = SearchChecks(context).smk_07()  # Run SMK-07 against the mismatched total.
    assert (  # Confirm that the warning names both values.
        result.status is CheckStatus.WARN and "alarms search total 1 differs from the count sum 5" in result.detail
    )


def test_smk_07_skips_the_device_comparison_when_the_device_search_is_incomplete() -> (  # Skip an incomplete device.
    None
):
    """SMK-07 gives SKIP with the contract cause for device events when the device search has a next link."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    script_searches(  # Script a device search with a next link, so the search is incomplete.
        session, device_next="/api/v1/orgs/x/devices/events/search?search_after=9"
    )
    script_counts(session)  # Script the four counts for the comparison.
    context = make_context(  # Build a context that allows one page, so the device search stays incomplete.
        session, make_settings(Path("."), max_pages=1), claims=runbook_claims()
    )
    SearchChecks(context).smk_06()  # Run SMK-06 first, so SMK-07 has the searches to compare.
    result = SearchChecks(context).smk_07()  # Run SMK-07 with the incomplete device search.
    assert "device event search incomplete" in result.detail  # The contract cause of the skip.


def test_smk_07_fails_when_a_count_request_does_not_return_results() -> None:  # SMK-07 fails when a list is missing.
    """SMK-07 gives FAIL when the alarm count body has no results list."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    script_searches(session)  # Script the four organization searches first.
    session.add("/alarms/count", reply(data={"total": 1}))  # No results list.
    session.add(  # Script a device count with a results list.
        "/devices/events/count", reply(data={"results": [{"count": 1}]})
    )
    session.add(  # Script an empty Mist Edge count with a results list.
        "/mxedges/events/count", reply(data={"results": []})
    )
    session.add(  # Script a system count with a results list.
        "/events/system/count", reply(data={"results": [{"count": 1}]})
    )
    context = make_context(  # Build the context, so SMK-07 reads each count and total.
        session, make_settings(Path(".")), claims=runbook_claims()
    )
    SearchChecks(context).smk_06()  # Run SMK-06 first, so SMK-07 has the searches to compare.
    result = SearchChecks(context).smk_07()  # Run SMK-07 with the count reply that has no list.
    assert (  # Confirm that the detail names the alarm count defect.
        result.status is CheckStatus.FAIL and "alarms count did not return a results list." in result.detail
    )


# SMK-08, SMK-09, SMK-10: scope, filters, and inventory.


def script_site_searches(  # Script the four site searches, each with or without one record.
    session: FakeSession, records: bool = True
) -> None:
    """Queue one page of each site search, with or without records.

    Args:
        session: Fake SDK session.
        records: True when each site search returns one record.
    """
    rows = [{"id": "x"}] if records else []  # One record, or none.
    session.add(f"/sites/{SITE}/alarms/search", reply(data={"results": rows}))  # Script the site alarm search reply.
    session.add(  # Script the site device event search reply.
        f"/sites/{SITE}/devices/events/search", reply(data={"results": rows})
    )
    session.add(  # Script the site Mist Edge event search reply.
        f"/sites/{SITE}/mxedges/events/search", reply(data={"results": rows})
    )
    session.add(  # Script the site system event search reply.
        f"/sites/{SITE}/events/system/search", reply(data={"results": rows})
    )


def test_smk_08_passes_with_site_records_and_names_the_site_label() -> None:  # Confirm SMK-08 passes with site records.
    """SMK-08 passes when the four site searches return HTTP 200 with records, and prints the site-1 label."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    script_site_searches(session)  # Script the four site searches with one record each.
    result = ScopeChecks(  # Run SMK-08 with a configured site identifier.
        make_context(session, make_settings(Path("."), site_id=SITE))
    ).smk_08()
    assert (  # Confirm that the detail names the site label and not the identifier.
        result.status is CheckStatus.PASS and result.detail == "4 site searches returned HTTP 200 for site-1."
    )
    assert result.request_count == 4 and SITE not in result.detail  # No site identifier in the output.


def test_smk_08_skips_when_the_organization_has_no_site() -> None:  # Confirm that SMK-08 skips with no site.
    """SMK-08 skips with the contract cause when the site list is empty and no site was given."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    session.add(f"/orgs/{ORG}/sites", reply(data=[]))  # Script an empty site list for the organization.
    result = ScopeChecks(make_context(session, make_settings(Path(".")))).smk_08()  # Run SMK-08 with no site to read.
    assert (  # Confirm that the skip names its cause.
        result.status is CheckStatus.SKIP and result.detail == "no site in organization"
    )


def test_smk_08_reads_the_first_site_when_no_site_was_given_and_warns_on_zero_records() -> None:  # Read the first site.
    """SMK-08 reads the first site of the list, five requests in all, and warns for a site with no records."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    session.add(  # Script a site list whose first site is the one to read.
        f"/orgs/{ORG}/sites", reply(data=[{"id": SITE}, {"id": "other"}])
    )
    script_site_searches(session, records=False)  # Script the four site searches with no records.
    result = ScopeChecks(  # Run SMK-08 without a configured site.
        make_context(session, make_settings(Path(".")))
    ).smk_08()
    assert result.status is CheckStatus.WARN and result.request_count == 5  # The list plus four searches.
    assert "zero records for alarms in the site-1 collection window" in result.detail  # Zero-record warning.


def script_filters(  # The replies must follow the request order of SMK-09.
    session: FakeSession, first_types: list[str], switch_types: list[str] | None = None
) -> None:
    """Queue the six SMK-09 replies in request order.

    Args:
        session: Fake SDK session.
        first_types: Types of the records of request 1.
        switch_types: Types of the switch page, or None for an empty page.
    """
    records = [{"type": item} for item in first_types]  # Records of request 1.
    session.add("/devices/events/search", reply(data={"results": records}))  # Request 1: the type filter.
    probe = {"results": [{"type": "k"}], "limit": 1000, "next": "/x"}  # Request 2, with a smaller page.
    session.add("/devices/events/search", reply(data=probe))  # Script the second request, a probe with a smaller page.
    session.add(  # Script the switch page, which lists the switch types.
        "/devices/events/search", reply(data={"results": [{"type": t} for t in (switch_types or [])]})
    )
    session.add("/devices/events/search", reply(data={"results": []}))  # Request 4: the gateway page.
    session.add("/mxedges/events/search", reply(data={"results": [], "start": 1000, "end": 2000}))  # Duration probe.
    session.add("/mxedges/events/search", reply(data={"results": [], "start": 7, "end": 9}))  # Bare probe.


def test_smk_09_passes_when_the_type_filter_returns_only_its_types() -> (  # Confirm SMK-09 passes for a clean filter.
    None
):
    """SMK-09 passes when request 1 returns only the two filter types, and the probes record their answers."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    catalog_keys = ["ap-key", "gw-key", "sw-key"]  # The catalog has three keys; the filter takes the first two.
    context = make_context(  # Build a context whose catalog holds the device event keys.
        session, make_settings(Path("."))
    )
    context.catalogs["device_events"] = {  # Put the three catalog keys into the device event catalog.
        "items": [{"key": key} for key in catalog_keys]
    }
    script_filters(  # Script the filter request and the switch page.
        session, first_types=["ap-key", "gw-key"], switch_types=["sw-key"]
    )
    result = ScopeChecks(context).smk_09()  # Run SMK-09 on the scripted filter.
    assert result.status is CheckStatus.PASS and result.request_count == 6  # Six requests, as the contract says.
    assert (  # Confirm that the detail states the filter result and the limit.
        result.detail == "type filter returned only the filter types, limit 1000 gave HTTP 200."
    )
    assert context.observations["q3_limit_5000"] == {  # Confirm that the 5000 limit probe kept its reduced page size.
        "outcome": "reduced",
        "status_code": 200,
        "page_limit": 1000,
    }
    assert context.observations["device_event_types_by_device_type"] == {  # Record the types of each device type.
        "switch": ["sw-key"],
        "gateway": [],
    }
    assert context.observations["q2_mist_edge_window"]["with_duration_1h"] == {  # Confirm the duration probe window.
        "start": 1000,
        "end": 2000,
    }
    assert context.observations["q2_mist_edge_window"]["without_time_parameter"] == {  # Confirm the bare probe window.
        "start": 7,
        "end": 9,
    }


def test_smk_09_fails_when_a_type_outside_the_filter_is_returned() -> None:  # Confirm SMK-09 fails for an outside type.
    """SMK-09 gives FAIL when request 1 returns a type that the filter does not name."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    context = make_context(session, make_settings(Path(".")))  # Build a context for the filter check.
    context.catalogs["device_events"] = {  # Put two catalog keys into the device event catalog.
        "items": [{"key": "ap-key"}, {"key": "gw-key"}]
    }
    script_filters(session, first_types=["ap-key", "other-key"])  # Script a first page with a type outside the filter.
    result = ScopeChecks(context).smk_09()  # Run SMK-09 on the page with the outside type.
    assert (  # Confirm that the detail names the outside type.
        result.status is CheckStatus.FAIL and "outside the filter: other-key" in result.detail
    )


def test_smk_09_warns_for_zero_records_and_fails_for_a_non_200_first_request() -> (  # Confirm SMK-09 warns and fails.
    None
):
    """SMK-09 gives WARN for zero records from request 1, and FAIL for a request 1 that is not HTTP 200."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    context = make_context(session, make_settings(Path(".")))  # Build a context for the zero-record case.
    context.catalogs["device_events"] = {  # Put one catalog key into the device event catalog.
        "items": [{"key": "ap-key"}]
    }
    script_filters(session, first_types=[])  # Script a first page with no records.
    assert ScopeChecks(context).smk_09().status is CheckStatus.WARN  # Zero records, so the filter is not proven.
    other = FakeSession()  # Start a second session for the HTTP 400 case.
    other_context = make_context(other, make_settings(Path(".")))  # Build a context for the HTTP 400 case.
    other_context.catalogs["device_events"] = {  # Put one catalog key into the device event catalog for this case.
        "items": [{"key": "ap-key"}]
    }
    other.add(  # Script an HTTP 400 for the first request.
        "/devices/events/search", reply(status=400, data={"detail": "bad"})
    )
    other.add("/devices/events/search", reply(status=422, data={"detail": "bad"}))  # Probe, rejected.
    other.add("/devices/events/search", reply(data={"results": []}))  # Script an empty device page for the later probe.
    other.add(  # Script a second empty device page for the later probe.
        "/devices/events/search", reply(data={"results": []})
    )
    other.add(  # Script an empty Mist Edge page for the later probe.
        "/mxedges/events/search", reply(data={"results": []})
    )
    other.add(  # Script a second empty Mist Edge page for the later probe.
        "/mxedges/events/search", reply(data={"results": []})
    )
    result = ScopeChecks(other_context).smk_09()  # Run SMK-09 on the HTTP 400 first request.
    assert result.status is CheckStatus.FAIL  # Request 1 was HTTP 400.
    assert other_context.observations[  # Confirm that the rejected 5000 probe keeps its status code.
        "q3_limit_5000"
    ] == {
        "outcome": "rejected",
        "status_code": 422,
        "page_limit": None,
    }


def test_smk_09_skips_when_the_device_catalog_holds_no_key() -> (  # Confirm that SMK-09 skips with an empty catalog.
    None
):
    """SMK-09 skips without a request when the device event catalog is empty."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    context = make_context(session, make_settings(Path(".")))  # Build a context for the empty catalog case.
    context.catalogs["device_events"] = {"items": []}  # Put no keys into the device event catalog.
    result = ScopeChecks(context).smk_09()  # Run SMK-09 with no catalog key.
    assert (  # Confirm that the skip sends no request.
        result.status is CheckStatus.SKIP and result.request_count == 0 and session.uris == []
    )


def test_smk_10_passes_and_answers_q6_from_the_statistics() -> None:  # Confirm that SMK-10 passes and answers q6.
    """SMK-10 passes with HTTP 200 on six calls, sums each inventory type, and answers q6."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    session.add(  # Script the access point count, which has two results.
        "/inventory/count", reply(data={"results": [{"count": 3}, {"count": 2}]})
    )
    session.add("/inventory/count", reply(data={"results": [{"count": 1}]}))  # Script the switch count.
    session.add("/inventory/count", reply(data={"results": [{"count": 4}]}))  # Script the gateway count.
    session.add("/mxedges", reply(data=[{"id": "m", "name": "x"}]))  # Script one Mist Edge item in the list.
    session.add(  # Script one statistics item that holds the last trouble field.
        "/stats/devices", reply(data=[{"last_trouble": {"type": "t"}}])
    )
    webhooks = [  # Build two webhooks, one enabled and one disabled, with a secret.
        {"topics": ["alarms"], "enabled": True, "url": "https://u", "secret": "s"},
        {"topics": ["alarms"], "enabled": False},
    ]
    session.add("/webhooks", reply(data=webhooks))  # Script the webhook list.
    context = make_context(session, make_settings(Path(".")))  # Build a context for the inventory check.
    result = InventoryChecks(context).smk_10()  # Run SMK-10 on the scripted inventory.
    assert result.status is CheckStatus.PASS and result.request_count == 6  # Six requests in all.
    assert result.detail.startswith("6 calls returned HTTP 200.") and "ap devices 5." in result.detail  # 3 + 2.
    assert "enabled 1, disabled 1" in result.detail and "https://u" not in result.detail  # No URL, no secret.
    assert context.observations["q6_last_trouble_present"] is True  # The field is present.
    assert result.field_names == ("enabled", "id", "last_trouble", "name", "topics")  # Names only, sorted.


def test_smk_10_gives_info_and_warn_for_empty_mxedge_webhook_and_stats_lists() -> (  # Confirm INFO and WARN results.
    None
):
    """SMK-10 gives INFO for zero Mist Edge items and webhooks, WARN for zero statistics items, and q6 null."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    session.add("/inventory/count", reply(data={"results": []}))  # Script an empty access point count.
    session.add("/inventory/count", reply(data={"results": []}))  # Script an empty switch count.
    session.add("/inventory/count", reply(data={"results": []}))  # Script an empty gateway count.
    session.add("/mxedges", reply(data=[]))  # Script an empty Mist Edge list.
    session.add("/stats/devices", reply(data=[]))  # Script an empty statistics list.
    session.add("/webhooks", reply(data=[]))  # Script an empty webhook list.
    context = make_context(session, make_settings(Path(".")))  # Build a context for the empty lists.
    result = InventoryChecks(context).smk_10()  # Run SMK-10 on the empty lists.
    assert result.status is CheckStatus.WARN  # The statistics warning is the most severe.
    assert (  # Confirm that the detail names the empty statistics and webhook lists.
        "no AP statistics items." in result.detail and "no webhooks." in result.detail
    )
    assert context.observations["q6_last_trouble_present"] is None  # No item, so q6 stays null.


def test_smk_10_fails_when_a_list_request_is_not_an_array() -> None:  # Confirm that SMK-10 fails for an object list.
    """SMK-10 gives FAIL when the Mist Edge list answers with an object."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    for _ in range(3):  # Script three inventory counts, one for each inventory type.
        session.add(  # Answer each count, so only the list request fails.
            "/inventory/count", reply(data={"results": [{"count": 1}]})
        )
    session.add("/mxedges", reply(data={"results": []}))  # An object, not an array.
    session.add("/stats/devices", reply(data=[{"x": 1}]))  # Script one statistics item.
    session.add("/webhooks", reply(data=[]))  # Script an empty webhook list.
    result = InventoryChecks(  # Run SMK-10 on the object-shaped Mist Edge list.
        make_context(session, make_settings(Path(".")))
    ).smk_10()
    assert (  # Confirm that the detail names the non-array Mist Edge response.
        result.status is CheckStatus.FAIL and "Mist Edge items response is not a JSON array." in result.detail
    )


# Run stops that every check shares.
# The stops are HTTP 401, a final 429, a spent budget, a second timeout, and a repeated page.


def test_a_401_on_any_request_stops_the_run_with_exit_code_2() -> (  # Confirm that an HTTP 401 stops the run, exit 2.
    None
):
    """A HTTP 401 on a catalog request stops the run with exit code 2."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    session.add(  # Script an HTTP 401 for the alarm catalog request.
        "/api/v1/const/alarm_defs", reply(status=401, data={"detail": "no"})
    )
    with pytest.raises(StopRun) as caught:  # The stop is raised by the context.
        CatalogChecks(  # Run SMK-05, which must stop on the 401.
            make_context(session, make_settings(Path(".")))
        ).smk_05()
    assert caught.value.outcome is STOP.CONFIGURATION_ERROR  # A setup error exits 2, so the operator fixes the input.


def test_a_final_429_stops_the_run_with_exit_code_3() -> None:  # Confirm that a final HTTP 429 stops the run.
    """A final HTTP 429 on a catalog request stops the run with exit code 3."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    session.add(  # Script an HTTP 429 for the alarm catalog request.
        "/api/v1/const/alarm_defs", reply(status=429, data={"detail": "slow"})
    )
    with pytest.raises(StopRun) as caught:  # The throttle ends the run.
        CatalogChecks(  # Run SMK-05, which must stop on the 429.
            make_context(session, make_settings(Path(".")))
        ).smk_05()
    assert caught.value.outcome is STOP.RATE_LIMIT_STOP  # Rate limit exits 3, so the operator waits before rerun.


def test_a_spent_budget_stops_the_run_with_exit_code_4() -> None:  # Confirm that a spent budget stops the run.
    """A request after the budget is spent stops the run with exit code 4, and no request is sent."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    context = make_context(session, make_settings(Path("."), max_requests=2), budget=2)  # One unit left.
    session.add(  # Script the alarm catalog reply, which the budget allows.
        "/api/v1/const/alarm_defs", reply(data=[{"key": "k"}])
    )
    session.add(  # Script the device event reply, which the spent budget refuses.
        "/api/v1/const/device_events", reply(data=[{"key": "k"}])
    )
    with pytest.raises(StopRun) as caught:  # The second catalog request finds the budget spent.
        CatalogChecks(context).smk_05()  # Run SMK-05, which must stop before the second request.
    assert caught.value.outcome is STOP.BUDGET_STOP  # Exit code 4.
    assert session.uris == ["/api/v1/const/alarm_defs"]  # The refused request never reached the session.


def test_a_second_timeout_in_one_run_stops_with_exit_code_3() -> None:  # Confirm that a second timeout stops the run.
    """Two timeouts in one run stop the run with exit code 3, and a timeout is never retried."""
    release = threading.Event()  # Holds each fake call until the test releases it.
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    session.add("/api/v1/const/alarm_defs", release)  # The first call blocks, so the wait ends first.
    session.add("/api/v1/const/device_events", release)  # The second call blocks too.

    def never_finishes(  # Replace the thread wait, so each call counts as timed out at once.
        thread: threading.Thread, seconds: float
    ) -> None:
        """Return at once, so the worker thread is still alive and the call counts as timed out."""
        return None  # Return at once, which leaves the worker thread running.

    context = make_context(  # Build a context whose waits time out at once.
        session, make_settings(Path(".")), wait=never_finishes
    )
    try:  # The two timeouts happen across two catalog requests of the same run.
        with pytest.raises(StopRun) as caught:  # Expect the run to stop on the second timeout.
            CatalogChecks(context).smk_05()  # Run SMK-05, which makes two timed-out requests.
    finally:  # Release the blocked worker threads, so none is left behind.
        release.set()  # Release the blocked worker threads, so none stays alive.
    assert caught.value.outcome is STOP.RATE_LIMIT_STOP  # Rate limit exits 3, so the operator waits before rerun.
    assert context.client is not None and context.client.timeouts == 2  # Both timeouts were counted.
    assert session.uris == ["/api/v1/const/alarm_defs", "/api/v1/const/device_events"]  # No retry of a timeout.


def test_a_repeated_page_stops_the_run_with_exit_code_5() -> None:  # Confirm that a repeated next link stops the run.
    """A page whose next link repeats an earlier link stops the run with exit code 5."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    link = "/api/v1/orgs/x/alarms/search?search_after=1"  # Build one next link that both alarm pages return.
    session.add(  # The first page links to the shared URL, which the query follows once.
        "/alarms/search", reply(data={"results": [{"id": "a"}], "total": 2}, next_value=link)
    )
    session.add(  # The second page repeats the link, so the query must stop.
        "/alarms/search", reply(data={"results": [{"id": "b"}], "total": 2}, next_value=link)
    )
    with pytest.raises(StopRun) as caught:  # The repeated link ends the query.
        SearchChecks(  # Run SMK-06, which must stop on the repeated link.
            make_context(session, make_settings(Path(".")), claims=runbook_claims())
        ).smk_06()
    assert caught.value.outcome is STOP.UNSAFE_PAGING_STOP  # Exit code 5.


def test_q7_records_headers_and_retry_after_from_every_attempt() -> (  # Confirm that the evidence keeps the headers.
    None
):
    """Each sent attempt contributes its header names and Retry-After values."""
    session = FakeSession()  # Use a fake session, so no request reaches Mist.
    session.add(  # Script the alarm catalog with a 500 reply, then a success.
        "/api/v1/const/alarm_defs",
        reply(status=500, data={"detail": "x"}, headers={"X-RateLimit-Limit": "5"}),  # Retried once by the client.
        reply(data=[{"key": "alarm_defs-key"}], headers={"Retry-After": "soon"}),
    )
    for path in CATALOG_PATHS[1:]:  # The other catalogs answer with one key each.
        session.add(  # Script one key for each of the other catalog paths.
            path, reply(data=[{"key": f"{path.rsplit('/', 1)[-1]}-key"}])
        )
    context = make_context(session, make_settings(Path(".")))  # Build a context that keeps the headers of each attempt.
    CatalogChecks(context).smk_05()  # Run SMK-05, so the retry and its headers are recorded.
    names = sorted(  # Collect the header names that the attempts sent back.
        {name for call in context.calls for name in call.header_names}
    )
    assert names == ["retry-after", "x-ratelimit-limit"]  # Header names, lower case.
    assert [value for call in context.calls for value in call.retry_after_seconds] == ["not numeric"]  # Retry-After.
    assert len(session.uris) == 7  # One retry of the 500, plus the six catalogs.


def test_check_result_request_facts_skip_refused_attempts() -> None:  # Confirm that a refused attempt is not counted.
    """A budget-refused attempt sent no request, so it is not counted or listed in the statuses."""
    refused = CallRecord(  # Build an attempt that the budget refused before any send.
        path_label="/x",
        query_names=(),
        status_code=None,
        error_class=CallRecord.ErrorClass.BUDGET_EXHAUSTED,
        error_text="",
        data={},
        next_value=None,
        header_names=(),
        retry_after_seconds=(),
        elapsed_seconds=0.0,
        attempt=1,
    )
    result = CheckResult.from_calls(  # Build the result from the refused attempt only.
        "SMK-05", CheckStatus.PASS, "ok", (refused,)
    )
    assert result.request_count == 0 and result.http_statuses == ()  # Nothing was sent.


def test_check_result_detail_is_ascii_and_at_most_200_characters() -> None:  # Confirm a detail is ASCII and cut at 200.
    """A detail keeps ASCII only and is cut to 200 characters."""
    result = CheckResult.from_calls(  # Build a detail that is too long and holds one non-ASCII letter.
        "SMK-05", CheckStatus.PASS, "x" * 250 + "é", ()
    )
    assert len(result.detail) == 200 and result.detail.isascii()  # Cut and ASCII.


def test_skip_result_names_its_cause_and_has_no_stop_reason() -> None:  # Confirm that a skip result names its cause.
    """A SKIP result names its cause, and its evidence item has no stop reason."""
    skipped = CheckResult.skipped("SMK-07", "not run: rate-limit stop")  # Build a skip result with its cause.
    assert (  # Confirm that the skip keeps its status and its cause.
        skipped.status is CheckStatus.SKIP and skipped.detail == "not run: rate-limit stop"
    )
    assert skipped.as_evidence()["stop_reason"] is None  # The stop reason belongs to paged queries only.
    assert (  # Confirm that the rate-limit stop has its label and its exit code.
        STOP.RATE_LIMIT_STOP.label == "Rate-limit stop" and STOP.RATE_LIMIT_STOP.exit_code == 3
    )


def test_outcome_verdict_passes_only_when_a_check_ran_and_none_failed() -> None:  # Confirm the verdict rule of the run.
    """The verdict is PASS for WARN, INFO, and PASS results, and CHECK_FAILURE for a FAIL or for no result."""
    ok = CheckResult.from_calls("SMK-05", CheckStatus.WARN, "warn", ())  # A WARN result must not fail the verdict.
    failed = CheckResult.from_calls(  # Build a failed result, which fails the run.
        "SMK-06", CheckStatus.FAIL, "fail", ()
    )
    assert STOP.verdict([ok]) is STOP.PASS  # A warning does not fail the run.
    assert STOP.verdict([ok, failed]) is STOP.CHECK_FAILURE  # One failure fails the run.
    assert STOP.verdict([]) is STOP.CHECK_FAILURE  # No check ran.


def test_check_status_roll_up_order_is_fail_warn_skip_info_pass() -> (  # Confirm the roll-up picks the worst status.
    None
):
    """The roll-up returns the most severe status in the contract order."""
    assert (  # Confirm that SKIP outranks INFO and PASS.
        CheckStatus.most_severe([CheckStatus.PASS, CheckStatus.INFO, CheckStatus.SKIP]) is CheckStatus.SKIP
    )
    assert (  # Confirm that FAIL outranks WARN and PASS.
        CheckStatus.most_severe([CheckStatus.PASS, CheckStatus.WARN, CheckStatus.FAIL]) is CheckStatus.FAIL
    )
    assert CheckStatus.most_severe([]) is CheckStatus.SKIP  # No part ran.
