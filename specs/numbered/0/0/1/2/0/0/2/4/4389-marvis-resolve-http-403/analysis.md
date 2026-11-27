# Analysis: Issue 4389 consistency review

**Scope**: `spec.md`, `plan.md`, `tasks.md`, `design/`, and the remote code, tests, and documents that the record cites. The remote evidence is listed in `design/research.md`.

**Base**: remote `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. Local HEAD is the same commit. Eight cited files have a local git blob hash that equals the remote blob hash, so local and remote line numbers match for those files.

## Consistency checks

| ID | Check | Result | Evidence |
| - | - | - | - |
| C-1 | Each FR maps to a task and a test | Pass | The requirement map below. |
| C-2 | Each task names exact paths and one verification command | Pass | `tasks.md`. Final tasks use GitHub checks, because the local gates table has no remote step. |
| C-3 | Issue facts match the code path | Pass | Issue 4389 shows outcome `error` and an empty `verified_status`. `_send` marks `OUTCOME_ERROR` (`operation.py` line 288). `_verify` skips rows without `OUTCOME_SENT` (line 484). |
| C-4 | The owner comment matches the code | Pass | The owner states that only HTTP 2xx counts as success (`client.py` line 187). The owner states that the body returns to the results path (`client.py` lines 309 and 310). |
| C-5 | Remote and local blobs match for cited files | Pass | Eight files match. The check used the Git blob formula on local bytes. |
| C-6 | Count of remote checks matches | Pass | `design/research.md` and `STATUS.json` each list 54 remote checks. Five are absent. |
| C-7 | Count in the summary matches | Pass | `summary.md` states 54 checks. |
| C-8 | Five-item rule for new files | Pass | No file is added in a noncompliant folder. The new fragment sits in `changelog.d/`, which the repository workflow requires. |
| C-9 | Gate applicability | Pass | Four gates are not applicable, and `tasks.md` gives the reason for each. |

## Requirement map

| Requirement | Tasks | Tests |
| - | - | - |
| FR-001 | T001, T002 | T002 |
| FR-002 | T003, T008 | T003 |
| FR-003 | T003, T008 | T003 |
| FR-004 | T004, T009 | T004 |
| FR-005 | T004, T009 | T004 |
| FR-006 | T005, T009 | T005 |
| FR-007 | T006, T010 | T006 and the existing path test |
| FR-008 | T007, T006 | T006 and the existing tests T007 lists |
| FR-009 | T011, T012, T015 | T015 |
| FR-010 | T002 to T006, T015 | The tests named in each task |
| FR-011 | T013 | `tests/guardrails/test_changelog_fragment_policy.py` |

## Defects in existing work

| ID | Finding | Disposition |
| - | - | - |
| A-1 | Menu 270 mode 3 is `interactive_safe` (`operation_registry.py` line 347). The constitution lists other changes to the Mist cloud as destructive (line 120). The repository definition of destructive says a destructive operation changes the Mist cloud (`copilot-instructions.md` line 311). The portal label says mode 3 changes Mist (`web_portal/services/operation.py` line 654). | Not changed by this record. The required typed confirmation exists. The category conflict needs one separate issue. The needs-human-review label stays on issue 4389. |
| A-2 | The resolve loop sends a request for each Marvis Action after a refusal. The loop stops only for the stop signal (`operation.py` line 244). | Fixed by FR-004 and task T009. |
| A-3 | The raw Mist body reaches the results file (`client.py` lines 309 and 310) and the WARNING log (`operation.py` line 289). The issue states that the body was not reviewed. | Fixed by FR-002 and FR-003 and task T008. |
| A-4 | No unit test sends HTTP 403 to the resolve request. The resolve block of `test_client.py` (class `TestResolveRequest`, lines 358 to 418) has tests for HTTP 400, 429, 500, and 503. No run-level test sends a refused PUT with HTTP 403 (`test_operation.py`). | Fixed by tasks T002 to T006. |
| A-5 | The endpoint report says no live resolve ran (`marvis-actions-api-endpoints.md` line 582). Issue 4389 reports a live resolve with HTTP 403. The report is out of date. | Fixed by task T011. |
| A-6 | The labs path is absent from the public OpenAPI document and from the pinned SDK. The client calls the path through the generic session method. | Recorded as unverified (U-1). No code change follows from this item. |
| A-7 | `src/mist/intelligence/marvis/actions/` holds seven direct children on remote `main`. The five-item rule allows five. | Pre-existing debt. The plan adds no child. A separate refactor can address it. |
| A-8 | Mistapi logs each HTTP error with the exception text (`.venv\Lib\site-packages\mistapi\__api_request.py` lines 228 to 258). The text can include the request URL, which holds the organization identifier. The exact text is not verified in this record. Mistapi code sits outside this repository. | Recorded only. An organization identifier is not a credential under the constitution. |

## Parallel work and open pull requests

- The open pull requests number seven. None changes a path under `marvis`, `operation_registry.py`, `web_portal/services/operation.py`, `MistHelper.py`, or `menu_registry.py`.
- Issue #4008 is open. Its title is "Refactor: isolate Marvis alarm handling modules". The planned change does not touch the alarm modules. Task T-PR checks overlap again before the pull request opens.

## Unresolved items

| ID | Item | Owner | Reason it stays open |
| - | - | - | - |
| U-1 | The meaning of HTTP 403 for the labs suggestions path | Human with a lab session | No public or local source describes the labs path. |
| U-2 | The role that the 2026-10-21 token held | Human with Mist UI access | The repository does not record the role. |
| U-3 | Whether the Mist UI shows the same control to the same account | Human with Mist UI access | This check needs the Mist UI and no live API call from this record. |
| U-4 | The credential choice for mode 3 runs (D-7) | Human | Credential policy is a human decision. |
| U-5 | The category conflict (A-1) | Human, through a separate issue | Product and safety classification decides the category. |
| U-6 | The first live response to a resolve request after this change | Operator | The operator runs one approved request in the lab organization. Tests do not call Mist. |
| U-7 | A UUID cut by the 300-character limit | Accepted risk | A partial identifier of 35 characters or fewer can remain. It is not a complete identifier. |
| U-8 | Live coverage of the resolve path | Issue 3341 | Issue 3341 is open and tracks the live resolve gap. This record does not close it. |
