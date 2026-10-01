# Contract: Local Test-Quality Commands

**Specification**: [spec.md](../../spec.md)

This contract describes existing installed commands and their local procedure.
It adds no application API.
The three authorized guide sections now implement the procedure below.
The parent retains final validation and delivery.

## Required Locations

| Document | Heading chain |
|----------|---------------|
| `.github/copilot-instructions.md` | `Validate locally, then push once` |
| `agents.md` | `Local Development Quick Reference` |
| `.github/instructions/git-flow-multi-agent.instructions.md` | `Part 3. GitHub Actions minutes` / `The local-first loop` |

Each section contains the complete procedure.
A link to another guide is not sufficient.
Preserve existing checks and text outside each named section.

## Active Procedure Labels

Use these visible labels in each named section:

1. `**Intended base for the required check:**`
2. `**Required input preflight:**`
3. `**Required check after the local commit and before push:**`
4. `**Full-suite check for push or manual CI:**`

Each label introduces exactly one executable shell fence.
Use `powershell`, `bash`, or `sh` as the fence language.
The next nonblank block after a label is its command fence.
Do not place an active label inside a comment or quoted example.

The guard checks these active fences.
It rejects duplicate labels instead of choosing a convenient matching example.
Correct command text in another section or an unused example does not satisfy the contract.

## Sequence

1. Run existing applicable checks before the local commit.
2. Commit all intended tests and relevant inputs.
3. Confirm that the relevant working tree matches the intended candidate.
4. Set the intended pull-request base.
5. Fetch that base into its matching `origin/` reference.
6. Verify that the reference resolves to a commit.
7. Run the direct required-input preflight.
8. Run the scoped installed analyzer command.
9. Require zero new findings before push.

If any command fails, stop before the next command.
Do not push after a failed or skipped check.
Repeat affected checks if the candidate, checked content, or base changes.

The parent owns the local commit and delivery.
These steps do not authorize Git mutations in this planning session.

## Intended Base

Set `BASE_REF` to the intended pull-request base branch.
Use `main` only when that is the intended base.
Do not substitute a different base to obtain a zero-file result.

### PowerShell

```powershell
$BASE_REF = "main" # Replace this value when the intended base differs.
rtk proxy git fetch --no-tags origin "+refs/heads/${BASE_REF}:refs/remotes/origin/${BASE_REF}"
rtk proxy git rev-parse --verify "origin/${BASE_REF}^{commit}"
```

### Bash

```bash
BASE_REF=main # Replace this value when the intended base differs.
rtk proxy git fetch --no-tags origin "+refs/heads/${BASE_REF}:refs/remotes/origin/${BASE_REF}"
rtk proxy git rev-parse --verify "origin/${BASE_REF}^{commit}"
```

The fetch destination, resolved reference, and analyzer comparison use the same variable.
The guard preserves this relationship when it normalizes syntax.
Single quotes around `origin/$BASE_REF` prevent expansion and must fail.

## Required Input Preflight

After implementation, use the new direct live-guide test class.
The class reads all six required files and checks the active procedures.
It does not execute the analyzer or document commands.

```powershell
rtk proxy python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

Use the same token form in Bash.
The `-s` option keeps the measured guard report visible.
The preflight must pass before an analyzer result can satisfy the procedure.

A missing repository settings file fails this preflight.
The analyzer alone uses defaults when that file is missing or empty.
Do not claim that the analyzer alone rejects a missing settings file.
Unreadable or malformed settings cause analyzer errors.
The baseline must remain readable and valid even when no tests enter scope.

## Required Scoped Command

The current live pull-request contract is:

```text
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from "origin/$BASE_REF" --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Each guide contains an executable shell form, not only this text example.
The recommended RTK prefix preserves the complete analyzer output.

### PowerShell

```powershell
rtk proxy test-quality-analyzer --gate `
  --config .github/test-quality-config.toml `
  --baseline .github/test-quality-baseline.json `
  --changed-from "origin/$BASE_REF" `
  --full-gate-path .github/workflows/ci.yml `
  --full-gate-path requirements-dev.txt
```

### Bash

```bash
rtk proxy test-quality-analyzer --gate \
  --config .github/test-quality-config.toml \
  --baseline .github/test-quality-baseline.json \
  --changed-from "origin/$BASE_REF" \
  --full-gate-path .github/workflows/ci.yml \
  --full-gate-path requirements-dev.txt
```

The new guard derives the additional trigger values from live CI.
It does not cache this document's current two-path list in code.

## Full-Suite Command

Push and manual CI runs retain the empty changed-scope array.
They scan every discovered test root.
Each guide contains this complete local equivalent:

```powershell
rtk proxy test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

Use the same command in Bash.
Do not add `--changed-from`, `--roots`, or scope-narrowing controls to this command.
Use the same required-input preflight before the full-suite check.

## Selection and Content

`--changed-from` compares the intended base revision with `HEAD`.
The installed resolver uses two revision endpoints, not a merge-base comparison.
It selects existing recognized tests from that committed path difference.

Staged, unstaged, and untracked-only paths do not enter that comparison.
Changes to an already selected file can still change its analyzed content.
The analyzer reads selected files from the current working tree.
A clean local commit therefore supplies the intended committed candidate.

Recognized filenames are `test_*.py` and `*_test.py`.
A deleted test has no existing file to analyze.
Rename detection can name both paths.
Only existing recognized paths enter analysis.

## Full-Suite Triggers

| Current path | Source |
|--------------|--------|
| `.github/test-quality-config.toml` | Automatic trigger from the settings argument |
| `.github/test-quality-baseline.json` | Automatic trigger from the baseline argument |
| `.github/workflows/ci.yml` | Explicit live CI `--full-gate-path` |
| `requirements-dev.txt` | Explicit live CI `--full-gate-path` |

Each guide explains all four paths.
If the committed endpoint difference names a trigger, the analyzer selects every test root.
Git rename settings can change which names enter that difference.
An invalid required input can still make that full-suite run fail.
Full-suite selection does not excuse a missing baseline.

## Output and Result

The installed output shape is:

```text
gate_scope: N files checked, M findings checked
gate: K new findings vs baseline
```

`N` counts discovered test files before parsing and exclusions.
`M` counts findings after rule filters.
`K` counts new findings against the baseline.
Existing accepted findings can make `M` positive while `K` remains zero.

Selection and trigger explanations appear in stderr logging.
The `gate_scope` line does not contain mode, reason, or changed-path fields.
The JSON report lists `analyzed_files` when the run produces a report.
Do not equate discovered file counts with parsed or analyzed file counts.

Exit 0 and zero new findings are required.
Exit 1 reports new findings.
Exit 2 reports invalid use, an unresolved scope, or an input or engine error.
A missing report or skipped check is not passing evidence.
A valid empty-scope run prints zero counts but does not write a report.
The preliminary explicit-root run measured two new test files and zero findings.
Its two omitted-root records describe the intentionally unmeasured repository roots.
They do not replace full configured committed-candidate evidence.

## Forbidden Substitutions

- An obsolete repository module or different executable.
- A manual list of changed tests.
- A triple-dot or merge-base comparison.
- A hard-coded substitute base when the intended base differs.
- Missing or different settings, baseline, or live trigger values.
- Extra roots, disabled rules, or baseline-writing controls.
- Correct text only in comments or outside the active procedure.
- A pre-commit hook presented as committed-candidate evidence.
