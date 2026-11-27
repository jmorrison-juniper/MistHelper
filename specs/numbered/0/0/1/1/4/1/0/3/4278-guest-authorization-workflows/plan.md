# Implementation Plan: Guest authorization workflows

**Branch**: `feat/4278-guest-authorization-workflows` (planned) | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Issue 4278. The gates come from issue 4231 and the planning record for issue 4588. Evidence appears in [research](design/research.md).

## Summary

Add a guest authorization page, review, and write workflows to the existing MistHelper web portal. Use mistapi only. Keep Mist as the source of truth. Store intent and outcome rows in the existing SQLite store. Enable each capability only after its gate passes. Decision D-4 blocks all guest data.

Record folder: `specs\numbered\0\0\1\1\4\1\0\3\4278-guest-authorization-workflows`. The route digits equal 4278 in base 5. The calculation is 1 times 5^5, plus 1 times 5^4, plus 4 times 5^3, plus 1 times 5^2, plus 3, which equals 4278.

## Technical Context

- **Language and version**: Python 3.15 or newer (`.github/copilot-instructions.md` line 20). The pyproject file (line 23) requires the same version.
- **Primary dependencies**: flask-wtf 1.3.0, mistapi 0.64.1, and structlog 26.1.0 (`requirements.txt` lines 54, 129, and 249). Flask and Gunicorn stay unchanged.
- **Storage**: Mist stores the authorization records. The SQLite file `data/mist_data.db` stores intent and outcome rows (`documentation/operator-guide.md` line 752).
- **Testing**: pytest unit, contract, and route tests. Playwright browser tests under `tests/e2e/web_portal`. No live Mist call in any test.
- **Target platform**: Windows 11, macOS, Linux, and the Podman container.
- **Project type**: One feature inside the existing web portal.
- **Performance goals**: A CSV batch has at most 200 rows and 262144 bytes. Writes run one at a time. The source gives no latency target, so this plan sets none.
- **Constraints**: Site scope only. Trusted identity under D-4. CSRF protection. Typed confirmation for each write. One Gunicorn worker with four threads (`wsgi.py` line 4).
- **Scale and scope**: One organization from `create_app` (`web_portal/app.py` line 37). Six user stories, 32 requirements, 20 tasks, and 37 planned tests.

## Constitution Check

Each row gives the result and the reason. A fail names the condition that clears it.

| Rule | Result | Reason |
| --- | --- | --- |
| I. Five-item rule, `src` | pass | `src/interfaces/portals` keeps five children. The package replaces the module `guest_authorizations.py`. Each new level holds five children or fewer. |
| I. Five-item rule, `tests` | fail (grandfathered) | `tests/unit/web_portal` and `tests/e2e/web_portal` already exceed five children. This plan adds one nested package and one module. Remediation R-1 covers the split. |
| II. Class-based architecture | pass | Each concern uses a named class: read model, scope resolver, confirmation checker, identity resolver, Mist client, mutation service, CSV service, audit store, and route class. |
| III. Safety first | fail until D-4 passes | Typed confirmation is in place (D-12). The access decision D-4 is open. Reads and writes stay disabled until approval. |
| IV. Full deployment pipeline | pass (planned) | `T-LOCAL-GATES`, `T-PR`, `T-REMOTE-CI`, and `T-MERGE` run the steps in order. The image build follows the merged revision. |
| V. Observability and logging | pass (planned) | structlog is pinned (`requirements.txt` line 249). Logs use ASCII text and masked values (D-17). |
| VI. Inline comments | pass (planned) | Each new executable line carries an inline comment. The review in `T-LOCAL-GATES` checks this rule. |
| VII. Action logging | pass (planned) | Each action logs before and after it runs (D-17). |
| Technology: mistapi | pass | Each Mist call uses one mistapi function. Contract tests TEST-005 to TEST-008 check this rule. |
| Technology: Podman | pass | The feature adds no container. Test containers follow `documentation/container-deployment.md` line 141. |
| Technology: file paths | pass | Each path uses `pathlib` and the `data` directory. |
| Output backends | pass (not applicable) | The feature exports no data. The SQLite audit store is an operational store under the constitution clause at line 315. |
| Operational store | pass (design) | D-14 and D-15 define fail-closed behavior, recovery, retention, and verified persistence. TEST-015 to TEST-017 check them. |
| Database keys | pass | The feature adds no export and no menu. The existing strategy entry for `listSiteAllGuestAuthorizations` stays (R076). |
| Container security | pass | The container user, volumes, and ports stay unchanged. |
| Spec Kit layout | pass | The route equals the base-5 value of 4278. The record uses `design/` for supporting files. |
| Multi-agent file ownership | fail until handover | `web_portal/app.py` and `web_portal/templates/base.html` belong to open PR 4208 (R093). Task T001 clears this condition. |
| Menu registry | pass | No menu is added. `operation_registry.py` and menu 286 stay unchanged. |

The grandfathered `tests` debt is recorded in the Complexity Tracking table. No new debt enters the `src` tree.

## Architecture

- **Read path**: The browser calls `web/routes.py`. The route checks identity and scope. `services/mist_client.py` calls the list function. `domain/read_model.py` masks each row before the response.
- **Write path**: The route builds a review with the exact scope and the masked target. `domain/confirmation.py` checks the typed word and the digest. `services/audit_store.py` writes the intent row. `services/mutations.py` makes one SDK call. The response class is recorded in an outcome row.
- **Import path**: `services/csv_import.py` checks size and headers. Preview resolves each row and sends no write. The run uses the write path for each row in sequence. A stop condition marks later rows not attempted.
- **Registration**: `web_portal/app.py` registers the blueprint in `_register_blueprints` (line 182), after the WAN dashboard blueprint (line 207).
- **Navigation**: `web_portal/templates/base.html` adds one link after the Operations link (line 60).

## Project Structure

### Documentation (this record)

```text
4278-guest-authorization-workflows/
  spec.md
  plan.md
  tasks.md
  analysis.md
  design/
    research.md
    data-model.md
    quickstart.md
    contracts/
      portal.md
      mist-api.md
      audit.md
      csv-import.md
    checklists/
      requirements.md
      security.md
      gates.md
```

### Source code (repository paths)

| Action | Path | Purpose |
| --- | --- | --- |
| Delete | `src/interfaces/portals/guest_authorizations.py` | Replaced by the package in the same change. |
| Add | `src/interfaces/portals/guest_authorizations/__init__.py` | Package entry point. |
| Add | `src/interfaces/portals/guest_authorizations/domain/__init__.py` | Domain package entry point. |
| Add | `src/interfaces/portals/guest_authorizations/domain/read_model.py` | Moved projection with unchanged behavior (FR-032). |
| Add | `src/interfaces/portals/guest_authorizations/domain/scope.py` | Scope binding and discovery checks (FR-002, FR-003). |
| Add | `src/interfaces/portals/guest_authorizations/domain/confirmation.py` | Typed words and review digest (FR-005, FR-022). |
| Add | `src/interfaces/portals/guest_authorizations/domain/identity.py` | Trusted identity rule (FR-004). |
| Add | `src/interfaces/portals/guest_authorizations/services/__init__.py` | Service package entry point. |
| Add | `src/interfaces/portals/guest_authorizations/services/mist_client.py` | One class for every mistapi call (FR-028, FR-029). |
| Add | `src/interfaces/portals/guest_authorizations/services/mutations.py` | Grant, update, extend, and revoke (FR-009 to FR-016). |
| Add | `src/interfaces/portals/guest_authorizations/services/csv_import.py` | Bounded CSV preview and run (FR-020 to FR-024). |
| Add | `src/interfaces/portals/guest_authorizations/services/audit_store.py` | SQLite intent and outcome rows (FR-017 to FR-019). |
| Add | `src/interfaces/portals/guest_authorizations/web/__init__.py` | Web package entry point. |
| Add | `src/interfaces/portals/guest_authorizations/web/routes.py` | Blueprint and JSON responses (FR-001, FR-005). |
| Add | `src/interfaces/portals/guest_authorizations/web/templates/guest_authorizations.html` | Page with stable data-testid attributes (FR-026). |
| Modify | `web_portal/app.py` | Register the blueprint in `_register_blueprints` (FR-001, FR-027). Owned by PR 4208 until handover. |
| Modify | `web_portal/templates/base.html` | Add the navigation link (FR-001). Owned by PR 4208 until handover. |

### Tests (repository paths)

| Action | Path | Purpose |
| --- | --- | --- |
| Delete | `tests/unit/web_portal/test_guest_authorization_read_model.py` | Moved to `test_domain.py`. |
| Add | `tests/unit/web_portal/guest_authorizations/__init__.py` | Test package entry point. |
| Add | `tests/unit/web_portal/guest_authorizations/test_domain.py` | Projection, scope, confirmation, and identity tests (TEST-001 to TEST-004). |
| Add | `tests/unit/web_portal/guest_authorizations/test_contract.py` | SDK contract tests (TEST-005 to TEST-009). |
| Add | `tests/unit/web_portal/guest_authorizations/test_routes.py` | Route tests (TEST-024 to TEST-028). |
| Add | `tests/unit/web_portal/guest_authorizations/services/__init__.py` | Service test package entry point. |
| Add | `tests/unit/web_portal/guest_authorizations/services/test_mutations.py` | Write tests (TEST-010 to TEST-014). |
| Add | `tests/unit/web_portal/guest_authorizations/services/test_audit_store.py` | Audit tests (TEST-015 to TEST-018). |
| Add | `tests/unit/web_portal/guest_authorizations/services/test_csv_import.py` | CSV tests (TEST-019 to TEST-023). |
| Add | `tests/e2e/web_portal/test_guest_authorization_portal.py` | Browser tests (TEST-029 to TEST-032). The e2e guard expects shared portal tests in this folder. |

### Documentation and process

| Action | Path | Purpose |
| --- | --- | --- |
| Modify | `documentation/operator-guide.md` | Add a section under `### Open a portal` (line 211) (FR-031). |
| Add | `changelog.d/issue-4278-guest-authorization-workflows.md` | One release-note fragment (FR-031). Rename it to `pr-<number>.md` after the pull request exists. |

**Structure decision**: Extend the existing `WebPortalApp` through one blueprint. Do not create a second Flask application, port, database, or Compose group.

## Dependencies

- No new Python dependency is planned. The feature uses Flask, flask-wtf (CSRF), structlog, mistapi, pytest, and Playwright. `requirements.txt` does not change.
- `pip-audit -r requirements.txt` does not apply, because no dependency manifest changes.
- A new dependency needs a separate decision and a dependency audit under the quality gates.

## Risks and Mitigations

| ID | Risk | Mitigation |
| --- | --- | --- |
| RK-1 | Shared-file conflict with PR 4208. | Task T001 must pass first (D-18). |
| RK-2 | A write reaches the wrong target. | Exact scope, typed word, review digest, one call, and zero-write tests (D-12, TEST-010, TEST-025). |
| RK-3 | An SDK retry repeats a write. | Warning: the SDK retries HTTP 429 three times for PUT and POST. The client counts calls and treats the final response as the outcome (TEST-014). |
| RK-4 | An unknown outcome is repeated. | No automatic retry. Read-back reconciles the result (D-15, TEST-013). |
| RK-5 | An audit failure hides a write. | Intent before dispatch. Outcome failure is reported separately (D-14, TEST-015, TEST-016). |
| RK-6 | SQLite contention across threads. | One worker with four threads. A process lock and an immediate transaction (D-16, TEST-018). |
| RK-7 | Revocation reports success without evidence. | The read-back gate decides the result (D-10, TEST-012). |
| RK-8 | Personal data reaches logs or responses. | Masked forms only. Log tests check each private value (D-17, TEST-028). |
| RK-9 | A CSV file is unbounded. | Byte and row limits run before parsing (D-13, TEST-019). |
| RK-10 | An identity header is spoofed. | The header counts only from a trusted peer (D-4, TEST-004). |
| RK-11 | Source expression is reused. | Clean-room rule (D-3). Reviewers reject any copied source file. |
| RK-12 | Mist semantics differ from the schema. | Gate G5 blocks grant semantics, extension, and revoke read-back until evidence exists (checklists/gates.md). |

Warning: the portal cannot reverse a confirmed write. Review each intent row before a new write after a restart.

## Rollback Steps

1. Before merge, close the pull request. No data changes.
2. After merge, remove the blueprint line in `web_portal/app.py` and the navigation link in `base.html`. Rebuild the image through GitHub Actions.
3. Keep every audit row. Do not delete rows from `data/mist_data.db`.
4. Keep the projection behavior. The moved module keeps its public behavior.

## Complexity Tracking

| Existing constraint | Narrow treatment | Remediation |
| --- | --- | --- |
| `tests/unit/web_portal` exceeds five children. | One nested package and one removed module. Net change: zero modules. | R-1: split the folder by area in a separate issue. |
| `tests/e2e/web_portal` exceeds five children. | One module, as the e2e guard expects. | R-2: split the folder in a separate issue. |
| `web_portal/app.py` and `base.html` belong to PR 4208. | One registration and one link after handover. | T001 gate. |
| `src/interfaces/portals/guest_authorizations.py` exists. | Replaced by a package in one change. | T003 and T016. |

No complexity threshold, baseline, or analyzer allow-list changes in this plan.

## Approval and Stopping Condition

- This run stops after the record and the two meta files.
- No implementation task starts before D-4 passes and the gates in `design/checklists/gates.md` pass.
- The planning change does not close issue 4231 or issue 4278. It does not merge automatically.
