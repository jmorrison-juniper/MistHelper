## analysis.md

### Analysis method

This is a manual, source-grounded pre-implementation consistency review of the issue artifacts. It follows the categories in `.github/agents/speckit.analyze.agent.md`: duplication, ambiguity, underspecification, constitution alignment, coverage gaps, and inconsistency.

Native slash commands were not executed against files. Their configured git hooks would mutate the shared checkout. The next implementer must repeat native analysis after materializing the artifacts in its own worktree.

### Findings and dispositions

| ID | Severity | Finding | Disposition |
| --- | --- | --- | --- |
| A01 | High | Generated endpoint specs derive nonexistent SDK submodules from URL suffixes. | Every packet gives the real SDK source module. Packet tasks correct the original spec. |
| A02 | High | A direct-call-only audit misses callable tables and dynamic endpoint resolution. | The selection checked source references, callable values, and remote dynamic uses. Organization duplicates and #1316 were removed. |
| A03 | High | Existing get_all does not validate later-page HTTP status. | C03 requires checked SDK continuation and no output before completion. |
| A04 | High | Existing Arango key construction ignores later composite fields and does not scope inherited entities by site. | C07 adds an explicit opt-in key contract. Existing unselected endpoints remain unchanged. |
| A05 | High | Existing export paths can mirror original raw records after flattening. | C05 requires the same redacted copy in both paths and tests credential sentinels. |
| A06 | High | A bool returned by the canonical writer proves only the primary output. | C06 defines saved narrowly and preserves mirror warnings. |
| A07 | Medium | Derived schema examples can omit id. | C04 rejects missing identity. A real endpoint with no usable identity requires a reviewed amendment, not a guessed key. |
| A08 | Medium | The old endpoint specs request twenty menu entries. | The shared family decision supersedes that UX detail under #1807. One menu test proves the count. |
| A09 | Medium | The local checkout and remote menu tail differed. | The manifest pins remote main. The menu number is allocated from current main, never copied blindly. |
| A10 | Medium | The existing virtual environment has a broken simplejson import. | Full imports and tests require a new worktree environment. Source probes passed but are not represented as full import tests. |
| A11 | Medium | Old constitution deployment instructions conflict with supplied issue-first PR rules. | The supplied authoritative git-flow instructions govern. Record the conflict. Do not push to main or deploy during planning. |
| A12 | Medium | The PR template has narrower or stale gate examples. | The quickstart uses current ci.yml scopes, including Black and all MYPY_PATHS. |
| A13 | Medium | tests/conftest.py changes directory after collection-time bootstrap. | Tests require a secret-free worktree and fake network collaborators. The temporary-directory fixture alone is not proof of isolation. |

### Requirement-to-task coverage

| Requirement | Tasks or complete packet task range | Verification |
| --- | --- | --- |
| FR-001 | T005-T007, T031-T150, T151-T152 | Exactly twenty catalog entries and one menu. |
| FR-002 | T005, T008-T009, T016-T017 | Cancellation and valid context tests. |
| FR-003 | T002, T005-T007, T012-T013, T028, packet catalog tasks | Real SDK signature and fake GET binding. |
| FR-004 | T010-T011, packet fetch tasks, T156 | Two pages, failed later page, and continuation bounds. |
| FR-005 | T012-T013 | Pacer count, same session, and no second retry loop. |
| FR-006 | T008-T011, T026-T027, packet failure tasks | Cancelled, empty, saved, and error outcomes. |
| FR-007 | T014, T016-T017, packet fixture tasks | Input immutability and noncredential field preservation. |
| FR-008 | T014-T017, T026-T027, packet storage tasks, T156 | Secret sentinels absent from both payload paths and logs. |
| FR-009 | T024-T025, packet storage tasks | Canonical writer arguments and safe raw_data. |
| FR-010 | T016-T017, packet storage tasks | UUID-based basename and data-directory containment. |
| FR-011 | T016-T024, packet key and storage tasks, T156 | Native keys, repeated writes, and site separation. |
| FR-012 | T018-T023, packet strategy tasks | Opt-in encoder and unchanged legacy keys. |
| FR-013 | T024-T027, packet writer-result tasks | False writer outcome and preserved mirror warnings. |
| FR-014 | T006, T028-T029, T152, T158 | Import, structure, comments, logging, and diagnostics. |
| FR-015 | T004-T030, packet test tasks, T155-T159 | Focused coverage, full gates, and recorded evidence. |
| FR-016 | T003, packet spec tasks, T151-T160 | Correct specs, menu references, PR, and issue closure. |

All sixteen functional requirements have assigned implementation tasks. The seven success criteria have explicit test outcomes in the specification and quickstart. Every task maps to a requirement or delivery obligation. This is 100 percent planning coverage, not 100 percent runtime coverage.

### Dependency review

The foundation precedes endpoint rows. All endpoint rows precede menu integration. Storage opt-in follows encoder tests. Secret redaction precedes raw_data handoff. Full checks and final analysis precede a PR. Shared files have one owner and no parallel task marker.

### Remaining implementation preconditions

1. The selected issues remain open and unclaimed when implementation starts.
2. A fresh worktree can import the SDK and test dependencies.
3. Existing endpoint collections are empty, or a separate migration receives review.
4. Current API responses supply the required identity fields. Missing fields cause safe failure, not invented identity.
5. Materialized native analysis reports no unresolved critical conflict.

No precondition permits silent scope expansion. Stop and report the missing fact if one fails.

### Final planning boundary

The planning deliverable is complete when GitHub contains the manifest, seven shared artifacts, and twenty endpoint packets, and read-back verifies their contents. Source implementation remains untouched. No task from T001 through T160 is represented as executed.

## 2026-09-16 verification update

Issue #2339 was rechecked against `mistapi` 0.64.0 and OpenAPI 2607.1.1. All twenty SDK functions exist. All planned parameter names still match. All OpenAPI paths still match. All twenty endpoint plans name a primary-key strategy and scoped storage fields. No live Mist request occurred. Keep implementation stopped until the user assigns it. See `verification.md` for the table.
