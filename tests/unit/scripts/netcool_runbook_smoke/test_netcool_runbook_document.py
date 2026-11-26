"""Offline document test for the Mist NetCool alarm integration runbook.

The module reads the real runbook, the real Mist OpenAPI file, and the feature specification. It sends
no network request and reads no token. It checks the headings, the Mist API paths, and the query parameters.
It also checks the regional hosts, the Appendix B names, the privacy patterns, and the operations of the specification.

Why: a runbook edit can remove a heading, add an identifier, or name a path that the Mist API does not
define. This test finds each defect offline, before an operator reads the runbook.
"""

from __future__ import annotations  # Postpone annotations, so the helper types can refer to each other.

import importlib  # Import each SDK module that the specification names.
import json  # Read the JSON error type that the OpenAPI copies must raise.
import re  # Match the subsection numbers, the query names, and the privacy patterns.
from pathlib import Path  # Build paths with pathlib, so tests run on Windows, macOS, and Linux.

import pytest  # Provide the module fixtures and the parametrized family cases.

from scripts.netcool_runbook_smoke.documents import (  # The shared readers of the runbook and the OpenAPI file.
    MarkdownTables,
    OpenApiIndex,
    RunbookClaims,
)

REPO_ROOT = Path(__file__).resolve().parents[4]  # Folder that holds documentation, scripts, and specs.
RUNBOOK_FILE = REPO_ROOT / "documentation" / "noc-runbooks" / "MIST_NETCOOL_ALARM_INTEGRATION.md"  # Runbook under test.
OPENAPI_FILE = REPO_ROOT / "documentation" / "mist-api-openapi31json.json"  # Mist OpenAPI file of the repository.
SPEC_FILE = REPO_ROOT.joinpath(  # Specification of feature 4934, which lists the Mist API operations.
    "specs", "numbered", "0", "0", "1", "2", "4", "2", "1", "4", "4934-mist-netcool-runbook", "spec.md"
)
H2_ORDER: tuple[str, ...] = (  # The twenty H2 headings, in the order of runbook-structure.md.
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
SUBSECTION_NUMBERS: tuple[str, ...] = (  # H3 numbers that the contract names.
    "4.4",
    "5.4",
    "5.5",
    "8.4",
    "12.2",
    "12.3",
    "12.4",
    "12.5",
)
FAMILY_HEADINGS: tuple[str, ...] = (  # The four endpoint family sections of section 6.
    "6.1 Alarm Search",
    "6.2 Device Event Search",
    "6.3 Mist Edge Event Search",
    "6.4 System Event Search",
)
ENDPOINT_FACTS: tuple[tuple[str, str], ...] = (  # Each query label with the fact row that holds its path.
    ("Organization search", "Organization path"),
    ("Site search", "Site path"),
    ("Count", "Count path"),
)
CATALOG_NUMBERS: tuple[str, ...] = ("B.1", "B.2", "B.3", "B.4", "B.5")  # Appendix B subsection numbers.
CATALOG_KEYS: tuple[str, ...] = (  # Catalog keys of the five name tables.
    "alarm_defs",
    "device_events",
    "mxedge_events",
    "system_events",
    "webhook_topics",
)
REGIONAL_HOST_COUNT = 12  # Regional API hosts in section 5.5 and in the OpenAPI servers list.
MINIMUM_API_PATHS = 20  # Fewest Mist API paths that a complete parse of the runbook finds.
OPERATION_COUNT = 25  # Operations in the Mist API Operations section of the specification.
QUERY_SEGMENT_PATTERN = re.compile(  # Labeled segments of a Query parameters row.
    r"(Organization search|Site search|Count): (.*?)(?=Organization search:|Site search:|Count:|$)"
)
OPERATION_ID_PATTERN = re.compile(r"- \*\*operationId\*\*: `([^`]+)`")  # One operationId bullet of the specification.
SDK_MODULE_PATTERN = re.compile(r"- \*\*mistapi SDK module\*\*: `([^`]+)`")  # One SDK module bullet.
PRIVACY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (  # Each privacy kind with the pattern that finds it.
    ("UUID", re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.IGNORECASE)),
    ("MAC address", re.compile(r"\b(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}\b|\b[0-9a-f]{12}\b", re.IGNORECASE)),
    ("email address", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("token", re.compile(r"\bToken [A-Za-z0-9]{20,}", re.IGNORECASE)),
    ("long run of letters or digits", re.compile(r"[A-Za-z0-9]{40,}")),
)


@pytest.fixture(scope="module")
def runbook_text() -> str:  # Load the runbook text once, so each check reads the same file.
    """Read the runbook text once for the tests of this module."""
    assert RUNBOOK_FILE.is_file(), f"runbook is missing: {RUNBOOK_FILE.name}"  # No local folder reaches output.
    return RUNBOOK_FILE.read_text(encoding="utf-8")  # Read the whole runbook as UTF-8.


@pytest.fixture(scope="module")
def runbook_claims() -> RunbookClaims:  # Parse the runbook facts once, so each check shares one parse.
    """Parse the runbook facts once for the tests of this module."""
    assert RUNBOOK_FILE.is_file(), f"runbook is missing: {RUNBOOK_FILE.name}"  # No local folder reaches output.
    return RunbookClaims.from_path(RUNBOOK_FILE)  # Parse the runbook with the shared reader.


@pytest.fixture(scope="module")
def runbook_tables(  # Split the runbook into prose and tables for the query checks.
    runbook_text: str,
) -> MarkdownTables:
    """Split the runbook text into prose and tables once for the query checks."""
    return MarkdownTables(runbook_text)  # Keep the prose lines and their table rows.


@pytest.fixture(scope="module")
def openapi_index() -> OpenApiIndex:  # Index the OpenAPI file once, so the path and host checks share it.
    """Index the OpenAPI file once for the tests of this module."""
    assert OPENAPI_FILE.is_file(), f"OpenAPI file is missing: {OPENAPI_FILE.name}"  # No local folder reaches output.
    return OpenApiIndex.from_path(OPENAPI_FILE)  # Index each GET operation and each server.


@pytest.fixture(scope="module")
def specification_text() -> str:  # Load the feature specification for the operation check.
    """Read the feature specification once for the operation check."""
    assert SPEC_FILE.is_file(), f"specification is missing: {SPEC_FILE.name}"  # No local folder reaches output.
    return SPEC_FILE.read_text(encoding="utf-8")  # Read the whole specification as UTF-8.


def heading_number_present(  # Match the heading number as one token, because the contract names sections by number.
    headings: tuple[tuple[int, str], ...], level: int, number: str
) -> bool:
    """Return True when a heading of the level starts with the subsection number.

    Why: the contract names each subsection by its number, so the title text is not compared. The number
    must end at a space or at the end of the heading, so that 4.4 does not match 4.40.

    Args:
        headings: Each heading as (level, text), in document order.
        level: Heading level to search, from 1 to 3.
        number: Subsection number, for example 4.4.

    Returns:
        True when one heading of the level starts with the number.
    """
    pattern = re.compile(rf"{re.escape(number)}(?:\s|$)")  # Match the number as one whole token.
    return any(  # Search each heading for the given level and number.
        heading_level == level and pattern.match(text) is not None for heading_level, text in headings
    )


def level_two_findings(  # Report each difference between the H2 headings and the contract list.
    claims: RunbookClaims,
) -> list[str]:
    """Return each difference between the H2 headings of the runbook and the contract list.

    Why: the contract fixes each H2 heading and its order. A missing or moved heading breaks the anchor
    links to that section, so each difference is reported by its text.

    Args:
        claims: Parsed facts of the runbook.

    Returns:
        One finding for each missing heading. When none is missing, one finding for a different order or
        count. Empty when the H2 headings equal the contract list.
    """
    missing = [  # Headings that the runbook lacks.
        f"missing H2 heading: {title}" for title in H2_ORDER if title not in claims.h2_headings
    ]
    if missing:  # A missing heading is the first defect to report.
        return missing  # Report each missing heading.
    if claims.h2_headings != H2_ORDER:  # Every heading exists, so the order or an extra heading differs.
        return ["H2 headings differ in order or count"]  # Report the order defect.
    return []  # The H2 headings equal the contract list.


def catalog_findings(  # Report each Appendix B heading that is missing and each table that has no name.
    claims: RunbookClaims,
) -> list[str]:
    """Return each Appendix B heading that is missing and each Appendix B table that has no name.

    Why: each Appendix B table names the catalog entries that the live smoke test compares with Mist. A
    missing heading or an empty table lets that comparison pass with nothing to compare.

    Args:
        claims: Parsed facts of the runbook.

    Returns:
        One finding for each defect. Empty when each heading exists and each table has a name.
    """
    missing = [  # Appendix B headings that the runbook lacks.
        f"missing Appendix B heading: {number}"
        for number in CATALOG_NUMBERS
        if not heading_number_present(claims.headings, 3, number)
    ]
    empty = [  # Appendix B tables that hold no name.
        f"Appendix B table has no name: {key}" for key in CATALOG_KEYS if not claims.catalog_names.get(key)
    ]
    return missing + empty  # Report the missing headings, then the empty tables.


def _backticked_names(text: str) -> tuple[str, ...]:  # Collect each backticked name once, in document order.
    """Return the backticked names of a text, in order and without repeats.

    Why: each query name of the runbook is one word in backticks.

    Args:
        text: Text that can hold backticked names.

    Returns:
        The unique names, in document order.
    """
    return tuple(dict.fromkeys(re.findall(r"`([^`]+)`", text)))  # Unique names in document order.


def _first_backticked(  # Take the first backticked value of a fact cell, which holds the endpoint path.
    text: str,
) -> str:
    """Return the first backticked value of a text, or an empty text when none exists.

    Why: each fact cell holds its endpoint path in backticks, and the first value is that path.

    Args:
        text: Cell text that can hold backticked values.

    Returns:
        The first backticked value, or an empty text.
    """
    values = re.findall(r"`([^`]+)`", text)  # Every backticked value of the cell.
    return values[0] if values else ""  # The first value, or nothing when the cell has none.


def _segment_names(  # Collect the query names that one labeled segment of the Query parameters row takes.
    segment: str, organization_names: tuple[str, ...]
) -> tuple[str, ...]:
    """Return the query names that one labeled segment of a Query parameters row takes.

    Why: a site segment repeats the organization names with the words "the same names", and it removes
    names with the word "without". Both rules apply, so the names match the site endpoint.

    Args:
        segment: Text of one labeled segment.
        organization_names: Names of the organization search, which a segment can repeat.

    Returns:
        The names that the endpoint of the segment takes, in order.
    """
    excluded = tuple(re.findall(r"without `([^`]+)`", segment))  # Names that the segment removes.
    own_text = re.sub(r"without `[^`]+`", "", segment)  # Segment text without the removed names.
    inherited = organization_names if "the same names" in segment else ()  # Names that the segment repeats.
    names = _backticked_names(own_text)  # Names that the segment lists itself.
    return tuple(name for name in dict.fromkeys((*inherited, *names)) if name not in excluded)  # Kept names.


def query_name_pairs(  # Pair each endpoint path with the query names of a family section.
    tables: MarkdownTables, heading: str
) -> list[tuple[str, str]]:
    """Return each (endpoint path, query name) pair that a family section names.

    Why: the Query parameters row names the parameters of three endpoints: the organization search, the
    site search, and the count. Each name is checked against the endpoint that the row names for it.

    Args:
        tables: Markdown tables of the runbook.
        heading: Family section heading, for example 6.1 Alarm Search.

    Returns:
        The pairs in document order. Empty when the section has no Query parameters row.
    """
    rows = tables.rows_after_heading(heading, ("Fact", "Value"))  # Table rows under the heading.
    facts = {row[0]: row[1] for row in rows if len(row) > 1}  # Value of each fact name.
    segments = dict(QUERY_SEGMENT_PATTERN.findall(facts.get("Query parameters", "")))  # Text of each labeled segment.
    organization_names = _backticked_names(segments.get("Organization search", ""))  # Names of the organization search.
    pairs: list[tuple[str, str]] = []  # Pairs found in this section.
    for label, fact_name in ENDPOINT_FACTS:  # Each endpoint of the section.
        path = _first_backticked(facts.get(fact_name, ""))  # Path of this endpoint.
        pairs.extend((path, name) for name in _segment_names(segments.get(label, ""), organization_names))  # Its names.
    return pairs  # Pairs of endpoint path and query name.


def unknown_query_pairs(  # Report each query name that the OpenAPI operation does not define.
    pairs: list[tuple[str, str]], openapi_index: OpenApiIndex
) -> list[str]:
    """Return each (path, name) pair whose query name the OpenAPI operation does not define.

    Why: the runbook tells an operator which parameters to send, so each name must exist for its endpoint
    in the OpenAPI file.
        openapi_index: Index of the OpenAPI file.

    Returns:
        One finding for each pair that the OpenAPI operation does not define. Empty when each pair exists.
    """
    return [  # One finding for each undefined query name.
        f"{path} has no query parameter {name}"
        for path, name in pairs
        if name not in openapi_index.query_parameters(path)
    ]


def host_findings(  # Report each host that only one of the two host lists names.
    claims: RunbookClaims, openapi_index: OpenApiIndex
) -> list[str]:
    """Return each host that only the section 5.5 table or only the OpenAPI servers list names.

    Why: the runbook and the OpenAPI file must name the same regional hosts.

    Args:
        claims: Parsed facts of the runbook.
        openapi_index: Index of the OpenAPI file.

    Returns:
        One finding for each host that only one list names. Empty when the two lists match.
    """
    runbook_hosts = set(claims.regional_hosts)  # Hosts of the section 5.5 table.
    server_hosts = set(openapi_index.server_hosts())  # Hosts of the OpenAPI servers list.
    only_runbook = [  # Hosts that the runbook names and OpenAPI does not.
        f"runbook host not in OpenAPI servers: {host}" for host in sorted(runbook_hosts - server_hosts)
    ]
    only_openapi = [  # Hosts that OpenAPI names and the runbook does not.
        f"OpenAPI server not in runbook: {host}" for host in sorted(server_hosts - runbook_hosts)
    ]
    return only_runbook + only_openapi  # Report the runbook-only hosts, then the OpenAPI-only hosts.


def privacy_findings(  # Report the line number and the kind of each privacy match, and never the value.
    text: str,
) -> list[tuple[int, str]]:
    """Return the line number and the kind of each privacy match in a text.

    Why: a runbook must never hold a real identifier, a contact address, or a token. Each finding names the
    line and the kind only, so the test output never repeats the matched value.

    Args:
        text: Full text of the runbook, or of an edited copy of it.

    Returns:
        One (line number, kind) pair for each pattern that matches a line. Line numbers start at 1.
    """
    findings: list[tuple[int, str]] = []  # Pairs of line number and kind, in document order.
    for line_number, line in enumerate(text.splitlines(), start=1):  # Each line, numbered from 1.
        for kind, pattern in PRIVACY_PATTERNS:  # Each privacy kind and its pattern.
            if pattern.search(line) is not None:  # The pattern matches somewhere in the line.
                findings.append((line_number, kind))  # Record the line number and the kind only.
    return findings  # The findings, in document order.


def _section_lines(  # Collect the lines under one heading, up to the next heading.
    text: str, heading: str
) -> tuple[str, ...]:
    """Return the lines under one heading, up to the next heading of any level.

    Why: the operations of the specification sit under one heading. The next heading ends the section, so
    an operation of a later section is not counted.

    Args:
        text: Full Markdown text.
        heading: Heading line, including its markers.

    Returns:
        The lines under the heading. Empty when the heading is absent.
    """
    collected: list[str] = []  # Lines under the heading.
    inside = False  # True after the heading line.
    for line in text.splitlines():  # Each line of the document, in order.
        if line.strip() == heading:  # The heading line starts the section.
            inside = True  # Collect the lines that follow.
        elif inside and re.match(r"#{1,6} ", line):  # The next heading ends the section.
            break  # Stop the search at the next heading.
        elif inside:  # A line under the heading.
            collected.append(line)  # Keep the line.
    return tuple(collected)  # The lines of the section.


def specification_operations(  # Read the operationId values and the SDK module names of the operations section.
    spec_text: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return the operationId values and the SDK module names of the Mist API Operations section.

    Why: the specification gives each operation as two bullet lines, one for the operationId and one for the
    SDK module. The two lists stay separate, so the caller can detect a bullet without a partner.

    Args:
        spec_text: Full text of the specification.

    Returns:
        The operationId values and the SDK module names, each in document order.
    """
    operation_ids: list[str] = []  # Operation identifiers, in document order.
    module_names: list[str] = []  # SDK module names, in document order.
    for line in _section_lines(spec_text, "### Mist API Operations"):  # Each line of the section.
        operation_match = OPERATION_ID_PATTERN.search(line)  # An operationId bullet, if this line holds one.
        module_match = SDK_MODULE_PATTERN.search(line)  # An SDK module bullet, if this line holds one.
        if operation_match is not None:  # Keep the identifier of an operationId bullet.
            operation_ids.append(operation_match.group(1))  # Add the identifier in order.
        if module_match is not None:  # Keep the name of an SDK module bullet.
            module_names.append(module_match.group(1))  # Add the module name in order.
    return tuple(operation_ids), tuple(module_names)  # Both lists, in document order.


def operation_findings(  # Report each reason that one operation fails, so the test names the missing part.
    pair: tuple[str, str], get_operation_ids: frozenset[str]
) -> list[str]:
    """Return each reason that one specification operation fails the check.

    Why: a specification operation needs a GET operation in the OpenAPI file and a function in its SDK module.
    Each missing part gives its own finding, so the test names the part that is missing.

    Args:
        pair: The operationId and the SDK module name of one operation.
        get_operation_ids: Each operationId of a GET operation in the OpenAPI file.

    Returns:
        One finding for each missing part. Empty when both parts exist.
    """
    operation_id, module_name = pair  # Split the pair into its identifier and its module name.
    findings: list[str] = []  # Reasons that this operation fails.
    if operation_id not in get_operation_ids:  # The OpenAPI file has no GET operation with this identifier.
        findings.append(f"no GET operation with operationId {operation_id}")  # Record the missing GET operation.
    try:  # Load the SDK module that the specification names.
        module = importlib.import_module(module_name)  # Load the module by its dotted name.
    except ImportError:  # The installed SDK has no module of this name.
        findings.append(f"SDK module cannot be imported: {module_name}")  # Record the import failure.
        return findings  # Without a module, the function check cannot run.
    has_function = hasattr(module, operation_id)  # The module defines a name of the operation.
    if not has_function or not callable(getattr(module, operation_id)):  # The name must be callable.
        findings.append(f"{module_name} has no function {operation_id}")  # Record the missing function.
    return findings  # The reasons, which are empty when the operation passes.


def test_runbook_and_openapi_files_exist_and_parse(  # Confirm that both files exist and hold content to examine.
    runbook_claims: RunbookClaims, openapi_index: OpenApiIndex
) -> None:
    """Confirm that both files exist and that each one holds content to examine.

    Why: a missing or empty input would let the other checks pass with nothing examined.
    """
    assert RUNBOOK_FILE.is_file(), f"runbook is missing: {RUNBOOK_FILE.name}"  # No local folder reaches output.
    assert OPENAPI_FILE.is_file(), f"OpenAPI file is missing: {OPENAPI_FILE.name}"  # No local folder reaches output.
    assert len(runbook_claims.headings) > 0, "runbook examined 0 headings"  # Zero headings means the parse failed.
    assert len(openapi_index.operations) > 0, "OpenAPI examined 0 GET operations"  # Zero operations means no parse.


def test_h2_headings_equal_the_contract_list_in_order(  # Confirm that the H2 headings match the contract list.
    runbook_claims: RunbookClaims,
) -> None:
    """Confirm that the H2 headings of the runbook equal the contract list, in order.

    Why: the contract fixes each H2 heading. A changed heading breaks the anchor links to its section.
    """
    findings = level_two_findings(runbook_claims)  # Differences from the contract list.
    count = len(runbook_claims.h2_headings)  # Headings examined by the check.
    assert findings == [], f"H2 check examined {count} headings, findings: {findings}"  # Report each difference.


def test_h3_subsections_exist(  # Confirm that each contract subsection number exists as an H3 heading.
    runbook_claims: RunbookClaims,
) -> None:
    """Confirm that each subsection number that the contract names exists as an H3 heading.

    Why: the contract requires each number. The check reads only the number, so an edit of a
    title does not fail it.
    """
    h3_count = sum(1 for level, _text in runbook_claims.headings if level == 3)  # H3 headings examined.
    missing = [  # Subsection numbers with no H3 heading.
        number for number in SUBSECTION_NUMBERS if not heading_number_present(runbook_claims.headings, 3, number)
    ]
    assert h3_count > 0, "H3 check examined 0 headings"  # Zero H3 headings means the parse failed.
    assert missing == [], f"H3 check examined {len(SUBSECTION_NUMBERS)} numbers, missing: {missing}"  # Report gaps.


def test_every_mist_api_path_has_a_get_operation(  # Confirm that each runbook API path has a GET operation in OpenAPI.
    runbook_claims: RunbookClaims, openapi_index: OpenApiIndex
) -> None:
    """Confirm that each Mist API path in the runbook has a GET operation in the OpenAPI file.

    Why: the runbook uses GET requests only, so a path without a GET operation cannot run as written. The
    check reads each path anywhere in the runbook, so a path in a code block is checked too.
    """
    paths = runbook_claims.api_paths  # Every Mist API path of the runbook, without its query string.
    missing = [path for path in paths if not openapi_index.has_get(path)]  # Paths with no GET operation.
    assert len(paths) >= MINIMUM_API_PATHS, f"examined {len(paths)}"  # Too few paths mean a failed parse.
    assert missing == [], f"{len(missing)} of {len(paths)} paths lack GET: {missing}"  # Report each path.


@pytest.mark.parametrize("heading", FAMILY_HEADINGS)  # Run the check once for each endpoint family.
def test_query_parameters_exist_for_each_family(  # Run the query parameter check once for each endpoint family section.
    heading: str, runbook_tables: MarkdownTables, openapi_index: OpenApiIndex
) -> None:
    """Confirm that each query parameter of a family section exists for its endpoint in OpenAPI.

    Why: the runbook tells an operator which parameters to send, so each name must exist for its endpoint
    in the OpenAPI file.
    """
    pairs = query_name_pairs(runbook_tables, heading)  # Each endpoint path and query name of the section.
    findings = unknown_query_pairs(pairs, openapi_index)  # Pairs that the OpenAPI operation does not define.
    assert len(pairs) > 0, f"{heading} examined 0 query names"  # Zero names means the parse failed.
    assert findings == [], f"{heading} examined {len(pairs)} query names, findings: {findings}"  # Any gap fails.


def test_regional_hosts_equal_the_openapi_servers(  # Confirm that section 5.5 hosts match the twelve OpenAPI servers.
    runbook_claims: RunbookClaims, openapi_index: OpenApiIndex
) -> None:
    """Confirm that the section 5.5 hosts equal the OpenAPI servers, and that each list holds 12 hosts.

    Why: the runbook and the OpenAPI file must name the same regional hosts.
    """
    runbook_count = len(runbook_claims.regional_hosts)  # Hosts examined in section 5.5.
    server_count = len(openapi_index.server_hosts())  # Hosts examined in the OpenAPI servers list.
    findings = host_findings(runbook_claims, openapi_index)  # Hosts that only one list names.
    assert runbook_count == REGIONAL_HOST_COUNT, f"section 5.5 examined {runbook_count} hosts"  # Count the hosts.
    assert server_count == REGIONAL_HOST_COUNT, f"OpenAPI examined {server_count} servers"  # Count the servers.
    assert findings == [], f"host findings: {findings}"  # Report each host that one list lacks.


def test_appendix_b_tables_have_names_and_headings(  # Confirm that each Appendix B table has a name and a heading.
    runbook_claims: RunbookClaims,
) -> None:
    """Confirm that each Appendix B table holds a name and that B.1 to B.5 exist as H3 headings.

    Why: each table names the catalog entries that the live smoke test compares with Mist. An empty table or a
    missing heading would let that comparison pass with nothing to compare.
    """
    examined = sum(len(runbook_claims.catalog_names.get(key, ())) for key in CATALOG_KEYS)  # Names in the five tables.
    findings = catalog_findings(runbook_claims)  # Missing headings and empty tables.
    assert examined > 0, "Appendix B examined 0 names"  # Zero names means nothing was checked.
    assert findings == [], f"Appendix B examined {examined} names, findings: {findings}"  # Any gap fails.


def test_runbook_holds_no_identifier_token_or_contact_address(  # Confirm the runbook holds no identifier or token.
    runbook_text: str,
) -> None:
    """Confirm that the runbook holds no UUID, no MAC address, no email address, and no token.

    Why: the runbook is shared with the NOC and kept in source control. A real identifier, a contact address,
    or a token in the runbook exposes the customer. Each finding names the line and the kind only.
    """
    line_count = len(runbook_text.splitlines())  # Lines examined by the scan.
    findings = privacy_findings(runbook_text)  # Line number and kind of each match.
    assert line_count > 0, "privacy scan examined 0 lines"  # Zero lines means nothing was checked.
    assert findings == [], f"privacy scan examined {line_count} lines, findings: {findings}"  # Line and kind only.


def test_each_specification_operation_has_a_get_operation_and_sdk_function(  # Confirm each operation has a GET and SDK.
    openapi_index: OpenApiIndex, specification_text: str
) -> None:
    """Confirm that each specification operation has a GET operation and an SDK function of its name.

    Why: the specification names the Mist operation and the SDK module of each feature operation. A name that
    the OpenAPI file or the SDK does not define cannot run as written.
    """
    operation_ids, module_names = specification_operations(specification_text)  # Two bullet lists, in order.
    operations = openapi_index.operations.values()  # Each GET operation as (operationId, parameters).
    get_ids = frozenset(operation_id for operation_id, _parameters in operations)  # Unique GET identifiers.
    assert len(operation_ids) == len(module_names) == OPERATION_COUNT, (  # Each operation needs one SDK module.
        f"specification examined {len(operation_ids)} operationId and {len(module_names)} SDK module bullets, "
        f"need {OPERATION_COUNT}"
    )
    findings: list[str] = []  # Reasons that an operation fails.
    for pair in zip(operation_ids, module_names, strict=True):  # Check each operation with its SDK module.
        findings.extend(operation_findings(pair, get_ids))  # Collect the reasons for this operation.
    assert findings == [], f"examined {len(operation_ids)} operations, findings: {findings}"  # Any gap fails.


def test_openapi_copy_that_is_empty_raises_value_error(tmp_path: Path) -> None:  # Empty copy must raise a clear error.
    """An empty copy of the repository OpenAPI file raises a ValueError, and its cause is the JSON parse error.

    Why: a download that wrote no bytes must stop the run with a clear message, not with a parse traceback.

    Args:
        tmp_path: Folder for the copy of the OpenAPI file.
    """
    copy_path = tmp_path / OPENAPI_FILE.name  # Name the copy like the repository file, so the message matches.
    copy_path.write_bytes(b"")  # The copy has an empty body, so it holds no JSON value.
    with pytest.raises(ValueError) as error:  # Expect the loader error, so the test checks its message.
        OpenApiIndex.from_path(copy_path)  # The empty copy must raise the clear error.
    assert str(error.value) == f"OpenAPI file cannot be read: {OPENAPI_FILE.name}"  # No local path in the message.
    assert isinstance(error.value.__cause__, json.JSONDecodeError)  # The cause is the JSON parse failure.


def test_openapi_copy_cut_short_raises_value_error(tmp_path: Path) -> None:  # Truncated copy must raise a clear error.
    """A repository OpenAPI copy that stops in the middle raises a ValueError, with the JSON parse error as cause.

    Why: an interrupted download leaves a prefix of the document, and the loader must reject that prefix.

    Args:
        tmp_path: Folder for the truncated copy of the OpenAPI file.
    """
    document_text = OPENAPI_FILE.read_text(encoding="utf-8")  # The real document, read once to make the copy.
    copy_path = tmp_path / OPENAPI_FILE.name  # Name the copy like the repository file, so the message matches.
    copy_path.write_text(document_text[:500], encoding="utf-8")  # The first 500 characters are an unfinished object.
    with pytest.raises(ValueError) as error:  # Expect the loader error, so the test checks its message.
        OpenApiIndex.from_path(copy_path)  # The truncated copy must raise the clear error.
    assert str(error.value) == f"OpenAPI file cannot be read: {OPENAPI_FILE.name}"  # No local path in the message.
    assert isinstance(error.value.__cause__, json.JSONDecodeError)  # The cause is the JSON parse failure.


def test_missing_runbook_is_reported_by_file_name(  # Confirm that a missing runbook stops the parse, naming the file.
    tmp_path: Path,
) -> None:
    """Confirm that an unreadable runbook stops the parse with a message that names only the file.

    Why: the operator needs the cause, and the message must not print the folder of the user.
    """
    missing_path = tmp_path / "absent-runbook.md"  # A path that does not exist in tmp_path.
    expected_message = re.escape("runbook cannot be read: absent-runbook.md")  # The reader names the file only.
    with pytest.raises(ValueError, match=expected_message):  # The reader must raise this message.
        RunbookClaims.from_path(missing_path)  # Parse the missing file.


def test_removed_heading_is_reported(  # Confirm that the H2 check reports a heading that a copy of the runbook lacks.
    tmp_path: Path, runbook_text: str
) -> None:
    """Confirm that the H2 check reports a heading that a copy of the runbook lacks.

    Why: the check must fail on a real defect, so the test removes one heading from a copy and checks the report.
    """
    edited = runbook_text.replace("## 9. Netcool Integration\n", "", 1)  # Remove one H2 heading from the copy.
    assert edited != runbook_text, "the copy keeps the heading, so the edit did not run"  # Guard against a no-op.
    copy_path = tmp_path / "runbook-without-heading.md"  # Keep the copy in tmp_path, away from the repository.
    copy_path.write_text(edited, encoding="utf-8")  # Write UTF-8, the encoding of the repository files.
    findings = level_two_findings(RunbookClaims.from_path(copy_path))  # The H2 check on the copy.
    assert findings == ["missing H2 heading: 9. Netcool Integration"]  # The check names the removed heading.


def test_added_uuid_is_reported_by_line_and_kind(  # Confirm that the privacy scan reports an added UUID by line.
    tmp_path: Path, runbook_text: str
) -> None:
    """Confirm that the privacy scan reports an added UUID by its line number and its kind.

    Why: the scan must fail on a real identifier, and its report must not repeat the identifier. The test adds
    one fake UUID to a copy of the runbook and checks the report.
    """
    lines = runbook_text.splitlines()  # Lines of the real runbook.
    added_line_number = len(lines) + 1  # The added line is the last line of the copy.
    fake_identifier = "11111111-2222-4333-8444-555555555555"  # A fake UUID that no real system holds.
    edited = "\n".join([*lines, f"Test identifier {fake_identifier} for the scan."]) + "\n"  # Copy with one fake UUID.
    copy_path = tmp_path / "runbook-with-uuid.md"  # Keep the copy in tmp_path, away from the repository.
    copy_path.write_text(edited, encoding="utf-8")  # Write UTF-8, the encoding of the repository files.
    findings = privacy_findings(copy_path.read_text(encoding="utf-8"))  # The privacy scan on the copy.
    assert (added_line_number, "UUID") in findings, f"findings: {findings}"  # The scan names the line and the kind.
    assert fake_identifier not in str(findings), "the report repeats the matched value"  # Never repeat the value.
