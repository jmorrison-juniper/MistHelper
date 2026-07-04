# Contract: Per-File Remediation PR

**Feature**: 1009-compliance-backlog-remediation
**Scope**: The exact shape of a single remediation PR. Every PR opened under this initiative MUST conform to this contract.

---

## Preconditions

- The current branch is `main` (or a fresh branch cut from `main`), fully rebased.
- `data/compliance_backlog.tsv` is fresh (regenerated within the last 5 merges, or is the initial authoring-time snapshot).
- The top unresolved row of the backlog has been identified. Its `path`, `rank`, current `grade`, and current `score` are recorded.
- No other `RemediationPR` is `opened` or `gates_green` (I2 in data-model).
- If the picked file is rank 1 and it is the untracked `src\mist_ideas_analyzer\__init__.py`, the FR-015 provenance decision has already been recorded and executed.

## Commands (in order)

1. **Baseline scan** (produces `pre_score`):

   ```
   py -m tools.compliance_analyzer <path> -o /tmp/before.md -q
   ```

   Record `<old-grade>` and `<old-score>` from the top of `/tmp/before.md`.

2. **Branch**:

   ```
   git checkout -b refactor/compliance-<rank>-<slug>
   ```

   Where `<slug>` is derived from the file's stem by replacing non-`[A-Za-z0-9_-]` characters with `_`.

3. **Refactor** (behavior-preserving):
   - Extract helpers so no function exceeds cyclomatic complexity 10 or line-count 50.
   - Add same-line `# WHY:` comments on control-flow lines, `return` statements, guards, and non-obvious constants until analyzer inline-comment coverage is >=80%.
   - Preserve public signatures, `__all__`, class hierarchies, side effects, and test assertions.

4. **Verification scan** (produces `post_score`):

   ```
   py -m tools.compliance_analyzer <path> -o /tmp/after.md -q
   ```

   `<new-score>` MUST be >=94.0; target is 100.0 (A+).

5. **Local gates** (fast fail before push):

   ```
   py -m ruff check <path>
   py -m black --check <path>
   py -m mypy --strict <path>
   py -m pytest tests/<matching-tests>
   ```

   All four MUST pass locally.

6. **Push and open PR**:

   ```
   git push -u origin refactor/compliance-<rank>-<slug>
   gh pr create --base main --head refactor/compliance-<rank>-<slug> \
     --title "refactor: <slug> compliance <old-grade>/<old-score> -> <new-grade>/<new-score>" \
     --body "<analysis>...</analysis><summary>...</summary>"
   ```

7. **Wait for CI gate matrix** (all 13 gates must be `pass`):
   Ruff, Black, mypy strict, Pylint, pytest coverage, Bandit, Vulture, pydocstyle, Interrogate, pip-audit, Radon, CodeQL, E2E smoke.

8. **Merge**:

   ```
   gh pr merge <n> --squash --delete-branch --admin
   ```

   `--admin` MUST NOT be used to bypass a red gate.

## Postconditions

- The PR is `squash_merged` with branch deleted.
- The refactored file's score on a fresh scan is >=94.0.
- No new `# noqa: STRUCT-*`, `# noqa: CONV-*`, `# type: ignore`, or `# pragma: no cover` markers exist in the file.
- Inline `# WHY:` coverage on the file is >=80%.

## PR body format (text-only)

The body is exactly two tagged blocks, no markdown headers, no code fences:

```
<analysis>
[Plain text describing what compliance issues existed in the file at baseline, which
helper extractions were performed, and which lines received # WHY: anchors. Note any
deviation from A+ target and why A (>=94.0) is the accepted result.]
</analysis>
<summary>
[One-paragraph summary of the diff: files touched, before/after grades and scores, gate
status. No bullet lists, no headers.]
</summary>
```

Enforcement: reviewer inspection at PR time. Any markdown header (`#`, `##`) or fenced code block (` ``` `) inside the body is a merge blocker.

## Rejection reasons (a PR MUST NOT merge if any hold)

- Files touched count != 1.
- Post-scan score < 94.0.
- Any of the 13 gates is red.
- New suppression marker introduced.
- Public signature or `__all__` change.
- Test assertion change.
- Body contains markdown header or code fence.
- Title does not match the required regex.
- Branch name does not match `refactor/compliance-<rank>-<slug>`.
