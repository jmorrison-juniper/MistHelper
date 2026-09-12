# Feature Specification: Narrow the pylint W0613 unused-argument suppression

**Feature Directory**: `specs/887-pylint-unused-argument/`

**Feature Branch**: not created. This spec creates no branch and no commit.

**Created**: 2026-07-29

**Status**: Draft

**Source Issue**: #887, part 1 of 3

**Input**: Narrow the repository-wide pylint `W0613` (unused-argument) suppression so that unused arguments in ordinary functions are flagged again. Cover `W0613` only.

---

## Context

The file `pyproject.toml` holds this line in the `[tool.pylint."messages control"]` table:

```toml
disable = ["C0114", "C0115", "C0116", "W0613", "W0718"]
```

The committed rationale for `W0613` is: "unused-argument -- WebSocket callback signatures are protocol-mandated". That rationale covers protocol callbacks only. The disable covers the whole repository. Any unused argument in any ordinary function is therefore hidden.

Issue #887 asks the team to narrow the suppression. This feature covers `W0613` only.

### Measured baseline

The command `pylint src/ --disable=all --enable=W0613` reports 21 findings. The findings sit in 20 functions across 13 files. One function, `AppRunner._prompt_for_commands`, holds 2 of the 21 findings. The team measured this baseline on `main` at commit `45c7b8d`.

### Gate behavior

The continuous integration job runs this command:

```text
pylint src/ --fail-under=9.5 --ignore=maps,ssh,ui
```

The `--ignore` flag hides `src/maps`, `src/ssh`, and `src/ui`. Four of the 21 findings sit inside `src/maps` and `src/ssh`. Those four findings do not change the gate score today. Issue #891 tracks the removal of the `--ignore` flag. This feature does not change that flag.

### Prior failure to avoid

Issue #891 recorded a score disagreement. A Windows checkout reported 9.71. The `ubuntu-latest` runner reported 9.41 for the same commit and failed the 9.5 threshold. A local Windows run is therefore not a safe proxy for this gate. This feature must confirm the score on the runner.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Record a decision for every finding (Priority: P1)

A maintainer needs to know which unused arguments are dead code and which are bound by a contract. The maintainer reviews each of the 21 findings, reads the surrounding code, and assigns one outcome to each finding. The maintainer writes the decision and the evidence into a triage record.

**Why this priority**: The triage record is the foundation. Without it, a code change is a guess. The record alone gives the team value, because it separates dead parameters from contract-bound parameters.

**Independent Test**: Read the triage record. Confirm that it holds 21 rows. Confirm that every row names a file, a line, a function, a parameter, an outcome, and a justification. No code change is needed for this test.

**Acceptance Scenarios**:

1. **Given** the measured baseline of 21 findings, **When** the maintainer completes the triage, **Then** the record holds one outcome for each of the 21 findings.
2. **Given** a finding with no clear contract, **When** the maintainer inspects the function body and the call sites, **Then** the record states Outcome A and names every call site.
3. **Given** a finding in a library callback, **When** the maintainer inspects the library contract, **Then** the record states Outcome B and names the contract.
4. **Given** a finding where the argument should have been used, **When** the maintainer inspects the intended behavior, **Then** the record states Outcome C and links a companion issue.

---

### User Story 2 - Make the code match the triage (Priority: P2)

A maintainer applies the recorded outcomes to the source tree. The maintainer removes each Outcome A parameter from the signature and from every call site. The maintainer adds a site-local suppression with a one-line reason to each Outcome B parameter. The maintainer takes the safest minimal action for each Outcome C site.

**Why this priority**: The code change makes the source tree honest. A reviewer can then read one line and learn why an argument stays.

**Independent Test**: Run `pylint src/ --disable=all --enable=W0613`. Confirm that it reports zero findings. Run the full test suite. Confirm that it passes.

**Acceptance Scenarios**:

1. **Given** an Outcome A parameter, **When** the maintainer removes it, **Then** every call site drops the argument and the test suite passes.
2. **Given** an Outcome A parameter that a caller passes positionally, **When** the maintainer removes it, **Then** the remaining arguments still bind to the correct parameters.
3. **Given** an Outcome B parameter, **When** the maintainer adds the suppression, **Then** the comment names the contract that mandates the parameter.
4. **Given** any Outcome A or Outcome B site, **When** the maintainer completes the change, **Then** the runtime behavior is the same as before the change.
5. **Given** a test that calls a changed signature, **When** the maintainer changes the signature, **Then** the maintainer updates the test in the same change.

---

### User Story 3 - Turn the gate back on (Priority: P3)

A maintainer removes `W0613` from the `disable` list in `pyproject.toml`. The maintainer updates the comment block above the list. The continuous integration run on the branch confirms that the pylint gate still passes at the 9.5 threshold.

**Why this priority**: The gate is the durable outcome. From this point, the gate reports any new unused argument on the first run.

**Independent Test**: Read the continuous integration result for the branch. Confirm that the pylint job passed. Confirm that `W0613` is absent from the `disable` list.

**Acceptance Scenarios**:

1. **Given** a triaged and clean source tree, **When** the maintainer removes `W0613` from the `disable` list, **Then** the pylint gate passes on the Linux runner at the 9.5 threshold.
2. **Given** a merged change, **When** a developer adds a new unused argument, **Then** the pylint gate reports it on the first run.
3. **Given** a local Windows pylint score above 9.5, **When** the maintainer reports the result, **Then** the maintainer still waits for the Linux runner result before merge.

---

### Edge Cases

- A parameter is unused in one method but is mandated because the method overrides a base-class method. Removing the parameter breaks the override contract.
- A caller passes an Outcome A parameter positionally. Removing the parameter shifts every later argument to the wrong slot.
- An Outcome A parameter carries a default value. A caller passes it by keyword. Removing the parameter raises a `TypeError` at that caller.
- A test calls a changed signature. The test fails until the maintainer updates it.
- A parameter is unused in the body but a decorator or a framework reads the signature.
- Removing the `W0613` entry from the `disable` list makes hidden messages visible and lowers the pylint score below 9.5 on Linux.
- Four findings sit in packages that the gate ignores. Those findings never change the score, so the gate cannot prove that they are fixed.
- The baseline count drifts because other work lands on `main` before this feature starts.
- A site is an Outcome C defect and the correct fix is larger than this feature. The team must not hide the defect by deleting the parameter.

---

## Requirements *(mandatory)*

### Functional Requirements

#### Triage

- **FR-001**: The feature MUST assign exactly one outcome to each of the 21 measured findings. The outcome set is A, B, and C.
- **FR-002**: The triage record MUST name the file, the line, the function, the parameter, the outcome, and a one-sentence justification for each finding.
- **FR-003**: The feature MUST re-measure the baseline before the triage starts. If the count differs from 21, the feature MUST record the new count and triage every finding in the new list.
- **FR-004**: The feature MUST triage the four findings that sit in `src/maps` and `src/ssh`, even though the gate ignores those packages today.

#### Outcome A, remove the parameter

- **FR-005**: Outcome A applies when the argument is a refactor leftover and no contract requires it.
- **FR-006**: An Outcome A change MUST remove the parameter from the signature and from every call site.
- **FR-007**: Before an Outcome A removal, the feature MUST locate every call site in the source tree and in the test tree.
- **FR-008**: The feature MUST confirm that no caller passes the parameter positionally in a way that shifts another argument.
- **FR-009**: The feature MUST confirm that no caller passes the parameter by keyword.

#### Outcome B, keep with a narrow suppression

- **FR-010**: Outcome B applies when an external library protocol, an override contract, or a documented back-compat promise mandates the signature.
- **FR-011**: An Outcome B change MUST add a site-local `# pylint: disable=W0613` comment with a one-line reason. The comment MUST sit on the same line or on the line directly above.
- **FR-012**: The feature MUST NOT add a file-wide, module-wide, or repository-wide disable for `W0613`.
- **FR-013**: The Outcome B reason MUST name the specific contract. A generic phrase such as "signature required" is not sufficient.

#### Outcome C, a real defect

- **FR-014**: Outcome C applies when the argument should have been used and the omission is a defect.
- **FR-015**: The feature MUST NOT resolve an Outcome C site by deleting the parameter.
- **FR-016**: The feature MUST record each Outcome C site in the triage record.
- **FR-017**: The feature MUST file a companion GitHub issue for each Outcome C site and MUST link that issue from the triage record.
- **FR-018**: The feature MUST take the safest minimal action at each Outcome C site and MUST state that action in the record.

#### Gate change

- **FR-019**: The feature MUST remove `"W0613"` from the `disable` list in `pyproject.toml`. This MUST be the final source change.
- **FR-020**: The feature MUST update the comment block above the `disable` list so that it no longer claims that `W0613` is disabled.
- **FR-021**: After the change, `pylint src/ --disable=all --enable=W0613` MUST report zero findings.
- **FR-022**: The continuous integration pylint job MUST pass with `--fail-under=9.5` on the `ubuntu-latest` runner.
- **FR-023**: The feature MUST confirm the score with a real continuous integration run on the branch. A local Windows pylint run MUST NOT be accepted as proof.
- **FR-024**: If the Linux score falls below 9.5, the feature MUST raise the score by removing findings. The feature MUST NOT lower the threshold and MUST NOT restore the repository-wide disable.

#### Safety

- **FR-025**: The runtime behavior MUST NOT change at any Outcome A or Outcome B site.
- **FR-026**: Every existing test MUST still pass. The feature MUST update any test that calls a changed signature in the same change.
- **FR-027**: The feature MUST NOT change the `W0718` suppression.
- **FR-028**: The feature MUST NOT change the mypy `src.db` override.
- **FR-029**: The feature MUST NOT change the `--ignore=maps,ssh,ui` flag on the pylint gate.

#### Project conventions

- **FR-030**: Every changed line MUST carry an inline comment that explains why the line exists, not what the line does.
- **FR-031**: All prose MUST follow the Simplified Technical English rules in `documentation/ASD-STE100_writing-guide.md`.
- **FR-032**: The feature MUST NOT add a wrapper function.
- **FR-033**: The feature MUST NOT add a legacy compatibility shim, a pass-through alias, or a fallback compatibility path.

---

### Key Entities

- **Finding**: One pylint `W0613` message. A finding names a file, a line, a function, and a parameter.
- **Site**: One function that holds one or more findings. The baseline holds 20 sites and 21 findings.
- **Outcome**: One of three decisions. Outcome A removes the parameter. Outcome B keeps the parameter with a narrow suppression. Outcome C records a defect.
- **Triage record**: The document that maps every finding to an outcome, a justification, and evidence.
- **Suppression**: A `# pylint: disable=W0613` comment that covers one line or one function. A suppression always carries a reason.

---

## Site Inventory

The table lists the measured baseline. The outcome column is empty for every row that the team has not verified. The triage must fill every empty cell.

| # | File | Line | Function | Parameter | Gate sees it | Outcome |
| - | - | - | - | - | - | - |
| 1 | `src/capture/packet_capture.py` | 911 | `PacketCaptureManager._multi_ap_gather_params` | `ap_macs` | Yes | To triage |
| 2 | `src/firmware/bulk_ap_upgrader.py` | 1487 | `BulkAPFirmwareUpgrader._upgrade_version_group` | `mistapi` | Yes | To triage |
| 3 | `src/firmware/org_ap_upgrader.py` | 675 | `OrgLevelAPFirmwareUpgrader._display_org_list` | `msp_name` | Yes | To triage |
| 4 | `src/inventory/inventory_summary/version_per_model_fetcher.py` | 188 | `VersionPerModelFetcher._rows_for_model` | `target_org_id` | Yes | To triage |
| 5 | `src/maps/_maps_clone.py` | 149 | `_MapsClone._confirm_clone` | `clone_payload` | No | Outcome A, verified |
| 6 | `src/maps/maps_manager.py` | 532 | `MapsManager._render_site_maps_table` | `site_name` | No | To triage |
| 7 | `src/org/org_synthetic_probes_manager.py` | 1619 | `_build_probe_set` | `vlan_ids` | Yes | Outcome B, verified |
| 8 | `src/site/address_audit/address_resolver.py` | 93 | `AddressResolver._combine` | `candidates` | Yes | Outcome A, verified |
| 9 | `src/ssh/runtime/app_runner.py` | 265 | `AppRunner._prompt_for_commands` | `env_cmds` | No | To triage |
| 10 | `src/ssh/runtime/app_runner.py` | 265 | `AppRunner._prompt_for_commands` | `csv_cmds` | No | To triage |
| 11 | `src/ssid_consolidation/_ssid_template_cache.py` | 193 | `_SsidTemplateCacheCluster._offer_resume` | `results` | Yes | To triage |
| 12 | `src/ssid_consolidation/_ssid_template_phase1.py` | 121 | `_resolve_template` | `sitegroup_lookup` | Yes | To triage |
| 13 | `src/ssid_consolidation/_ssid_template_phase45.py` | 267 | `_build_template_config` | `resolutions` | Yes | To triage |
| 14 | `src/utils/address_utils.py` | 494 | `AddressUtils.apply_business_context_rules` | `debug` | Yes | To triage |
| 15 | `src/utils/address_utils.py` | 902 | `NominatimValidator._make_api_request` | `source` | Yes | To triage |
| 16 | `src/utils/address_utils.py` | 947 | `NominatimValidator._calculate_component_match` | `source` | Yes | To triage |
| 17 | `src/utils/address_utils.py` | 977 | `NominatimValidator._calculate_quality_boost` | `source` | Yes | To triage |
| 18 | `src/websocket/manager.py` | 318 | `WebSocketManager._on_open` | `websocket_connection` | Yes | Outcome B, verified |
| 19 | `src/websocket/manager.py` | 323 | `WebSocketManager._on_message` | `websocket_connection` | Yes | Outcome B, verified |
| 20 | `src/websocket/manager.py` | 336 | `WebSocketManager._on_error` | `websocket_connection` | Yes | Outcome B, verified |
| 21 | `src/websocket/manager.py` | 343 | `WebSocketManager._on_close` | `websocket_connection` | Yes | Outcome B, verified |

"Gate sees it" is "No" when the file sits in `src/maps` or `src/ssh`. The `--ignore=maps,ssh,ui` flag hides those packages from the score.

---

## Verified Observations

The team already read the code at five of the 21 findings. The notes below are evidence for the triage. The triage must still record them in the triage record.

### Rows 18 to 21, `src/websocket/manager.py`

The four methods are callbacks for the `websocket-client` library. The library calls each method with the connection object as the first argument. The signature is protocol-mandated. These four findings match the committed rationale. Expected outcome: B.

### Row 7, `src/org/org_synthetic_probes_manager.py`

The docstring of `_build_probe_set` already documents the ignore. The text states that the parameter is kept for signature and back-compat with the caller, and that VLAN scoping belongs on the `tests[]` row that references the probe, not on the `custom_probes` definition. This is a deliberate, documented ignore. It is not a defect. Expected outcome: B.

### Row 8, `src/site/address_audit/address_resolver.py`

The parameter `candidates` is a leftover. The body of `_combine` delegates to `_pick_tier_winner(ui, internal, osm)` and to `_resolve_validated(winner, ui, osm)`. Neither helper needs `candidates`. A previous refactor extracted those helpers and left the parameter behind. The removal is safe. Expected outcome: A.

### Row 5, `src/maps/_maps_clone.py`

The method `_confirm_clone` prints a clone plan and prompts for confirmation. It never reads `clone_payload`. The minimal correct change is to remove the parameter. Expected outcome: A.

**Companion observation, not in scope**: the plan text prints a static capability list, "Will copy: dimensions, orientation, location data, wayfinding, walls". The text does not describe the actual payload. The confirmation prompt may therefore not match what the operation sends. The feature MUST file a companion issue for this observation. The feature MUST NOT redesign the confirmation text.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The triage record covers every finding in the measured baseline. Zero findings are unassigned.
- **SC-002**: A scan of the source tree for unused arguments reports zero findings after the change.
- **SC-003**: The repository-wide suppression entry for unused arguments is absent from the project configuration file.
- **SC-004**: The continuous integration quality-score gate passes on the Linux runner at the 9.5 threshold. A run on the branch confirms the result.
- **SC-005**: The full test suite passes. The pass count matches the count before the change, apart from tests that the feature updated for a changed signature.
- **SC-006**: Every retained argument carries a one-line reason that names a specific contract. A reviewer reads that reason without opening another file.
- **SC-007**: Every recorded defect has a companion issue. The triage record links each issue.
- **SC-008**: A new unused argument added after this change is reported by the quality gate on the first run.
- **SC-009**: Zero behavior changes are observed at any Outcome A or Outcome B site.

---

## Out of Scope

The items below belong to other issues. This feature MUST NOT change them.

- `W0718` (broad-exception-caught). The repository holds 507 sites. This is a separate slice of issue #887.
- The mypy `src.db` override. This is a separate slice of issue #887.
- The `--ignore=maps,ssh,ui` flag on the pylint gate. Issue #891 tracks that work.
- The `C0114`, `C0115`, and `C0116` docstring suppressions.
- The redesign of the maps clone confirmation text. The feature records the observation and files a companion issue only.
- Any raise or lowering of the `fail-under` threshold.

---

## Assumptions

- The measured baseline of 21 findings holds at commit `45c7b8d` on `main`. Other work may land first and change the count. The feature re-measures before the triage starts.
- The pylint version on the runner matches the version that produced the baseline. A version change can add or remove findings.
- The four `src/websocket/manager.py` callbacks are expected to be Outcome B. The triage still records the evidence rather than assuming the result.
- The `src/org/org_synthetic_probes_manager.py` site is expected to be Outcome B, because the docstring already documents the ignore.
- Companion issues use the repository issue templates and the standard labels. Each issue carries a type label and a scope label.
- The team accepts a longer review for this feature, because a signature change needs a call-site search for each removal.
- The 4 findings in the ignored packages still get the full triage. The gate cannot prove that they are fixed, so a manual scan of those files confirms the result.

---

## Non-Negotiable Project Conventions

The conventions below apply to every change in this feature.

- **Inline comments**: every changed line carries an inline comment that explains why the line exists. A comment that restates the code is not sufficient.
- **Simplified Technical English**: all documentation, code comments, commit text, pull request text, and issue text follow `documentation/ASD-STE100_writing-guide.md`.
- **No wrappers**: the feature adds no wrapper function that only delegates to another function.
- **No legacy shims**: the feature adds no compatibility alias, adapter, or fallback path that exists only to keep an old call site working. The feature updates the real call sites.
- **Action logging**: the feature keeps the existing logging at every touched block. If a touched block lacks logging, the feature adds it.
