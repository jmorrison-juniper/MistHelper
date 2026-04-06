# Plan

## Goal
Prepare specification, design, and test scaffolding so implementation of Site Inventory Health Analysis (menu 121) can proceed safely and consistently with SQL upsert semantics and CI validation.

## High-level phases (spec -> plan -> tasks -> implement)
1. Discovery & Verification (verify current PK entries, API function signature)
   - Milestone: confirm PK entries and example output shapes
   - Dependency: access to existing PK registry and codebase
2. Design & PK Strategy (finalize keys, schema, and upsert pattern)
   - Milestone: approved PK strategy and SQL schema draft
   - Dependency: results from discovery
3. Test & Export Scaffolding (create test fixtures, SQL verification scripts, and test cases)
   - Milestone: unit and integration test skeletons and SQL verification scripts present in repo
   - Dependency: schema draft and analyzer output shape
4. Documentation & Review (place spec files, update README, stakeholder review)
   - Milestone: spec directory populated, reviewers assigned
   - Dependency: completed tests scaffolding and schema
5. Ready for Implement (handoff)
   - Deliverables: completed spec.md, plan.md, and tasks.md (this step), test templates, SQL migration skeletons

## Milestones & checkpoints
- M1: PK audit complete and API signature validated
- M2: PK strategy and SQL schema draft approved by platform engineer
- M3: Unit + integration test shells added and passing locally against mocks/SQLite
- M4: Spec and plan merged; implementation ticket created and scheduled

## Risks & mitigations
- Risk: PK entries are inaccurate or inconsistent. Mitigation: audit task + small migration plan.
- Risk: Analyzer output shape mismatches expectations. Mitigation: add adapter/flattening tests and a contract test for SiteInventoryHealthAnalyzer.analyze.

## Exit criteria for plan phase
- PK strategy finalized and documented
- Test skeletons and SQL verification scripts exist in repo
- Stakeholder sign-off on spec directory


