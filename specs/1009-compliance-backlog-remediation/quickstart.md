# Quickstart: Operator Runbook for Serial Compliance Remediation

**Feature**: 1009-compliance-backlog-remediation
**Audience**: The operator (single-agent or human) driving remediation PRs one at a time.
**Preconditions**: Local checkout of `main` up to date; `data/compliance_backlog.tsv` present; `gh` CLI authenticated with admin privileges on the repo.

This runbook is the day-to-day loop. It reduces to two nested cycles: the **per-file loop** (7-step recipe) inside the **refresh loop** (repeat every 5 merges).

---

## Phase 2 Preview: How tasks.md Will Be Structured

`/speckit.tasks` will produce a single ordered list, one task per file in the current `data/compliance_backlog.tsv`, in strict rank order. Each task references its TSV row and has the same body shape:

```
T<rank>: refactor <path> compliance <old-grade>/<old-score> -> A/>=94.0 (target A+)

Backlog row: rank=<rank>, total=<total>, critical=<c>, high=<h>, medium=<m>, low=<l>, score=<s>, grade=<g>
Prereqs: T<rank-1> complete (or, for T1, FR-015 provenance decision recorded).
Recipe: contracts/per-file-pr.md (7 steps).
Done predicate: contracts/done-definition.md (D1..D6).
```

The task list is not fixed at 99 entries; after each backlog refresh, the remaining tasks are regenerated from the refreshed TSV. Rank-1 task carries the extra provenance-decision precondition (FR-015).

---

## The Per-File Loop (7 steps)

Given: the top unresolved row of `data/compliance_backlog.tsv` -- `path`, `rank`, `old-grade`, `old-score`.

### Step 1. Baseline scan

```bash
py -m tools.compliance_analyzer <path> -o /tmp/before.md -q
```

Open `/tmp/before.md`, note the grade and score in the header. These become `<old-grade>` and `<old-score>` in the PR title.

### Step 2. Branch

```bash
git checkout main && git pull --ff-only
git checkout -b refactor/compliance-<rank>-<slug>
```

`<slug>` = filename stem with non-`[A-Za-z0-9_-]` characters replaced by `_`.

### Step 3. Refactor (behavior-preserving)

Extract helpers so no function exceeds cyclomatic complexity 10 or line-count 50. Add same-line `# WHY:` comments on:
- every `if / elif / else / for / while / try / except / finally / with` line,
- every `return` statement,
- every guard clause,
- every non-obvious constant or magic value.

Do NOT change public signatures, `__all__`, class hierarchies, observable side effects, or test assertions.

### Step 4. Verify

```bash
py -m tools.compliance_analyzer <path> -o /tmp/after.md -q
```

Confirm the score is >=94.0 (target 100.0). If not, iterate on Step 3.

### Step 5. Local gates

```bash
py -m ruff check <path>
py -m black --check <path>
py -m mypy --strict <path>
py -m pytest tests/<matching-tests>
```

All four MUST pass. If any fail, fix and rerun.

### Step 6. Push and open PR

```bash
git add <path>
git commit -m "refactor: <slug> compliance <old-grade>/<old-score> -> <new-grade>/<new-score>"
git push -u origin refactor/compliance-<rank>-<slug>
gh pr create --base main \
  --title "refactor: <slug> compliance <old-grade>/<old-score> -> <new-grade>/<new-score>" \
  --body "<analysis>...</analysis><summary>...</summary>"
```

Body is text-only: `<analysis>` block describing the compliance issues and the extractions, `<summary>` block giving before/after grades and scores. No markdown headers, no code fences.

### Step 7. Wait for CI, then merge

Watch the PR page or run `gh pr checks <n> --watch`. When every gate is green:

```bash
gh pr merge <n> --squash --delete-branch --admin
```

Then `git checkout main && git pull --ff-only`. The row is now `Retired`.

---

## The Refresh Loop (every 5 merges)

After 5 `squash_merged` PRs since the last refresh:

```bash
py -m tools.compliance_analyzer src -r -o data/full_repo_compliance.md -q
# then regenerate data/compliance_backlog.tsv via the split-parser
```

Sanity checks:
- File count in the new TSV should be lower than before (or equal, if transitive lift did not fire on this batch).
- No previously-A+ file appears in the new TSV. If one does, it is treated as a blocker under FR-017: the next PR remediates it before any new backlog rank is picked.
- Any file whose refreshed grade is already >=A/94.0 is dropped from the queue (FR-016).

If the new TSV is empty AND the recursive scan's overall score is >=94.0, the initiative is complete. Report to the compliance owner.

---

## The Rank-1 Provenance Gate (once, before any refactor PR)

Before opening the very first remediation PR of this initiative:

1. Inspect the untracked file `src\mist_ideas_analyzer\__init__.py` (129 KB, F/54.0, 45 issues).
2. Decide with the compliance owner: **keep-and-commit**, **delete**, or **relocate**.
3. Execute the decision in a preparatory PR (NOT a remediation PR):
   - **keep-and-commit**: `git add src/mist_ideas_analyzer/__init__.py && git commit -m "chore: commit mist_ideas_analyzer/__init__.py under provenance decision"` on a branch `chore/mist_ideas_analyzer-provenance`; open and merge that PR. THEN the remediation loop starts at rank 1 against the now-tracked file.
   - **delete**: `git rm src/mist_ideas_analyzer/__init__.py` on branch `chore/delete-mist_ideas_analyzer-init`; open PR with justification in `<analysis>`; merge; refresh backlog; the next-highest rank becomes rank 1.
   - **relocate**: `git mv` the file to its appropriate package; open PR on `chore/relocate-mist_ideas_analyzer-init`; merge; refresh backlog; the new path is refactored under its new rank.

Record the decision in `contracts/done-definition.md`'s E4 escalation trigger notes if it is contested later.

---

## What to Do When Things Go Wrong

| Situation | Action |
|-----------|--------|
| Local ruff/black/mypy fails | Fix in place before push. |
| CI gate fails on merit | Push a follow-up commit to the same branch; do not force-merge. |
| CI gate is flaky | Rerun the gate (`gh workflow run` or the check's rerun button). Do not merge with `--admin` over a red gate. |
| Analyzer says post_score < 94.0 | Continue extracting helpers and adding `# WHY:` anchors until it passes; do NOT open the PR. |
| Reviewer requests a `# noqa` or `# type: ignore` | Refuse (FR-010). Escalate to the compliance owner if the reviewer insists. |
| PR review reveals a genuine bug | Split into a separate bug-fix PR (FR-019). The compliance PR remains behavior-preserving. |
| Rank drift moves the file mid-review | Complete the PR anyway (spec Edge Case). Next pick uses the refreshed backlog. |
| A previously-A+ file drops below A+ on refresh | Open a blocker PR to restore A+ before any new backlog rank (FR-017 / SC-003). |

---

## Success Signal

The initiative is done when:

- `data/compliance_backlog.tsv` regenerated from a fresh recursive scan is empty.
- `py -m tools.compliance_analyzer src -r ...` reports overall score >=94.0.
- No file previously at A+ has regressed.
- Every merged PR in the initiative touched exactly one backlog file and passed every gate.

Report completion to the compliance owner with a link to the final recursive scan output.
