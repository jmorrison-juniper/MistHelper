# Feature Specification: Org-Level Synthetic Test Probes (Zscaler Destinations)

**Feature Branch**: `1022-org-synthetic-probes`

**Created**: 2026-07-23

**Status**: Draft

**Input**: User description: "Add a new MistHelper menu option that lets an operator create/manage org-level `synthetic_test` custom probes for Zscaler Client Connector destinations. Prompt for VLAN list; if probes already exist, offer merge (add VLANs to existing) vs. swap (replace probes entirely). Curated Zscaler destination data lives under `data/`. Targets are prefixed with `https://` and carry no port number. Register the new op in `OperationRegistry`. Include the menu wire-up in `MistHelper.py` on this branch."

## Summary

A network operator needs a repeatable, single-command way to apply a curated set of Zscaler Client Connector reachability probes as **org-level `synthetic_test.custom_probes`** in Mist, scoped to a chosen list of VLANs. The curated destination catalogue lives in `data/zscaler_client_connector_probes.json` (17 roles, ~30 concrete FQDNs) plus `data/zscaler_cenr_hostnames.json` (104 proxy + 104 VPN Cloud Enforcement Node hostnames). When the operator selects the new menu option, MistHelper prompts for the VLAN list, reads the current org setting, detects whether probes already exist, and offers a merge vs. swap choice before PUT-ing an updated `synthetic_test` block.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - First-Time Probe Deployment (Priority: P1)

An operator with a fresh Mist org selects the new interactive menu option, enters a comma-separated VLAN list (e.g. `10,20,30`), and — because no `synthetic_test.custom_probes` exist yet — the tool builds the full probe set from the curated JSON data files, prefixes every target with `https://`, applies the VLAN list to each probe's `vlan_ids`, and PUTs the resulting org setting. The operator sees a per-probe success/failure summary and the org's Zscaler reachability probes are now in place.

**Why this priority**: This is the primary use case; every downstream story assumes an initial deployment path exists and works.

**Independent Test**: Given a mocked `getOrgSettings` returning no existing `synthetic_test.custom_probes`, invoking the manager with VLAN list `[10,20,30]` MUST produce a probe body containing one entry per FQDN in the curated JSON data files with `type="reachability"`, `target` prefixed with `https://`, no port suffix, and `vlan_ids=[10,20,30]`, and MUST call `updateOrgSettings` exactly once with that body.

**Acceptance Scenarios**:

1. **Given** the org has no existing `synthetic_test.custom_probes`, **When** the operator selects the menu option and enters a VLAN list, **Then** the tool MUST build the probe set from `data/zscaler_client_connector_probes.json` + `data/zscaler_cenr_hostnames.json`, applying the entered VLAN list to every probe's `vlan_ids`.
2. **Given** the tool builds a probe body, **When** any concrete FQDN is emitted as a probe target, **Then** it MUST be prefixed with `https://` and MUST NOT include a port number (per operator constraint 2026-07-23).
3. **Given** the operator confirms the change, **When** the tool applies it, **Then** it MUST call `mistapi.api.v1.orgs.setting.updateOrgSettings` exactly once with the constructed body and MUST report per-probe status.
4. **Given** any curated `fqdn` entry contains a wildcard (`*.zscaler.net`), **When** the tool builds the probe body, **Then** it MUST skip that wildcard entry (documented in the source JSON `wildcards` array), because wildcards cannot be directly probed.

### User Story 2 - Merge New VLANs Into Existing Probes (Priority: P2)

An operator returning to add a new VLAN (e.g. `40`) to already-deployed probes selects the menu option, enters `[40]`, and is told existing probes already cover VLANs `[10,20,30]`. The operator chooses **merge**. The tool leaves the existing probe set intact and, for each existing probe, appends `40` to `vlan_ids` (deduplicated, preserving order where possible). No probes are added or removed.

**Why this priority**: Merge is the safe, additive path — the most common operational reason to re-run the menu after a first deployment.

**Independent Test**: Given a mocked existing `synthetic_test.custom_probes` block with `vlan_ids=[10,20,30]` on every probe, invoking the manager with new VLAN list `[40]` in merge mode MUST result in a body where each probe's `vlan_ids` is exactly `[10,20,30,40]` (deduplicated), with no probe added, removed, or renamed.

**Acceptance Scenarios**:

1. **Given** existing probes are detected, **When** the tool prompts the operator, **Then** it MUST clearly display: (a) number of existing probes, (b) union of existing VLAN ids across those probes, and (c) an unambiguous two-choice prompt (merge | swap).
2. **Given** the operator chooses **merge**, **When** the tool builds the updated body, **Then** every existing probe MUST be preserved by name and target, and each probe's `vlan_ids` MUST be the deduplicated union of the existing ids and the newly-entered ids.
3. **Given** the operator's newly-entered VLAN list is a subset of what each probe already carries, **When** the tool computes the merge diff, **Then** it MUST report "no changes required" and MUST NOT issue a PUT.

### User Story 3 - Swap Replaces Probes Entirely (Priority: P3)

An operator wants to replace a legacy probe set with a freshly curated set (e.g. because the curated JSON was updated). They enter a VLAN list, choose **swap**, and confirm. The tool discards every existing entry under `synthetic_test.custom_probes` whose name matches the curated set's naming scheme (plus any probe not present in the new curated set), rebuilds the probe set from the curated JSON with the new VLAN list, and PUTs the result. Non-conflicting user-owned probes (i.e. probes not authored by this tool) MUST be preserved.

**Why this priority**: Swap is the destructive path, needed for legitimate re-curation but must not blow away hand-authored probes.

**Independent Test**: Given a mocked existing block with 3 tool-authored probes plus 1 hand-authored probe (name prefix outside the tool's namespace), invoking swap MUST leave the hand-authored probe untouched and rewrite only the tool-authored ones.

**Acceptance Scenarios**:

1. **Given** the operator chooses **swap**, **When** the tool builds the updated body, **Then** it MUST rewrite exactly the probes whose names match this tool's naming convention (documented in `data-model.md`), leaving any other probes untouched.
2. **Given** swap mode, **When** the tool builds the new probe set, **Then** it MUST derive `vlan_ids` for every new probe **only** from the operator's newly-entered VLAN list — no VLAN from a prior deployment is carried forward.
3. **Given** the operator declines to confirm at the final prompt, **When** the confirmation prompt is answered "no", **Then** the tool MUST NOT call `updateOrgSettings` and MUST report that no changes were made.

### Edge Cases

- Empty VLAN list at the prompt → the tool MUST re-prompt (or exit cleanly) rather than PUT probes with empty `vlan_ids`.
- Non-integer or negative VLAN entries → the tool MUST reject them at the prompt with a helpful message.
- `getOrgSettings` returns a `synthetic_test` block with `custom_probes` absent (only `vlans` or other siblings present) → the tool MUST treat this identically to "no existing probes" and MUST NOT drop the sibling fields when it PUTs the updated block.
- `getOrgSettings` returns an unexpected shape (missing `synthetic_test` key entirely) → the tool MUST create a new `synthetic_test` block containing only `custom_probes`, without setting other sibling fields.
- The two source JSON files are missing or malformed → the tool MUST fail closed with a clear error identifying which file was unreadable.
- The operator running the menu option lacks org-scope write permission → the mistapi call will surface an HTTP error; the tool MUST report it verbatim and MUST NOT silently succeed.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: MistHelper MUST expose a new interactive menu entry that launches the org-level synthetic-probe manager.
- **FR-002**: The menu entry MUST be registered in `src/utils/operation_registry.py` with category `destructive` (it PUTs to org settings via `updateOrgSettings`).
- **FR-003**: The manager MUST prompt for a comma-separated VLAN list and MUST validate each entry as a non-negative integer in the range `[0, 4094]`.
- **FR-004**: The manager MUST call `mistapi.api.v1.orgs.setting.getOrgSettings(session, org_id)` to read the current org setting.
- **FR-005**: The manager MUST inspect the response's `synthetic_test.custom_probes` field. If present and non-empty, it MUST prompt the operator for **merge** vs. **swap** using an unambiguous two-choice prompt.
- **FR-006**: The manager MUST build probe entries from `data/zscaler_client_connector_probes.json` (all roles) plus, for the `tunnel_zen` role only, the union of `proxy_hostnames` and `vpn_hostnames` from `data/zscaler_cenr_hostnames.json`.
- **FR-007**: Every probe target MUST be prefixed with `https://` and MUST NOT include a port number.
- **FR-008**: Wildcard FQDN entries in the source JSON MUST be skipped (they cannot be directly probed).
- **FR-009**: Every probe MUST use `type="reachability"` and `aggressiveness="high"` unless the curated JSON explicitly overrides these fields per-role.
- **FR-010**: Probe `name` MUST follow the pattern `zcc-<role>-<fqdn-slug>` (e.g. `zcc-pac-pac-zscaler-net`) so this tool can unambiguously identify probes it authored during a later swap.
- **FR-011**: In **merge** mode, existing probes matching the tool's `zcc-` name prefix MUST have their `vlan_ids` set to the deduplicated union of existing ids and newly-entered ids; probe names, targets, and other fields MUST be preserved.
- **FR-012**: In **swap** mode, every existing probe whose name matches the tool's `zcc-` prefix MUST be removed and replaced with the freshly-built set. Probes NOT matching the tool's prefix MUST be preserved unmodified.
- **FR-013**: The manager MUST show a final confirmation prompt summarizing (a) count of probes to be added/removed/updated, (b) resulting VLAN id list per probe, and (c) the resulting total probe count. A "no" answer MUST abort without calling `updateOrgSettings`.
- **FR-014**: The manager MUST call `mistapi.api.v1.orgs.setting.updateOrgSettings(session, org_id, body)` exactly once per confirmed run, and MUST report success/failure at both the HTTP-response level and the per-probe level.
- **FR-015**: The manager MUST NOT drop or overwrite any sibling fields (e.g. `synthetic_test.vlans`, `synthetic_test.wan_speedtest`) inside the org setting when constructing the PUT body.
- **FR-016**: `MistHelper.py --help` MUST NOT be regressed by this feature — help output MUST remain side-effect-free (per issue #1641, guarded on `main`).
- **FR-017**: The feature MUST include pytest unit tests covering: build-from-empty (Story 1), merge with existing (Story 2), swap preserving foreign probes (Story 3), wildcard skipping, empty-VLAN rejection, and the "no changes required" merge path.

### Key Entities *(include if feature involves data)*

- **Probe source (Zscaler Client Connector)** — `data/zscaler_client_connector_probes.json`. Schema v1. Contains `roles[]` (17 entries), each with `role`, `description`, `ports[]`, and either `fqdns[]` (concrete) or `fqdns_ref` (external file reference). Also contains a top-level `wildcards[]` array of informational wildcards.
- **Probe source (Zscaler CENR)** — `data/zscaler_cenr_hostnames.json`. Schema v1. Contains `proxy_hostnames[]` (104 entries, `*.sme.zscaler.net` naming) and `vpn_hostnames[]` (104 entries, `*-vpn.zscaler.net` naming). Fetched from `https://config.zscaler.com/api/zscaler.net/cenr/json` on 2026-07-23. IPs intentionally omitted per operator requirement.
- **Custom probe (Mist)** — an entry inside `org_setting["synthetic_test"]["custom_probes"]`, keyed by probe `name`. Fields consumed by this tool: `name`, `type`, `target`, `vlan_ids`, `aggressiveness`. Other fields (if the API adds them later) MUST be preserved unmodified when merging.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After a fresh first-time deployment (Story 1), `getOrgSettings` returns a `synthetic_test.custom_probes` block containing one probe per non-wildcard FQDN in the curated JSON data files. All target strings begin with `https://` and contain no `:` port separator after the host.
- **SC-002**: After a merge run (Story 2) adding one VLAN to an existing 3-VLAN deployment, every tool-authored probe reports `vlan_ids` of length 4 with the new VLAN appended; probe count is unchanged; no non-tool-authored probe is modified.
- **SC-003**: After a swap run (Story 3) against a set containing one hand-authored probe (name outside the `zcc-` prefix), the hand-authored probe is present verbatim in `getOrgSettings` post-run; every remaining probe carries `vlan_ids` exactly equal to the newly-entered VLAN list.
- **SC-004**: The new menu op appears in `OperationRegistry.destructive_options` with a `skip_reason` explicitly identifying it as an org-settings write. `python -m pytest tests/unit/test_operation_registry_guardrail.py` continues to pass.
- **SC-005**: `python -m pytest tests/unit/org/test_org_synthetic_probes_manager.py` (new) achieves ≥90% coverage of the new module.
- **SC-006**: `ruff check .`, `black --check .`, `interrogate` (≥90%), and `pydoclint --style=google` continue to pass on all new/modified files.
