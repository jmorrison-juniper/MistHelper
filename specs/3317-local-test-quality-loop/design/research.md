# Research: Local Test-Quality Loop

**Date**: 2026-09-30

**Specification**: [spec.md](../spec.md)

**Status**: Research, implementation, and local validation are complete. The committed comparison and delivery remain pending.

## Sources and Evidence Limits

Read these local sources:

- `.github/workflows/ci.yml`, job `test_quality_gate`, step `Run test quality ratchet`
- The three required guide sections
- `tests/guardrails/test_quality_ratchet_files.py`
- `.github/test-quality-config.toml` and the baseline's JSON shape
- `requirements-dev.txt`, `pyproject.toml`, and `.ste-linter.toml`
- `.specify/memory/constitution.md` and the checked-in planning template
- Installed analyzer CLI help and read-only package sources

Installed source inspection covered `changed_scope.py`, `config.py`, `discovery.py`, `__main__.py`, reporting, and the weak-assertion detector.
The parent supplied the verified package pin, interpreter version, empty-scope run, and existing 14-test result.
This session did not rerun those behavioral checks.

The parent reported missing packages in broader selected commands.
Both requirements files remain unchanged.
This session creates no environment and installs no package.

No new guardrail or fixture test ran.
The planned T01-T16 cases must supply that evidence during implementation.
No agent or external research service ran.
The installed STE CLI accepts explicit files, not directory targets.
It read all nine planning files without the configured dictionary.
The missing `data/ste_dictionary.json` limits vocabulary coverage.
That partial review does not prove a complete dictionary-backed STE check.

## R01: Use the Installed CLI and Exact Pin

**Decision**: Use `test-quality-analyzer` from `misthelper-devtools` 0.5.2.
Retain commit `0b969be7f60599f9a19ebc3069161f9353a1d830`.

**Rationale**: Current CI installs that pinned package.
The installed CLI exposes every required scope control.
The package already owns selection and gate behavior.

**Alternatives considered**:

- Reject the obsolete repository `tools.test_quality_analyzer` entry point.
- Reject a new local analyzer implementation.
- Reject dependency or pin changes for this guidance issue.

## R02: Compare Two Revision Endpoints

**Decision**: Document `git diff --name-only --relative -z REVISION HEAD`.
Keep the installed `--changed-from` control.

**Rationale**: `ChangedScopeResolver` uses that exact comparison.
A divergent-history fixture distinguishes it from merge-base selection.
Staged, unstaged, and untracked-only paths do not enter this revision comparison.

Selected files must exist and match `test_*.py` or `*_test.py`.
The analyzer reads their current working-tree content.
A clean local commit before push therefore supplies the intended CI candidate.
CI explicitly checks out the pull-request head commit for this job.

**Alternatives considered**:

- Reject triple-dot selection because it changes the comparison.
- Reject index or working-tree path selection because the installed command does not use it.
- Reject a manual file list because it duplicates selection and misses automatic triggers.

## R03: Keep the Check After the Local Commit

**Decision**: Retain applicable checks before commit.
Require this analyzer check after the local commit and before push.
Fetch the intended base into its matching remote-tracking reference first.

**Rationale**: An index-only change cannot prove committed path selection.
An already selected file can still contain uncommitted content.
The required candidate therefore needs committed intended tests and clean relevant inputs.

**Alternatives considered**:

- Reject a pre-commit hook because it cannot change the installed committed-tree comparison.
- Reject an unfetched or substituted `origin/main` when the intended base differs.
- Reject reuse of results after the candidate or intended base changes.

## R04: Derive Controls From Live CI

**Decision**: Parse the named job and step with PyYAML.
Decode its empty scope, pull-request scope array, and analyzer invocation without shell execution.
Derive each explicit `--full-gate-path` from that live scope.

**Rationale**: Current CI supplies `.github/workflows/ci.yml` and `requirements-dev.txt`.
Config and baseline arguments supply the two automatic triggers.
A future added CI control must make outdated guides fail.

The existing ratchet guard contains a cached path constant.
Leave that file unchanged.
Do not import its constant as the new guard's expected path list.

**Alternatives considered**:

- Reject whole-file string search because comments and stale examples can satisfy it.
- Reject a second cached trigger list because both copies can drift.
- Reject shell execution of CI text because parsing needs no executable input.

## R05: Parse Active Local Commands Semantically

**Decision**: Inspect fenced shell blocks inside each exact named section.
Normalize supported RTK prefixes, harmless static quoting, option order, and shell continuations.
Preserve base-variable expansion and scope meaning.

**Rationale**: A token or string match cannot distinguish an active command from a comment.
Removing quotes without expansion checks can accept an incorrect literal base.
A narrow shell grammar is sufficient for these three procedures.

Require one scoped command and one full-suite command in each active procedure.
Reject omitted controls, wrong values, conflicting duplicates, extra roots, disabled rules, and obsolete entry points.
Reject unknown execution forms instead of assuming equivalence.

**Alternatives considered**:

- Reject raw substring matching.
- Reject a general shell evaluator.
- Reject independent copied command expectations in each test.

## R06: Read and Account for All Six Inputs

**Decision**: Read the three guides, CI workflow, repository settings, and baseline directly.
Count completed reads and completed validations separately.
Give every failed input a named error and a measured partial result.

**Rationale**: Four files cover only the guides and CI.
Settings and baseline preflight add two tightly coupled safety inputs.
A successful run therefore reads six files, including three guide documents.
Input failures must not disappear behind a zero-test gate result.

Missing settings fail the new guard's read preflight.
The analyzer alone intentionally uses defaults for missing or empty settings.
Readable empty TOML retains that documented default behavior.
The existing ratchet tests separately enforce the repository settings structure.

Unreadable or malformed settings cause analyzer errors.
Missing, unreadable, or malformed baselines fail gate mode, including zero selected tests.
Do not change `ConfigLoader` or any repository analyzer input.

**Alternatives considered**:

- Reject a claimed analyzer failure for missing settings.
- Reject a hard-coded four-input success message.
- Reject silent skips or a successful result after a failed read.

## R07: Keep Output Counts Distinct

**Decision**: Explain only these `gate_scope` fields:

- Discovered test file count, before parsing and exclusions
- Finding count after rule filters

Use stderr selection logging for the comparison and trigger reason.
Use `analyzed_files` in installed JSON reports for analyzed path sets.
Use parsed-file logging and completed detector traces for additional measured evidence.

**Rationale**: The CLI does not print mode or reason fields on `gate_scope`.
Finding counts are not counts of new findings.
Selected, discovered, parsed, and analyzed paths can differ.
The current CI comment does not establish additional printed fields.
Leave that workflow unchanged and document verified CLI behavior.

A valid empty scope prints zero counts and validates its baseline.
That early return does not write a JSON report.
An early input error can produce neither a scope line nor a report.
Record absent evidence as unavailable, not as a fabricated zero.

**Alternatives considered**:

- Reject invented `gate_scope` fields.
- Reject using only an exit result as scope proof.
- Reject reusing a previous invocation's report.

## R08: Use Real Offline Analyzer Fixtures

**Decision**: Create small local Git repositories through class-based test support.
Run the installed analyzer in a fresh subprocess for each observation.
Use the active interpreter's installed module entry point for portable subprocess execution.

The subprocess form is `python -B -m misthelper_devtools.test_quality_analyzer`.
It executes the unchanged installed CLI implementation.
Guide commands still use the required `test-quality-analyzer` executable name.

**Rationale**: Real Git history and known weak assertions prove selection.
Separate report paths prevent stale output from satisfying a later case.
Fresh processes prevent detector state from leaking between observations.

Use `weak_is_not_none` as a known finding identity.
Its settings control name is `weak_assert_not_none`.
Those names are not interchangeable.
Keep fixture template lines stable and fixture baselines local.

The initial minimal full-mode fixture produced two discovered files, two parsed files, and one finding.
It returned exit 2 because a full scan requires applicable scope for each detector.
The fixture now contains a local JSON subject with numeric, empty-input, and malformed-input coverage.
Those real source signatures provide the required detector scope without disabling rules.
The intentional weak assertion remains on line 3.
The ordinary full scan still analyzes two test files and finds one weak identity.

**Alternatives considered**:

- Reject fabricated CLI output or replacement selection logic.
- Reject network-dependent fixtures.
- Reject shared baseline edits or line-number shifts.
- Reject importing MistHelper product modules into simple analyzer witnesses.

## R09: Keep New Code in Five Files

**Decision**: Use `tests/guardrails/local_test_quality_loop/` with five direct files.
Use `guard.py`, `fixtures.py`, two test modules, and `__init__.py`.
Keep each new class and method within the project limits.

**Rationale**: The existing guardrail parent has 38 tracked children.
One nested package limits further parent growth.
The plan records the strict parent-child variance instead of hiding it.

**Alternatives considered**:

- Reject several new flat test files.
- Reject expansion of another issue's existing guard.
- Reject unrelated parent-directory restructuring.
- Reject new shared fixtures or wrapper entry points.

## R10: Adapt Planning Without Shared Writes

**Decision**: Read checked-in templates directly and write only issue-owned artifacts.
Place ancillary design artifacts under `design/`.
Skip optional Git hooks and the global agent-context update.

**Rationale**: PowerShell is absent.
The user prohibits branch changes, commits, agents, and shared context writes.
The companion hook is registered but its command and scripts are absent.

The feature root remains within five children.
No replacement companion state record is created.
No release-note fragment is required for internal-only guidance.

**Alternatives considered**:

- Reject invoking Git hooks without authorization.
- Reject installing tools or creating an environment in this session.
- Reject claiming mandatory companion execution.
- Reject adding a sixth feature-root child for each ancillary artifact.

## Local Proof Update

The implementation completed all T01-T16 groups through direct guard decisions and unchanged analyzer subprocesses.
The scope module passed 82 cases with 124 real invocations.
The guidance module passed 397 cases, including the actual live preflight.
The combined suite retained the existing 14 ratchet tests and passed all 493 cases.
No required case skipped.

Literal-preservation tests exposed nine false approvals before the parser correction.
The corrected parser preserves fenced HTML text and quote operators.
It rejects ambiguous concatenation instead of assuming PowerShell has Bash semantics.
All 12 targeted literal cases then passed.
Only plain CLI and `rtk proxy` forms have accepted prefix coverage.

Incoming trigger renames retain fixture-local rename detection.
Outgoing trigger-removal cases set fixture-local `diff.renames=false` to expose the old path.
Recognized test-name rename cases retain `diff.renames=true`.
The guard and guides now state the actual path-difference requirement.
No real repository or global Git setting changed.

The preliminary configured-input analyzer used explicit roots for both new test files.
It returned exit 0 with two checked files, zero findings, and zero new findings.
That result does not establish committed CI scope before the parent's local commit.
PowerShell, native Windows command execution, and dictionary-backed STE vocabulary coverage remain unavailable.
