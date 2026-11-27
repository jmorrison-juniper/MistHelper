# Handover Checklist: G3 Shared-File Ownership

**Purpose**: Record the G3 state before any change to a shared portal file.
**Status on 2026-11-26**: pending.
**Feature**: [spec.md](../../spec.md)

No owner worktree was read. Each fact below comes from GitHub metadata or from the coordinator comments on issue #4633.

## Facts

- [x] PR #4208 is OPEN. Its head branch is `jmorrison-juniper-4200-migrate-mistwanperformance`. Source: `gh pr view 4208`, read on 2026-11-26.
- [x] PR #4208 changes `web_portal/app.py` and `web_portal/templates/base.html`. Source: the same command, file list.
- [x] PR #4615 merged on 2026-11-13 at 06:20:12Z. It no longer blocks `web_portal/services/data_browser.py`. Source: `gh pr view 4615`.
- [x] The coordinator decision on issue #4633 names account `jmorrison-juniper` as the integration owner. Source: comment of 2026-11-08T23:37:56Z.
- [x] The coordinator decision on issue #4633 names PR #4208 as the blocker for G3. Source: the same comment.
- [x] Issue #4633 requires a fresh ownership check for `web_portal/services/output_scan.py`. Source: the same comment.
- [x] Issue #4648 requires the owner to confirm the exact paths and scope before any edit. Source: issue body, "Constraints / Performance".

## Required before task T009

- [ ] PR #4208 is CLOSED or MERGED. Explained: OPEN on 2026-11-26.
- [ ] The coordinator posts the handover comment on issue #4648. Explained: absent on 2026-11-26.
- [ ] Issues #4636, #4644, #4646, and #4647 are CLOSED. Explained: all four are OPEN on 2026-11-26.
- [ ] The state of `web_portal/services/output_scan.py` is checked again. Explained: the check belongs to the coordinator before any edit to that file. This integration does not edit it.

## Required before task T010

- [ ] Task T009 is merged. Explained: not started.

## Cross-reference

Issue #4224 task T015 names the same two shared files. Task T009 of this record replaces T015 after the handover. Issue #4224 keeps T015 open until then.
