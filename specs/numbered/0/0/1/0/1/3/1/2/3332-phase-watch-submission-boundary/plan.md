# Implementation Plan: Clarify the Phase-Watch Submission Boundary

**Branch**: `jmorrison-juniper-docs-3332-phase-watch-boundary`  
**Date**: 2026-10-06  
**Spec**: [spec.md](./spec.md)

## Summary

Issue #3332 Child 1 changes wording only. The change corrects the phase-watch
submission boundary without changing firmware behavior.

The driver, the organization watch, and the organization phase card will use
the same approved statements. The contract test will assert the exact rendered
operator text.

The implementation will not add a settle timeout, reachability gate, retry
rule, resume rule, firmware order, lock release rule, or durable state.

## Technical Context

**Language/Version**: Python 3.13 or newer, Jinja HTML, and Markdown.

**Primary Dependencies**: Existing Flask, Jinja, pytest, and Playwright
packages. No dependency changes.

**Storage**: N/A. The change adds no stored field and changes no record.

**Testing**: pytest contract tests, the complete upgrade portal end-to-end
suite, exact-string audits, and repository quality gates.

**Target Platform**: Windows 11, macOS, Linux, and the existing Podman
deployment.

**Project Type**: Existing Python web portal with Jinja templates.

**Performance Goals**: N/A. The change adds no runtime operation.

**Constraints**: Change wording only. Edit only the approved implementation
files and the issue-named changelog fragment.

**Scale/Scope**: Four approved wording locations, one release-note fragment,
and the Spec Kit planning records.

## Canonical Wording

Use these exact strings:

1. `The phase watch starts after the portal sends the upgrade requests.`
2. `It observes the submitted work and sends no firmware request.`
3. `It does not prove that the cloud accepted each request or that the portal sent device types in this order.`
4. `Warning: If a submission result is uncertain, do not start another upgrade. A second upgrade can target the same devices.`

The driver and organization watch use statements 1 through 3. The organization
phase card uses all four statements.

The contract test directly asserts all four exact strings in the rendered page
text. It does not infer the contract from a selector, a substring fragment, or
a helper result.

## Constitution Check

### Before Design

| Principle | Result |
| - | - |
| I. Five-Item Rule | Pass. The feature adds planning records under the managed numeric route. It adds no product hierarchy child. |
| II. Class-Based Architecture | Pass. The feature adds no function, class, wrapper, or behavior. |
| III. Safety-First | Pass. The wording removes a false safety promise and gives one direct warning. |
| IV. Full Deployment Pipeline | Pass. The implementation plan includes gates, rebase, one force-with-lease push, pull request checks, and review readiness. |
| V. Observability | Pass. The feature changes no log event or logging behavior. |
| VI. Inline Comments | Pass. The implementation changes comments, docstrings, template text, and contract assertions only. |
| VII. Action Logging | Pass. The feature changes no meaningful runtime action. |

The approved production paths are in a destructive portal flow. The feature
does not execute or change that flow.

The existing `specs/` folder debt remains grandfathered. Issue #3332 adds one
record under the required eight-level base-5 route. A separate repository
migration owns any unrelated folder remediation.

### After Design

The design adds no clarification, behavior, data field, interface endpoint, or
dependency. All constitution gates remain satisfied.

## Approved Implementation Manifest

The implementation phase can edit only these files:

```text
src/interfaces/portals/upgrade_portal/upgrade/driver.py
src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py
src/interfaces/portals/upgrade_portal/app/assets/templates/partials/org_phase_list.html
tests/contract/upgrade_portal/test_org_phase_watch_contract.py
tests/unit/upgrade_portal/test_org_phase_list_parity.py
changelog.d/issue-3332-phase-watch-wording.md
```

The release-note fragment will use this content:

```markdown
### Phase-watch submission boundary

- **Changed**: The upgrade portal now states that the phase watch observes
  submitted work but proves neither cloud acceptance nor request order. The
  portal warns the operator not to start a duplicate upgrade. Issue #3332.
```

No other production file, test file, documentation file, workflow file, or
dependency file is in the implementation scope.

## Project Structure

### Planning Records

```text
specs/numbered/0/0/1/0/1/3/1/2/3332-phase-watch-submission-boundary/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── phase-watch-wording.md
```

### Existing Implementation Locations

```text
src/interfaces/portals/upgrade_portal/
├── upgrade/
│   ├── driver.py
│   └── org_cascade/
│       └── walk.py
└── app/assets/templates/partials/
    └── org_phase_list.html

tests/contract/upgrade_portal/
└── test_org_phase_watch_contract.py

tests/unit/upgrade_portal/
└── test_org_phase_list_parity.py

changelog.d/
└── issue-3332-phase-watch-wording.md
```

**Structure Decision**: Make surgical wording edits in existing files. Add no
module, package, route, state, or helper.

## Implementation Sequence

1. Run the exact-string audit across all files under `tests/`.
2. Replace the false driver submission-order statement with statements 1
   through 3.
3. Keep the organization watch read-only wording and add its post-submit
   boundary with statements 1 through 3.
4. Add statements 1 through 4 to the organization phase card.
5. Add direct exact-string assertions to the approved contract test.
6. Add `changelog.d/issue-3332-phase-watch-wording.md`.
7. Review the diff for wording-only changes and excluded subjects.
8. Run the validation sequence in [quickstart.md](./quickstart.md).
9. Commit, fetch, and rebase onto `origin/main`.
10. Rerun affected gates after the rebase.
11. Push one time with `--force-with-lease`.
12. Verify that the pull request is ready for review.

## Excluded Subjects

Do not add or change:

- a settle timeout
- a reachability gate
- a retry rule
- a resume rule
- firmware submission ordering
- a firmware write
- lock renewal or lock release
- a durable state or record field

Any diff that changes executable control flow fails the plan.

## Complexity Tracking

No constitution violation requires an exception.
