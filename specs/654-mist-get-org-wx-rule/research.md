# Phase 0 Research: getOrgWxRule

**Feature**: 654-mist-get-org-wx-rule
**Date**: 2026-07-01
**Source doc**: `documentation/api/orgs/GET_orgs_org_id_wxrules_wxrule_id.md`

## Research Task 1: SDK Function Signature and Behavior

**Decision**: Call `mistapi.api.v1.orgs.wxrules.getOrgWxRule(apisession, org_id,
wxrule_id)` and treat the returned `mistapi.APIResponse` object's `.data` attribute as
a single Python `dict` matching the OpenAPI `Wrule` schema.

**Rationale**: The enriched endpoint doc lists the exact SDK path
`mistapi.api.v1.orgs.wxrules.getOrgWxRule()`, matching the mistapi 0.59+ convention of
one module per URL segment. The endpoint is non-paginated and returns a single JSON
object (not a list), so no pagination loop and no `mistapi.get_all()` helper are
required. The two path parameters (`org_id`, `wxrule_id`) are positional in the SDK
signature. `APIResponse.data` returns the parsed JSON body directly; HTTP status is
available on `.status_code`.

**Alternatives Considered**:
- Using raw `requests` against the URL template: rejected -- violates the constitution
  requirement that all Mist Cloud calls go through the `mistapi` SDK.
- Wrapping the response in `mistapi.get_all()`: rejected -- that helper is for list
  endpoints only and would raise on a single-object response.
- Fetching the full org WxRules list and filtering by id client-side: rejected -- costs
  one extra network round trip and defeats the purpose of exposing the detail endpoint.

## Research Task 2: Primary Key Strategy

**Decision**: Register the operationId `getOrgWxRule` in
`ENDPOINT_PRIMARY_KEY_STRATEGIES` (currently defined near
`MistHelper.py:3462`-`3980`) with `type: "natural_pk"`, `primary_key: ["id"]`,
`indexes: ["org_id", "site_id", "template_id", "order"]`, `unique_constraints: []`,
`description: "Detail of a single organization WxLAN rule"`.

**Rationale**: The response schema exposes a stable `id` UUID that the Mist Cloud
guarantees for the lifetime of the WxRule (identical to the pattern used by
`listOrgWxRules` which is already registered as `natural_pk` on `["id"]` at
`MistHelper.py:3969`). Using the same natural key ensures repeated runs of menu 96
upsert cleanly into the same SQLite row rather than duplicating. Secondary indexes on
`org_id`, `site_id`, `template_id`, and `order` support the common analyst queries
"give me all rules in this template" and "show me rule order for this scope".

**Alternatives Considered**:
- `composite_pk` on `(id, modified_time)`: rejected -- would create a new row every
  time the rule is edited upstream, defeating the upsert model.
- `auto_increment_with_unique` on `misthelper_internal_id`: rejected -- unnecessary
  overhead when a stable natural key already exists in the payload.

## Research Task 3: Output Filename and SQLite Table

**Decision**: CSV/JSON output file `data/org_wxrule_<org_id_short>_<wxrule_id_short>.csv`
(or `.json` per active backend) using the DataExporter default naming convention;
SQLite table name `org_wxrule_detail`.

**Rationale**: The existing `listOrgWxRules` menu emits `data/org_wxrules_<org_id>.csv`
and lands rows in table `org_wxrules`. Following the same stem with the `_detail`
suffix (matches the pattern used by other single-object detail endpoints) makes the
new file discoverable while preventing collision with the list-endpoint output.
`api_function_name="getOrgWxRule"` is passed to
`DataExporter.write_with_format_selection()` so the table lookup keys off the
`ENDPOINT_PRIMARY_KEY_STRATEGIES` entry defined above. The short-UUID suffix in the
filename keeps multiple rules from a single org distinguishable on disk without
producing overly long Windows paths.

**Alternatives Considered**:
- Reusing the `org_wxrules` list-endpoint table: rejected -- mixing single-object
  detail rows with list-scan rows makes analytics ambiguous when a rule is present in
  one but not the other.
- Flat filename `data/wxrule.csv`: rejected -- overwrites across runs and loses org
  context.

## Research Task 4: Menu Category Placement and Next Available Number

**Decision**: Propose menu number **96**. Category: Interactive Safe Viewers (60-96
per `.github/copilot-instructions.md` menu map). Label:
`"Export org WxLAN rule detail (by rule id)"`.

**Rationale**: The 60-96 Interactive Safe range holds site- and org-level viewers
that prompt for one or two IDs and emit a single object or short list -- an exact
behavioral match. Slot 96 is the last free number in the cluster before the
resource-intensive block 97-101; adjacency to menu 84 (`SiteExportUtils.wxrules_usage`)
and menu 82/83 (org/site WxRule list exports) keeps the WxLAN-related items visually
grouped in the menu. If 96 is taken by an in-flight feature branch at task-generation
time, fall back to the next free integer in the same 60-96 cluster.

**Alternatives Considered**:
- Slot 154+ (Destructive range): rejected -- endpoint is strictly read-only.
- Slot 1-59 (Safe Org Exports): rejected -- that cluster is for bulk list exports that
  need no user prompts beyond the org context; this endpoint requires a specific
  rule id and is inherently interactive.

## Research Task 5: Required User Prompts

**Decision**: Two prompts, both via `safe_input()`:

1. `org_id` -- prompt string `"Org UUID [default MIST_ORG_ID from .env]: "`,
   context `"org_wxrule_detail:org_id"`. If the user enters an empty string, fall
   back to `os.getenv("MIST_ORG_ID")`. If both are empty, log a warning and return.
2. `wxrule_id` -- prompt string `"WxRule UUID: "`, context
   `"org_wxrule_detail:wxrule_id"`. No `.env` fallback; the rule id is
   scope-specific and must be supplied per invocation.

Both inputs are stripped, lowercased, and validated against
`re.fullmatch(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
value)` (the existing MistHelper UUID pattern) before the SDK call. Validation
failure logs a warning and returns early.

**Rationale**: `org_id` is stable per user and already pinned in `.env` for CI /
non-interactive test runs -- honoring the `MIST_ORG_ID` default lets `--test` and
`--menu 96` in scripted runs succeed with a single `MIST_TEST_WXRULE_ID` supplied.
`wxrule_id` varies per invocation and has no obvious default, so it stays as a
mandatory prompt. Both prompts use the safety-first `safe_input()` wrapper so SSH
and container EOF exit code 0 without a traceback.

**Alternatives Considered**:
- Reading `wxrule_id` from `.env` too: rejected -- would encourage stale hard-coded
  test rules and mask the interactive UX we want for NOC engineers.
- Fetching the list of WxRules first and letting the user pick by index: rejected --
  doubles the API cost and expands the 25-line method beyond the 5-Item Rule budget;
  the analyst path where the caller already knows the rule id (from a Marvis
  action, an audit log, or an upstream ticket) is the primary use case.
