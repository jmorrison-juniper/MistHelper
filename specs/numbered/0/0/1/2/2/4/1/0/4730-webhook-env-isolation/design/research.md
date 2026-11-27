# Research: Webhook config test isolation

## Summary

Issue #4730 reports that the test `test_the_factory_stores_an_empty_secret_when_the_variable_is_absent` depends on the environment variable `WEBHOOK_ENABLED`. PR #4843 merged the one-line repair on 2026-11-19. Remote checks R-01 to R-09 prove the merged state. The open work is verification, issue closure, and a comment-only follow-up for Principle VI.

## Issue Facts

- State: OPEN. Created 2026-11-10T02:18:37Z. Updated 2026-11-10T09:29:24Z. Author: `jmorrison-juniper`.
- Labels: `bug`, `test`, `tests`, and `in-progress`.
- Requirement: The test sets its own default-state preconditions. No production behavior change is requested.
- Reproduction steps: four steps. Quickstart Q-0 gives the exact commands.
- Error text: `E   assert False is True` at `assert app.config["WEBHOOK_ENABLED"] is True`.
- Comment 1 (2026-11-10T02:19:01Z): reserves the test file. Names blob `372302985df902560df4c497d8b3dc1e07bc407e` at `3964d21d`.
- Comment 2 (2026-11-10T02:23:24Z): names local commit `5e55cca` and repaired blob `bcf0ad12`. Reports a hook bypass warning.
- Comment 3 (2026-11-10T02:25:21Z): reports an independent replay and a mutation check. Not reproduced (U-2, U-3).
- Comment 4 (2026-11-10T09:29:23Z): reports a hook audit. Says the clone needs authorization (D-5).
- The body names related evidence in #2711 and holds for #4358 and serial publication.

## Decisions

### D-1. Treat the repair as merged. Verify it on main. Add no second repair branch.

- Alternatives: (a) Open a new branch that applies the one-line repair again. (b) Verify the merged repair and add only the missing comments in a follow-up.
- Chosen: (b).
- Reason: The merged blob equals the repaired blob (R-01, R-08). PR #4843 changed one file with one added line (R-09). Quality Gates run 45774119357 passed the root unit shard on `f03c6c9` (R-21).
- Risk: CI evidence is not a local run. Step A of T-LOCAL-GATES runs the file locally in two states.
- Human decision required: no.

### D-2. Close issue #4730 after step A passes. The orchestrator closes it and removes `in-progress`.

- Alternatives: (a) The executor closes the issue now. (b) The orchestrator closes the issue after step A passes. (c) Keep the issue open until the follow-up merges.
- Chosen: (b).
- Reason: The authoring process forbids GitHub writes by the spec author. The repair is verified (R-01 to R-09). The comment gap is a separate subject, so it has its own issue (`AGENTS.md` line 183). An open issue shows a false state for `main` (A-1).
- Risk: The issue closes before a local run. Step A runs before the closure. A closed issue can be reopened (quickstart Q-6).
- Human decision required: no.

### D-3. Repair the missing inline comments in a comment-only follow-up under a new issue.

- Alternatives: (a) Accept the gap with a waiver. (b) Open a new issue and make a comment-only follow-up. (c) Reopen issue #4730 and push to the merged branch.
- Chosen: (b).
- Reason: Principle VI is NON-NEGOTIABLE. It states that code without comments MUST NOT be merged (`.specify/memory/constitution.md` line 204 and R-25). `AGENTS.md` line 233 section "Merge" forbids a push after a squash merge. It requires a new issue and a new branch from `main`.
- Risk: One more pull request. Checks TC-005, TC-006, and TC-008 limit the change to comments.
- Human decision required: no.

### D-4. Add no changelog fragment to the follow-up. State the internal-only reason in the pull request body.

- Alternatives: (a) Add a fragment named `issue-<NEW-ISSUE>-webhook-test-comments.md`. (b) Add no fragment and state the reason in the pull request body.
- Chosen: (b).
- Reason: `changelog.d/README.md` rule 4 exempts internal-only changes (R-28). The changelog guard requires no fragment for each change (R-29). PR #4843 passed CI with no fragment. The constitution wording differs (R-26). The constitution supersedes practice documents (R-27). Analysis item A-5 records the conflict.
- Risk: The constitution wording is not met. FR-013 requires the reason in the pull request body. The owner reviews A-5.
- Human decision required: no.

### D-5. Treat the publication and hook-compliance holds as superseded. Run normal hooks. Create no clone.

- Alternatives: (a) Create an independent clone with a private hook path. Issue comment 4 says that this needs explicit authorization. (b) Run the follow-up with normal hooks and rely on remote CI. (c) Hold all work until the owner releases the holds.
- Chosen: (b).
- Reason: The commit with the hook bypass (`5e55cca`) is not an ancestor of `main` (R-06). The merged commit is a GitHub squash commit (R-08). Remote CI runs every gate on each pull request (R-21). The serial merge slot rule (R-23) governs T-MERGE, and the orchestrator authorizes T-MERGE.
- Risk: The bypass history remains in the issue comments (U-5). FR-012 and check TC-012 block any bypass in the follow-up.
- Human decision required: no.

### D-6. Keep scope to issue #4730. Record that no sibling test depends on the default.

- Alternatives: (a) Extend the record to each test that touches webhook settings. (b) Keep the scope and record the sibling evidence.
- Chosen: (b).
- Reason: `AGENTS.md` line 183 section "Issue first" says that one issue holds one subject. The sibling tests set the variable themselves (R-13, R-14, R-15). The unit conftest holds no handling (R-16).
- Risk: A sibling defect can exist outside the searched paths (U-6). Open separate issues after the bodies are read (A-7).
- Human decision required: no.

### D-7. Place the record at the numbered route with the slug `4730-webhook-env-isolation`.

- Alternatives: (a) A timestamp route under `specs\live\`. (b) The numbered route for issue 4730.
- Chosen: (b).
- Reason: Principle I of `.specify/memory/constitution.md` says that numeric records use the eight-level base-5 route. `Resolve-SpecFeaturePath` gives the numbered route for number 4730 (R-30). Check TC-010 confirms the route.
- Risk: The route is wrong if the number mapping changes. TC-010 detects that change.
- Human decision required: no.

### D-8. Omit the contracts folder because no interface contract changes.

- Alternatives: (a) Write a contract file for the webhook route response codes. (b) Omit the folder and state the reason in `plan.md`.
- Chosen: (b).
- Reason: The route, the response codes, and the header contract do not change. `plan.md` records the reason.
- Human decision required: no.

### D-9. Mark Mist SDK checks not applicable. The changed code makes no mistapi call.

- Alternatives: (a) Read the pinned `mistapi` source under `.venv`. (b) Record the checks as not applicable and cite the import evidence.
- Chosen: (b).
- Reason: The test imports at lines 19 to 31 include no `mistapi` module (R-34). The route imports at lines 19 to 27 include no `mistapi` module (`web_portal/routes/webhooks.py`, blob `bd33ba1d2f185fab411631c0b1b91e616b4226e7`). The test uses a recording router, not an SDK call.
- Risk: A future change can add an SDK call. The constitution check in `plan.md` applies to that change.
- Human decision required: no.

### D-10. Mark the Types gate not applicable to the test file. MYPY_PATHS excludes tests.

- Alternatives: (a) Run mypy on the test file. (b) Record the gate as not applicable.
- Chosen: (b).
- Reason: The mypy path list in `.github/workflows/ci.yml` line 93 holds no tests path (R-18, R-19). The change adds comments only.
- Risk: None for this change.
- Human decision required: no.

### D-11. Keep the route reading only `X-Mist-Signature`. Record `X-Mist-Signature-v2` as an out-of-scope observation.

- Alternatives: (a) Add support for the v2 header in this issue. (b) Record the observation and keep the scope.
- Chosen: (b).
- Reason: The issue requests no production change. The v2 header needs its own issue and a contract (A-6).
- Risk: A delivery that carries only the v2 header can fail closed with code 403 (U-10). The owner decides the change.
- Human decision required: no.

## Remote Verification

Each row is one remote check. The `remote_checks` array in `META_DIR\4730-STATUS.json` has the same 38 rows. Ref `main` means the tip `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (R-38). Blob SHAs come from the git tree or the blob API.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| R-01 | Main test file is the repaired blob | tests/unit/web_portal/test_webhook_signature.py | main | bcf0ad12319281ea484e98bba65ff2d544f6b8d3 | present | 0 |
| R-02 | Main test deletes WEBHOOK_ENABLED before the factory call | tests/unit/web_portal/test_webhook_signature.py | main | bcf0ad12319281ea484e98bba65ff2d544f6b8d3 | present | 234 |
| R-03 | Main test asserts the receiver is enabled by default | tests/unit/web_portal/test_webhook_signature.py | main | bcf0ad12319281ea484e98bba65ff2d544f6b8d3 | present | 240 |
| R-04 | Main touched test function carries inline comments | tests/unit/web_portal/test_webhook_signature.py | main | bcf0ad12319281ea484e98bba65ff2d544f6b8d3 | absent | 229 |
| R-05 | Pre-fix blob is the main blob | tests/unit/web_portal/test_webhook_signature.py | main | 372302985df902560df4c497d8b3dc1e07bc407e | stale | 0 |
| R-06 | Commit 5e55cca is on main | tests/unit/web_portal/test_webhook_signature.py | main | bcf0ad12319281ea484e98bba65ff2d544f6b8d3 | stale | 0 |
| R-07 | Commit 3964d21d is an ancestor of main | tests/unit/web_portal/test_webhook_signature.py | main | 372302985df902560df4c497d8b3dc1e07bc407e | present | 0 |
| R-08 | Merge commit 15da34506 is an ancestor of main | tests/unit/web_portal/test_webhook_signature.py | main | bcf0ad12319281ea484e98bba65ff2d544f6b8d3 | present | 0 |
| R-09 | PR 4843 changes one file with plus one and minus zero | tests/unit/web_portal/test_webhook_signature.py | main | bcf0ad12319281ea484e98bba65ff2d544f6b8d3 | present | 0 |
| R-10 | PR 4843 links issue 4730 for automatic closure | pull request 4843 body | main | not applicable (pull request body) | partial | 0 |
| R-11 | Factory reads WEBHOOK_ENABLED with default true | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 129 |
| R-12 | Persistence reader uses WEBHOOK_ENABLED default true | src/foundation/persistence/db/__init__.py | main | 11f8dd6d5f13d04c931e9888bf25c3e968df4173 | present | 69 |
| R-13 | Ingestion test sets WEBHOOK_ENABLED itself | tests/unit/config/standalone/foundation/persistence/redis/test_webhook_ingestion.py | main | 69f44921c2c14f6af4beeb901d9791534b441445 | present | 76 |
| R-14 | E2E journey sets WEBHOOK_ENABLED itself | tests/e2e/web_portal/test_map_site_selection_race_journey.py | main | 51b658421cc74ee53a1c28ce1ca0e11b0d2a9e96 | present | 415 |
| R-15 | Support control sets WEBHOOK_ENABLED itself | tests/support/wip_target_controls/native.py | main | bdea5b10003eed53be35c160b519afbec166d3f0 | present | 190 |
| R-16 | Unit conftest handles WEBHOOK_ENABLED | tests/conftest.py | main | f55885cafab8f4c346ee7d7a813835bab300e45d | absent | 0 |
| R-17 | Compose file sets WEBHOOK_ENABLED | compose.yml | main | b3944fc9f994ca149974072b1a9c8f13797d7924 | absent | 0 |
| R-18 | CI defines MYPY_PATHS | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R-19 | MYPY_PATHS includes the tests folder | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | absent | 0 |
| R-20 | Root unit shard runs tests/unit | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 263 |
| R-21 | Quality Gates run 45774119357 passed the root unit shard on f03c6c9 | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 262 |
| R-22 | Local gates table lists the Tests command | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| R-23 | Serial merge slot rule applies to merges | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 485 |
| R-24 | AGENTS.md defines the inline comment rule | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 97 |
| R-25 | Constitution Principle VI requires inline comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| R-26 | Constitution requires one release-note fragment for each change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| R-27 | Constitution supersedes practice documents | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 529 |
| R-28 | Changelog README exempts internal-only changes | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| R-29 | Changelog guard requires one fragment for each change | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | absent | 0 |
| R-30 | Route script sets the radix base to 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R-31 | Ruff and Black line length is 120 | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 202 |
| R-32 | Folder baseline lists a route entry for specs/numbered/0/0/1/2/2/4 | tests/guardrails/process_folder_baseline.json | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | absent | 0 |
| R-33 | Test quality baseline lists the test file | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | absent | 0 |
| R-34 | Test file imports a mistapi module | tests/unit/web_portal/test_webhook_signature.py | main | bcf0ad12319281ea484e98bba65ff2d544f6b8d3 | absent | 0 |
| R-35 | Record folder for issue 4730 exists on main | specs/numbered/0/0/1/2/2/4/1/0/4730-webhook-env-isolation | main | not applicable (no tree entry) | absent | 0 |
| R-36 | Reference record spec exists on main | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| R-37 | No open pull request changes a webhook path | open pull requests (7 scanned) | main | not applicable (file lists only) | absent | 0 |
| R-38 | Main ref equals local HEAD f03c6c9 | refs/heads/main | main | not applicable (commit f03c6c9b36d612a48d7b9652998c2fd87dd777ca) | present | 0 |

### Notes on the table

- Blob equality: 21 local files at `HEAD` match the remote tree blob SHAs. Local reads therefore match remote content.
  - Code and test blobs: the test file, `web_portal/app.py`, `web_portal/routes/webhooks.py`, the database module, `tests/conftest.py`, and the ingestion test.
  - Other test and config blobs: `native.py`, the e2e journey, `.github/workflows/ci.yml`, `pyproject.toml`, `compose.yml`, and `deploy/.env.example`.
  - Rule blobs: `AGENTS.md`, the copilot instructions, the constitution, and the changelog README.
  - Guard and record blobs: the route script, the changelog guard, the folder baseline, the test quality baseline, and the reference spec.
- R-07 uses the blob that issue #4730 cites for `3964d21d`. The blob is not a main blob (R-05).
- R-21 cites the job conclusion from `gh run view`. The shard definition is in the workflow file (R-20).

## Local Reads

- The repository root holds five modified files that this issue does not change: `src/foundation/support/utils/logger_utils.py`, `src/interfaces/wan_performance/collection/request_admission.py`, `src/mist/intelligence/reports/subscription_expiry/client.py`, and two test files. The follow-up must start from `origin/main`, not from the local checkout.
- A local search for `WEBHOOK_ENABLED` covered `src`, `web_portal`, `tests`, `scripts`, `deploy`, `documentation`, `.github`, `changelog.d`, `wsgi.py`, `wsgi_capture.py`, `MistHelper.py`, `compose.yml`, and `README.md`. It found the files that R-11 to R-17 cover.
- A local search for `load_dotenv` and `dotenv` found no `load_dotenv` call in `tests/conftest.py`. The file names the package only (line 45). The integration conftest at `tests/integration/conftest.py` calls `load_dotenv(override=False)`. The unit test lives in `tests/unit`, a different folder.
- A local search for `webhook` in `architecture.md`, `development-setup.md`, `container-deployment.md`, `operator-guide.md`, and `quality-gates.md` found no match. The local OpenAPI file has 860 matches. Its webhook topics appear at lines 1012 to 1022, 1432 to 1442, and 120961 to 121009. The header names appear at lines 43937 to 44074.
- The file `.env` was not read because of the secrets rule. The test removes the variable, so a `.env` value does not change the test result.
- The local grep used read-only search tools and `git --no-optional-locks` commands. No file was written in the repository.

## Sources

- Rule files, read at `HEAD`: `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, and `changelog.d/README.md`.
  - Template files, read at `HEAD`: `spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md` under `.specify/templates/`.
  - Code and test files, read at `HEAD`: `tests/unit/web_portal/test_webhook_signature.py`, `web_portal/app.py`, `web_portal/routes/webhooks.py`, `src/foundation/persistence/db/__init__.py`, and `.specify/scripts/powershell/spec-route.ps1`.
  - CI and guard files, read at `HEAD`: `.github/workflows/ci.yml`, `pyproject.toml`, `tests/guardrails/test_changelog_fragment_policy.py`, `tests/guardrails/process_folder_baseline.json`, and `.github/test-quality-baseline.json`.
  - Document read at `HEAD`: `documentation/quality-gates.md`.
- Reference record (shape only, not content): `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv` with `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design\` (R-36).
- Local OpenAPI file: `documentation/mist-api-openapi31yaml.yaml`, lines 43937 to 44074 (header names for webhook deliveries).
- Remote sources through `gh`: the git tree of `main`, blob reads by SHA, and commit reads.
  - Remote sources through `gh`: compare results for `15da34506` and `3964d21d`, and the pull request 4843 view.
  - Remote sources through `gh`: the open pull request file lists, and the Quality Gates run 45774119357 with its jobs.
  - Remote sources through `gh`: the issue views for #4730, #2711, #4358, #1907, and #4718.
- Documents searched for webhook terms and judged not applicable: `documentation/architecture.md`, `documentation/development-setup.md`, `documentation/container-deployment.md`, and `documentation/operator-guide.md`. The issue changes no operator behavior, no container, and no setup step.
- Documents not used: `documentation/MIST_API_GET_ENDPOINTS.md` and `documentation/MIST_API_MISSING_ENDPOINTS.md`. No Mist REST endpoint is in scope.
- Local skills: none loaded. The issue has no Podman, Juniper device, or container behavior in scope.
- Web URLs: none fetched with `web_fetch`. The pull request URL `https://github.com/jmorrison-juniper/MistHelper/pull/4843` came from `gh` output and was not fetched.

## Related Issues

- #1907 (closed): the origin of the webhook secret defect. The test file header and `web_portal/app.py` comments cite it.
- #2711 (open): named by issue #4730 as related evidence. Its body does not name #4730 (A-8).
- #4358 (merged pull request, 2026-11-13): a test relocation pull request. The issue comments mention it as a hold. It does not block this record.
- #4718 (open): webhook response failures in the runtime. It uses the same route, and it has a different defect.
- #4728, #4731, #4797, and #4492 (open): the same defect class (ambient global state) by title. The bodies are not read (U-12).
- #4228 (merged pull request): not linked. Its body mentions the number 4730 as a test count.

## Unverified

- U-1: Local runs of checks TC-001 to TC-004 and TC-007 to TC-014. This authoring process runs no tests. The only evidence is CI run 45774119357 (R-21).
- U-2: The negative control in TC-004 fails as described. The issue comment 3 reports a mutation probe. This record does not reproduce it.
- U-3: Counts in issue comments 2 and 3: 842 passed tests, seven offline self-checks, 1,248 files, devtools 0.6.3 and 0.6.4, and 50 skips. These counts are not reproduced.
- U-4: Issue comment 4 states that no executable commit hook exists at the shared default Git hook path. No hook path was inspected.
- U-5: Issue comment 2 states that `core.hooksPath` and `commit.gpgsign` were set during commit `5e55cca`. The commit environment is not readable.
- U-6: The sibling search scope excludes `.venv` and the root files that the search did not name.
- U-7: The head blob of pull request 4843 (`3ea78a394554b71228da0d24c36aeab46677bc73`). The head commit exists, but its blob was not read. The merge blob is verified (R-01, R-08).
- U-8: Principle IV steps 11 and 12 (image revision check and deploy). Container and deploy work is outside this record (CT-1).
- U-9: The digest algorithm that Mist Cloud uses for `X-Mist-Signature`. The OpenAPI lines 43937 to 44074 name the header but do not state the algorithm in the read range. The HMAC-SHA256 statement is a code comment in `web_portal/routes/webhooks.py`.
- U-10: A delivery that carries only the `X-Mist-Signature-v2` header can fail closed with code 403. This is an inference from `_reject_unverified_request` and `request.headers.get(SIGNATURE_HEADER, "")`. It is not tested.
- U-11: The link between issue #4730 and issue #2711 (A-8).
- U-12: The bodies of issues #4728, #4731, #4797, and #4492. Only the titles are read.
