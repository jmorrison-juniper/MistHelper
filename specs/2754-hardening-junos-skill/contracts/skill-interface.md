# Contract: The skill interface

**File**: `.github/skills/hardening-junos/SKILL.md`

**Consumers**: The agent runtime that loads a skill. The engineer who reads the answer.

**Date**: 2026-09-16

## Front matter

The router file starts with YAML front matter. The 3 fields match every other skill in
`.github/skills/`.

```yaml
---
name: hardening-junos
description: >-
  Use when you harden a Junos device ...
argument-hint: Describe the platform, the Junos train, and the control or the configuration to review.
---
```

| Field | Rule |
| - | - |
| `name` | It must equal the folder name `hardening-junos`. |
| `description` | It states when to use the skill. It names the platforms, the checklist, and the DISA STIG bundle. |
| `argument-hint` | One sentence. It asks for the platform, the train, and the task. |

## Routing table

`SKILL.md` holds one routing table. Each row gives a task, a reference file, and the required
result. This matches `managing-mist-api`.

| Task | Reference | Required result |
| - | - | - |
| Apply a hardening control from the checklist. | `references/baseline-controls.md` | The control, the Junos command, the reason, the risk, and the citation. |
| Answer a DISA STIG question or map a failure to a rule. | `references/stig-rules.md` | The rule identifier, the severity, the check, and the fix. |
| Find the source document for a control. | `references/corpus-index.csv` | The title, the train, the page count, and the relative path. |
| Search the corpus, refresh the index, or read the gap register. | `references/corpus-operations.md` | The search procedure or the refresh procedure with its acceptance rules. |
| Prove that the skill and its citations are correct. | `references/verification.md` | The command and the expected result for each check. |

## Answer contract

Every answer holds these parts. A missing part is a defect.

| # | Part | Rule |
| - | - | - |
| A1 | Control | One sentence that states the control. |
| A2 | Junos command | The configuration syntax, the platform, and the train. |
| A3 | Reason | Why the control reduces risk. |
| A4 | Citation | The document, the train, the public URL when one exists, and the relative path below the corpus root. |
| A5 | Evidence command | The `show` command that proves the state of the device. |
| A6 | Lockout warning | It comes before the command, when the control can remove access. |
| A7 | Recovery step | It follows the warning, when a warning exists. |

### Citation rule

Warning: an answer must never cite a path below `documentation/references/`. `.gitignore` line
28 ignores that directory, because it holds verbatim vendor text. A clone and a new worktree
do not receive it.

The skill cites 3 kinds of place.

1. A public URL. Every reader can open it.
2. A path below the corpus root. A reader with the staged corpus can open it.
3. A committed repository path, such as `documentation/noc-runbooks/`.

Each reference file ends with a `Sources` section. That section gives a `Source` and `Where`
table, which matches section 14 of `documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md`.
The section states that the vendor text is not committed, and it names the rebuild command.

### Order rule

A warning comes before the instruction that causes the risk. This follows the STE warning
rule and Principle III of the constitution.

## Condition contracts

| Condition | Required behavior | Source |
| - | - | - |
| The corpus root is absent. | State that the corpus is absent. Give the title, the train, and the public URL. Answer from the curated references. Do not fail. | SC-007 |
| The answer comes from outside the security subset. | State that the source is outside the security subset. | FR-009 |
| The cited document is in the gap register. | State the gap and the fallback train. | FR-047 |
| A document has no Junos train. | State the archive and its product version. State that the document has no train. | Decision 5 |
| Two trains disagree. | Give the newest readable statement first. State that an older train differs. Give both trains. | Edge case list |
| No source exists. | State that the skill found no source. Give no invented answer. | FR-001 acceptance scenario 3 |
| A DISA rule has no Juniper source. | Give the rule alone. State that no matching Juniper document exists. | Edge case list |
| The user asks the skill to change a device. | Refuse. Give the configuration text and the reason. State that a human applies it. | FR-049 |
| The user asks the skill to commit the corpus. | Refuse. State that the repository holds the skill files only. | Edge case list |
| The corpus holds a partial conversion. | Compare the index against the conversion manifest. Report the count of missing files. | Edge case list |

## Configuration review contract

User story 2 asks for a review of a configuration file. The review holds one result for each
of the 67 controls.

| Result | Meaning |
| - | - |
| `pass` | The configuration holds the control. |
| `fail` | The configuration contradicts the control. The result gives the matching STIG rule and its severity. |
| `not-assessable` | The file cannot show the control. The result states the evidence that the review needs. |

The review states that it is advice. The review states that it changed no device.

## Size and shape rules

| Rule | Value | Source |
| - | - | - |
| Router file size | 12 KB or less | FR-002 |
| Reference folder width | 5 children or less | Five-Item Rule |
| Skill file count | 10 or less. The plan ships 6. | FR-005 |
| Single file size | 90 KB or less | FR-006 |
| Total size | 400 KB or less | FR-005 |
| Writing score | 80 or more for each Markdown file | FR-051 |
| Snapshot statement | Each file states the date of 2026-09-16 and the counts | FR-053 |
