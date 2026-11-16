# Tasks: Main workflow recovery

## Consumer configuration

- [x] T001 Confirm the four workflow triggers and the reviewed shared revision. (delivered: .github/workflows/auto-merge.yml)
- [x] T002 Pin the shared recovery and include the STE workflow. (delivered: .github/workflows/auto-merge.yml)
- [x] T003 Extend the existing pin and dispatch-list guard. (delivered: tests/guardrails/test_auto_merge_issue_close.py)
- [x] T004 Add the unique release fragment. (delivered: changelog.d/issue-4763-post-merge-consumer.md)

## Hosted acceptance

- [ ] T005 Observe immediate and delayed consumer behavior after an approved ordinary merge.
  Do not create a test merge or dispatch a workflow solely for acceptance.
