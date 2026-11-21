# Tasks: Upgrade Spec Kit scaffolding to 1.4.3 and keep the routed layout

**Input**: Design documents in this directory (`spec.md`, `plan.md`)

## Phase 1: Record

- [ ] T001 Commit this spec record on branch `chore/4869-speckit-1-4-3`.

## Phase 2: Upgrade the managed files

- [ ] T002 Set the version markers in `.specify/init-options.json` and `.specify/integration.json` to 1.4.3.
- [ ] T003 Copy the 1.4.3 manifests into `.specify/integrations/`.
- [ ] T004 Add `ConvertTo-AsciiJson` to `.specify/scripts/powershell/common.ps1` and keep the rest of the file.
- [ ] T005 Merge the four setup scripts and keep their local guards.
- [ ] T006 Merge the three skills that have local edits and copy the six unedited skills.
- [ ] T007 Copy `markdown_sections.py` and the constitution template.

## Phase 3: Verify

- [ ] T008 Parse each changed PowerShell file with zero errors.
- [ ] T009 Parse each changed JSON file.
- [ ] T010 Run the four setup scripts. Each script exits 0 and returns JSON.
- [ ] T011 Run `create-new-feature.ps1 -DryRun`. The printed path is under `specs/numbered/`.
- [ ] T012 Run the guardrail tests and record the examined counts.
- [ ] T013 Run `ste-linter` on the new spec files when the tool is available.

## Phase 4: Deliver

- [ ] T014 Add the release note fragment `changelog.d/issue-4869-speckit-1-4-3.md`.
- [ ] T015 Open the pull request with the list of kept files.
- [ ] T016 File the follow-up issue for the routed port and the git extension.
