# Contract: `MistUIGeocoder` (Tier 3, optional Playwright "hijack")

Resolves OQ-001 and OQ-002. This tier is OFF by default, enabled only by
`--ui-geocode`, invoked selectively (e.g. `AMBIGUOUS` rows), and MUST fail soft.

---

## Authentication (OQ-001 -> resolved)

**v1 = interactive operator login.** At run start (when `--ui-geocode` set), launch
a non-headless Playwright browser, navigate to the Mist dashboard login, and pause
for the operator to authenticate manually. No credentials stored in `.env`; no new
secrets. The audit proceeds once the operator confirms the session is ready (via a
`safe_input()` "press Enter when logged in" gate).

Deferred opt-ins (documented, NOT built in v1):
- (b) scripted login from `.env` dashboard credentials,
- (c) reuse of an existing browser profile / cookie jar.

---

## Lookup behavior

Input: a query string `"{business_name} {address}"` (or raw address if no business
name). Steps:
1. Open/focus the site-edit **address autocomplete** field.
2. Type the query.
3. Wait for the Google-Places suggestion dropdown (bounded by per-lookup timeout).
4. Capture the top suggestion text; capture additional suggestions to detect ambiguity.

Output: `ResolverResult(source="mist_ui", canonical_address=<top suggestion>,
ambiguous=<len(suggestions) > 1>)`, or `None` on any failure.

---

## Bounds (configurable via `.env`)

| Bound | Default | Env key |
|-------|---------|---------|
| Per-lookup timeout | 20 s | `UI_GEOCODE_TIMEOUT_SECONDS` |
| Max lookups per run | 50 | `UI_GEOCODE_MAX_LOOKUPS` |

When the max-lookups cap is reached, remaining eligible rows skip Tier 3 (logged)
and fall back to their Tier 1/2 outcome.

---

## Fail-soft (OQ-002 -> resolved)

Any selector miss, timeout, navigation error, or exception:
- log a WARNING with context (never the session/credentials),
- return `None` so the row classifies `NO_RESULT` (or `AMBIGUOUS` when multiple
  suggestions were seen before failure),
- NEVER raise out of the audit loop. One flaky lookup must not abort the run.

---

## Selector capture + re-capture procedure (OQ-002)

The dashboard DOM is **not contract-stable**. The implementation MUST:
1. Centralize selectors as named constants at the top of `ui_geocoder.py` with a
   dated comment (e.g. `# captured 2026-06-29; re-verify if dashboard UI changes`).
2. Document the re-capture procedure inline:
   - open the Mist site-edit page in a browser,
   - inspect the address autocomplete input + suggestion list elements,
   - update the selector constants,
   - run the Tier 3 e2e test (`tests/e2e/`, reuse `gunicorn_server` fixture where
     applicable) to confirm capture.
3. Prefer role/label/placeholder-based locators over brittle CSS/XPath where possible.

---

## Testing

- Unit: `MistUIGeocoder` is NOT invoked unless `ui_geocode=True` is passed (mock
  Playwright; assert not called by default) -- see `test_address_resolver.py`.
- e2e (optional, only where a UI tier test is warranted): reuse existing
  `tests/e2e/` infra and the `gunicorn_server` fixture; mark slow/skippable so the
  default unit suite stays fast and deterministic.
