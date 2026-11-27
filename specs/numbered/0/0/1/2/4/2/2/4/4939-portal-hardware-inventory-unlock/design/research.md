# Research: Portal hardware inventory unlock without the free-form shell

## Summary

Issue #4939 asks for a narrower unlock for the Collect EX hardware inventory action. On `main`, the action needs `PORTAL_WS_ENABLE_SHELL=true`. That flag also unlocks every free-form shell. The code path, the lock rule, and the refusal are verified on `main` (table below). This record recommends option 1, a new hardware flag that unlocks only the server-owned hardware preset. The owner must approve option 1 (D-1).

## Decisions

### D-1 Unlock model (HUMAN-DECISION-REQUIRED)
- Alternatives: option 1, the hardware flag for the hardware preset only. Option 2, keep the shell flag rule and document it. Option 3, operator sign-in tracked by issue #4936.
- Chosen: option 1. The owner records the choice before any code starts. This record recommends option 1.
- Reason: only option 1 removes free-form shell access from the inventory path. Option 2 is already on `main` through PR #4940, and it keeps the full unlock. Option 3 is a separate credential policy.
- Risk: the owner chooses option 2. This record then closes without code.

### D-2 Flag name
- Alternatives: reuse the shell flag with a scope list. Use generic per-preset flags. Use the name `PORTAL_WS_ENABLE_HARDWARE_INVENTORY`.
- Chosen: `PORTAL_WS_ENABLE_HARDWARE_INVENTORY`.
- Reason: the name states the one action it unlocks. A generic mechanism is a non-goal in spec.md.
- Risk: the name is long. Documents and tests must use the exact name.

### D-3 Source of the lock scope
- Alternatives: key-based lock on `ex.createShellSession`. Browser field `lock_scope`. Server value set in the hardware branch.
- Chosen: server value `hardware_preset`, set in the hardware branch only.
- Reason: the lookup accepts any shell request with the same key (`stream_catalog.py` lines 46 to 48, RC-058), so a key cannot separate the paths. A browser field could widen the unlock.
- Risk: a future preset that needs the same unlock must add its own scope value.

### D-4 Check points
- Alternatives: check at preview only. Check at admission only. Check at preview per target and at admission.
- Chosen: preview per target (`sessions.py` line 447, RC-084) and admission (`sessions.py` lines 614 to 619, RC-087 and RC-088).
- Reason: the preview lists targets, so it needs the check. A flag change after preview needs the admission check.
- Risk: the check runs twice. The cost is one flag read and one scope value.

### D-5 Payload shape
- Alternatives: a top-level key for the hardware flag. Reuse `flags.shell` with a scope list.
- Chosen: `flags.hardware_inventory` with `enabled` and `variable`, the same shape as `flags.shell` (RC-061).
- Reason: the page already reads the `flags` structure. The shape stays consistent.
- Risk: an older page reads only `changes` and `shell`. The page reads the new key only when present.

### D-6 Invalid flag value
- Alternatives: refuse startup on an invalid value. Read false and warn once.
- Chosen: read false and log one warning that names the variable. The rule is the existing `_read_flag` rule (RC-124, RC-125, RC-128).
- Reason: the existing flags behave this way. A new rule for one flag adds a second behavior.
- Risk: a typo leaves the action locked. The warning names the variable.

### D-7 Settings field
- Alternatives: add one `StreamSettings` field. Add a second environment reader in the catalog.
- Chosen: add one field, and record the debt in plan.md Complexity Tracking.
- Reason: a second reader duplicates the parser and its warning. The field keeps one parser.
- Risk: `StreamSettings` grows from nine to ten fields (RC-051).

### D-8 Mistapi pin
- Alternatives: keep 0.64.1. Lower the floor to 0.64.0 to match the instruction line. Change the instruction line in this record.
- Chosen: keep 0.64.1. Record the instruction drift as finding A-01 in analysis.md.
- Reason: the feature needs no SDK change. A pin change or an instruction edit is unrelated work.
- Risk: the instruction line stays wrong until a separate issue fixes it.

### D-9 Transport
- Alternatives: call the SDK function `create_shell_session` directly. Add a REST endpoint. Reuse the owned `ShellClient`.
- Chosen: reuse the owned `ShellClient` without change (RC-101, RC-102).
- Reason: FR-014 forbids a new transport and a new REST call.
- Risk: whether repository code calls the SDK function on `main` is Unverified (U-2).

### D-10 Page hint
- Alternatives: change the refusal message text. Add a modal dialog. Show the flag name in a hidden element.
- Chosen: a hidden element `wsBatchHardwareLock` shows the flag name (T016, T017).
- Reason: the refusal message text is pinned by tests (RC-117). A modal adds a new interaction.
- Risk: the hidden element is not checked in a live browser (U-5).

### D-11 Env example ordering
- Alternatives: edit `deploy/.env.example` now. Skip the env example.
- Chosen: wait until draft PR #4208 merges or its owner completes a handover (T022).
- Reason: AGENTS.md lines 244 and 245 forbid a second open pull request on one file. The env example is required by FR-010.
- Risk: T022 and T008 case (2) wait for PR #4208.

### D-12 Contract amendment
- Alternatives: rewrite the shell lock section of the 4920 contract. Leave the contract unchanged.
- Chosen: a dated amendment under "Locks and limits" (RC-037, RC-038).
- Reason: the amendment keeps the history. The current text states that the shell lock gates the action.
- Risk: readers must read the amendment with the original text.

## Remote verification

Commit: `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` on `main`. The full tree holds 11404 entries and is not truncated. The table has 128 rows (RC-001 to RC-128). Result values are `present`, `absent`, and `stale`. The Blob column shows the first 12 characters of the blob SHA. Rows RC-034 to RC-036 read the installed package in `.venv`. Their blob is the local git object hash, computed without writing an object.

| ID | Path | Line | Claim | Result | Blob |
|----|------|------|-------|--------|------|
| RC-001 | AGENTS.md | 244 | Check open pull requests for overlap before work | present | 44a9afffb5bd |
| RC-002 | AGENTS.md | 245 | One file cannot carry two open pull requests | present | 44a9afffb5bd |
| RC-003 | .github/copilot-instructions.md | 50 | Local gates section heading | present | f1ec2a4694d0 |
| RC-004 | .github/copilot-instructions.md | 21 | Mistapi pin text reads 0.64.0 | stale | f1ec2a4694d0 |
| RC-005 | .github/copilot-instructions.md | 74 | STE gate lists five files | present | f1ec2a4694d0 |
| RC-006 | .specify/memory/constitution.md | 38 | Principle I Five-Item Rule | present | 4584997a264c |
| RC-007 | .specify/memory/constitution.md | 71 | Five hierarchy levels listed | present | 4584997a264c |
| RC-008 | .specify/memory/constitution.md | 91 | Principle II Class-Based Architecture | present | 4584997a264c |
| RC-009 | .specify/memory/constitution.md | 113 | Principle III Safety-First | present | 4584997a264c |
| RC-010 | .specify/memory/constitution.md | 143 | Principle IV Full Deployment Pipeline | present | 4584997a264c |
| RC-011 | .specify/memory/constitution.md | 148 | Pipeline steps 1 to 9 | present | 4584997a264c |
| RC-012 | .specify/memory/constitution.md | 166 | Pipeline steps 10 to 12 | present | 4584997a264c |
| RC-013 | .specify/memory/constitution.md | 182 | Principle V Observability and Logging | present | 4584997a264c |
| RC-014 | .specify/memory/constitution.md | 204 | Principle VI Inline Comments | present | 4584997a264c |
| RC-015 | .specify/memory/constitution.md | 235 | Principle VII Action Logging | present | 4584997a264c |
| RC-016 | .specify/memory/constitution.md | 420 | Complexity-Driven SpecKit Escalation | present | 4584997a264c |
| RC-017 | .specify/templates/spec-template.md | 0 | Template exists | present | 083ef123c7a2 |
| RC-018 | .specify/templates/plan-template.md | 0 | Template exists | present | 1a54553bd85c |
| RC-019 | .specify/templates/tasks-template.md | 0 | Template exists | present | 7e5170324d41 |
| RC-020 | .specify/templates/checklist-template.md | 0 | Template exists | present | 806657da09d1 |
| RC-021 | changelog.d/README.md | 38 | Change types are Added, Changed, Fixed, Removed, Security | present | fcbde10e0c29 |
| RC-022 | changelog.d/issue-4939-portal-hardware-inventory-unlock.md | 0 | Fragment is not on main | absent | none |
| RC-023 | specs/numbered/0/0/1/2/4/2/2/4/4939-portal-hardware-inventory-unlock | 0 | Record folder is not on main | absent | none |
| RC-024 | .github/workflows/ci.yml | 93 | MYPY_PATHS value | present | d51efbc13c0f |
| RC-025 | .github/workflows/ci.yml | 101 | VULTURE_PATHS value | present | d51efbc13c0f |
| RC-026 | .github/workflows/ci.yml | 104 | PYDOCSTYLE_PATHS value | present | d51efbc13c0f |
| RC-027 | .github/workflows/ci.yml | 107 | INTERROGATE_PATHS value | present | d51efbc13c0f |
| RC-028 | .github/workflows/ci.yml | 123 | Interrogate threshold default 90 | present | d51efbc13c0f |
| RC-029 | .github/workflows/ci.yml | 127 | Vulture confidence default 70 | present | d51efbc13c0f |
| RC-030 | .github/workflows/container-build.yml | 0 | Container build workflow exists | present | 737325976de7 |
| RC-031 | pyproject.toml | 23 | Python requirement is 3.15 or later | present | eca34c826ea4 |
| RC-032 | pyproject.toml | 29 | Mistapi pin is 0.64.1 below 0.65 | present | eca34c826ea4 |
| RC-033 | requirements.txt | 129 | Mistapi pinned at 0.64.1 | present | 50fe63d4cf5e |
| RC-034 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA | 3 | Installed mistapi version is 0.64.1 | present | 86b3b7003d56 (local) |
| RC-035 | .venv\Lib\site-packages\mistapi\device_utils\__tools\shell.py | 314 | Function create_shell_session is defined | present | e49283a6f955 (local) |
| RC-036 | .venv\Lib\site-packages\mistapi\device_utils\ex.py | 63 | Alias createShellSession points to create_shell_session | present | ab5308eb0cf7 (local) |
| RC-037 | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/contracts/portal.md | 94 | Locks and limits section | present | 7681942fa5f2 |
| RC-038 | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/design/contracts/portal.md | 96 | Shell lock still gates the action | present | 7681942fa5f2 |
| RC-039 | deploy/.env.example | 218 | Warning about the remote shell | present | 713736442330 |
| RC-040 | deploy/.env.example | 221 | Commented shell flag line | present | 713736442330 |
| RC-041 | deploy/.env.example | 0 | Hardware flag name is not in the file | absent | 713736442330 |
| RC-042 | documentation/operator-guide.md | 398 | Collect EX hardware action heading | present | 60d28f9ea461 |
| RC-043 | documentation/operator-guide.md | 415 | Steps name the shell flag | present | 60d28f9ea461 |
| RC-044 | documentation/operator-guide.md | 432 | Sentence refers to issue 4939 narrower unlock | present | 60d28f9ea461 |
| RC-045 | documentation/operator-guide.md | 0 | Hardware flag name is not in the file | absent | 60d28f9ea461 |
| RC-046 | documentation/wiki/Web-Portal.md | 130 | Unlock steps start | present | e9dac116b73e |
| RC-047 | documentation/wiki/Web-Portal.md | 284 | Shell flag settings row | present | e9dac116b73e |
| RC-048 | documentation/wiki/Web-Portal.md | 291 | Hardware concurrency settings row | present | e9dac116b73e |
| RC-049 | documentation/wiki/Web-Portal.md | 0 | Hardware flag name is not in the file | absent | e9dac116b73e |
| RC-050 | src/mist/realtime/websocket_streams/live/sessions/settings.py | 20 | StreamSettings class | present | a93befc8b3ff |
| RC-051 | src/mist/realtime/websocket_streams/live/sessions/settings.py | 35 | Nine attribute fields on lines 35 to 43 | present | a93befc8b3ff |
| RC-052 | src/mist/realtime/websocket_streams/live/sessions/settings.py | 46 | Method from_environment | present | a93befc8b3ff |
| RC-053 | src/mist/realtime/websocket_streams/live/sessions/settings.py | 59 | Shell flag read by _read_flag | present | a93befc8b3ff |
| RC-054 | src/mist/realtime/websocket_streams/live/sessions/settings.py | 69 | Method from_environment returns settings | present | a93befc8b3ff |
| RC-055 | src/mist/realtime/websocket_streams/live/sessions/settings.py | 88 | Method _read_flag | present | a93befc8b3ff |
| RC-056 | src/mist/realtime/websocket_streams/live/sessions/settings.py | 0 | Hardware flag name is not in the file | absent | a93befc8b3ff |
| RC-057 | src/mist/realtime/websocket_streams/catalog/registry/stream_catalog.py | 27 | Constant SHELL_FLAG | present | 22e7347226b9 |
| RC-058 | src/mist/realtime/websocket_streams/catalog/registry/stream_catalog.py | 46 | Lookup accepts shell kind by key | present | 22e7347226b9 |
| RC-059 | src/mist/realtime/websocket_streams/catalog/registry/stream_catalog.py | 52 | Method lock_flag | present | 22e7347226b9 |
| RC-060 | src/mist/realtime/websocket_streams/catalog/registry/stream_catalog.py | 57 | Shell utilities locked when shell flag is false | present | 22e7347226b9 |
| RC-061 | src/mist/realtime/websocket_streams/catalog/registry/stream_catalog.py | 75 | Payload entry flags shell | present | 22e7347226b9 |
| RC-062 | src/mist/realtime/websocket_streams/catalog/registry/stream_catalog.py | 0 | Hardware flag names are not in the file | absent | 22e7347226b9 |
| RC-063 | src/mist/realtime/websocket_streams/catalog/utilities/metadata/utility_profile.py | 11 | createShellSession selects Safety.SHELL | present | 506101640c30 |
| RC-064 | src/mist/realtime/websocket_streams/catalog/utilities/metadata/utility_text.py | 39 | Label of createShellSession is Remote shell | present | 535c724843b7 |
| RC-065 | src/mist/realtime/websocket_streams/intake/start_request/validation.py | 23 | Class RequestValidator | present | 6955995ff56d |
| RC-066 | src/mist/realtime/websocket_streams/intake/start_request/validation.py | 53 | Method check_lock | present | 6955995ff56d |
| RC-067 | src/mist/realtime/websocket_streams/intake/start_request/validation.py | 59 | Locked refusal carries the flag | present | 6955995ff56d |
| RC-068 | src/mist/realtime/websocket_streams/intake/start_request/validation.py | 0 | Lock scope is not in the file | absent | 6955995ff56d |
| RC-069 | src/mist/realtime/websocket_streams/intake/start_request/checker.py | 57 | Method check_batch | present | 211ac5fd40b5 |
| RC-070 | src/mist/realtime/websocket_streams/intake/start_request/checker.py | 67 | Method resolve_definition | present | 211ac5fd40b5 |
| RC-071 | src/mist/realtime/websocket_streams/intake/start_request/checker.py | 0 | Lock scope is not in the file | absent | 211ac5fd40b5 |
| RC-072 | src/mist/realtime/websocket_streams/intake/fields/error.py | 14 | Code bad_request maps to 400 | present | a509d72dee9a |
| RC-073 | src/mist/realtime/websocket_streams/intake/fields/error.py | 16 | Code locked maps to 403 | present | a509d72dee9a |
| RC-074 | src/operations/exporting/ex_hardware_inventory/run/routing.py | 207 | Class ScopeAwareChecker | present | aeeb69cd62fb |
| RC-075 | src/operations/exporting/ex_hardware_inventory/run/routing.py | 215 | Method check_batch | present | aeeb69cd62fb |
| RC-076 | src/operations/exporting/ex_hardware_inventory/run/routing.py | 223 | Forwards the body to the checker | present | aeeb69cd62fb |
| RC-077 | src/operations/exporting/ex_hardware_inventory/run/routing.py | 0 | Lock scope is not in the file | absent | aeeb69cd62fb |
| RC-078 | src/operations/exporting/ex_hardware_inventory/run/batch.py | 144 | CLI settings set shell_enabled to true | present | 5fe7b5061eda |
| RC-079 | src/operations/exporting/ex_hardware_inventory/run/batch.py | 147 | CLI catalog sets shell unlock | present | 5fe7b5061eda |
| RC-080 | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | 77 | Preview lifetime is 300 seconds | present | edcb8413d4bf |
| RC-081 | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | 94 | Method selection of Input | present | edcb8413d4bf |
| RC-082 | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | 113 | Method parse of SelectionParser | present | edcb8413d4bf |
| RC-083 | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | 149 | Operation resolves the definition with lock rules | present | edcb8413d4bf |
| RC-084 | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | 447 | Per-target call to check_batch | present | edcb8413d4bf |
| RC-085 | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | 570 | Preview expiry comparison | present | edcb8413d4bf |
| RC-086 | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | 606 | Method admission | present | edcb8413d4bf |
| RC-087 | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | 614 | Method validate_fingerprint | present | edcb8413d4bf |
| RC-088 | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | 619 | Stored operation resolved again | present | edcb8413d4bf |
| RC-089 | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | 628 | Start values include the preset | present | edcb8413d4bf |
| RC-090 | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | 865 | Class WebSocketBatchService | present | edcb8413d4bf |
| RC-091 | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | 900 | Preview validates the selection | present | edcb8413d4bf |
| RC-092 | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | 916 | Method start | present | edcb8413d4bf |
| RC-093 | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | 0 | Lock scope is not in the file | absent | edcb8413d4bf |
| RC-094 | src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py | 300 | Class HardwareXmlPreset | present | bb018c99e0fc |
| RC-095 | src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py | 303 | Preset name ex-hardware-xml | present | bb018c99e0fc |
| RC-096 | src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py | 304 | Fixed command text | present | bb018c99e0fc |
| RC-097 | src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py | 344 | Allowed browser fields exclude commands | present | bb018c99e0fc |
| RC-098 | src/mist/realtime/websocket_streams/web/services/operations/hardware_xml.py | 365 | Shell operation uses ex.createShellSession | present | bb018c99e0fc |
| RC-099 | src/mist/realtime/websocket_streams/web/services/assembly/collaborators.py | 48 | Method _catalog | present | fed35c53a77b |
| RC-100 | src/mist/realtime/websocket_streams/web/services/assembly/collaborators.py | 58 | Constructor call StreamCatalog | present | fed35c53a77b |
| RC-101 | src/mist/realtime/websocket_streams/live/transport/shell_client.py | 0 | Owned ShellClient module exists | present | 902fbe2db6cc |
| RC-102 | src/mist/realtime/websocket_streams/live/runners/shell/lifecycle/opening.py | 90 | Owned ShellClient is created | present | a5f80e0b1f28 |
| RC-103 | src/mist/realtime/websocket_streams/live/transport/endpoint.py | 45 | Reads the _apitoken attribute | present | 6a1c1a6296e8 |
| RC-104 | src/mist/realtime/websocket_streams/web/blueprint/routes/sessions.py | 110 | Preview checks the preset name | present | 2b94e1d02056 |
| RC-105 | src/mist/realtime/websocket_streams/web/static/websockets.js | 69 | Site query uses kind shell | present | c0b4f4397432 |
| RC-106 | src/mist/realtime/websocket_streams/web/static/websockets.js | 204 | Function changeBatchHardwarePreset | present | c0b4f4397432 |
| RC-107 | src/mist/realtime/websocket_streams/web/static/websockets.js | 0 | Lock element is not in the file | absent | c0b4f4397432 |
| RC-108 | src/mist/realtime/websocket_streams/web/templates/websockets_page.html | 177 | Hardware preset checkbox | present | cba30182879b |
| RC-109 | src/mist/realtime/websocket_streams/web/templates/websockets_page.html | 189 | Hardware format select | present | cba30182879b |
| RC-110 | src/mist/realtime/websocket_streams/web/templates/websockets_page.html | 0 | Lock element is not in the file | absent | cba30182879b |
| RC-111 | tests/unit/websocket_streams/live/sessions/test_ws_stream_settings.py | 32 | Shell off case | present | cfb656dcca0a |
| RC-112 | tests/unit/websocket_streams/catalog/test_ws_stream_catalog.py | 23 | Catalog fixture | present | 85b08985b579 |
| RC-113 | tests/unit/websocket_streams/catalog/test_ws_stream_catalog.py | 37 | Shell lookup assertion | present | 85b08985b579 |
| RC-114 | tests/unit/websocket_streams/intake/test_ws_start_request.py | 194 | Checker fixture with changes locked | present | bd185f3056df |
| RC-115 | tests/unit/websocket_streams/web/test_ws_web_services.py | 489 | Shell safety fixture | present | d20a6c7b2f7e |
| RC-116 | tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py | 34 | Fixed command constant | present | dc4422ccd00a |
| RC-117 | tests/integration/ex_hardware_inventory/test_hardware_portal_flow.py | 569 | Locked message constant | present | dc4422ccd00a |
| RC-118 | tests/unit/ex_hardware_inventory/run/test_hardware_routing.py | 53 | Fake checker calls check_batch with body | present | 640689ce86b7 |
| RC-119 | tests/e2e/websockets_tab/test_websockets_page.py | 159 | Flags fixture | present | 2d608a96bae7 |
| RC-120 | tests/e2e/websockets_tab/test_websockets_page.py | 998 | Hardware preset click | present | 2d608a96bae7 |
| RC-121 | tests/guardrails/test_hardware_shell_lock_docs.py | 112 | Refusal helper locked_refusal | present | 83926b3fbc87 |
| RC-122 | tests/guardrails/test_hardware_shell_lock_docs.py | 140 | Steps tuple | present | 83926b3fbc87 |
| RC-123 | tests/guardrails/test_hardware_shell_lock_docs.py | 0 | Hardware flag name is not in the file | absent | 83926b3fbc87 |
| RC-124 | src/mist/realtime/websocket_streams/live/sessions/settings.py | 100 | Enabled values are 1, true, yes, on | present | a93befc8b3ff |
| RC-125 | src/mist/realtime/websocket_streams/live/sessions/settings.py | 104 | Invalid flag logs one warning that names the variable | present | a93befc8b3ff |
| RC-126 | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | 135 | Unknown field refused with bad_request | present | edcb8413d4bf |
| RC-127 | src/mist/realtime/websocket_streams/web/services/operations/sessions.py | 610 | Unknown or expired preview refused | present | edcb8413d4bf |
| RC-128 | src/mist/realtime/websocket_streams/live/sessions/settings.py | 102 | Disabled values are empty, 0, false, no, off | present | a93befc8b3ff |

Counts: 128 rows. Results: 113 present, 1 stale (RC-004), and 14 absent (RC-022, RC-023, RC-041, RC-045, RC-049, RC-056, RC-062, RC-068, RC-071, RC-077, RC-093, RC-107, RC-110, RC-123).

## Linked work

- Issue #4939: OPEN. Labels `feature` and `web-portal`. Updated 2026-11-26.
- Issue #4936: OPEN. Browser sign-in with two-factor support (option 3).
- Issue #4938: CLOSED. Documentation that the action needs `PORTAL_WS_ENABLE_SHELL`.
- PR #4940: MERGED on 2026-11-26. Changed five files. Four of them are in this change map (analysis.md A-06).
- PR #4208: OPEN draft. Changes `deploy/.env.example` (analysis.md A-05).
- PR #4813: OPEN draft. CSV carriage returns. No file overlap with this change map.
- PR #4569: MERGED on 2026-11-05. Unrelated dependency bump that matched the search text.
- Overlap scan: seven open pull requests. One shares a file with this change map (PR #4208).

## Sources

- Brief: `C:\Users\jmorrison\.copilot\session-state\30878eb1-80d0-451d-bd0c-0b3624089852\files\spec-brief.md`.
- Remote tree: `gh api repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1` (11404 entries).
- Remote file bodies: `gh api -H "Accept: application/vnd.github.raw" repos/jmorrison-juniper/MistHelper/contents/<path>?ref=main`.
- Remote issues and pull requests: `gh issue view`, `gh pr view`, and `gh pr list` on `jmorrison-juniper/MistHelper`.
- Installed package: `.venv\Lib\site-packages\mistapi\device_utils\__tools\shell.py` lines 308 to 326, `.venv\Lib\site-packages\mistapi\device_utils\ex.py` lines 58 to 66, and `.venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA` lines 1 to 4.
- Skill: juniper-cliref-operational, file `04-chassis-and-hardware/04-chassis-hardware-inventory.md`. It confirms that `show chassis hardware` needs view privilege.
- Mist API: no endpoint lookup. This change adds no REST call (FR-014).
- Containers: no Podman skill and no container run.

## Mist API and SDK

- The change adds no Mist REST endpoint and no mistapi REST method.
- The SDK shell function is read from the installed package (RC-035, RC-036).
- Whether repository code on `main` calls the SDK function is Unverified (U-2).

## Unverified

- U-1: The live 403 reproduction in the issue body (2026-11-25). No container run is allowed in this record.
- U-2: Whether repository code on `main` calls the SDK function `create_shell_session` directly. Only the installed package was read.
- U-3: Junos pipe behavior of `display xml` and `no-more` in the fixed command. The local skill confirms only the view privilege of `show chassis hardware`.
- U-4: Whether the Multi Site site query (`websockets.js` line 69) returns the lock when both flags are false.
- U-5: Rendering of the new hidden element. No Playwright run is allowed in this record.
- U-6: Effect of `PORTAL_ALLOWED_IPS` in the owner deployment. The spec assumption is not checked in a deployment.
- U-7: Owner acceptance of option 1 and of the flag name. Recorded as D-1.
- U-8: Container build, revision label, and deploy checks (constitution lines 166 to 171). These run after the merge, outside this record.
- U-9: Refusal code and HTTP status for an unknown output format. The verified lines refuse site selections with `bad_request` (`hardware_xml.py` lines 56 to 61). No verified line refuses an unknown output format.
- U-10: Installed mistapi files other than the three cited files. Only the cited files were read.
