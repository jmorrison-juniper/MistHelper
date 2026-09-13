# Implementation Plan: Org-Level Synthetic Test Probes (Zscaler Destinations)

**Feature Branch**: `1022-org-synthetic-probes`

**Created**: 2026-07-23

**Status**: Ready

**Companion**: `spec.md`

## 1. Architecture

```text
MistHelper.py  (menu wire-up + dispatch)
    │
    └─▶ src/org/org_synthetic_probes_manager.py  (this feature — new module)
            │
            ├─ Loads: data/zscaler_client_connector_probes.json
            ├─ Loads: data/zscaler_cenr_hostnames.json
            ├─ Uses:  mistapi.api.v1.orgs.setting.getOrgSettings / updateOrgSettings
            └─ Emits: rich per-probe status via existing logging + stdout

src/utils/operation_registry.py  (append: "206": {"category": "destructive", ...})
tests/unit/org/test_org_synthetic_probes_manager.py  (new)
```

### 1.1 Module boundary

The new module `src/org/org_synthetic_probes_manager.py` exposes a single public callable:

```python
def manage_org_synthetic_probes(mist_session, org_id: str) -> None: ...
```

This mirrors the signature convention of neighbouring org-level exporters/managers in `src/org/` and is what the menu dispatch entry will call.

### 1.2 Internal helpers (all module-private, `_`-prefixed)

- `_load_probe_sources(data_dir: Path) -> tuple[dict, dict]` — read the two curated JSON files, raise a clear error if either is missing/malformed.
- `_prompt_vlan_list() -> list[int]` — prompt loop with per-entry `[0, 4094]` validation; empty list re-prompts.
- `_build_probe_set(sources, vlan_ids) -> dict[str, dict]` — pure function that produces the `custom_probes` dict from the sources and a VLAN list. Skips wildcard entries. Applies `https://` prefix. Emits `name` per FR-010.
- `_detect_existing(setting) -> dict[str, dict]` — extract `synthetic_test.custom_probes` safely, return `{}` if absent.
- `_partition_tool_authored(existing) -> tuple[dict, dict]` — split existing probes into `(tool_authored, foreign)` by name-prefix.
- `_merge_probes(existing_tool, new_probes, extra_vlans) -> dict` — union VLANs on shared names; return the merged tool-authored map.
- `_swap_probes(new_probes) -> dict` — return new_probes unchanged (helper exists for symmetry with `_merge_probes` and to keep the dispatch table readable).
- `_prompt_mode() -> str` — return `"merge"` or `"swap"` from the two-choice prompt.
- `_prompt_confirm(summary: str) -> bool` — yes/no confirmation.
- `_apply(mist_session, org_id, setting, probes) -> None` — construct the PUT body preserving all sibling fields, call `updateOrgSettings`, print per-probe status.

### 1.3 Naming convention (FR-010)

Probe name = `zcc-<role>-<fqdn-slug>` where slug is FQDN with `.` → `-` and lowercased. Examples: `zcc-pac-pac-zscaler-net`, `zcc-tunnel_zen-atl1-sme-zscaler-net`. The `zcc-` prefix is the sole marker used to identify tool-authored probes during merge/swap.

## 2. Dependencies

| Component | Version | Rationale |
|---|---|---|
| Python | ≥3.13 | Project constitution. |
| mistapi | ≥0.63.1 (0.63.3 installed) | `orgs.setting.getOrgSettings` / `updateOrgSettings`. |
| pytest, pytest-cov | (existing) | Unit tests. |
| ruff, black, mypy, interrogate, pydoclint | (existing) | Quality gates. |

**No new third-party dependency is added.** The curated JSON was pre-generated in a prior session and is checked into `data/`; no network fetch happens at menu-runtime.

## 3. Phase Plan

### Phase A — Spec & Data (already complete)

- `data/zscaler_client_connector_probes.json` — authored 2026-07-23 (17 roles, 4 wildcards).
- `data/zscaler_cenr_hostnames.json` — fetched & normalized 2026-07-23 (104 proxy + 104 VPN hostnames).
- `specs/1022-org-synthetic-probes/spec.md` — authored 2026-07-23.
- `specs/1022-org-synthetic-probes/plan.md` — this file.
- `specs/1022-org-synthetic-probes/tasks.md` — see companion.

### Phase B — Module skeleton + tests

1. Create `src/org/__init__.py` if not present (verify first).
2. Create `src/org/org_synthetic_probes_manager.py` with public entry + all `_`-prefixed helpers documented per DOCS.md (Google-style docstrings, ≥90% coverage).
3. Create `tests/unit/org/__init__.py` if not present.
4. Create `tests/unit/org/test_org_synthetic_probes_manager.py` covering: Story 1 build-from-empty, Story 2 merge, Story 3 swap preserving foreign, wildcard skipping, empty-VLAN rejection, no-changes-required, malformed-source-file failure.

### Phase C — Registry + menu wire-up

5. Append `"206": {"category": "destructive", "skip_reason": "DESTRUCTIVE: Modifies org synthetic_test.custom_probes"}` to `src/utils/operation_registry.py`.
6. Import the manager in `MistHelper.py` and add `"206": (lambda mist_session, org_id: manage_org_synthetic_probes(mist_session, org_id), "Manage org Zscaler synthetic probes")` to the `menu_actions` dispatch table (line ~5755).

### Phase D — Quality gates

7. Run `cd src; pytest -q; ruff check .; black --check .; interrogate -c pyproject.toml`.
8. Fix any formatting / coverage issues.
9. Verify `--testinteractive` still walks correctly (op 206 is `destructive`, so it MUST be skipped by the interactive harness — no code change required to achieve this, but verify empirically).
10. Verify `python MistHelper.py --help` still exits without side-effects (issue #1641 guard).

### Phase E — GH artefacts

11. Commit all changes on branch `1022-org-synthetic-probes` (already checked out in worktree).
12. Push branch.
13. Open GitHub issue describing the feature (link to spec.md).
14. Open draft PR referencing the issue.

## 4. Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Concurrent agent edits `MistHelper.py` on main causing merge conflict | Medium | Worktree isolates the branch; conflict resolved at PR time by rebasing on latest main. Menu number 206 is chosen just above the current max (205) — collision only if the other agent also adds a new menu entry, in which case I'll bump to 207 at rebase time. |
| Mist API shape drift under `synthetic_test` sibling fields | Low | FR-015 requires sibling preservation via full-block round-trip; tests assert siblings are retained. |
| Wildcard entries accidentally emitted as probes | Low | `_build_probe_set` explicitly filters entries starting with `*.` and covers this in a unit test. |
| Curated JSON becomes stale as Zscaler updates their list | Medium | Out of scope for this feature. Both source files carry `schema_version` and a `source` string with a fetch date; a follow-up feature can automate refresh. |
| Operator confusion between merge and swap | Low | Two-choice prompt uses full words (`merge` / `swap`); confirmation prompt lists exact per-probe diff before PUT. |

## 5. Traceability

| Requirement | Design element |
|---|---|
| FR-001 (menu entry) | Phase C step 6 — `menu_actions["206"]` in MistHelper.py |
| FR-002 (registry) | Phase C step 5 — `operation_registry.py` "206" |
| FR-003 (VLAN prompt validation) | `_prompt_vlan_list` |
| FR-004 (getOrgSettings) | `manage_org_synthetic_probes` top-level |
| FR-005 (merge/swap prompt) | `_prompt_mode` |
| FR-006 (data sources) | `_load_probe_sources` + `_build_probe_set` |
| FR-007 (https:// prefix, no port) | `_build_probe_set` — hard-coded prefix, no port suffix concatenation |
| FR-008 (wildcard skip) | `_build_probe_set` — filters `startswith("*.")` |
| FR-009 (defaults) | `_build_probe_set` — `type="reachability"`, `aggressiveness="high"` |
| FR-010 (naming convention) | `_build_probe_set` — `zcc-<role>-<slug>` |
| FR-011 (merge behavior) | `_merge_probes` |
| FR-012 (swap behavior) | `_swap_probes` + `_partition_tool_authored` (foreign preserved) |
| FR-013 (confirmation) | `_prompt_confirm` |
| FR-014 (single PUT) | `_apply` — exactly one `updateOrgSettings` call |
| FR-015 (sibling preservation) | `_apply` — copies full setting block, only mutates `synthetic_test.custom_probes` |
| FR-016 (--help side-effect-free) | No import-time side effects added; module import gated inside the menu callable |
| FR-017 (tests) | Phase B step 4 |
