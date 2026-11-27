# Research: Menu step names the generated pages

Each decision lists the alternatives, the reason, and the risk. Remote facts come from read-only `gh api` calls on `main`. Local facts come from the working tree, and ten local files match their remote blob SHAs (see Local to Remote Equality).

## Facts From the Issue and Linked Work

- Issue #4922 is OPEN. Its labels are `chore` and `docs`. It has no comments. It was created on 2026-11-25 at 01:41:24 UTC. Source: `gh issue view 4922 -R jmorrison-juniper/MistHelper`.
- Linked pull requests: none. `gh pr list -R jmorrison-juniper/MistHelper --state all --search "4922"` returned an empty list.
- Related issues: #4916 is CLOSED. It removed the menu content from the README. #4920 is CLOSED. Its record holds the menu 309 plan, which records this stale step. #4915 is OPEN. It tracks the stale operation count in the operator guide, which is out of scope.
- Existing record: none. No folder under `specs\` starts with `4922-`. The remote tree has no entry under `specs/numbered/0/0/1/2/4/1/4/2/` (RC-27).
- Route: `specs\numbered\0\0\1\2\4\1\4\2`. The base-5 digits of 4922 are 1, 2, 4, 1, 4, and 2. `Get-SpecRadixSegments` in `.specify/scripts/powershell/spec-route.ps1` pads them to eight segments with zeros, which gives the route (RC-25).

## Decisions

### D-1 Amend step 5 and the README bullet

- Decision: Amend step 5 of "Adding New Menu Operations" and the README bullet of the Documentation section.
- Alternatives: (a) amend step 5 only. (b) amend step 5 and the README bullet. (c) rewrite the whole Development Workflow section.
- Chosen: (b).
- Rationale: The README bullet at line 400 still says the README MUST change for each new operation (RC-02). That duty contradicts the README role that issue #4916 set (RC-09). Option (a) leaves the contradiction in the same section. Option (c) changes rules outside this issue.
- Risk: The bullet drops a MUST. D-5 classes the change as a wording correction.

### D-2 Amend the rule file in the same pull request

- Decision: Amend step 1 of "Add a menu operation" in `.github/copilot-instructions.md` in this pull request.
- Alternatives: (a) amend it in this pull request. (b) file a second issue. (c) leave it stale.
- Chosen: (a).
- Rationale: The issue says the rule file already states that the README keeps no menu number. On `main`, step 1 at line 242 says the opposite (RC-06 and RC-07). The constitution and the rule file describe one procedure. A split leaves agents with two rules for one step. The fix is one line.
- Risk: The diff grows by one line in another file. Guard case `rule-file-step` covers the line.

### D-3 Name both generated pages and both commands in step 5

- Decision: Step 5 names `python scripts/generate_menu_wiki.py`, `python -m scripts.menu_api_map`, `documentation/menu_reference.md`, and `documentation/wiki/Menu-Reference.md`.
- Alternatives: (a) name the generator only. (b) name both pages and both commands. (c) name the wiki page only.
- Chosen: (b).
- Rationale: The CI job `menu_reference_drift` compares both pages after the generator runs (RC-16). The generator writes both files (RC-12 and RC-13). Each page needs a regeneration.
- Risk: A later path change breaks a guard case. The guard names each path, so the change fails in the same pull request.

### D-4 Require operator notes only when an operation needs operator steps

- Decision: Step 5 requires an operator note only when the operation needs operator steps.
- Alternatives: (a) require a note for each operation. (b) require a note when the operation needs operator steps. (c) require no note.
- Chosen: (b).
- Rationale: The operator guide holds notes for menus with operator steps. Menu 164 requires `APPLY`, menu 305 requires `CONFIGURE`, and menu 306 requires `RESTORE` (RC-11, and operator guide lines 118 to 130). Menus 213 and 214 also have notes (RC-10). Option (a) adds upkeep for each simple export. Option (c) drops the operator steps for destructive operations.
- Risk: A reviewer disagrees about which operations need operator steps. The operator guide stays the page for those notes, and the reviewer decides in the pull request.

### D-5 Bump the constitution to 1.9.1 as PATCH

- Decision: Set the version to 1.9.1, the class to PATCH, and `Last Amended` to 2026-11-26.
- Alternatives: (a) MINOR, 1.10.0. (b) PATCH, 1.9.1.
- Chosen: (b).
- Rationale: The amendment rules define PATCH for clarification and wording (RC-05). The change adds no principle. The removed MUST aligns the README rule with the owner decision of issue #4916.
- Risk: A reviewer reads the removed MUST as a change of rule, which is MINOR. The Sync Impact Report and the pull request body state the reason. The reviewer can change the class before the merge.

### D-6 Add one changelog fragment with the issue-form name

- Decision: Add `changelog.d/issue-4922-constitution-menu-doc-step.md` with one `Changed` bullet.
- Alternatives: (a) add a fragment. (b) add no fragment and state the reason in the pull request body.
- Chosen: (a).
- Rationale: Constitution step 6 and the Documentation section state that each change MUST add one fragment. The constitution supersedes the practice documents, as its governance section says. `changelog.d/README.md` rule 4 exempts an internal-only change (RC-18). Issue #4916 added a fragment for a documentation change, which sets precedent. The conflict is recorded in `analysis.md`.
- Risk: The release note lists an internal rule. The bullet is short and names the issue.

### D-7 Add one parametrized method to `TestPolicyStaysStated`

- Decision: Add one method with five cases at the end of the existing class `TestPolicyStaysStated`.
- Alternatives: (a) a new test file in `tests/guardrails/`. (b) a new class in the module. (c) one new method in the existing class. (d) a new file in a new package under `tests/guardrails/`.
- Chosen: (c).
- Rationale: `tests/guardrails` holds 79 direct children on `main` (RC-28). The Five-Item Rule forbids a new direct child under a noncompliant parent. Option (a) adds one. Option (b) adds a top-level child to a module that already holds more than five top-level definitions. Option (d) adds a direct child to `tests/guardrails`. Option (c) adds one method, and the class then holds five methods, which the rule allows. The class already guards instruction-file wording (RC-19).
- Risk: The module keeps its debt. Complexity Tracking in `plan.md` records the debt and a follow-up.

### D-8 Keep historical spec records unchanged

- Decision: Leave each historical spec record unchanged.
- Alternatives: (a) update each historical record. (b) keep each historical record.
- Chosen: (b).
- Rationale: The records document past plans and tasks. The code search found the old phrase in five historical records (U-1). Rewriting them removes the evidence of earlier decisions.
- Risk: An agent copies the old step from a record. The constitution and the rule file give the current step.

### D-9 Measure the constitution with `ste-linter`, and keep the CI list

- Decision: Measure the constitution in T-LOCAL-GATES and report the score. Keep the CI list unchanged.
- Alternatives: (a) add the constitution to the CI STE list. (b) measure the constitution and keep the CI list. (c) skip the measurement.
- Chosen: (b).
- Rationale: The Writing style section of `AGENTS.md` requires each Markdown file to score 80 or above (line 40 onward). The CI list in `.github/workflows/ste-lint.yml` omits the constitution (RC-22). A change to the CI list alters a gate, which this issue does not own. The measurement gives evidence without a new gate.
- Risk: The constitution scores below 80 before this change. The pull request body reports the score, and a follow-up issue owns the fix.

### D-10 Commit this record in the same pull request

- Decision: Add the record folder to the same pull request as the change.
- Alternatives: (a) the same pull request. (b) a separate spec pull request.
- Chosen: (a).
- Rationale: The record of issue #4920 sits on `main` with its change (RC-23). Principle I allows a change to add only its own record. One pull request keeps the record with the change that it describes.
- Risk: The diff grows. The record holds Markdown only.

### D-11 Keep the generic README checkbox in the pull request template

- Decision: Leave the checkbox in `.github/PULL_REQUEST_TEMPLATE.md` unchanged.
- Alternatives: (a) change the checkbox. (b) keep the checkbox.
- Chosen: (b).
- Rationale: The checkbox reads "README.md updated (if user-facing changes)" (RC-21). It names no menu operation. The README still holds start-guide content, so the checkbox still fits start-guide changes. A change widens the scope.
- Risk: An author ticks the checkbox for a menu operation and edits the README. The constitution step now says the README holds no menu content.

### D-12 Check exact phrases inside marker slices

- Decision: The guard checks phrases inside a slice that starts and ends at a marker.
- Alternatives: (a) match full sentences. (b) match phrases inside a marker slice. (c) parse the Markdown.
- Chosen: (b).
- Rationale: A full-sentence match breaks on a line wrap or a reworded sentence. A Markdown parser adds a dependency. The existing guard `tests/guardrails/test_websocket_transport_constitution.py` checks phrases (RC-20). The slice limits each check to one step or one bullet.
- Risk: A reworded phrase passes the check. Each phrase names a path or a version, and the review checks the wording.

## Remote Verification

The remote checks read `main` by blob SHA, and each line number comes from a decoded file body. The table has 28 rows. `design/research.md`, `STATUS.json`, and `summary.md` each report the same count.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| --- | --- | --- | --- | --- | --- | --- |
| RC-01 | Constitution step 5 tells the author to update the README operation count and menu table. | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | stale | 352 |
| RC-02 | The constitution README bullet says the README MUST change for each new operation. | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | stale | 400 |
| RC-03 | The constitution footer shows Version 1.9.0 and Last Amended 2026-10-06. | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 562 |
| RC-04 | The Sync Impact Report shows the version change 1.8.0 -> 1.9.0 (MINOR). | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 4 |
| RC-05 | The amendment rules define PATCH for clarification, wording, or typo fixes. | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 537 |
| RC-06 | Rule file step 1 of "Add a menu operation" tells the author to update the README menu table. | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | stale | 242 |
| RC-07 | The rule file says the README keeps no menu number. This is the issue premise. | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | absent | 0 |
| RC-08 | Rule file step 2 runs the two menu generators. | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 243 |
| RC-09 | The README links to the menu reference and holds no menu list. | `README.md` | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | present | 40 |
| RC-10 | The operator guide holds the notes for menus 213 and 214. | `documentation/operator-guide.md` | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 120 |
| RC-11 | The operator guide holds the confirmation note for menu 305. | `documentation/operator-guide.md` | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 126 |
| RC-12 | The generator writes the wiki menu reference page. | `scripts/generate_menu_wiki.py` | main | f959225275536743e93bc95d37cb015865a73d53 | present | 65 |
| RC-13 | The generator writes the menu reference page. | `scripts/generate_menu_wiki.py` | main | f959225275536743e93bc95d37cb015865a73d53 | present | 66 |
| RC-14 | The generated menu reference page exists. | `documentation/menu_reference.md` | main | 2bd972183c64302e76442d30669bb9e7362856f1 | present | 0 |
| RC-15 | The generated wiki menu reference page exists. | `documentation/wiki/Menu-Reference.md` | main | 2bd972183c64302e76442d30669bb9e7362856f1 | present | 0 |
| RC-16 | The CI menu reference drift job compares both generated pages. | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 722 |
| RC-17 | The menu API map module runs as a command. | `scripts/menu_api_map/__main__.py` | main | 19f72aa767a1821f2ccf88680b8778b89012873d | present | 198 |
| RC-18 | The changelog policy exempts an internal-only change from a fragment. | `changelog.d/README.md` | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| RC-19 | The changelog guard lists the constitution and the rule file as guidance files. | `tests/guardrails/test_changelog_fragment_policy.py` | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 58 |
| RC-20 | The WebSocket guard reads the constitution exception text. | `tests/guardrails/test_websocket_transport_constitution.py` | main | 447306b0a09400daabf79987e2b1a97f6430d951 | present | 36 |
| RC-21 | The pull request template holds a generic README checkbox. | `.github/PULL_REQUEST_TEMPLATE.md` | main | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 35 |
| RC-22 | The STE CI list names five files and omits the constitution. | `.github/workflows/ste-lint.yml` | main | abaeff6d5e299bfa7de4dc15d04f4ef31cf13b5f | present | 44 |
| RC-23 | The reference plan of issue #4920 says step 5 does not apply to menu 309. | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/plan.md` | main | 686c89f85ee7c094526bafaf782d4398f6c523ff | present | 54 |
| RC-24 | The reference plan Complexity Tracking names the constitution follow-up. | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/plan.md` | main | 686c89f85ee7c094526bafaf782d4398f6c523ff | present | 189 |
| RC-25 | The spec route resolver defines `Resolve-SpecFeaturePath`. | `.specify/scripts/powershell/spec-route.ps1` | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 34 |
| RC-26 | `AGENTS.md` holds the Simplified Technical English writing rules. | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| RC-27 | No record folder exists for issue 4922 on `main`. | `specs/numbered/0/0/1/2/4/1/4/2/` | main | not applicable, no tree entry | absent | 0 |
| RC-28 | `tests/guardrails` holds 79 direct children, above the Five-Item Rule limit. | `tests/guardrails/` | main | not applicable, directory count from the tree | present | 0 |

Source of RC-27 and RC-28: one `gh api` call for the recursive tree of `main`, with the count of entries that match `^tests/guardrails/[^/]+$`.

## Local to Remote Equality

Ten local files match the remote blob SHAs in the table above. The check ran `git hash-object` on each file, which is read-only. The files are the constitution, the rule file, `README.md`, `changelog.d/README.md`, and the operator guide. The rest are the generator, the pull request template, the changelog guard, the WebSocket guard, and `ci.yml`.

## Sources

- `AGENTS.md`: the Writing style section (line 40 onward) and the Git flow sections.
- `.github/copilot-instructions.md`: the Language and environment section and the Menu categories section. The local gates table (STE row, line 74) and the Add a menu operation section (lines 230 to 246) are also used. The Test quality ratchet section gives the commands.
- `.specify/memory/constitution.md`: the Sync Impact Report (lines 1 to 25) and the Adding New Menu Operations section (lines 339 to 358). The Documentation section (lines 398 to 412) and the Governance section (lines 525 to 563) are also used.
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`: the headings and the record shape. The templates name no README menu step.
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/`: the spec, plan, tasks, analysis, and design files, read for shape and depth. The record content is not copied.
- `documentation/operator-guide.md`: lines 118 to 134 for the menu notes.
- `documentation/quality-gates.md`: line 67 for the `menu_reference_drift` command, and lines 283 to 292 for the STE gate.
- `scripts/generate_menu_wiki.py`: lines 64 to 67 for the output paths.
- `changelog.d/README.md`: the Name the file section (line 19 onward) and rule 4 (line 58).
- `tests/guardrails/test_changelog_fragment_policy.py`: `GUIDANCE_FILES` (line 56 onward), `NAME_FORMS` (line 64), and the class `TestPolicyStaysStated` (line 231 to line 264).
- `tests/guardrails/test_websocket_transport_constitution.py`: line 36.
- `tests/guardrails/test_destructive_menu_docs.py` and `tests/guardrails/test_move_module_guidance.py`: read for scope. Neither guards the README menu step, so neither takes the new cases.
- `.github/workflows/ci.yml`: lines 93, 101, 104, 107 (path variables), and lines 704 to 725 (menu drift job).
- `.github/workflows/ste-lint.yml`: line 44.
- `.github/PULL_REQUEST_TEMPLATE.md`: line 35.
- `README.md`: lines 40, 43, 46, and 113 for the start guide and the links.
- `scripts/menu_api_map/__main__.py`: line 198.
- `.specify/scripts/powershell/spec-route.ps1`: lines 4 and 34.
- GitHub issues, read through `gh issue view`: https://github.com/jmorrison-juniper/MistHelper/issues/4922, https://github.com/jmorrison-juniper/MistHelper/issues/4916, https://github.com/jmorrison-juniper/MistHelper/issues/4920, and https://github.com/jmorrison-juniper/MistHelper/issues/4915.
- GitHub code search, read through `gh search code "Update the operation count" -R jmorrison-juniper/MistHelper`. It returned six paths, U-1 covers its limits.

## Not Applicable Checks

- Mist API: `documentation/mist-api-openapi31yaml.yaml` was not read. The issue names no Mist endpoint.
- mistapi: `.venv\Lib\site-packages\mistapi` was not read. The issue names no SDK function.
- Podman and container skills: not loaded. The issue has no container question.
- Juniper device skills: not loaded. The issue has no device question.
- Architecture, development setup, and container deployment pages: a local search for the README menu step found no match in `documentation/`. Those pages stay unchanged.

## Unverified

- U-1: GitHub code search covers the default branch index. The index can lag. Copies of the old step can exist outside its result set. The result listed the rule file and five historical spec records.
- U-2: The STE scores of the changed files. The gates run in T-LOCAL-GATES. This stage runs no gate.
- U-3: The guard results. The tests run in T-LOCAL-GATES. This stage runs no test.
- U-4: The remote CI results. They become known in T-REMOTE-CI.
