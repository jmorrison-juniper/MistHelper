# Plan

## Goal
Take the menu item "Zone Configuration Analysis" from its current state (metadata + notes) to a ready-to-implement, fully-specified work item with tests and SQL schema defined.

## High-level phases
1. Discovery & Verification (analysis)
   - Verify ZoneConfigurationAnalyzer.analyze exists and capture its signature and return structure.
   - Confirm what unique identifiers the analyzer returns (id, name, org_id, site_id, timestamp).
   - Decide exact primary_key column set.
   - Milestone: API function verified and PK strategy decided.

2. Spec Completion
   - Write spec documents (spec.md) into specs/089-audit-menu-119-zone-analysis and include SQL schema draft and upsert examples.
   - Milestone: spec files added to repo (design-only changes).

3. Test Scaffolding
   - Produce unit & integration test plans and create test stubs/fixtures (no implementation changes yet).
   - Draft SQL verification tests (create DB, seed, run upsert logic simulation using sample SQL). 
   - Milestone: tests scaffolded and CI hooks identified.

4. Implementation Preparation
   - Register endpoint metadata (ENDPOINT_PRIMARY_KEY_STRATEGIES entry) in design docs or config draft for developer implementation.
   - Prepare tickets/PR description and code change checklist (what to modify: call writer with api_function_name, ensure exporter uses chosen PK strategy).
   - Milestone: Implementation ticket(s) ready and reviewed.

5. Review & Sign-off
   - Stakeholder review (NOC, QA, platform)
   - Finalize docs and move to IMPLEMENT phase (outside this task).

## Dependencies & sequencing
- Discovery & Verification must complete before Spec Completion and PK registration.
- Test Scaffolding depends on verified analyzer return schema.
- Implementation Preparation depends on all previous phases.

## Risks & mitigations
- Risk: Analyzer returns no stable ID. Mitigation: include fallback composite PK recommendation and example mapping rules (e.g., use zone name + org_id). 
- Risk: Exporter doesn't accept api_function_name. Mitigation: document required exporter change and include example call signature in implementation ticket.

## Success criteria for this plan
- Clear, actionable spec.md, plan.md, and tasks.md in specs/089-audit-menu-119-zone-analysis
- Verified api_function_name and chosen PK strategy documented
- Test scaffolding and SQL schema drafts present, enabling a well-scoped implement phase

