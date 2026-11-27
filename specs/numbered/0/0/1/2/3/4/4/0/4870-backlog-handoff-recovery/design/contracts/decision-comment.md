# Contract: Decision Comment on Issue 4870

## Location

Each decision comment is a new comment on issue 4870. A new comment never edits an earlier comment. The AGENTS Git flow rule requires a handoff in a comment, and it forbids replacing an earlier comment.

## Heading

The heading reads `## Decisions and state update (YYYY-MM-DD)`. The date is the UTC date of the update.

## Body order

1. A verification line. It gives the full main head SHA, the open issue count, and the open PR count.
2. The section `### Decisions`. It lists only the new decisions. Each item uses the four labels below.
3. The section `### Human decisions`. It lists each new H-n item with its options and its recommended option.
4. The section `### Merges`. Include it only when a merge occurred. Give the PR number, the merge SHA, the head SHA, and the Quality Gates run ID on the new head.
5. The section `### Unverified`. It points to the entries in design/research.md.

## Decision item labels

Each decision item has four labeled lines:

- `Decision`: the choice, in one sentence.
- `Reason`: the evidence, with its check ID.
- `Risk`: the main risk and its mitigation.
- `Human decision`: `yes` or `no`.

## Rules

- Do not write a secret value, a token, or a password in the comment (FR-017).
- Do not paste file contents. Give the path and the blob SHA instead.
- Keep each instruction to 20 words or fewer. Keep each description to 25 words or fewer.
- Use no semicolon, no contraction, and no Latin abbreviation.
- Keep a human decision open until the user answers in a new comment.
- Keep the text ASCII only.
