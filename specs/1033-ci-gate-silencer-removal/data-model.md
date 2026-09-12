# Phase 1 Data Model: CI Gate Silencer Removal

**Feature**: `1033-ci-gate-silencer-removal` | **Branch**: `ci/891-893-gate-silencers` | **Date**: 2026-07-28

This feature stores no data at runtime. The entities below are review records. Each one lives in a configuration file, in the pull request body, or in the changelog. A reviewer reads them to answer one question: why does this gate run as it does?

---

## Entity 1: Gate Silencer

A gate silencer is one command line flag or one configuration value that hides a finding from a CI quality gate.

### Fields

| Field | Type | Description |
| - | - | - |
| `issue` | Integer | The GitHub issue that owns the removal. |
| `file` | Path | The file that holds the silencer. |
| `line` | Integer | The line number at the start of this work. |
| `current` | String | The value or flag that CI runs today. |
| `target` | String | The value or flag after this work. |
| `evidence` | String | The measured result that supports the change. |
| `verification` | Command | The command that proves the gate still passes. |
| `measurable_locally` | Boolean | Whether a workstation can produce the result. |

### The ledger

| `issue` | `file` | `line` | `current` | `target` | `evidence` | `measurable_locally` |
| - | - | - | - | - | - | - |
| #891 | `.github/workflows/ci.yml` | 291 | `--ignore=maps,ssh,ui` | The flag is absent. | 757 messages become 1259 messages. Both runs exit 0. | Yes |
| #892 | `.github/workflows/ci.yml` | 35 | `default: '90'` | `default: '70'` | 0 findings at 90 and 0 findings at 70. | Yes |
| #892 | `.github/workflows/ci.yml` | 51 | The `env` fallback value `'90'` | The `env` fallback value `'70'` | 0 findings at 90 and 0 findings at 70. | Yes |
| #893 | `.github/codeql/codeql-config.yml` | 11 to 12 | `exclude: py/clear-text-logging-sensitive-data` | The exclusion is absent, or it returns with a rationale. | Unknown until CI runs. | No |
| #893 | `.github/codeql/codeql-config.yml` | 13 to 14 | `exclude: py/stack-trace-exposure` | The exclusion is absent, or it returns with a rationale. | Unknown until CI runs. | No |

### Validation rules

1. A ledger row reaches a final state only after its `verification` command exits 0 or after the pull request records a CodeQL count.
2. A row with `measurable_locally` set to `Yes` must pass on the workstation before the push. Requirement FR-006 and requirement FR-008 depend on this rule.
3. A row with `measurable_locally` set to `No` must carry a CodeQL run link in the pull request. Requirement FR-014 depends on this rule.
4. No row may reach a final state that holds a silencer without a Review Record. Requirement FR-017 and requirement FR-018 depend on this rule.

---

## Entity 2: Review Record

A review record defends a suppression that survives the feature. The issue #890 precedent defines it. A bare suppression fails review.

### Fields

| Field | Type | Required | Description |
| - | - | - | - |
| `review_date` | Date, `YYYY-MM-DD` | Yes | The date of the review that accepted the suppression. |
| `evidence_link` | URL | Yes | The measurement or the CI run that supports the decision. |
| `next_review_trigger` | String | Yes | The event that forces the next review. |
| `reason` | String | Yes | Why the finding is safe at this site. |

### Validation rules

1. All four fields must hold a value. A missing field fails review.
2. `reason` must state a fact about this repository. A generic word such as "safe" carries no information and fails review.
3. `reason` for `py/clear-text-logging-sensitive-data` must not claim that the tool never logs an actual secret. Issue #1710 contradicts that claim. Requirement FR-016 states this rule.
4. `reason` for `py/clear-text-logging-sensitive-data` must link issue #1710.
5. Every character must be ASCII. Principle V states this rule. The existing comment holds an em dash, so the rewrite replaces it.

### Records that this feature writes

| Site | Record type | Trigger for the next review |
| - | - | - |
| The pylint step in `ci.yml` | A forward-looking rule, not a suppression. | Any future proposal to add an ignore flag. |
| The vulture step in `ci.yml` | A threshold rationale. | Issue #1703 lands and removes the dynamic `mh.*` lookup. |
| `codeql-config.yml`, per surviving exclusion | A full suppression record. | Conditional. See Entity 3. |

---

## Entity 3: CodeQL Query Decision

One decision record exists for each of the two queries. The record starts in the `pending` state and reaches one of three final states.

### Fields

| Field | Type | Description |
| - | - | - |
| `query_id` | String | `py/stack-trace-exposure` or `py/clear-text-logging-sensitive-data`. |
| `query_ran` | Boolean | Whether the default suite executed the query. See research decision R7. |
| `finding_count` | Integer | The number of alerts on the branch. |
| `verdict` | Enum | `clean`, `false_positive`, `real`, or `inert`. |
| `state` | Enum | `pending`, `removed`, or `restored`. |
| `follow_up_issue` | Integer or none | The issue that tracks a fix, when the verdict is `real`. |

### State transitions

```text
pending
  |
  |-- query_ran = false ------------------> inert   -> state = removed, note the finding in the pull request
  |
  |-- query_ran = true, count = 0 --------> clean   -> state = removed
  |
  |-- query_ran = true, count > 0
        |
        |-- the team judges the alerts safe --------> false_positive -> state = restored, write a Review Record
        |
        |-- the team judges an alert real
              |
              |-- a fix fits this feature ----------> real -> state = removed, the fix lands in this pull request
              |
              |-- a fix does not fit ---------------> real -> state = restored, write a Review Record and open a follow-up issue
```

### The decision table

| `query_ran` | `finding_count` | Team judgment | `verdict` | `state` | Required artifact |
| - | - | - | - | - | - |
| No | Not applicable | Not applicable | `inert` | `removed` | A pull request note that the exclusion was always inert. |
| Yes | 0 | Not applicable | `clean` | `removed` | The count and the run link in the pull request. |
| Yes | Greater than 0 | The alerts are false positives. | `false_positive` | `restored` | A Review Record on the restored exclusion. |
| Yes | Greater than 0 | An alert is real and a fix fits. | `real` | `removed` | The fix in this pull request and the count in the body. |
| Yes | Greater than 0 | An alert is real and a fix does not fit. | `real` | `restored` | A Review Record and a follow-up issue linked from the pull request. |

### Validation rules

1. Neither record may stay in the `pending` state when the pull request merges. Requirement FR-014 states this rule.
2. A record in the `restored` state must carry a complete Review Record. Requirement FR-015 states this rule.
3. A record with the verdict `real` and the state `restored` must name a follow-up issue.
4. The two records are independent. One query may end in `removed` while the other ends in `restored`.

---

## Entity 4: Changelog Entry

One entry lives under `## [Unreleased]` in `CHANGELOG.md`. Requirement FR-019 states the rule.

### Fields

| Field | Required | Content |
| - | - | - |
| Heading | Yes | Names all three issues. |
| Pylint result | Yes | The message count before and after, and the gate exit code. |
| Vulture result | Yes | The confidence before and after, the finding count, and the count at confidence 60. |
| CodeQL result | Yes | The finding count for each query and the decision that followed. |
| Follow-up links | Yes | The pylint backlog issue and the reference to issue #1703. |

### Validation rules

1. The entry must not claim a CodeQL result before the CI run produces one.
2. Every sentence must score 80 or above on the Simplified Technical English linter. Requirement FR-022 and success criterion SC-012 state this rule.
3. The entry follows the Keep a Changelog format that the file already uses.
