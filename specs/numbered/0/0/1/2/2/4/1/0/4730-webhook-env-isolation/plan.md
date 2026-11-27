# Implementation Plan: Webhook config test isolation

**Branch**: `fix/4730-webhook-env-isolation` (merged). Follow-up branch name: `chore/<NEW-ISSUE>-webhook-test-comments`.

**Date**: 2026-11-26 | **Spec**: `specs\numbered\0\0\1\2\2\4\1\0\4730-webhook-env-isolation\spec.md`

**Input**: Numeric specification from `/specs/numbered/0/0/1/2/2/4/1/0/4730-webhook-env-isolation/spec.md`. The route comes from `.specify/scripts/powershell/spec-route.ps1`, lines 4 to 52 (R-30).

Keep `spec.md`, `plan.md`, and `tasks.md` at the feature root. Place research, data model, quickstart, and checklists under `design/`. Keep five children or fewer at every new directory level. No contract folder is needed, so it is omitted (see Contracts below).

## Summary

The repair that issue #4730 requests is on `main`. PR #4843 merged it on 2026-11-19, and the main blob matches the repaired blob (R-01). This plan verifies the merged repair, closes the issue after verification, and adds the inline comments that Principle VI requires in the touched test function. No production file changes.

## Technical Context

**Language/Version**: Python 3.15 or newer (`.github/copilot-instructions.md` lines 18 to 24).

**Primary Dependencies**: pytest, the Flask test client, and the app factory in `web_portal/app.py`. The changed test imports no `mistapi` module (R-34).

**Storage**: Not applicable. The test uses no database and no file.

**Testing**: pytest. The file runs in the `root-units` shard (`.github/workflows/ci.yml` lines 262 to 265 and R-20).

**Target Platform**: Windows 11, macOS, and Linux (`.github/copilot-instructions.md` lines 8 to 16).

**Project Type**: Unit test of a Flask blueprint and an app factory.

**Performance Goals**: Not applicable. The change touches one test function.

**Constraints**: No production behavior change. ASCII-only output. Each code line of the touched function carries an inline comment. Maximum line length is 120 characters (`pyproject.toml` line 202 and R-31).

**Scale/Scope**: One test file and one test function.

## Constitution Check

The check uses `.specify/memory/constitution.md` version 1.9.0. Each rule has a result and a reason.

| Rule | Result | Reason |
| - | - | - |
| I. Five-Item Rule | PASS | The record adds one folder under the route leaf. The leaf holds one child. The parent `specs\numbered\0\0\1\2\2\4\1` holds two children after the addition (R-30 gives the route rule). The record folder holds five children at most. |
| II. Class-Based Architecture | PASS | The test stays in class `TestAppFactoryWebhookConfig` (line 217). The change adds no function and no wrapper. |
| III. Safety-First | PASS | The changed code has no `input()` call and no destructive operation. The test removes `WEBHOOK_SECRET` by name and never prints its value. |
| IV. Full Deployment Pipeline | FAIL | Steps 1 to 10 passed for PR #4843. Steps 11 and 12 (image revision check and deploy) are not run by this record. Complexity item CT-1 records the reason. |
| V. Observability and Logging | PASS | The changed lines add no log call. The production log calls stay unchanged. The output is ASCII. |
| VI. Inline Comments | FAIL until T010 | The touched function has no inline comments on `main` (R-04). Tasks T010 and T011 repair this. Complexity item CT-2 records the gap. |
| VII. Action Logging | PASS | The changed lines perform no external request, file write, database operation, data transform, or operator question. The action list appears in `AGENTS.md` under "Action logging" (line 104). |
| Technology constraints | PASS | Python 3.15 is the runtime. Not applicable: mistapi, UV, Podman, file paths, output backends, operational store, database keys, data directory, container security, and Zscaler. The change has no Mist call, package, container, or path operation. |
| Syntax validation before commit | PASS in plan | Task T-LOCAL-GATES runs `python -m py_compile MistHelper.py` (check TC-009). |
| Security findings | PASS | No security tool reports a finding for the file. The Bandit job passed on main (run 45774119357). |
| Documentation and release notes | PASS under the repository rule | `changelog.d/README.md` rule 4 exempts internal-only changes (R-28). The constitution wording differs (R-26). Analysis item A-5 and decision D-4 record the conflict. |
| Audience standard | PASS | The record uses plain words. The user-facing text of the test is not changed. |
| Complexity-driven escalation | PASS | The orchestrator requested a record. The repair alone would not need one. |
| Multi-agent git workflow | PASS | T008 files the follow-up issue before the branch (issue first). The branch name follows `chore/<issue>-<slug>`. Labels use type `chore` and scope `tests`. No open pull request changes a webhook path (R-37). T-PR rebases before push. T-MERGE uses a squash merge. |

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/2/2/4/1/0/4730-webhook-env-isolation/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    checklists/
      requirements.md
      verification.md
```

### Source Code (repository root)

```text
tests/unit/web_portal/test_webhook_signature.py   (modify: comments only, lines 229 to 240)
```

No other source file changes.

**Structure Decision**: The numeric route comes from `Get-SpecRadixSegments` and `Resolve-SpecFeaturePath` (R-30). The base is 5, and the width is 8. The number 4730 gives the digits 0, 0, 1, 2, 2, 4, 1, 0. The record folder is the direct child of the route leaf.

## File-by-File Change Map

| Path | Action | Requirements | Tasks |
| - | - | - | - |
| `tests/unit/web_portal/test_webhook_signature.py` | Modify. Add comments on lines 229, 230, 233, 234, 235, 237, 239, and 240. The merged repair already exists on lines 233 and 234. | FR-008, FR-009 | T010, T011 |
| `specs/numbered/0/0/1/2/2/4/1/0/4730-webhook-env-isolation/` | Add. The orchestrator places this record from the draft folder. | FR-010 | T-LOCAL-GATES step A |
| All other repository files | No change | FR-005 | T004, T006 |

No file is deleted.

## Dependencies

- No new package and no dependency change.
- Tools in `requirements-dev.txt` (R-22 names the gate row, and `.github/copilot-instructions.md` lines 39 to 44 name the devtools package): pytest, ruff, black, `symbol-diff`, and `test-quality-analyzer`.
- GitHub CLI (`gh`) for reads. The executor uses `gh` for the pull request and the issue writes.

## Architecture and Call Path

```text
test_the_factory_stores_an_empty_secret_when_the_variable_is_absent   (test line 229)
  -> monkeypatch.delenv("WEBHOOK_SECRET")                                 (line 233)
  -> monkeypatch.delenv("WEBHOOK_ENABLED")                                (line 234)
  -> WebPortalApp._load_webhook_config(app)                               (web_portal/app.py line 119)
  -> os.environ.get("WEBHOOK_ENABLED", "true")                            (web_portal/app.py line 129)
  -> assert app.config["WEBHOOK_ENABLED"] is True                         (test line 240)
```

The root cause is that the test read the caller's environment. The production default `true` applies only when the variable is absent. The test now sets its own precondition.

## Risks and Mitigations

| Risk | Effect | Mitigation |
| - | - | - |
| A future loader sets `WEBHOOK_ENABLED` again | The test fails again | Check TC-003 runs the whole file in each state. |
| A comment edit changes code | Behavior changes | Checks TC-005 and TC-006 review the diff and the symbols. |
| The issue closes before verification | The issue shows a false state | D-2 orders the closure after step A. |
| CI evidence is not local evidence | False confidence | T-LOCAL-GATES runs the file locally in two states. |
| A commit hook bypass hides a failure | An unverified commit reaches main | FR-012 and check TC-012 block the bypass. |
| The serial merge slot is busy | A second merge conflicts with the first | Wait for the slot (`.github/copilot-instructions.md` lines 483 to 498 and R-23). |

## Rollback

1. Follow-up: revert the follow-up commit on a new branch. The revert restores the test without comments. No product file changes.
2. Issue closure: the orchestrator reopens issue #4730 with the `gh` command in quickstart Q-6 if verification later fails.
3. Repair: reverting PR #4843 restores blob `372302985df902560df4c497d8b3dc1e07bc407e`. Warning: the restored test fails when the environment sets `WEBHOOK_ENABLED=false`. Use this rollback only with a replacement fix.

## Complexity Tracking

| ID | Violation | Why it exists | Simpler alternative rejected because |
| - | - | - | - |
| CT-1 | Principle IV steps 11 and 12 are not run by this record | The record adds no product code. The orchestrator decides whether a deploy runs. | Deploying a test-only change adds runtime risk and changes no product behavior. |
| CT-2 | Principle VI gap in the touched test function (lines 229 to 240, R-04) | PR #4843 changed a line in a function that has no comments. | Accepting the gap breaks a non-negotiable rule. The follow-up repairs it (T010). |
| CT-3 | Constitution wording on fragments differs from the changelog rule | Governance text conflicts with `changelog.d/README.md` rule 4 (R-26, R-28). | Adding a fragment to every change adds noise. The guard does not require one (R-29). |
| CT-4 | Grandfathered debt: other test functions in the same file lack inline comments | These functions predate the issue. | AGENTS.md limits the comment rule to touched blocks. This record does not change untouched functions. |

## Contracts

No interface contract applies. The webhook response codes (403, 503, and 200) and the `X-Mist-Signature` header contract are unchanged. The `contracts\` folder is omitted for this reason.

## Phase Outputs

- `design/research.md`: decisions, remote verification table, sources, and the unverified list.
- `design/data-model.md`: not applicable.
- `design/quickstart.md`: exact verification commands and expected results.
- `design/checklists/requirements.md` and `design/checklists/verification.md`: quality and verification checklists.
