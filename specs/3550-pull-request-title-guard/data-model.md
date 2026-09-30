# Data Model: Pull request title guard

**Issue**: #3550
**Feature**: [spec.md](spec.md)

These entities describe input and results.
They do not require new model classes, database tables, or persistent storage.
The checker uses local values within its four methods.

## 1. Pull request title

| Field | Type | Rule |
| --- | --- | --- |
| Exact value | String | Preserve every character. Do not trim, normalize, or truncate it. |
| Type | Derived text | Use only one of the nine allowed lowercase types. |
| Scope | Optional derived text | Require a nonblank value without parentheses when present. |
| Breaking marker | Derived Boolean | Allow one `!` immediately before the colon. |
| Description | Derived text | Require nonblank text on one line after a colon and ASCII space. |

The derived fields describe the grammar.
The implementation can decide validity without storing or returning parsed fields.
Reject the forbidden character ranges in the [title contract](contracts/title-check.md).
Unicode text and large descriptions can pass the same grammar.
An available empty string remains a title, even though its decision fails.

## 2. Pull request input

| Field | Type | Rule |
| --- | --- | --- |
| `GITHUB_EVENT_PATH` | Environment string | Require a nonempty path to a readable file. |
| Event content | UTF-8 JSON | Fail on a file, decoding, or JSON error. |
| Event root | Object | Reject another root type. Do not print unrelated fields. |
| `pull_request` | Object | Require this object within the root. |
| `pull_request.title` | String | Require the field and its string type. Preserve empty strings. |

The input owns the source relationship.
One readable input supplies exactly one title.
Actor, author, and draft fields do not affect the decision.
Workflow concurrency uses GitHub context, not additional parsed title data.

## 3. Title result

| Field | Type | Rule |
| --- | --- | --- |
| State | `pass`, `title_failure`, or `input_failure` | Only a valid available title produces `pass`. |
| Checked count | Integer | Use one for a title decision and zero for an input failure. |
| Title representation | Optional JSON string text | Use ASCII double-quoted escapes. Omit it when no title is available. |
| Reason | Fixed ASCII text | Name the title rule or input problem without copying the payload. |
| Exit code | Integer | Use zero for `pass`. Use one for either failure state. |

The result is a process result, not a durable application record.
Stdout identifies the result and count.
Stderr contains structured action records and sanitized exception stacks.
The [title contract](contracts/title-check.md) defines exact stdout.

### State transitions

```text
Start
  -> Read input
     -> Input failure -> Report count 0 -> Exit 1
     -> Exact title available
        -> Valid title -> Report exact title and count 1 -> Exit 0
        -> Invalid title -> Report exact title and count 1 -> Exit 1
```

A title edit starts a new workflow run with a new event file.
The checker does not reuse an older title or result.

## 4. Workflow run

| Field | Type | Rule |
| --- | --- | --- |
| Workflow label | Fixed text | Use `Pull request title`. |
| Job and check name | Fixed text | Use `Conventional Commits PR title`. |
| Activity | Enum | Use the five approved `pull_request` activity types. |
| Concurrency group | Derived text | Combine the workflow label with the head branch or fallback reference. |
| Cancellation decision | Boolean expression | Preserve `refs/heads/main`. Cancel an older run in the same group otherwise. |

One workflow run reads one event and reports one title check.
Runs with different head branches use different groups.
The [workflow contract](contracts/workflow-policy.md) fixes the expressions and permission boundary.

## 5. Dependency update policy

| Field | Type | Rule |
| --- | --- | --- |
| Ecosystem | `pip`, `github-actions`, or `npm` | Preserve all three streams and their order. |
| Directory | Fixed text | Preserve `/`, `/`, and `/ops-portal` respectively. |
| Commit prefix | Fixed text | Use `chore`, `ci`, and `chore(ops-portal)` respectively. |
| Other update settings | Existing mapping | Preserve schedules, limits, labels, groups, ignores, and all other keys. |

Each stream supplies future titles to the common title grammar.
Prefix changes do not rename an existing pull request.
A maintainer must correct an existing invalid bot title.
Do not close that pull request or disable its update stream.

## Persistence and scope

The feature needs no schema migration, cache, API export, or operational store.
It changes no runtime, menu, portal, or database behavior.
Only the issue-owned SpecKit context records planning completion.
