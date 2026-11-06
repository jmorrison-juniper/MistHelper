# Implementation Plan: Reject Failed HTTP Data in Rogue DHCP Scans

**Branch**: `jmorrison-juniper-fix-4560-rogue-dhcp-http-503` | **Date**: 2026-11-06 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `specs/numbered/0/0/1/2/1/2/2/0/4560-rogue-dhcp-http-response/spec.md`.

## Summary

Check each Mist SDK response before pagination. Reject non-success status values so an error body cannot become a rogue DHCP finding. Keep plain list test responses and successful SDK responses unchanged.

## Technical Context

**Language/Version**: Python 3.13 or newer
**Primary Dependencies**: mistapi 0.64.x
**Storage**: No change
**Testing**: pytest
**Target Platform**: Windows, macOS, and Linux
**Project Type**: Python command-line tool
**Performance Goals**: No additional request or pagination call.

**Constraints**: Use the existing Mist SDK. Do not call Mist during validation.
**Scale/Scope**: One status check in the rogue DHCP scanner and its unit tests.

## Constitution Check

- **Structure**: Pass. The change updates one existing method and its existing test module.
- **Safety**: Pass. The scanner rejects failed SDK responses before it reads their bodies.
- **Mist transport**: Pass. Existing SDK endpoints and authentication remain unchanged.
- **Tests**: Pass after implementation. Unit tests cover 4xx, 5xx, successful responses, and site failure reporting.
- **Process records**: Pass. The feature uses the managed numeric route and adds one issue-specific release fragment. The checked route parents contain fewer than five children.
- **Process-folder remediation**: Keep existing folder debt unchanged. Track future reduction through the process-folder baseline guard.
- **Open PR ownership**: Pass. No open PR owns the scanner or its rogue DHCP unit tests.

## Phase 0: Research

### Decision: Reject failed responses before pagination

The scanner currently sends every SDK response to `mistapi.get_all`. The installed SDK response exposes an HTTP status, and a valid-looking error body can still contain a `results` list. Check the status before calling the paginator.

### Decision: Preserve explicit failure reporting

Raise an error for a response without a valid 2xx status. An organization failure stops the scan. The existing site fan-out catches a site failure and adds that site to the failed-site result.

### Alternatives considered

- Returning an empty page would hide failed reads as clean results. Reject this option.
- Parsing the body and filtering its rows would still trust a failed response. Reject this option.
- Changing SDK calls or adding direct HTTP would expand scope and violate the existing transport contract. Reject this option.

## Phase 1: Design

### Mist response contract

An SDK response with an integer status from 200 through 299 may reach pagination. A response with any other status, an absent status, or a malformed status must raise before pagination. Existing list-based test doubles remain supported.

### Verification

Run the rogue DHCP scanner unit tests. Include 4xx and 5xx responses that carry plausible alarm data. Confirm the paginator does not receive those responses. Confirm a successful response still yields the finding. Run Ruff and Black checks on changed Python files.

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
tests/unit/security/rogue_dhcp/test_scanner.py
changelog.d/issue-4560-rogue-dhcp-http-503-data.md
```

**Structure Decision**: Keep the status check in the scanner’s shared response-reading path. Keep regression tests in the existing rogue DHCP scanner module. Add the required issue-specific changelog fragment.

## Complexity Tracking

No constitution violations require an exception.
