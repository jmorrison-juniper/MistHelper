# Tasks: Org-Level Synthetic Test Probes (Zscaler Destinations)

**Feature Branch**: `1022-org-synthetic-probes`

**Created**: 2026-07-23

**Companion**: `spec.md`, `plan.md`

Tasks are dependency-ordered. `[P]` = parallelisable with the immediately preceding `[P]` task.

## T001 — Verify worktree state and pre-existing artefacts

Verify:
- Working directory is `.claude/worktrees/1022-org-synthetic-probes/`.
- Current branch is `1022-org-synthetic-probes`.
- `data/zscaler_client_connector_probes.json` exists (~4.5 KB, schema_version 1).
- `data/zscaler_cenr_hostnames.json` exists (~22 KB, schema_version 1, 104 proxy + 104 vpn hostnames).
- `specs/1022-org-synthetic-probes/spec.md`, `plan.md`, `tasks.md` exist.

## T002 — Confirm `src/org/` package structure

Check whether `src/org/__init__.py` exists. If not, create an empty one (with a one-line module docstring) so Python can import the new module.

## T003 — Confirm `tests/unit/org/` package structure

Check whether `tests/unit/org/__init__.py` exists. If not, create an empty one.

## T004 — Author `src/org/org_synthetic_probes_manager.py`

Write the module implementing all helpers named in `plan.md §1.2`, using Google-style docstrings per `~/.claude/DOCS.md` (every public/private function documented with a **Why:** section where the summary is not self-evident).

Public API: `manage_org_synthetic_probes(mist_session, org_id: str) -> None`.

Behavior: implements FR-003 through FR-015 verbatim. Module-import must be side-effect free (no top-level I/O, no top-level network, only `import` statements).

## T005 [P] — Author `tests/unit/org/test_org_synthetic_probes_manager.py`

Cover, at minimum, one test per acceptance scenario in `spec.md`:

- `test_build_from_empty_produces_https_prefixed_no_port_targets` (Story 1 / SC-001)
- `test_build_from_empty_skips_wildcards` (FR-008)
- `test_build_from_empty_includes_tunnel_zen_cenr_hostnames` (FR-006)
- `test_merge_dedupes_vlan_union` (Story 2 / SC-002)
- `test_merge_reports_no_changes_when_subset` (Story 2 acceptance #3)
- `test_swap_preserves_foreign_probes` (Story 3 / SC-003)
- `test_swap_replaces_vlan_ids_completely` (Story 3 acceptance #2)
- `test_prompt_rejects_empty_vlan_list`
- `test_prompt_rejects_out_of_range_vlan`
- `test_apply_preserves_synthetic_test_sibling_fields` (FR-015)
- `test_confirm_no_aborts_without_put` (Story 3 acceptance #3)
- `test_missing_source_file_raises_with_clear_message`

Use `unittest.mock.patch` to stub `mistapi.api.v1.orgs.setting.getOrgSettings` / `updateOrgSettings` and `input()`.

## T006 [P] — Register op "206" in `src/utils/operation_registry.py`

Append entry:

```python
"206": {
    "category": "destructive",
    "skip_reason": "DESTRUCTIVE: Modifies org synthetic_test.custom_probes",
},
```

Ensure the alphabetical/numeric ordering matches surrounding entries (numeric keys are grouped near the bottom in existing patterns).

## T007 — Wire the menu entry in `MistHelper.py`

At the top of `MistHelper.py`, guard the import inside a lazy accessor or place it alongside other org-manager imports so that `--help` remains side-effect-free (issue #1641). Then, in the `menu_actions` dict (line ~5755), add:

```python
"206": (
    lambda mist_session, org_id: manage_org_synthetic_probes(mist_session, org_id),
    "Manage org Zscaler synthetic probes",
),
```

The `float(x.replace("a", "."))` sort key already handles "206" correctly.

## T008 — Local quality gate

Run from repo root (inside worktree):

```bash
cd src
pytest tests/unit/org/test_org_synthetic_probes_manager.py -q
pytest tests/unit/test_operation_registry_guardrail.py -q
ruff check .
black --check .
interrogate -c ../pyproject.toml src/org/org_synthetic_probes_manager.py
pydoclint --style=google src/org/org_synthetic_probes_manager.py
```

Fix anything red. Do not proceed to T009 until every gate is green.

## T009 — Regression sanity checks

```bash
python MistHelper.py --help >/dev/null           # exit 0, no side effects (#1641)
```

## T010 — Commit + push

```bash
git add -A
git status
git commit -m "feat(1022): org synthetic_test probes for Zscaler destinations"
git push -u origin 1022-org-synthetic-probes
```

## T011 — Open GitHub issue

Body: link to `specs/1022-org-synthetic-probes/spec.md`; summarize FR-001..FR-017; note the feature is destructive (writes to org settings via PUT).

## T012 — Open draft PR

Base = `main`; head = `1022-org-synthetic-probes`. Reference the issue from T011. Attach the acceptance-scenario checklist so a reviewer can walk each one against the diff.
