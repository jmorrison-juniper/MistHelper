# Contract: Ops platform dateutil pin and Dependabot rule

This contract defines the interface between the ops platform requirements file, the Dependabot policy, and the guard module. It applies to issue #4908 only.

## Identity

- **Job**: `ops_platform_pytest`. The job name is `pytest (ops platform)` (RC-01).
- **Workflow**: Quality Gates, file `.github/workflows/ci.yml`.
- **Install command**: `pip install -r requirements.txt -e ".[dev]" -r requirements-dev.txt`, run in `mist-ops-platform` (RC-02).

## Ops pin

- **Input file**: `mist-ops-platform/requirements.txt`.
- **Rule**: The file holds exactly one `python-dateutil` line. Its version is `2.9.0.post0`. The line carries the annotation `# via celery`.
- **Source of the rule**: `requirements/default.txt` line 8 at tag `v5.7.0` of celery (RC-50).
- **Defect message**: For the pin 4.0.0, the message reads `python-dateutil pin 4.0.0 differs from celery pin 2.9.0.post0`.
- **Missing input**: The guard fails and names the missing file.

## Dependabot rule

- **Input file**: `.github/dependabot.yml`.
- **Target entry**: The entry with `package-ecosystem: "pip"` and `directory: "/"` (RC-23).
- **Required rule**: The entry holds an `ignore` list. The list holds one item with `dependency-name: "python-dateutil"` and `update-types` equal to `["version-update:semver-major"]`.

The required YAML block follows. Place it after the `commit-message` block of the pip entry.

```yaml
    ignore:
      # celery 5.7.0 pins python-dateutil to 2.9.0.post0. A major update breaks the ops platform install.
      # Remove this rule when a released celery accepts python-dateutil 4.x. Update the guard pin in the same change.
      - dependency-name: "python-dateutil"
        update-types: ["version-update:semver-major"]
```

- **Forbidden**: An `ignore` item without `update-types`, which blocks every update of its package.
- **Forbidden**: An `ignore` item that names any package other than `python-dateutil` in the pip entry.
- **Forbidden**: A pip entry with no `ignore` list when the rule is required. The guard reports this as a missing pip entry or a missing rule.

## Guard outcomes

| Input | Outcome |
| - | - |
| Ops pin `2.9.0.post0`, rule present | Pass. The guard reports zero defects. |
| Ops pin `4.0.0` | Fail. The guard reports one pin defect. |
| Rule missing | Fail. The guard reports one rule defect. |
| Rule narrowed to `version-update:semver-minor` | Fail. The guard reports one rule defect. |
| Blanket rule for `python-dateutil` | Fail. The guard reports one rule defect. |
| Rule for another package in the pip entry | Fail. The guard reports one rule defect. |
| Pip entry missing | Fail. The guard reports one entry defect. |
| Requirements file or policy file unreadable | Fail. The guard names the file. |

## Output

The guard writes one summary line to the test log. The line names the number of files read and the number of defects. The guard writes its `info` lines in ASCII.

## Reversal

Remove the Dependabot rule, and update the guard pin constant, in the same pull request. Do this only after a released celery accepts python-dateutil 4.x (RC-52 shows the unreleased upstream state).
