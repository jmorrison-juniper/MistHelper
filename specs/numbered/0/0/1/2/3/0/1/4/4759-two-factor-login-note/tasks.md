# Tasks: Correct interactive two-factor login notes

**Input**: `plan.md` and `spec.md` in the record folder `specs\numbered\0\0\1\2\3\0\1\4\4759-two-factor-login-note`.

**Format**: Each task lists requirement IDs, exact paths, an acceptance statement, one verification command, and a status. The status is one of open, verified-present, partial, or absent. `[P]` marks a task that can run in parallel with other `[P]` tasks.

## Phase 1: Verify existing work

### T001 [P] Verify the corrected two-factor note on main

- **Requirements**: FR-001, FR-002, FR-003, FR-004
- **Files**: `documentation/api/admins/POST_login_two_factor.md` (no change)
- **Acceptance**: Line 91 names the interactive login, the SDK call, and the page `/auth/twofactor`. It states that an API-token run never sends the code. It states that the operations portal has no code page. No line states that MistHelper lacks interactive two-factor support. Remote checks RC-01, RC-02, RC-06 to RC-17, and RC-54 support this task.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 documentation/api/admins/POST_login_two_factor.md`
- **Status**: verified-present

### T002 [P] Verify the POST_login note on main

- **Requirements**: FR-007
- **Files**: `documentation/api/admins/POST_login.md` (no change)
- **Acceptance**: Line 122 names the two SDK places, the `--login` and menu 143 path, the browser login on port 8056, and the start options for port 8055. Remote checks RC-13, RC-14, RC-15, RC-23, RC-24, and RC-34 support this task. The owner review stays open (D-2).
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 documentation/api/admins/POST_login.md`
- **Status**: verified-present

## Phase 2: Add the release-note fragment

### T003 [P] Add the release-note fragment

- **Requirements**: FR-005
- **Files**: `changelog.d/issue-4759-two-factor-login-note.md` (add)
- **Acceptance**: The file name is `issue-4759-two-factor-login-note.md`. The file holds one `###` heading and one `Fixed` bullet that names issue #4759. The file holds no version stamp. The changelog guard passes (RC-35 to RC-40).
- **Content**:

```markdown
### Correct the two-factor login note

- **Fixed**: The API pages for `POST /api/v1/login` and `POST /api/v1/login/two_factor` state how the interactive login uses the two-factor code. Issue #4759.
```

- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`
- **Status**: absent

### T004 Keep README and CHANGELOG unchanged

- **Requirements**: FR-006
- **Files**: `README.md` and `CHANGELOG.md` (no change)
- **Acceptance**: The branch diff holds no change to either file. The changelog guard covers `CHANGELOG.md`. Quickstart step 9 covers the complete file list, which includes `README.md`.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`
- **Status**: open

## Phase 3: Gates and publication

### T-LOCAL-GATES

- **Depends on**: T001, T002, T003, T004
- **Requirements**: FR-001 to FR-007, SC-002, SC-003
- **Files**: each changed file in the change manifest
- **Acceptance**: Run the STE gate on each changed Markdown file. Run the changelog guard. Record each result and its count. Record each gate that does not apply, with its reason from `plan.md`. Stop at the first failure.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 documentation/api/admins/POST_login_two_factor.md documentation/api/admins/POST_login.md changelog.d/issue-4759-two-factor-login-note.md` and `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`
- **Status**: open

### T-PR

- **Depends on**: T-LOCAL-GATES, and a new owner instruction (D-7)
- **Requirements**: FR-005, FR-006, SC-004
- **Files**: `changelog.d/issue-4759-two-factor-login-note.md` and the record folder
- **Acceptance**: Gate: the owner instruction supersedes the hold in RC-56. Clear `GH_TOKEN` and `GITHUB_TOKEN`, then run `gh auth switch --user jmorrison-juniper` (RC-67). Commit with the subject `docs(api): correct two-factor login note` and the body `Closes #4759`. The subject meets the title rule (RC-62). Rebase onto `main`. Push `docs/4759-two-factor-login-note`. Open the pull request. Its body holds `Closes #4759`, a files changed summary, each local gate result, the deployment and rollback notes, and a link to pull request #4924 (RC-65). Its file list matches the manifest.
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`
- **Status**: open

### T-REMOTE-CI

- **Depends on**: T-PR
- **Requirements**: SC-004
- **Files**: none changed
- **Acceptance**: Run `gh pr checks --watch` on the branch. Each required check reports success. Record the result in the pull request. CI runs the changelog guard (RC-41). The STE workflow checks only the instruction files and the README (RC-61), so the local STE gate in T-LOCAL-GATES covers the changed documentation.
- **Verification**: `ste-linter --config .ste-linter.toml --min-score 80 changelog.d/issue-4759-two-factor-login-note.md`
- **Status**: open

### T-MERGE

- **Depends on**: T-REMOTE-CI, and owner authorization (D-7)
- **Requirements**: SC-004
- **Files**: none changed
- **Acceptance**: Gate: the owner authorizes the merge. Use one serial merge slot (RC-63). Warning: a squash merge to `main` cannot be undone without a new pull request. Add the `auto-merge` label only after each check shows green. Squash merge and delete the branch. Wait for `.github/workflows/container-build.yml` on the merged revision. Verify that the image revision label equals the merged commit SHA. Deploy and check health (constitution Principle IV, steps 9 to 12).
- **Verification**: `python -m pytest tests/guardrails/test_changelog_fragment_policy.py -q`
- **Status**: open

## Dependencies

- T001, T002, and T003 have no prerequisite. Each can run in parallel.
- T004 follows T003, because the file list check needs the new fragment.
- T-LOCAL-GATES follows T001, T002, T003, and T004.
- T-PR follows T-LOCAL-GATES and the owner instruction.
- T-REMOTE-CI follows T-PR.
- T-MERGE follows T-REMOTE-CI and the owner authorization.

## Requirement Coverage

| Requirement | Tasks |
| - | - |
| FR-001 | T001, T-LOCAL-GATES |
| FR-002 | T001, T-LOCAL-GATES |
| FR-003 | T001, T-LOCAL-GATES |
| FR-004 | T001, T-LOCAL-GATES |
| FR-005 | T003, T-PR |
| FR-006 | T004, T-PR |
| FR-007 | T002, T-LOCAL-GATES |
