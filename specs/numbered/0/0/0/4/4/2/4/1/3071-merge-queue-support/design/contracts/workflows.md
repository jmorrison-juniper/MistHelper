# Workflow contracts

## Events

Both required workflows accept `merge_group.checks_requested`.
Pull requests retain no branch filter. Push events remain limited to `main`.
Other workflow events remain unchanged.

## Required contexts

Preserve each existing required CI job ID and exact display name.
Preserve the CodeQL caller job, Python language, configuration file, and reusable workflow identity.
The application-owned `CodeQL` context needs live verification after activation.

## Candidate isolation

CI retains `quality-gates-${{ github.event.pull_request.number || github.ref }}`.
CodeQL retains its existing workflow-prefixed equivalent.
Both workflows cancel only superseded pull request runs.
Different queue references cannot share a concurrency group.
Main and queue runs never cancel another run.

Every CI checkout uses the event commit.
The quality job may use the pull request head only for a pull request event.
On a queue event, that expression must fall back to `github.sha`.
The shared CodeQL checkout uses the caller event commit.

## Contract decisions

Tests accept the live workflow and reject missing events, renamed jobs, changed checkout targets, and unsafe cancellation.
Mutation tests alter copies, not repository files.
Missing or malformed source files fail explicitly.
The guard prints examined workflow and context counts.

## Activation

No contract test changes protection or queue settings.
No local result proves the owner-enabled queue accepted a candidate.
Keep #3071 open until live required contexts and protected merges are recorded.
