---
description: "Reject HTTP error responses before endpoint exporters interpret payloads."
---

# Feature Specification: Empty Export Endpoint Response Handling

**Feature Branch**: `fix-empty-export-endpoints`

**Created**: 2026-10-06

**Status**: Draft

**Input**: Issues #4038 and #4043 identify empty output from endpoint exporters.

## User Scenarios and Testing

### User Story 1 - Report a failed site device request

As an operator, I need `exportSiteDevices` to report an HTTP failure instead of a successful empty export.

**Independent Test**: Run the endpoint family exporter test with a response that has HTTP 401 and an error body.

### User Story 2 - Share one HTTP status decision

As a maintainer, I need both exporter families to use one strict 2xx status gate.

**Independent Test**: Run the shared response status tests for missing, mocked, successful, and failed statuses.

## Requirements

- The shared helper MUST return `False` for a missing or non-integer status.
- The shared helper MUST return `False` for every integer status from 200 through 299.
- The shared helper MUST return `True` for every other integer status.
- A failed status MUST log `! Error fetching <operation>: HTTP <status> from <url>`.
- `EndpointFamilyExporter._run` MUST stop before `mistapi.get_all` for a failed status.
- `SimpleEndpointExporter._run` remains a follow-up for issue #4043 because another branch owns that file.

## Success Criteria

- An HTTP error body without `results` cannot produce an empty successful export.
- The #4038 endpoint test proves the response parser is not called after a failed status.
- The shared helper has direct coverage for all status classes.
