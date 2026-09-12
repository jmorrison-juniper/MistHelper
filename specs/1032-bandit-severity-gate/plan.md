# Implementation Plan: Bandit Severity Gate Hardening

**Branch**: `security/889-bandit-ll` (SpecKit feature directory `1032-bandit-severity-gate`) | **Date**: 2026-07-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/1032-bandit-severity-gate/spec.md`

**GitHub Issue**: [#889](https://github.com/jmorrison-juniper/MistHelper/issues/889)

## Summary

The CI security gate runs `bandit -c pyproject.toml -r . -ll`. The `-ll` flag hides every finding below MEDIUM severity. The gate reports success while 54 LOW severity findings stay hidden.

This work clears all 54 findings, then removes the `-ll` flag. The work groups the findings by bandit rule, not by file. One rule shares one reasoning pattern. Grouping by rule keeps each decision consistent and keeps the pull request reviewable.

The plan orders the work from the most mechanical group to the group that needs the most judgment. The workflow edit comes last, because the gate fails while any finding remains.

## Technical Context

**Language/Version**: Python 3.13 (`pyproject.toml` target `py313`)

**Primary Dependencies**: `bandit[toml]` (no new runtime dependency)

The scan reads the `[tool.bandit]` table in `pyproject.toml`.

**Storage**: N/A (comment and guard changes only)

**Testing**: `pytest` with `--cov=src/ --cov-fail-under=80`. The existing suite must keep its pass count.

**Target Platform**: The CI runner uses Linux. Developers work on Windows. The two platforms report different raw counts. The section "Measurement contract" states the correction.

**Project Type**: static analysis remediation (no new module and no new class)

**Performance Goals**: The bandit job must stay inside its existing 5 minute timeout. The job finishes in about 10 seconds today.

**Constraints**:

- The root `ruff` line length is 120 characters. The `mist-ops-platform` subtree holds its own `pyproject.toml` with a line length of 99 characters. Three findings sit in that subtree.
- `black` formats the whole repository. `ruff check .` lints the whole repository.
- `mypy`, `pylint`, `radon`, `vulture`, and the coverage gate read `src/` only. `pylint` also skips `src/maps`, `src/ssh`, and `src/ui`.
- 24 of the 54 findings sit outside `src/`. Those findings face only `ruff`, `black`, and `bandit`.

**Scale/Scope**: 54 findings, 8 rules, 21 source files, and 1 workflow line.

### Measurement contract

The implementer re-measured the baseline on 2026-07-28 at commit `fb604b4` with bandit 1.9.4. The result matches the specification exactly.

```powershell
bandit -c pyproject.toml -r . -f json -o "$env:TEMP\bandit_1032.json" -q
```

A raw Windows run reports 105 findings. The implementer must apply two filters by hand, because a Windows scan does not honor the `exclude_dirs` entry for the analyzer fixtures. The entry uses a forward slash and a Windows scan reports a backslash.

| Filter step | Count |
| - | - |
| Raw findings on Windows | 105 |
| Minus findings in files that git does not track | 96 |
| Minus findings under `tools/test_quality_analyzer/fixtures/` | 54 |
| Findings above LOW severity, in scope | 0 |

The filter compares each normalized path against `git ls-files`. See [quickstart.md](quickstart.md) for the exact procedure.

### Verified mechanics

The implementer probed the bandit suppression behavior before writing this plan. Two results shape the tasks.

1. A `# nosec` comment suppresses a finding when it sits on **any line inside the statement**, not only on the reported line. Six subprocess calls span several lines. The comment may therefore sit on the clearest line.
2. One comment suppresses several rules when the rules appear space separated, as in `# nosec B603 B607`. Three statements carry both B603 and B607. Each of those needs one comment, not two.

### Discovered risk: the ruff `S` annotations do not reach bandit

The root `ruff` configuration selects `["E", "F", "W", "I", "UP", "B", "G"]`. It does **not** select `S`, which is the `flake8-bandit` rule set. Several source lines already carry annotations such as `# noqa: S101` and `# noqa: S603`. Those annotations suppress nothing today. They do not affect `ruff`, because `S` is not selected. They do not affect `bandit`, because `bandit` reads `# nosec` only.

The implementer must not read an existing `# noqa: S...` annotation as an earlier triage decision. Each affected line still needs a real decision and a real `# nosec` comment.

### Discovered risk: the CI bandit version is not pinned

The workflow runs `pip install 'bandit[toml]'` with no version constraint. A future bandit release may add a rule and may fail the stricter gate without a code change. The specification lists a pinned version as an assumption, but the workflow pins nothing. This plan records the gap. A version pin stays outside this scope, because the specification does not require it. The implementer must open a separate issue if the team wants the pin.

## Constitution Check

*GATE: The plan passes before Phase 0 research. The plan passes again after Phase 1 design.*

| Principle | Status | Basis |
| - | - | - |
| I. Five-Item Rule | PASS with a constraint | Seven `assert` statements become explicit checks. Each converted function must stay inside 25 lines and 5 blocks. The affected functions hold 1 to 3 statements today. |
| II. Class-Based Architecture (No Wrappers) | PASS | The work adds no function, no class, and no wrapper. |
| III. Safety-First | PASS with a gate | The credential family needs proof that each value is not a secret. Task group B blocks on that proof. No input handling changes. |
| IV. Full Deployment Pipeline | ADAPTED | Principle IV describes a direct push to `main`. This work follows the multi-agent branch workflow instead. The branch runs the full gate suite through CI and merges through a pull request. The container image needs no rebuild, because no runtime behavior changes. |
| V. Observability and Logging | PASS with a constraint | Every added comment and every added log message uses ASCII only. Six existing suppression comments use an em dash. Every comment that this work adds uses the ASCII hyphen. |
| VI. Inline Comments (NON-NEGOTIABLE) | PASS | Each `# nosec RULE - reason` comment states the reason on the changed line. Each converted guard carries a `# WHY:` comment. |
| VII. Action Logging (NON-NEGOTIABLE) | PASS with one deviation | The `shutil.which` resolution and the narrowed `except` blocks log before and after. `src/utils/logger_utils.py` is the single deviation. See Complexity Tracking. |
| Security Findings: Fix Over Suppress (NON-NEGOTIABLE) | PASS with a gate | The constitution permits `# nosec` for a **verified** false positive with a justification. This plan forbids a blanket suppression. Each suppressed finding needs one evidence line in the triage ledger. The review step rejects any suppression without evidence. |

### The suppression question

This plan proposes a code change for about 15 findings and a suppression for about 39 findings. That ratio needs a justification against the "fix over suppress" rule.

Rules B101, B105, B107, B404, B603, and B606 report a **pattern**, not a defect. B105 fires on a variable name that holds `token`, `secret`, or `password`. `CANCEL_TOKEN = "q"` is a prompt sentinel, not a credential. No fix exists, because no defect exists. A rename from `CANCEL_TOKEN` to `CANCEL_SENTINEL` would silence the rule, but it would spread churn across call sites and would reduce the accuracy of names such as `_TOKEN_ATTR`, which genuinely names a token attribute. Research decision R2 records that trade.

The plan therefore treats each suppression as a claim that needs proof. The triage ledger in [data-model.md](data-model.md) holds the proof. A reviewer who rejects one proof gets a fix instead.

## Project Structure

### Documentation (this feature)

```text
specs/1032-bandit-severity-gate/
├── plan.md              # This file
├── research.md          # Phase 0 output: the eight rule decisions
├── data-model.md        # Phase 1 output: triage entities and the 54-row ledger
├── quickstart.md        # Phase 1 output: how to measure and how to validate
├── contracts/
│   └── suppression-comment.md   # The comment format and the gate command contract
├── checklists/          # Pre-existing
└── tasks.md             # Phase 2 output from /speckit.tasks. This command does not create it.
```

### Source code (repository root)

The work touches 21 source files and 1 workflow file. It creates no file and deletes no file.

```text
.github/workflows/ci.yml                              # Group E: remove -ll and rewrite the step comment

starlink_dashboard.py                                 # Group A: B404 x1, B603 x6, B606 x1, B607 x2
tools/compliance_analyzer/engine.py                   # Group A: B404 x1, B603 x1, B607 x1
tools/ste_linter/parsing/wordcount.py                 # Group B: B105 x1

src/
├── auth/interactive/login_orchestrator.py            # Group C: B110 x1
├── db/redis_writer.py                                # Group B: B105 x1
├── export/
│   ├── data_exporter.py                              # Group D1: B101 x5
│   └── site_insights/device_metric_operation.py      # Group C: B110 x1
├── firmware/
│   ├── firmware_manager.py                           # Group C: B110 x1, Group D1: B101 x4
│   └── site_auto_upgrade.py                          # Group D1: B101 x1, Group D2: B101 x2
├── gateway/
│   ├── _wan2_variable_device.py                      # Group D1: B101 x1
│   └── wan_probe_device_override_manager.py          # Group B: B105 x2
├── maps/
│   ├── _flask_viewer.py                              # Group B: B105 x1
│   ├── plotly_map_figure_builder.py                  # Group B: B105 x3
│   └── plotly_map_templates.py                       # Group D2: B101 x5
├── site/address_audit/ui_geocoder.py                 # Group A: B404 x1, B603 x1
├── utils/
│   ├── logger_utils.py                               # Group C: B110 x1
│   └── zscaler_probe.py                              # Group A: B404 x1, B603 x1. Group C: B110 x1
└── wan_vpn_builder.py                                # Group B: B105 x2

mist-ops-platform/src/                                # Line length 99, not 120
├── api/routes/health.py                              # Group C: B110 x2
└── shared/
    ├── mist/session.py                               # Group B: B105 x1
    └── services/notification.py                      # Group B: B107 x1
```

**Structure Decision**: The work stays inside the existing tree. It adds no package and no module, because the change is a triage of existing lines plus one workflow line. The map above ties each file to its rule group, so a reviewer reads one group at a time.

## Phased approach

Each group ends with a measurement. The implementer re-runs the scan and confirms two facts. The count for that group dropped to zero. No other count changed. A group that does not reach zero blocks the next group.

### Group A - The subprocess family (17 findings, 4 files)

Rules B404, B603, B606, and B607. This group is the most mechanical, so it comes first.

- 13 of the 17 findings sit outside `src/`. They face only `ruff`, `black`, and `bandit`. The risk is the lowest of any group.
- All 3 B607 findings sit outside `src/`. The `shutil.which` resolution therefore never touches `mypy`, `pylint`, `radon`, `vulture`, or the coverage gate.
- Three statements carry both B603 and B607. Each takes one combined comment.
- Every B404 comment follows the model at `MistHelper.py` line 47. The comment names the seam and names the runner.

**Exit measurement**: B404, B603, B606, and B607 each report 0.

### Group B - The credential-string family (12 findings, 8 files)

Rules B105 and B107. The group is mechanical, but it carries a mandatory security check.

- Every one of the 11 B105 findings is a module-level constant whose name holds `TOKEN` or `SECRET`. The implementer must read each value and must record what it is. The categories are a prompt sentinel, a field name, a CSS alpha value, a Vault path, and a delimiter.
- The single B107 finding is the `password: str = ""` default in `EmailAdapter.__init__`. The empty string is a "not provided" sentinel. The precedent sits at `src/ssh/config/env_loader.py` line 67.
- **Stop condition**: If any value turns out to be a real credential, the implementer stops. The implementer then moves the value to the environment and raises a rotation request. No suppression covers a real secret.
- Three findings sit in `mist-ops-platform`. Those comments must fit inside 99 characters.

**Exit measurement**: B105 and B107 each report 0.

### Group C - Silent exception handling (7 findings, 6 files)

Rule B110. This group changes behavior, so it needs the most care of the three suppression groups.

- The default decision narrows the exception type and adds a debug log.
- Two findings escalate to a suppression. `src/utils/logger_utils.py` line 113 sits inside the logging path, so a log call there risks recursion. `src/utils/zscaler_probe.py` line 371 is a best-effort socket close, which the specification names as a valid escalation.
- **Coordination with issue [#1709](https://github.com/jmorrison-juniper/MistHelper/issues/1709)**: The research confirms that none of the 7 findings sit in `MistHelper.py`. Issue #1709 targets the broad `except` blocks in `MistHelper.py`. The overlap that the specification feared does not exist at these line numbers. The implementer still checks the current scope of #1709 before the first edit, because that scope may grow.
- A narrowed exception type adds no branch, so the `radon` complexity score stays flat.

**Exit measurement**: B110 reports 0.

### Group D - Assert statements (18 findings, 5 files)

Rule B101. The group splits into two halves with different decisions.

**D1 - Type narrowing, 11 findings.** The statement exists for `mypy`. It carries no runtime duty, because an earlier guard already proved the value. Requirement FR-010 permits a suppression. The comment must name the guard that proves the value.

Files: `src/export/data_exporter.py` (5), `src/firmware/firmware_manager.py` (4), `src/firmware/site_auto_upgrade.py` line 88 (1), and `src/gateway/_wan2_variable_device.py` line 371 (1).

**D2 - Runtime guards, 7 findings.** The statement protects the user. Python removes it under the `-O` flag. Requirement FR-009 demands an explicit check that raises.

- `src/maps/plotly_map_templates.py` holds 5 asserts inside four `_rule_*` validators. `validate_template` calls them through a rule table and catches nothing. Under `-O` the whole validator becomes a no-op. Each assert becomes a `raise ValueError`. The `validate_template` docstring names `AssertionError` in its `Raises` section, so the docstring changes with the code. The `pydocstyle` gate and the `interrogate` gate read that docstring.
- `src/firmware/site_auto_upgrade.py` lines 54 and 55 sit in the `__post_init__` of the frozen `SiteAutoUpgradeConfig` dataclass. Each `isinstance` check becomes a `raise TypeError`.
- **Verified**: No test asserts `AssertionError` against any of these five files. The existing `validate_template` tests cover the success path only. The exception-type change is therefore safe. The implementer re-runs the affected test files to confirm.
- `pylint` skips `src/maps`, so the D2 work in that directory faces `mypy`, `radon`, `vulture`, and coverage only.

**Exit measurement**: B101 reports 0. The full in-scope count reports 0.

### Group E - The gate change (1 file)

- Remove `-ll` from the bandit step in `.github/workflows/ci.yml`.
- Replace the second comment line. The new comment must state that the gate fails on any severity, per FR-005.
- Keep `-c pyproject.toml` and keep `-r .`, per FR-004.
- Add no confidence filter, per FR-003.
- This group runs last. CI fails while any finding remains, so an earlier flip would block every push in between.

**Exit measurement**: A text search of the bandit step returns no match for `-ll`. The CI bandit job passes.

## Complexity Tracking

| Violation | Why needed | Simpler alternative rejected because |
| - | - | - |
| Principle VII: `src/utils/logger_utils.py` line 113 gets a suppression and no log call | The block sits inside a logging filter. A log call from inside the logging path can re-enter the same filter and can recurse without end. The existing comment already states that the block must never crash the logger. | A debug log is the default decision for B110, and it is unsafe here. A narrowed exception type without a log is the next option. The block must swallow every failure to protect the logger, so narrowing would let an unexpected error escape into the logging path. |
| About 39 of the 54 findings receive a suppression instead of a code change | Rules B101, B105, B107, B404, B603, and B606 report a pattern, not a defect. A prompt sentinel named `CANCEL_TOKEN` holds no credential. No fix exists where no defect exists. | A rename that avoids the rule keyword would remove the finding without a suppression. It would also spread churn across call sites and would make names such as `_TOKEN_ATTR` less accurate. Research decision R2 records the trade. |
| Principle IV runs as a branch and a pull request, not as a direct push to `main` | The multi-agent git workflow governs a change of this size. The change touches 22 files. | A direct push to `main` would skip the review that the "fix over suppress" gate depends on. |
