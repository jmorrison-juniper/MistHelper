# Implementation Plan: The options page shows a real note under each type control

**Issue**: #3381 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

Change one template line so that a `None` warning shows the default note. Add
a contract test with the shipped selection shape, and add a browser check of
each visible note.

## Technical context

- **Language**: Python 3.13 and Jinja.
- **Test tools**: pytest, the Flask test client, and Playwright with the Edge
  channel.
- **Storage**: none changes.

## Constitution check

- **Safety**: the change touches one line of text on a page. No cloud call and
  no firmware write change.
- **5-Item Rule**: the new test helpers keep five blocks or fewer and 25 lines
  or fewer.
- **Inline comments**: each new line of code carries an inline comment.
- **STE**: every new text passes the STE linter at 80 or more.

## Files

| File | Change |
| - | - |
| `src/upgrade_portal/app/assets/templates/upgrade/options.html` | Line 195 uses `default(<text>, true)`. |
| `tests/contract/upgrade_portal/test_upgrade_options.py` | Add a stand-in with the shipped selections, and two tests. |
| `tests/e2e/upgrade_portal/test_upgrade.py` | Read each visible type note in the type control test. |
| `changelog.d/issue-3381-options-none-note.md` | Add the release note. |

## Order of work

1. Add the contract tests. Run them on the old template, and record the red
   result.
2. Change the template line. Run the contract tests green.
3. After pull request #3382 merges, rebase, and add the browser check.
4. Run every gate, the portal suites, and the browser suite.
5. After the merge, deploy the template to port 8056 with a class B reload.

## Risks

- **A test that reads the note text.** The search found no test that reads
  `None` or the note identifier.
- **The overlap with pull request #3382.** That pull request changes
  `test_upgrade.py`. The browser check waits for that merge.
