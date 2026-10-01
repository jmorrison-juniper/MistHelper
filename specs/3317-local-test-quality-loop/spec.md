# Feature Specification: Local Test-Quality Loop

**Feature Branch**: `jmorrison-juniper-local-test-quality-guidance`

**Created**: 2026-09-30

**Status**: Local implementation, validation, and committed comparison are complete. Delivery remains pending.

**Input**: User description: "Complete the required specification for MistHelper issue #3317. Add the missing local test-quality check to three development guides. Require direct guardrails and offline proof of the installed analyzer's scope."

**Issue**: [MistHelper #3317](https://github.com/jmorrison-juniper/MistHelper/issues/3317)

**SPECIFY_FEATURE_DIRECTORY**: `specs/3317-local-test-quality-loop`

**SPEC_FILE**: `specs/3317-local-test-quality-loop/spec.md`

The required test-quality check already runs in continuous integration (CI).
Three local guides omit that check.
Maintainers need a complete local procedure before they push a committed change.
The procedure must use the same scope controls as current CI.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Check a Local Commit Before Push (Priority: P1)

A maintainer uses any one of the three local guides.
The guide explains the required test-quality command, the intended base, and the scope.
The maintainer checks the local commit before push.

**Why this priority**: Local checks prevent avoidable CI failures and extra pushes.

**Independent Test**: Use each guide for a separate walkthrough.
Compare its command and scope instructions with live CI and verified analyzer behavior.

**Acceptance Scenarios**:

1. **Given** current CI and a valid intended base, **When** a maintainer reads any named guide, **Then** that guide contains the complete required command.
   It names the repository settings, baseline, base comparison, and both explicit full-suite paths.
2. **Given** a local feature commit, **When** the maintainer prepares the required check, **Then** the guide directs a fetch of the intended base.
   It uses that same remote reference for the comparison.
3. **Given** staged, unstaged, or untracked tests, **When** the maintainer reads the guide, **Then** it explains their verified selection and analysis behavior.
   The required pre-push proof uses a clean local commit.
   Selection compares the intended base revision with `HEAD`.
   The comparison excludes paths that exist only in staged, unstaged, or untracked changes.
   The analyzer reads selected files from the current working tree.
4. **Given** new findings or an unresolved base, **When** the required check fails, **Then** the guide prohibits push.
   The maintainer corrects the cause and repeats the check.
5. **Given** a completed check, **When** the commit, checked files, or intended base changes, **Then** the maintainer repeats the affected local checks.
   Earlier results do not prove the changed candidate.

---

### User Story 2 - Detect Incomplete Local Guidance (Priority: P1)

A maintainer runs a direct guardrail against live CI and all three guides.
The guardrail rejects incomplete commands and incorrect scope controls.
It reports the inputs and paths that it checked.

**Why this priority**: A direct check prevents another omission when CI or a guide changes.

**Independent Test**: Give the guardrail valid local inputs.
Then change one required command or input at a time.
Confirm success for valid inputs and failure for each incorrect input.

**Acceptance Scenarios**:

1. **Given** matching CI and complete guides, **When** the guardrail runs, **Then** it succeeds and reports three checked documents.
   It reports six required input files and two explicit full-suite paths.
   Those inputs are the three guides, CI workflow, repository settings, and baseline.
   It also identifies the two automatic triggers and four effective trigger paths.
2. **Given** a missing or incorrect command in one guide, **When** the guardrail runs, **Then** it fails.
   Its report identifies the guide and incorrect control.
3. **Given** a new full-suite path in the live CI command, **When** the guides omit that path, **Then** the guardrail fails.
   A duplicate copy of the old command does not define the expected result.
4. **Given** an unreadable required input or an unrecognizable CI command, **When** the guardrail runs, **Then** it fails with the input name.
   It does not report success or treat the missing input as a valid empty scope.
5. **Given** correct text only in a comment or an unused example, **When** the active local procedure uses an incorrect command, **Then** the guardrail fails.
   Equivalent quoting and option order remain valid if they preserve the command's meaning.

---

### User Story 3 - Prove Scope Without Network Access (Priority: P2)

A maintainer runs controlled offline cases through the unchanged installed analyzer.
The cases prove which tests the command includes.
They also prove full-suite triggers, failure behavior, and comparison semantics.

**Why this priority**: Matching command text does not prove matching test selection.

**Independent Test**: Use an isolated local repository with known commits and test findings.
Run the installed analyzer against those inputs without network access.
Check the observed scope, counts, findings, and exit result against explicit expectations.

**Acceptance Scenarios**:

1. **Given** selected and excluded tests with distinct known findings, **When** a changed-scope command runs, **Then** its findings prove the actual selection.
   A text match alone does not satisfy this scenario.
2. **Given** a change to any effective trigger path, **When** the same command runs, **Then** it scans the full suite.
   An unchanged test with a known new finding proves that scope.
3. **Given** two bases with different histories, **When** the comparison runs, **Then** the evidence identifies the installed comparison semantics.
   A divergent-history case distinguishes endpoint comparison from merge-base comparison.
4. **Given** invalid controls, an unknown base, or unreadable analyzer inputs, **When** the corresponding negative case runs, **Then** it proves failure.
   A skipped case does not count as successful evidence.
5. **Given** staged, unstaged, and untracked tests, **When** each case runs before and after a local commit, **Then** the evidence records selection and analysis separately.
   The guidance matches that evidence.

### Edge Cases

- A changed test name can match one supported naming pattern but not another.
  Lookalike names must not count as recognized tests without proof.
- A deletion leaves no file to analyze.
  A rename can enter or leave test scope.
  Expected scope must match the installed analyzer.
- An unrelated-only change can produce a valid empty changed-test scope.
  An unknown base or missing baseline cannot produce a valid empty gate result.
  The guardrail rejects any missing required input.
  The analyzer alone uses defaults when its settings file is missing or empty.
- A trigger path can change through addition, modification, deletion, or rename.
  Offline evidence must cover these change forms where they apply.
- A selected file can contain uncommitted edits.
  Committed path selection does not necessarily prove committed file content.
- A baseline can allow existing findings while the check rejects new findings.
  Do not change the baseline to avoid this issue's acceptance criteria.
- The intended base can differ from `main`.
  A stale or incorrect base must not replace the intended comparison.
- CI command text can change while an old example remains elsewhere.
  The guardrail must read the named live job and step.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Update local test-quality guidance in exactly the three documents below.
  Each named section must provide a complete local procedure.
  A link to another guide does not replace its required command.

  | Document | Required section |
  |----------|------------------|
  | `.github/copilot-instructions.md` | Validate locally, then push once |
  | `agents.md` | Local Development Quick Reference |
  | `.github/instructions/git-flow-multi-agent.instructions.md` | Part 3 / The local-first loop |

- **FR-002**: Each section MUST contain the installed `test-quality-analyzer` command with the exact repository settings and baseline.
  The pull-request comparison MUST include `--changed-from` and every `--full-gate-path` from live CI.
  The current command contract is:

  ```text
  test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/$BASE_REF" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
  ```

  `BASE_REF` names the intended pull-request base branch.
  Each guide MUST explain its value and use shell syntax that correctly expands it.
  Do not copy obsolete issue commands or manual test-file selection snippets.

- **FR-003**: Each guide MUST direct a fetch of the intended base into its remote-tracking reference.
  The reference MUST resolve before the check runs.
  The command MUST compare against that fetched reference.
  Do not assume `main` when the intended base differs.

- **FR-004**: Each guide MUST retain applicable checks before the local commit.
  It MUST require the test-quality check after a local commit and before push.
  The checked candidate MUST contain all intended tests and have no uncommitted changes to relevant inputs.
  If the candidate or base changes, repeat the affected checks.

- **FR-005**: Each guide MUST explain whether staged, unstaged, and untracked tests enter the installed command.
  Distinguish path selection from the file content that the analyzer reads.
  Do not claim that an uncommitted test passes the required committed-candidate check.
  Base these statements on the parent's verified analyzer evidence.

- **FR-006**: The documented base comparison MUST match the unchanged installed analyzer.
  Offline evidence MUST distinguish comparison of two revisions from a merge-base comparison.
  Do not substitute a manual file list or another comparison with different semantics.

- **FR-007**: Each guide MUST explain all four current full-suite trigger paths.
  The analyzer automatically handles the settings and baseline paths.
  CI supplies the other two paths explicitly.

  | Path | Source of the full-suite trigger |
  |------|----------------------------------|
  | `.github/test-quality-config.toml` | Automatic analyzer behavior |
  | `.github/test-quality-baseline.json` | Automatic analyzer behavior |
  | `.github/workflows/ci.yml` | Explicit CI `--full-gate-path` |
  | `requirements-dev.txt` | Explicit CI `--full-gate-path` |

- **FR-008**: Each guide MUST explain that push and manual CI runs scan the full suite.
  The full-suite local command MUST retain the same settings and baseline without `--changed-from`:

  ```text
  test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
  ```

- **FR-009**: Each guide MUST explain the installed analyzer's `gate_scope` output.
  That line prints only the file count and finding count.
  The file count measures discovered test files before parsing and exclusions.
  The finding count measures findings after rule filters, not only new findings.
  Scope selection and its reason appear in stderr logging, not fields on `gate_scope`.
  The JSON report lists `analyzed_files` when the run produces a report.
  Do not invent mode, reason, or changed-path fields on `gate_scope`.
  Do not treat zero counts as proof that every required input was readable.

- **FR-010**: Each guide MUST require a successful check with zero new findings before push.
  Existing accepted findings can remain in the unchanged baseline.
  A failed command, unknown base, unreadable input, or skipped check MUST block the local procedure.

- **FR-011**: A direct guardrail MUST read `.github/workflows/ci.yml` and all three named documents.
  It MUST obtain the command from job `test_quality_gate`, step `Run test quality ratchet`.
  It MUST parse the active fenced command in each named local section.
  It MUST check the executable name, `--gate`, settings, baseline, intended base comparison, and all live full-suite paths.
  It MUST reject absent commands, incorrect option values, conflicting duplicate options, and incorrect scope controls.
  Extra roots, disabled rules, and obsolete entry points MUST fail.
  Correct text outside the applicable local procedure MUST NOT satisfy the check.
  Equivalent static quoting, option order, RTK prefixes, and PowerShell continuation MUST preserve valid commands.
  Quoting that prevents the intended base variable from expanding is not equivalent.

- **FR-012**: The guardrail MUST report how many documents, required inputs, and scope paths it actually checked.
  Current successful counts are three documents, six input files, two explicit paths, and four effective trigger paths.
  The six inputs include the three guides, CI workflow, repository settings, and baseline.
  Its report MUST distinguish the two automatic paths from the two explicit paths.
  Count a completed file read separately from a completed validation.
  If an input fails, report completed checks and identify the failed input.

- **FR-013**: The guardrail MUST fail if any required guide, CI workflow, settings file, or baseline is missing, unreadable, or unusable.
  It MUST also fail if it cannot locate or interpret the required live command.
  It MUST NOT use a cached command, silently skip an input, or report an unsupported check as successful.
  The settings and baseline checks are required-input safety checks, not analyzer changes.
  The unchanged analyzer uses defaults for a missing or empty settings file.
  Unreadable or malformed settings cause an analyzer error.
  A missing or malformed baseline fails gate mode, including an empty changed-test scope.
  The guides MUST distinguish guardrail rejection from analyzer default behavior.

- **FR-014**: Positive and negative offline tests MUST execute the unchanged installed analyzer.
  Known findings in selected and excluded tests MUST prove actual scope.
  Assert the scope counts, relevant findings, and exit result against explicit fixture expectations.
  Measure parsed file counts and analyzed paths from installed logging and reports.
  If an early error prevents a count or report, identify that evidence as unavailable.
  Do not substitute an invented zero count.
  Text-only checks, fabricated analyzer output, or replacement selection logic cannot satisfy the behavioral proof.

- **FR-015**: Offline evidence MUST cover all 16 case groups below.
  Each group MUST include the applicable valid result and failure or exclusion result.
  The four trigger groups MUST each prove that an unchanged test enters full-suite scope.

  | Case | Required evidence |
  |------|-------------------|
  | T01 | Added and modified tests use recognized filename forms. Check `test_*.py`, `*_test.py`, and lookalike non-test names. |
  | T02 | Deleted tests produce the correct scope without an attempt to analyze a nonexistent test. |
  | T03 | Test renames preserve correct selection. Include test-to-test, test-to-non-test, and non-test-to-test names. |
  | T04 | Unrelated-only changes do not add unrelated tests to changed-test scope. Verify the valid empty result. |
  | T05 | A change to `.github/workflows/ci.yml` forces full-suite scope through the explicit control. |
  | T06 | A change to `requirements-dev.txt` forces full-suite scope through the explicit control. |
  | T07 | A change to `.github/test-quality-config.toml` automatically forces full-suite scope. |
  | T08 | A change to `.github/test-quality-baseline.json` automatically forces full-suite scope. |
  | T09 | The command without changed-scope controls scans the full suite, as push and manual CI runs do. |
  | T10 | Different valid bases and divergent history prove the exact installed comparison. The guidance states that same comparison. |
  | T11 | An unknown or unresolved base fails. An incorrect substitute base does not satisfy the documented procedure. |
  | T12 | Staged tests show their actual selection and analysis behavior before and after a local commit. |
  | T13 | Unstaged tests show their actual selection and analysis behavior, including edits to an already selected test. |
  | T14 | Untracked tests show their actual selection and analysis behavior before and after a local commit. |
  | T15 | The guardrail rejects each missing or unreadable required input. The analyzer uses defaults for missing or empty settings. Unreadable or malformed settings fail. Missing, unreadable, or malformed baselines fail, including zero selected tests. |
  | T16 | Command drift fails for each guide and each required control. A changed live CI control also causes failure. |

  Trigger evidence MUST include applicable additions, modifications, deletions, and renames.
  Command-drift evidence MUST include omitted paths, incorrect paths, an incorrect base, and an obsolete entry point.
  Include altered commands whose text appears similar but whose actual selection differs.

- **FR-016**: Do not add a pre-commit hook.
  Clear local instructions and direct guardrails satisfy this feature.
  Do not change hook configuration or add another automatic commit mechanism.

- **FR-017**: Do not change the analyzer, its installed implementation, repository settings, baseline, or workflows.
  Do not change `README.md`, application behavior, `CHANGELOG.md`, or another change's release fragment.
  This internal guidance change requires no release-note fragment.
  Guardrails and their tests MUST remain limited to this issue's command and scope contract.

### Key Entities

- **Local Guide**: One of the three named documents and its required local section.
- **Gate Contract**: The required command, settings path, baseline path, base comparison, and full-suite controls from live CI.
- **Base Reference**: The fetched intended base revision that the analyzer uses for changed-scope selection.
- **Scope Evidence**: A controlled case with known revisions, file states, expected findings, counts, and an observed exit result.
- **Guardrail Result**: A pass or failure with checked input counts, checked path counts, and specific errors.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All three local guides contain the complete required procedure.
  No guide omits a required command or scope control.
- **SC-002**: Three walkthroughs succeed, one for each guide.
  A maintainer selects the intended base and correct check sequence without another guide.
- **SC-003**: Every planned incorrect-command case and unreadable-input case produces a clear failure.
  No such case reports success or counts a skip as proof.
- **SC-004**: All 16 offline case groups produce their expected scope, counts, findings, and success or failure result.
  Evidence covers both inclusion and exclusion, not command text alone.
- **SC-005**: Each of the four trigger paths includes an unchanged test in the required full-suite check.
  The complete-suite procedure also includes that test without a trigger change.
- **SC-006**: Every successful guardrail run accounts for all three guides and every live scope path.
  The report gives exact counts and names any failed input.
- **SC-007**: The final candidate produces zero new findings before push.
  The change adds zero hooks and makes zero changes to excluded files or application behavior.

## Assumptions

### Scope and Dependencies

- The parent already read and claimed issue #3317.
  This feature uses that issue only.
  It does not create or claim another issue.
- Current CI defines the required command and explicit full-suite paths.
  The installed analyzer defines automatic triggers, filename recognition, comparison semantics, and printed scope counts.
- The parent verifies installed options and behavior in an isolated Python 3.13 environment before implementation.
  The parent initially verified CPython 3.13.13 and `misthelper-devtools` 0.5.2.
  The authorized rebase now uses incoming `misthelper-devtools` 0.6.0.
  `requirements-dev.txt` pins commit `b140350ebc40e61b57a3a65731c0df520f143661`.
  All 514 ratchet cases pass under that unchanged incoming pin.
  The parent verified the installed CLI options and read the installed implementation.
  The resolver uses `git diff --name-only --relative -z REVISION HEAD`, not a merge-base comparison.
  Only existing files with `test_*.py` or `*_test.py` names enter changed-test selection.
  Rename detection can name both paths, but only existing recognized files enter analysis.
  The parent observed a successful unchanged-commit check against `origin/main` with zero selected tests and zero new findings.
  The existing `tests/guardrails/test_quality_ratchet_files.py` passed all 14 tests.
  Broader selected commands failed because packages were missing.
  The parent restored both requirements files unchanged.
  Those facts do not prove the new 16-group behavioral matrix.
  Verification of external facts does not require a new feature decision.
- Offline cases use isolated local repositories and local base references.
  They require no network, credentials, production services, or changes to the real analyzer inputs.
- The parent owns implementation and final checks.
  Those checks include selected tests, compilation, Ruff, Black, types, links, STE, and the unchanged test-quality check.
  The parent owns the local commit with the Copilot co-author.
  It waits for the coordinator's full verified stable `main` SHA before the one push and pull request.
  Final delivery requires protected exact-head squash and exact-main proof.

### Specification Workflow Adaptation

- The specification phase created `spec.md` and `checklists/requirements.md` inside `specs/3317-local-test-quality-loop`.
  The planning phase can update those files and add issue-owned planning artifacts in the same directory.
  This session does not implement the guides, guardrail, or tests.
- The explicit feature directory replaces automatic numbering and branch-derived directory selection.
  Later commands must receive `SPECIFY_FEATURE_DIRECTORY=specs/3317-local-test-quality-loop` explicitly.
- The checked-in `.specify/templates/spec-template.md` defines the specification structure.
  The checked-in `.specify/templates/checklist-template.md` defines the checklist structure.
  The checked-in `.specify/templates/plan-template.md` defines the planning structure.
  Direct template use replaces the normal template-resolution and PowerShell scripts because PowerShell is unavailable.
- This session does not write `.specify/feature.json` or another shared feature record.
  The explicit path above supplies the feature context.
- Pre-hook `speckit.git.feature` does not run.
  The user forbids branch creation, branch changes, and Git settings changes in this reserved worktree.
  The existing app-managed branch remains unchanged.
- Optional post-hook `speckit.git.commit` does not run.
  The user does not authorize a commit, push, or pull request in this session.
- Post-hook `speckit.companion.after-specify` is unavailable.
  Registration exists, but the local companion command and script files are absent.
  This session does not claim hook execution or create a replacement context record.
- The same absence prevents post-hook `speckit.companion.after-plan`.
  Planning must report that limitation without claiming hook completion.
- The planning session does not run `update-agent-context.ps1`.
  That script updates global agent files outside this session's write boundary.
- The planning session uses direct research and starts no additional agents.
- All file writes use `apply_patch`.
  Repository inspection and validation use RTK.
  Prose uses the repository STE writing guide.
  This session starts no additional agents.
