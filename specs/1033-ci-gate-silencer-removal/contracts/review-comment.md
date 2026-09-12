# Contract: The review comment and the gate commands

**Feature**: `1033-ci-gate-silencer-removal` | **Date**: 2026-07-28

This feature exposes two contracts. A future maintainer reads the first one in a configuration file. A CI job runs the second one.

---

## Contract 1 - The review comment

### Purpose

A review comment is the only record of why a gate runs as it does. Success criterion SC-009 requires that a reviewer names the reason without asking the author. The reviewer reads only the file that holds the setting.

Issue #890 set this format. This feature reuses it without change.

### The three required facts

| Fact | Requirement |
| - | - |
| The review date | The date in `YYYY-MM-DD` form. |
| A link to the evidence | A CI run, a measurement, or an upstream tracker. |
| The next review trigger | The event that forces the next review. |

A suppression that omits any fact fails review. Requirement FR-018 states this rule.

### Format rules

| Rule | Reason |
| - | - |
| The comment sits directly above the setting that it defends. | A reader finds it without a search. |
| Every character is ASCII. The separator is a hyphen, not an em dash. | Principle V requires ASCII. |
| The reason states a fact about this repository. | A generic word such as "safe" carries no information. |
| The comment holds no claim that a measurement contradicts. | Requirement FR-016 states this rule for the logging query. |
| Each line stays inside 100 characters. | A long YAML comment wraps badly in a diff view. |
| The prose follows Simplified Technical English. | Requirement FR-022 states this rule. |

### Accepted example: a threshold rationale

```yaml
      # Dead code gate. Reviewed 2026-07-28 for issue #892.
      # Measured on this checkout: confidence 90 reports 0 findings, confidence 70
      # reports 0 findings, and confidence 60 reports 306 findings. The floor sits at 70,
      # because the cliff between 70 and 60 is a false positive cliff, not a defect cliff.
      # Two patterns drive that rate. The first is module level dependency injection.
      # The second is a dynamic mh.* lookup that vulture cannot resolve.
      # Next review: issue #1703 removes the second pattern. Re-measure at confidence 60
      # after that issue lands. A later slice owns the move to 60.
      - name: Detect dead code
        run: vulture ${{ env.SRC_PATH }} --min-confidence ${{ env.VULTURE_CONFIDENCE }}
```

### Accepted example: a forward-looking rule

```yaml
      # Pylint reads every package under SRC_PATH. Reviewed 2026-07-28 for issue #891.
      # The step ran with --ignore=maps,ssh,ui until this date. That flag hid 502 messages
      # from src/maps, src/ssh, and src/ui. The measured run without the flag reports
      # 1259 messages and still exits 0 at the 9.5 threshold.
      # Before you add a new --ignore entry, record three facts in a comment: the date of
      # the review, a link to the evidence, and the condition that triggers the next review.
      - name: Run Pylint
        run: pylint ${{ env.SRC_PATH }} --fail-under=${{ env.PYLINT_THRESHOLD }}
```

### Accepted example: a restored CodeQL exclusion

The implementer writes this block only when the CodeQL evidence supports it. The placeholders take real values from the run.

```yaml
# Exclude the py/stack-trace-exposure query.
# Reviewed <YYYY-MM-DD> for issue #893.
# Evidence: CodeQL run <URL> reported <N> alerts on branch ci/891-893-gate-silencers.
# Reason: <one sentence that states why each alert is safe at its site>.
# Next review: <the event that forces the next review>.
query-filters:
  - exclude:
      id: py/stack-trace-exposure
```

### Rejected examples

| Example | Why it fails |
| - | - |
| An exclusion with no comment above it. | It carries none of the three facts. Requirement FR-017 forbids it. |
| A comment that states a reason and no date. | A reader cannot tell whether the reason is current. |
| A comment that states a date and no evidence link. | A reader cannot check the claim. |
| A comment that states a date and a link and no trigger. | The suppression never expires and never returns for review. |
| "No passwords, API tokens, or actual secrets are ever logged." | Issue #1710 found a partial API token value in `data/script.log`. Requirement FR-016 forbids this claim. |
| A comment that uses an em dash as a separator. | Principle V requires ASCII. |

---

## Contract 2 - The gate commands

### The pylint gate

**Command after this work**:

```text
pylint ${{ env.SRC_PATH }} --fail-under=${{ env.PYLINT_THRESHOLD }}
```

| Property | Value |
| - | - |
| Exit code on success | 0 |
| Timeout | 10 minutes, unchanged |
| Threshold | 9.5, unchanged |
| Scope | `src/`, unchanged |
| Forbidden flag | Any `--ignore` value without a Review Record |

The job log must hold at least one message for `src/maps`, at least one for `src/ssh`, and at least one for `src/ui`. Success criterion SC-001 states this rule.

### The vulture gate

**Command after this work**:

```text
vulture ${{ env.SRC_PATH }} --min-confidence ${{ env.VULTURE_CONFIDENCE }}
```

The command text does not change. The value behind `VULTURE_CONFIDENCE` changes.

| Property | Value |
| - | - |
| Exit code on success | 0 |
| Timeout | 5 minutes, unchanged |
| Confidence floor | 70, changed from 90 |
| Expected findings | 0 |
| Forbidden value | Any floor above 70 without a Review Record |

A future pull request that adds unreachable code at confidence 70 or above must fail this job. The log must name the file and the symbol. Acceptance scenario 4 of User Story 2 states this rule.

### The CodeQL gate

**Configuration after this work, when both queries end in the `removed` state**:

```yaml
name: "MistHelper CodeQL Configuration"
```

| Property | Value |
| - | - |
| Query suite | The default suite, unchanged |
| Trigger | `pull_request` against `main`, `push` to `main`, and a weekly schedule |
| Allowed exclusion | Only an exclusion that carries a complete Review Record |
| Forbidden state | A `query-filters` key with a `null` value |

The file holds no `query-filters` key when no exclusion survives. Research decision R4 states the reason.

### The prose gate

Every changed prose file must pass the Simplified Technical English linter.

```powershell
.venv\Scripts\python.exe -m tools.ste_linter <path>
```

| Property | Value |
| - | - |
| Minimum score | 80 |
| Scope | Every new sentence and every changed sentence |

Requirement FR-022 and success criterion SC-012 state this rule.
