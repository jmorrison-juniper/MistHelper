# Research: Credential default audit

## Method

- **Truth order**: GitHub `main` at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (committed 2026-11-26T07:15:01Z), read with `gh api`.
- **Local checkout**: `HEAD` equals `main`. Every path in this table has a local `HEAD` blob that equals the remote blob (`git ls-tree` comparison, 0 mismatches). The working tree holds no change for these paths.
- **Line checks**: Lines came from a masked read. Each non-empty literal default appears as a masked token. No credential value appears in this record.
- **Not run**: The AST scanner, tests, linters, and container builds were not run. Rule 2 forbids them. The count beyond the 64 baseline lines is unverified (U-1).
- **Result key**: `present` means the line holds the candidate. `partial` means the env fallback is gone and a session read remains. `absent` means the candidate is gone. `local-only` means a path that exists only in the local virtual environment.

## Linked Pull Requests (Step 2)

| PR | Title | State | Merged | Head branch | Relation to #2861 |
| - | - | - | - | - | - |
| 4406 | fix(security): reject conflicting Mist token values | MERGED | 2026-10-28T19:47:58Z | 3996-mist-token-conflict | Part of #2861. Changes `MistHelper.py` and adds the token-conflict record. |
| 4507 | fix(mist-session): reject unusable required tokens | MERGED | 2026-11-05T17:09:32Z | jmorrison-juniper-2861-credential-token-slice | Part of #2861. Changes `mist-ops-platform/src/shared/mist/session.py` and four test files. Merge commit `296b977e28be50cd9ddcca57c46b35bb029afe27`. |
| 4317 | fix(security): use session token only in websocket, routing and ARP code | MERGED | 2026-10-26T21:59:37Z | jmorrison-juniper-fix-2861-credential-defaults | Part of #2861. Removes three environment fallbacks. |
| 4015 | docs(security): specify credential default resolution | CLOSED | not merged | jmorrison-juniper-credential-defaults-spec | Spec pull request for #2861. Closed. Its record is absent from main. |
| 3036 | fix(db): reject missing database credentials | MERGED | 2026-09-19T22:22:11Z | fix/2861-credential-defaults | Refs #2861. Changed `src/db/__init__.py`, which main no longer holds (R-08). |
| 3096 | Fix credential default handling | MERGED | 2026-09-20T13:23:56Z | fix/2861-credential-defaults | Part of #2861. Changed `src/maps/_flask_viewer.py`, which main no longer holds (R-09). |
| 2864 | chore(validation): fail visibly when a required input is missing | MERGED | 2026-09-17T19:58:56Z | chore/2753-masking-defaults | Issue #2753. Deferred 31 credential candidates to #2861. |
| 4498 | fix(analytics): reject missing zone summary statistics | MERGED | 2026-10-30T08:51:30Z | jmorrison-juniper-zone-summary-validation | Refs #2753. The body mentions #2861. Not a #2861 slice. |
| 4521 | fix(device): stop AP discovery after a failed site read | MERGED | 2026-11-05T12:39:26Z | jmorrison-juniper-audit-missing-input-defaults | Part of #2753. The body mentions #2861. Not a #2861 slice. |
| 4055 | fix(org-config): reject missing created identifiers | CLOSED | not merged | jmorrison-juniper-fix-3070-blind-handler-ratchet | Closes #2753. The body mentions #2861. Not a #2861 slice. |
| 3098 | Fix scope ID default handling | MERGED | 2026-09-20T15:07:34Z | fix/2863-scope-id-defaults | Part of #2863. Does not mention #2861. |
| 2064 | fix(portal): show the stored size of a finished capture | MERGED | 2026-08-25T21:50:35Z | fix/2063-stored-size-display | The search matched the text 2861. Not a #2861 slice. |

**Open pull requests** (`gh pr list --state open`): #4890, #4889, #4888, #4887, #4886, #4813, and #4208. Only #4208 changes a candidate file (`web_portal/app.py`, C-62). Its file count is 82. No batch in this record changes `web_portal/app.py` (D-14).

## Existing Record Review (Step 3)

The route `specs/numbered/0/0/0/4/2/4/2/1` holds two records for #2861 on main. Each file was read from the local checkout, and each blob matches its remote blob (R-04, R-05).

| ID | Item | Result |
| - | - | - |
| L-01 | `2861-token-conflict` folder, 8 files read. Its spec, plan, tasks, and research match the merged PR #4406 behavior. | verified |
| L-02 | `2861-required-token-resolution` folder, 5 files read. Its source change matches the merged PR #4507 behavior. | verified |
| L-03 | `2861-required-token-resolution/tasks.md` leaves T019 unchecked after PR #4507 merged. | stale |
| L-04 | `2861-required-token-resolution/plan.md` names Python 3.13. `pyproject.toml:23` requires 3.15 (R-55 scope). | stale |
| L-05 | `2861-required-token-resolution/spec.md` status says publication is pending. Its plan names PR #4497 as the next merge position. | stale |
| L-06 | `2861-required-token-resolution/spec.md` FR-003 keeps the configured token as the final source. The owner analysis of 2026-10-06 lists the same path as a wrong identity. | stale, conflict with D-6 |
| L-07 | Both quickstart files give POSIX commands only, such as `.venv/bin/python`. The Windows target needs `.venv\Scripts\python.exe`. | gap |
| L-08 | `specs/numbered/0/0/0/4/2/4/2/1/2861-credential-defaults` is absent on main. Closed PR #4015 never merged it. | absent |

**Counts**: verified 2, stale 4, absent 1.

## Remote Verification

Each row is one check. The table holds 64 candidate rows (C-01 to C-64, from the owner manifest of 2026-10-06T21:56:45Z) and 72 other rows (R-01 to R-72). Group A is wrong identity. Group B is fail-closed or display. Group C is intentional or test support. The owner manifest assigned these groups.

| ID | Claim | Path | Blob SHA | Result | Line |
| - | - | - | - | - | - |
| C-01 | A: legacy token env `or` default (baseline 2901) | MistHelper.py | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | absent | 0 |
| C-02 | C: `require_token` default true (baseline 2924, moved) | MistHelper.py | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2848 |
| C-03 | C: settings token empty default (baseline 85) | mist-ops-platform/src/shared/config/settings.py | fdf3418fc442dcff621d048b3f490c4f31f0ae92 | present | 85 |
| C-04 | C: settings Vault token empty default (baseline 87) | mist-ops-platform/src/shared/config/settings.py | fdf3418fc442dcff621d048b3f490c4f31f0ae92 | present | 87 |
| C-05 | C: settings webhook secret empty default (baseline 88) | mist-ops-platform/src/shared/config/settings.py | fdf3418fc442dcff621d048b3f490c4f31f0ae92 | present | 88 |
| C-06 | A: configured-token fallback after cache and Vault misses (baseline 87, moved) | mist-ops-platform/src/shared/mist/session.py | c591516dcfe68e8e884d584811858b556f962600 | present | 90 |
| C-07 | C: SMTP username empty default (baseline 62) | mist-ops-platform/src/shared/services/notification.py | 07cd2364150957a90af7c98d9ea5d8181ff831d9 | present | 62 |
| C-08 | C: SMTP password empty default (baseline 63) | mist-ops-platform/src/shared/services/notification.py | 07cd2364150957a90af7c98d9ea5d8181ff831d9 | present | 63 |
| C-09 | B: sender name fallback (baseline 124) | mist-ops-platform/src/shared/services/notification.py | 07cd2364150957a90af7c98d9ea5d8181ff831d9 | present | 124 |
| C-10 | B: token read with empty default (baseline 188) | mist-ops-platform/src/shared/services/session_store.py | a60333b602275db4aad3eefc077da08ae14680e0 | present | 188 |
| C-11 | B: GitHub token environment empty default (baseline 355) | scripts/mist_ideas_analyzer_pkg/__init__.py | 75189e765092de65ae90dd7931c58b1876d8332c | present | 355 |
| C-12 | B: AI key environment empty default (baseline 405) | scripts/mist_ideas_analyzer_pkg/__init__.py | 75189e765092de65ae90dd7931c58b1876d8332c | present | 405 |
| C-13 | A: database username dataclass default (baseline 58, moved) | src/foundation/persistence/db/__init__.py | 11f8dd6d5f13d04c931e9888bf25c3e968df4173 | present | 44 |
| C-14 | A: database password dataclass default (baseline 59, moved) | src/foundation/persistence/db/__init__.py | 11f8dd6d5f13d04c931e9888bf25c3e968df4173 | present | 45 |
| C-15 | A: Redis password dataclass default (baseline 62, moved) | src/foundation/persistence/db/__init__.py | 11f8dd6d5f13d04c931e9888bf25c3e968df4173 | present | 48 |
| C-16 | B: webhook secret empty default (baseline 65, moved) | src/foundation/persistence/db/__init__.py | 11f8dd6d5f13d04c931e9888bf25c3e968df4173 | present | 51 |
| C-17 | C: Redis writer passes None for AUTH (baseline 109) | src/foundation/persistence/db/writers/redis_writer.py | 7b66735dab8091d32a98cd3d2040db8745c55229 | present | 109 |
| C-18 | C: Redis writer passes None for AUTH (baseline 551) | src/foundation/persistence/db/writers/redis_writer.py | 7b66735dab8091d32a98cd3d2040db8745c55229 | present | 551 |
| C-19 | B: username sort key default (baseline 47) | src/foundation/runtime/input/prompt_client_utils.py | a8d6d1cc0758a097953af09506f97a5267c917ce | present | 47 |
| C-20 | B: username label default (baseline 111) | src/foundation/runtime/input/prompt_client_utils.py | a8d6d1cc0758a097953af09506f97a5267c917ce | present | 111 |
| C-21 | B: username label default (baseline 167) | src/foundation/runtime/input/prompt_client_utils.py | a8d6d1cc0758a097953af09506f97a5267c917ce | present | 167 |
| C-22 | B: lock token attribute default (baseline 329, moved) | src/interfaces/portals/upgrade_portal/api/run_controls/routes.py | 38ad8dfd9ce91aa7289a95d2753bb47d2bb64aee | present | 349 |
| C-23 | B: lock token read default (baseline 91) | src/interfaces/portals/upgrade_portal/api/run_controls/services/bulk.py | 83018bf1608c489a9e5a398f2fd9985cbe32704d | present | 91 |
| C-24 | B: lock token attribute default (baseline 92) | src/interfaces/portals/upgrade_portal/api/run_controls/services/bulk.py | 83018bf1608c489a9e5a398f2fd9985cbe32704d | present | 92 |
| C-25 | A: database username environment default (baseline 276) | src/interfaces/portals/upgrade_portal/app/config.py | adfa7ba9b59ea1ab89bbcb8a20a18cfc28b4ff6e | present | 276 |
| C-26 | C: session key environment default (baseline 424) | src/interfaces/portals/upgrade_portal/app/config.py | adfa7ba9b59ea1ab89bbcb8a20a18cfc28b4ff6e | present | 424 |
| C-27 | C: browser-token flag default false (baseline 762) | src/interfaces/portals/upgrade_portal/app/routes/auth.py | 5c496f5465a7f940896080958efafb40b000b0a7 | present | 762 |
| C-28 | C: browser-token flag default false (baseline 1081) | src/interfaces/portals/upgrade_portal/app/routes/auth.py | 5c496f5465a7f940896080958efafb40b000b0a7 | present | 1081 |
| C-29 | B: lock token body default (baseline 2411, moved) | src/interfaces/portals/upgrade_portal/app/routes/select.py | 604f8a5e1b6f72b6df860cf1ae03d0ffbc01055c | present | 2429 |
| C-30 | B: capture username dataclass default (baseline 131) | src/interfaces/portals/upgrade_portal/capture/clients.py | 27fd5fac69d45c794ba5bc73f9b6a880777440b4 | present | 131 |
| C-31 | B: capture username fallback (baseline 713) | src/interfaces/portals/upgrade_portal/capture/clients.py | 27fd5fac69d45c794ba5bc73f9b6a880777440b4 | present | 713 |
| C-32 | B: lock token default none (baseline 25) | src/interfaces/portals/upgrade_portal/locking/session_lock.py | 008edfb56f69c169aa5c1eb4f59de993488a1622 | present | 25 |
| C-33 | B: stored lock token read default (baseline 800) | src/interfaces/portals/upgrade_portal/runtime/lock.py | 1b9a4a2916ab3ffe3a5835c69db7220902c5e8c7 | present | 800 |
| C-34 | C: Redis password environment read with None (baseline 1058) | src/interfaces/portals/upgrade_portal/runtime/lock.py | 1b9a4a2916ab3ffe3a5835c69db7220902c5e8c7 | present | 1058 |
| C-35 | B: map viewer token attribute default (baseline 155) | src/interfaces/visualization/maps/_flask_viewer.py | e1f7234c06f73f3c196123e29e39bd769ce42ad0 | present | 155 |
| C-36 | A: session token read with environment fallback removed (baseline 262) | src/mist/networking/network/_routing_utils_payload.py | 38c2458ff14370be660d956ca30c252dc4fd291c | partial | 263 |
| C-37 | A: session token read with environment fallback removed (baseline 79) | src/mist/realtime/websocket/manager.py | bae16bb803cdf8ca2a0fa5274b916c96c40fdec9 | partial | 79 |
| C-38 | A: session token read with environment fallback removed (baseline 166) | src/mist/realtime/websocket/manager.py | bae16bb803cdf8ca2a0fa5274b916c96c40fdec9 | partial | 166 |
| C-39 | B: ZTP password display fallback to response text (baseline 371) | src/mist/resources/device/_utility_commands_action.py | 0f889b3dedaff5d23aff581a6dc1802f36d6d12c | present | 371 |
| C-40 | A: session token read with environment fallback removed (baseline 62) | src/mist/resources/device/arp_command_manager.py | 1858561b08b81b45de5101af575a2bfa722fb410 | partial | 62 |
| C-41 | B: hostname fallback in capture display (baseline 186) | src/operations/execution/capture/client_pcap_downloader.py | 7509cf86ff9b5cf930c16a616306ef15ed792a4a | present | 186 |
| C-42 | B: SSH username dataclass default (baseline 48) | src/operations/execution/ssh/batch/multi_host_runner.py | cc0968e09826d7042eb4afd865d8f48c4e81e445 | present | 48 |
| C-43 | B: SSH password dataclass default (baseline 49) | src/operations/execution/ssh/batch/multi_host_runner.py | cc0968e09826d7042eb4afd865d8f48c4e81e445 | present | 49 |
| C-44 | C: SSH username precedence, command line first (baseline 184) | src/operations/execution/ssh/runtime/app_runner.py | 424e60d9514de0e1cc3b7cdc9364ddf4d64c0281 | present | 184 |
| C-45 | C: SSH password prompt with cancellation to None (baseline 191) | src/operations/execution/ssh/runtime/app_runner.py | 424e60d9514de0e1cc3b7cdc9364ddf4d64c0281 | present | 191 |
| C-46 | C: test lock token default (baseline 358, moved) | tests/contract/upgrade_portal/test_lock.py | 5b42ad89c07ce0449d3fc44a6329e71873b43b2d | present | 359 |
| C-47 | C: test lock token fallback (baseline 549) | tests/e2e/upgrade_portal/test_upgrade.py | 5c019ec98a184a0d0cd881a08fb1595b065fd703 | present | 549 |
| C-48 | C: test token read, legacy name first (baseline 36) | tests/integration/conftest.py | d2055ec1b483548a1b9220fbfb5ee9697f3dd000 | present | 36 |
| C-49 | C: test token read, legacy name first (baseline 93) | tests/integration/conftest.py | d2055ec1b483548a1b9220fbfb5ee9697f3dd000 | present | 93 |
| C-50 | C: test compose password environment default (baseline 34) | tests/integration/test_compose_deploy.py | 2e62d01038114b938544af3342c0354958931d8b | present | 34 |
| C-51 | C: test compose password environment default (baseline 45) | tests/integration/test_compose_deploy.py | 2e62d01038114b938544af3342c0354958931d8b | present | 45 |
| C-52 | C: test lock token read default (baseline 517) | tests/integration/upgrade_portal/test_two_operators.py | 92046a2dd5d2ff3da254999b928027b1bd330df4 | present | 517 |
| C-53 | C: test record lock token read default (baseline 254) | tests/support/upgrade_portal_e2e/records/portal.py | d94ebaa6a045e2d1330235e0623edb2abc5cdd05 | present | 254 |
| C-54 | C: test site lock token read default (baseline 223) | tests/support/upgrade_portal_e2e/site_lock.py | c747935210a3cfac583f3b3652b780a4337b1ca8 | present | 223 |
| C-55 | C: test token field read default (baseline 326) | tests/support/upgrade_portal_e2e/site_lock.py | c747935210a3cfac583f3b3652b780a4337b1ca8 | present | 326 |
| C-56 | C: test lock token parameter default (baseline 44) | tests/unit/upgrade_portal/test_e2e_lock_holds.py | f49761fcfd405ce14388f2966a19945755879bd9 | present | 44 |
| C-57 | C: test CSRF token parameter default (baseline 70) | tests/unit/upgrade_portal/test_e2e_lock_holds.py | f49761fcfd405ce14388f2966a19945755879bd9 | present | 70 |
| C-58 | C: test CSRF token parameter default (baseline 114) | tests/unit/upgrade_portal/test_e2e_org_operations.py | fa634f6e60649546966e816d15f1eaa2b25445c5 | present | 114 |
| C-59 | C: test token field read default (baseline 92) | tests/unit/upgrade_portal/test_token_refusal_messages.py | 3476a618a2c006c73dd18e0feeaa3668560f3cff | present | 92 |
| C-60 | C: test webhook secret parameter default (baseline 59) | tests/unit/web_portal/test_webhook_signature.py | bcf0ad12319281ea484e98bba65ff2d544f6b8d3 | present | 59 |
| C-61 | C: test session token parameter default (baseline 324) | tests/unit/websocket/test_manager.py | 61b7d7bc6833c3b522720c2d3a40ddd6812d3d50 | present | 324 |
| C-62 | B: webhook secret environment fallback (baseline 133) | web_portal/app.py | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 133 |
| C-63 | B: webhook secret configuration fallback (baseline 69) | web_portal/routes/webhooks.py | bd33ba1d2f185fab411631c0b1b91e616b4226e7 | present | 69 |
| C-64 | C: random local portal key fallback (baseline 113) | web_portal/services/config.py | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 113 |
| R-01 | Changelog fragment for PR 4406 exists | changelog.d/issue-2861-mist-token-conflict.md | 6e5f18486fa4dba596373c4afcdef912070c3d09 | present | 0 |
| R-02 | Changelog fragment for PR 4507 exists | changelog.d/issue-2861-required-token-resolution.md | d26e8e7e4bc5aab7fbb9da0fafd0973d8c72f4be | present | 0 |
| R-03 | Changelog fragment for PR 4317 exists | changelog.d/issue-2861-session-token-only.md | 0543a7c8a31cfb02ce800428e8c462b7a175ab88 | present | 0 |
| R-04 | Legacy folder 2861-token-conflict exists (tree) | specs/numbered/0/0/0/4/2/4/2/1/2861-token-conflict | 7b78e8545b9fc1e394723a7ed90735fed7ae944e | present | 0 |
| R-05 | Legacy folder 2861-required-token-resolution exists (tree) | specs/numbered/0/0/0/4/2/4/2/1/2861-required-token-resolution | 8506b1fdfb04f75a71493c401f48df426bea382c | present | 0 |
| R-06 | Folder 2861-credential-defaults is absent | specs/numbered/0/0/0/4/2/4/2/1/2861-credential-defaults | - | absent | 0 |
| R-07 | Proposed direct guard path is absent | tests/guardrails/test_credential_default_ratchet.py | - | absent | 0 |
| R-08 | PR 3036 target path is absent | src/db/__init__.py | - | absent | 0 |
| R-09 | PR 3096 target path is absent | src/maps/_flask_viewer.py | - | absent | 0 |
| R-10 | Token resolution test exists | mist-ops-platform/tests/unit/mist/token_resolution/test_required_resolution.py | c540948e7745e0d5b7ba83f0eff892d19d4b0551 | present | 0 |
| R-11 | Token resolution test exists | mist-ops-platform/tests/unit/mist/token_resolution/test_session_boundary.py | 55a6b2dc02641652246479d278b42efb151f86ea | present | 0 |
| R-12 | Token resolution test exists | mist-ops-platform/tests/unit/mist/token_resolution/test_provider_contracts.py | 1972bd1daeb840c4c5af48b6a868e023ea3ceca0 | present | 0 |
| R-13 | Preflight tests exist, including conflict tests | tests/unit/test_credential_preflight.py | 7093442609330bd69c2e90f7d295f42257606370 | present | 0 |
| R-14 | Standalone database tests exist | tests/unit/test_standalone.py | 3f44914d1fadad8a326ba97a5cbdde507eedf0de | present | 0 |
| R-15 | Database discovery tests exist and build configs without credentials | tests/unit/db_discovery/test_config.py | 36d4a866c9e16b82533312cee26f4f1b3de9a2a9 | present | 0 |
| R-16 | Portal configuration tests exist | tests/unit/upgrade_portal/test_config.py | c516f3a3e5b98a2b1930b84a006349d226514cc7 | present | 0 |
| R-17 | Session-only ARP test exists | tests/unit/device/test_arp_command_manager.py | a2e71e56812b4f49193ab18f80c4faf51e26e2ef | present | 0 |
| R-18 | Session-only routing test exists | tests/unit/test_routing_utils.py | 06b1ef72bdc6cc24f3d026daea6470966e4bda49 | present | 0 |
| R-19 | Source backreference guard is the pattern for counts and proofs | tests/guardrails/test_source_misthelper_backrefs.py | 322f03c373365f06387b9b3c4dfe051fca2eba4e | present | 0 |
| R-20 | Blind-handler ratchet guards exception growth | tests/guardrails/test_blind_exception_handler_ratchet.py | 3cab97e42178b7b978bcc78eab73d8a0fb3eae27 | present | 0 |
| R-21 | Changelog policy test enforces fragment names | tests/guardrails/test_changelog_fragment_policy.py | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| R-22 | Compose database settings guard exists | tests/guardrails/test_compose_database_settings.py | 1554f9f08147077163455a0399d9d9e7be39f3ac | present | 0 |
| R-23 | Compose naming guard exists | tests/guardrails/test_compose_naming_policy.py | 660541004645f6300cd0b4217fafa90abc9e7da8 | present | 0 |
| R-24 | SDK compatibility contract test exists | tests/integration/test_mistapi_sdk_compatibility.py | cab2d602113012729f6c392dff43197d05913a38 | present | 0 |
| R-25 | Markdown link guard exists | tests/guardrails/test_markdown_links.py | cafefdac69006ddf7544e5a57a101f0f63fbcc38 | present | 0 |
| R-26 | Agent rules: writing, secrets, git flow | AGENTS.md | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 0 |
| R-27 | Repository rules: local gates lines 57 to 76, route rules lines 159 to 167, Hot files | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 57 |
| R-28 | Constitution principles I to VII at lines 38, 91, 113, 143, 182, 204, and 235 | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R-29 | Spec template headings | .specify/templates/spec-template.md | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 0 |
| R-30 | Plan template headings and design layout | .specify/templates/plan-template.md | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| R-31 | Tasks template format | .specify/templates/tasks-template.md | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| R-32 | Checklist template format | .specify/templates/checklist-template.md | 806657da09d1058823923e346a323b633114971a | present | 0 |
| R-33 | Route algorithm: base 5 at lines 17 and 18, route function at line 34 | .specify/scripts/powershell/spec-route.ps1 | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R-34 | Job table of quality gates from line 48 | documentation/quality-gates.md | 6776d334cca5d9b43273473a06da367a65605c6d | present | 48 |
| R-35 | Development setup names the token variable at line 154 | documentation/development-setup.md | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 154 |
| R-36 | Container deployment test containers section at line 141 | documentation/container-deployment.md | f06228bc6bbe77cc009f956403872a06462466ea | present | 141 |
| R-37 | README names the token variable at line 63 | README.md | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | present | 63 |
| R-38 | OpenAPI file exists | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 85 |
| R-39 | OpenAPI security requirement apiToken | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 85 |
| R-40 | Inventory cited by the issue body exists | specs/1924-failure-evidence/inventory.md | 9d5724dbdf6811d9458e60937e7afcb8d9d28e36 | present | 0 |
| R-41 | Compose ArangoDB password fallback literal | compose.yml | b3944fc9f994ca149974072b1a9c8f13797d7924 | present | 223 |
| R-42 | Compose Redis password fallback literal | compose.yml | b3944fc9f994ca149974072b1a9c8f13797d7924 | present | 244 |
| R-43 | Compose Redis health check fallback literal | compose.yml | b3944fc9f994ca149974072b1a9c8f13797d7924 | present | 250 |
| R-44 | SSH build-time password default documented | container/scripts/start.sh | 3b138807883a8a8785bac7d8c9b7f9a79458ed0c | present | 7 |
| R-45 | Session script refuses a missing token by empty default | container/scripts/misthelper-session.sh | 599d5753b35981e60085d0c4342dacf0e484ec3b | present | 119 |
| R-46 | Web entry point builds a session from an env file | wsgi.py | e8b2be7cb33c54266afcd5723293b7487df4d365 | present | 48 |
| R-47 | Web entry point builds a session without a token | wsgi.py | e8b2be7cb33c54266afcd5723293b7487df4d365 | present | 52 |
| R-48 | Maps builds a session from an env file | src/interfaces/visualization/maps/maps_manager.py | b3d4f9251221fbdf7bbddbb2ca833fc29b607b8c | present | 2681 |
| R-49 | Maps passes a token keyword the SDK does not accept | src/interfaces/visualization/maps/maps_manager.py | b3d4f9251221fbdf7bbddbb2ca833fc29b607b8c | present | 2689 |
| R-50 | Probe script builds a session without a token | scripts/probe_pk_strategy.py | 991e56c43e381c2cb655387261b68bb6a6222198 | present | 402 |
| R-51 | Services auth passes the token explicitly | mist-ops-platform/src/shared/services/auth.py | 175cb458001750b6af4e02b14072848fca1a19a5 | present | 107 |
| R-52 | Token initializer reads tokens through the parser | src/foundation/support/refactors/initialize_mist_session.py | b5e3c1ec102cbe08b1e68b0909f2da94318280ca | present | 168 |
| R-53 | Conflict refusal for token variables (PR 4406) | MistHelper.py | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 2823 |
| R-54 | Terminal check before a prompt | MistHelper.py | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 7049 |
| R-55 | mistapi pin in pyproject allows 0.64.1 and later below 0.65 | pyproject.toml | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 29 |
| R-56 | mistapi pinned at 0.64.1 | requirements.txt | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| R-57 | SDK session class | .venv\Lib\site-packages\mistapi\__api_session.py | local-only | present | 52 |
| R-58 | SDK constructor takes apitoken | .venv\Lib\site-packages\mistapi\__api_session.py | local-only | present | 59 |
| R-59 | SDK reads MIST_APITOKEN from the environment when unset | .venv\Lib\site-packages\mistapi\__api_session.py | local-only | present | 363 |
| R-60 | SDK builds the Token authorization header | .venv\Lib\site-packages\mistapi\__api_session.py | local-only | present | 201 |
| R-61 | Commit of PR 4507 merge | (commit) | 296b977e28be50cd9ddcca57c46b35bb029afe27 | present | 0 |
| R-62 | Commit cited as main on 2026-11-09 | (commit) | 3964d21d03f9f5717cb8eafb7272ecff21f5362a | present | 0 |
| R-63 | Preserved recovery commit | (commit) | 6cea98a9794d87e0ed3738bf331afff51280f76c | present | 0 |
| R-64 | Approved base commit | (commit) | 76f976358f6217a9e7df48e3e5d4c4b6d63c5d14 | present | 0 |
| R-65 | Initial base commit | (commit) | 644037dcc1eee0e43fac0d40b1186ff1cb6e322e | present | 0 |
| R-66 | Recovery branch points to R-63 | recovery/2861-handoff-20261004 | 6cea98a9794d87e0ed3738bf331afff51280f76c | present | 0 |
| R-67 | Related issue 4748 is open | (issue) 4748 | - | present | 0 |
| R-68 | Related issue 2753 is open | (issue) 2753 | - | present | 0 |
| R-69 | Related issue 2863 is open | (issue) 2863 | - | present | 0 |
| R-70 | Related issue 1924 is closed | (issue) 1924 | - | present | 0 |
| R-71 | Related issue 2862 is closed | (issue) 2862 | - | present | 0 |
| R-72 | Remote main reference | refs/heads/main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R-73 | Python 3.15 requirement | pyproject.toml | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| R-74 | Compose sets ARANGO_USERNAME for the container | compose.yml | b3944fc9f994ca149974072b1a9c8f13797d7924 | present | 145 |
| R-75 | Copilot instructions document the container SSH default password | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 427 |

**Counts**: 139 checks. Candidate rows 64. Other rows 75. The STATUS file repeats this count.

**Candidate summary**: Group A has 10 lines. Five are present (C-06, C-13, C-14, C-15, C-25). Four are partial (C-36, C-37, C-38, C-40). One is absent (C-01). Group B has 23 present lines. Group C has 31 present lines. Total present 59, partial 4, absent 1.

**Note**: The row for R-38 cites the OpenAPI file. Its line 85 holds the security requirement that R-39 cites.

## Decisions

Each decision lists the chosen option, the rejected options, the reason, and the risk. Decisions D-5, D-6, and D-7 are human decisions.

- **D-1 Database credential defaults.** Chosen: remove the three literal defaults (C-13, C-14, C-15). Reject sample values in `__post_init__`. Rejected: keep defaults and require a validated object only, because the default still selects an account. Rejected: require non-empty credentials for every construction, because probe tests build configs without credentials (R-15). Risk: direct construction yields empty credentials that fail at connect time.
- **D-2 Portal database username.** Chosen: container runtime requires `ARANGO_USERNAME`. Other runtimes use the image account name and log the variable name. Rejected: remove the default everywhere, because local runs break. Rejected: keep the default everywhere, because a container masks a missing input. Risk: a container without the variable stops. Compose sets the variable (R-74).
- **D-3 Missing Mist token.** Chosen: prompt only in the command-line entry point when stdin and stdout are terminals. Otherwise refuse with status 1. Use hidden input and handle end of file. Rejected: prompt in every path, because services have no terminal and a prompt blocks them. Rejected: never prompt, because it breaks owner decision 1. Risk: an interactive user types a token that is not stored. The token lasts for one process.
- **D-4 Test helper precedence.** Chosen: read the canonical name first. Fail the test session on a conflict. Rejected: keep the legacy name first, because it differs from the application (C-48, C-49) and hides a conflict. Rejected: skip on conflict, because a skip masks a missing input. Risk: a developer with conflicting variables sees a failure. That result is correct.
- **D-5 Legacy token variable window. HUMAN-DECISION-REQUIRED.** Options: remove the legacy read now. Remove it in a named release after the docs and samples name only `MIST_API_TOKEN`. Keep it. Recommended: the named release. Reason: owner decision 2 requires removal, but no date exists. Risk: operators with legacy env files stop when the read is removed.
- **D-6 Configured-token fallback in `MistSessionFactory`. HUMAN-DECISION-REQUIRED.** Options: (a) keep the fallback, as the merged PR 4507 spec requires (L-06). (b) Remove it and raise the existing `RuntimeError` when cache and Vault miss. (c) Allow it only for a configured default organization. `AppSettings` holds no organization field, because a search of `mist-ops-platform/src/shared/config/settings.py` found no match. Recommended: (b). Reason: the owner analysis says do not use a process token as a silent replacement. Risk: a single-tenant deployment without Vault or cache stops.
- **D-7 Container literal credential defaults. HUMAN-DECISION-REQUIRED.** Items: `compose.yml` lines 223, 244, and 250 use non-empty literal fallbacks after `:-`. Line 109 already requires `CAPTURE_SECRET_KEY`. `container/scripts/start.sh` documents a build-time SSH password when none is supplied (lines 7 and 8). Options: (a) keep the defaults. (b) Require each variable in compose and require `MISTHELPER_SSH_PASSWORD` or disable password login. (c) Keep the defaults only in the test profile. Recommended: (b). Risk: an existing deployment does not start until an operator sets each value.
- **D-8 Ratchet design.** Chosen: a nested guard package. The scanner lists tracked Python files with `git ls-files`. The baseline has two sections, candidates and accepted. Each entry keys on path, scope, kind, and fingerprint. The guard fails on new candidates, stale entries, zero files, and parse failures. Rejected: line-keyed entries, because 9 of the 59 present lines moved in this audit (C-02, C-06, C-13, C-14, C-15, C-16, C-22, C-29, C-46). Rejected: a direct file under `tests/guardrails`, because constitution I forbids a new direct child of a noncompliant parent. Rejected: `rglob` over the repository, because it reads `.venv`. Risk: a fingerprint change can hide a real change. Each change needs review.
- **D-9 Accepted groups B and C.** Chosen: keep the 54 entries in the accepted section with reasons. Make no code change. Rejected: change the display fallbacks, because they change labels and never select an identity. Rejected: remove them from the baseline, because that hides them. Risk: a future edit adds a new use. The guard then reports that use as a candidate.
- **D-10 Utility password display fallback (C-39).** Chosen: keep the fallback. The terminal gate at `_utility_commands_action.py` lines 372 to 377 withholds the value off a terminal. Defer the fallback change to a separate output-safety issue, as the owner asked on 2026-10-06. Risk: the terminal still shows response text when the field is missing.
- **D-11 SDK environment token channel.** Chosen: keep the documented entry points at `wsgi.py` lines 48 and 52, `maps_manager.py` line 2681, and `scripts/probe_pk_strategy.py` line 402. Add an allowlist test. The SDK reads `MIST_APITOKEN` when `apitoken` is absent (R-59). Rejected: remove the environment session, because it breaks the web entry point. Rejected: ignore the channel, because it allows silent drift. Risk: an allowlist entry needs review when a file moves.
- **D-12 Maps keyword defect (R-49).** The keyword `token` is not an `APISession` parameter (R-58 scope, `__api_session.py` lines 55 to 71). The `except` clause at `maps_manager.py` lines 2692 to 2694 prints and exits with status 1. The failure is loud. Chosen: a separate issue, outside this campaign.
- **D-13 Analyzer candidate.** The owner reported a missing connection-error case in `mist-ops-platform/tests/unit/mist/token_resolution/test_session_boundary.py` on 2026-11-10. Chosen: no change in this record. Coordinate with the owner and #4748 before a change, as the owner asked.
- **D-14 PR 4208 overlap.** No batch changes `web_portal/app.py`. Batch 3 changes only the baseline file. PR 4208 does not block this record.
- **D-15 Issue lifecycle and labels.** Chosen: keep #2861 open until every candidate is repaired (owner decision 5). Use `Refs #2861` in batch pull requests and `Closes #2861` only in the final pull request. The brief asked for `Closes` in each pull request. That conflicts with owner decision 5, so the final pull request uses it. Labels to add: `stage:speckit-artifacts-emitted`. Keep `in-progress` and `needs-human-review`.
- **D-16 Size.** Chosen: XL. Reason: four batches, more than 25 files, and changes across database, authentication, portal, command line, containers, and the guard.

## Sources

**Local files** (read from the checkout at `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`): `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, the four `.specify/templates/` files, `.specify/scripts/powershell/spec-route.ps1` (read only, not run), `documentation/quality-gates.md`, `documentation/development-setup.md`, `documentation/container-deployment.md`, `README.md`, `MistHelper.py`, `mist-ops-platform/src/shared/mist/session.py`, `mist-ops-platform/src/shared/config/settings.py`, `mist-ops-platform/tests/unit/mist/token_resolution/` (3 files read by name and line), `src/foundation/persistence/db/__init__.py`, `src/interfaces/portals/upgrade_portal/app/config.py`, `src/mist/realtime/websocket/manager.py`, `src/mist/networking/network/_routing_utils_payload.py`, `src/mist/resources/device/arp_command_manager.py`, `src/interfaces/visualization/maps/maps_manager.py`, `wsgi.py`, `scripts/probe_pk_strategy.py`, `compose.yml`, `container/scripts/start.sh`, `container/scripts/misthelper-session.sh`, `tests/integration/conftest.py`, `tests/unit/test_standalone.py`, `tests/unit/db_discovery/test_config.py`, `tests/unit/upgrade_portal/test_config.py`, `tests/unit/test_credential_preflight.py`, `tests/guardrails/test_source_misthelper_backrefs.py`, `tests/guardrails/test_changelog_fragment_policy.py`, `tests/guardrails/test_compose_database_settings.py`, `tests/guardrails/test_compose_naming_policy.py`, `tests/unit/test_unparseable_response_guards.py`, the 13 legacy record files, `pyproject.toml`, `requirements.txt`, and `documentation/mist-api-openapi31yaml.yaml` (line search only).

**Local-only**: `.venv\Lib\site-packages\mistapi\__api_session.py` (SDK source, read only).

**GitHub reads** (`gh`, read only): `repos/jmorrison-juniper/MistHelper/branches/main`, `git/trees/main?recursive=1`, `commits/<sha>` for five commits, `git/ref/heads/recovery/2861-handoff-20261004`, `issues/<number>` for five issues, `issues/2861` (view with body, comments, labels, and authorship), `pr list` for the issue search and the open list, and `pr view` for 12 linked pull requests.

**URLs fetched**: none. No web source was used.

**Skills**: none loaded. The compose interpolation rules in D-7 are not checked against a skill (U-14).

**Searched, not cited**: `documentation/architecture.md` (its line 173 names the Dockerfile only), `documentation/operator-guide.md` (no credential default text), and both endpoint files (`documentation/MIST_API_GET_ENDPOINTS.md` and `documentation/MIST_API_MISSING_ENDPOINTS.md`). This record adds no REST endpoint.

## Unverified

- **U-1**: The AST scanner was not run (rule 2). The number of candidates outside the 64 lines is unverified.
- **U-2**: `ste-linter` was not run (rule 2). Simplified Technical English conformance is a manual check.
- **U-3**: No test, linter, formatter, or container command was run (rule 2).
- **U-4**: GitHub lists no submitted review on PR #4507 (owner comment of 2026-11-09). A review outside GitHub is unverified.
- **U-5**: The claim of 31 credential candidates in `specs/1924-failure-evidence/inventory.md` is unverified. The file holds 253789 bytes. It was not parsed.
- **U-6**: The Dockerfile line that sets the SSH default password was not read. The claim rests on `.github/copilot-instructions.md` line 427 and `container/scripts/start.sh` lines 7 and 8.
- **U-7**: The effect of the `token` keyword in `maps_manager.py` line 2689 is inferred from the constructor signature. It was not executed.
- **U-8**: The effect of compose literal fallbacks is inferred from text. No container was started.
- **U-9**: Check rollups for the merged pull requests show SUCCESS and SKIPPED only. CodeQL and dependency audit results were not re-run.
- **U-10**: The OpenAPI scheme definition was not found. Only the security requirement at line 85 is cited.
- **U-11**: The owner measurement tool and its 2,295-file count were not reproduced.
- **U-12**: The owner classified the analyzer candidate as a static finding (2026-11-10). It was not verified.
- **U-13**: The number of `except` clauses in each changed file was not counted. SC-006 needs a measured baseline before batch 1.
- **U-14**: The compose interpolation rules for `:-` and `:?` are not checked against Compose documentation. D-7 depends on them.
