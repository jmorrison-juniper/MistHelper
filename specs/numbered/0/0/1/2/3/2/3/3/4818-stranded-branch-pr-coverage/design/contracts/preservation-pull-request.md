# Contract: Preservation pull request and ledger comment

This contract defines the shape of each preservation pull request, and the shape of each ledger comment on the tracker issue. The rollout must follow it. A pull request that breaks it fails FR-002, FR-003, or FR-009.

## Pull Request Identity

| Field | Required value | Source |
| - | - | - |
| Repository | `jmorrison-juniper/MistHelper` | Fixed |
| Base branch | `main` | Fixed |
| Head branch | The existing remote branch, with its exact name | Batch manifest |
| Head commit | The head commit of the branch at creation, 40 hexadecimal characters | Branch API, `commit.sha` |
| Draft state | Draft | Fixed |
| Labels | `chore` and `ci`, and no other label | Fixed |
| Reviewers | None | Fixed |
| New commits | None. The rollout never pushes to a branch | FR-004 |

## Title

The title uses this form:

```text
chore(git): preserve the head of the branch name
```

The text after `preserve the head of` must be the exact branch name. Never change the branch name. The title must pass the Conventional Commits check that the repository instructions define (RC-112).

## Body

The body has four parts. Each part starts on its own line.

| Part | Content | Rule |
| - | - | - |
| Reference | `Refs #4818` | First line. Must not use a closing keyword |
| Statement | `Preservation only. Do not merge this pull request.` | Fixed text |
| Branch | The branch name, with the word `Branch:` before it | Exact name |
| Head | The head commit, with the words `Head commit:` before it | Equal to the head commit field |
| Count | The commits above `main`, with the words `Commits above main:` before it | At least 1 |

The body must not contain any of these words followed by `#4818`: `Closes`, `Close`, `Closed`, `Fixes`, `Fix`, `Fixed`, `Resolves`, `Resolve`, or `Resolved`. The check in T017 searches each body for these words.

## Ledger Comment

The rollout posts one new comment for each pilot and each batch on issue 4818. A ledger comment has these parts:

| Part | Content |
| - | - |
| Heading | `Pilot` or `Batch` with its two-digit ordinal |
| Table | One row for each pull request: branch, pull request number, head commit, commits above main |
| Gate count | Pilot comments only. The count of new open quality-gate issues |
| Stop rule | The result: `not fired` or the name of the rule that fired |

Rules for ledger comments:

- The rollout posts each ledger comment as new text. It does not edit a previous comment (FR-010).
- Each row uses the exact branch name and the exact head commit.
- The stop rule result must state `not fired` when no rule fired.

## Report Row

The report prints one row for each stranded branch. Each row holds the branch name in backticks, the commits above `main`, and the age in days. The replica writes the same three values for each branch. The rollout uses the report output as the scope (FR-001).
