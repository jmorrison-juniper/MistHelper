# Implementation Plan: Capture seed lifecycle fidelity

**Branch**: `jmorrison-juniper-capture-seed-lifecycle-fidelity` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/3375-capture-seed-lifecycle/spec.md`.

## Summary

Change the test harness, not the product.
Give native seeds and actual runner documents separate lifecycle and content fields.
Use the shipped client-name builder.
Compare the actual stand-in predicate with the actual shipped reader through a controlled query boundary.
Prove partial adoption with a private browser scenario and real rendered pages.

## Technical Context

**Language/Version**: Python 3.13.13 in this worktree's ignored `.venv`.

**Primary Dependencies**: Existing pytest, Flask, mistapi, Playwright, Chromium, Ruff, Black, mypy, and Bandit.

**Storage**: Fresh process-owned `PortalRecordStore` values and controlled in-memory query records only.

**Testing**: Native fixture observations, direct guards, unit tests, contract tests, and Chromium.

**Target Platform**: Local macOS. Native Windows execution remains unperformed.

**Project Type**: Test-harness repair.

**Performance Goals**: Bound each browser server and stop every owned helper after its test.

**Constraints**: No product changes, external SDK transport, production store writes, actual firmware callback, or publication.

**Scale/Scope**: Five existing seeds, nine counts, three device rows, matched and unmatched clients, and private partial adoption.

## Constitution Check

- Keep existing source boundaries and complete the actual field migration.
- Use classes for new support behavior. Add no wrapper, alias, facade, or compatibility fallback.
- Give every new method at most five parameters, five logical blocks, and 25 lines.
- Preserve natural capture identifiers and the existing record serialization.
- Keep logs ASCII and keep credentials outside logs.
- Preserve the production lifecycle/content distinction and the actual reader rules.
- Use exact path reservations before executable edits.
- Keep the publication and deployment stages blocked until the parent's separate authorization.

The repository has existing oversized fixture and test hierarchies.
`stand_in_capture` and `stand_in_tier3_capture` already exceed the function-length limit.
Their narrow field repairs must not trigger an unrelated fixture refactor.
Record the necessary line change and preserve every unaffected statement with an AST comparison.
A separate future issue can divide the global fixture into typed seed modules.

## Project Structure

### Documentation (this feature)

```text
specs/3375-capture-seed-lifecycle/
  spec.md
  plan.md
  tasks.md
changelog.d/issue-3375-capture-seed-lifecycle.md
```

### Source Code (repository root)

```text
tests/e2e/upgrade_portal/
  conftest.py
  test_capture_lifecycle_fidelity.py
tests/support/upgrade_portal_e2e/
  capture_fidelity.py
  records/portal.py
tests/unit/upgrade_portal/
  test_e2e_capture_lifecycle.py
  test_e2e_capture_statistics.py
  test_e2e_standin_precheck_adopter.py
tests/contract/upgrade_portal/
  test_e2e_capture_lifecycle_contract.py
```

**Structure Decision**: Keep the two authorized harness boundaries.
Use one issue-owned support module only after parent release.
Migrate the two directly coupled old unit modules only after parent release.
Do not change an old browser journey without its exact path release.

## Evidence Procedure

1. Read every live claim and paginated open pull request before the issue claim.
2. Preserve the immutable baseline separately from the app starting commit.
3. Use the native pytest fixture identity for every observation.
4. Prove seed lifecycle/content and parent-name defects before the repair.
5. Compare partial adoption against the shipped query and reject content-only eligibility.
6. Repair the native seed builder, Tier 3 content status, and stand-in predicate.
7. Use a private site for partial adoption without shared capture deletion or fixture-lifetime changes.
8. Check real rendered counts, device cells, parent cells, history content, and the pre-check card.
9. Run focused acceptance, the complete portal unit scope, and complete current E2E collection.
10. Run configured quality gates, strict owned typing, unchanged test-quality inputs, and changed-statement coverage.
11. Commit only necessary reserved files and repeat the clean committed-scope check.
12. Report the full local SHA, exact evidence, limitations, clean state, and cleanup to the parent.

The default browser artifact settings remain off.
No wildcard Python route handler or tracing-dependent decision is permitted.
The browser must read the current Flask routes, JavaScript, CSS, and stable selectors.

## Tool Capability Limits

The documented bootstrap failed in `ensurepip` with `SIGABRT`.
The complete trace remains in this session's artifacts.
Recovery changed only the ignored owned environment through UV seed, copy linking, and system certificates.
Bootstrap source remains unchanged.

The actual PowerShell probe returned `pwsh: command not found`.
The automatic SpecKit branch hook conflicts with the app-managed branch and the local-only publication boundary.
Use the current templates directly for this feature's three files.
Do not run a raw branch hook or change `.specify/feature.json`.
Do not commit a shared SpecKit context.

## Complexity Tracking

| Existing debt | Narrow change | Separate remediation |
| - | - | - |
| Oversized native capture builder | Add lifecycle/content fields and native parent names only. | Divide native seeds into typed modules in a separate issue. |
| Oversized Tier 3 builder | Resolve content status after the existing partial reasons. | Move Tier 3 records into a separately owned seed class. |
| Existing wide test directories | Keep new test behavior in bounded classes. | Restructure the test hierarchy separately without changing this concern. |

## Local Evidence

The exact immutable RED reference produces four expected failures and one passing control.
The control already proves 45 count fields and 30 Version/Status fields.
The repair retains those fields and changes only the required content, lifecycle, and parent names.

The focused final run passes 176 cases with no skips.
It includes 35 new unit cases, ten new contract cases, seven new browser cases, and the 124 accepted regression cases.
The complete portal unit scope passes 4,529 cases.
One existing case skips because it needs a native Windows import.

The complete current E2E scope collects 607 cases.
An exact starting-main export collects 600 cases under the same environment.
After removal of the seven new identifiers from the comparison, every existing identifier and its order match.
No optional journey receives a success claim from historical evidence.

Every edited existing runtime statement location executes: 21 of 21.
The four new files execute 627 of 640 statement locations and 47 of 54 branch arcs.
These measurements do not claim complete coverage of the oversized global fixture.
The separate coverage configuration stays in session artifacts.
It enables thread and greenlet measurement without changing the repository coverage exclusions.
Playwright tracing, screenshots, and video remain off.

The preservation proof checks 6,789 unaffected tracked blobs.
It handles 18 declared CRLF checkouts through their exact Git attributes.
It also compares 223 unaffected fixture constructs and 27 unaffected store constructs.
The five actual seed documents retain every other field.
The permitted differences are four content values, four added lifecycle fields, and 16 parent names.

The full test-quality gate checks 1,013 files and 725 findings with zero new findings.
The exact immutable baseline checks 1,008 files and the same 725 findings.
Each input preflight reads six required inputs and checks three active guides.
No baseline, exclusion, rule, product file, or old browser journey changes.

The normal dependency audit fails at the same `ensurepip` boundary as bootstrap.
The strict substitute resolves and hashes the complete applicable runtime chain with UV.
It audits 105 packages with no known vulnerabilities and no ignored vulnerability.
Native Windows dependencies and Git-only development tooling remain outside that macOS runtime audit.

The STE result is `partial` with `dictionary_unavailable`.
Heuristic scores do not constitute a licensed dictionary pass.
No other session's dictionary is read.
VS Code Browser Agent tools, live menu execution, deployment, native Windows execution, and remote CI remain unperformed.
No publication authority exists.
