# Runbook structure contract

The runbook writers and the parser of the smoke test obey this file. Each heading string, column name, and row label is exact, and each comparison is case-sensitive. A change to this file needs a matching change to the parser and to the offline document test.

## 1. Document title

The runbook has one H1 heading. The heading string is:

```text
# MIST_NETCOOL_ALARM_INTEGRATION
```

## 2. Section headings

The runbook has these H2 headings, in this order. The parser requires each heading string. The runbook has no other H2 heading.

```text
## 1. Overview
## 2. How to Use This Runbook
## 3. Purpose and Scope
## 4. Architecture
## 5. Prerequisites
## 6. Mist Data Sources
## 7. Alarm and Event Selection
## 8. Collection Design
## 9. Netcool Integration
## 10. AP Warning Report (Menu 307)
## 11. NOC Operating Procedures
## 12. Troubleshooting
## 13. Verification and Smoke Test
## 14. Acceptance Criteria and UAT Plan
## 15. Open Decisions
## Appendix A. Endpoint Reference
## Appendix B. Verified Catalog Names
## Appendix C. Sample Payloads
## Appendix D. Glossary
## Appendix E. Revision History
```

The runbook has no section 0.

Appendix D holds one table with the header `| Term | Meaning |`. Each row holds one term or abbreviation of the runbook. Appendix E holds one table with the header `| Version | Date | Author | Change |`.

## 3. Section 1 tables

Section 1 holds one field table and one verification legend. The field table has this header row:

```text
| Field | Value |
```

The field table has these row labels, in this order: `Document type`, `Platform`, `Purpose`, `Audience`, `Author`, `Version`, `Date`, `Status`, `Verification`. The `Date` value is a UTC timestamp in ISO 8601 form. The `Author` value is `Joseph Morrison`.

The verification legend has this header row:

```text
| Mark | Meaning |
```

The legend has these six marks, in this order. Write each mark exactly as shown, with no change of case or spelling.

```text
Verified (live)
Verified (OpenAPI)
Verified (MistHelper)
Verified (vendor documentation)
Proposal
Open decision
```

## 4. Contents list

The contents list follows the field table and the legend, in section 1. It is a bullet list with one link for each H2 heading.

Each link uses the GitHub anchor of its heading. The anchor rule has three steps. Lowercase the text. Remove each character that is not a letter, a digit, a space, or a hyphen. Replace each space with a hyphen.

| Heading | Anchor |
| --- | --- |
| `## 1. Overview` | `#1-overview` |
| `## 10. AP Warning Report (Menu 307)` | `#10-ap-warning-report-menu-307` |
| `## Appendix A. Endpoint Reference` | `#appendix-a-endpoint-reference` |

## 5. Section 5.5 table

Section 5.5 has this H3 heading. The parser uses it to read the regional API hosts.

```text
### 5.5 Regional API Hosts
```

The table has this header row. The column `API host` holds one host name in backticks for each row.

```text
| Region | API host | Verification |
```

The host column holds the 12 hosts of the `servers` list of the OpenAPI file. The smoke test check SMK-02 compares this set with the `servers` list. The sets must be equal.

## 6. Section 6 family headings

Section 6 has these H3 headings, in this order.

```text
### 6.1 Alarm Search
### 6.2 Device Event Search
### 6.3 Mist Edge Event Search
### 6.4 System Event Search
### 6.5 Definition Catalogs
### 6.6 Webhook Topics
```

Each family heading from 6.1 to 6.4 has one table with this header row:

```text
| Fact | Value |
```

Each family table has these row labels, in this order:

```text
Organization path
Site path
Count path
Query parameters
Pagination
Identifier fields
Time field
Clear role
Meaning of zero results
Scope
Verification
```

Each path value holds one path in backticks. The `Identifier fields` value holds each field name in backticks, separated by commas. The value `none` appears when the family has no identifier field.

The headings 6.5 and 6.6 each hold one table with the header `| Fact | Value |`. The table of 6.5 has the row labels `Catalog paths` and `Verification`. The table of 6.6 has the row labels `Topic source` and `Verification`. The parser reads only the family tables of 6.1 to 6.4.

## 7. Appendix A table

Appendix A holds one table with this header row:

```text
| Method | Path | Scope | Purpose | Verification |
```

The `Method` column holds `GET` without backticks, because each row is a GET path. The `Path` column is the second column, and it holds one path in backticks. The parser reads the first backticked value that starts with `/api/v1/` in each row.

## 8. Appendix B tables

Appendix B has these H3 headings. Heading B.4 exists only when the live system event catalog holds at least one item. The parser treats an absent B.4 as no error. The offline document test accepts B.4 present or absent. The live run checks the names of B.4 (SMK-05).

```text
### B.1 Alarm Types
### B.2 Device Event Types
### B.3 Mist Edge Event Types
### B.4 System Event Types
### B.5 Webhook Topics
```

Each Appendix B table has this header row. The name column holds one name in backticks.

```text
| Name | Use in this runbook |
```

The parser maps each heading to one catalog key:

| Heading | Catalog key |
| --- | --- |
| `B.1 Alarm Types` | `alarm_defs` |
| `B.2 Device Event Types` | `device_events` |
| `B.3 Mist Edge Event Types` | `mxedge_events` |
| `B.4 System Event Types` | `system_events` |
| `B.5 Webhook Topics` | `webhook_topics` |

## 9. Diagrams and placeholders

Each diagram is a fenced block that starts with the language name `mermaid`. The first line of the diagram is `flowchart` or `sequenceDiagram`. Do not use any other diagram type.

Each identifier in the runbook is one of these placeholders:

- `{api_host}`
- `{org_id}`
- `{site_id}`
- `{device_mac}`
- `{token}`
- `{alarm_id}`
- `{event_id}`
- `{mxedge_id}`
- `{webhook_id}`
- `{start_epoch}`
- `{end_epoch}`

## 10. Parse rules

The parser reads the runbook once, in UTF-8. The parser applies these rules.

1. A heading line starts with one, two, or three `#` characters, then one space. The parser compares the text after the space with the heading strings of this file.
2. The parser ignores each line between two fence markers when it reads headings and tables.
3. A table row starts with a pipe and ends with a pipe. A separator row contains only dashes, colons, pipes, and spaces. The parser skips each separator row.
4. The parser trims each cell. A backtick span holds one value, and the span stays on one line.
5. `endpoint_paths()` returns the first backticked `/api/v1/` value of each row of Appendix A.
6. `catalog_names()` returns, for each catalog key of section 8, the first backticked value of each row of its table.
7. `regional_hosts()` returns each backticked value of the `API host` column of section 5.5.
8. `identifier_fields()` returns, for each family of sections 6.1 to 6.4, the backticked names of the `Identifier fields` row.
9. `required_headings()` returns the H1 string, the H2 strings of section 2, and the H3 strings of sections 5.5, 6.1 to 6.6, and 8. It omits B.4 when the live catalog holds no item.

Failure rules for the smoke test:

- A missing heading gives check SMK-02 the status `FAIL`. The detail names the missing heading.
- A runbook file that does not exist gives the status `SKIP` with the cause `runbook not found`, when the operator did not pass `--runbook`. The run continues.
- A runbook file that does not exist, when the operator passed `--runbook`, stops the run with exit code 2.

## 11. Checks of the offline document test

The offline document test (`tests/unit/scripts/netcool_runbook_smoke/test_netcool_runbook_document.py`) runs with no token and no network access. The test applies these checks.

- Each Mist API path in the runbook, in code spans, code blocks, and tables, has a GET operation at that path in the OpenAPI file.
- Each of the 25 operations of the specification has a GET operation at its declared path in the OpenAPI file. Its SDK module defines a function with the same name.
- Each heading of this file exists in the runbook.
- An H3 heading of the runbook starts with each of these subsection numbers: 4.4, 5.4, 5.5, 8.4, 12.2, 12.3, 12.4, and 12.5. The test checks each number and does not compare the title text.
- The privacy scan finds no UUID, no MAC address, no email address, and no token.
- A token pattern is the word `Token`, a space, and 20 or more letters or digits.
- A token pattern is also any run of 40 or more letters or digits. The threshold is 40 characters, because the runbook holds only written text. The evidence redactor uses 32 characters, because it scrubs response text (`contracts/evidence.md`, section 7).
- The scan reports each match by line number and kind. The scan never prints the matched value.
- The offline scan checks the pattern classes UUID, MAC address, email address, and token. A customer identifier is one of these values.
  - An organization ID.
  - A site ID.
  - A device MAC address.
  - A device serial.
  - A device name.
  - A site name.
  - A customer name.
  - A person name of a customer.
  - An email address.
  - A token.
- The coordinator runs a local name scan, and the scan stays local by design. The scan uses a private term list that no commit holds.
- The test prints the number of paths, headings, and lines that it examined. The test fails when it cannot read the runbook or the OpenAPI file.
- A zero count of paths, headings, or lines gives a failure. The test never reports a pass for zero items examined.
