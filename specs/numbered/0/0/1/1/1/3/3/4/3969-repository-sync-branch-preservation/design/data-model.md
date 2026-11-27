# Data Model: Repository Sync Branch Preservation

The record stores no application data. The entities below describe the Git and GitHub objects that the tasks read or change.

## Entities

| Entity | Natural key | Attributes | States |
| - | - | - | - |
| Local branch | Branch name under refs/heads | Tip commit, commits beyond origin/main, merge count, class | Classified, tagged, deleted, kept |
| GitHub branch | Branch name under refs/heads on GitHub | Tip commit | Present, absent |
| Pull request | Pull request number | Head branch name, head commit, state, merged time | Open, merged, closed |
| Preservation tag | Tag name under archive/preservation | Target commit, creation date | Planned, created, pushed, verified |
| Claim | One comment on issue #3969 | Writer name, time in UTC | Absent, recorded, released |
| Container volume | Volume name | Name, presence | Present, removed |

## State transitions

- A class C or class D local branch moves from classified to tagged. Then it moves to deleted.
- A class A, class B, or class E local branch moves from classified to deleted after its gate passes.
- A class F local branch moves from classified to kept. It does not move again.
- A pull request moves from open to merged or closed. This record does not change that state.
- A preservation tag moves from planned to created, then to pushed, then to verified.
- A failed tag check returns the tag to created.
- A claim moves from absent to recorded, then to released.
- A container volume stays present through the refresh. Removal is outside this record.

## Matching rules

- A local branch matches a merged pull request only when its tip equals the pull request head.
- A name match alone does not prove a match. Name reuse occurs across pull requests.
- A branch tag uses the prefix archive/preservation/3969-, the branch slug, and the UTC date.
- A pull request head tag uses the prefix archive/preservation/3969-pr, the pull request number, the word head, and the UTC date.
