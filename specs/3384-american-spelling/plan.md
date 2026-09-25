# Implementation Plan: The portal pages use American spelling

**Issue**: #3384 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

Change five lines of two templates to American spelling. Add a contract guard
that reads every template and the portal script for a British spelling.

## Technical context

- **Language**: Python 3.13 and Jinja.
- **Test tools**: pytest.
- **Storage**: none changes.

## Constitution check

- **Safety**: the change touches text only. No cloud call and no firmware
  write change.
- **5-Item Rule**: each new test helper keeps five blocks or fewer and 25
  lines or fewer.
- **Inline comments**: each new line of code carries an inline comment.
- **STE**: every new text passes the STE linter at 80 or more.

## Files

| File | Change |
| - | - |
| `src/upgrade_portal/app/assets/templates/upgrade/options.html` | Four lines use "neighbor" or "neighborhood". |
| `src/upgrade_portal/app/assets/templates/upgrade/confirm.html` | One row name uses "neighbor". |
| `tests/contract/upgrade_portal/test_template_spelling.py` | Add the guard and the two pattern tests. |
| `changelog.d/issue-3384-american-spelling.md` | Add the release note. |

## Order of work

1. Add the guard tests. Run them on the old templates, and record the red
   result.
2. Change the five lines. Run the guard tests green.
3. After pull request #3385 merges, rebase onto main.
4. Run every gate, the portal suites, and the browser suite.
5. After the merge, deploy the two templates to port 8056 with a class B
   reload.

## Risks

- **A test that reads the old text.** The search of `tests/` found the word in
  code comments of other modules only.
- **A false guard hit.** Research Decision 2 lists the words that the guard
  omits and the reason for each word.
