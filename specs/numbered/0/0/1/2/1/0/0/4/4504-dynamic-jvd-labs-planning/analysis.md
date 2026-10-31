# Cross-Artifact Analysis: Dynamic JVD Labs Planning

**Date**: 2026-10-30. **Inputs**: `spec.md`, `plan.md`, `tasks.md`, `design/`.

## Consistency Result

| Check | Result |
| - | - |
| Each FR-001 to FR-022 maps to a task and a verifying task | Pass. See the traceability table in `tasks.md`. |
| Each user story has tasks and tests | Pass. US1 to US6 map to Phases 3 to 8. |
| Each task path matches the plan structure | Pass. |
| Implementation and live tasks stay unchecked | Pass. The guard `test_labs_planning_record.py` enforces this. |
| Scope excludes legacy parity, React frontends, licensing, and visibility | Pass. |
| Contradictions between artifacts | None found. |

## Unresolved Implementation Decisions

| ID | Decision | Owner | Blocks |
| - | - | - | - |
| D-01 | Submodule path and pinned commit | Maintainer | T032 |
| D-02 | Exact `mistapi` methods for each Mist call | Implementer, with maintainer review | T030 |
| D-03 | POSIX-only live execution or a cross-platform lock | Maintainer | T021, T070 |
| D-04 | Numeric limits for import, pagination, polling, concurrency, duration, retention | Maintainer | T052, T072 |
| D-05 | Approval words and lease bounds | Maintainer | T022 |
| D-06 | First release scope of the five increments | Maintainer | T106 |
| D-07 | Reusable image workflow update or host-local build | Maintainer | T033 |
| D-08 | Engine build-block list and role-pairing rules | Engine owner | T050 |
| D-09 | Whether a stable `PORTAL_SECRET_KEY` becomes mandatory for Labs actions | Maintainer | T022 |

## Risks

- The engine compiler supports only fixed dual-hub roles. Dynamic composition is new engine work (T050).
- Framework dev extra pins pytest below 9, and the host needs pytest 9. Separate environments are required.
- Preview and framework installation do not prove full lab capability. Each capability reports its own state.
- Direct-link throughput does not prove a path or SLA. The portal must not claim it.

## Findings Fixed During Analysis

- The spec referenced task T030 for the `mistapi` mapping. `tasks.md` now defines T030 for that purpose.
- The plan lists the guard test that examines this record. The guard exists in `tests/guardrails/`.
