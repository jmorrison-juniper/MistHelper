# Implementation Plan: Versioned Proposal Review and Safe Export

**Branch**: `feat/4641-proposal-review-export` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric record at `specs/numbered/0/0/1/2/2/0/3/1/4641-proposal-review-export/`. Decimal 4641 equals `122031` in base 5. Padded to eight levels, the route is `0/0/1/2/2/0/3/1`.

## Summary

Add a version 2 contract beside the unchanged version 1 DNS flow. Version 2 returns a structured proposal. The proposal holds the scope, object changes, omissions, unresolved mappings, and verification state. Review and export bind to the exact proposal digest in the browser session. The change stays offline. It writes no file and makes no Mist call.

## Technical Context

**Language/Version**: Python 3.15 or newer. The constitution requires it (`.specify/memory/constitution.md` line 278). The browser script is plain JavaScript in the existing presentation folder.

**Primary Dependencies**: Flask, Flask-WTF CSRF protection, and the existing portal shell. The change adds no dependency, so `requirements.txt` stays unchanged.

**Storage**: None. Review state is a digest in the signed browser session. Issue #4636 defines the later private store.

**Testing**: pytest unit and integration tests in `tests/integration/web_portal/cisco_config_converter/proposals/`. One Playwright browser test in `tests/e2e/web_portal/test_portal_smoke.py` runs in the isolated converter host.

**Target Platform**: Windows 11, macOS, Linux, and the Podman container. The code uses no platform-specific path.

**Project Type**: Feature package inside the existing web portal interface package at `src/interfaces/portals/cisco_config_converter/`.

**Performance Goals**: No latency target. The existing request bound applies. The route rule limits the converter path to 16 MiB plus 16 KiB (rows 6 and 76).

**Constraints**: Offline only. No Mist call. No file write. No shared portal file change. No new direct child of the converter root.

**Scale/Scope**: Three routes, one TypedDict, one assembler class, one route class, one script, one HTML section, one browser test method, and 21 test functions.

## Constitution Check

*GATE: Must pass before implementation. Each row names a rule, a result, and a reason. Row numbers refer to `design/research.md` section R4.*

| Rule | Result | Reason |
| - | - | - |
| I. Five-item rule, levels | Pass | The converter root keeps five children. The presentation folder grows to three. The integration test folder grows to four after issue #4636 (rows 2, 3, and 23). |
| I. Five-item rule, module names | Pass | `state/proposal.py` holds five names after the change. `conversion.py` and `routes.py` each hold at most four classes (rows 10 and 17). |
| I. Five-item rule, functions | Pass by plan | Each new method holds five parameters or fewer and 25 lines or fewer. The complexity gate checks each block. |
| I. Five-item rule, class members | Fail, justified | `StructuredProposal` declares ten keys. Complexity Tracking records the exception and the rejected alternative. |
| II. Class-based architecture | Pass | `ProposalAssembler` and `ProposalRoutes` carry the new behavior. No standalone wrapper function is added. |
| III. Safety-first input | Pass | `SourceConfiguration` validation stays in place. The version 2 body check validates the version and the keys first. |
| III. Destructive operations | Pass | No destructive operation exists. Cloud writes stay blocked. |
| III. Secrets in logs | Pass | Unsupported items keep a line number and a category only (rows 74 and 75). Test 17 proves that a synthetic secret is absent. |
| IV. Deployment pipeline | Pass by plan | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run in order. |
| V. ASCII logs | Pass | New log messages use ASCII text only. |
| V. Structured logs | Fail, inherited | The converter uses standard `logging`, as version 1 does. The owner decision on equivalence stays open in issue #4636, item U-2. |
| VI. Inline comments | Fail now, pass after T006 and T007 | Version 1 converter files hold no inline comment (row 12). Each touched or new line gets a comment. |
| VII. Action logging | Pass by plan | Version 2 actions log before and after each action (FR-018, test 18). |
| Technology: mistapi | Pass | The change makes no Mist call and imports no mistapi module (row 11). |
| Technology: UV and requirements | Pass | No dependency changes. |
| Technology: Podman | Pass | No container change. |
| Technology: test containers | Pass | No test container starts. |
| Technology: file paths | Pass | The suffix comes from a base name that `SourceConfiguration` already validated. |
| Technology: operational store | Pass | No declared store is used. The session holds digests only. |
| Technology: export boundary | Pass | The version 2 export does not call `DataExporter` (FR-015). The constitution scopes that exporter to API data (row 39). |
| Technology: database keys | Pass | No database row is written. |
| Technology: data directory | Pass | No file is written under `data/`. |
| Technology: container security | Pass | No file ownership changes. |
| Technology: Zscaler | Pass | No container build or push occurs. |
| Development: menu operations | Pass | No menu operation changes. |
| Development: documentation | Pass | One changelog fragment is added (FR-022). README holds no converter coverage (row 32), so no README change is made (analysis finding A-7). |
| Development: audience standard | Pass | New user-facing text uses plain words (`design/contracts/ui-v2.md`). |
| Escalation | Pass | The change touches more than three files and two classes. This record exists. |
| Multi-agent git: issue first | Pass | Issue #4641 exists. The `in-progress` label is added at T-PR. |
| Multi-agent git: branch | Pass | The branch name follows `feat/<issue>-<slug>` and starts from `main`. |
| Multi-agent git: overlap | Pass | The open PR scan found PR #4208 on `web_portal/app.py` and `web_portal/templates/base.html`. It found PR #4813 on another changelog fragment. This plan edits neither shared file, and its fragment name is unique. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/0/3/1/4641-proposal-review-export/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      proposal-v2.md
      routes-v2.md
      ui-v2.md
    checklists/
      requirements.md
      security.md
```

### Source Code (repository root)

```text
src/interfaces/portals/cisco_config_converter/
  __init__.py                    unchanged
  conversion.py                  adds ProposalAssembler
  routes.py                      adds ProposalRoutes and version 2 rules
  state/                         from issue #4636
    proposal.py                  adds StructuredProposal
  presentation/
    converter.html               adds the structured review section
    converter.js                 unchanged
    proposal_review.js           new script

tests/integration/web_portal/cisco_config_converter/
  __init__.py                    unchanged
  test_routes.py                 unchanged
  state/                         from issue #4636
  proposals/
    __init__.py                  new
    test_proposal_assembly.py    new, tests 1 to 7
    test_proposal_routes.py      new, tests 8 to 20

tests/e2e/web_portal/
  test_portal_smoke.py           adds test 21 to TestCiscoOfflinePreview

changelog.d/
  issue-4641-proposal-review-export.md   new, renamed at PR time
```

**Structure Decision**: Keep every new behavior in the existing converter modules. Add one class for each module, and add no direct child to the converter root. Put the version 2 tests in a nested `proposals/` package. Put the browser test in the existing converter class, because the Playwright job runs only `tests/e2e/`.

## Architecture

The flow runs in this order. Each step uses the output of the step before it.

1. The browser posts one multipart request to `/cisco-config-converter/v2/preview`.
2. `ConverterInput.source()` validates the source in memory. It reads no more than one byte beyond the limit.
3. `IOSDnsConverter.convert` builds the version 1 proposal. This code does not change.
4. `ProposalAssembler.assemble` adds the scope, object changes, omissions, unresolved mappings, and verification state.
5. `ReviewState.publish` stores the proposal digest in the browser session and clears any earlier review. `ProposalRoutes` then records the UTC time of the preview.
6. The browser posts the proposal to `/cisco-config-converter/v2/review`. The server refuses a preview recorded 15 minutes or more earlier, recomputes the digest, and records the review and its UTC time.
7. The browser posts the same proposal to `/cisco-config-converter/v2/export`. The server refuses a review recorded 15 minutes or more earlier, checks the reviewed digest, and returns the JSON attachment.

## File-by-File Change Map

| Path | Action | Content |
| - | - | - |
| `src/interfaces/portals/cisco_config_converter/state/proposal.py` | Modify, after issue #4636 | Add `StructuredProposal`. The module then holds five names. |
| `src/interfaces/portals/cisco_config_converter/conversion.py` | Modify | Add `ProposalAssembler` with methods `assemble`, `_scope`, `_object_changes`, and `_omissions`. Keep `IOSDnsConverter` unchanged. |
| `src/interfaces/portals/cisco_config_converter/routes.py` | Modify | Add `ProposalRoutes` with `preview`, `review`, `export`, and two helpers for the 15-minute lifetime. Import `REVIEW_LIFETIME` from `state/intake.py`. Register three rules in `ConverterRoutes.blueprint`. Add a `version` keyword with default 1 to `ConverterInput.action`. |
| `src/interfaces/portals/cisco_config_converter/presentation/converter.html` | Modify | Add the structured review section and its test IDs. Load `proposal_review.js` after `converter.js`. |
| `src/interfaces/portals/cisco_config_converter/presentation/proposal_review.js` | Add | Add `CiscoStructuredReview`. It renders the sections and calls the version 2 routes. |
| `tests/integration/web_portal/cisco_config_converter/proposals/__init__.py` | Add | Package marker. |
| `tests/integration/web_portal/cisco_config_converter/proposals/test_proposal_assembly.py` | Add | Tests 1 to 7. |
| `tests/integration/web_portal/cisco_config_converter/proposals/test_proposal_routes.py` | Add | Tests 8 to 20. |
| `tests/e2e/web_portal/test_portal_smoke.py` | Modify | Add test 21 to `TestCiscoOfflinePreview`. |
| `changelog.d/issue-4641-proposal-review-export.md` | Add | One release note. Rename it to `pr-<number>.md` after the pull request opens. |

Unchanged paths: `state/intake.py`, which supplies the `ReviewState.digest` function. `presentation/converter.js`. `tests/integration/web_portal/cisco_config_converter/test_routes.py`. `web_portal/app.py`. `web_portal/templates/base.html`. `web_portal/services/config.py`. `compose.yml`. `requirements.txt`. `documentation/`.

## Dependencies

- **Issue #4636**: Its package move must land first (decision D-14). `models.py` holds five top-level classes at lines 13, 21, 29, 38, and 84 (row 13). A new name in that module breaks the five-name limit.
- **Issues #4637 to #4640**: They produce fields that the proposal consumes. Each new field needs a contract revision (assumption A-1).
- **Issue #4648**: Its route allowlist must include the three version 2 routes (assumption A-2).
- **PR #4208**: It owns the shared portal files. This change does not overlap with it.
- **Packages**: No package is added.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| - | - | - |
| The browser session loses the secret after a restart. | Review and export return HTTP 409. | The operator reviews again. Decision D-15 keeps the owner decision in issue #4636. |
| Two worker processes use different secrets. | Review fails closed across processes. | The tests use one fixed key. Deployment must run one worker (analysis item U-7). |
| Issues #4637 to #4640 change the proposal fields. | The contract breaks. | Test 1 pins the key set. FR-012 rejects any unexpected key. |
| Issue #4648 rejects new routes in its allowlist. | Its route test fails. | Assumption A-2 requires the coordinator approval before that issue merges. |
| The integration test folder grows past five children. | The nested package guard fails. | The version 2 tests use a nested package (decision D-12). Analysis item A-1 asks issue #4648 to nest its files. |
| The browser test skips in the Playwright job. | A false pass. | T-LOCAL-GATES runs the file with `UPGRADE_PORTAL_E2E_STRICT` set to 1. |
| Source text reaches the page as markup. | Cross-site scripting. | The script uses `textContent` only (`design/contracts/ui-v2.md`). |
| Operators preview again more often. | Friction after 15 minutes. | The response names the next step. Decision D-20 records the lifetime and its owner. |
| Client JSON formatting changes the digest. | A valid review fails. | The digest uses sorted keys, compact separators, and `allow_nan` set to false (row 15). Test 10 proves the round trip. |
| `StructuredProposal` breaks the class-member guidance. | A review finding. | Complexity Tracking records the justification. |

## Rollback Steps

1. Revert the squash commit on `main` through a pull request.
2. Confirm that the three version 2 routes return HTTP 404.
3. Confirm that the version 1 route tests pass.
4. Remove no data. This change writes no file, so no cleanup is needed.

## Complexity Tracking

| Item | Type | Reason | Action |
| - | - | - | - |
| `StructuredProposal` declares ten keys. | New, justified | The response contract names ten keys. Nested TypedDict types would add names to `state/proposal.py`, which the five-name limit blocks. | The owner reviews the exception in the pull request. |
| Version 1 converter files hold no inline comment. | Grandfathered | The debt predates this change. | Analysis remediation R-1. Each block touched by T006 and T007 gets comments. |
| The converter uses standard `logging`. | Grandfathered | The debt predates this change. | The owner decision stays in issue #4636, item U-2. |
| `tests/e2e/web_portal/` holds 32 direct children. | Grandfathered, not touched | The debt predates this change (row 25). | Analysis remediation R-2. This change adds no child. |
