# Plan: From current state to Done

## Goals
- Verify API mapping and primary keys
- Finalize PK strategy and SQL schema
- Prepare tests, fixtures, and documentation so IMPLEMENT step can proceed safely

## High-level phases
1. Discovery & Verification (milestone: Verified API names & example payloads)
   - Identify exact Mist API function(s) the exporter should call.
   - Collect representative API response samples and record canonical response fields.
   - Output: file in spec_dir with API names and example payloads.

2. Design & Schema (milestone: Approved PK strategy and table schemas)
   - Choose primary key strategy per endpoint and document reasons.
   - Draft SQL table schemas and upsert patterns (INSERT OR REPLACE / ON CONFLICT DO UPDATE).
   - Output: SQL schema + mapping doc in spec_dir.

3. Test & Fixture Preparation (milestone: Tests defined and fixtures available)
   - Create unit test templates and integration test plans (using fixtures), but DO NOT implement exporter changes.
   - Prepare fixtures (golden JSON responses) and expected CSV/SQL golden outputs.
   - Output: tests/fixtures/* and tests/templates/* in spec_dir.

4. Documentation & Review (milestone: Ready-for-implement PR)
   - Update README and menu index with verified api_function_name and PK strategy.
   - Create a pre-implement checklist (lint, py_compile, test plan steps).
   - Peer review: stakeholder signoff on spec + tests.

5. Pre-Implement Acceptance
   - All stakeholders review and sign off; CI test templates validated locally.
   - Merge spec-only changes to trunk/branch; create implementation issue/PR template.

## Dependencies & sequencing
- Discovery & Verification must complete before Design & Schema.
- Test & Fixture Preparation depends on the Design & Schema outputs.
- Documentation & Review depends on all prior phases.

## Exit criteria for this planning stage
- API function names and sample payloads recorded.
- Primary key strategy chosen and documented per exported entity.
- Test fixtures and test templates exist in the spec_dir.
- Test scaffolding and CI hooks validated.

## Rough timeline (example, subject to change)
- Discovery: 1-2 days
- Design & Schema: 1 day
- Tests & Fixtures prep: 1-2 days
- Documentation & Review: 1 day

---
(Stop here. Implementation tasks and code changes are in the next phase.)