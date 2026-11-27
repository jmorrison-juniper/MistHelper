# Research: Correct interactive two-factor login notes

## Scope and Method

This step reads and reasons only. It runs no test, linter, build, install, container, or repository script. It reads the local repository with read-only git commands (`log`, `grep`, `show`, and `hash-object` without a write flag). It reads GitHub data with `gh` reads only. It writes only to the draft and meta folders.

Each claim about `main` cites the remote blob SHA and the line number from a decoded copy. Local reads confirm the same commit. The local `HEAD` equals main commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`.

Basis of the current state:

- Owner comment IC_kwDOQltU8c8AAAABlGYtEA cites blob `f897a85e` for the note on `main`. That blob holds the old text (RC-01).
- Current `main` holds blob `98aeb3e8`. The note in that blob is corrected (RC-02).
- Commit `4e81b2a4` (pull request #4924) changed the note (RC-33).

## Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk. No decision needs a human decision under brief section 6.

### D-1 Keep the corrected two-factor note from commit 4e81b2a4

- **Alternatives**: (a) Revert the note to the text of blob `f897a85e`. (b) Rewrite the note with new wording.
- **Chosen**: Keep the note as it stands on `main`.
- **Reason**: Every sentence of the note maps to present rows (see Claim Map). Caution: reverting restores a false statement.
- **Risk**: Caution: pull request #4924 carried the note. That pull request does not name issue #4759. It merged after the owner hold comment of 2026-11-16. The owner must review it (A-2 in `analysis.md`).
- **Human decision required**: No.

### D-2 Keep the POST_login.md note from commit 4e81b2a4

- **Alternatives**: (a) Revert the note in a separate pull request. (b) Keep the note and link pull request #4924.
- **Chosen**: Keep the note. Link pull request #4924 in the T-PR body.
- **Reason**: Each sentence of the note maps to present rows (see Claim Map). The cloud, email, and password prompts exist (RC-13, RC-14, RC-58).
- **Risk**: The change is outside the subject of issue #4759. The owner decides whether to keep it.
- **Human decision required**: No.

### D-3 Name the fragment `issue-4759-two-factor-login-note.md` and type it Fixed

- **Alternatives**: (a) Use `pr-<number>.md`, which needs a pull request that does not yet exist. (b) Use a date-based name.
- **Chosen**: `issue-4759-two-factor-login-note.md`, with the change type Fixed.
- **Reason**: Row 2 of the naming table applies, because the issue exists and the pull request does not (RC-37). The Fixed type matches the issue label `bug` and the example in issue #4755 (RC-39).
- **Risk**: The name stays fixed after the pull request opens. The changelog README gives that rule (RC-37).
- **Human decision required**: No.

### D-4 Track the SDK path defect on the two-factor page in a separate issue

- **Alternatives**: (a) Repair the SDK path in this branch. (b) Leave the defect unfiled.
- **Chosen**: File a separate issue. The owner or the orchestrator files it.
- **Reason**: `AGENTS.md` requires one subject for each issue (line 185). The defect sits in the SDK section, not in the MistHelper note (RC-03, RC-04, RC-05).
- **Risk**: Caution: the SDK section stays wrong until that issue merges.
- **Human decision required**: No.

### D-5 Keep the note signature `login_with_return(email, password, two_factor)`

- **Alternatives**: (a) Add `apitoken` to the signature. (b) Write the keyword call that `login_orchestrator.py` uses.
- **Chosen**: Keep the three names in the note.
- **Reason**: The three names match the SDK signature (RC-06). The order matches the call in `login_orchestrator.py` (RC-11).
- **Risk**: A reader may not see `apitoken` in the note.
- **Human decision required**: No.

### D-6 Omit the `design/contracts/` folder

- **Alternatives**: (a) Write a contract for the note text. (b) Write a contract for the SDK call.
- **Chosen**: Omit the folder. `plan.md` states the reason.
- **Reason**: The change edits prose. It defines no interface, input, or output shape.
- **Risk**: No risk identified.
- **Human decision required**: No.

### D-7 Hold T-PR, T-REMOTE-CI, and T-MERGE until a new owner instruction

- **Alternatives**: (a) Run the publication tasks now under this specification. (b) Request a human decision now.
- **Chosen**: Hold the three tasks. Run them only after a new owner instruction.
- **Reason**: The owner hold comment IC_kwDOQltU8c8AAAABm4cmpA stays in force (RC-56). No later comment lifts it. The brief lists the categories that need a human decision, and a publication hold is not one of them.
- **Risk**: The fragment reaches `main` later than this plan states.
- **Human decision required**: No. The owner instruction is the gate, and the final reply names it as the blocker.

### D-8 Verify with the STE gate and the changelog guard test

- **Alternatives**: (a) Run the full test suite and coverage. (b) Run no gate.
- **Chosen**: Run the STE gate on the changed Markdown files and the changelog guard test.
- **Reason**: The change edits Markdown and adds one fragment. CI runs the guard test (RC-41). The STE threshold is 80 (RC-48). AGENTS.md requires the STE gate for each Markdown file (RC-49). No Python file changes.
- **Risk**: Caution: an unrelated regression stays hidden until CI runs. CI runs in T-REMOTE-CI.
- **Human decision required**: No.

### D-9 Propose the label `stage:speckit-artifacts-emitted` and keep `in-progress`

- **Alternatives**: (a) Remove `in-progress`. (b) Add `docs` only.
- **Chosen**: Add `stage:speckit-artifacts-emitted` and keep `in-progress` (RC-57).
- **Reason**: The spec artifacts now exist. Publication stays gated, so the issue stays in progress.
- **Risk**: The stage label is stale if the owner rejects the specification.
- **Human decision required**: No.

## Claim Map

Each sentence of the two login notes maps to remote rows.

| Note sentence | Remote rows |
| - | - |
| Two-factor note: MistHelper completes the step in two places | RC-11, RC-17 |
| Two-factor note: interactive login asks for the code in the terminal, through `--login` or menu 143 | RC-10, RC-12, RC-19, RC-23 |
| Two-factor note: the SDK call takes email, password, and two_factor | RC-06, RC-08, RC-11 |
| Two-factor note: upgrade capture portal asks for the code on `/auth/twofactor` on port 8056 | RC-16, RC-44 |
| Two-factor note and POST_login note: an API-token run never calls the endpoint | RC-07, RC-09 |
| Two-factor note and POST_login note: operations portal on port 8055 has no code page or sign-in page | RC-44, RC-54 |
| POST_login note: interactive login asks for the cloud, the email, and the password | RC-13, RC-14, RC-58 |
| POST_login note: `--login` or menu 143 starts the interactive login | RC-19, RC-23 |
| POST_login note: upgrade capture portal offers a browser login | RC-15, RC-44 |
| POST_login note: operations portal starts with `--login --web-portal` or with a token | RC-24 |
| Both notes: link to the MSP sign-in section | RC-25, RC-26 |

## Remote Verification

The table holds 67 checks. The `STATUS.json` array holds the same 67 entries in the same order. The summary cites the same count.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | Owner comment cites the old note on main (blob f897a85e) | documentation/api/admins/POST_login_two_factor.md | main | f897a85e40ab9c30a0d9bb5e61d2aab9be0fd71e | stale | 91 |
| RC-02 | Corrected two-factor note is on main | documentation/api/admins/POST_login_two_factor.md | main | 98aeb3e81b08c956dc1137f04a833f33220a7bb2 | present | 91 |
| RC-03 | Two-factor page SDK section names mistapi.api.v1.admins.login.twoFactor | documentation/api/admins/POST_login_two_factor.md | main | 98aeb3e81b08c956dc1137f04a833f33220a7bb2 | stale | 68 |
| RC-04 | Installed mistapi has no admins login module | .venv\Lib\site-packages\mistapi\api\v1\admins\login.py | local mistapi 0.64.1 | none (file absent) | absent | 0 |
| RC-05 | Installed mistapi defines twoFactor in login two_factor | .venv\Lib\site-packages\mistapi\api\v1\login\two_factor.py | local mistapi 0.64.1 | d8d9b06c0fdd0b94b9f2d3ea4dafc8c659242eee | present | 17 |
| RC-06 | login_with_return takes apitoken, email, password, and two_factor | .venv\Lib\site-packages\mistapi\__api_session.py | local mistapi 0.64.1 | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 804 |
| RC-07 | An apitoken call takes the self branch and skips two_factor | .venv\Lib\site-packages\mistapi\__api_session.py | local mistapi 0.64.1 | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 849 |
| RC-08 | A login with two_factor calls _two_factor_authentication | .venv\Lib\site-packages\mistapi\__api_session.py | local mistapi 0.64.1 | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 869 |
| RC-09 | _two_factor_authentication posts to /api/v1/login/two_factor | .venv\Lib\site-packages\mistapi\__api_session.py | local mistapi 0.64.1 | 491530cb6e6397ec6fd3b1b34803192f4f68afa3 | present | 1096 |
| RC-10 | Interactive login prompt text is Enter 2FA code | src/mist/access/auth/interactive/credential_prompter.py | main | e1b5197a78e7ec5993faa7dd66eed9c8a553336c | present | 57 |
| RC-11 | Interactive login replays login_with_return with two_factor | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 199 |
| RC-12 | Interactive login asks for the two-factor code through the prompter | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 193 |
| RC-13 | Interactive login asks for the cloud first | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 36 |
| RC-14 | Interactive login asks for the email | src/mist/access/auth/interactive/credential_prompter.py | main | e1b5197a78e7ec5993faa7dd66eed9c8a553336c | present | 23 |
| RC-15 | Upgrade capture portal sign-in path is /auth/signin | src/interfaces/portals/upgrade_portal/app/routes/auth.py | main | 5c496f5465a7f940896080958efafb40b000b0a7 | present | 68 |
| RC-16 | Upgrade capture portal second factor page path is /auth/twofactor | src/interfaces/portals/upgrade_portal/app/routes/auth.py | main | 5c496f5465a7f940896080958efafb40b000b0a7 | present | 69 |
| RC-17 | Upgrade capture portal calls login_with_return with the code | src/interfaces/portals/upgrade_portal/app/routes/auth.py | main | 5c496f5465a7f940896080958efafb40b000b0a7 | present | 411 |
| RC-18 | Menu 143 is the switch to interactive login | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 144 |
| RC-19 | Menu 143 handler runs SwitchToInteractiveLoginManager | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 5133 |
| RC-20 | Menu 143 run calls the rollback login helper | src/foundation/support/refactors/switch_to_interactive_login.py | main | 40704618ea70a52aeba73ad64022b4bd313e8bed | present | 95 |
| RC-21 | Rollback login helper calls the interactive initializer | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2647 |
| RC-22 | Interactive initializer builds and runs LoginOrchestrator | src/foundation/support/refactors/initialize_mist_session_interactive.py | main | c0cea7c2cd4f88d60e7bc040f5dc90364911a45e | present | 48 |
| RC-23 | The --login flag routes to the interactive session | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 7635 |
| RC-24 | The --web-portal flag exists | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 7402 |
| RC-25 | Operator guide heading 'Sign in for an MSP run' exists | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 566 |
| RC-26 | Operator guide says the MSP sign-in covers two-factor authentication | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 505 |
| RC-27 | Regression test test_two_factor_login_resends_credentials_with_installed_sdk exists | tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py | main | 55133013405d582ce05fac7a36d6d11ed8112b64 | present | 251 |
| RC-28 | Regression test asserts the two_factor login URL | tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py | main | 55133013405d582ce05fac7a36d6d11ed8112b64 | present | 272 |
| RC-29 | Replay test asserts login_with_return with two_factor | tests/unit/marvis/mist/access/auth/interactive/test_login_orchestrator.py | main | 55133013405d582ce05fac7a36d6d11ed8112b64 | present | 467 |
| RC-30 | Prompt test asserts the Enter 2FA code text | tests/unit/marvis/mist/access/auth/interactive/test_credential_prompter.py | main | 49087357e58644c8f11147f542c688e5a9cd25c9 | present | 118 |
| RC-31 | Test path named by pull request #4757 is absent | tests/unit/auth/interactive/test_login_orchestrator.py | main | none (file absent) | absent | 0 |
| RC-32 | Merge commit c9aa2bb of pull request #4757 is on main | commits/c9aa2bbc01893a07bb7eec1a6462026a6e70b41b | main | c9aa2bbc01893a07bb7eec1a6462026a6e70b41b | present | 0 |
| RC-33 | Commit 4e81b2a4 changed the two-factor note | documentation/api/admins/POST_login_two_factor.md | 4e81b2a4a724e29476270564be927f797def82be | 98aeb3e81b08c956dc1137f04a833f33220a7bb2 | present | 91 |
| RC-34 | Commit 4e81b2a4 changed the POST_login note | documentation/api/admins/POST_login.md | 4e81b2a4a724e29476270564be927f797def82be | e3c382ede91b7e0587ffa84e4f7eaecafae044b8 | present | 122 |
| RC-35 | Changelog guard defines the five change types | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 45 |
| RC-36 | Changelog guard file holds 18 test functions, the first at line 133 | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 133 |
| RC-37 | Changelog README name table lists the three name forms | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 26 |
| RC-38 | Changelog README gives the fragment write rule | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 35 |
| RC-39 | Fragment example from issue 4755 holds a Fixed bullet | changelog.d/issue-4755-2fa-login.md | main | 7181f1567a7746f358b1f7e41d1917f4635b3c9d | present | 3 |
| RC-40 | Fragment for issue 4759 is absent on main | changelog.d/issue-4759-two-factor-login-note.md | main | none (file absent) | absent | 0 |
| RC-41 | CI runs the changelog guard | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 298 |
| RC-42 | Local gates table names the Tests gate | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| RC-43 | Local gates table names the STE gate and its command | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| RC-44 | Repository file assigns ports 8055 and 8056 | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 181 |
| RC-45 | Repository file gives the fragment rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| RC-46 | Repository file requires the base-5 route for numeric records | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 161 |
| RC-47 | Route script exists | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 0 |
| RC-48 | STE threshold is 80 | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 15 |
| RC-49 | AGENTS.md requires the STE gate for each Markdown file | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 340 |
| RC-50 | Constitution requires the full pipeline for each fragment | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 175 |
| RC-51 | Constitution permits unique records in changelog.d | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 46 |
| RC-52 | README states the verification code prompt | README.md | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | present | 26 |
| RC-53 | OpenAPI defines POST /api/v1/login/two_factor | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 3247 |
| RC-54 | Operations portal holds no two-factor or sign-in code | web_portal | HEAD f03c6c9b36d612a48d7b9652998c2fd87dd777ca | none (no matching file) | absent | 0 |
| RC-55 | No open pull request touches the note or fragment paths | documentation/api/admins/POST_login_two_factor.md | main | none (seven open pull requests checked) | absent | 0 |
| RC-56 | Owner hold comment is in force with no later instruction | issue #4759 comment IC_kwDOQltU8c8AAAABm4cmpA | github | none (comment) | present | 0 |
| RC-57 | Label stage:speckit-artifacts-emitted exists | repository labels | github | none (label) | present | 0 |
| RC-58 | Interactive login asks for the password | src/mist/access/auth/interactive/login_orchestrator.py | main | fd475be9467068e6c34a819697c3c46235801047 | present | 70 |
| RC-59 | changelog.d holds 335 entries on main, including README.md | changelog.d | main | ece56396f47d31dfed7bebe6c69f6dda39f53d83 (tree) | present | 0 |
| RC-60 | Pull request #4924 lists eight closing issues and does not name issue #4759 | pull request #4924 body | github | none (pull request body) | present | 0 |
| RC-61 | Workflow table says ste-lint.yml checks the instruction files and the README | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 470 |
| RC-62 | Repository file accepts four pull request title forms | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 507 |
| RC-63 | Repository file requires one serial merge slot until a merge queue is validated | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 485 |
| RC-64 | Constitution requires one unique fragment for each change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| RC-65 | Constitution lists the pull request body elements | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 518 |
| RC-66 | Constitution requires README updates for new operations or behavior changes | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 400 |
| RC-67 | Known pitfall: a stale GH_TOKEN or GITHUB_TOKEN pushed under another account | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 546 |

## Sources

Local paths read in this step:

- `AGENTS.md` (repository root). Read in full. Writing style at lines 40 to 52. Documentation rule at line 340.
- `.github\copilot-instructions.md`. Read in full, 601 lines. Local gates at lines 50 to 74. Spec route at lines 159 to 168. Ports at lines 378 and 379. Fragment rule at lines 451 to 455. Pull request title rules at lines 501 to 507. Known pitfalls at lines 540 to 594.
- `.specify\memory\constitution.md`. Read in full. Principle I at lines 38 to 46. Principle IV at lines 143 to 175. README rule at line 400. Release-note rule at line 409. Pull request body rule at lines 516 to 518.
- `.specify\templates\spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`. Read in full. The record follows their headings.
- `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv`. Read `spec.md` lines 1 to 110, `tasks.md` lines 1 to 80, and `design\research.md` lines 1 to 80. The shape was copied. The content was not copied.
- `changelog.d\README.md` (remote blob `fcbde10e`). Read in full through the remote copy.
- `tests\guardrails\test_changelog_fragment_policy.py` (remote blob `dbd5e877`). Read the rule constants, the content tests, and the changed-path tests.
- `documentation\api\admins\POST_login_two_factor.md` and `POST_login.md`. Read locally and in the remote copy.
- `documentation\operator-guide.md`. Read lines 504 to 505, 560 to 600, and 612 to 630 locally. The local copy equals the remote blob at `HEAD`.
- `documentation\api\INDEX.md` line 19 and `documentation\api\admins\POST_login.md` lines 14 and 109 (`HEAD`). The index lists the endpoint.
- `documentation\MIST_API_GET_ENDPOINTS.md` line 1066 and `documentation\MIST_API_MISSING_ENDPOINTS.md` line 1010 (`HEAD`). Both list `/api/v1/self/two_factor/token`, not the login endpoint. No conflict.
- `documentation\mist-api-openapi31yaml.yaml`. Read lines 3240 to 3300 locally. Endpoint at line 3247 (RC-53).
- `documentation\quality-gates.md`, `architecture.md`, `development-setup.md`, and `container-deployment.md`. Searched at `HEAD` with `git grep`. None holds two-factor text. Not applicable to this change.
- `.venv\Lib\site-packages\mistapi` (version 0.64.1, from the dist-info name). Read `__api_session.py` lines 800 to 830 and 826 to 872, and lines 1080 to 1100. Read `api\v1\login\two_factor.py` lines 17 and 37 by search. Blob hashes come from `git hash-object` without a write flag.
- `.ste-linter.toml`, `.github\workflows\ci.yml`, `README.md`, and `.specify\scripts\powershell\spec-route.ps1`. Checked in the remote copy.

Remote sources (GitHub, `jmorrison-juniper/MistHelper`):

- Issue #4759 with its four comments and its labels.
- Pull requests #4757 (merged), #4924 (merged), #4208 (open), and #4619 (merged). Issues #4755 and #4760 (closed).
- Commits `c9aa2bbc01893a07bb7eec1a6462026a6e70b41b` and `4e81b2a4a724e29476270564be927f797def82be`.
- The main tree at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, with 11,404 entries, not truncated.
- Seven open pull requests, with their file lists.

URLs fetched: none. No upstream `mistapi` URL was fetched, so every SDK claim cites the installed package.

## Unverified

- **U-1 Guard result**: The owner reports `17 passed, 1 skipped` for the changelog guard (comment IC_kwDOQltU8c8AAAABlEXN1g). The guard file holds 18 test functions (RC-36). This step runs no test, so the pass count is not verified. T-LOCAL-GATES reruns the guard.
- **U-2 STE scores**: The owner reports STE scores of 97 and 100 (comments IC_kwDOQltU8c8AAAABlEXN1g and IC_kwDOQltU8c8AAAABlGcWBw). This step runs no linter. T-LOCAL-GATES reruns STE.
- **U-3 Patch hash**: The owner reports a complete diff SHA-256 of `5597f7825fa48b48f8feb178764f26146f12d448ee21c4fdc7cb97bf4b2120e6`. The export format and the base diff text are outside the repository. This step cannot recompute the hash.
- **U-4 Ownership scan**: The owner reports 19 open pull requests, 686 file entries, and 421 rename sources. This step checked seven open pull requests (RC-55). The earlier scan cannot be repeated from this session.
- **U-5 Candidate fragment**: The candidate fragment is absent from the repository tree, the local working tree, and `main`. The issue does not name its location. T003 writes a new fragment from `spec.md`.

## Skills

No skill was loaded. The container skills do not apply, because the change has no Podman question. The Juniper skills do not apply, because the change has no device behavior question.
