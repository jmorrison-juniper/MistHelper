# Implementation Plan: Reject Failed HTTP Data in Rogue DHCP Scans

**Branch**: `jmorrison-juniper-fix-4560-rogue-dhcp-http-503` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/2/1/2/2/0/4560-rogue-dhcp-http-response/spec.md`.

## Summary

Check each Mist SDK response before reading its body.

Reject failed statuses and malformed page data.

Mark partial scans as incomplete. This prevents a false clean result.

## Technical Context

**Language/Version**: Python 3.13 or newer.
**Primary Dependencies**: mistapi 0.64.x.
**Storage**: No change.
**Testing**: pytest.
**Target Platform**: Windows, macOS, and Linux.
**Project Type**: Python command-line tool.
**Performance Goals**: No additional request or pagination call.

**Constraints**: Use the existing Mist SDK. Do not call Mist during validation.
**Scale/Scope**: Per-page response validation, operator reporting for incomplete scans, and focused unit tests.

## Constitution Check

- **Structure**: Pass. The change updates the existing scanner and operation paths with their unit tests.
- **Safety**: Pass. The scanner rejects failed SDK responses before it reads their bodies.
- **Mist transport**: Pass. Existing SDK endpoints and authentication remain unchanged.
- **Tests**: Pass after implementation. Unit tests cover 4xx, 5xx, pagination, failed sites, and incomplete scan reporting.
- **Process records**: Pass. The feature uses the managed numeric route and adds one issue-specific release fragment. The checked route parents contain fewer than five children.
- **Process-folder remediation**: Keep existing folder debt unchanged. Track future reduction through the process-folder baseline guard.
- **Open PR ownership**: Pass. No open PR owns the scanner or its rogue DHCP unit tests.

## Phase 0: Research

### Decision: Reject failed responses before pagination

The scanner currently sends each first SDK response to `mistapi.get_all`. The installed `get_all` calls `get_next` and appends later response data without checking its status. Check each response before reading its body.

### Decision: Preserve explicit failure reporting

Raise an error for a response without a valid 2xx status. An organization failure stops the scan. The existing site fan-out catches a site failure and adds that site to the failed-site result.

### Decision: Mark partial scan results as incomplete

Keep valid findings from successful requests when another site request fails. Name each failed site, label any exported rows as partial, and do not report an incomplete empty result as clean.

### Alternatives considered

- Returning an empty page would hide failed reads as clean results. Reject this option.
- Parsing the body and filtering its rows would still trust a failed response. Reject this option.
- Changing SDK calls or adding direct HTTP would expand scope and violate the existing transport contract. Reject this option.

## Phase 1: Design

### Mist response contract

An SDK response with an integer status from 200 through 299 may contribute records. A response with any other status, an absent or malformed status, or an invalid page body must raise before the scanner reads that page. Existing list-based test doubles remain supported.

### Verification

Run the rogue DHCP scanner and operation unit tests. Include first-page and later-page failures that carry plausible alarm data. Confirm malformed later bodies fail, successful later pages contribute records, and operator messages identify incomplete results. Run Ruff and Black checks on changed Python files.

## Project Structure

### Documentation

```text
specs/numbered/0/0/1/2/1/2/2/0/4560-rogue-dhcp-http-response/
  spec.md
  plan.md
  tasks.md
  design/
    research.md
    data-model.md
    quickstart.md
    checklists/
      requirements.md
```

### Source Code

```text
src/operations/protection/security/rogue_dhcp/scanner.py
src/operations/protection/security/rogue_dhcp/operation.py
tests/unit/security/rogue_dhcp/test_scanner.py
tests/unit/security/rogue_dhcp/test_operation.py
changelog.d/issue-4560-rogue-dhcp-http-503-data.md
```

**Structure Decision**: Keep status and body checks in the scanner’s shared page-reading path. Use the SDK next-page function so the scanner can validate each response. Keep operator report rules in the existing operation class. Keep regression tests in the existing rogue DHCP unit modules. Add the required issue-specific changelog fragment.

## Complexity Tracking

No constitution violations require an exception.
