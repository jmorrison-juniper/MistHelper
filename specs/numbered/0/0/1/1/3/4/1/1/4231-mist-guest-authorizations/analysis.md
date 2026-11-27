# Analysis: Migrate Mist Guest Authorizations (issue #4231)

## 1. Consistency review

| Check | Expected | Found | Result |
| --- | --- | --- | --- |
| Functional requirements | 30 (FR-001 to FR-030) | 30 | pass |
| Success criteria | 8 (SC-001 to SC-008) | 8 | pass |
| Tasks | 31 (T001 to T027 and four closing tasks) | 31 | pass |
| Test catalog | 49 (TC-001 to TC-049) | 49 | pass |
| Requirement coverage | Each FR has a task and a test | 30 of 30 | pass |
| Decisions | 17, each with alternatives, choice, reason, risk, and recommendation | 17 | pass |
| Human decisions | 2 (D-11 and D-13) | 2 | pass |
| Remote check rows | STATUS count equals research table count | 134 and 134 | pass |
| Legacy claims | 26 rows: 17 verified, 4 stale, 2 absent, 3 unverified | 26 | pass |
| Child counts (guard convention) | Five or fewer per directory | `portals` 5, `access` 4, `guests` 2, `guest_authorizations` 4, `workflows` 4, `presentation` 1 | pass |
| Verification commands | Taken from the local gates table | pytest, ruff, and STE commands match the table | pass |
| Typed words | One word per operation | GRANT, CHANGE, EXTEND, REVOKE, IMPORT | pass |
| Route and tab names | One term per concept | "Guest Access" tab, `/guest-access` routes | pass |

## 2. Defects in existing work

### 2.1 Legacy record on remote main

| ID | Defect | Evidence | Resolution |
| --- | --- | --- | --- |
| LD-1 | The plan targets Python 3.13. | L-18, R-81 | This plan targets Python 3.15. |
| LD-2 | The plan places code in `guest_workflows/`, which gives `portals` six children. | L-19, R-38, R-35 | D-2 converts the module into a package. |
| LD-3 | The checklist sits at the feature root. | L-20, R-90 | This draft places it at `design/checklists/`. |
| LD-4 | `analysis.md` is absent. | L-22, R-91 | This file fills the gap. |
| LD-5 | The API source is the OpenAPI 3.0 JSON file. | L-21, R-74 | Citations use the 3.1 YAML (R-64 to R-73). |
| LD-6 | Checkpoint commit `20cf234e2` does not exist. | L-23, R-92 | The record does not cite it. |

### 2.2 Pinned source at `0213240cb9edfa237f763acd156b90a6049363cb`

| ID | Defect | Evidence | Resolution |
| --- | --- | --- | --- |
| SD-1 | Authorize writes at organization scope after a site failure. | R-127 (line 592), exception at line 586 | D-3 keeps site scope only. |
| SD-2 | Guest listing falls back to the organization-wide list after an exception. | R-125 (line 423), exception at line 418 | Not reproduced. |
| SD-3 | Deauthorize sends `minutes` 0 with no WLAN check. | R-128 (line 652) | D-4 adds a WLAN check and a read-back. |
| SD-4 | Authorize reports success without a 2xx check. | `authorize_guest` at R-126 (lines 487 to 619) | FR-016 and D-7 require 2xx. |
| SD-5 | `field4` is overwritten with the token name. | `mist_connection.py` lines 550 to 552 | D-6 never writes `field4`. |
| SD-6 | Silent 1440-minute defaults. | R-120, R-123, R-132 | D-8 forbids import defaults. |
| SD-7 | The UI allows 2628000 minutes. | R-131, R-68 | D-5 uses 259200. |
| SD-8 | Delete has no confirmation step. | R-133, R-134 | D-7 uses typed words. |
| SD-9 | The guide promises five years and says DELETE does not remove guests. | R-116, R-118 | D-4 and D-5 correct both. |
| SD-10 | Exceptions turn into logs or empty results. | Exception branches at lines 483 to 484 and 803 | FR-021 requires an error, not an empty result. |

## 3. Defects found in this draft and fixed

| ID | Defect | Fix |
| --- | --- | --- |
| DD-1 | FR-026 barred full MAC addresses from journal entries, but reconciliation after a crash needs the full address. | FR-026 now bars full MAC addresses from logs and audit events only. The journal keeps the full address for reconciliation (spec, research D-9, data model, audit contract). |
| DD-2 | The first draft invented `ste-linter` commands for files outside the gates table. | Verification commands now match the local gates table. The STE command is copied exactly. |
| DD-3 | The first draft listed `templates/` and `static/` as children of `presentation/`. The guard counts only directories that hold Python files. | Child counts follow the guard convention (guard line 117). |
| DD-4 | The first draft paraphrased constitution rule names and listed rules it had not read in full. | The plan uses the constitution headings. The SpecKit and Multi-agent sections (lines 420 and 453) were checked by heading only. |
| DD-5 | TC-027 sat in the contract file in one place and in the integration file in another. | TC-027 belongs to the integration file. TC-022 to TC-026 belong to the contract file. |
| DD-6 | Several prose sentences exceeded the 25-word description limit, and four placeholder-like tokens appeared. | Each sentence was shortened, and each token became concrete text. |

## 4. Unresolved items

| ID | Item | Owner | Blocks | Status |
| --- | --- | --- | --- | --- |
| U-1 | Operator identity method (D-11). HUMAN-DECISION-REQUIRED. | Maintainer | All guest writes | open |
| U-2 | Licensing path for any reuse of source expression (D-13). HUMAN-DECISION-REQUIRED. | Maintainer | Any copy of source text | open |
| U-3 | Gate G5: WLAN binding on grant, the effect of minutes 0 on revoke, and the site list response shape. | Implementation owner, with an approved nonproduction tenant | All writes (D-16) | open |
| U-4 | PR #4208 handover of `web_portal/app.py` and `base.html`. | Owner of PR #4208 | Task T013 | open |
| U-5 | Issue #4936 browser sign-in for port 8055. | Owner of issue #4936 | Identity option (a) in D-11 | open |
| U-6 | The brief requires `Closes #4231` (D-17). PR #4290 and the issue comments ask to keep #4231 open. | Orchestrator | Wording of the T-PR body | open |
| U-7 | The constitution (lines 315 to 317) refers to "the declared operational store." AGENTS.md, the copilot instructions, and the documentation do not name it. | Maintainer | Confirmation that ArangoDB is the declared store | open |
| U-8 | Template and site-group WLAN inheritance. The source resolves it at `mist_connection.py` lines 245 to 283. | Implementation owner | Out of scope for version 1 | open |
| U-9 | The projection test total of 22 cases (L-25). | Implementation owner | None | unverified |
| U-10 | GitHub license metadata for the source (L-26). | Orchestrator | None | unverified |
| U-11 | Commit `1e9b280dd` tree contents (L-24). | Orchestrator | None | unverified |
| U-12 | The local source checkout differs from its remote. | Orchestrator | None, because remote blobs are used | information |

## 5. Checks not run

- No tests, linters, builds, containers, or repository scripts ran (brief rule 2).
- The STE gate in the local gates table grades README.md, AGENTS.md, the copilot instructions, CLAUDE.md, and the STE writing guide. It does not grade this record. Section 6 gives the record check.
- No live Mist request ran. No credential was read.
- Browser behavior, live mistapi behavior, and CSV parsing were not run.

## 6. Style and placeholder checks

Each check ran as a read-only search over the record files.

- Semicolons: none found.
- Contractions: none found.
- Latin abbreviations: none found.
- Phrasal verbs from the check list: none found.
- Placeholder tokens: none remain after the fixes in section 3.
- Prose sentences over 25 words: none remain after the fixes. Table cells hold structured data and are not counted.
- Human marker: `HUMAN-DECISION-REQUIRED` appears on D-11 and D-13 only.

## 7. Count reconciliation

| Count | Value | Source |
| --- | --- | --- |
| Requirements | 30 | spec.md |
| Success criteria | 8 | spec.md |
| User stories | 7 | spec.md |
| Tasks | 31 | tasks.md |
| Planned tests | 49 | design/quickstart.md section 4 |
| Decisions | 17 (2 human) | design/research.md section 7 |
| Remote check rows | 134 | design/research.md section 8 and `4231-STATUS.json` |
| Legacy claims | 26 (17 verified, 4 stale, 2 absent, 3 unverified) | design/research.md section 3 |

## 8. Reading coverage

- `AGENTS.md`: the cited sections (lines 40, 157, 172, and 345) and the headings were read. The full file was not read in this pass.
- `.github/copilot-instructions.md`: the local gates table (lines 44 to 80) and the headings were read. The full file was not read in this pass.
- `.specify/memory/constitution.md`: lines 1 to 380 were read. Lines 380 to 526 were checked by heading only.
- `.specify/templates/`: not read in this pass. The layout follows brief section 4.
- Quality, architecture, and setup documents: not cited in this record. The operator guide and the container deployment guide were checked only at the cited lines and for existence.
