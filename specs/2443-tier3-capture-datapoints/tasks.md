# Tasks: Expose every Tier 3 capture datapoint to operators

**Spec**: [spec.md](./spec.md) · **Plan**: [plan.md](./plan.md) · **Issue**: #2443

## T1 — Inspect existing markup/macro conventions

Read `capture.html` in full and check whether the repo already uses a Jinja
macro/include for repeated table markup. Decide whether to add a macro for the
six Tier 3 tables or copy the existing per-table pattern six times.

## T2 — `capture/tables.py`: add Tier 3 + guest table builders

Add a shared helper that turns `(rows_or_none, reason_or_none, field_list)`
into `(visible_rows, held_count, state)` using the existing `TABLE_ROW_CAP`,
`capped()`, and `readable()` helpers. Add one builder per section (guest,
switch_ports, poe, radios, tunnels, bgp_peers, alarms). Wire all seven into
`page_tables()`'s returned context.

## T3 — `capture/export.py`: add Tier 3 + guest export rows

Add `KIND_*` constants and column lists for the seven new kinds. Extend
`build_rows()` to emit rows for populated ("ok" state) sections only, applying
the existing credential-field filter. Populate the guest kind (already defined
in `CLIENT_GROUPS`, currently unused).

## T4 — `app/routes/capture.py`: wire new context keys

Update `table_context()` to pass through the new keys from `page_tables()` to
the template context. No new business logic expected here.

## T5 — `capture.html`: render the seven new sections

Add Guest clients + six Tier 3 tables after Wireless clients, each with
`data-testid`, capped-note, and three-state empty messaging (not requested /
no rows / reason string), following existing table conventions.

## T6 — Unit tests

Add/extend unit tests for the new `tables.py` and `export.py` builders,
covering: not_requested, no_rows, unavailable (reason string), ok-with-rows,
row-cap-exceeded, and credential-field-filtered cases.

## T7 — Playwright E2E coverage

Extend `tests/e2e/` to start a Tier 3 capture, wait for Verified, and assert
every new table renders with the correct row count and both CSV/JSON exports
contain matching rows per kind. Must fail (not skip) if a section with data is
missing from page or export.

## T8 — Local quality gates

Run `py_compile`, `ruff check`, `black --check`, `mypy`, and `pytest` against
every changed file before building the image.

## T9 — Rebuild image & re-verify live

Rebuild the container image on the fix branch, swap it into `misthelper-app`,
and re-run the full Playwright walk (sign in → org → site → lock → Tier 3
capture → verify) capturing "after" screenshots and export dumps.

## T10 — Update issue #2443 & open PR

Post the "after" evidence to issue #2443. Open a PR with `Closes #2443`,
wait for CI (including CodeQL), then apply the `auto-merge` label.
