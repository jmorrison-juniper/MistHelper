# Implementation Plan: Integrate Mist Cisco Config Converter

**Branch**: `feat/4224-cisco-config-converter` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric specification from `/specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/spec.md`. The route matches base-5 of 4224 (R-62, R-63).

## Summary

Integrate the Cisco IOS to Mist gateway converter into the MistHelper web portal. The integration keeps review before every cloud change. The merged DNS slice stays unregistered. Child records 4634 to 4649 add the rest of the parity scope in dependency order. This parent record adds no product code.

## Technical Context

**Language/Version**: Python 3.15 or newer. `pyproject.toml` requires `>=3.15` (R-32 stale claim, R-69 pin row, R-67 setup text). The legacy plan named Python 3.13 and is stale.

**Primary Dependencies**: Flask and the existing MistHelper web portal. The Mist SDK is mistapi 0.64.1 (R-78). `requirements.txt` pins `mistapi==0.64.1` (R-68). `pyproject.toml` allows `>=0.64.1,<0.65` (R-69). `.github/copilot-instructions.md` states `>=0.64.0,<0.65` (R-49). Analysis A-10 lists the mismatch.

**Storage**: Private files under `data/`. No new database. No Redis service. Preview and export write no file (spec, Edge Cases).

**Testing**: pytest for unit and integration tests. Playwright for browser journeys in the existing e2e tests. Mocked mistapi responses for all cloud behavior.

**Target Platform**: Windows 11, macOS, and Linux for development. The MistHelper container for deployment (R-64).

**Project Type**: Flask portal integrated with the MistHelper runtime. Web UI on port 8055 (R-54).

**Performance Goals**: Each upload is at most 16 MiB plus 16 KiB of multipart overhead (R-26). Each write is bounded at 90 seconds. Each run is bounded at 10 minutes (child 4644).

**Constraints**: Strict UTF-8. Six suffixes. Path-like names rejected. Typed words EXPORT, APPLY, and CONFIRM. Write families disabled by default. Logs in ASCII. No credential in browser storage, uploads, generated files, logs, or fixtures.

**Scale/Scope**: One operator per browser session. One organization for each apply run. Sixteen child records with 403 planned tests in total.

## Constitution Check

The check uses the rules in `.specify/memory/constitution.md` and `AGENTS.md`.

| Rule | Result | Reason |
|---|---|---|
| I. Five-item rule (R-56) | Pass for this record. Fail on `main` for existing folders. | The record folder has five children at the feature root and five in `design/`. `tests/contract` holds 17 children (R-92). `tests/e2e/web_portal` holds 32 children (R-93). The plan adds no child to either folder (D-9). The converter root holds five children (R-94). D-10 keeps the root at five. |
| II. Class-based architecture | Pass by design | The parent record adds no function. Child records keep behavior in named classes. |
| III. Safety first, typed confirmation (R-57) | Pass by design | Cloud writes need typed words (D-5). Input validation runs first (FR-002). Secrets stay out of logs (R-58). |
| IV. Full deployment pipeline | Pass by design | Tasks T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE cover each step. None has run. |
| V. Observability and ASCII logs (R-59) | Pass with a stated reading | D-12 uses the standard logger with key=value fields. A reviewer confirms that reading in T-PR. |
| VI. Inline comments (R-60) | Pass by design | Each code task carries inline comments on executable lines. |
| VII. Action logging (R-61) | Pass by design | Each action logs before and after execution. |
| Mist Cloud transport | Pass by design | Each REST request uses a mistapi method (R-80, R-28). Direct HTTP is prohibited. Child 4634 owns the contract tests. |
| Compatibility of shared files | Conditional | `web_portal/app.py` and `web_portal/templates/base.html` wait for gate G3 (D-11). |
| Deployment | Pass | The plan adds no service, volume, network, database, Redis instance, or Compose group (FR-033). `misthelper-redis` is the shared Redis name (R-65). Rule 1 requires test containers in the compose group (R-64). |
| Release notes | Pass by design | Each implementation pull request adds one unique fragment under `changelog.d/`. This record adds none, because it changes no user-visible behavior. |
| Secrets | Pass by design | Credentials come from existing settings (R-55). The seal key decision is open (D-16). |

No constitution violation requires a complexity exception. The table in the Complexity Tracking section lists the existing debt that this plan does not increase.

## Architecture

```text
Operator browser
  -> converter tab (after gate G3) or isolated test host (before G3)
  -> routes.py (CSRF, ConverterRequest, no-store responses)
  -> state/intake (in-memory upload and source review)
  -> conversion/ (DNS, hardware, network, and management converters)
  -> state/proposal (SHA-256 digest and review record)
  -> review and export (typed word EXPORT)
  -> discovery (read-only mistapi calls with the existing credential)
  -> approval (typed word APPLY, 15 minutes, one use)
  -> state/execution (write families, disabled by default)
  -> state/lifecycle/backup and state/lifecycle/recovery
  -> private files under data/ (no new database and no new service)
```

The browser never receives a credential or a configuration value that a log does not allow.

## Project Structure

### Documentation (this feature)

```text
specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      portal-routes.md
      mist-gateway-template.md
    checklists/
      requirements.md
      security.md
```

The feature root holds five children. `design/` holds five children. `contracts/` holds two files. `checklists/` holds two files.

### Source and test layout

The source layout keeps five children at the converter root. It also keeps five children in `presentation/` and in each new package. Child records name the paths. Analysis items A-14 to A-17 list the paths that need amendment.

## File-by-File Change Map

| Path | Action | Child issue | Parity tasks | Gate |
|---|---|---|---|---|
| `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/` | Modify. Replace the legacy files with this record. | Parent | T-PR | None |
| `src/interfaces/portals/cisco_config_converter/routes.py` | Modify. Add the routes for each stage. | 4637, 4641, 4642, 4643, 4644, 4645, 4646 | T008, T010, T018, T020, T022, T024, T026, T028 | G2, G4, G5 for write routes |
| `src/interfaces/portals/cisco_config_converter/models.py` | Delete after `state/` exists. | 4636 | T006 | None |
| `src/interfaces/portals/cisco_config_converter/state/` | Add a package. | 4636, 4637, 4643, 4644, 4645, 4646 | T006, T008, T018, T022, T024, T026, T028 | None |
| `src/interfaces/portals/cisco_config_converter/conversion.py` | Delete after `conversion/` exists. | 4640 | T013, T014 | None |
| `src/interfaces/portals/cisco_config_converter/conversion/` | Add a package. The child 4640 skeleton comes first (D-14). | 4640, 4638, 4639 | T011, T012, T014, T015, T016 | G2 |
| `src/interfaces/portals/cisco_config_converter/presentation/converter.html` | Modify. | 4637, 4638, 4641, 4647 | T010, T012, T030 | None |
| `src/interfaces/portals/cisco_config_converter/presentation/converter.js` | Modify. | 4638, 4641, 4647 | T012, T018, T030 | None |
| `src/interfaces/portals/cisco_config_converter/presentation/converter.css` | Add. | 4647 | T030 | None |
| `src/interfaces/portals/cisco_config_converter/presentation/proposal_review.js` | Add. | 4641 | T018 | None |
| `src/interfaces/portals/cisco_config_converter/presentation/administration/` | Add a subfolder (D-10). | 4645 | T026 | G4 |
| `src/mist/access/targets/` | Add a package for read-only discovery. | 4642 | T020 | G2 |
| `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py` | Modify at its path on `main` (R-17). | 4637, 4640 | T007, T009, T013 | None |
| `tests/integration/web_portal/cisco_config_converter/test_routes.py` | Modify. | 4637, 4641, 4644 | T007, T017, T021 | None |
| `tests/integration/web_portal/cisco_config_converter/` subfolders | Add grouped test packages (D-9). | Child records | T006 to T031 | None |
| `tests/e2e/web_portal/test_portal_smoke.py` | Modify. Add no new file (R-93, D-9). | 4647, 4648 | T029, T030 | None |
| `web_portal/app.py` | Modify after the handover. | 4648 | T032 | G3 |
| `web_portal/templates/base.html` | Modify after the handover. | 4648 | T032 | G3 |
| `web_portal/services/data_browser.py` | Modify. Exclude the private converter folder (R-47). | 4637, 4643 | T024 | G3 and a separate pull request |
| `web_portal/services/output_scan.py` | Modify. Exclude the private converter folder from the output scan. | 4643 | T024 | G3 |
| Converter guide path | Add after the owner approves documentation. The path comes from the child 4649 decision. This record does not create it. | 4649 | T033 | D-17 approval |

## Gates

| Gate | Definition (parity plan, R-87) | Applies to |
|---|---|---|
| G1 Legal | Owner or legal decision for reuse, independent-authorship review, and distribution constraints | Any reuse and release (D-17) |
| G2 API | Current OpenAPI fields, installed signatures, model data, and independent contract tests | Each unverified mapping and write |
| G3 Integration owner | Explicit ownership and shared-file handover | Portal and shared-service changes (D-11) |
| G4 Cloud owner | Approved operation families, roles, scope, and recovery policy | Enabling apply, restore, delete, or unassign (D-15) |
| G5 Operator | Current proposal, exact typed word, permission, and backup evidence | Each individual cloud write |

## Dependencies

- Python 3.15 for the project environment (R-67).
- Flask and the existing portal code. No new Flask extension is added by this record.
- mistapi 0.64.1 (R-68). The pin conflict in A-10 stays open until the owner corrects the text.
- pytest and Playwright for the existing test layout.
- The shared Redis service `misthelper-redis` (R-65). This record adds no Redis service.
- Child records 4634 to 4649, read as drafts. No child record exists on `main` yet.

## Risks and Mitigations

| Risk | Impact | Mitigation | Owner |
|---|---|---|---|
| The merged converter files lack a license review (A-01) | Legal exposure | Keep the code unregistered (D-2). Record the decision (D-17). | Owner |
| A write reaches production | Production change | Disabled families (D-3). Decision D-15. Typed APPLY (D-5). | Owner and child 4644 |
| The data browser lists private converter files (R-47) | Data exposure | Exclude the private folder before production retention (D-7). | Child 4637 and child 4643 |
| The seal key falls back to a random UUID (R-46) | Stored review records break after restart | Decision D-16. | Owner |
| web_portal/app.py defines no operator identity source (A-12) | Writes lack an accountable operator | Decision D-16. | Owner |
| mistapi retries HTTP 429 three times (R-79) | A repeated write | No application retry for writes (D-6). Indeterminate result. | Child 4644 |
| Two open PRs edit the same shared files | Merge conflict | Gate G3 (D-11). | Child 4648 |
| Child paths break the five-child rule | Structure violation | Amend the child paths (A-14 to A-17). | Child owners |
| Legacy and parity task IDs collide | Wrong task tracking | Use parity IDs only (D-13). | Parent |

## Rollback Steps

1. Revert the parent record merge commit. Caution: the revert restores the legacy DNS-only text and removes this umbrella record.
2. Keep the merged DNS slice unregistered. Do not revert PR #4226 without the decision in D-17.
3. Disable each enabled write family in the registry. Warning: a code revert does not reverse a completed cloud write. Use the recorded backup and a fresh approval.
4. Remove the blueprint registration in one change. Caution: this removes the portal tab only.
5. Keep the backup files under `data/` until the owner approves deletion. Warning: deleting a backup removes the recovery evidence for each completed write.

## Complexity Tracking

| Item | Why it exists | Simpler option rejected because |
|---|---|---|
| `tests/contract` holds 17 children (R-92) | Existing debt. The plan adds no child. | Adding a sixth child would breach the rule. |
| `tests/e2e/web_portal` holds 32 children (R-93) | Existing debt. The plan adds no file. | A new browser file would add a child to an overfull folder. |
| Child paths for tests and presentation files need amendment | Child records drafted the paths before this layout | Keeping the paths breaks the five-child rule. |
| Standard logging for Principle V (D-12) | The portal already uses the standard logger (R-97) | A structlog migration would change shared logging. |
