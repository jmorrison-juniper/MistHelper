# Plan

## Overview
Deliver a fully tested, SQL-compliant exporter for VPN peer path statistics anchored on OrgDeviceStatsExporter.vpn_peer_stats. Work stops before IMPLEMENT step; plan covers discovery, design, and prep tasks needed to implement safely.

## High-level phases
1. Spec (done) — capture current state, acceptance criteria, PK recommendation, and test plan.
2. Design & Discovery (this phase)
   - Confirm API response schema via fixtures and API docs.
   - Finalize composite primary-key fields.
3. Preparation (pre-implementation tasks)
   - Create fixtures, test scaffolding, and SQL verification scripts.
   - Produce spec_dir artifacts and review checklist.
4. Implement (NOT part of this deliverable)
   - Refactor exporter to call DataExporter.write_with_format_selection, add PK strategy to ENDPOINT_PRIMARY_KEY_STRATEGIES, implement upsert SQL, add indexes, and add unit/integration tests.
5. Validate & Release (post-implement)
   - Run test suite, CI jobs, and update README/menu docs.

## Milestones
- M1: API fixtures and schema confirmed (Design)
- M2: Primary key strategy approved and documented (Design)
- M3: Test scaffolding and SQL verification queries created in specs/027-audit-menu-15-vpn-peer-stats (Preparation)
- M4: Ready-to-implement PR checklist completed (Preparation)

## Dependencies
- Access to API sample responses (real or recorded fixtures).
- Existing DataExporter and APIDataFetcher helpers (already in codebase).
- Test runner and temporary SQLite capability in CI.

## Non-goals in this phase
- No code changes to exporter or database configs.
- No committing of implementation code or DB migrations.

## Risks & mitigations
- Risk: API returns fields with inconsistent names (peer vs. peer_id). Mitigation: capture multiple fixtures and include normalization mapping in test fixtures.
- Risk: Choosing wrong PK fields. Mitigation: validate against fixtures and analytics query patterns in design phase.

## Deliverables for implement-ready handoff
- specs/027-audit-menu-15-vpn-peer-stats: API fixtures, PK recommendation, SQL verification scripts, test templates, PR checklist, and reviewers list.
- tasks.md with prioritized actionable tasks (below).
