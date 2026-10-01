# Implementation Plan: Local Test-Quality Loop

**Branch**: `jmorrison-juniper-local-test-quality-guidance` | **Date**: 2026-09-30 | **Spec**: [spec.md](spec.md)

**Input**: `specs/3317-local-test-quality-loop/spec.md`

**Feature selection**: `SPECIFY_FEATURE_DIRECTORY=specs/3317-local-test-quality-loop`

**Template**: `.specify/templates/plan-template.md`, read directly.

## Summary

Add the required local test-quality procedure to three existing sections.
Add one issue-owned guardrail package that compares those procedures with live CI.
Prove the unchanged installed analyzer's behavior in isolated local Git fixtures.
Do not change the analyzer, settings, baseline, CI, hooks, or application.

The planning phase produced these design artifacts.
The bounded local implementation and offline tests now exist.
The parent retains final relevant validation, the clean candidate commit, and delivery.
See [quickstart.md](design/quickstart.md) for measured local proof and remaining parent work.

## Technical Context

**Language/Version**: Python 3.13 or newer. The parent verified CPython 3.13.13.

**Primary Dependencies**: Existing pytest, PyYAML, and `misthelper-devtools` 0.6.0.
Use standard-library `pathlib`, `shlex`, `json`, `tomllib`, `logging`, and `subprocess`.
Add no dependency.

**Installed Tool Pin**: `requirements-dev.txt` pins `b140350ebc40e61b57a3a65731c0df520f143661`.
Use the installed `test-quality-analyzer`, not an old repository module.

**Storage**: Six read-only repository inputs and transient fixture files.
Each analyzer invocation writes reports inside its isolated fixture.
No application store, shared baseline, or production data changes.

**Testing**: Existing pytest discovery accepts `test_*.py` and `*_test.py`.
Use class-based tests, `tmp_path`, real analyzer subprocesses, and explicit case expectations.
The parent reported 14 passing tests in `tests/guardrails/test_quality_ratchet_files.py`.
The new T01-T16 matrix passes.
The quickstart records its measured results.

**Target Platform**: Windows PowerShell guidance with portable Python guardrails.
Support Bash equivalents and RTK command prefixes in contract tests.
This planning session runs on macOS without PowerShell.

**Project Type**: Internal development guidance and direct pytest guardrails.
No new application interface or network service.

**Performance Goals**: Read each required input once per guard run.
Bound each fixture analyzer subprocess to 30 seconds.
Use small local repositories, not repeated full scans of MistHelper.
These are design bounds, not measured performance results.

**Constraints**: Planning writes stayed inside this feature directory.
Implementation touches only the three named sections and the five new package files.
Keep new methods within 25 lines and five parameters.
Keep each new module and class within the five-item limits.
Use meaningful ASCII logging and concise purpose comments.
Do not create wrapper functions.

**Scale/Scope**: Three guides, six required input files, and 16 behavioral case groups.
Current CI supplies two explicit trigger paths.
Settings and baseline add two automatic trigger paths.
Measure counts from actual reads and decoded controls.

**Resolved Questions**: [research.md](design/research.md) resolves the comparison, command parsing, input safety, output counts, and fixture design.
No unresolved clarification remains.

## Constitution Check

*Evaluate these gates before research and after design.*

| Gate | Before research | After design | Evidence or disposition |
|------|-----------------|--------------|-------------------------|
| I. New hierarchy limits | Justified variance | Justified variance | Feature root has five children. The new guardrail package has five direct files. One parent-child variance appears below. |
| II. Classes and no wrappers | Pass | Pass | Parsing, input accounting, fixture support, and tests use named classes. No new entry-point wrapper is needed. |
| III. Input safety | Pass | Pass | Read required files directly. Reject unreadable inputs and unsupported commands. Never execute document or CI text. |
| IV. Deployment pipeline | Parent-owned | Parent-owned | Local implementation and validation are complete. The parent retains the candidate commit and gated delivery steps. |
| V. Observability | Pass by design | Pass by design | Count completed reads, validations, paths, and analyzer observations. Never convert unavailable evidence into zero. |
| VI. Inline comments | Not applicable yet | Required for implementation | Add short purpose comments to executable Python lines. Do not copy implementation bodies into these artifacts. |
| VII. Action logging | Pass by design | Pass by design | Log before meaningful reads, parsing, comparisons, fixture mutations, and analyzer runs. Log measured results afterward. |
| Technology and paths | Pass | Pass | Use Python 3.13+, existing dependencies, and `Path`. Keep fixture inputs and reports local. |
| Release notes | Justified variance | Justified variance | FR-017 excludes fragments for this internal-only guidance change. No customer or application behavior changes. |
| Scope and ownership | Pass | Pass | No branch changes, commits, pushes, issues, pull requests, workflows, agents, or shared context writes occur here. |

### Existing structural debt

Read-only `git ls-files` measurements found these tracked direct-child counts:

| Parent | Existing children | Planned effect |
|--------|-------------------|----------------|
| Repository root | 48 | No new direct child |
| `tests/` | 38 | No new direct child |
| `tests/guardrails/` | 38 | One new nested package, giving 39 children |
| `specs/` | 737 | The requested feature directory already exists. Planning adds no sibling. |
| `.github/` | 15 | Edit an existing guide during implementation only |
| `.github/instructions/` | 4 | Edit an existing guide during implementation only |

These counts exclude ignored runtime caches.
Do not claim that the new package leaves the guardrail parent's count unchanged.
Its five-file child structure contains the new work.

Separate remediation can group existing guardrail files by contract under compliant packages.
That work needs its own ownership, migration checks, and existing-test proof.
It is not an implementation task for issue #3317.
This session does not create another issue.

## Project Structure

### Documentation for this feature

```text
specs/3317-local-test-quality-loop/
|-- spec.md
|-- plan.md
|-- tasks.md
|-- checklists/
|   `-- requirements.md
`-- design/
    |-- data-model.md
    |-- quickstart.md
    |-- validation-matrix.md
    |-- research.md
    `-- contracts/
        |-- local-commands.md
        `-- guardrail.md
```

The feature root has five children.
The design directory has five children.
Its contracts directory has two children.
Task generation moves the issue-owned research to `design/research.md`.
The root-level `tasks.md` uses the checked-in task template.
These paths preserve both directory limits.

### Future implementation files

```text
.github/copilot-instructions.md
    section: Validate locally, then push once
agents.md
    section: Local Development Quick Reference
.github/instructions/git-flow-multi-agent.instructions.md
    section: Part 3 / The local-first loop
tests/guardrails/local_test_quality_loop/
|-- __init__.py
|-- guard.py
|-- fixtures.py
|-- test_guidance.py
`-- test_scope.py
```

**Structure Decision**: Keep all new guardrail code in one small nested package.
Keep test-support classes there instead of adding a sixth file or a shared fixture.
Leave the existing 14-test ratchet file unchanged.
Edit only the named local sections in the three guides.

## Phase 0: Research

Research uses local sources and the parent's verified facts.
No research agent or external service runs.

The accepted comparison is `git diff --name-only --relative -z REVISION HEAD`.
It uses two revision endpoints.
It does not select staged, unstaged, or untracked-only paths.
The analyzer then reads existing selected files from the current working tree.

The accepted CI source is job `test_quality_gate`, step `Run test quality ratchet`.
Expand its pull-request scope array without executing its shell script.
Keep its empty scope for push and manual runs.
Derive explicit trigger paths from that live step.
Do not import the existing guard's cached `FULL_GATE_PATHS` constant.

The accepted safety check reads all six required files.
A missing settings file fails the guard even though the analyzer alone uses defaults.
A readable empty settings file retains the analyzer's documented default behavior.
An unreadable or malformed settings file fails.
The baseline must remain valid even when zero tests enter scope.

The accepted output contract contains two `gate_scope` counts only.
Use stderr for selection explanations.
Use installed JSON reports and detector logs for actual analyzed-path evidence.

## Phase 1: Design and Contracts

### Guardrail design

Use at most five responsibility classes in `guard.py`:

| Class | Responsibility |
|-------|----------------|
| `InputLedger` | Read inputs, record successful reads and validations, and preserve named errors. |
| `SectionCommands` | Locate exact headings, select active fenced commands, and handle continuations and comments. |
| `CommandControls` | Decode supported tokens, preserve expansion meaning, and reject conflicting or unsafe controls. |
| `CiGateContract` | Read the named live job and step, then derive scoped and full-suite commands. |
| `GuideGuard` | Compare the three procedures with the live contract and report measured results. |

Use pytest test classes as the direct invocation surface.
Do not add a standalone CLI, wrapper function, dependency, or shared `conftest.py`.
Avoid extra module constants when five responsibility classes already fill that module's limit.
Keep logger access and grouped contract values inside those responsibilities.

The parser supports a narrow, documented command grammar.
It is not a general shell interpreter.
It must preserve variable expansion when it removes harmless quotes.
Static single quotes can be harmless.
Single quotes around `origin/$BASE_REF` are not harmless.

Read all available required inputs even when one independent read fails.
Continue only safe checks whose inputs exist.
Report completed progress on failure.
Count distinct live path controls separately from repeated comparisons across guides.

See [guardrail.md](design/contracts/guardrail.md) for parsing and reporting rules.
See [data-model.md](design/data-model.md) for transient records.

### Local procedure design

Retain existing checks before the local commit.
Place the required analyzer check after the local commit and before push.
Require a clean intended candidate and a fetched, resolved intended base.
Repeat affected checks after any candidate or base change.

Each guide contains both complete commands.
Each guide explains the working-tree content distinction and all four full-suite triggers.
Each guide explains both `gate_scope` counts and the separate stderr selection messages.
The guard's settings preflight prevents the documented procedure from accepting a missing repository settings file.

See [local-commands.md](design/contracts/local-commands.md) for copyable command forms.
No pre-commit hook can replace this committed-revision comparison.
The analyzer's supported selection does not inspect the index or untracked-only paths.

### Offline evidence design

Use real installed analyzer subprocesses inside isolated local Git repositories.
Pass fixture-local settings, baselines, reports, and summaries.
Derive additional trigger controls from live CI.
Use known `weak_is_not_none` findings and strong controls to prove scope.

Assert exact path sets, parsed counts, finding identities, and exit results.
Use local baseline records only when a case tests accepted findings.
Do not modify shared baseline lines.
Do not treat skips as passing evidence.

See [validation-matrix.md](design/validation-matrix.md) for all 16 groups.
See [quickstart.md](design/quickstart.md) for the parent's validation procedure.

## Phase 2: Bounded Implementation Handoff

This table is the planning handoff, not a completed implementation checklist.
Every write listed here belongs to the parent's implementation phase.

| Task | Depends on | Write boundary | Required result |
|------|------------|----------------|-----------------|
| I01: Add input and command guard classes | None | `__init__.py`, `guard.py` | Six-input preflight, live CI decoding, active-section parsing, and measured failure reports |
| I02: Prove guidance guard decisions | I01 | `test_guidance.py` | Positive normalization cases and negative T15/T16 mutations, including each guide and each control |
| I03: Add isolated fixture support | I01 | `fixtures.py` | Local history, installed analyzer subprocesses, unique outputs, and exact observation records |
| I04: Prove changed-scope behavior | I03 | `test_scope.py` | T01-T04 and T10-T14 inclusion, exclusion, endpoint history, and working-tree evidence |
| I05: Prove triggers and input behavior | I02, I04 | `test_scope.py` | T05-T09 and T15, including all applicable trigger forms and settings-default behavior |
| I06: Update the three local procedures | I02, I05 | Three named guide sections only | Complete commands, base fetch, committed-candidate sequence, full-suite explanation, and count definitions |
| I07: Validate the final candidate | I04, I05, I06 | No new implementation file | All applicable local gates, exact allowed diff, and unchanged analyzer/config/baseline/CI proof |

I02 must demonstrate the guard's rejection before I06 repairs the guides.
A direct local red run is sufficient.
Do not create a temporary bad commit or start CI to obtain that proof.

The parent must resolve environment gaps before it claims complete validation.
The earlier successful empty-scope run does not prove the new tests.
After the parent's clean local commit, repeat the unchanged installed analyzer against the intended fetched base.
Require zero new findings before the parent proceeds with its authorized delivery.

## Workflow Adaptations and Hook Status

- Use the explicit feature directory, not `.specify/feature.json`.
- Use the checked-in planning template because PowerShell is absent.
- Do not run setup or agent-context scripts that require unavailable tooling or forbidden writes.
- Do not update `CLAUDE.md`, global agent context, or shared feature records.
- Do not create, switch, or rename a branch.
- Do not run optional Git commit hooks or branch hooks.
- The registered `speckit.companion.after-plan` command and script files are absent.
  The mandatory companion hook cannot run.
  The registered dispatch attempt failed with `No such file or directory`.
  No companion hook executed.
  Do not claim that it ran or create a replacement `.spec-context.json`.
- Recheck `hooks.after_plan` before the completion report.
- Apply all artifact edits with `apply_patch`.
- Use RTK for repository inspection and validation.
- Use the repository STE guide and installed `ste-linter` for prose review.
  The CLI requires explicit file paths.
  Its configured `data/ste_dictionary.json` is absent, so vocabulary coverage is partial.
  Report that limitation instead of claiming a complete dictionary-backed check.

### Planning validation

The planning phase checked nine artifacts, 22 local links, 17 requirements, and 16 case groups.
Its initial handoff contained seven implementation groups.
Task generation expanded those groups into 40 executable tasks.
All new directory levels remain within five children.
Planning kept the branch unchanged and made no implementation edits.
The planning STE review met the 80-point threshold with zero structural errors.
Dictionary-backed vocabulary coverage remains partial.
The implementation evidence below supersedes the planning-only test status.

## Complexity Tracking

| Violation or variance | Why needed | Simpler alternative rejected because |
|----------------------|------------|--------------------------------------|
| Add one child to the already noncompliant `tests/guardrails/` parent | The requested issue-owned package contains all new work within five direct files. | Adding flat test files increases parent debt further. Expanding another issue's guard or restructuring unrelated tests violates the surgical boundary. |
| No release-note fragment | FR-017 explicitly excludes fragments for this internal-only feature. | A fragment expands scope and claims a customer-facing release change that does not occur. |

All other planned new hierarchy levels remain compliant.
No unresolved gate failure remains beyond these documented variances.
Mandatory companion execution remains unavailable, separate from design-gate evaluation.

### Final scope decision

The SpecKit analysis identifies the strict parent-child rule as unmet.
This issue retains the contained five-file package as a documented deviation.
The requested scope requires direct guardrails and excludes unrelated migrations.
The new package limits that deviation to one existing parent and one new child.
This decision does not claim constitution-wide hierarchy compliance.

The current task and canonical contribution guidance exempt internal-only changes from release fragments.
Those instructions govern this issue instead of the older constitution's blanket fragment rule.
No constitution, template, workflow, or shared record changes.
The coordinator still controls publication through its verified stable-main permission.

## Local Implementation Evidence

The implementation uses five source files and the three authorized existing sections.
No analyzer, installed package, settings, baseline, workflow, manifest, hook, application, README, or release file changed.

Input accounting produced 24 expected red failures, then 24 passing cases.
Missing CI decoding produced 12 expected normalization failures before its implementation.
The final direct fixture suite passed 396 cases with only the live class excluded.
Additional literal-preservation cases produced nine real false-approval failures, then all 12 targeted cases passed.

The actual live guides failed before their edits.
That report measured six reads, three validations, three guide decisions, and four effective paths.
After the edits, the same class passed with six reads and six validations.
All three guide decisions completed.
The decoder measured two explicit, two automatic, and four effective controls.

The scope suite passed 82 cases with 124 real installed analyzer subprocesses.
The combined new and unchanged ratchet suite passed 493 tests without skips.
Affected document guards passed 142 additional tests without skips.
The preliminary explicit-root analyzer checked two new files and found zero findings.
That preliminary result does not prove a clean committed CI candidate.

All five files passed semantic compilation, measured source limits, Ruff, Black, and explicit-file mypy.
The installed STE check passed its 80-point threshold for all eight implementation files.
Dictionary-backed vocabulary coverage remains unavailable.
The parent completed T038-T040.
The final package and existing ratchet suite passed 514 tests without skips.
Guard and fixture coverage measured 98.22 percent across 841 statements.
Twenty-one shell-profile regression cases failed before the correction and passed afterward.
The final document and link guards passed 161 tests.
One existing changelog guard skipped because a local run has no pull-request event.
Global Ruff, Black, compilation, and the CI type scope passed.
The configured full-suite ratchet checked 949 files and reported zero new findings.
The parent retains the clean candidate commit and gated publication.

### Authorized-base validation

The coordinator released publication on `856e5065413d3026f9c0f6d5222d9d379ec79d8b`.
The feature rebased onto that exact revision without conflicts.
The isolated environment now uses the incoming `misthelper-devtools` 0.6.0 pin.
No requirement file changed in this feature.

All 514 ratchet cases pass without skips and retain 98.22 percent coverage.
The required input guard checks six inputs, three guides, and four effective paths.
The committed CI-equivalent comparison checks two files and reports zero new findings.
The configured full-suite comparison checks 994 files and reports zero new findings.
Global Ruff passes, and Black leaves 2,005 files unchanged.
The current CI type scope passes for 663 source files.
The package type scope passes for five files.
The 13-file Markdown link check passes.
The complete hashed runtime audit checks 105 packages and finds no known vulnerabilities.
Dictionary-backed writing coverage and native PowerShell execution remain unavailable.

### Coupled CodeQL correction

CodeQL alert 236 identifies an omitted HTML comment terminator in the new guard.
The failed source is `2f931c69a867e1f914e347e8ae7f9a2e04ff04fd`.
The correction recognizes both tokens and rejects unsupported outside-fence `--!>` syntax.
This preserves CommonMark heading semantics rather than promote hidden commands.
Standard comments, unclosed comments, and fenced literals retain their intended behavior.

The 31 regression cases produced 18 failures before the correction and all pass afterward.
The complete focused corpus passes 542 tests without skips.
Coverage remains 98.22 percent across 843 guard and fixture statements.
The five-file structure and 136 functions remain within the measured limits.
All required local gates repeat before the authorized replacement push.
No suppression or excluded file changes.
Fresh CodeQL status and every other required check remain mandatory before merge.

PowerShell prerequisite execution failed because `pwsh` is absent.
The implementation used the explicit feature directory and checked-in context.
The optional commit hook remains unauthorized and did not run.
The mandatory after-implement companion dispatch was attempted with the registered command identifier.
RTK returned `No such file or directory` before the command could execute.
The companion extension directory is absent.
No companion hook or journal ran.
No replacement shared feature record or companion journal is authorized.
