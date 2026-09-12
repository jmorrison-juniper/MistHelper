# Quickstart: Verification Recipes per Story

**Feature**: `specs/1016-misthelper-suppression-cleanup/`

**Date**: 2026-07-13

## Purpose

Give a reviewer or operator a one-page recipe per story to confirm the story is complete. Every recipe returns pass/fail deterministically — no judgement calls.

## Pre-push local gate (applies to every story)

Run before every `git push`:

```bash
rtk black --check .
rtk ruff check .
pytest -v --tb=short
```

All three MUST return zero findings / all-pass before the branch is pushed. This is the mandatory pre-push gate per user feedback recorded in memory (`Pre-push black + ruff gate`).

## Merge gate (applies to every PR)

Immediately before invoking merge:

```bash
gh pr view <PR_NUMBER> --json mergeStateStatus
```

MUST return `"mergeStateStatus": "CLEAN"`. No `--admin` bypass under any condition (FR-006 / recorded feedback `No --admin merge bypass`).

Then arm auto-merge:

```bash
GITHUB_TOKEN= gh pr merge <PR_NUMBER> --auto --squash --delete-branch
```

Then poll:

```bash
gh pr view <PR_NUMBER> --json state,mergeCommit
```

Until state is `MERGED`.

## Public API preservation (applies to every PR)

At every PR opening AND immediately before merge:

```bash
python -c "import MistHelper; print('\n'.join(sorted(n for n in dir(MistHelper) if not n.startswith('_'))))" > /tmp/current_public_api.txt
diff specs/1016-misthelper-suppression-cleanup/contracts/public_api_snapshot.txt /tmp/current_public_api.txt
```

The `diff` MUST produce empty output. Any diff blocks merge.

---

## Story 1 (#895) — Bootstrap re-exports

```bash
# Must all return zero findings:
ruff check MistHelper.py --select F401
pylint MistHelper.py --disable=all --enable=unused-import

# Must return zero matches:
grep -n "# noqa: F401" MistHelper.py
grep -n "# pylint: disable=unused-import" MistHelper.py

# Must succeed and print a positive integer:
python -c "import MistHelper; print(len(MistHelper.__all__))"

# Audit delta (via tools/refactor_analyzer/) must show suppression drop of ≥ 120.
```

## Story 2 (#899) — Mypy grab-bag

```bash
# Must report zero findings in these five categories on MistHelper.py:
mypy MistHelper.py --strict

# Must return zero matches:
grep -nE "# type: ignore\[(misc|assignment|no-any-return|arg-type|operator)" MistHelper.py
```

## Story 3 (#901) — Complexity extraction

```bash
# Must return zero findings:
ruff check MistHelper.py --select C901,PLR0913

# Must return zero matches:
grep -nE "# noqa: (C901|PLR0913)" MistHelper.py

# Extracted helpers coverage ≥ 90% (project gate coverage.fail_under=90 still passes overall):
pytest -v --tb=short --cov=MistHelper --cov-fail-under=90
```

## Story 4 (#898) — no-untyped-call via Protocols

```bash
# Must report zero no-untyped-call findings in MistHelper.py:
mypy MistHelper.py --strict

# Must return zero matches:
grep -n "# type: ignore\[no-untyped-call" MistHelper.py

# Protocol classes must exist:
test -f src/utils/misthelper_facade.py
python -c "from src.utils import misthelper_facade; print(dir(misthelper_facade))"
```

## Story 5 (#897) — type-arg

```bash
# Must report zero type-arg findings:
mypy MistHelper.py --strict

# Must return zero matches:
grep -n "# type: ignore\[type-arg" MistHelper.py
```

## Story 6 (#896) — Line length

```bash
# Must return zero findings:
ruff check MistHelper.py --select E501

# Must return zero matches:
grep -n "# noqa: E501" MistHelper.py

# Must report no diffs:
black --check MistHelper.py
```

## Story 7 (#900) — Bandit

```bash
# Must report zero findings:
bandit -r MistHelper.py

# Must return zero matches:
grep -n "# nosec" MistHelper.py

# If subprocess_runner was introduced, it must exist and its coverage must be ≥ 90%:
test -f src/utils/subprocess_runner.py && \
  pytest -v --tb=short --cov=src.utils.subprocess_runner --cov-fail-under=90 \
    tests/utils/test_subprocess_runner.py
```

## Story 8 (#902) — Long tail (final sweep)

```bash
# All four lint tools must pass with zero findings AND zero suppression comments:
ruff check MistHelper.py
pylint MistHelper.py --fail-under=9.5
mypy MistHelper.py --strict
bandit -r MistHelper.py
black --check MistHelper.py

# Success criterion SC-001: exactly zero suppression comments remain:
grep -cE "# (noqa|type: ignore|nosec|pylint: disable)" MistHelper.py
# MUST print: 0

# Config gate FR-010: pyproject.toml changes limited to per-file-ignore removals:
git diff main -- pyproject.toml
# Reviewer confirms visually that no rule disables or fail-under changes appear.
```

## Full-suite regression (applies to every PR)

Beyond the per-story recipes above, every PR MUST pass:

```bash
pytest -v --tb=short              # all tests green
coverage report --fail-under=90   # project coverage gate
pylint --fail-under=9.5 .         # project pylint gate
```

## Audit refresh (between stories)

After each merge, before opening the next story's PR:

```bash
python tools/refactor_analyzer/... MistHelper.py > /tmp/audit_post_story_<N>.txt
# Attach delta (previous baseline vs. current) to the next story's PR description per FR-015.
```
