# Implementation Plan: Migrate Mist Guest Authorizations

**Branch**: docs/4231-mist-guest-authorizations | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)
**Input**: Issue #4231 and its linked work: PR #4290, PR #4589, PR #4279, issue #4278, issue #4588, and issue #4936.

## Summary

Plan a web portal feature that brings the legacy operator workflows into MistHelper. Reads stay live and bounded. Writes stay disabled until decision D-11 and gate G5 close. The feature reuses the existing portal process and the existing ArangoDB database. It stores no guest data in Redis. This planning change adds no product code.

## Technical Context

- **Language and version**: Python 3.15 or newer. `pyproject.toml` line 23 requires `>=3.15`. The legacy plan named Python 3.13. This plan corrects it.
- **Primary dependencies**: The Flask web portal in `web_portal/`. `mistapi` 0.64.1 is pinned at `requirements.txt` line 129, which satisfies the brief range `>=0.64.0,<0.65`. `python-arango` 8.3.7 is pinned at line 197. `structlog` 26.1.0 is pinned at line 249. `playwright` 1.65.2 is pinned at `requirements-dev.txt` line 272. No new dependency is added.
- **Storage**: ArangoDB database `misthelper`. New collection `guest_authorization_actions`. Existing collection `audit_logs`. The named volume `misthelper-arangodb-data` holds the data (`compose.yml` lines 347-348). No Redis guest data.
- **Testing**: pytest unit, contract, integration, and guardrail tests under `tests/`. Playwright browser tests under `tests/e2e/web_portal/`. Commands come from the local gates table in `.github/copilot-instructions.md` line 50.
- **Target platform**: Windows 11 with a local venv, Linux, and Podman containers (constitution line 300).
- **Project type**: Web portal feature inside the nested `src/` package structure.
- **Performance goals**: One WLAN list per view. One reconciliation read per write. At most 1000 Mist requests for a 500-row import.
- **Constraints**: Site scope only. No automatic write retries. Fail-closed journal. Five-child rule.
- **Scale**: One organization per portal process. One site and one WLAN per view.

## Architecture

The feature has five layers, from the operator to the Mist cloud:

1. **Presentation**: `GuestAccessBlueprint` in `presentation/routes.py`. It parses requests and renders results.
2. **Workflows**: `GuestInputValidator`, `TypedWordGate`, `GuestChangeService`, `ActionJournal`, and `AuditRecorder`. They enforce permission, typed words, hashes, journal writes, and audit writes.
3. **Gateway**: `SiteGuestGateway` in `src/mist/access/guests/gateway.py`. It calls allowlisted mistapi functions with keyword arguments.
4. **Read model and import**: `GuestAuthorizationReadModel` shows returned fields. `CsvImportParser` parses rows offline.
5. **Storage**: ArangoDB collections `guest_authorization_actions` and `audit_logs`.

The write path runs in a fixed order. It checks permission, then the typed word and hash, then writes the journal intent. It makes one SDK call and one reconciliation read. It writes the journal outcome and the audit event. A failed journal or audit step blocks the next write.

## Constitution Check

Each rule has a result and a reason. No rule fails. This change adds no product code, so the code rules apply to the implementation tasks.

| Rule | Result | Reason |
| --- | --- | --- |
| I. Five-Item Rule | Pass | `src/interfaces/portals/` keeps five children after the module becomes a package. The guard excludes `__init__.py` (guard line 117). `src/mist/access/` grows to four children. |
| I. Specs records | Pass | The record sits under `specs/numbered/` on the fixed eight-level base-5 route. The feature root holds five children. |
| I. Existing violations | Pass | No touched parent is noncompliant. The baseline has no `src/interfaces/portals` entry (`nested_package_baseline.json`). |
| II. Class-based architecture | Pass | Each behavior lives in a named class (see Architecture). No wrapper function delegates to a class. |
| III. Safety-first | Pass | Changes to the Mist cloud use typed words and reviewed-content hashes (D-7). Validation runs before each call. The web form has no `input()` call, so `safe_input()` does not apply. |
| IV. Full deployment pipeline | Pass | Steps 1 to 9 apply to this planning PR. Steps 10 to 12 apply to the implementation PR, which adds code and a release note. |
| V. Observability and logging | Pass | New log text is ASCII. New modules write structured entries through `structlog` 26.1.0. Secrets stay out of logs (FR-026). |
| VI. Inline comments | Pass | This change adds no code. Each implementation task requires an inline comment on each new executable line. |
| VII. Action logging | Pass | This change adds no code. Each implementation task requires an info log before and a debug log after each action. |
| Python 3.15 | Pass | `pyproject.toml` line 23 and constitution line 278 state the rule. |
| mistapi as sole interface | Pass | The gateway calls allowlisted mistapi functions only (FR-028). No direct HTTP request exists. |
| Owned WebSocket transport | Pass | The feature owns no WebSocket transport. The exception does not apply. |
| Package manager | Pass | No dependency changes. `requirements.txt` stays unchanged. |
| Podman runtime | Pass | Test containers join the compose group. Commands avoid Docker-only syntax. |
| File paths | Pass | Code uses `pathlib.Path`. No hard-coded separator appears. |
| Output backends | Pass | The feature exports no API data. The import reads a CSV file. The journal stores operational records only. |
| Operational store | Pass with open item U-7 | The journal is an internal coordination record that needs transactions, locks, and compare-and-swap (constitution lines 315 to 317). FR-019, FR-020, D-9, and D-10 define fail-closed behavior, backup, retention, and read-back. U-7 tracks the named store. |
| Export boundary | Pass | No API export or collected API data path changes. |
| Database keys | Pass | Mist records keep natural keys: site, WLAN, and MAC address. The journal adds an internal action key for idempotency. The feature adds no menu operation, so the endpoint strategy entry does not apply. |
| Data directory | Pass | The feature writes no product output. Browser failure evidence goes to `test-artifacts` (FR-029). |
| Container security | Pass | The feature changes no permission. The container user stays UID 1000. |
| Zscaler and proxy | Pass | This change pushes through GitHub only. Container builds run in GitHub Actions. |
| Menu operation sequence | Pass | The feature adds a portal tab, not a menu operation. The release note and README steps still apply (T016 and T027). |
| SpecKit escalation | Pass | The change touches more than three files and adds classes. The spec and plan precede product code. |
| Multi-agent Git workflow | Pass | One issue, one branch, one pull request, and no force push. |

Gate summary: the transport gate passes. Gate G5 is open, so writes stay blocked.

## Mist Cloud Gate

- **Transport**: mistapi functions only, as listed in spec.md. Pass.
- **Owned WebSocket transport**: none. Pass.
- **Contract tests**: TC-022 to TC-026 in `design/contracts/mist-api.md`. Pending implementation.
- **Write semantics**: Gate G5 is open for WLAN binding, revoke semantics, and list shape (U-3). Writes stay blocked (D-16).

## Project Structure

### Documentation

```text
specs/numbered/0/0/1/1/3/4/1/1/4231-mist-guest-authorizations/
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
      mist-api.md
      csv-import.md
      audit-journal.md
    checklists/
      requirements.md
```

Children per level: the feature root holds five (spec.md, plan.md, tasks.md, analysis.md, design). `design/` holds five (research.md, data-model.md, quickstart.md, contracts, checklists). `contracts/` holds four files. `checklists/` holds one file.

### Source code and tests

```text
src/interfaces/portals/guest_authorizations/
  __init__.py
  read_model.py
  imports.py
  workflows/
    __init__.py
    domain.py
    changes.py
    journal.py
    audit.py
  presentation/
    __init__.py
    routes.py
    templates/guest_access.html
    static/guest_access.js
src/mist/access/guests/
  __init__.py
  gateway.py
  responses.py
tests/unit/web_portal/          (domain, imports, journal, audit, and read model tests)
tests/contract/guests/test_guest_gateway.py
tests/integration/web_portal/test_guest_authorizations.py
tests/guardrails/test_guest_access_topology.py
tests/e2e/web_portal/test_guest_authorizations.py
```

Children per level, using the guard convention that excludes `__init__.py`:

- `src/interfaces/portals/` holds five: cisco_config_converter, guest_authorizations, licensing_comparison, upgrade_portal, and wan_dashboard.
- `src/interfaces/portals/guest_authorizations/` holds four: read_model.py, imports.py, workflows, and presentation.
- `workflows/` holds four modules. `presentation/` holds one module, `routes.py`. Templates and static files are not Python and do not count.
- `src/mist/access/` holds four: api, audit, auth, and guests. `src/mist/access/guests/` holds two modules.

## File-by-File Change Map

| Path | Action | Purpose | Requirements |
| --- | --- | --- | --- |
| src/interfaces/portals/guest_authorizations.py | Delete | Replaced by the package (D-2) | FR-027 |
| src/interfaces/portals/guest_authorizations/__init__.py | Add | Exports the blueprint factory only | FR-027 |
| src/interfaces/portals/guest_authorizations/read_model.py | Add | Moves `GuestAuthorizationReadModel` with unchanged output fields | FR-007, FR-008, FR-030 |
| src/interfaces/portals/guest_authorizations/imports.py | Add | `CsvImportParser` with limits, headers, and row states | FR-022, FR-023, FR-024 |
| src/interfaces/portals/guest_authorizations/workflows/domain.py | Add | `GuestInputValidator` and `TypedWordGate` with hashes | FR-006, FR-009, FR-011, FR-014 |
| src/interfaces/portals/guest_authorizations/workflows/changes.py | Add | `GuestChangeService` with intent, call, reconciliation, and outcomes | FR-012, FR-013, FR-015 to FR-020 |
| src/interfaces/portals/guest_authorizations/workflows/journal.py | Add | `ActionJournal` with ArangoDB records and scope locks | FR-003, FR-019, FR-020 |
| src/interfaces/portals/guest_authorizations/workflows/audit.py | Add | `AuditRecorder` with masked audit events | FR-026, FR-030 |
| src/interfaces/portals/guest_authorizations/presentation/routes.py | Add | `GuestAccessBlueprint` with review, change, search, and import routes | FR-001, FR-005, FR-006, FR-015 |
| src/interfaces/portals/guest_authorizations/presentation/templates/guest_access.html | Add | Page with stable `data-testid` values | FR-029, FR-030 |
| src/interfaces/portals/guest_authorizations/presentation/static/guest_access.js | Add | Client review display without secrets | FR-029 |
| src/mist/access/guests/__init__.py | Add | Package marker | FR-028 |
| src/mist/access/guests/gateway.py | Add | `SiteGuestGateway` with allowlisted mistapi calls and keyword arguments | FR-016 to FR-018, FR-028 |
| src/mist/access/guests/responses.py | Add | Status classes and list parsing | FR-016, FR-021 |
| web_portal/app.py | Modify after handover | Register the blueprint and the navigation flag | FR-001, FR-002 |
| web_portal/templates/base.html | Modify after handover | Add the tab with `data-testid="nav-guest-access"` | FR-001, FR-029 |
| deploy/.env.example | Modify | Add `GUEST_ACCESS_ENABLED` with the value false | FR-001 |
| README.md | Modify | Describe the tab and its flag | Documentation |
| documentation/guest-authorizations.md | Add | Operator guide with typed words, limits, and recovery steps | Documentation |
| changelog.d/issue-4231-guest-authorizations.md | Add | Release note fragment (constitution Development Workflow step 6) | Documentation |
| tests/unit/web_portal/test_guest_authorization_read_model.py | Modify | Import the module path and keep five test functions | FR-007, FR-008 |
| tests/unit/web_portal/test_guest_authorization_domain.py | Add | Validation and typed-word tests | FR-009, FR-011, FR-014 |
| tests/unit/web_portal/test_guest_authorization_imports.py | Add | CSV limit and row tests | FR-022 to FR-024 |
| tests/unit/web_portal/test_guest_authorization_journal.py | Add | Journal and lock tests | FR-019, FR-020 |
| tests/unit/web_portal/test_guest_authorization_audit.py | Add | Audit masking and redaction tests | FR-026, FR-030 |
| tests/contract/guests/test_guest_gateway.py | Add | Gateway contract tests | FR-016 to FR-018, FR-021, FR-028 |
| tests/integration/web_portal/test_guest_authorizations.py | Add | Route and workflow tests | FR-001 to FR-025 |
| tests/guardrails/test_guest_access_topology.py | Add | Topology, provenance, and import guards | FR-002, FR-004, FR-027, FR-028 |
| tests/e2e/web_portal/test_guest_authorizations.py | Add | Browser journeys | FR-029, FR-030 |
| tests/guardrails/nested_package_baseline.json | No change | The baseline stays unchanged | FR-027 |

## Phases and Sequence

1. **Phase 0 (gates)**: Record D-11 and D-13. Close G5 for WLAN binding, revoke semantics, and list shape. Receive the PR #4208 handover.
2. **Phase 1 (foundation)**: Convert the module. Add the gateway, journal, audit, and domain classes. Add contract and unit tests.
3. **Phase 2 (review)**: Add the review route, template, flag, and navigation. Ship read-only behavior behind the flag.
4. **Phase 3 (writes)**: Add grant, edit, extend, and revoke only after G5 closes.
5. **Phase 4 (search and import)**: Add client search and CSV import with the stop rules.
6. **Phase 5 (validation and release)**: Add documentation and browser hardening. Run the local gates. Open the pull request. Watch CI. Merge after authorization.

## Dependencies and Ownership

- PR #4208 is open. It owns `web_portal/app.py` and `web_portal/templates/base.html`. Task T005 requires a handover before T013.
- Issue #4936 is open. It tracks browser sign-in for port 8055. D-11 depends on that path or on an approved alternative.
- Issue #4278 is open for implementation. Issue #4588 is open for parity planning. PR #4589 merged on 2026-11-05 for issue #4588.
- PR #4279 merged on 2026-10-18. Its offline projection is the base for `read_model.py`.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| G5 WLAN binding fails | Grants cannot bind to a WLAN | Grants stay disabled (D-16). A new decision covers an organization-scope path. |
| Revoke semantics differ from the source | A false "ended" result | "ended" needs an unauthorized read-back (FR-013). |
| No approved identity method | Writes stay blocked | The flag stays false (FR-001). |
| PR #4208 conflicts | Navigation work waits | The handover precedes T013 (T005). |
| Journal unavailable | Writes stop | The feature fails closed (FR-019). |
| Audit write fails after a cloud success | Unrecorded change | Later writes block until reconciliation (FR-020). |
| Mist rate limits | Import stops early | The SDK retries 429 responses three times (`__api_request.py` line 59). A final 429 stops the batch (FR-025). |
| Licensing path not approved | Source reuse blocked | Reimplement from the Mist schema and documented behavior (D-13). |
| Organization and site scope mix | Wrong scope change | Site methods only, with no-fallback tests (TC-024). |
| Pinned source drifts | Wrong citations | Cite the pinned blob SHA for each claim (research section 8). |
| Secrets appear in logs | Credential exposure | Redaction tests (TC-015). |
| Browser tests skip silently | False pass | Run the browser file directly (quickstart section 3). |

## Rollback

1. Set `GUEST_ACCESS_ENABLED` to false. Restart the portal container with the steps in `documentation/container-deployment.md`.
2. Revert the implementation pull request with a squash revert. Do not force-push a shared branch.
3. Warning: Do not delete `guest_authorization_actions` or `audit_logs` records during rollback. They are the only local evidence of cloud changes.

## Complexity Tracking

No exception is requested. Touched existing violations: none. Remediation action: none.

The legacy plan placed code in `src/interfaces/portals/guest_workflows/`. That placement gives `src/interfaces/portals/` six children, and the guard rejects it (guard line 17 and line 117). D-2 converts the module instead.
