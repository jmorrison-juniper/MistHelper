# Contract: The suppression comment and the security gate command

**Feature**: `1032-bandit-severity-gate` | **Date**: 2026-07-28

This feature exposes two contracts. A future maintainer reads the first one in the source. A CI job runs the second one.

---

## Contract 1 - The suppression comment

### Purpose

A suppression comment hides one bandit finding. The comment is the only record of why the team accepted the finding. User Story 3 requires that a maintainer understands the reason without help from the author.

### Format

```text
<code>  # nosec <RULE> [<RULE> ...] - <reason>
```

### Rules

| Rule | Requirement | Source |
| - | - | - |
| The comment starts with `# nosec`. | Bandit reads `# nosec` only. It ignores `# noqa`. | Research decision R4 |
| At least one rule identifier follows `# nosec`. | A bare `# nosec` hides every future rule on that line. | FR-007 |
| Several identifiers appear space separated, as in `# nosec B603 B607`. | One statement can carry two findings. | Research decision R3 |
| A single ASCII hyphen with one space on each side separates the identifiers from the reason. | Principle V requires ASCII. An em dash fails. | Principle V |
| The reason is one sentence. It ends with a period. | A short reason reads faster than a long one. | FR-007 |
| The reason states why the finding is safe **at this call site**. | A generic reason such as "safe" carries no information. | FR-007, SC-008 |
| The comment may sit on any line inside the flagged statement. | Bandit matches the whole line range of the statement. | Research decision R3 |
| The line must not exceed 120 characters at the repository root. | The root `ruff` line length is 120. | `pyproject.toml` |
| The line must not exceed 99 characters inside `mist-ops-platform`. | That subtree holds its own `ruff` configuration. | `mist-ops-platform/pyproject.toml` |
| Two spaces separate the code from the comment. | `black` and `ruff` expect two spaces before an inline comment. | PEP 8 |

### Accepted examples

```python
import subprocess  # nosec B404 - Injected into the PackageInstaller seam only. Every runtime call uses SubprocessRunner.

CANCEL_TOKEN = "q"  # nosec B105 - Prompt sentinel that aborts the flow. It is not a credential.

subprocess.run(  # nosec B603 B607 - Every argument is a literal. shutil.which resolved the executable above.
    [git_path, "check-ignore", "--stdin"],
    check=False,
)

assert prepared is not None  # nosec B101 - Type narrowing only. The early return above proves the value.
```

### Rejected examples

| Example | Why it fails |
| - | - |
| `# nosec` | No rule identifier. It hides every future rule on the line. |
| `# nosec B105` | No reason. Requirement FR-007 forbids a bare suppression. |
| `# nosec B105 - safe` | The reason states no fact. A reviewer learns nothing. |
| `# nosec B105 — sentinel value` | The separator is an em dash. Principle V requires ASCII. |
| `# noqa: S105 - sentinel value` | Bandit ignores `# noqa`. The finding still reports. |
| `# nosec B105 - reason` on line 200 for a statement that spans lines 210 to 214 | The comment sits outside the statement range. |

### Scope

This contract governs the comments that this feature adds. The specification states that the existing 79 suppression comments in 38 files stay valid, and that this work does not review them.

---

## Contract 2 - The CI security gate command

### Purpose

The gate stops a pull request that adds a bandit finding at any severity.

### Location

`.github/workflows/ci.yml`, in the job named `bandit`.

### Command before this feature

```yaml
      - name: Run Bandit
        # -c pyproject.toml picks up [tool.bandit] targets/exclude_dirs (issue #881)
        # -ll gates on MEDIUM+ severity (LOW findings surface in logs but don't fail)
        run: bandit -c pyproject.toml -r . -ll
```

### Command after this feature

```yaml
      - name: Run Bandit
        # -c pyproject.toml picks up [tool.bandit] targets/exclude_dirs (issue #881)
        # No severity flag: the gate fails on a finding at any severity, including LOW (issue #889)
        run: bandit -c pyproject.toml -r .
```

### Rules

| Rule | Requirement |
| - | - |
| The command must not contain `-ll`. | FR-002, SC-002 |
| The command must not contain any other severity flag, such as `-l` or `--severity-level`. | FR-003 |
| The command must not contain a confidence flag, such as `-i` or `--confidence-level`. | FR-003 |
| The command must keep `-c pyproject.toml`. | FR-004 |
| The command must keep `-r .`. | FR-004 |
| The comment above the step must state that the gate fails on any severity. | FR-005 |
| The step must stay inside the existing 5 minute job timeout. | SC-003 |

### Exit behavior

| Condition | Exit code | Job result |
| - | - | - |
| The scan reports zero findings. | 0 | Pass |
| The scan reports one or more findings at any severity. | 1 | Fail |
| The scan cannot read the configuration file. | 2 | Fail |

### Do not change

- The `[tool.bandit]` table in `pyproject.toml`. The `targets` list and the `exclude_dirs` list stay as issue #881 left them. The specification lists a change there as a non-goal.
- The `pip install 'bandit[toml]'` step. Research decision R11 records the missing version pin as a separate concern.
