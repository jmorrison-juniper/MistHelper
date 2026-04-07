# Plan to complete Offline Device Report (menu_id: 158)

## Objective
Prepare all specification, schema, tests, and artifacts so the implementation phase can be executed with low risk and clear acceptance criteria. Stop before code implementation; produce everything the implement step will need.

## High-level phases
1. Spec finalization (current) — produce spec.md (this file). Milestone: stakeholders sign-off.
2. Schema & PK strategy definition — create DDL and ENDPOINT_PRIMARY_KEY_STRATEGIES entry draft. Milestone: DDL file added to spec_dir.
3. Test scaffolding — ensure unit and integration test plans and skeletons exist; confirm tests/test_offline_device_reporter.py baseline and create SQL verification tests (fixtures). Milestone: tests added to specs/ and CI hooks noted.
4. Fixtures & sample data — create representative sample JSON/CSV fixtures for offline devices. Milestone: fixtures available in spec_dir.
5. Documentation & runbook — create a README in spec_dir describing how to run tests and verify SQL upsert behaviour. Milestone: README created.
6. Review & handoff — peer review of spec, schema, tests; prepare a single implement ticket containing the PR checklist. Milestone: implement-ticket with all artifacts attached.

## Dependencies and sequencing
- Schema must be defined before integration SQL verification tests can be finalized.
- Test scaffolding depends on fixtures; create fixtures early.
- README depends on final DDL and test commands.

## Success milestones
- M1: Spec.md and plan.md checked in under specs/091-audit-menu-158-offline-report/
- M2: Schema DDL draft saved and PK strategy documented
- M3: Integration test skeleton + SQL verification assertions added
- M4: Sample fixtures created
- M5: Review completed and implement-ticket created (ready-to-implement)

## Risks & mitigations
- Ambiguity about whether historical snapshots are required — mitigation: default to composite_pk (history) and note alternative in spec.
- Test flakiness due to system time — mitigation: use fixed report_timestamp fixture in tests or pass explicit run_id to reporter during tests.

## Exit criteria for planning phase
- All artifacts (spec, DDL, tests, fixtures, README) are present in specs/091-audit-menu-158-offline-report/ and pass a quick lint/check (no runtime code changes). Implementation may begin once artifacts are approved.
