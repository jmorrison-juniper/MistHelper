# Implementation Plan: The browser seed captures hold the counts of a real capture

**Issue**: #3492 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

The seed captures of the browser tests write a count map of three keys by
hand. A new helper in the seed file, `stand_in_counts`, builds the count map
with the shipped function `build_counts`. The helper reads the device index,
the device records, and the client lists of one capture document.

The function `stand_in_capture` calls the helper for each base seed. The
function `stand_in_tier3_capture` calls it again after it adds the guest
client. No file under `src/` changes.

## Technical context

- Python 3.13, pytest, and Playwright. No new dependency.
- No route change, no schema change, and no change to a JSON body.
- No new cloud read, no new store read, and no new write.
- The direct test reads the five seeds with no browser. The session fixture
  of the folder still starts the browser test server, so each test of the
  folder waits for that server. The direct test replaces the builder with a
  marker to prove that the seed file calls it.
- The browser journey drives the real history page of the browser test
  server. It opens the page with no site and the page of one site. It runs in
  Microsoft Edge on this computer. The CI job "E2E smoke tests" runs it in
  Chromium.

## Constitution check

| Principle | Result |
| - | - |
| I. Five-item rule | Pass. The new helper takes one parameter and holds fewer than 25 lines. Each new test function takes five parameters or fewer. |
| II. Class-based design | Pass. The seed file keeps its builder functions, which is the convention of the fixtures. The helper maps a document to the sections of the builder, so it is not a wrapper. |
| III. Safety first | Pass. The change touches test files only, and it adds no write to a real store. |
| IV. Full pipeline | Pass. Tests, gates, a pull request, and a hand merge. No deploy, because the portal code does not change. |
| V. Observability | Pass. The helper logs before and after it builds the map. The journey logs each measured width. |
| VI. Inline comments | Pass. Each new line carries a comment. |
| VII. Action logging | Pass. The count build is the only new action, and it logs. |

`MistHelper.py` does not change.

## Files

| File | Change |
| - | - |
| `tests/e2e/upgrade_portal/conftest.py` | The new helper `stand_in_counts`. The function `stand_in_capture` calls it. The function `stand_in_tier3_capture` calls it after the guest list. |
| `tests/e2e/upgrade_portal/test_seed_counts.py` | New. The direct test of the five count maps and the marker test. It holds no browser import. |
| `tests/e2e/upgrade_portal/test_history_device_types_journey.py` | New. The browser journey of the device type cells, the Clients cell of the Tier 3 row, and the row height at three widths on the two history pages. |

## Test plan

1. Write the new tests first. Run them on the old seed, and record the red
   result.
2. Change the seed file. Run the new tests green.
3. Read each screenshot of the browser journey. Record the measured widths in
   the research.
4. Run every test under `tests/e2e/upgrade_portal/`, as the Caution of the
   issue asks. Explain or fix each changed result.

## Gates

py_compile, ruff, black, mypy (the `MYPY_PATHS` of `ci.yml`), and the test
quality gate of the new test files. Also run the STE lint of each new
Markdown file.

## Release note

The change touches test files and specification files only. An operator sees
no change, so the change adds no fragment under `changelog.d/`. The pull
request body states this reason.

## Overlap

The draft pull request #3264 also changes `tests/e2e/upgrade_portal/conftest.py`.
This change takes the file first. Pull request #3264 rebases after this merge.

## Deploy

No deploy. The portal on port 8056 runs no test file.
