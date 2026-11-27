# Security Requirements Quality Checklist: Backlog Handoff Recovery

## Credential and Identity Handling

- [x] SEC001 No secret value appears in any record file. The scan TST-35 covers the record folder, and self-review ran it on the draft.
- [x] SEC002 The identity check runs before each GitHub write (FR-018 and decision D-10). The check in TST-01 returns jmorrison-juniper.
- [x] SEC003 The `.env` file of worktree live-deploy-aa0762d stays in place until the owner names a destination (decision D-14 and human decision H-4).

## Write and Destruction Safety

- [x] SEC004 No recovery ref and no archive tag is deleted in this work (FR-011 and SC-006). TST-07 counts them before and after the review.
- [x] SEC005 No Podman volume is pruned (FR-016 and TST-34). The container policy rule at container-deployment.md:50 forbids the removal of production store volumes.
- [x] SEC006 No rollback step uses a force push to main (plan.md, Rollback Steps).
- [x] SEC007 Each GitHub write in tasks T021 and T022 needs an explicit instruction from the orchestrator or the owner. The tasks do not start a write on their own.

## Data Exposure and Scope

- [x] SEC008 The record names the worktree and the file names of the handoff. It names no secret value or credential path.
- [x] SEC009 The record covers only MistHelper. It names no other repository's state, and it defers vmm-topology-automation to its session (decision D-22).
- [x] SEC010 The quickstart commands read GitHub. The only write steps are the tasks T021 and T022, and they run after the identity check.

## Notes

- Every item is checked. SEC001 depends on TST-35, which self-review ran on the draft files. Task T-LOCAL-GATES runs TST-35 again on the committed files.
