"""Tests for the runbook, OpenAPI, and evidence readers and writers of the NOC runbook smoke test.

The tests use fixtures under tmp_path and the repository OpenAPI file, which is a local file. No test
opens a network connection, and no test reads a token. Why: the document checks must prove each rule on
known text before they judge the real runbook.
"""

from __future__ import annotations  # Postpone annotations, so the helper types can refer to each other.

import json  # Build the OpenAPI fixtures and read the evidence files back.
from datetime import UTC, datetime, timedelta, timezone  # Build fixed moments for the evidence file names.
from pathlib import Path  # Build paths with pathlib, so tests run on Windows, macOS, and Linux.
from typing import Any  # Type the JSON fixtures and the deliberately wrong input.

import pytest  # Run the parametrized boundary cases and assert the raised errors.

from scripts.netcool_runbook_smoke.documents import (  # The document readers and writers under test.
    EvidenceRedactor,
    EvidenceWriter,
    MarkdownTables,
    OpenApiIndex,
    RunbookClaims,
)

ORG_ID = "11111111-2222-4333-8444-555555555555"  # Fake organization identifier, never a real one.
SITE_ID = "66666666-7777-4888-8999-aaaaaaaaaaaa"  # Fake site identifier, never a real one.
REPO_ROOT = Path(__file__).resolve().parents[4]  # Folder that holds scripts, documentation, and test-artifacts.
OPENAPI_FILE = REPO_ROOT / "documentation" / "mist-api-openapi31json.json"  # The repository OpenAPI file.
H2_ORDER = [  # The twenty H2 headings in the order of runbook-structure.md.
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
]  # The twenty H2 headings in the order of runbook-structure.md.
RUNBOOK_TEXT = """# MIST_NETCOOL_ALARM_INTEGRATION

## 1. Overview

| Field | Value |
| --- | --- |
| Document type | Runbook |

| Mark | Meaning |
| --- | --- |
| Proposal | A proposed value |

## 2. How to Use This Runbook
## 3. Purpose and Scope
## 4. Architecture
## 5. Prerequisites

### 5.5 Regional API Hosts

| Region | API host | Verification |
| --- | --- | --- |
| Global 01 | `api.mist.com` | Verified (OpenAPI) |
| Global 02 | `api.gc1.mist.com` | Verified (OpenAPI) |

## 6. Mist Data Sources

### 6.1 Alarm Search

| Fact | Value |
| --- | --- |
| Organization path | `/api/v1/orgs/{org_id}/alarms/search?limit=1000` |
| Identifier fields | `id`, `org_id` |

### 6.2 Device Event Search

| Fact | Value |
| --- | --- |
| Identifier fields | none |

### 6.3 Mist Edge Event Search
### 6.4 System Event Search
### 6.5 Definition Catalogs
### 6.6 Webhook Topics

## 7. Alarm and Event Selection

The usage request uses `/api/v1/self/usage?x=1`, and the alarm acknowledgement uses `/api/v1/orgs/{org_id}/alarms/ack`.

## 8. Collection Design
## 9. Netcool Integration
## 10. AP Warning Report (Menu 307)
## 11. NOC Operating Procedures
## 12. Troubleshooting
## 13. Verification and Smoke Test
## 14. Acceptance Criteria and UAT Plan
## 15. Open Decisions

## Appendix A. Endpoint Reference

| Method | Path | Scope | Purpose | Verification |
| --- | --- | --- | --- | --- |
| GET | `/api/v1/orgs/{org_id}/alarms/search` | org | Search alarms | Verified (OpenAPI) |

## Appendix B. Verified Catalog Names

### B.1 Alarm Types

| Name | Use in this runbook |
| --- | --- |
| `ap_offline` | Alarm type |
| `rogue_ap` | Alarm type |

### B.2 Device Event Types

| Name | Use in this runbook |
| --- | --- |
| `AP_CONNECTED` | Device event type |

### B.3 Mist Edge Event Types

| Name | Use in this runbook |
| --- | --- |
| `MXEDGE_RECONNECT` | Mist Edge event type |

### B.5 Webhook Topics

| Name | Use in this runbook |
| --- | --- |
| `alarms` | Webhook topic |

## Appendix C. Sample Payloads

```text
GET /api/v1/orgs/{org_id}/devices/events/search
```

## Appendix D. Glossary

| Term | Meaning |
| --- | --- |
| AP | Access point |

## Appendix E. Revision History

| Version | Date | Author | Change |
| --- | --- | --- | --- |
| 1.0 | 2026-11-25 | Joseph Morrison | Draft |
"""  # Valid runbook fixture. It holds every heading and table that the parser reads.


def write_runbook(  # Write one runbook fixture under the test folder and return its path.
    tmp_path: Path, text: str
) -> Path:
    """Write one runbook fixture under tmp_path and return its path.

    Args:
        tmp_path: Folder of the test.
        text: Runbook text to write.

    Returns:
        The path of the written file.
    """
    path = tmp_path / "runbook.md"  # Keep the fixture in tmp_path, so the repository stays unchanged.
    path.write_text(text, encoding="utf-8")  # Write the UTF-8 text.
    return path  # The path of the written runbook.


def write_openapi(  # Write one OpenAPI fixture under the test folder and return its path.
    tmp_path: Path, document: Any
) -> Path:
    """Write one OpenAPI fixture under tmp_path and return its path.

    Args:
        tmp_path: Folder of the test.
        document: JSON value to write.

    Returns:
        The path of the written file.
    """
    path = tmp_path / "openapi.json"  # Keep the fixture in tmp_path, so the repository stays unchanged.
    path.write_text(json.dumps(document), encoding="utf-8")  # Write the JSON text.
    return path  # The path of the written OpenAPI file.


def openapi_fixture() -> (  # Build an OpenAPI document with a reference, a POST-only path, and two servers.
    dict[str, Any]
):
    """Return a small OpenAPI document with a $ref parameter, a POST-only path, and two servers.

    Returns:
        The OpenAPI document as a dictionary.
    """
    return {  # The OpenAPI document of the fixture.
        "openapi": "3.1.0",  # The version of the fixture format.
        "servers": [
            {"url": "https://api.mist.com", "description": "Global 01"},  # The first approved host.
            {"url": "https://api.mist.com", "description": "Duplicate"},  # A duplicate host, kept once.
            {"url": "https://api.eu.mist.com/", "description": "EMEA 01"},  # A second host with a slash.
        ],
        "paths": {
            "/api/v1/orgs/{org_id}/alarms/search": {
                "parameters": [{"$ref": "#/components/parameters/org_id"}],  # Path-level reference.
                "get": {
                    "operationId": "searchOrgAlarms",
                    "parameters": [
                        {"in": "query", "name": "start"},  # A query parameter of the operation.
                        {"in": "header", "name": "X-Trace"},  # A header parameter, not a query parameter.
                        {"$ref": "#/components/parameters/limit"},  # An operation-level reference.
                    ],
                },
            },
            "/api/v1/orgs/{org_id}/alarms/ack": {
                "post": {"operationId": "ackAlarm"},  # A POST-only path has no GET operation.
            },
        },
        "components": {
            "parameters": {
                "org_id": {"in": "path", "name": "org_id"},  # The organization placeholder.
                "limit": {"in": "query", "name": "limit"},  # A reusable query parameter.
            },
        },
    }


def token_text(  # Build a token-like text of a given length, in the word form or the plain form.
    token_length: int, token_word: bool
) -> str:
    """Build a text that holds a token-like value of a given length.

    Args:
        token_length: Number of letters in the value.
        token_word: True for the form "Token <value>", False for a plain run.

    Returns:
        The text with the value.
    """
    value = "a" * token_length  # The letters of the token-like value.
    return f"Token {value}" if token_word else value  # Add the word Token only for the word form.


def make_redactor(token_value: str = "") -> EvidenceRedactor:  # Build a redactor for the fixture organization and site.
    """Build a redactor for the fixture organization, with one site and the given token value.

    Args:
        token_value: Token value to remove, or an empty text.

    Returns:
        The redactor.
    """
    return EvidenceRedactor(organization_id=ORG_ID, site_ids=(SITE_ID,), token_value=token_value)  # The fixture.


def test_markdown_tables_skip_each_line_inside_a_fence() -> None:  # Confirm that a fenced heading is not prose.
    """A heading inside a code fence is not prose, so the parser never sees it."""
    tables = MarkdownTables("```text\n## Hidden\n```\n## Shown")  # A fenced heading, then a real heading.
    assert tables.prose_lines == ("## Shown",)  # Only the line outside the fence is prose.


def test_markdown_rows_follow_the_header_and_stop_at_the_first_non_row() -> (  # Confirm that rows stop at a non-row.
    None
):
    """A table gives its data rows as trimmed cells, and it ends at a line that is not a row."""
    text = "### Table\n| Name | Use |\n| --- | --- |\n|  a  | one |\n| b | two |\nAfter the table."  # Two data rows.
    rows = MarkdownTables(text).rows_after_heading("Table", ("Name", "Use"))  # Read the table under the heading.
    assert rows == (("a", "one"), ("b", "two"))  # Two data rows, with the cells trimmed.


def test_markdown_table_without_a_separator_row_is_not_read() -> None:  # Confirm a header with no separator is ignored.
    """A header without a separator row is not a table, so no row is read."""
    text = "### Table\n| Name | Use |\n| a | one |"  # No separator row after the header.
    assert MarkdownTables(text).rows_after_heading("Table", ("Name", "Use")) == ()  # Nothing is read.


def test_markdown_table_with_another_header_is_not_read() -> (  # Confirm that a table with another header is ignored.
    None
):
    """A table whose header differs from the contract header is not read."""
    text = "### Table\n| Name | Other |\n| --- | --- |\n| a | one |"  # The header text differs.
    assert MarkdownTables(text).rows_after_heading("Table", ("Name", "Use")) == ()  # The contract header is absent.


def test_markdown_missing_heading_gives_no_rows() -> None:  # Confirm that a missing heading gives no rows.
    """A heading that is absent from the text gives no rows."""
    assert MarkdownTables("## Other\n| a | b |").rows_after_heading("Missing", ("a", "b")) == ()  # Nothing found.


def test_claims_read_the_headings_in_order_with_their_levels(  # Confirm that the headings keep their levels and order.
    tmp_path: Path,
) -> None:
    """Each heading keeps its level, and the H2 texts keep the document order.

    Args:
        tmp_path: Folder for the runbook fixture.
    """
    claims = RunbookClaims.from_path(write_runbook(tmp_path, RUNBOOK_TEXT))  # Read the fixture once.
    assert claims.headings[0] == (1, "MIST_NETCOOL_ALARM_INTEGRATION")  # The H1 title comes first.
    assert claims.h2_headings == tuple(H2_ORDER)  # The H2 texts keep the contract order.


def test_claims_api_paths_cover_code_spans_blocks_and_tables_without_queries(  # Confirm API paths are found, no query.
    tmp_path: Path,
) -> None:
    """Each Mist API path of the file is listed once, sorted, with no query string.

    Args:
        tmp_path: Folder for the runbook fixture.
    """
    claims = RunbookClaims.from_path(write_runbook(tmp_path, RUNBOOK_TEXT))  # Parse the fixture into the claims.
    assert claims.api_paths == (  # The four paths, sorted, with no query string.
        "/api/v1/orgs/{org_id}/alarms/ack",  # A path in prose, which is listed even without a GET.
        "/api/v1/orgs/{org_id}/alarms/search",  # A path in a table and in the appendix.
        "/api/v1/orgs/{org_id}/devices/events/search",  # A path inside a fenced code block.
        "/api/v1/self/usage",  # A path whose query string is removed.
    )


def test_claims_endpoint_paths_are_the_first_api_path_of_each_row(  # Confirm that each row gives its first API path.
    tmp_path: Path,
) -> None:
    """Appendix A gives the first backticked path that starts with /api/v1/ in each row.

    Args:
        tmp_path: Folder for the runbook fixture.
    """
    claims = RunbookClaims.from_path(write_runbook(tmp_path, RUNBOOK_TEXT))  # Parse the fixture into the claims.
    assert claims.endpoint_paths == ("/api/v1/orgs/{org_id}/alarms/search",)  # One row, one path.


def test_claims_catalog_names_are_keyed_and_an_absent_table_is_empty(  # Confirm that catalog names are keyed by table.
    tmp_path: Path,
) -> None:
    """Each Appendix B table gives its names under its catalog key, and B.4 is empty when absent.

    Args:
        tmp_path: Folder for the runbook fixture.
    """
    claims = RunbookClaims.from_path(write_runbook(tmp_path, RUNBOOK_TEXT))  # Parse the fixture into the claims.
    assert claims.catalog_names["alarm_defs"] == ("ap_offline", "rogue_ap")  # The alarm names, in order.
    assert claims.catalog_names["device_events"] == ("AP_CONNECTED",)  # The device event names.
    assert claims.catalog_names["system_events"] == ()  # The fixture has no B.4 table.


def test_claims_regional_hosts_come_from_the_api_host_column(  # Confirm that the regional hosts come from one column.
    tmp_path: Path,
) -> None:
    """Section 5.5 gives each API host in backticks, in table order.

    Args:
        tmp_path: Folder for the runbook fixture.
    """
    claims = RunbookClaims.from_path(write_runbook(tmp_path, RUNBOOK_TEXT))  # Parse the fixture into the claims.
    assert claims.regional_hosts == ("api.mist.com", "api.gc1.mist.com")  # Two hosts, in order.


def test_claims_identifier_fields_per_family_and_none_gives_no_field(  # Confirm each family lists its identifier.
    tmp_path: Path,
) -> None:
    """Each family gives its identifier fields, and the value none gives an empty tuple.

    Args:
        tmp_path: Folder for the runbook fixture.
    """
    claims = RunbookClaims.from_path(write_runbook(tmp_path, RUNBOOK_TEXT))  # Parse the fixture into the claims.
    assert claims.identifier_fields["6.1 Alarm Search"] == ("id", "org_id")  # The alarm fields.
    assert claims.identifier_fields["6.2 Device Event Search"] == ()  # The text none names no field.


def test_claims_missing_heading_is_absent_from_the_h2_list(  # Confirm that a removed heading is missing from H2.
    tmp_path: Path,
) -> None:
    """A runbook without section 7 has no H2 text for section 7.

    Args:
        tmp_path: Folder for the broken fixture.
    """
    text = RUNBOOK_TEXT.replace("## 7. Alarm and Event Selection\n", "")  # Remove the heading only.
    claims = RunbookClaims.from_path(write_runbook(tmp_path, text))  # Read the broken fixture.
    assert "7. Alarm and Event Selection" not in claims.h2_headings  # The heading is missing.
    assert len(claims.h2_headings) == len(H2_ORDER) - 1  # Every other heading is still found.


def test_claims_wrong_order_is_visible_in_the_h2_list(  # Confirm that a swapped pair of sections shows in the H2 order.
    tmp_path: Path,
) -> None:
    """A runbook with sections 7 and 8 swapped gives the H2 texts in the wrong order.

    Args:
        tmp_path: Folder for the broken fixture.
    """
    swapped = (  # The runbook text with sections 7 and 8 swapped.
        RUNBOOK_TEXT.replace("## 7. Alarm and Event Selection", "@@SECTION_SEVEN@@")  # Park section 7.
        .replace("## 8. Collection Design", "## 7. Alarm and Event Selection")  # Move section 8 up to 7.
        .replace("@@SECTION_SEVEN@@", "## 8. Collection Design")  # Put section 7 after the moved section.
    )
    claims = RunbookClaims.from_path(write_runbook(tmp_path, swapped))  # Read the broken fixture.
    assert claims.h2_headings.index("8. Collection Design") < claims.h2_headings.index(  # Section 8 comes first.
        "7. Alarm and Event Selection"
    )


def test_claims_missing_appendix_a_row_gives_no_endpoint_paths(  # Confirm that a missing row gives no endpoint paths.
    tmp_path: Path,
) -> None:
    """A runbook whose Appendix A table has no row gives no endpoint paths.

    Args:
        tmp_path: Folder for the broken fixture.
    """
    row = "| GET | `/api/v1/orgs/{org_id}/alarms/search` | org | Search alarms | Verified (OpenAPI) |"  # The only row.
    claims = RunbookClaims.from_path(write_runbook(tmp_path, RUNBOOK_TEXT.replace(row, "")))  # Runbook without the row.
    assert claims.endpoint_paths == ()  # No row is left to read.


def test_claims_path_without_a_get_is_still_listed_for_the_openapi_check(  # Confirm a path without GET is still listed.
    tmp_path: Path,
) -> None:
    """A path in prose is listed in api_paths, so the OpenAPI check can judge it.

    Args:
        tmp_path: Folder for the runbook fixture.
    """
    claims = RunbookClaims.from_path(write_runbook(tmp_path, RUNBOOK_TEXT))  # Parse the fixture into the claims.
    assert "/api/v1/orgs/{org_id}/alarms/ack" in claims.api_paths  # The POST path is listed.


def test_claims_missing_file_raises_with_the_file_name_only(  # Confirm that a missing runbook names only the file.
    tmp_path: Path,
) -> None:
    """A missing runbook raises a ValueError that names the file, and no folder of the user.

    Args:
        tmp_path: Folder that does not hold the runbook.
    """
    missing = tmp_path / "missing-runbook.md"  # A path that does not exist.
    with pytest.raises(ValueError, match="missing-runbook.md") as error:  # The error names the file.
        RunbookClaims.from_path(missing)  # The missing file must raise the clear error.
    assert str(tmp_path) not in str(error.value)  # The folder of the test is not in the message.


def test_claims_text_that_is_not_utf8_raises_value_error(  # Confirm that a non-UTF-8 runbook raises a clear error.
    tmp_path: Path,
) -> None:
    """A runbook that is not UTF-8 text raises a ValueError, and no partial parse is returned.

    Args:
        tmp_path: Folder for the broken file.
    """
    path = tmp_path / "bad.md"  # A file with bytes that UTF-8 cannot decode.
    path.write_bytes(b"\xff\xfe\x00bad")  # Invalid UTF-8 bytes.
    with pytest.raises(ValueError, match="bad.md"):  # The decode failure becomes a clear error.
        RunbookClaims.from_path(path)  # The non-UTF-8 file must raise the clear error.


def test_openapi_index_normalizes_placeholders_so_org_id_and_id_match(  # Confirm placeholder names match the path.
    tmp_path: Path,
) -> None:
    """A runbook placeholder and an OpenAPI placeholder with another name refer to the same path.

    Args:
        tmp_path: Folder for the OpenAPI fixture.
    """
    index = OpenApiIndex.from_path(write_openapi(tmp_path, openapi_fixture()))  # Use the real parser on the fixture.
    assert index.has_get("/api/v1/orgs/{org_id}/alarms/search") is True  # The runbook name matches.
    assert index.has_get("/api/v1/orgs/{id}/alarms/search") is True  # Another placeholder name matches too.
    assert index.has_get("/api/v1/orgs/{org_id}/alarms/ack") is False  # A POST-only path has no GET.


def test_openapi_index_resolves_references_for_query_names_and_skips_headers(  # Confirm that $ref parameters resolve.
    tmp_path: Path,
) -> None:
    """Query names come from both parameter levels, a $ref is resolved, and header names are excluded.

    Args:
        tmp_path: Folder for the OpenAPI fixture.
    """
    index = OpenApiIndex.from_path(write_openapi(tmp_path, openapi_fixture()))  # Use the real parser on the fixture.
    assert index.query_parameters("/api/v1/orgs/{org_id}/alarms/search") == ("start", "limit")  # Query names only.


def test_openapi_index_gives_the_operation_identifier_and_empty_for_a_missing_get(  # A path without GET has no name.
    tmp_path: Path,
) -> None:
    """The operationId is returned for a GET path, and an empty value is returned for a path without GET.

    Args:
        tmp_path: Folder for the OpenAPI fixture.
    """
    index = OpenApiIndex.from_path(write_openapi(tmp_path, openapi_fixture()))  # Use the real parser on the fixture.
    assert index.operation_id("/api/v1/orgs/{org_id}/alarms/search") == "searchOrgAlarms"  # The GET name.
    assert index.operation_id("/api/v1/orgs/{org_id}/alarms/ack") == ""  # The POST-only path has no GET name.
    assert index.query_parameters("/api/v1/orgs/{org_id}/alarms/ack") == ()  # No query names for a missing GET.


def test_openapi_index_keeps_each_server_host_once_and_in_file_order(  # Confirm that each server host is kept once.
    tmp_path: Path,
) -> None:
    """The server hosts are the unique host names of the servers list, in file order.

    Args:
        tmp_path: Folder for the OpenAPI fixture.
    """
    index = OpenApiIndex.from_path(write_openapi(tmp_path, openapi_fixture()))  # Use the real parser on the fixture.
    assert index.server_hosts() == ("api.mist.com", "api.eu.mist.com")  # The duplicate is dropped.


def test_openapi_index_missing_file_raises_value_error(  # Confirm that a missing OpenAPI file names the file.
    tmp_path: Path,
) -> None:
    """A missing OpenAPI file raises a ValueError that names the file only.

    Args:
        tmp_path: Folder that does not hold the OpenAPI file.
    """
    with pytest.raises(ValueError, match="openapi-missing.json"):  # The file name is in the message.
        OpenApiIndex.from_path(tmp_path / "openapi-missing.json")  # A missing file must raise the clear error.


def test_openapi_index_invalid_json_raises_value_error(  # Confirm that a file that is not JSON raises a clear error.
    tmp_path: Path,
) -> None:
    """A file that is not JSON raises a ValueError.

    Args:
        tmp_path: Folder for the broken file.
    """
    path = tmp_path / "broken.json"  # A file with text that is not JSON.
    path.write_text("{not json", encoding="utf-8")  # Write the broken text.
    with pytest.raises(ValueError, match="broken.json"):  # The invalid JSON is reported.
        OpenApiIndex.from_path(path)  # The invalid JSON file must raise the clear error.


def test_openapi_index_empty_file_raises_value_error(tmp_path: Path) -> None:  # Empty body must raise a clear error.
    """An empty OpenAPI file raises a ValueError that names the file, and its cause is the JSON parse error.

    Args:
        tmp_path: Folder for the empty OpenAPI file.
    """
    path = tmp_path / "openapi.json"  # Keep the fixture in tmp_path, so the repository stays unchanged.
    path.write_bytes(b"")  # A zero-byte body, which holds no JSON value.
    with pytest.raises(ValueError) as error:  # Expect the loader error, so the test checks its message.
        OpenApiIndex.from_path(path)  # The empty file must raise the clear error.
    assert str(error.value) == "OpenAPI file cannot be read: openapi.json"  # No local path in the message.
    assert isinstance(error.value.__cause__, json.JSONDecodeError)  # The cause is the JSON parse failure.


def test_openapi_index_malformed_body_raises_value_error(tmp_path: Path) -> None:  # Bad JSON must raise a clear error.
    """A body that opens like JSON and then breaks raises a ValueError with the JSON parse error as its cause.

    Args:
        tmp_path: Folder for the malformed OpenAPI file.
    """
    path = tmp_path / "openapi.json"  # Keep the fixture in tmp_path, so the repository stays unchanged.
    path.write_bytes(b'{"paths": {bad json')  # Valid opening text, then text that is not JSON.
    with pytest.raises(ValueError) as error:  # Expect the loader error, so the test checks its message.
        OpenApiIndex.from_path(path)  # The malformed file must raise the clear error.
    assert str(error.value) == "OpenAPI file cannot be read: openapi.json"  # No local path in the message.
    assert isinstance(error.value.__cause__, json.JSONDecodeError)  # The cause is the JSON parse failure.


def test_openapi_index_without_a_paths_object_raises_value_error(  # Confirm that a document without paths is refused.
    tmp_path: Path,
) -> None:
    """A JSON document with no paths object is not an OpenAPI file.

    Args:
        tmp_path: Folder for the OpenAPI fixture.
    """
    with pytest.raises(ValueError, match="no paths object"):  # The structure check fails first.
        OpenApiIndex.from_path(write_openapi(tmp_path, {"openapi": "3.1.0"}))  # No paths object is refused.


def test_openapi_index_reads_the_repository_file_with_twelve_hosts() -> None:  # Confirm the file has twelve hosts.
    """The repository OpenAPI file has the GET alarm search and the twelve regional hosts of the contract."""
    index = OpenApiIndex.from_path(OPENAPI_FILE)  # Index the real file, which is a local read.
    assert index.has_get("/api/v1/orgs/{org_id}/alarms/search") is True  # The alarm search has a GET.
    assert len(index.server_hosts()) == 12  # The contract names twelve regional hosts.


def test_redactor_replaces_the_organization_and_site_identifiers_with_labels() -> None:  # Identifiers become labels.
    """The organization identifier becomes org-1 in any letter case, and the site identifier becomes site-1."""
    redactor = make_redactor()  # Build the redactor that labels each fixture identifier.
    text = f"org {ORG_ID.upper()} site {SITE_ID} plain {ORG_ID.replace('-', '')}"  # Upper case and no hyphens.
    assert redactor.scrub(text) == "org org-1 site site-1 plain org-1"  # Each form becomes its label.


def test_redactor_removes_the_token_value_and_an_empty_token_removes_nothing() -> None:  # Token value is removed.
    """The token value is removed, and an empty token value leaves the text unchanged."""
    token = "Abc123def456ghi789jkl0"  # A fake token value, which is never a real token.
    assert make_redactor(token).scrub(f"value {token} end") == "value [redacted] end"  # The value is removed.
    assert make_redactor("").scrub("unchanged text") == "unchanged text"  # An empty value matches nothing.


def test_redactor_replaces_uuids_emails_and_each_mac_form() -> (  # Confirm that UUIDs, emails, and MACs are replaced.
    None
):
    """A UUID, an email address, and each MAC form are replaced with the marker."""
    redactor = make_redactor()  # Build the redactor that labels each fixture identifier.
    other_uuid = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"  # A UUID that is not the organization or a site.
    assert redactor.scrub(other_uuid) == "[redacted]"  # A UUID is replaced.
    assert redactor.scrub("admin@example.com") == "[redacted]"  # An email address is replaced.
    assert redactor.scrub("5c:5b:35:aa:bb:cc") == "[redacted]"  # A MAC address with colons is replaced.
    assert redactor.scrub("5C-5B-35-AA-BB-CC") == "[redacted]"  # A MAC address with dashes is replaced.
    assert redactor.scrub("5c5b35aabbcc") == "[redacted]"  # Twelve plain hexadecimal digits are replaced.


@pytest.mark.parametrize(
    ("length", "expected_redacted"),
    [(19, False), (20, True)],
)
def test_token_word_form_is_redacted_from_twenty_characters(  # Confirm the word form boundary at twenty characters.
    length: int, expected_redacted: bool
) -> None:
    """The word Token and a space need twenty letters or digits before the value is redacted.

    Args:
        length: Number of letters after the word Token.
        expected_redacted: True when the sentence must be redacted.
    """
    scrubbed = make_redactor().scrub(token_text(length, token_word=True))  # Scrub the sentence.
    assert (scrubbed == "[redacted]") is expected_redacted  # The boundary of the word form.


@pytest.mark.parametrize(
    ("length", "expected_redacted"),
    [(31, False), (32, True), (39, True), (40, True)],
)
def test_token_run_form_is_redacted_from_thirty_two_characters(  # Confirm the run form boundary at thirty-two.
    length: int, expected_redacted: bool
) -> None:
    """A run of letters or digits is redacted from thirty-two characters.

    Args:
        length: Number of letters in the run.
        expected_redacted: True when the run must be redacted.
    """
    scrubbed = make_redactor().scrub(token_text(length, token_word=False))  # Scrub the run.
    assert (scrubbed == "[redacted]") is expected_redacted  # The boundary of the run form.


def test_scrub_recurses_into_objects_arrays_and_keys_and_keeps_numbers() -> None:  # Confirm nested values are scrubbed.
    """Nested objects, arrays, and keys are scrubbed, and numbers and booleans are kept as they are."""
    redactor = make_redactor()  # Build the redactor that labels each fixture identifier.
    value = {f"owner-{ORG_ID}": ["admin@example.com", {"site": SITE_ID, "count": 7, "ok": True}]}  # Nested data.
    assert redactor.scrub(value) == {  # The nested keys and values are scrubbed, numbers are kept.
        "owner-org-1": ["[redacted]", {"site": "site-1", "count": 7, "ok": True}]
    }


def test_detail_is_cut_to_200_characters_after_the_replacements() -> None:  # Confirm a detail is cut after the labels.
    """A detail text is cut to 200 characters, and the cut comes after the identifier label is written."""
    redactor = make_redactor()  # Build the redactor that labels each fixture identifier.
    detail = f"{ORG_ID} " + "plain text " * 40  # The identifier first, then spaced words that no pattern redacts.
    cut = redactor.scrub({"detail": detail})["detail"]  # Scrub the detail entry.
    assert len(cut) == 200  # The cut keeps 200 characters.
    assert cut.startswith("org-1 ")  # The label is written before the cut.


def test_allow_keeps_only_the_allowlisted_keys_and_scrubs_the_values() -> (  # Confirm the allowlist drops unknown keys.
    None
):
    """The allowlist drops each unknown key, and the kept values are scrubbed."""
    record = {  # A record with allowed keys, unknown keys, bad items, and an unknown catalog.
        "schema_version": "1",  # A top-level key of the contract.
        "organization_label": "org-1",  # A top-level key of the contract.
        "secret_dump": {"body": "not allowed"},  # An unknown top-level key, which must be dropped.
        "settings": {"max_pages": 3, "runbook": "docs.md", "extra": "dropped"},  # One unknown settings key.
        "checks": [{"check_id": "SMK-01", "detail": ORG_ID, "raw": "dropped"}, "not an object"],  # Bad item kept out.
        "catalogs": {
            "alarm_defs": {"status_code": 200, "item_count": 1, "items": [{"key": "a", "example": {"x": 1}}]},
            "unknown_catalog": {"status_code": 200, "item_count": 0, "items": []},  # An unknown catalog is dropped.
        },
        "observations": {"q6_last_trouble_present": True, "q9_extra": "dropped"},  # One unknown observation key.
    }
    kept = make_redactor().allow(record)  # Filter the record.
    assert "secret_dump" not in kept  # The unknown top-level key is dropped.
    assert kept["settings"] == {"max_pages": 3, "runbook": "docs.md"}  # Only the allowed settings remain.
    assert kept["checks"] == [{"check_id": "SMK-01", "detail": "org-1"}]  # Only allowed check keys remain.
    assert kept["catalogs"] == {  # Only the known catalog remains, without its example member.
        "alarm_defs": {"status_code": 200, "item_count": 1, "items": [{"key": "a"}]},  # The example is dropped.
    }
    assert kept["observations"] == {"q6_last_trouble_present": True}  # The unknown observation key is dropped.


def test_writer_writes_sorted_utf8_json_with_a_final_newline_and_creates_the_folder(  # Confirm sorted JSON output.
    tmp_path: Path,
) -> None:
    """The writer creates the folder, writes sorted UTF-8 JSON with a final newline, and returns the path.

    Args:
        tmp_path: Folder for the evidence file.
    """
    target = tmp_path / "nested" / "folder" / "record.json"  # A path whose folders do not exist yet.
    written = EvidenceWriter(target).write({"zeta": "z", "alpha": "a-value"})  # Write two ASCII values.
    assert written == target  # The writer returns the path that it wrote.
    text = target.read_text(encoding="utf-8")  # Read the file back as UTF-8.
    assert text == '{\n  "alpha": "a-value",\n  "zeta": "z"\n}\n'  # Sorted keys, indent two, final newline.


def test_writer_rejects_a_record_that_is_not_an_object(  # Confirm that a non-object value is refused first.
    tmp_path: Path,
) -> None:
    """A value that is not an object is refused before any file is touched.

    Args:
        tmp_path: Folder that must stay empty.
    """
    target = tmp_path / "never.json"  # The path that must not be written.
    not_an_object: Any = ["not", "an", "object"]  # A list that the writer must refuse.
    with pytest.raises(ValueError, match="object"):  # The input check fails at once.
        EvidenceWriter(target).write(not_an_object)  # The list must be refused before any file is written.
    assert not target.exists()  # No file was created.


def test_writer_raises_os_error_when_the_target_is_a_directory(  # Confirm that a folder target raises an OS error.
    tmp_path: Path,
) -> None:
    """A target that is an existing folder cannot be written, so the writer raises an OSError.

    Args:
        tmp_path: Folder that holds the existing target folder.
    """
    folder = tmp_path / "already-a-folder"  # A folder where the file should be.
    folder.mkdir()  # Create the folder before the write.
    with pytest.raises(OSError):  # The write fails with an operating-system error.
        EvidenceWriter(folder).write({"key": "value"})  # The folder path cannot be written as a file.


def test_default_path_uses_the_utc_stamp_for_an_aware_moment(  # Confirm that an offset moment is converted to UTC.
    tmp_path: Path,
) -> None:
    """A moment with another offset is converted to UTC before the stamp is written.

    Args:
        tmp_path: Stands in for the repository root.
    """
    offset = timezone(timedelta(hours=2))  # A moment two hours ahead of UTC.
    moment = datetime(2026, 11, 25, 16, 30, 5, tzinfo=offset)  # 16:30:05 at +02:00, which is 14:30:05 UTC.
    path = EvidenceWriter.default_path(tmp_path, moment)  # Build the default path.
    assert path == tmp_path / "test-artifacts" / "netcool-runbook-smoke" / "20261125T143005Z.json"  # The UTC stamp.


def test_redactor_with_an_empty_organization_identifier_changes_no_text() -> (  # An empty identifier changes no text.
    None
):
    """An empty organization identifier would match everywhere, so the redactor skips it."""
    redactor = EvidenceRedactor(organization_id="", site_ids=(), token_value="")  # Nothing to replace.
    assert redactor.scrub("plain text") == "plain text"  # The text stays as it is.


def test_writer_default_path_is_under_the_test_artifacts_folder(  # Confirm the default path is under test-artifacts.
    tmp_path: Path,
) -> None:
    """The default path sits under test-artifacts/netcool-runbook-smoke of the root.

    Args:
        tmp_path: Stands in for the repository root.
    """
    moment = datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC)  # A UTC moment with one-digit fields.
    path = EvidenceWriter.default_path(tmp_path, moment)  # Build the default path.
    assert path.parent == tmp_path / "test-artifacts" / "netcool-runbook-smoke"  # The fixed folder.
    assert path.name == "20260102T030405Z.json"  # Zero-padded UTC stamp.


def test_default_path_rejects_a_naive_moment(  # Confirm that a moment without a time zone is refused.
    tmp_path: Path,
) -> None:
    """A moment with no time zone cannot be named in UTC, so it is refused.

    Args:
        tmp_path: Stands in for the repository root.
    """
    with pytest.raises(ValueError, match="time zone"):  # The naive moment has no offset.
        EvidenceWriter.default_path(tmp_path, datetime(2026, 11, 25, 14, 30, 5))  # A naive time must be refused.
