# Implementation Plan: Expose every Tier 3 capture datapoint to operators

**Branch**: `fix/2443-tier3-capture-datapoints` | **Date**: 2026-09-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/2443-tier3-capture-datapoints/spec.md`

## Summary

`capture/extras.py` and the collector already gather guest clients and all six
Tier 3 sections (switch ports, PoE, radios, tunnels, BGP peers, alarms) and store
them in the capture document. The bug is entirely downstream: `capture/tables.py`
never turns that data into page tables, `capture/export.py` never emits export
rows for it, and `capture.html` never renders it. The fix touches four files and
adds a new dataclass shape for Tier 3 row groups, plus Playwright coverage.

## Technical Context

**Language/Version**: Python 3.13+ (unchanged, matches `pyproject.toml`).

**Primary Dependencies**: No new dependency. Reuses `capture/extras.py`'s
existing section constants (`SECTION_SWITCH_PORTS`, `SECTION_POE`,
`SECTION_RADIOS`, `SECTION_TUNNELS`, `SECTION_BGP_PEERS`, `SECTION_ALARMS`) and
field lists (`_SWITCH_PORT_FIELDS`, `_POE_FIELDS`, `_RADIO_FIELDS`).

**Storage**: No schema change. The capture document already stores Tier 3 data;
confirmed live (40,738-byte Verified Tier 3 capture,
`cap-92ee161a3fa24761a4c0b476bdea3412-01`).

**Testing**: `pytest` for unit coverage of the new table/export builders (empty
list, capped list, credential-filtered field, reason-string passthrough).
Playwright E2E coverage extended to assert every Tier 3 section renders on the
page and appears in both CSV and JSON exports for a live Tier 3 capture, and
that the assertion actually fails (not skips) when a section is missing.

**Target Platform**: Same Podman container / Flask app used today; no
infrastructure change.

**Project Type**: Existing web application, `src/upgrade_portal/`.

## Approach by file

1. **`capture/tables.py`**
   - Add a generic Tier 3 section table builder that takes: section constant,
     row list (or `None` if not requested), reason string (if call failed), and
     a field list, and returns `(rows, held_count, state)` where `state` is one
     of `"not_requested"`, `"no_rows"`, `"unavailable"`, or `"ok"` — reusing the
     existing `TABLE_ROW_CAP` / `capped()` / `readable()` helpers.
   - Add a guest-client table builder reusing the existing client-row shape.
   - Extend `page_tables()` to call the new builders for all seven new sections
     and merge their context into the returned mapping (e.g., `guest_rows`,
     `switch_port_rows`, `poe_rows`, `radio_rows`, `tunnel_rows`,
     `bgp_peer_rows`, `alarm_rows`, each paired with a `*_state` /
     `*_held_count` key).

2. **`capture/export.py`**
   - Add `KIND_GUEST`, `KIND_SWITCH_PORT`, `KIND_POE`, `KIND_RADIO`,
     `KIND_TUNNEL`, `KIND_BGP_PEER`, `KIND_ALARM` row kinds.
   - Extend `EXPORT_COLUMNS` with the field lists from `extras.py` for each new
     kind (credential fields excluded via the existing `_readable()` /
     `is_credential_field()` filter).
   - Extend `build_rows()` to call one row builder per new section, following
     the same pattern as `device_rows()` / `client_rows()`, and to populate the
     guest kind (currently defined in `CLIENT_GROUPS` but never populated).
   - Sections with `state in {"not_requested"}` emit no rows (Tier 2 parity);
     `"no_rows"` and `"unavailable"` also emit no rows (nothing to export) —
     only `"ok"` sections with data emit rows.

3. **`app/routes/capture.py`**
   - `table_context()` passes through the new keys returned by
     `page_tables()` unchanged (no new business logic needed here beyond
     wiring).

4. **`app/assets/templates/capture/capture.html`**
   - After the existing Wireless clients table, add: Guest clients table, then
     six Tier 3 section tables (Switch ports, PoE, Radios, Tunnels, BGP peers,
     Alarms), each following the existing table markup pattern
     (`data-testid`, `portal-table`, capped-note, empty-state row) and each
     showing one of three states per FR-003: "Tier 3 not requested for this
     capture.", "No rows.", or the stored reason string.

5. **Tests**
   - `tests/unit/` (or existing unit test location for `capture/`): new tests
     for `tables.py` builders and `export.py` row builders covering all four
     states (not_requested / no_rows / unavailable / ok) and credential
     filtering.
   - `tests/e2e/`: extend or add a Playwright spec that starts a Tier 3
     capture, waits for Verified, and asserts (a) every new table is visible
     with the expected row count, and (b) both CSV and JSON exports contain
     matching row counts per kind. The test must fail, not skip, when data
     exists but a section is absent (i.e., assert on presence, not
     conditionally skip if missing).

## Risks / Mitigations

- **Template bloat**: Six new tables could make `capture.html` unwieldy. Reuse
  a Jinja macro/include for the repeated Tier 3 table markup instead of copy
  pasting six near-identical blocks, if the existing template already uses
  macros elsewhere (check `capture.html`/templates for existing include
  patterns before adding a new one).
- **Radio field ambiguity**: Radio data rides inside Tier 2's `radio_stat`
  device field rather than its own cloud call; ensure the table builder reads
  it from the correct place in the stored document, not from a separate
  Tier-3-only source.
- **Export size growth**: Adding six sections roughly doubles export row
  volume for large sites; the existing `TABLE_ROW_CAP` bounds the on-page
  table but exports should still include the *held* rows (the cap is a
  presentation concern only) unless `extras.py` itself already caps at
  collection time — confirm before deciding whether export bypasses the page
  cap.

## Rollout / Verification

1. Implement in worktree `../MistHelper-2443-tier3` on branch
   `fix/2443-tier3-capture-datapoints`.
2. Run local quality gates (`py_compile`, `ruff check`, `black --check`,
   `mypy`, `pytest`) on every changed file.
3. Rebuild the container image from the branch, swap it into the running
   `misthelper-app` service (same technique used for baseline reproduction),
   and re-run the full Playwright walk (sign in → org → site → lock → Tier 3
   capture → verify) to confirm every section now renders and exports
   correctly. Capture "after" screenshots.
4. Update issue #2443 with the new live-run evidence.
5. Open a PR with `Closes #2443`, wait for CI (including CodeQL), then apply
   `auto-merge`.
