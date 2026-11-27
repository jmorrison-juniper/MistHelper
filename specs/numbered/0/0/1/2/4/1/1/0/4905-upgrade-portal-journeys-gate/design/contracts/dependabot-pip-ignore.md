# Contract: Dependabot pip ignore entry for mando

**Surface**: `.github/dependabot.yml`, the pip update stream (`updates[0]`).
**Owner**: the repository maintainers. The guard test `tests/guardrails/test_pr_title_workflow.py` enforces the shape.
**Decision**: D-2 in `design/research.md`.

## Shape

The pip update stream gains one `ignore` list. The list holds one entry. The entry names the package and the rejected version range.

```yaml
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
    labels:
      - "dependencies"
    commit-message:
      prefix: "chore"
    ignore:
      # Radon 6.0.1, the newest radon release, requires mando below 0.8.
      # Pull request #4888 raised mando to 0.8.2, so pip could not resolve
      # requirements-dev.txt. The upgrade portal journeys gate failed (issue #4905).
      # This entry stops Dependabot from proposing mando 0.8 or later.
      # Remove this entry only after a radon release accepts mando 0.8.
      - dependency-name: "mando"
        versions: [">=0.8"]
```

## Fields

| Field | Value | Reason |
| - | - | - |
| `dependency-name` | `"mando"` | The package name in `requirements-dev.txt` line 179 (R-01). |
| `versions` | `[">=0.8"]` | A PEP 440 range. Its lower bound equals the first rejected release. Radon 6.0.1 requires mando from 0.6 up to, but not including, 0.8 (R-64, R-66). |
| `update-types` | not present | The range names every rejected release. A release-level filter would block more releases than radon rejects. |

The range form for pip is unverified (U-1). The GitHub docs state that a range uses the standard pattern of the package manager (R-68), and they give no pip example (R-69).

## Inputs and outputs

- Input: the Dependabot service reads `.github/dependabot.yml` on each scheduled run.
- Output: Dependabot skips each mando release that matches `>=0.8`. Dependabot still proposes the other pip updates.

## Invariants

1. The pip update stream keeps `commit-message.prefix: "chore"`. The policy test asserts the prefix (TST-001).
2. The github-actions stream and the npm stream stay unchanged. The policy snapshot compares every other field (TST-001, R-12 to R-16).
3. Removing the `ignore` list fails the policy test (TST-002).
4. Changing the range to a different boundary fails the policy test (TST-003).
5. The range excludes mando 0.8.2 and includes mando 0.7.1 (TST-004).
6. The rationale comment names issue 4905, pull request 4888, and the radon constraint. No automated test reads the comment. The review in T-PR checks it (FR-004).

## Non-goals

- No change to `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`, or `uv.lock` (FR-003).
- No change to the npm `typescript` ignore entry (R-11).
- No change to the commit prefixes of the other streams.

## Failure modes

- Dependabot rejects the range. The pip update stream then reports a configuration error. Mitigation: check the first pip run after the merge (U-1).
- A future radon release accepts mando 0.8. The entry then blocks a valid release. Mitigation: the comment names the removal condition.
- A maintainer removes the entry. The policy test fails in CI, and the change cannot merge until the snapshot and the file match again.

Caution: an invalid entry can stop the pip update stream until a maintainer corrects the file.

## Verification

- `python -m pytest tests/guardrails/test_pr_title_workflow.py` runs TST-001 to TST-004.
