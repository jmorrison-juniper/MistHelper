# Quickstart Validation: Local Test-Quality Loop

**Specification**: [spec.md](../spec.md)

**Plan**: [plan.md](../plan.md)

## Scope and Current Status

The new package and three guide edits now exist.
This guide separates completed local proof from the parent's final candidate validation.
Run the applicable parent checks again before delivery.

The parent verified these existing facts:

- CPython 3.13.13.
- `misthelper-devtools` 0.5.2 at commit `0b969be7f60599f9a19ebc3069161f9353a1d830`.
- Installed CLI support for the required controls.
- A valid unchanged-commit comparison against `origin/main` with zero selected tests and zero new findings.
- All 14 existing `tests/guardrails/test_quality_ratchet_files.py` tests passed.

Broader selected commands failed because packages were missing.
The parent restored both requirements files unchanged.
The parent then restored the isolated environment before implementation.
The completed local proof below now covers the new guardrail and T01-T16 matrix.

### Initial implementation proof

All commands used RTK and this worktree's `.venv/bin/python`.
The implementation agent used no nested agents or real-repository delivery actions.

| Check | Actual result |
|-------|---------------|
| Input accounting | 24 red failures, then 24 passed |
| Guidance fixtures | 396 passed with only the live class excluded |
| Actual live preflight | Red with 6 reads and 3 validations, then green with 6 reads and 6 validations |
| Scope module | 82 passed with 124 real installed analyzer invocations |
| New and existing ratchet guards | 493 passed, including the existing 14 tests, 0 skipped |
| Affected document guards | 142 passed, 0 skipped |
| Semantic compilation | 5 new Python files passed without bytecode output |
| Source limits | All methods, parameters, and class children passed |
| Scoped Ruff and Black | Passed |
| Explicit-file mypy | No issues in 5 source files |
| Installed STE | All 8 implementation files met the 80-point threshold, dictionary coverage skipped |
| Preliminary analyzer with `--roots` | 2 new files checked, 0 findings, 0 new findings, exit 0 |

The preliminary analyzer used unchanged repository settings and baseline.
Its reports stayed in a disposable temporary directory.
Its two omitted-root records identify unmeasured repository roots.
It does not prove configured committed CI scope.
Only the parent's clean local commit and intended-base check can supply that proof.

Outgoing trigger-removal tests use fixture-local `diff.renames=false`.
Incoming and recognized test-name renames retain detection.
These cases distinguish actual endpoint path names without changing real Git configuration.
Native PowerShell execution remains unavailable.
The required PowerShell prerequisite attempt failed because `pwsh` is absent.
The mandatory `speckit.companion.after-implement` dispatch failed with `No such file or directory`.
No companion hook or replacement journal ran.
Both optional commit hooks remained unauthorized and did not run.

### Final parent validation

The parent added 21 cases for incorrect shell-specific base assignments.
All 21 cases failed before the guard correction and passed afterward.
The correction preserves the shell profile before tokenization removes quotes.

| Check | Actual result |
|-------|---------------|
| New and existing ratchet guards | 514 passed, 0 skipped |
| Guard and fixture coverage | 98.22 percent across 841 statements |
| Document and link guards | 161 passed, 1 existing pull-request-only skip |
| Global Ruff | Passed |
| Global Black | 1,890 files unchanged |
| Compilation | Entrypoint and all five package files passed |
| CI type scope | No issues in 608 source files |
| Explicit package types | No issues in five source files |
| Markdown links | 13 files checked, no broken links |
| Package structure | Five files and 136 functions checked, no limit failures |
| Installed STE | Eight implementation files passed, dictionary coverage unavailable |
| Configured full-suite ratchet | 949 files, 725 findings, zero new findings |
| Repository Bandit | Passed with no new exclusion |
| UV-resolved runtime audit | No known vulnerabilities |

The direct `pip-audit -r requirements.txt` command failed during its temporary `ensurepip` creation on macOS.
The parent resolved the unchanged runtime requirements with UV.
It audited the complete pinned result with `pip-audit --disable-pip --no-deps`.
No dependency manifest changed.
The existing changelog diff test skips without a pull-request event.
No new guard or required offline case skips.
The committed intended-base check follows the local commit.
Publication still requires the coordinator's stable-main permission.

### Authorized-base validation

The coordinator supplied `856e5065413d3026f9c0f6d5222d9d379ec79d8b` after its protected bootstrap merge and exact-main proof.
The local feature rebased onto that exact revision without conflicts.
The unchanged incoming requirements now install devtools 0.6.0 at `b140350ebc40e61b57a3a65731c0df520f143661`.

| Repeated check | Actual result |
|----------------|---------------|
| New and existing ratchet cases | 514 passed, no skips |
| Guard and fixture coverage | 98.22 percent |
| Required input guard | Six inputs, three guides, four effective paths |
| Committed CI-equivalent ratchet | Two files, zero findings, zero new findings |
| Configured full-suite ratchet | 994 files, 725 findings, zero new findings |
| Global Ruff and Black | Passed, 2,005 files unchanged |
| CI type scope | 663 files passed |
| Explicit package types | Five files passed |
| Changed Markdown links | 13 files, no broken links |
| Document and link guards | 161 passed, one existing pull-request-only skip |
| Complete hashed runtime audit | 105 packages, no known vulnerabilities |
| Bandit and writing structure | Passed |

The writing dictionary and native PowerShell remain unavailable.
The required checks repeat after the local evidence commit and before push.
Publication, the protected merge, and exact-main proof remain under the released coordinator sequence.

## Prerequisites

1. Use an existing activated Python 3.13 or newer environment.
2. Confirm that it contains the pinned devtools package, pytest, and PyYAML.
3. Confirm that Git and RTK are available.
4. Complete parent-owned environment repairs before claiming a test result.
5. Provide the configured STE dictionary before claiming complete vocabulary coverage.

Use unchanged requirements for any parent-owned installation.
Do not add dependencies or recreate the environment in this planning session.
Scope fixtures need no network, token, Mist service, or container.
The configured `data/ste_dictionary.json` is absent in this planning environment.
The installed STE linter can read files without it, but its vocabulary coverage remains partial.

Run validation commands from the repository root.
Use the current workspace only.
No command in this artifact authorizes branch changes or delivery from the planning session.

## 1. Confirm Installed Tools

```powershell
rtk proxy python -B --version
rtk proxy test-quality-analyzer --help
rtk proxy ste-linter --help
```

Expect the installed analyzer's required gate and scope options.
Do not use an obsolete repository analyzer module.
The parent retains the exact package pin.

## 2. Prove the Direct Guard Can Fail

Before the guide edits, run the new live-guide class:

```powershell
rtk proxy python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

Expect a failure that identifies missing active procedures in the current guides.
The report must show actual completed input reads and validations.
Do not create a bad commit or start a workflow for this proof.

After the guide edits, repeat the same command.
Expect all three active procedures to match the named live CI step.
The current successful report reads six inputs, including three guide documents.
It decodes two explicit paths and two automatic paths.
The effective trigger set contains four distinct paths.

Also run the mutation tests:

```powershell
rtk proxy python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py
```

Expect positive normalization cases and negative drift cases to pass their explicit assertions.
Each negative case must observe a guard failure, not a skip.
Use [guardrail.md](contracts/guardrail.md) for exact report definitions.

## 3. Run the Offline Behavioral Matrix

```powershell
rtk proxy python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_scope.py
```

Expect the unchanged installed analyzer to run inside temporary local Git fixtures.
Every invocation uses fixture-local settings, baseline, and unique output paths.
The real repository settings and baseline remain unchanged.

Account for T01-T16 across the scope and guidance test modules.
Use [validation-matrix.md](validation-matrix.md) for each group and variant.
Use [data-model.md](data-model.md) for the evidence records.

For each available scan, inspect parsed counts and exact analyzed paths.
Confirm known weak findings in included tests and their absence from excluded tests.
For early errors, expect named failures and explicitly unavailable evidence fields.
For valid empty scope, expect zero scope counts and no report.

An expected analyzer exit 1 or 2 can produce a passing pytest case.
The test must assert that exit and its required evidence.
An unexpected result must fail.

## 4. Retain the Existing Ratchet Proof

```powershell
rtk proxy python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop tests/guardrails/test_quality_ratchet_files.py
```

Expect the existing 14 ratchet tests and all new cases to pass.
Do not assert a fixed total pytest count for parametrized new cases.
Record actual collected, passed, failed, and skipped counts.
Any missing required group or skipped required case blocks completion.

## 5. Check the Changed Files

Run the parent's applicable compile, Ruff, Black, type, link, and STE checks.
Keep every new Python method within 25 lines and five parameters.
Keep new package, module, and class children within five items.
Review ASCII logging and purpose comments.

Example scoped checks after implementation:

```powershell
rtk proxy python -m ruff check tests/guardrails/local_test_quality_loop
rtk proxy python -m black --check tests/guardrails/local_test_quality_loop
rtk proxy python -m mypy tests/guardrails/local_test_quality_loop --config-file pyproject.toml
```

The STE CLI requires explicit files, not directory targets.
Select the five package files with the guide files:

```powershell
$STE_FILES = @(".github/copilot-instructions.md", "agents.md", ".github/instructions/git-flow-multi-agent.instructions.md")
$STE_FILES += (Get-ChildItem tests/guardrails/local_test_quality_loop -Filter *.py -File).FullName
rtk proxy ste-linter --min-score 80 @STE_FILES
```

Use the parent-owned selected-path compile and link checks.
Do not claim that these commands ran during planning.
Keep all excluded application, analyzer, workflow, baseline, and release files unchanged.

## 6. Validate the Clean Local Commit Before Push

Run existing applicable checks before the parent's local commit.
Commit all intended tests and relevant inputs through the parent's authorized process.
Then confirm the intended candidate is clean:

```powershell
rtk git status --short
```

If relevant staged, unstaged, or untracked changes remain, stop.
Selection compares committed path differences between the intended base and `HEAD`.
The analyzer then reads selected files from current working-tree content.
Do not treat an uncommitted test as committed-candidate evidence.

Set and fetch the intended base:

```powershell
$BASE_REF = "main" # Replace this value when the intended base differs.
rtk proxy git fetch --no-tags origin "+refs/heads/${BASE_REF}:refs/remotes/origin/${BASE_REF}"
rtk proxy git rev-parse --verify "origin/${BASE_REF}^{commit}"
```

If the fetch or resolution fails, stop.
Do not substitute a different valid reference.

Run the required-input preflight:

```powershell
rtk proxy python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

If the guard fails, stop before the analyzer.
This preflight rejects a missing repository settings file.
The analyzer alone uses defaults for missing or empty settings.

Run the installed scoped command:

```powershell
rtk proxy test-quality-analyzer --gate `
  --config .github/test-quality-config.toml `
  --baseline .github/test-quality-baseline.json `
  --changed-from "origin/$BASE_REF" `
  --full-gate-path .github/workflows/ci.yml `
  --full-gate-path requirements-dev.txt
```

Expect exit 0 and `gate: 0 new findings vs baseline`.
The file count depends on the actual committed candidate.
Zero file counts alone do not prove correct base choice or readable required settings.
Read stderr selection messages and the guard's separate input report.

If the candidate, working-tree content, or fetched base changes, repeat the affected checks.
The parent owns any later push, pull request, merge, and delivery.

## 7. Validate Full-Suite Behavior

Use the same preflight before the full-suite command:

```powershell
rtk proxy test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

This command matches push and manual CI scope.
It scans every discovered test root without changed-scope controls.
Keep the same settings and baseline.
Require zero new findings.
Do not update the baseline to avoid this feature's criteria.

Each guide must also explain all four committed-change triggers.
The settings and baseline are automatic triggers.
The workflow and development requirements are explicit live CI triggers.
See [local-commands.md](contracts/local-commands.md) for the complete path and output definitions.

## Completion Evidence

The parent records:

- Exact implemented file set and named section boundaries.
- Measured positive and negative guard results.
- T01-T16 case results with parsed and analyzed-path evidence.
- Existing ratchet test result and actual new pytest counts.
- Applicable local gate results and any environment limitation.
- Clean candidate revision, intended fetched base revision, and final zero-new-finding result.

T038-T040 passed final parent validation.
The parent must receive a full verified stable `main` SHA from coordinator `6d71fd26-57c2-48c0-abc8-607af98f75d0`.
The parent must wait for that message before any push or pull request.
No local observation or shortened SHA replaces that permission.
No skipped check counts as proof.
No new hook, dependency, release fragment, or shared state record belongs to this feature.
