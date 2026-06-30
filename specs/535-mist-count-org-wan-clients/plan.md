# Implementation Plan: countOrgWanClients

**Branch**: `535-mist-count-org-wan-clients`
**Date**: 2026-06-29
**Spec**: `specs/535-mist-count-org-wan-clients/spec.md`
**Constitution**: `.specify/memory/constitution.md`
**Plan Template**: `.specify/templates/plan-template.md`

## Summary

Add a new MistHelper menu item that invokes the Mist Cloud read-only endpoint
`GET /api/v1/orgs/{org_id}/wan_clients/count` via the `mistapi` SDK function
`mistapi.api.v1.orgs.clients_-_wan.countOrgWanClients()`. The menu collects an
`org_id` (from `.env` or `safe_input()` override), accepts optional `distinct`,
`start`, `end`, `duration`, `limit` query parameters, retrieves aggregated
count buckets, and persists them through
`DataExporter.write_with_format_selection(data, filename, api_function_name=...)`
so CSV, SQLite, and ArangoDB+Redis backends all stay consistent. Inline
comments and action logging are required on every executable line per
Constitution VI and VII.

## Technical Context

| Field | Value |
|-------|-------|
| Language/Version | Python 3.13+ |
| Primary Dependencies | `mistapi` 0.59+, `python-dotenv`, existing `DataExporter`, `safe_input`, `EnhancedSSHRunner` patterns |
| Storage | Local SQLite (`data/mist_data.db`) primary; CSV under `data/` fallback; optional ArangoDB+Redis polyglot |
| Testing | `python -m py_compile MistHelper.py`, `python -m ruff check MistHelper.py`, `python -m black --check MistHelper.py`, `python MistHelper.py --test` (this menu auto-included; not in skip list 14, 18, 63-65, 90-100) |
| Target Platform | Windows 11 native venv and Podman container `ghcr.io/jmorrison-juniper/misthelper:latest` (port 2200 SSH, port 8055 web UI) |
| Project Type | Single-file Python monolith (`MistHelper.py`, ~28K lines) |
| Performance Goals | Single-page request <=5s p95; full retrieval bounded by Mist adaptive delay system (`delay_metrics.json`, `tuning_data.json`) |
| Constraints | Read-only GET; ASCII-only logging; no Unicode; 5-Item Rule (<=25 lines, <=5 params, <=5 nesting blocks); no `input()` outside `safe_input()`; no secrets in logs |
| Scale/Scope | Org-level aggregate count; result row count bounded by Mist `limit` (default 100, max 1000) per call |

No `NEEDS CLARIFICATION` markers remain. All decisions are recorded in `research.md`.

## Constitution Check

Each principle below has an explicit verdict against this plan.

### Principle I -- Multi-Backend Output (NON-NEGOTIABLE)

**Verdict: PASS.** The new menu method calls
`DataExporter.write_with_format_selection(data, filename, api_function_name="countOrgWanClients")`,
inheriting CSV/SQLite/ArangoDB+Redis fan-out used by adjacent menu items.

### Principle II -- Natural Primary Keys (NON-NEGOTIABLE)

**Verdict: PASS.** Strategy `auto_increment_with_unique` registered in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` with a unique tuple
`(org_id, distinct_field, distinct_value, start_epoch, end_epoch)`. Aggregate
counts have no stable natural ID; the surrogate `misthelper_internal_id`
with a unique upsert constraint is the correct pattern documented in
`.github/copilot-instructions.md` for aggregate/summary endpoints (see
`data-model.md`).

### Principle III -- Safe Input Handling (NON-NEGOTIABLE)

**Verdict: PASS.** All prompts use
`safe_input(prompt, context="count_org_wan_clients")` so EOF in SSH/container
sessions exits 0 without a traceback.

### Principle IV -- 5-Item Rule (NON-NEGOTIABLE)

**Verdict: PASS.** Implementation method `run_count_org_wan_clients()` is
<=25 lines, <=5 parameters (`self`, `org_id`, `distinct`, `start`, `end`),
<=5 nesting blocks. Optional `duration` and `limit` are accepted through a
small helper to keep the public method's parameter count bounded.

### Principle V -- ASCII-Only Logging (NON-NEGOTIABLE)

**Verdict: PASS.** All `logging.info` / `logging.debug` strings are ASCII;
no emoji, no Unicode separators.

### Principle VI -- Inline Comments (NON-NEGOTIABLE)

**Verdict: PASS.** Every executable line of the new method, the new strategy
dict entry, and the new menu-table row carries an inline comment explaining
*why*, per the project standard.

### Principle VII -- Action Logging (NON-NEGOTIABLE)

**Verdict: PASS.**
`logging.info("Counting org WAN clients for org %s distinct=%s", org_id, distinct)`
fires before the SDK call;
`logging.debug("countOrgWanClients returned %d rows (total=%s)", len(rows), total)`
fires after, in ASCII only.

### Pre-Phase 0 Gate

**Verdict: PASS.** No principle requires an exception; no
`NEEDS CLARIFICATION` remain in the plan or spec. Proceeding to Phase 0
research.

## Project Structure (this feature)

```
specs/535-mist-count-org-wan-clients/
|-- spec.md                              # Feature spec (already exists, untouched)
|-- plan.md                              # This file
|-- research.md                          # Phase 0 decisions
|-- data-model.md                        # Phase 1 entities + SQLite DDL
|-- quickstart.md                        # Phase 1 dev quickstart
`-- contracts/
    `-- count_org_wan_clients.md         # Phase 1 HTTP + SDK contract
```

## Project Structure (source code)

The new menu method lives in `MistHelper.py`. It is added to the existing
`MistAPIOperations` class (the class that already owns adjacent org-scoped
GET wrappers) -- no new class is justified because the operation is a
single-method read-only call that reuses `self.api`, `self.adaptive_delay`,
and `self.data_exporter` already attached to that class.

Touch points in `MistHelper.py`:

1. `ENDPOINT_PRIMARY_KEY_STRATEGIES` dict (around line ~1672) -- add the
   `"countOrgWanClients"` strategy entry.
2. `MistAPIOperations` class -- add method
   `run_count_org_wan_clients(self, org_id, distinct=None, start=None, end=None)`.
3. Menu dispatch table -- add menu number **230** (next sequential slot in
   the batch reserved for the OpenAPI cataloging series; see `research.md`
   Task 4 for placement rationale).
4. `README.md` menu table -- add row for menu 230.
5. `CHANGELOG.md` -- add entry under the next `version YY.MM.DD.HH.MM` heading.

## Post-Phase 1 Re-Check

After Phase 1 artifacts (`data-model.md`, `quickstart.md`,
`contracts/count_org_wan_clients.md`) were written, all seven principle
verdicts above were re-evaluated against the concrete contract and SQLite
DDL. No verdict flips; no new exception is required. The
`auto_increment_with_unique` strategy survives the schema check, the SDK
signature matches the spec, and the safe-input + logging patterns are
consistent with the adjacent count-endpoint menu items.

### Post-Phase 1 Gate

**Verdict: PASS.** All principles still PASS with the concrete schema and
contract in place. Ready for `/speckit.tasks`.

## Complexity Tracking

| Constitution Principle | Exception Requested | Justification |
|------------------------|---------------------|---------------|
| (none)                 | n/a                 | No exceptions required; plan satisfies all seven principles without compromise. |
