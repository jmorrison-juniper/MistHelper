# Security and Privacy Requirements Checklist: Versioned Proposal Review and Safe Export

**Purpose**: Check that the security and privacy requirements of version 2 are complete and testable.

**Created**: 2026-11-26

**Feature**: [spec.md](../../spec.md)

## Credential and Secret Handling

- [x] Exports omit secret values. FR-016 states the rule, and tests 7 and 17 check it.
- [x] Logs omit source text, template name, unsupported values, and secrets. FR-016 states the rule, and test 17 checks it.
- [x] The browser session stores digests only. The data model names each session key. Test 12 checks the review keys.
- [x] The response holds no digest of the source content. Decision D-4 records the reason.
- [x] Unsupported items keep a line number and a label only. Research rows 74 and 75 cite the code.
- [x] A session that cannot be read fails closed. The data model and the spec Caution record the behavior.
- [x] Review and export state expire 15 minutes after the preview or the review. FR-023 states the rule, and test 19 checks it.
- [x] The portal secret fallback stays unchanged. Decision D-15 records the human owner decision.

## Request Boundaries

- [x] Each version 2 POST route requires the CSRF token. FR-017 states the rule, and test 15 checks it.
- [x] The request bound applies to version 2 routes through the converter prefix. Test 20 checks it.
- [x] Version 2 bodies must hold the exact key set and version. FR-012 states the rule, and test 14 checks it.
- [x] The source limit stays at 16 MiB. The edge cases name the HTTP status for each limit.

## Data Exposure and Offline Behavior

- [x] Version 2 routes open no network connection. FR-014 states the rule, and test 16 checks it.
- [x] Version 2 routes write no file. FR-014 states the rule, and test 16 checks it.
- [x] The version 2 export does not call `DataExporter`. FR-015 states the rule, and test 16 checks it.
- [x] Version 2 responses send `Cache-Control: no-store`. FR-019 states the rule, and test 8 checks it.
- [x] The browser script renders each value with `textContent`. The UI contract states the rule.

## Notes

- Each checked item names the requirement or the contract section that holds the rule.
- The checks describe planned behavior. The tests in tasks T004, T005, and T011 prove each item when they run.
- The tests use synthetic values only. No live credential appears in the test plan.
