# Analysis: Main workflow recovery

The reviewed shared revision reports a confirmed merge separately from an enabled pending request.
Its dispatch job requires a confirmed merge for the immediate path.
It also retains the schedule, manual, and merged-close paths and uses `!cancelled()`.
The pull request paths require the configured default branch.

The four consumer workflow files accept `workflow_dispatch` and pushes to main.
The container push trigger also has a path filter.
The existing recovery list already includes the container workflow without that filter.
This change preserves that behavior and adds the missing STE workflow.

The consumer guard checks the exact pinned revision and exact workflow list.
It also checks the dispatch and main push triggers for each named file.
Those checks do not prove hosted dispatch timing or a delayed merge.
The shared recovery checks the current default-branch tip.
A later tip cannot prove that an earlier merge had a run.

The Spec Kit branch hook was not run because this worktree already has its assigned branch.
The feature selector was not changed.
The managed route came from the numeric dry run for issue #4763.
