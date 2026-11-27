# Contract: Dependabot Mando Ignore Rule

**Scope**: The pip entry in `.github\dependabot.yml` and the two guard tests that read it.

**Evidence**: Decision D-3 in `design\research.md`. Remote rows R-20, R-21, R-45, and R-46.

## Configuration Shape

The pip entry gains one `ignore` list. The existing keys do not change.

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
      # Block comment: radon 6.0.1 range, issue 4892, and the removal condition.
      - dependency-name: "mando"
        versions: [">=0.8"]
```

Rules for the entry:

- The entry has `package-ecosystem: "pip"` and `directory: "/"`.
- The `ignore` list holds one rule with `dependency-name: "mando"`.
- The `versions` value is a PEP 440 specifier. The schema calls it the package manager pattern (R-45).
- The value rejects mando 0.8.0, 0.8.2, and 1.0.0.
- The value accepts mando 0.6.0 and 0.7.1 for update proposals.

## Guard Behavior

The guard lives in `tests\guardrails\test_dependency_lock_file.py`. The change adds class `DependabotPolicy` and two test functions.

| Element | Contract |
| - | - |
| Radon range | A class constant with the value `<0.8,>=0.6`. The value comes from the PyPI metadata of radon 6.0.1 (R-46). |
| Sample releases | 0.6.0, 0.7.1, 0.8.0, 0.8.2, and 1.0.0. |
| Expected result | A sample is ignored if and only if the radon range rejects it. |
| Input file | `.github\dependabot.yml`, read with PyYAML `safe_load`. |
| Pip entry lookup | The entry whose `package-ecosystem` is `pip` and whose `directory` is `/`. |
| Missing rule | The check returns one defect. The defect names mando and the missing rule. |
| Count line | The guard prints the number of samples and the number of defects. |

Test functions:

1. `test_dependabot_pip_ignores_each_mando_release_radon_rejects` reads the real file. It fails when a sample is ignored in error, or not ignored in error. It fails before the configuration change (task T001).
2. `test_dependabot_guard_reports_missing_mando_rule` passes a pip entry without a mando rule to the check. It expects one defect. This test proves that the check can fail.

## Failure Messages

Each message names the release and the rule. Examples:

- `Dependabot pip entry does not ignore mando 0.8.2, which radon 6.0.1 rejects.`
- `Dependabot pip entry ignores mando 0.7.1, which radon 6.0.1 accepts.`

## Compatibility

When radon accepts a newer mando, one pull request changes three things:

1. The radon range constant in the guard.
2. The `versions` value in `.github\dependabot.yml`.
3. The comment block above the rule.
