# Phase 0 Research: getMspInventoryByMac

**Feature**: 583-mist-get-msp-inventory-by-mac
**Source contract**: `documentation/api/msps/GET_msps_msp_id_inventory_device_mac.md`
**Date**: 2026-06-29

This document resolves the five outstanding research questions surfaced by
`/speckit.plan` before Phase 1 design can begin.

---

## Research Task 1: SDK Function Signature & Behavior

- **Decision**: Call `mistapi.api.v1.msps.inventory.getMspInventoryByMac(apisession,
  msp_id, device_mac)` exactly once per invocation. Returns a single object payload
  (not a list, not paginated) describing one device. Accept the response as
  `response.data` (a dict) per the mistapi SDK convention.

- **Rationale**: The enriched per-endpoint doc
  (`documentation/api/msps/GET_msps_msp_id_inventory_device_mac.md`) declares this is a
  non-paginated GET that returns a single device object whose required fields are
  `mac`, `model`, `org_id`, `serial`, `site_id`, `type`, plus optional `for_site`. The
  mistapi SDK exposes the function under
  `mistapi.api.v1.msps.inventory.getMspInventoryByMac` (operationId-cased) and follows
  the same `(apisession, path_param_1, path_param_2)` ordering used by every other
  two-path-parameter GET in the SDK (e.g. `getMspOrgStats`,
  `getOrgInventoryByMac`). The MAC must be passed in the colon-separated lowercase form
  the API expects; the SDK does not normalize for us.

- **Alternatives considered**:
  - **Iterate `getMspInventory` (list endpoint) client-side and filter by MAC** --
    Rejected. That requires pulling potentially thousands of rows for a single lookup,
    burns the 5000-call/hour budget, and defeats the point of the dedicated `by_mac`
    endpoint.
  - **Hit the raw HTTP URL via `apisession.mist_get()`** -- Rejected. We are
    constitution-bound to use the `mistapi` SDK as the sole permitted interface to
    Mist Cloud; bypassing it would break SDK-managed retry, rate-limit, and auth
    behavior.

---

## Research Task 2: Primary Key Strategy

- **Decision**: Use `composite_pk` with `primary_key=['msp_id', 'mac']` and
  `indexes=['org_id', 'site_id', 'model', 'serial', 'type']`. No `timestamp` column is
  needed because the endpoint returns a current-state snapshot, not a time-series row.

- **Rationale**: The response object does NOT include the MSP identifier (only
  `org_id` / `site_id`), and the user-supplied `msp_id` is required context to make
  the row uniquely identifiable across MSPs. `mac` is the only globally unique field
  the API guarantees in the response (it is also marked `required`). The combination
  `(msp_id, mac)` therefore matches the way a junior NOC engineer would re-query the
  table: "which org owns this MAC under this MSP?" `INSERT OR REPLACE` on this
  composite key makes repeated lookups idempotent. Adding `org_id`, `site_id`,
  `model`, `serial`, and `type` as secondary indexes supports the common follow-up
  queries ("show me all devices of model X in my MSP") without forcing a full table
  scan.

- **Alternatives considered**:
  - **Natural PK on `mac` alone** -- Rejected. While `mac` is required, the table is
    keyed within MSP context; if MistHelper is ever pointed at multiple MSPs in the
    same database file, MAC alone is no longer unique because nothing prevents the
    same hardware from being transferred between MSP scopes over time.
  - **Natural PK on `serial`** -- Rejected. `serial` is required but the user query
    pattern is MAC-driven (MAC is what is printed on the shipping label and what the
    user has in hand); keying on `serial` would make upserts harder when the user
    re-runs with the same MAC they just typed.
  - **auto_increment_with_unique** -- Rejected. We have stable, API-provided natural
    keys; introducing a synthetic ID hides duplicate-insert bugs and bloats the SQLite
    file.

---

## Research Task 3: Output Filename and SQLite Table

- **Decision**:
  - Output filename: `data/msp_inventory_by_mac.csv` (and `.json` fallback if
    DataExporter is configured for JSON).
  - SQLite table: `msp_inventory_by_mac`.
  - DataExporter `api_function_name` passed at call site:
    `"getMspInventoryByMac"` (the literal operationId so the upsert path in
    `DataExporter.write_with_format_selection` can find the PK strategy entry).

- **Rationale**: The naming follows the established MistHelper convention -- snake
  case derived from the operationId minus the leading `get`. It groups in `data/`
  next to the existing MSP exports (`msp_inventory.csv` from menu 117) so a NOC
  engineer browsing the folder sees the relationship immediately. The SQLite table
  name matches the file basename, which is also the existing project convention.

- **Alternatives considered**:
  - **`msp_inventory_lookup.csv`** -- Rejected. Loses the `_by_mac` discriminator that
    distinguishes single-record lookups from the bulk list endpoint.
  - **Append to existing `msp_inventory.csv`** -- Rejected. The bulk endpoint and the
    single-MAC endpoint have different operationIds, different PK strategies (the bulk
    endpoint keys on `(msp_id, org_id, mac)`), and different user-query patterns;
    sharing one table would force a more permissive composite PK and confuse the
    SQLite indexes.

---

## Research Task 4: Menu Category Placement and Next Available Menu Number

- **Decision**: Place the new operation in the **Safe Org / MSP Exports** category
  cluster as menu number **96** (the next free integer immediately above the
  Safe-Org-Exports block 51-95 and below the resource-intensive block 97-101).
  Dispatch lives on the `MSPInventoryExporter` class so the menu listing groups it
  visually with menu 117 (the existing MSP inventory bulk export).

- **Rationale**: Per `.github/copilot-instructions.md` and the project's documented
  menu range table, 1-96 is the read-only / safe-export zone, 97-101 is reserved for
  resource-intensive operations, and 124+ is interactive. A single-MAC lookup is
  unambiguously safe and lightweight, so it belongs in the 1-96 band. 96 is the next
  unused integer in that band at the time of writing. If a sibling in-flight branch
  has already claimed 96 by the time `/speckit.tasks` runs, the implementer takes the
  next free integer in the same band without re-running planning.

- **Alternatives considered**:
  - **Slot it next to menu 117 (e.g. 117.5 or 118)** -- Rejected. MistHelper menu
    numbers are integers; inserting at 118 would push or collide with the WebSocket
    operations cluster (102-123).
  - **Wait for the destructive block (154-194)** -- Rejected. The endpoint is
    read-only; placing it in the destructive band would mislead the user into
    expecting a confirmation prompt.

---

## Research Task 5: Required User Prompts (Which IDs from User vs `.env`)

- **Decision**:
  - **From `safe_input()` (user prompt at runtime)**:
    1. `msp_id` -- prompt: `"Enter MSP ID (UUID): "`, context:
       `"msp_inventory_by_mac:msp_id"`. UUID-validated before API call.
    2. `device_mac` -- prompt: `"Enter device MAC (any separator): "`, context:
       `"msp_inventory_by_mac:device_mac"`. Normalized to colon-separated lowercase
       (`aa:bb:cc:dd:ee:ff`) by stripping non-hex chars, lowercasing, and inserting
       colons every two characters; validated as 12 hex digits before the SDK call.
  - **From `.env`**:
    1. `MIST_HOST` (already standard) -- e.g. `api.mist.com`.
    2. `MIST_API_TOKEN` (already standard) -- never echoed.
    3. `MSP_ID` (optional default) -- if set, used as the default for prompt 1 so the
       user can press Enter to accept; behavior matches other MSP-cluster menus.
    4. `MSP_TEST_DEVICE_MAC` (optional, test-only) -- used by `--test` mode to
       supply a known-good MAC without prompting, mirroring the pattern from
       menu 117.

- **Rationale**: The endpoint has exactly two required path parameters, so two
  prompts is the natural minimum. Pulling `msp_id` from `.env` as a default keeps the
  interactive experience fast for the common case (one MSP per operator) while still
  allowing override. Pulling the test MAC from `.env` keeps the `--test` sweep
  non-interactive and parallels the established convention used by adjacent MSP
  operations. The API token and host are never prompted -- they are infrastructure
  configuration, not per-call inputs.

- **Alternatives considered**:
  - **Read MAC from stdin / argv only** -- Rejected. Breaks the menu-driven flow
    junior NOC engineers expect.
  - **Skip UUID / MAC validation and let the API 400** -- Rejected. Constitution
    Principle III (Safety-First) requires we fail fast at the prompt with a
    `WARNING` log rather than burn an API call on malformed input.
