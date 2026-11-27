# Contract: Dependabot pip update block

## Consumers

- Dependabot reads the pip update block in `.github/dependabot.yml`.
- The policy guard in `tests/guardrails/test_pr_title_workflow.py` reads the same block through `POLICY_SNAPSHOTS["dependabot"]`.

## Required Shape

The pip update block holds the `ignore` entry below. The block starts at line 3 of `.github/dependabot.yml`.

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
      # radon 6.0.1 requires mando below 0.8, so a later mando release breaks the dependency_lock job.
      - dependency-name: "mando"  # Skip every mando update that radon rejects.
        update-types: ["version-update:semver-minor", "version-update:semver-major"]  # Minor and major updates cover each mando release from 0.8 on.
```

## Guard Expectations

- The snapshot in `POLICY_SNAPSHOTS["dependabot"]` equals this shape after the guard reverses the two approved prefixes.
- Removing the `ignore` entry makes the guard fail.
- Replacing `version-update:semver-minor` with another update type makes the guard fail.
- The guard message names Dependabot, so each failure is easy to read.

## Exit Condition

Caution: removing the ignore admits a mando pin that the radon constraint rejects. Remove it only when radon publishes a release that accepts `mando` 0.8 or later. The same reviewed change must update the guard snapshot.

## Verification

```powershell
python -m pytest tests/guardrails/test_pr_title_workflow.py
```
