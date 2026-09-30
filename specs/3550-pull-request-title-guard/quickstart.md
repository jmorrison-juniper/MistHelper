# Quickstart Validation: Pull request title guard

**Issue**: #3550
**Plan**: [plan.md](plan.md)

Use this guide after implementation.
The planning step does not create the checker or run its tests.
The [title contract](contracts/title-check.md) and [workflow contract](contracts/workflow-policy.md) define expected behavior.
The [data model](data-model.md) defines counts and result states.

## Prerequisites

1. Use the existing issue worktree and its app-managed branch.
2. Use a local worktree environment with Python 3.13 and the pinned development tools.
3. Run each command from this worktree's repository root.
4. Keep `SPECIFY_FEATURE_DIRECTORY=specs/3550-pull-request-title-guard` explicit for each SpecKit step.
5. Use no credentials, network call, main-checkout environment, or production container for these local proofs.

If a required tool is unavailable, stop and name the missing capability.
Do not install packages during this planning step.
Do not treat an absent tool or skipped test as a pass.

The commands below use the local POSIX environment path.
On Windows, use the corresponding worktree `.venv\Scripts` executable.
Keep the `rtk` prefix.

## 1. Confirm the local context

```bash
rtk proxy git --no-pager status --short
rtk proxy git --no-pager branch --show-current
rtk proxy env SPECIFY_FEATURE_DIRECTORY=specs/3550-pull-request-title-guard .venv/bin/python --version
```

Expect `jmorrison-juniper-pull-request-title-guard` and Python 3.13.
Confirm the owned manifest before a manual edit.
Do not change `.specify/feature.json`.

## 2. Prove the two exact title decisions

```bash
rtk proxy .venv/bin/python -c "from scripts.pr_title_guard import PullRequestTitleGuard; raise SystemExit(PullRequestTitleGuard().check('wip: model prompts'))"
rtk proxy .venv/bin/python -c "from scripts.pr_title_guard import PullRequestTitleGuard; raise SystemExit(PullRequestTitleGuard().check('fix(web-portal): model prompts'))"
```

Run these commands separately.
The first command must exit with one.
It must print `"wip: model prompts"` and `Checked 1 pull request title`.
The second command must exit with zero.
It must print `"fix(web-portal): model prompts"` and the same count.
Compare complete stdout with the title contract, not only these two lines.

These direct decisions need no event file or network.
The actual decision must have before and after log records when logging capture is enabled.

## 3. Run all owned behavior and policy tests

```bash
rtk proxy .venv/bin/python -m pytest tests/unit/scripts/test_pr_title_guard.py tests/guardrails/test_pr_title_workflow.py -q --timeout=120
```

Expect all selected tests to pass with no successful environmental skip.
The unit tests must prove these outcomes.

| Scenario | Expected evidence |
| --- | --- |
| Nine types and four forms | Exact true decisions. |
| Unsupported types and invalid grammar | Exact false decisions and failing results. |
| Unicode, quotes, backslashes, and shell punctuation | Reversible ASCII JSON string output. |
| Controls, Unicode separators, blank strings, and large invalid strings | Failure with count one for available strings. |
| Large valid descriptions | Pass without truncation or an invented length restriction. |
| Missing environment, missing or unreadable file, and unusable path | Explicit input failure with count zero. |
| Bad UTF-8, bad JSON, and wrong payload or title type | Explicit input failure with count zero. |
| Before/after action records | Correct order and safe variable output. |
| `main` and the module CLI | Correct stdout, stderr boundary, count, and exit code. |

The CLI tests must invoke `python -m scripts.pr_title_guard` with temporary event fixtures.
They must not interpolate the fixture title into a shell command.
They must prove passing, title-failure, and input-failure process outcomes.

The guardrail tests must prove all five events, no filters, exact concurrency, and read-only execution.
They must compare the complete Dependabot policy after reversing only the two allowed prefix changes.
They must verify the actual check name and the approval boundary in Part 6.

## 4. Prove the missing-input CLI failure

```bash
rtk proxy env -u GITHUB_EVENT_PATH .venv/bin/python -m scripts.pr_title_guard
```

Expect exit code one and these exact stdout lines.

```text
Result: FAIL - GITHUB_EVENT_PATH is missing or empty.
Checked 0 pull request titles
```

Expect event-read before and failed-after records on stderr.
Expect sanitized error context, not an invented title or a title-decision record.

## 5. Run the applicable local source gates

```bash
rtk proxy .venv/bin/python -m py_compile MistHelper.py scripts/pr_title_guard/__init__.py scripts/pr_title_guard/__main__.py tests/unit/scripts/test_pr_title_guard.py tests/guardrails/test_pr_title_workflow.py
rtk proxy .venv/bin/python -m ruff check scripts/pr_title_guard/__init__.py scripts/pr_title_guard/__main__.py tests/unit/scripts/test_pr_title_guard.py tests/guardrails/test_pr_title_workflow.py
rtk proxy .venv/bin/python -m black --check scripts/pr_title_guard tests/unit/scripts/test_pr_title_guard.py tests/guardrails/test_pr_title_workflow.py
rtk proxy .venv/bin/python -m mypy --config-file pyproject.toml scripts/pr_title_guard/__init__.py scripts/pr_title_guard/__main__.py
rtk proxy .venv/bin/python -m bandit scripts/pr_title_guard/__init__.py scripts/pr_title_guard/__main__.py
```

Expect no syntax, lint, format, type, or security finding.
Give Ruff the explicit new files because the repository excludes broader script scans.
Confirm each gate measures the package rather than skipping it.
Use explicit source files for mypy and Bandit.
The repository configuration excludes scripts during directory discovery.
The targeted Bandit command keeps all checks and measures both files.
Review method and class limits directly.
Review explanatory inline comments and real before/after logging.
Run all other existing gates that apply to the owned file set.
Read their current commands without editing the shared workflow or quality guide.

## 6. Run the unchanged test quality ratchet

```bash
rtk proxy .venv/bin/test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --roots tests/unit/scripts tests/guardrails
```

Expect zero new findings and exit code zero.
Explicit roots include new untracked test files before the feature commit.
The analyzer writes only its existing ignored reports.
Do not add those reports to the feature manifest.

Do not use `--write-baseline`, `--prune-baseline`, `--disable-rule`, or an exclusion change.
Do not replace either repository ratchet file with an installed-package default.
If another file causes an existing failure, report it without changing its ownership.

## 7. Review ownership and policy

```bash
rtk proxy git --no-pager diff --name-only
rtk proxy git --no-pager diff -- .github/dependabot.yml .github/instructions/git-flow-multi-agent.instructions.md
rtk proxy git --no-pager status --short --untracked-files=all
```

Expect only the approved feature paths.
The Dependabot diff must contain only the two prefix substitutions.
The instruction diff must stay inside Part 6.
Record this one-time git proof in the feature-owned context.
Do not freeze unrelated instruction text with a permanent test hash.
Keep `ci.yml`, `quality-gates.md`, ratchet files, shared feature pointers, and other shared instructions unchanged.
Do not add a required check or change strict protection.

## 8. Collect later delivery evidence

The parent performs this section only during the authorized full cycle.
It is not part of this planning command.

1. Record the local gates, direct failure proof, owned manifest, and metadata-only deployment note.
2. Use one Conventional Commits commit and one push.
3. Complete the PR template and include `Closes #3550`.
4. Wait for all required checks, including CodeQL.
5. Complete the coordinated squash merge only after those checks pass.
6. Verify the exact merged commit locally without using the main checkout.
7. Rerun the owned behavior, policy, and test quality proofs against that merged tree.

On the implementation PR, confirm the exact check name and its conclusion.
Verify that a title edit starts a new result from the edited event file.
If two runs overlap, confirm same-group cancellation and another head branch's independent run.
Do not push an extra commit only to demonstrate cancellation.
Use the offline contract when the overlap does not occur naturally.

No production container deployment is required.
The existing squash-title setting and required checks must remain unchanged.
