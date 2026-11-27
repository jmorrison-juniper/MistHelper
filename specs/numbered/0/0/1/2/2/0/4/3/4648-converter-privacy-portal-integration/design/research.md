# Research: Converter Privacy and Shared Portal Integration

Each decision lists the options, the chosen option, the reason, and the risk. Facts come from read-only remote checks against GitHub `main` and from local copies that match those remote blobs.

## Source Baseline

- Remote `main` commit: `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (2026-11-26T07:15:01Z).
- Remote tree: not truncated. It holds 11,404 entries.
- Local HEAD: the same commit. `git hash-object` matched the remote blob for these files: `web_portal/app.py`, `web_portal/templates/base.html`, `src/interfaces/portals/cisco_config_converter/routes.py`, `tests/integration/web_portal/cisco_config_converter/test_routes.py`, `tests/e2e/conftest.py`, `wsgi.py`, `MistHelper.py`, `web_portal/services/config.py`, and the live and parent record documents. For those files, local line numbers equal remote line numbers. Every other line number came from a remote read.

## Decisions

### D-1. Split T031 into offline work now and integration work later

- **Options**: (a) run all of T031 after every prerequisite closes. (b) integrate now. (c) split the work. Chosen: (c).
- **Reason**: The issue requires cross-cutting tests before integration. Rows that depend on T022, T028, and T030 cannot pass now (live `tasks.md` line 156).
- **Risk**: The offline suite covers the offline blueprint only. Decision D-2 limits this risk.
- **Human decision**: No.

### D-2. Use a composition harness for real-factory tests before the handover

- **Options**: (a) an isolated blueprint host, as in the existing route tests. (b) edit the shared files now. (c) a test-only harness on the real factory. Chosen: (c).
- **Reason**: The issue requires the real factory. The harness calls `WebPortalApp.create_app` the way `tests/e2e/conftest.py` lines 273 to 277 do. It sets the request class and registers the blueprint in memory.
- **Risk**: The harness can diverge from T009. Test `test_handover_state_matches_shared_files` changes at T009, and the same tests run afterward.
- **Human decision**: No.

### D-3. Gate shared-file edits on the G3 handover and the prerequisites

- **Options**: (a) wait for PR #4208 to merge. (b) require a handover comment on issue #4648, PR #4208 to close or merge, and the four prerequisite issues to close. (c) skip the handover. Chosen: (b).
- **Reason**: The issue body requires owner confirmation of the exact paths. The coordinator decision on issue #4633 names PR #4208 as the blocker. The issue lists four prerequisites.
- **Risk**: The gate delays integration. The delay protects the shared files from a conflict.
- **Human decision**: No.

### D-4. Place the browser module in the feature folder

- **Options**: (a) `tests/e2e/web_portal/`, which adds a child to a noncompliant parent (R-26). (b) a new package under `tests/e2e/`, which makes that folder six children (R-25). (c) `tests/integration/web_portal/cisco_config_converter/` (R-15). Chosen: (c).
- **Reason**: The constitution bars a new direct child in a noncompliant parent. Issue #4636 analysis remediation R-3 recommends a feature folder.
- **Risk**: The E2E hook in `tests/e2e/conftest.py` (lines 192 to 225) does not cover the module. The module sets its own timeout mark of 120 seconds (R-23).
- **Human decision**: No.

### D-5. Verify debug defaults by test only

- **Options**: (a) set `app.debug = False` in `create_app`. (b) test the current behavior only. Chosen: (b).
- **Reason**: The container runner forces `debug=False` (R-40). The `--debug` flag defaults to false (R-41). The factory sets no debug flag, so the defaults hold.
- **Risk**: A later edit can enable debug. Tests `test_debug_off_in_real_factory` and `test_container_runner_forces_debug_false` catch that edit.
- **Human decision**: No.

### D-6. Reuse the shared CSRF answer

- **Options**: (a) a converter-specific CSRF handler. (b) the shared handler (chosen).
- **Reason**: The shared handler answers JSON callers with `csrf_expired` and status 400 (R-36). A second handler would change shared request handling.
- **Risk**: The shared handler applies to every route. Tests check the converter prefix, the `/api/` prefix, and a browser caller.
- **Human decision**: No.

### D-7. Set the request class for the whole portal, with a converter prefix guard

- **Options**: (a) a per-blueprint request class, which Flask does not support. (b) an app-wide class with a prefix guard (chosen). (c) no class, which fails the registration guard (R-04).
- **Reason**: The registration guard requires the class (routes.py lines 105 to 106). The guard limits the upload behavior to the converter prefix (routes.py lines 20 to 42).
- **Risk**: The class applies to every request. Test `test_other_upload_routes_keep_flask_limits` checks a route outside the prefix.
- **Human decision**: No.

### D-8. Block cloud write routes with an allowlist test

- **Options**: (a) no guard. (b) an allowlist of the five approved rules (chosen).
- **Reason**: Cloud writes need issue #4644, the decision gates G2, G4, and G5, and owner approval. The allowlist fails on any new rule.
- **Risk**: Issue #4644 must update the allowlist. That update needs owner approval.
- **Human decision**: No.

### D-9. Use a synthetic secret in tests and keep the production fallback decision open

- **Options**: (a) change the random fallback now. (b) keep the fallback and set a synthetic key in tests (chosen).
- **Reason**: A shared fallback change needs the G3 handover first. The production policy affects credentials and multi-process deployments (R-37). Issue #4636 decision D-15 asks the same question.
- **Risk**: Multi-process deployments fail CSRF until the owner decides. The container runs one worker (R-39).
- **Human decision**: HUMAN-DECISION-REQUIRED. Credential policy belongs to the owner. This issue does not block on it.

### D-10. Defer storage exposure tests to the storage issues

- **Options**: (a) write tests against a fake store now. (b) defer the tests to task T014 with a named trigger (chosen).
- **Reason**: The converter writes no file today. The offline journey patches `builtins.open` and expects no call (`test_routes.py` lines 60 to 66). No private store exists yet.
- **Risk**: A storage change can skip the tests. T014 names issues #4636 and #4643 as the trigger.
- **Human decision**: No.

### D-11. Store browser evidence in `test-artifacts/cisco-portal/`

- **Options**: (a) `data/`, which holds product output. (b) `tmp_path`, which pytest removes after a failure. (c) `test-artifacts/`, which Git ignores (R-48). Chosen: (c).
- **Reason**: The constitution places generated test evidence in `test-artifacts/`.
- **Risk**: None known.
- **Human decision**: No.

### D-12. Read the comparison table with a guard test

- **Options**: (a) manual review. (b) a guard test that reads the live comparison table (chosen).
- **Reason**: The table holds forty rows (R-60, R-61). A guard fails when a row loses its disposition.
- **Risk**: The guard reads a spec path. The test uses the fixed path from the task list.
- **Human decision**: No.

### D-13. Use an exact-key health contract with an integer uptime

- **Options**: (a) an exact uptime value, which is unstable. (b) a status check only, which is weak. (c) exact keys and an integer type (chosen).
- **Reason**: The monitors match the word `healthy` exactly (R-33). The `services` map must not change.
- **Risk**: None known.
- **Human decision**: No.

### D-14. Reuse no source expression, so the license row does not block this issue

- **Options**: (a) wait for issue #4635 before any test. (b) continue, and keep row C40 open (chosen).
- **Reason**: Issue #4648 requires original code and assets only. The integration reuses no source expression.
- **Risk**: Issue #4635 may later require a change. Task T014 keeps row C40 open until that decision.
- **Human decision**: No.

### D-15. Size M, record status complete, implementation waits on the gates

- **Options**: (a) size L, as issue #4636 has. (b) size M (chosen).
- **Reason**: The work touches two shared files and adds two modules with 28 test functions. The record is complete. The implementation waits on the gates in D-3.
- **Risk**: The size changes after the handover if the owner adds scope.
- **Human decision**: No.

## Remote Verification

Each row is one remote check. The result uses `present`, `absent`, `partial`, or `stale`. A result of `absent` confirms a claim that a file, route, or import does not exist. A `not-a-blob` value marks a path that does not exist on `main`.

| ID | Claim | Path | Blob or tree SHA | Result | Line |
| - | - | - | - | - | - |
| R-01 | Converter package holds five direct children | src/interfaces/portals/cisco_config_converter | 363cf44f8bad5dfdcd344a76852a8a34146b9190 | present | 0 |
| R-02 | Converter blueprint sets the prefix /cisco-config-converter | src/interfaces/portals/cisco_config_converter/routes.py | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 54 |
| R-03 | Converter body limit is 16 MiB plus 16 KiB | src/interfaces/portals/cisco_config_converter/routes.py | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 36 |
| R-04 | Registration guard requires ConverterRequest and CSRFProtect | src/interfaces/portals/cisco_config_converter/routes.py | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 103 |
| R-05 | Converter responses set Cache-Control to no-store | src/interfaces/portals/cisco_config_converter/routes.py | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 113 |
| R-06 | Validation logs use static text and the error type only | src/interfaces/portals/cisco_config_converter/routes.py | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 83 |
| R-07 | Converter package has no Mist SDK, HTTP, or socket import | src/interfaces/portals/cisco_config_converter | 363cf44f8bad5dfdcd344a76852a8a34146b9190 | absent | 0 |
| R-08 | Review state keeps a digest only in the session | src/interfaces/portals/cisco_config_converter/models.py | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 96 |
| R-09 | Unsupported items use labels and omit source values | src/interfaces/portals/cisco_config_converter/conversion.py | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 83 |
| R-10 | Browser script sends the X-CSRFToken header | src/interfaces/portals/cisco_config_converter/presentation/converter.js | 9c7ad354600aade5b3a37bbd536ac49486edfd6e | present | 56 |
| R-11 | Browser script uses no local or session storage | src/interfaces/portals/cisco_config_converter/presentation/converter.js | 9c7ad354600aade5b3a37bbd536ac49486edfd6e | absent | 0 |
| R-12 | Converter page exposes stable cisco test IDs | src/interfaces/portals/cisco_config_converter/presentation/converter.html | 270c3e40e226c026a54aef846f9b341d6a76eee9 | present | 11 |
| R-13 | Existing offline journey test blocks sockets and file opens | tests/integration/web_portal/cisco_config_converter/test_routes.py | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 60 |
| R-14 | Existing test keeps Flask upload behavior for other routes | tests/integration/web_portal/cisco_config_converter/test_routes.py | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 194 |
| R-15 | Converter test folder holds two direct children | tests/integration/web_portal/cisco_config_converter | 6538f20cdb454342a96e079a0e7678fb6baa7a42 | present | 0 |
| R-16 | Planned parity test module is absent | tests/integration/web_portal/cisco_config_converter/test_parity.py | not-a-blob | absent | 0 |
| R-17 | Converter unit test exists at the marvis path | tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py | 31a84e3795665ebea1a9346fd835fffc619a9fe7 | present | 0 |
| R-18 | Stale unit test path from the parent record is absent | tests/unit/gateway/overrides/test_cisco_config_converter.py | not-a-blob | absent | 0 |
| R-19 | Isolated browser test imports the converter route test module | tests/e2e/web_portal/test_portal_smoke.py | 56e87d332700603c9925aa061c4594f864e7ac49 | present | 18 |
| R-20 | Isolated browser fixture serves the blueprint with make_server | tests/e2e/web_portal/test_portal_smoke.py | 56e87d332700603c9925aa061c4594f864e7ac49 | present | 29 |
| R-21 | Existing health endpoint test class | tests/e2e/web_portal/test_portal_smoke.py | 56e87d332700603c9925aa061c4594f864e7ac49 | present | 404 |
| R-22 | E2E flask_app fixture calls the real factory without an API session | tests/e2e/conftest.py | e450e1855770d2e0ec587935a95233262b118ae1 | present | 273 |
| R-23 | E2E timeout constant is 120 seconds | tests/e2e/conftest.py | e450e1855770d2e0ec587935a95233262b118ae1 | present | 33 |
| R-24 | Planned browser module path from issue #4647 is absent | tests/e2e/web_portal/test_cisco_parity.py | not-a-blob | absent | 0 |
| R-25 | tests/e2e holds five direct children | tests/e2e | 828f24a6106147d9263b550da13acfaa4866b3bf | present | 0 |
| R-26 | tests/e2e/web_portal holds 32 direct children | tests/e2e/web_portal | 3d492d6e0bec7e4a76925d345c095dfa44bb813e | present | 0 |
| R-27 | Factory applies security before blueprint registration | web_portal/app.py | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 52 |
| R-28 | Factory calls _register_blueprints after security | web_portal/app.py | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 53 |
| R-29 | Portal registers no converter blueprint | web_portal/app.py | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | absent | 0 |
| R-30 | Portal sets no request class | web_portal/app.py | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | absent | 0 |
| R-31 | Navigation bar holds the licensing comparison entry | web_portal/templates/base.html | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | present | 79 |
| R-32 | Navigation bar holds no converter entry | web_portal/templates/base.html | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | absent | 0 |
| R-33 | Health route returns status and services keys | web_portal/routes/dashboard.py | 9a4f0f5398483b3dac56fdbf084d1ebd1554c300 | present | 62 |
| R-34 | Ready route is defined | web_portal/routes/dashboard.py | 9a4f0f5398483b3dac56fdbf084d1ebd1554c300 | present | 69 |
| R-35 | CSRFProtect initializes inside the security middleware | web_portal/services/config.py | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 301 |
| R-36 | CSRF failures answer JSON for /api/ paths or JSON callers | web_portal/services/config.py | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 335 |
| R-37 | Portal secret falls back to a random UUID | web_portal/services/config.py | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 113 |
| R-38 | WSGI builds the portal through create_app | wsgi.py | e8b2be7cb33c54266afcd5723293b7487df4d365 | present | 107 |
| R-39 | WSGI docstring names one Gunicorn worker | wsgi.py | e8b2be7cb33c54266afcd5723293b7487df4d365 | present | 4 |
| R-40 | Container runner forces debug to False | MistHelper.py | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 6889 |
| R-41 | Debug flag defaults to False | MistHelper.py | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 7271 |
| R-42 | Compose file holds no converter service | compose.yml | b3944fc9f994ca149974072b1a9c8f13797d7924 | absent | 0 |
| R-43 | Flask 3.1.3 is pinned | requirements.txt | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 49 |
| R-44 | Flask-WTF 1.3.0 is pinned | requirements.txt | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 54 |
| R-45 | pytest-playwright 0.10.0 is pinned | requirements-dev.txt | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 333 |
| R-46 | pytest-timeout 2.4.0 is pinned | requirements-dev.txt | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 335 |
| R-47 | Python floor is 3.15 | pyproject.toml | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 23 |
| R-48 | test-artifacts folder is git-ignored | .gitignore | 17eadfadb35a59e191a61c78877569ad747ddcc7 | present | 107 |
| R-49 | Local gates table has the Tests row | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| R-50 | Local gates table has the STE row | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| R-51 | CI defines VULTURE_PATHS with web_portal | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| R-52 | CI defines the playwright job | .github/workflows/ci.yml | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 954 |
| R-53 | AGENTS.md has the writing style section | AGENTS.md | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| R-54 | AGENTS.md has the inline comment rule | AGENTS.md | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 97 |
| R-55 | Constitution Principle III is safety-first | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 113 |
| R-56 | Constitution Principle VI is inline comments | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| R-57 | Live T031 task text | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 112 |
| R-58 | Live T032 task text | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 113 |
| R-59 | Live T032 dependency row | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 156 |
| R-60 | Live C36 comparison row | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 120 |
| R-61 | Live C40 comparison row | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 124 |
| R-62 | Live G3 decision gate row | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/analysis.md | a08601943e89b95af5ebe9530c0d8b9bb47459ab | present | 25 |
| R-63 | Live FR-029 requirement | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 135 |
| R-64 | Live FR-032 requirement | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 138 |
| R-65 | Parent FR-010 forbids storing content or credentials | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/spec.md | 5e8b1bc162cbfe2e9a3d604420c42e670dd0cd97 | present | 72 |
| R-66 | Parent T015 registration remains open | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/tasks.md | fcdff941b5dfd214ae882be77d26c17ec903e8d5 | present | 51 |
| R-67 | Parent T027 existing-behavior check remains open | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/tasks.md | fcdff941b5dfd214ae882be77d26c17ec903e8d5 | present | 85 |
| R-68 | Parent plan states Python 3.13 | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/plan.md | 9c3fdacc929850e1ed923b248f1dc6520aa01fdd | stale | 15 |
| R-69 | Parent contract requires the request class | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/contracts/portal.md | 774b487ab32ae1417368ba79930e7eac0b3dad43 | present | 43 |
| R-70 | Route script sets base five | .specify/scripts/powershell/spec-route.ps1 | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| R-71 | Changelog fragment policy guard exists | tests/guardrails/test_changelog_fragment_policy.py | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 0 |
| R-72 | Nested package guard exists | tests/guardrails/test_nested_package_structure.py | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 0 |
| R-73 | Test-quality configuration exists | .github/test-quality-config.toml | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 0 |
| R-74 | tests/integration/web_portal holds four direct children | tests/integration/web_portal | 1ae7142b9720687639abc3e3fc3212351f01304a | present | 0 |
| R-75 | web_portal holds seven direct children | web_portal | 1d1a9efa3f808aed5698f655385f4294e7accf06 | present | 0 |
| R-76 | src/interfaces/portals holds six direct children | src/interfaces/portals | 7f5ac6778b6a7a78ad7268542bb8de2a9c550926 | present | 0 |
| R-77 | Factory defines create_app | web_portal/app.py | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 37 |
| R-78 | Factory defines _register_blueprints | web_portal/app.py | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 182 |
| R-79 | Converter file-stream guard checks the converter prefix | src/interfaces/portals/cisco_config_converter/routes.py | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 28 |
| R-80 | Converter body-limit guard checks the converter prefix | src/interfaces/portals/cisco_config_converter/routes.py | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 35 |
| R-81 | Registration guard checks the request class | src/interfaces/portals/cisco_config_converter/routes.py | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 105 |
| R-82 | Registration guard checks CSRF | src/interfaces/portals/cisco_config_converter/routes.py | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 107 |
| R-83 | Converter action path sets Cache-Control to no-store | src/interfaces/portals/cisco_config_converter/routes.py | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 149 |
| R-84 | CSRF configuration function starts at line 297 | web_portal/services/config.py | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 297 |
| R-85 | CSRF answer returns the Flask-WTF HTML page for non-JSON callers | web_portal/services/config.py | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 321 |
| R-86 | CSRF answer returns status 400 in JSON form | web_portal/services/config.py | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 328 |
| R-87 | Health route docstring states no disk or network cost | web_portal/routes/dashboard.py | 9a4f0f5398483b3dac56fdbf084d1ebd1554c300 | present | 49 |
| R-88 | Ready payload holds the status word | web_portal/routes/dashboard.py | 9a4f0f5398483b3dac56fdbf084d1ebd1554c300 | present | 83 |
| R-89 | Smoke test class names the isolated converter fixture | tests/e2e/web_portal/test_portal_smoke.py | 56e87d332700603c9925aa061c4594f864e7ac49 | present | 23 |
| R-90 | Existing navigation test IDs begin at line 105 | tests/e2e/web_portal/test_portal_smoke.py | 56e87d332700603c9925aa061c4594f864e7ac49 | present | 105 |
| R-91 | Werkzeug 3.1.9 is pinned | requirements.txt | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 291 |
| R-92 | Playwright 1.65.2 is pinned | requirements-dev.txt | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 272 |
| R-93 | pytest 9.2.0 is pinned | requirements-dev.txt | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 325 |
| R-94 | Operator guide web portal row | documentation/operator-guide.md | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | present | 215 |

## Sources

Local sources. The repository holds each path below. Remote reads gave the blob and line numbers in the table above.

- `AGENTS.md`, `.github/copilot-instructions.md` (local gates table at lines 50 to 76, Web UI tests at line 301), and `.specify/memory/constitution.md`.
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`. The templates set the section headings of this record.
- The reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv`. Its `plan.md` and `design/research.md` set the depth. Its `spec.md` and `tasks.md` set the shape only. No content was copied.
- `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/` (parent record) and `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/` (full-parity record). The live research table at lines 85 to 124 holds the 40 comparison rows.
- `documentation/operator-guide.md` (web portal row near line 215). `documentation/container-deployment.md` (section "Test and debug containers" at line 141).
- Draft records under `spec-drafts`, local only: `4636/` (state model), `_meta/4636-STATUS.json`, and `_meta/4636-summary.md`. The folders `4647/` and `4649/` hold no files.

GitHub sources. Each read used the `gh` command with read-only arguments:

- Issue #4648: https://github.com/jmorrison-juniper/MistHelper/issues/4648 (open, with no comments on 2026-11-26).
- Issue #4633: https://github.com/jmorrison-juniper/MistHelper/issues/4633 (closed on 2026-11-08). Coordinator decision: https://github.com/jmorrison-juniper/MistHelper/issues/4633#issuecomment-6728769633. Closing comment: https://github.com/jmorrison-juniper/MistHelper/issues/4633#issuecomment-6728770916.
- Parent issue #4224: https://github.com/jmorrison-juniper/MistHelper/issues/4224 (open).
- Program issues #4634 to #4647 and #4649 are open. Issue #4636 is open. Titles came from `gh issue list` on 2026-11-26.
- PR #4596: https://github.com/jmorrison-juniper/MistHelper/pull/4596 (merged on 2026-11-13). It added the full-parity record.
- PR #4208: https://github.com/jmorrison-juniper/MistHelper/pull/4208 (OPEN). Its file list holds `web_portal/app.py` and `web_portal/templates/base.html`.
- PR #4615: https://github.com/jmorrison-juniper/MistHelper/pull/4615 (merged on 2026-11-13 at 06:20:12Z). Its file list holds `web_portal/services/data_browser.py`.
- `gh pr list --search 4648` returned an empty list on 2026-11-26. No PR links to issue #4648.
- Main commit: https://github.com/jmorrison-juniper/MistHelper/commit/f03c6c9b36d612a48d7b9652998c2fd87dd777ca.

No upstream URL was fetched. No Mist API, mistapi, Podman, or Python behavior was checked from outside the repository.

## Skills

No skill was loaded. The listed skills cover containers, Juniper devices, and other products. None covers this Flask portal and Python test scope. This plan starts no container.

## Mist API and SDK

This record makes no Mist REST or WebSocket claim. The converter package has no SDK import (R-07). The OpenAPI file and the installed `mistapi` source were not read, because no claim depends on them.

## Unverified

- The browser module was not run. Playwright and Chromium behavior on Windows, macOS, and Linux is unverified (task T011 and issue question U-5).
- The pytest case counts are planned, not measured. This pass ran no test.
- The installed `pytest-playwright` plugin source was not read. The `page` fixture behavior is inferred from `tests/e2e/web_portal/test_portal_smoke.py` line 14 and line 39.
- The shared CSRF handler answer for `Accept: */*` was read in code only (`services/config.py` lines 333 to 338). It was not run.
- The 308 redirect status for a POST without a trailing slash is expected from Werkzeug 3.1.9 (`requirements.txt` line 291). It was not run.
- Gunicorn with more than one worker was not run. The CSRF behavior across processes is unverified (decision D-9).
- The status text that `converter.js` shows on an error was not read in full. The browser test checks only that status text is present.
- The operator guide row near line 215 was located by search. Its full text was not read. Read it before task T013 edits it.
- `documentation/quality-gates.md`, `documentation/architecture.md`, and `documentation/development-setup.md` were not read in full. The local gates table in `.github/copilot-instructions.md` (R-49, R-50) is the authority that this record uses.
- PR #4208 may close or change its files after 2026-11-26. The handover check in task T001 must repeat the state check.
