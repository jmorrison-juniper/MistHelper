# Implementation Plan: Show a picker refusal inside the picker page

**Issue**: #3240 | **Spec**: [spec.md](spec.md) | **Research**: [research.md](research.md)

## Summary

The three picker routes answer a browser refusal with a 303 redirect to the
page that corrects the choice. The route flashes the refusal sentence first, so
the next page shows the sentence in the shared message region. A script and a
JSON client keep the JSON envelope.

## Technical context

- Python 3.13 and Flask 3.1. The session is the signed cookie session of
  Flask, so a flashed sentence travels in that cookie.
- `wants_browser_page` in `factory.py` is the one rule that chooses a page or
  JSON for a post.
- `next_page_answer` in `routes/select.py` answers a success. The module
  `org_controls.py` and the module `org_upgrade.py` import it, so this change
  keeps it as it is.
- `partials/flash.html` renders each flashed sentence as
  `<div class="flash-item flash-<level>">`.

## Design

### 1. The class `PickerRefusal` in `routes/select.py`

- `answer(refusal, page_path)` takes the envelope pair that a route built.
  - If `wants_browser_page` is false, it returns the pair unchanged.
  - Otherwise it flashes the sentence with the level `warning`, and it answers
    a 303 redirect to `page_path`.
- `message_of(response)` reads `error.message` out of the envelope body. A
  body with no readable sentence gives one fixed sentence.

### 2. The route changes in `routes/select.py`

- `choose_org` sends the refusal of `org_refusal` through
  `PickerRefusal.answer` with the target `/select/org`. The docstring states the
  new rule.
- `choose_mode` sends a missing organization to `/select/org`, and a missing
  mode to `/select/mode`.
- `choose_sites` reads the site set first. The new helper
  `site_choice_refusal(org_id, chosen)` runs the four checks in the old order.
  It returns the envelope and the target page, or None.
- Each route that this change touches gets inline comments and a log line
  before and after its action.

### 3. Tests

- Contract tests in `tests/contract/upgrade_portal/test_select.py`:
  - Each refusal of each route answers 303 to its target page for a browser.
  - The target page shows the sentence one time, with the class
    `flash-warning`. A second read of the page shows no sentence.
  - A script post keeps the code and the status of each refusal.
  - A refusal keeps the stored organization, the mode, and the site set.
  - `PickerRefusal.message_of` gives the fixed sentence for a body with no
    sentence.
- Browser journeys in `tests/e2e/upgrade_portal/test_picker_refusal_pages.py`:
  - An empty site choice shows the sentence on the site page. The next choice
    opens the options page, and a back step shows the site page.
  - A site identifier that the page script changed shows the unknown site
    sentence.
  - A mode change in a second tab sends the first tab to the mode page.
  - An empty mode choice shows the mode sentence.
  - An empty organization choice shows the organization sentence.

## Risks

- A flashed sentence waits in the session until a page renders it. Each target
  page extends `layout.html`, so the next page always renders it.
- The redirect target is a fixed path of this module. No client text reaches
  the `Location` header.

## Performance

- The change adds one flash write to the session cookie on a refusal only. The
  success path does not change.
- `choose_sites` still reads the site rows one time, and only after the three
  cheap checks pass.

## Constitution check

- The change adds no dependency, no stored field, and no new route.
- The change keeps the JSON contract of every route.
