# Source Comparison and Migration Decisions

## Evidence Boundary

Observation date: 2026-11-05. No source application or source tests were executed.
No live Mist connection was made. No source screenshots were downloaded or copied.

| Evidence | Revision or state |
| --- | --- |
| MistHelper `origin/main` and local `HEAD` | `296b977e28be50cd9ddcca57c46b35bb029afe27` |
| Live `origin/main` after serial branch update | `ba5d60a63ae154a5b86263b2baba8802acc7e7b1` |
| Rebased PR worktree before this evidence refresh | `b8583b6b3bdee2399408d93dc248c548c7a776a8` |
| Remote PR head before this evidence refresh | `5bdf622c0e09447824f408e0291a99937f516758` |
| Source public default branch | `main`, `d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c` |
| MistHelper issue [#4224](https://github.com/jmorrison-juniper/MistHelper/issues/4224) | OPEN when inspected |
| MistHelper PR [#4226](https://github.com/jmorrison-juniper/MistHelper/pull/4226) | MERGED, 2026-10-26T20:35:38Z |
| PR merge commit | `14ac97942f1e575edd7dbf8c4bbfb517ef58fad3` |
| Installed SDK | `mistapi` 0.64.1 |

On 2026-11-06, the branch was rebased onto the live default branch.
The converter package, shared portal registration and template, converter tests, and OpenAPI
file did not change since the recorded target revision. The dependency manifests changed, but
both root requirements files still pin `mistapi==0.64.1`. Other portal tests changed outside
the converter test paths. This refresh does not claim that unrelated paths stayed unchanged.

The current issue requests the full workflow. The merged PR delivered only a conservative offline DNS component.
The PR's spec and task record are historical evidence, not evidence of complete implementation.
This record does not change that historical record or its task boxes.

The initial target revision was `c57c9b704c1ce23976228cd72cad80b9d99926be`.
The final check found a newer default-branch commit for required-token handling in `mist-ops-platform/`.
The isolated branch advanced to that commit without creating a commit.
The converter, shared web portal, converter tests, and target OpenAPI had no changes in that update.
The final comparison uses the newer recorded target revision.

Read the source README, user guide, interface walkthrough, mapping reference, license declaration, route decorators, parser family identifiers, and test category identifiers.
Read source references through GitHub's public content API.
Use immutable source links below to reproduce the comparison.
Read only the current isolated MistHelper worktree.
Do not examine another worktree's uncommitted implementation or integration changes.

| Source label | Immutable reference |
| --- | --- |
| S1 | [README](https://github.com/jmorrison-juniper/MistCiscoConfigConverter/blob/d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c/README.md) |
| S2 | [User guide](https://github.com/jmorrison-juniper/MistCiscoConfigConverter/blob/d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c/docs/USER_GUIDE.md) |
| S3 | [Interface walkthrough](https://github.com/jmorrison-juniper/MistCiscoConfigConverter/blob/d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c/docs/INTERFACE.md) |
| S4 | [Mapping reference](https://github.com/jmorrison-juniper/MistCiscoConfigConverter/blob/d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c/docs/CISCO_TO_MIST_MAPPING.md) |
| S5 | [Route inventory](https://github.com/jmorrison-juniper/MistCiscoConfigConverter/blob/d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c/app.py) |
| S6 | [Parser family inventory](https://github.com/jmorrison-juniper/MistCiscoConfigConverter/blob/d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c/parser/cisco_parser.py) |
| S7 | [Tests directory](https://github.com/jmorrison-juniper/MistCiscoConfigConverter/tree/d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c/tests) |
| S8 | [License](https://github.com/jmorrison-juniper/MistCiscoConfigConverter/blob/d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c/LICENSE) |
| S9 | [Control inventory](https://github.com/jmorrison-juniper/MistCiscoConfigConverter/blob/d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c/templates/index.html) |

Target evidence uses these repository paths:

- `src/interfaces/portals/cisco_config_converter/routes.py`, `models.py`, and `conversion.py`.
- `src/interfaces/portals/cisco_config_converter/presentation/converter.html` and `converter.js`.
- `web_portal/app.py`, `web_portal/templates/base.html`, and `web_portal/routes/dashboard.py`.
- `tests/unit/gateway/overrides/test_cisco_config_converter.py` and `tests/integration/web_portal/cisco_config_converter/test_routes.py`.
- `tests/e2e/web_portal/test_portal_smoke.py` and `documentation/mist-api-openapi31json.json`.

Target tests mount a feature blueprint in an isolated Flask host.
The browser fixture also uses that isolated host.
The current shared portal has no converter registration or navigation entry.
Passing these tests does not prove deployed portal integration.

## Coverage Vocabulary

**Implemented** means the inspected component provides the named narrow behavior.
It does not mean the shared portal exposes that component.
**Partial** means only part of the observed journey exists.
**Missing** means no converter counterpart exists in the inspected target.
**Unsupported** means the current converter explicitly omits the family.
**Requiring approval/contract evidence** means a write, reuse, or mapping cannot proceed on observation alone.
The gate column adds a condition to the current target state.

## Source-to-Target Coverage Matrix

Each row defines an independent acceptance check.
All remaining work appears in [tasks](../tasks.md).
No target behavior is inferred from another agent's dirty worktree.

| Row | Observed source capability | Source | Current target and state | Required target check | Requirements | Tasks | Gate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C01 | Stored file listing and prepopulation | S2, S5 | Missing. Upload only. | List only private contained supported files. | FR-001, FR-028 | T007, T008 | Private storage policy |
| C02 | Browser upload and file selection | S1, S2, S9 | Partial. Transient multipart upload exists. | Stored selection and drag/drop produce the same validated input. | FR-001, FR-002 | T007, T008 | No source UI reuse |
| C03 | Display-only structured configuration | S3, S5 | Missing. Target shows proposal JSON only. | Show sectioned observations without conversion or cloud calls. | FR-003, FR-004 | T009, T010 | Redacted review |
| C04 | Branch, Hub, Standalone roles | S4, S5, S9 | Partial. Only spoke and standalone template types exist. | Exercise three explicit roles with no inferred site creation. | FR-005, FR-014 | T011, T012 | Role contract |
| C05 | SRX and SSR family selection | S3, S5, S9 | Missing. No hardware controls. | Exercise both families with each role. | FR-006 | T011, T012 | Hardware evidence |
| C06 | Model and port mapping | S4, S6 | Unsupported. Current output warns about mappings. | Verify model inventory and explicit valid port assignments. | FR-006, FR-007 | T011, T012 | Model contract |
| C07 | System identity and location review | S4, S6 | Unsupported. No hostname/location parser. | Inspect identity and location without automatic cloud creation. | FR-004, FR-013 | T009, T010 | Privacy |
| C08 | Interface addressing, WAN/LAN, VLAN, aggregation | S5, S6 | Unsupported. DNS only. | Test ambiguity, missing ports, subinterfaces, speed, and VLAN ranges. | FR-007 | T013, T014 | Model and payload contracts |
| C09 | DHCP pools and excluded ranges | S5, S6, S7 | Unsupported. DNS only. | Test valid ranges, overlaps, exclusions, and invalid masks. | FR-007 | T013, T014 | Payload contract |
| C10 | Static routes, VRFs, and BGP | S4, S5, S6 | Unsupported. DNS only. | Preserve routing intent or show explicit unresolved items. | FR-007, FR-008 | T013, T014 | Payload contract |
| C11 | Global IPv4 DNS addresses | S4, S6 | Implemented in offline blueprint only. | Retain unique addresses and reject contextual or malformed directives. | FR-007, FR-010 | T005, T013 | Payload evidence for apply |
| C12 | DNS suffixes, NTP, and variables | S4, S6 | Unsupported except C11. | Validate inheritance, variable resolution, and unresolved references. | FR-008, FR-014 | T013, T014 | Payload contract |
| C13 | Syslog, SNMP, and management egress | S4, S6 | Unsupported. DNS only. | Verify destination object and avoid secret/location disclosure. | FR-008, FR-028 | T015, T016 | Conflicting source claims |
| C14 | AAA, TACACS, and local accounts | S4, S6 | Unsupported. Values omitted. | Review identity intent with no decoded secrets or hash recovery. | FR-008, FR-028 | T015, T016 | Identity and secret contract |
| C15 | ACLs, classes, policies, zones, and crypto review | S6 | Unsupported. Source parser families are not proof of conversion. | Review each family and distinguish display-only from verified conversion. | FR-004, FR-008 | T009, T015, T016 | Family contract |
| C16 | Cellular profiles and redundancy review | S6 | Unsupported. Source family identifiers include cellular and HSRP parsing. | Show observations and explicit hardware-specific limits. | FR-004, FR-008 | T009, T015, T016 | Family contract |
| C17 | Flow export review and limits | S4, S6 | Unsupported. Source documents a conversion gap. | Show display-only limits. Do not generate raw device commands. | FR-008, FR-030 | T015, T016 | Owner decision for any later workaround |
| C18 | Proposal inspection and export | S1, S3, S5 | Partial. Reviewed DNS JSON export exists. | Show structured changes, omissions, object identities, and exact export. | FR-009, FR-011 | T017, T018 | Proposal contract |
| C19 | No-credentials preview | S1, S3 | Implemented in offline blueprint only. | Keep local inspection available and mark checks unavailable. | FR-010, FR-012 | T005, T019, T020 | No live credentials |
| C20 | Mist connection and permission status | S5 | Missing in converter. | Distinguish unavailable, denied, failed, pending, and verified states. | FR-012, FR-027 | T019, T020 | Read contract |
| C21 | Existing/new site and gateway selection | S4, S5, S9 | Missing in converter. | Use stable IDs and distinguish empty inventory from failed lookup. | FR-012, FR-013 | T019, T020 | Read and assignment contracts |
| C22 | Templates, profiles, variables, and site settings | S4, S5 | Requiring approval/contract evidence. No converter write path. | Verify role/object contracts, inheritance, and preservation. | FR-014, FR-015 | T003, T021, T022 | API and owner |
| C23 | Typed apply and cancellation | S2, S3, S5 | Missing. Review button is export approval only. | Exact APPLY, current scope, cancel reset, and zero refused writes. | FR-015, FR-016, FR-017 | T021, T022 | API and owner |
| C24 | Write execution, duplicate prevention, and retry | S5 | Requiring approval/contract evidence. Source route existence proves no safety guarantee. | Test duplicate submission, stale state, 429, timeout, and unknown results. | FR-018, FR-019 | T021, T022 | API and owner |
| C25 | Power-user visibility and permissions | S2, S5, S9 | Missing in converter. | Hidden by default and denied server-side without permission. | FR-021, FR-024 | T025, T026 | Owner |
| C26 | Policy, service, and network backups | S2, S5 | Missing in converter. | Complete paginated private backups with manifests and UTC timestamps. | FR-021, FR-028 | T023, T024 | Storage and read contracts |
| C27 | Three backup listing journeys | S5, S9 | Missing in converter. | List only contained verified backups in the correct object family. | FR-021, FR-028 | T023, T024 | Storage policy |
| C28 | Policy, service, and network restore | S2, S5 | Requiring approval/contract evidence. No converter recovery path. | Resolve name conflicts explicitly and verify each update/create result. | FR-020, FR-022, FR-024 | T027, T028 | API and owner |
| C29 | Delete services, networks, and templates | S5, S9 | Requiring approval/contract evidence. No converter path. | Exact reviewed object scope, backup, two confirmations, and refusal tests. | FR-023, FR-024 | T025, T026 | API and owner |
| C30 | Unassign site templates and templated devices | S5, S9 | Requiring approval/contract evidence. No converter path. | Preserve unrelated references and require fresh scope approval. | FR-023, FR-024 | T025, T026 | API and owner |
| C31 | Recovery after partial apply | S2 backup behavior, target safety requirement | Missing. Source documentation gives no atomic rollback guarantee. | Reconcile each result and restore only approved recorded changes. | FR-020, FR-019 | T027, T028 | API and owner |
| C32 | Pink/charcoal centered selection card | S3 and supplied visual facts | Partial. Portal magenta theme exists, converter lacks card layout. | Independently author centered card in the real portal shell. | FR-025, FR-026 | T029, T030 | Legal review before reuse |
| C33 | Structured review and proposal/confirmation flow | S3 and supplied visual facts | Partial. Proposal preformatted text and two buttons only. | Distinct input review, change review, confirmation, and cancel states. | FR-025, FR-027 | T017, T018, T029, T030 | No source assets |
| C34 | Four configured visual intentions | S2, S9 | Partial. Host theme manager exists, no converter parity evidence. | Map pink, red, neon, and green intentions to approved host themes. | FR-026 | T029, T030 | Owner visual acceptance |
| C35 | Responsive, keyboard, loading, error states | S2, S3, S9 | Partial. Status text and reset logic exist in isolated page. | Test focus, contrast, narrow screens, stale responses, and recovery. | FR-025, FR-027 | T029, T030 | Visual acceptance |
| C36 | Health and shared deployment behavior | S2, S5 | Partial. Host `/health` exists, converter not registered. | Preserve existing health and service ownership without another stack. | FR-027, FR-029 | T031, T032 | Integration owner |
| C37 | Path, size, encoding, and parser boundary safety | S2, S7 | Partial. Upload validation exists, stored path flow absent. | Test exact bounds, symlinks, invalid text, malformed masks, and banners. | FR-002, FR-028 | T007, T009, T031 | No live data |
| C38 | Credential, response, and log safety | S2, S7 | Partial. Current unknown values are omitted and session stores digests. | Prove no secrets in richer review, backups, browser state, or logs. | FR-028, FR-032 | T006, T015, T031 | Security evidence |
| C39 | Independent test category parity | S7 | Partial. Unit, route, and isolated browser DNS tests exist. | Cover each observed category with original fixtures and negative tests. | FR-030, FR-032 | T031, T032 | No copied tests |
| C40 | License and provenance | S8 | Requiring approval/contract evidence. Observation only. | Obtain legal review before reuse and audit independent authorship. | FR-031 | T001, T002, T033 | Legal and owner |

## Complete Source Route Inventory

There are 24 observed route decorators.
Identifiers describe externally visible contracts, not copied implementation.
New target routes must use the converter namespace and existing portal controls.
Existing preview, review, and export paths must remain compatible.

| Source method and path | Coverage row | Target counterpart |
| --- | --- | --- |
| GET `/` | C32, C36 | Existing portal shell plus future converter entry |
| GET `/health` | C36 | Existing portal `/health`, unchanged |
| GET `/api/mist-status` | C20 | Future converter status |
| GET `/api/site-gateways/<site_id>` | C21 | Future selected-site gateway inventory |
| GET `/api/unassigned-gateways` | C21 | Future unassigned gateway inventory |
| GET `/api/files` | C01 | Future contained file catalog |
| POST `/api/upload` | C02 | Future bounded upload |
| POST `/api/convert` | C18 | Existing preview extended without breaking current clients |
| POST `/api/display` | C03 | Future independent parsed review |
| POST `/api/apply` | C23, C24 | Future gated apply |
| POST `/api/poweruser/unassign-all-templates` | C30 | Future scoped site-template detachment |
| POST `/api/poweruser/delete-all-templates` | C29 | Future scoped template deletion |
| POST `/api/poweruser/unassign-templated-devices` | C30 | Future scoped profile/device detachment |
| POST `/api/poweruser/backup-service-policies` | C26 | Future policy backup |
| GET `/api/poweruser/list-service-policy-backups` | C27 | Future policy backup catalog |
| POST `/api/poweruser/restore-service-policies` | C28 | Future policy restore proposal |
| POST `/api/poweruser/backup-services` | C26 | Future service backup |
| GET `/api/poweruser/list-service-backups` | C27 | Future service backup catalog |
| POST `/api/poweruser/restore-services` | C28 | Future service restore proposal |
| POST `/api/poweruser/delete-all-services` | C29 | Future reviewed service deletion |
| POST `/api/poweruser/backup-networks` | C26 | Future network backup |
| GET `/api/poweruser/list-network-backups` | C27 | Future network backup catalog |
| POST `/api/poweruser/restore-networks` | C28 | Future network restore proposal |
| POST `/api/poweruser/delete-all-networks` | C29 | Future reviewed network deletion |

## Implementation Readiness Evidence

S5 identifies the route functions below at source revision `d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c`.
The existing route inventory and coverage matrix give each target disposition.
These function and test identifiers are citations, not reusable source expression.
The target fixtures and tests must be independently authored.

| Source evidence | Coverage | Synthetic fixture and refusal evidence still needed |
| --- | --- | --- |
| `index`, `list_files`, `upload_file`; S7 `test_path_containment.py` | C01-C02, C37 | Empty catalog, supported suffixes, exact size, invalid UTF-8, collision, traversal, absolute paths, and symlink escape. |
| `display_config`, `convert_config`; S7 `test_conversion.py`, `test_regex_safety.py` | C03-C18 | Original inputs for each parser family, invalid masks, hostile lengths, missing hostname, ambiguous ports, unsupported features, and no cloud calls. |
| `health`, `mist_status`, `get_site_gateways`, `get_unassigned_gateways` | C19-C21, C36 | Offline, denied, failed, empty, paginated, duplicate-name, and wrong-organization simulated responses. |
| `apply_config`; S7 `test_missing_confirmation_is_rejected_before_mist_calls`, `test_wrong_confirmation_is_rejected_before_mist_calls` | C22-C24 | Current and stale proposal, changed target, missing approval, exact typed word, backup failure, duplicate request, partial write, timeout, and unknown result. Assert zero writes for refusals. |
| `poweruser_unassign_all_templates`, `poweruser_unassign_templated_devices`, `poweruser_delete_all_templates` | C25, C29-C30 | Disabled permission, explicit IDs, changed relationships, unrelated objects, backup failure, and interrupted operations. |
| `poweruser_backup_service_policies`, `poweruser_list_service_policy_backups`, `poweruser_restore_service_policies` | C26-C28 | Policy pages, invalid manifest, wrong organization, duplicate names, private access, and partial restore. |
| `poweruser_backup_services`, `poweruser_list_service_backups`, `poweruser_restore_services`, `poweruser_delete_all_services` | C26-C29 | Service pages, corrupt backup, scope confirmation, create/update ambiguity, deletion refusal, and recovery conflict. |
| `poweruser_backup_networks`, `poweruser_list_network_backups`, `poweruser_restore_networks`, `poweruser_delete_all_networks` | C26-C29 | Network pages, corrupt backup, scope confirmation, duplicate objects, deletion refusal, and recovery conflict. |
| S7 `test_error_responses.py`, `test_sensitive_logging.py`, `test_flask_debug.py` | C37-C39 | Safe error shape, secret-free logs, exception redaction, debug disabled, and no credential or customer data in any fixture. |
| S7 `test_documentation.py`, `test_workflows.py` | C39-C40 | Independently written link, license, browser, and workflow checks. Do not copy test bodies or screenshots. |

Each write family also needs schema-positive and schema-negative fixtures, 4xx, 5xx, 429, and malformed-response tests.
Exercise backup verification, lock loss, restart, reconciliation, and unrelated changes with simulated services.
Use no production credentials, real customer configurations, or live requests.

### Readiness Decisions

- [ ] Legal and repository owners record a CC BY-NC 4.0 review and the independent-authorship and distribution decision.
- [ ] The integration owner grants the exact shared file ownership and portal handover.
- [ ] The cloud owner approves each enabled object family, scope, retention policy, and recovery limits.
- [ ] The owner approves authenticated operator identity and server-side authorization. An IP allowlist is not identity.
- [ ] API owners verify each field, schema, role, model, method signature, response, and failure fixture.
- [ ] Storage owners approve private paths and prove browser, scan, download, symlink, backup, and restart boundaries.
- [ ] Operators review the current exact scope, verified backup, proposal, and typed confirmation for each cloud write.
- [ ] The visual owner accepts independent target journeys and all missing or unsupported dispositions.

These are open gates, not approvals granted by the discovery pass.
See [portal integration blockers](contracts/portal.md) and [write contracts](contracts/mist.md).

## Test Category Comparison

Source tests were inspected, not executed or copied.

| Source category | Current target evidence | Remaining evidence |
| --- | --- | --- |
| Conversion and apply confirmation | DNS unit and route tests | Full family fixtures and zero-write apply refusals |
| Documentation integrity | No converter-specific equivalent inspected | New guide links and provenance |
| Safe error responses | Invalid input and stale proposal tests | Every cloud and administrative failure shape |
| Debug defaults | Existing shared host, unchanged | Converter registration must not enable debug |
| Path containment | Upload filename tests | Stored input and backup symlink containment |
| Regex boundaries | Banner tests only | Address text, masks, bounded parsing, and size adversaries |
| Sensitive logging | DNS redaction assertions | Identity, decoded values, inventory, location, and recovery |
| Workflow governance | Existing MistHelper gates | Required statuses and unchanged pipeline contracts |

## Visual Journey Comparison

Supplied visual facts are design constraints only.
The walkthrough confirms journey order, not pixel-level target parity.
No rendered target browser comparison was performed during this documentation task.

| Journey | Observed design fact | Current MistHelper counterpart | Required comparison |
| --- | --- | --- | --- |
| Landing | Pink/charcoal theme and centered file-selection card | Magenta portal theme and unregistered simple upload form | Real portal entry, centered card, offline status |
| Selection | File choice followed by role and SRX/SSR controls | Template name and spoke/standalone type only | Three roles, two families, explicit model mapping |
| Input review | Structured display-only review | No counterpart | Sectioned redacted review independent of conversion |
| Proposal | Inspect settings and omissions before apply | DNS JSON review/export only | Object-level change review and uncertain-check labels |
| Confirmation | Typed word, disabled submit, cancel/reset | Export review button, not cloud confirmation | Exact APPLY, changed-scope invalidation, accessible dialog |
| Administration | Grouped backup, restore, delete, unassign controls | No converter counterpart | Permission-gated controls and explicit object scope |
| Status and themes | Offline status and four dark intentions | Shared themes and local status text | All state transitions, host themes, keyboard and narrow screens |

## Decisions

**Decision**: Independently author requirements, fixtures, mappings, and presentation.
**Rationale**: CC BY-NC 4.0 is not permission for unrestricted reuse in MistHelper.
**Alternatives considered**: Copying implementation, CSS, screenshots, prose, or tables is prohibited without legal approval.
Public availability and common ownership do not establish license compatibility.

**Decision**: Verify every mapping against current target OpenAPI, installed SDK signatures, and independent tests.
**Rationale**: S4 includes older SDK claims and inconsistent syslog placement statements for Hub profiles.
**Alternatives considered**: Treating S4 as API truth risks incorrect object placement and inheritance.
No source mapping table or workaround command is reproduced here.

**Decision**: Preserve display-only families when conversion lacks verified support.
**Rationale**: Parsed ACL, policy, crypto, cellular, redundancy, and flow data do not establish a safe Mist transformation.
**Alternatives considered**: Silent omission loses operator visibility. Unverified conversion risks production changes.
A confirmed unsupported conversion retains its review and warning journey.

**Decision**: Separate offline completion, contract completion, integration ownership, and cloud approval.
**Rationale**: A complete plan can name blocked work without pretending that approval exists.
**Alternatives considered**: Deferring all planning loses scope. Enabling writes before approval violates safety.

**Decision**: Use a timestamp record and command-scoped feature selection.
**Rationale**: The merged numeric record must remain unchanged.
**Alternatives considered**: Reusing issue 4224's record would mix completed history with unverified migration work.
PowerShell is absent. The route was independently calculated using the resolver's 17-digit base-5 UTC rule.
Nineteen parents passed containment, ownership, and capacity checks.
The standard allocation and setup commands remain unexecuted because their interpreter is unavailable.
No `.specify/feature.json` update is necessary for this explicitly scoped documentation workflow.

## Hook and Template Handling

Parsed `.specify/extensions.yml` with the worktree YAML reader during validation.
The Git branch hook conflicts with the requested app-managed branch and documentation-only restriction.
Do not execute that hook.
Decline every optional commit hook before and after specify, plan, tasks, and analyze.
Companion hooks are disabled.
No extension configuration changed.
Use the core spec, plan, task, and checklist templates.
No preset or template override was present in the inspected override stack.
