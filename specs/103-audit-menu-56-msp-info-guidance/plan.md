# Plan for MSP Info Guidance (Menu 56)

## Approach

- Invoke OrgConfigExporter.msp with selected org_id, collect returned guidance items, normalize them to a concise schema, and present to user via MistHelper menu with two output options: plain text (default) and CSV (optional flag).
- Validate returned items against expected schema; filter/remove any sensitive values; format recommendations and references.

## Milestones

1. Hook CLI/menu entry to call OrgConfigExporter.msp and pass org_id (small smoke test).
2. Implement normalization/validation of returned guidance items.
3. Implement CLI output renderers: plain text summary and CSV export (flag-driven).
4. Add unit tests and basic integration test against a sample fixture.
5. Update README/menu index and add spec files in specs/103-audit-menu-56-msp-info-guidance.

## Deliverables

- CLI menu entry for "MSP Info Guidance" that calls OrgConfigExporter.msp.
- Output formatting utilities (text and CSV) and a small schema validator.
- Unit and integration tests (fixtures) verifying acceptance criteria.
- Spec files placed under the specified spec_dir.

## Verification Plan

- Unit tests validate schema normalization, sensitive-field filtering, and CSV generation.
- Integration test: run the menu against a saved fixture of OrgConfigExporter.msp output and assert acceptance criteria (non-empty guidance -> success message; empty->graceful notice).
- Manual smoke run documented in README change.
