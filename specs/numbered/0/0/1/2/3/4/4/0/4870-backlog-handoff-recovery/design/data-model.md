# Data Model: Backlog Handoff Recovery

Each entity uses a natural key from GitHub or from the repository. No entity uses an artificial identifier.

## BacklogIssue

- **Natural key**: the issue number in `jmorrison-juniper/MistHelper`.
- **Attributes**: number, title, label names, state (OPEN or CLOSED), census category, next action, and check date.
- **Census categories**: fix-now-candidate, fix-in-progress, held-reservation, held-staging-or-credentials, needs-human-decision, owner-decision, stale-or-superseded, unknown, and not classified. These names come from the inventory comment.
- **Transitions**: OPEN to CLOSED on a merge with a closing reference or on a manual close. CLOSED to OPEN on a manual reopen, as issue 4762 shows (R-08).
- **Rule**: An open issue without a category stays unclassified until task T023 assigns one.

## PullRequest

- **Natural key**: the PR number in `jmorrison-juniper/MistHelper`.
- **Attributes**: number, title, draft flag, merge state, head SHA, merge commit SHA, and closing references.
- **Transitions**: draft to ready on an owner action. OPEN to MERGED only through task T-MERGE. OPEN to CLOSED unmerged, as PR 4831 shows (R-22). MERGED is final.
- **Rule**: A merge needs merge state CLEAN, a green Quality Gates run on the head, and a passing hold-phrase check.

## RecoveryBranch

- **Natural key**: the full ref name, for example `refs/heads/recovery/jmorrison-juniper-3726-ambiguous-upgrade-submission-wip-20261122`.
- **Attributes**: ref name, tip SHA, linked issue number when the handoff names one, and review decision.
- **Review decisions**: none, keep, copy, or delete. The record sets no decision.
- **Transitions**: exists and unreviewed to reviewed-keep, reviewed-copy, or reviewed-delete. Each transition needs a recorded decision in a later task.
- **Rule**: This record deletes no ref (FR-011). A copy keeps the original ref.

## ArchiveTag

- **Natural key**: the full tag name under `archive/`.
- **Attributes**: tag name and target SHA.
- **Transitions**: exists to kept. The default state is kept. This record deletes no tag.

## CommitTip

- **Natural key**: the full 40-character commit SHA.
- **Attributes**: local branch name from comment 1, and a flag that shows whether GitHub holds the SHA.
- **Transitions**: local only to on GitHub after a push.
- **Rule**: A local branch or worktree can be removed only after its tip exists on GitHub (FR-012).

## Decision

- **Natural key**: the decision ID, D-1 to D-22.
- **Attributes**: topic, decision text, alternatives, reason, risk, and the human flag.
- **Transitions**: proposed to decided to recorded. A recorded decision has a dated comment on issue 4870.
- **Rule**: A decision with the human flag set moves to HumanDecision and waits for the user.

## HumanDecision

- **Natural key**: the human decision ID, H-1 to H-4.
- **Mapping**: H-1 maps to D-2, H-2 maps to D-12, H-3 maps to D-13, and H-4 maps to D-14.
- **Transitions**: asked to answered to recorded. The answer comes from the user only.
- **Rule**: No agent answers a human decision (FR-015).

## MergeSlot

- **Natural key**: the repository name and the single merge slot.
- **States**: idle, candidate, green, merging, merged, and idle again.
- **Transitions**: idle to candidate when one PR starts its checks. Candidate to green when CI succeeds on the head. Green to merging when the orchestrator authorizes. Merging to merged when main moves. Merged to idle after the next Quality Gates run succeeds.
- **Rule**: One candidate holds the slot at a time. Handoff section 3 and the serialized merge rule in documentation/quality-gates.md (line 116) require it.

## DevtoolsPin

- **Natural key**: the file path and the line number of the pin.
- **Attributes**: the commit SHA and any annotation comment.
- **Transitions**: 79a5e459 or d63a1204 to 2239e7bd for each workflow uses line (task T027). The three Python pins already name 2239e7bd (R-46 to R-48).
- **Rule**: The Python pins and the workflow uses lines name one commit after task T027 (FR-008).
