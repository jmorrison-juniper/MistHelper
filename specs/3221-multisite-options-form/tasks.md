# Tasks: Multi-site options form repair

- [x] Read issues #3221, #3207, #3208, and #3206.
- [x] Restore saved multi-site choices in the options view and template.
- [x] Hide and disable family-specific controls in the template and browser script.
- [x] Change the reboot delay placeholder and placeholder style.
- [x] Move request refusal focus to the flash message.
- [x] Map multi-site option errors to page labels.
- [x] Add contract tests for restored choices and label-based refusal text.
- [x] Add browser tests and screenshots for the repaired form behavior.
- [x] Record old-code failure proof.
- [x] Run the new-code test command and quality gates.
- [x] Read issue #3273 and the failed coverage shard of pull request #3272.
- [x] Remove the multi-site labels from `OPTION_HELP`, and add `ORG_OPTION_HELP` for `org_options.html`.
- [x] Add `OrgOptionRefusal` to translate each shared refusal, and name the version control of the refused family.
- [x] Refuse an unreadable canary phase, failure percentage, or start time with the multi-site label.
- [x] Add unit tests that compare `ORG_OPTION_HELP` with the posted fields and the labels of `org_options.html`.
- [x] Record the #3273 old-code failure proof: 1 collection error and 7 route test failures.
- [x] Run the #3273 tests, the browser tests, and the quality gates.
- [ ] Commit, push, open the pull request, and comment on the issues.
