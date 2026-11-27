# Tasks: Cisco converter licensing and authorship decisions

## Format

Each task shows its ID, the parallel marker, its requirement IDs, its files, its acceptance statement, its verification command, and its status. Status values are open, verified-present, partial, and absent.

The record Markdown files for each STE command are these ten files:

- specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/spec.md
- specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/plan.md
- specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/tasks.md
- specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/analysis.md
- specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md
- specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/data-model.md
- specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/quickstart.md
- specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/checklists/requirements.md
- specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/checklists/decisions.md
- specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/checklists/provenance.md

## Phase 1: Evidence (completed in the drafting pass)

**T001** [P] Requirements: FR-009, FR-018
- Task: Verify the source license at commit d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c.
- Files: specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md, rows RC-49 to RC-52.
- Acceptance: Blob e9ae5eff92457c2372db3be30a3d99166aeee547 names CC BY-NC 4.0 at line 1, names no holder at line 3, and states a NonCommercial term at line 16.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md`
- Status: verified-present

**T002** [P] Requirements: FR-010, FR-011, FR-018
- Task: Verify the MistHelper license and the converter files on main.
- Files: specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md, rows RC-01 to RC-03 and RC-45 to RC-47.
- Acceptance: Blob d115eeab9dbd6f61d0233b0894d3f8309bb976e8 names CC BY-NC-SA 4.0 at line 1. The three converter files exist on main with the blob SHAs in research.md.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md`
- Status: verified-present

**T003** [P] Requirements: FR-013, FR-018
- Task: Verify the pull requests and related issues that the record cites.
- Files: specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md, rows RC-31, RC-48, and RC-62 to RC-64, and the Sources section. Also analysis.md.
- Acceptance: PR 4596 and PR 4226 show their merged state. Issues 4224, 4632, 4633, 4634, 4636, 4643 to 4649, and 4870 show their states in the Sources section.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/analysis.md`
- Status: verified-present

## Phase 2: Owner decisions (HUMAN-DECISION-REQUIRED)

**T004** Requirements: FR-001, FR-002, FR-013
- Task: The owner records the answer to Q1 and decision D-1 (licensor and holder of the source).
- Files: specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/spec.md, Clarifications Q1. specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md, decision D-1.
- Acceptance: The answer names the licensor and the legal basis. Legal review appears by role. The owner records the date of the answer.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/spec.md specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md`
- Status: open. HUMAN-DECISION-REQUIRED.

**T005** Requirements: FR-001, FR-002, FR-003, FR-006
- Task: The owner records the answer to Q2 and decision D-2 (source-code reuse).
- Files: specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/spec.md, Clarifications Q2. specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md, decision D-2. specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/checklists/decisions.md.
- Acceptance: The answer names one option (A, B, or C) and the approved scope. An approved option names its legal basis. All other scope stays blocked.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/spec.md specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/checklists/decisions.md`
- Status: open. HUMAN-DECISION-REQUIRED.

**T006** Requirements: FR-001, FR-002, FR-003
- Task: The owner records the answer to Q3 and decision D-3 (text reuse).
- Files: specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/spec.md, Clarifications Q3. specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md, decision D-3. specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/checklists/decisions.md.
- Acceptance: The answer names one option and the approved scope. All other text stays blocked.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/spec.md specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/checklists/decisions.md`
- Status: open. HUMAN-DECISION-REQUIRED.

**T007** Requirements: FR-001, FR-002, FR-003
- Task: The owner records the answer to Q4 and decision D-4 (mapping reuse).
- Files: specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/spec.md, Clarifications Q4. specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md, decision D-4. specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/checklists/decisions.md.
- Acceptance: The answer names one option and the approved scope. The answer states whether mapping facts count as protected expression.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/spec.md specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/checklists/decisions.md`
- Status: open. HUMAN-DECISION-REQUIRED.

**T008** Requirements: FR-001, FR-002, FR-003
- Task: The owner records the answer to Q5 and decision D-5 (asset reuse).
- Files: specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/spec.md, Clarifications Q5. specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md, decision D-5. specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/checklists/decisions.md.
- Acceptance: The answer names one option and each approved asset by path. All other assets stay blocked.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/spec.md specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/checklists/decisions.md`
- Status: open. HUMAN-DECISION-REQUIRED.

**T009** Requirements: FR-001, FR-002, FR-005
- Task: The owner records the answer to Q6 and decision D-6 (independent-authorship rules).
- Files: specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/spec.md, Clarifications Q6. specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md, decision D-6.
- Acceptance: The answer names one rule set and the reviewer steps that apply before merge.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/spec.md specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md`
- Status: open. HUMAN-DECISION-REQUIRED.

**T010** Requirements: FR-001, FR-002, FR-004
- Task: The owner records the answer to Q7 and decision D-7 (distribution path).
- Files: specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/spec.md, Clarifications Q7. specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md, decision D-7.
- Acceptance: The answer names one path for the repository, releases, and container images. The answer names the publication workflows that change.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/spec.md specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/research.md`
- Status: open. HUMAN-DECISION-REQUIRED.

## Phase 3: Audit and link

**T011** Requirements: FR-011
- Task: Compare each converter file on main with the source at the pinned commit. Use read-only evidence. Copy no text. Start only after T009 records the authorship rules.
- Files: specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/analysis.md, the provenance table. specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/checklists/provenance.md.
- Acceptance: Each converter file has one result: matches protected expression, no match found, or not compared. Each result cites the blob SHA of both files.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/analysis.md specs/numbered/0/0/1/2/2/0/2/0/4635-cisco-converter-licensing-authorship/design/checklists/provenance.md`
- Status: open. Depends on T009.

**T012** Requirements: FR-006, FR-007, FR-012
- Task: Link this record from parity tasks.md line 29 (T002) and plan.md line 125 (G1). Keep the text of gates G2 to G5 unchanged. Start only after T004 to T010 finish.
- Files: specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md. specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/plan.md.
- Acceptance: T002 and the G1 row name this record path and the approved scope. Gates G2 to G5 keep their text. No parity checkbox changes state.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80 specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/plan.md`
- Status: open. Depends on T004, T005, T006, T007, T008, T009, and T010.

## Phase 4: Final gates and delivery

**T-LOCAL-GATES** Requirements: FR-015, FR-016, FR-018
- Task: Run each local gate that applies to the changed files. Run the compile gate before the commit, because the constitution requires it at line 370.
- Commands and expected results:
  - Compile: `python -m py_compile MistHelper.py`. Expected: no output.
  - Tests: `python -m pytest tests/guardrails/test_process_folder_structure.py`. Expected: all tests pass, with the examined counts printed.
  - STE: `ste-linter --config .ste-linter.toml --min-score 80` with the ten record files and the two parity files that T012 changes. Expected: each file scores 80 or above.
  - STE on Windows: `.venv\Scripts\ste-linter.exe --config .ste-linter.toml --min-score 80` with the same files (quality-gates.md line 283, RC-77).
  - Not applicable: Lint, Format, Types, Full tests, Safe sweep, Coverage, Test quality, Complexity, Security lint, and Dependency audit. Also not applicable: Code quality, Dead code, Docstrings, Menu reference, Symbols, Ops portal, and Ops platform. No Python, test, dependency, or portal file changes exist.
- Files: the ten record files and the two parity files that T012 changes.
- Acceptance: Each applicable gate reports its expected result. The pull request body names each result and its count.
- Verification: `python -m pytest tests/guardrails/test_process_folder_structure.py`
- Status: open

**T-PR** Requirements: FR-014, FR-016, FR-017
- Task: Add the in-progress label to issue 4635. Check the open pull requests for overlapping files. Create the branch chore/4635-cisco-converter-licensing-authorship from main. Add the files by explicit path. Commit. Rebase the branch onto origin/main before the push. Open the pull request.
- Commit message: `docs(spec): record Cisco converter licensing and authorship decisions`. The body holds `Closes #4635` and the trailer `Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>`.
- Pull request: The title equals the commit subject. The body holds `Closes #4635`, the gate results, and the reason for no changelog fragment (D-11). It also holds the count of remote checks (77), the rollback notes from plan.md, and the seven human decisions. The labels are chore, docs, in-progress, and needs-human-review.
- Files: the ten record files. The two parity files join only after T012 runs.
- Acceptance: The pull request exists. Its body contains `Closes #4635`. It holds the four labels named above. The commit adds files by explicit path only.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80` with the ten record files, run before the push.
- Status: open
- Caution: A commit pushed after the squash merge leaves an orphan pull request. Create a new branch from main for later changes.

**T-REMOTE-CI** Requirements: FR-015
- Task: Watch the pull request checks until they finish. Run `gh pr checks` with the `--watch` option for the pull request number that T-PR reports.
- Acceptance: The STE lint job passes, as defined in .github/workflows/ste-lint.yml at line 17. Every required check reports success.
- Verification: `ste-linter --config .ste-linter.toml --min-score 80` with the ten record files. The CI job runs the same gate.
- Status: open

**T-MERGE** Requirements: FR-008, FR-017
- Task: Use one serial merge slot (RC-76). Add the `auto-merge` label only after all three conditions hold. The label starts the merge once checks pass (RC-75). The conditions are: every check passes, the owner or the maintainer removes needs-human-review after review, and the orchestrator authorizes the merge.
- Acceptance: The auto-merge label appears only after the three conditions hold. No release, tag, or image publication occurs.
- Verification: `python -m pytest tests/guardrails/test_process_folder_structure.py` on main after the merge.
- Status: open
- Caution: Auto-merge without the human review removes the review point. Revert the merge commit if an unreviewed decision reaches main.

## Tests

- **TS-01** (FR-015): Run `ste-linter --config .ste-linter.toml --min-score 80` on each record Markdown file. Expected: each file scores 80 or above.
- **TS-02** (FR-016): Run `python -m pytest tests/guardrails/test_process_folder_structure.py`. Expected: all tests pass, and the guard prints the examined counts.
- **TS-03** (FR-001, FR-002, FR-003, FR-004, FR-005, FR-013): Read the Clarifications in spec.md and the decisions in design/research.md. Expected: D-1 to D-7 each show two or more options, evidence rows, a recommended option, and an owner. Each legal decision keeps HUMAN-DECISION-REQUIRED until the owner answers.
- **TS-04** (FR-009, FR-010, FR-018): Count the rows of design/research.md that begin with `| RC-`. Count the entries in the STATUS remote_checks array. Expected: both counts equal 77. Compare each blob SHA with the GitHub API. Expected: each blob SHA matches the API.
- **TS-05** (FR-006, FR-007, FR-008, FR-011, FR-012, FR-017): Maintainer review. Expected: parity T002 and the G1 row link this record only after the owner answers. Gates G2 to G5 keep their text. The analysis holds the audit result. No task authorizes a release. The needs-human-review label remains until the review completes.
- **TS-06** (FR-014): Read the record and search it for tokens, secrets, customer data, and legal communications. Expected: none found.
