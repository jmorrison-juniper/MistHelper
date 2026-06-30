# Contract: `MistUIGeocoder` (Tier 3, optional Playwright "hijack")

Resolves OQ-001 and OQ-002. This tier is OFF by default, enabled only by
`--ui-geocode`, invoked selectively (e.g. `AMBIGUOUS` rows), and MUST fail soft.

> **Status**: connection foundation IMPLEMENTED and verified
> (`src/site/address_audit/ui_geocoder.py`, `models.py`). Both connection modes
> below were proven end-to-end against the system browser on 2026-06-29. The
> per-row resolver wiring (selective invocation from `AddressResolver`) lands
> with the full feature implementation.

---

## Environment constraint (verified)

On a Zscaler SSL-inspected Windows host, **Playwright cannot download its own
Chromium** (`UNABLE_TO_GET_ISSUER_CERT_LOCALLY` from the Playwright CDN -- same
root cause as the documented GHCR-push block). Therefore this tier MUST drive a
**system-installed browser**, never a Playwright-bundled one:

- `chromium.launch(channel="msedge")` (or `"chrome"`) uses the OS browser -- no download.
- `chromium.connect_over_cdp(...)` attaches to a browser the OS already has.

The host used for verification has **Microsoft Edge** (Chromium) and no Chrome,
so `browser_channel` defaults to `"msedge"`.

---

## Connection modes (OQ-001 -> resolved)

Configured via `UIGeocoderConfig.connect_mode`:

**1. `attach` (DEFAULT, recommended) -- CDP takeover.** Reuse a browser the
operator already has open and logged into Mist. The operator (or
`MistUIGeocoder.spawn_debuggable_browser()`) starts Edge with
`--remote-debugging-port=9222` and a throwaway `--user-data-dir`; the tier calls
`connect_over_cdp("http://localhost:9222")` and reuses `browser.contexts[0]` --
the live SSO session, cookies intact. **No credentials stored in `.env`; no new
secrets; no re-auth per run.** This is the cleanest fit for SSO/MFA dashboards.

**2. `launch` -- fresh system Edge + interactive login.** `chromium.launch(
channel="msedge", headless=False)`, navigate to `dashboard_url`, then block on a
`InputUtils.safe_input()` "press Enter when logged in" gate before the first
lookup.

Deferred opt-ins (documented, NOT built in v1):
- scripted login from `.env` dashboard credentials,
- reuse of the operator's *default* browser profile / cookie jar (we use an
  isolated throwaway profile instead, to avoid touching their real session).

---

## Selectors (anchored on Google, not Mist)

The Location Search field is a **Google Places Autocomplete** widget ("powered
by Google"). The implementation anchors on Google's own stable classes rather
than Mist's surrounding markup:

- Input candidates (first match wins): `input.pac-target-input` ->
  `input[placeholder*='Location Search']` -> `input[placeholder*='Location']`.
- Suggestion rows: `.pac-container .pac-item`.

These `.pac-*` classes are emitted by Google's JS and are far more stable than
Mist's DOM. Constants are dated at the top of `ui_geocoder.py`; see the
re-capture procedure below.

---

## Lookup behavior

Input: a query string `"{business_name} {address}"` (or raw address if no business
name). Steps:
1. Open/focus the site-edit **address autocomplete** field (selector candidates above).
2. Type the query (with a small per-key delay so Google fires autocomplete).
3. Wait for the Google-Places suggestion dropdown (bounded by per-lookup timeout).
4. Capture the top suggestion text; capture additional suggestions to detect ambiguity.

The tier **never commits** a change (read-only): it reads the suggestion text and
backs out. Output: `ResolverResult(source="mist_ui", canonical_address=<top
suggestion>, confidence=0.9 single / 0.6 ambiguous, raw_response={suggestions,
ambiguous})`, or `None` on any failure.

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
