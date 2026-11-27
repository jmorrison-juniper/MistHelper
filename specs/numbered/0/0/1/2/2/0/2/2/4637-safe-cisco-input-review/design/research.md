# Research: Safe Cisco Input and Structured Review

This record covers issue 4637 of the Cisco converter program. It keeps decisions consistent with issues 4224, 4596, and 4636, and with the merged PRs 4226 and 4596.

## R1. Scope and sources of truth

Issue 4637 is open. It has labels `feature` and `web-portal`, no comments, and it was created on 2026-11-07. The body gives no reproduction steps and no error text. Its body sets these facts:

- Complete tasks T007 to T010 of the full-parity map in PR #4596.
- Add contract tests for six suffixes, the exact 16 MiB limit, UTF-8, null bytes, traversal, drive paths, symbolic links, upload collisions, and failed-review invalidation.
- Use transient upload storage by default. Keep persistent input under an approved private area.
- Use opaque identifiers. Do not overwrite a file silently.
- Use original synthetic fixtures. Make no live request. Make no cloud call.
- Preserve the offline DNS workflow from PR #4226. Do not register shared portal routes.
- Prerequisite: issue 4636. Parent: issue 4224.

Linked PR facts from GitHub on 2026-11-26:

- PR #4226 is MERGED at 2026-10-26T20:35:38Z. Its title is `feat(web-portal): add isolated offline Cisco DNS converter`. Its body says `Do not merge` and names PR #4208 as the blocker for shared integration.
- PR #4596 is MERGED at 2026-11-13T09:41:52Z. It adds the full-parity task map under `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/`.
- A search for `4637` in pull requests returned no result.
- Issues 4224, 4634 to 4649, and 4636 are open. The issue 4636 record states that issues 4632 and 4633 are closed. This pass did not read issues 4632 or 4633.
- At the time of reading, the spec-drafts folder held a complete draft for 4636 and drafts for 4644 to 4649. Folders for 4638 to 4643 were empty.

Local HEAD equals `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`. The commit API returns that commit with committer date 2026-11-26T07:15:01Z.

## R2. Decision register

Each decision names its alternatives, its reason, and its risk. No decision needs a human owner under section 6 of the brief.

| ID | Decision | Alternatives rejected | Reason | Risk |
| --- | --- | --- | --- | --- |
| D-1 | Keep the six suffixes `.txt`, `.conf`, `.cfg`, `.ios`, `.config`, and `.log`. | Add suffixes. Drop `.log`. | Matches issue 4224 FR-003, PR #4226 code at `models.py` lines 60 to 67, and PR #4596 contract line 75. | `.log` files can hold noise. The review shows unknown lines as unsupported. |
| D-2 | Keep the 16 MiB limit inclusive at 16,777,216 bytes. Keep the 16 KiB multipart allowance. Share one constant. | Limits for each suffix. A larger limit. | PR #4596 contract line 77 sets this policy. The existing boundary test at `test_routes.py` line 125 proves it. | Hosts can drift from the constant. The boundary test guards the value. |
| D-3 | Treat names as display text. Refuse control characters, null characters, path separators, drive colons, UNC prefixes, and parent references. Never use a name as a path. | Refuse Windows device names. Keep the current rules only. | After D-8, the name never reaches the file system. The rule removes the input class that the issue names. | A misleading label can still appear. The UI escapes all text. |
| D-4 | Select a stored input by its 32-character lowercase identifier only. The server finds the file. | Client path. Sequential identifiers. | Client paths allow traversal. Sequential identifiers are guessable. PR #4596 contract line 80 requires opaque identifiers. | None known. |
| D-5 | Create identifiers with `uuid.uuid4().hex`. Do not use a content digest as the key. | SHA-256 content digest as the natural key. | AGENTS prefers natural keys. A digest would let a person test whether a known configuration exists in the folder. | Identical content gets two identifiers. Each save stays explicit. |
| D-6 | Create each stored file with exclusive creation and mode 0600 on POSIX. A collision returns 409 and changes nothing. | Overwrite. Rename with a counter. | PR #4596 contract line 81 forbids silent overwrite. | None known. |
| D-7 | Keep uploads in memory by default. Save only when the browser sends `retain` and the host passes an enabled retention object. The blueprint default has no retention. | Environment variable. Always persist. | A new environment variable needs a `deploy/.env.example` entry and host wiring. PR #4596 contract line 83 requires explicit retention. | Operators can misread the retain checkbox. The UI disables it when retention is off. |
| D-8 | Store no original file names. The catalog reports identifier, suffix, byte count, and UTC modification time. | Sidecar metadata with the original name. | PR #4596 contract line 82 requires safe metadata only. A name can carry identity data. | Operators cannot recognize a file by its name. |
| D-9 | Store stored inputs under `data/cisco_config_converter/input/`. | `test-artifacts/`. A new top-level folder. | `test-artifacts/` holds test evidence only. The constitution data rule names `data/` for product output. | The shared data browser can reach the folder. Decision D-11 blocks production enablement. |
| D-10 | Ignore symbolic links and non-regular entries in the catalog. Resolve every retrieval under the canonical root and refuse a link. Return a safe 400 or 409. | Rely on the operating system only. | PR #4596 contract line 79 requires escape checks after canonical resolution. | Windows has no `O_NOFOLLOW`. The check runs before and after opening. Unresolved item U-3 records the residual race. |
| D-11 | Keep production retention disabled. Enablement waits for a separate exclusion change. | Enable now. Move storage outside `data/`. | `web_portal/services/data_browser.py` lines 138 to 161 serve any allowed file under `data/` except firmware backups. `output_scan.py` lines 84 to 99 do not exclude a converter folder. | Warning: enabling retention before the exclusion change exposes customer configuration. Remediation R-4 files the separate issue. |
| D-12 | Add `GET /inputs` and `POST /observations`. Keep the `/preview`, `/review`, and `/export` response shapes. `/preview` accepts `stored_id` and `retain`. | Add keys to the proposal. Add a version field now. | Adding keys changes the export object and its digest. PR #4596 contract lines 15 to 17 require a version contract for extended proposals, which issue 4641 owns. | A later version contract needs a migration. Issue 4641 owns it. |
| D-13 | Observe eleven display-only families for rows C07 to C17. Convert no setting. | Convert families now. Observe DNS only. | Issues 4638 to 4640 own conversion. PR #4596 task T009 names rows C03 and C07 to C17. | The review may show a family without a conversion. The sections say so. |
| D-14 | Show object names and network values. Omit descriptions, hostnames, locations, contacts, usernames, secrets, communities, keys, and banner text. | Show all values. Omit all values. | PR #4596 research rows C07, C14, and C37 require redacted identity data. Showing nothing gives the review no value. | An operator may need an omitted value. The unsupported section gives the line number. |
| D-15 | Keep the review state unchanged for observation requests. Clear the earlier review before a preview saves anything. | Store observations in the session. | Session storage grows and can go stale. The current test `test_failed_preview_revokes_review` already proves the clear order. | None known. |
| D-16 | Convert `state/intake.py` into the `intake/` package. Keep `conversion.py` DNS-only. Add no child to the converter root. | New root package. Observations inside `conversion.py`. An extra child in `state/`. | The converter root and `state/` already hold five children. Constitution Principle I forbids a sixth child. | This change depends on issue 4636. See unresolved item U-1. |
| D-17 | Put new tests in `tests/integration/web_portal/cisco_config_converter/input/`. Add browser coverage to the existing `tests/e2e/web_portal/test_portal_smoke.py`. | `tests/contract/cisco_config_converter/` from the 4596 map. A new e2e folder. | `tests/contract/` holds 17 children. `tests/e2e/web_portal/` holds 32 children. Issue 4636 decision D-2 chose the integration folder. | The file-level move from the 4596 map needs a note in the pull request. |
| D-18 | Use the standard `logging` module with `%s` templates and `key=value` text in the new modules. | Adopt structlog now. | The converter package uses stdlib logging at `routes.py` line 4 and `conversion.py` line 4. Issue 4636 uses the same form. The upgrade portal uses structlog at `audit/logger.py` lines 12 and 18. | A reviewer may reject the equivalence reading of Principle V. Unresolved item U-2 records that risk. |
| D-19 | Add one fragment named `changelog.d/issue-4637-safe-cisco-input-review.md`. | No fragment. | The changelog rule at `changelog.d/README.md` lines 26 to 28 names the issue form when no pull request exists. The user sees the change. | The fragment name needs no change after the pull request opens. |
| D-20 | Grade each Markdown file of this record with `ste-linter` at a score of 80. | Exclude the record. | `quality-gates.md` lines 277 to 283 and AGENTS section Documentation require the gate for each Markdown file. This also closes issue 4636 item U-8 for this record. | The dictionary run needs a local machine. Unresolved item U-5 covers it. |

## R3. Current behavior on `main`

Each line below cites the blob read at the SHA in R4.

- Suffix allowlist: `models.py` lines 60 to 67.
- Name rule: `models.py` lines 49 to 50. Length 1 to 120 and no character below 32.
- Kind rule: `models.py` lines 51 to 52. Values `standalone` and `spoke` only.
- File-name rule: `models.py` lines 58 to 59. A directory part or a drive colon is refused. A null character is not refused.
- Text rule: `models.py` lines 73 to 80. The limit is 16 MiB. The decode is strict UTF-8. Null characters and empty text are refused.
- Request allowance: `routes.py` line 36 returns 16 MiB plus 16 KiB for the converter path prefix only.
- Upload read: `routes.py` line 124 reads at most 16 MiB plus one byte.
- Memory-only upload: `routes.py` lines 28 and 29.
- Review digest: `models.py` lines 88 to 91. Session values: lines 94 to 112.
- Routes: `routes.py` lines 45 to 65. The routes are `/`, `/preview`, `/review`, and `/export`.
- Host check: `routes.py` lines 103 to 108. Registration fails without `ConverterRequest` or CSRF.
- Logging: `routes.py` line 75 logs before validation. Line 150 logs after a successful action.
- Comments: `routes.py` and `conversion.py` contain no `#` comment. `models.py` contains one at line 46.
- Page and source: `ConverterRoutes.page` (lines 68 to 70) and `ConverterInput.source` (lines 117 to 127) contain no log call.
- DNS conversion: `conversion.py` lines 11 to 34 and 37 to 53. Unsupported items keep line numbers and command categories. Values omit identity data.

## R4. Remote verification table

Each row names a check on `main`. The `ref` column reads `main` for each GitHub check. Blob bodies came from the blob endpoint, with one call for each SHA in the main tree. For `routes.py`, the `contents` endpoint with the literal path returned the same SHA. The mistapi row checks the local `.venv` folder and names no repository path. Result `absent` means the check found no entry.

| Row | Claim | Path | Ref | Blob SHA | Result | Line |
| --- | --- | --- | --- | --- | --- | --- |
| R-01 | AGENTS writing and code rules | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| R-02 | Local gates table | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| R-03 | Nested package guard row in section Add a menu operation | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 230 |
| R-04 | Section Move a module | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 261 |
| R-05 | Principle I Five-Item Rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| R-06 | Principle III Safety-First | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 113 |
| R-07 | Principle V Observability and structured logs | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 182 |
| R-08 | Principle VI Inline Comments | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 204 |
| R-09 | Principle VII Action Logging | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 235 |
| R-10 | Technology section, data directory rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 274 |
| R-11 | Radix route function | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 4 |
| R-12 | Parent five-child guard | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 92 |
| R-13 | Spec template | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 1 |
| R-14 | Plan template | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 1 |
| R-15 | Tasks template | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 1 |
| R-16 | Checklist template | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 1 |
| R-17 | Writing gate section | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 277 |
| R-18 | Browser test section | documentation/development-setup.md | main | 1733975a7e0a0962fe5367e165a21f5831f8c3e5 | present | 262 |
| R-19 | Container account UID 1000 | documentation/container-deployment.md | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 114 |
| R-20 | Operator guide has no converter entry | documentation/operator-guide.md | main | 60d28f9ea461fc8798973d1d1b7e40491c27c248 | absent | 0 |
| R-21 | README has no converter entry | README.md | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | absent | 0 |
| R-22 | Changelog naming rule | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 26 |
| R-23 | Data folder ignored by Git | .gitignore | main | 17eadfadb35a59e191a61c78877569ad747ddcc7 | present | 95 |
| R-24 | Flask pin | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 49 |
| R-25 | Flask-WTF pin | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 54 |
| R-26 | mistapi pin | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| R-27 | structlog transitive pin | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 249 |
| R-28 | Type gate paths | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| R-29 | Dead-code gate paths | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| R-30 | Docstring style paths | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| R-31 | Docstring coverage paths | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| R-32 | Coverage command | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 311 |
| R-33 | Strict browser variable | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 896 |
| R-34 | STE linter configuration | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 1 |
| R-35 | Project configuration | pyproject.toml | main | eca34c826ea44ba4f2faefc07d04c2c117e99751 | present | 1 |
| R-36 | Test quality configuration | .github/test-quality-config.toml | main | d0c88405e03f11e71b1fc8fe9238f14936991da7 | present | 1 |
| R-37 | Test quality baseline | .github/test-quality-baseline.json | main | 512da22b0769e8343a4b5b734c507d6aa3969ac6 | present | 1 |
| R-38 | Main commit read for this record | commit f03c6c9b36d612a48d7b9652998c2fd87dd777ca | main | f03c6c9b36d612a48d7b9652998c2fd87dd777ca | present | 0 |
| R-39 | Pinned mistapi package folder | .venv\Lib\site-packages\mistapi | local | none (local directory) | present | 0 |
| R-40 | Converter package initializer | src/interfaces/portals/cisco_config_converter/__init__.py | main | 5e34b005c2ae54d3f2a766dd8ab0be7ceab40a7e | present | 1 |
| R-41 | DNS converter class | src/interfaces/portals/cisco_config_converter/conversion.py | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 11 |
| R-42 | Conversion imports the models module | src/interfaces/portals/cisco_config_converter/conversion.py | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 6 |
| R-43 | Source read method | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 46 |
| R-44 | File-name rule | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 56 |
| R-45 | Suffix allowlist | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 60 |
| R-46 | Text limit and decode | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 73 |
| R-47 | Review digest | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 88 |
| R-48 | In-memory request class | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 29 |
| R-49 | Request allowance | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 36 |
| R-50 | Route table | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 45 |
| R-51 | Upload read limit | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 124 |
| R-52 | Host check for CSRF and request class | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 107 |
| R-53 | Preview logs before validation | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 75 |
| R-54 | Page controls with test identifiers | src/interfaces/portals/cisco_config_converter/presentation/converter.html | main | 270c3e40e226c026a54aef846f9b341d6a76eee9 | present | 7 |
| R-55 | Reset on input | src/interfaces/portals/cisco_config_converter/presentation/converter.js | main | 9c7ad354600aade5b3a37bbd536ac49486edfd6e | present | 12 |
| R-56 | Exact boundary test | tests/integration/web_portal/cisco_config_converter/test_routes.py | main | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 125 |
| R-57 | Path rejection test | tests/integration/web_portal/cisco_config_converter/test_routes.py | main | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 156 |
| R-58 | Protection test at registration | tests/integration/web_portal/cisco_config_converter/test_routes.py | main | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 180 |
| R-59 | Unit test imports the models module | tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py | main | 31a84e3795665ebea1a9346fd835fffc619a9fe7 | present | 6 |
| R-60 | Isolated browser test class | tests/e2e/web_portal/test_portal_smoke.py | main | 56e87d332700603c9925aa061c4594f864e7ac49 | present | 23 |
| R-61 | Shared app registers the data browser | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | present | 201 |
| R-62 | Shared app has no converter registration | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | absent | 0 |
| R-63 | Shared base template has no converter navigation | web_portal/templates/base.html | main | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | absent | 0 |
| R-64 | Random secret when the variable is unset | web_portal/services/config.py | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 113 |
| R-65 | Portal has no user authentication | web_portal/services/config.py | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 12 |
| R-66 | Data browser resolves allowed files under the data folder | web_portal/services/data_browser.py | main | 247d411105a7af1ed54458418630626182494ffe | present | 147 |
| R-67 | Data browser refuses the firmware backup folder | web_portal/services/data_browser.py | main | 247d411105a7af1ed54458418630626182494ffe | present | 154 |
| R-68 | Output scan has no converter exclusion | web_portal/services/output_scan.py | main | bf97eb8f0e92a51ac2b13b2a5922359321b54bc5 | absent | 84 |
| R-69 | Upgrade portal uses structlog | src/interfaces/portals/upgrade_portal/audit/logger.py | main | f437f4c581001347fad88bad8e4ec2af7dc06a96 | present | 12 |
| R-70 | Nested package guard exists | tests/guardrails/test_nested_package_structure.py | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 1 |
| R-71 | Move module guard exists | tests/guardrails/test_move_module_guidance.py | main | ae163b792b330285dba7a8c32cc957a78c3838d4 | present | 1 |
| R-72 | Process folder guard exists | tests/guardrails/test_process_folder_structure.py | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 1 |
| R-73 | Process folder baseline exists | tests/guardrails/process_folder_baseline.json | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 1 |
| R-74 | Intake module is absent before issue 4636 | src/interfaces/portals/cisco_config_converter/state/intake.py | main | none (no tree entry) | absent | 0 |
| R-75 | Issue 4224 suffix and limit rules | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/spec.md | main | 5e8b1bc162cbfe2e9a3d604420c42e670dd0cd97 | present | 62 |
| R-76 | Issue 4224 portal input rules | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/contracts/portal.md | main | 774b487ab32ae1417368ba79930e7eac0b3dad43 | present | 14 |
| R-77 | Full-parity task T007 | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 44 |
| R-78 | Full-parity task T008 | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 45 |
| R-79 | Full-parity task T009 | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 46 |
| R-80 | Full-parity task T010 | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 47 |
| R-81 | Full-parity dependency rows | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 131 |
| R-82 | Full-parity input and persistence rules | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/portal.md | main | 56e3b23b9ac04e4a733c62970811ca0ead4df83c | present | 73 |
| R-83 | Full-parity portal states the shared app has no converter registration | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/portal.md | main | 56e3b23b9ac04e4a733c62970811ca0ead4df83c | present | 22 |
| R-84 | Full-parity comparison row C07 | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md | main | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 91 |
| R-85 | Full-parity comparison row C37 | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md | main | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 121 |
| R-86 | Full-parity requirements FR-001 to FR-004 | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md | main | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 107 |
| R-87 | Full-parity edge case for the exact limit | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md | main | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 93 |
| R-88 | Reference record folder for shape | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv | main | 00922155516e4f21e34a0bf75613fae7ab481193 | present | 1 |
| R-89 | Issue 4636 record folder is absent from main | specs/numbered/0/0/1/2/2/0/2/1/4636-converter-package-state-model | main | none (no tree entry) | absent | 0 |
| R-90 | Issue 4637 record folder is absent from main | specs/numbered/0/0/1/2/2/0/2/2/4637-safe-cisco-input-review | main | none (no tree entry) | absent | 0 |
| R-91 | No legacy 4637 record exists under specs | specs/**/4637-* | main | none (no tree entry) | absent | 0 |
| R-92 | PR 4226 unit test folder is absent from main | tests/unit/gateway/overrides | main | none (no tree entry) | absent | 0 |
| R-93 | Python 3.15 requirement | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 18 |

Count check: the table holds 93 rows. The STATUS file lists the same 93 checks in the same order.

## R5. Local-only evidence

These checks read the local working tree. They support a claim only when the blob SHA matches a row in R4.

- `git hash-object` on the local files matches the remote blob SHA for `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, `documentation/quality-gates.md`, `documentation/architecture.md`, `documentation/development-setup.md`, `documentation/container-deployment.md`, `documentation/operator-guide.md`, the four templates, `.github/workflows/ci.yml`, and `requirements.txt`. The `AGENTS.md` value also matches.
- The `.venv` folder holds `Lib\site-packages\mistapi` and `Lib\site-packages\flask`. Row R-39 uses that check.
- The local search for `structlog` found matches in `src/foundation` and in the upgrade portal. The upgrade portal match is confirmed remotely in row R-69. The other matches are not used in this record.

## R6. Directory capacity on `main`

Counts come from the main tree on 2026-11-26.

| Directory | Children | Limit | Use in this change |
| --- | --- | --- | --- |
| `src/interfaces/portals/cisco_config_converter/` | 5: `__init__.py`, `conversion.py`, `models.py`, `presentation/`, `routes.py` | 5 | Issue 4636 replaces `models.py` with `state/`. No child is added. |
| `src/interfaces/portals/cisco_config_converter/presentation/` | 2: `converter.html`, `converter.js` | 5 | Both files change. |
| `src/interfaces/portals/` | 6 | 5 | Not touched. Over limit. |
| `tests/integration/web_portal/cisco_config_converter/` | 2: `__init__.py`, `test_routes.py` | 5 | Adds `input/`. Issue 4636 adds `state/`. |
| `tests/unit/marvis/mist/resources/gateway/overrides/` | 5 | 5 | One import line changes. No child is added. |
| `tests/e2e/web_portal/` | 32 | 5 | One existing file gains functions. No child is added. |
| `tests/contract/` | 17 | 5 | Not used. |
| `web_portal/` | 7 | 5 | Not touched. |
| `input/` under the former source root | 0, absent | 5 | Not used. |

## R7. Shared portal exposure of stored inputs

- `web_portal/app.py` registers the shared data browser at line 201. The function `_register_blueprints` starts at line 182.
- `data_browser.py` lists the top-level entries of the data folder at lines 49 to 61. The listing includes directories at lines 172 to 180.
- `data_browser.py` resolves a request path under the data folder at lines 138 to 161. It refuses only the firmware backup folder at lines 154 to 156.
- An allowed extension is required at lines 164 to 168. The contents of `ALLOWED_EXTENSIONS` were not read. See R12.
- `output_scan.py` excludes named folders at lines 84 to 99. A converter folder is not named there.

This evidence supports decision D-11. Production retention stays disabled until a separate change excludes the converter folder from both services.

## R8. Logging form

- Constitution Principle V at line 182 requires structured logs through `structlog` or an equivalent form.
- The converter package uses stdlib logging. The import is on `routes.py` line 4 and `conversion.py` line 4.
- The upgrade portal uses `structlog` at `audit/logger.py` lines 12 and 18.
- Issue 4636 uses stdlib logging with `key=value` text. Its record marks that form as unresolved item U-2.

Decision D-18 keeps the stdlib form for consistency with the converter package and with issue 4636. The choice has a risk. The reviewer decides whether the form is equivalent. Adopting `structlog` in both records is the alternative.

## R9. Sources

- Local draft records: `spec-drafts\4636\` (plan, tasks, analysis, state-store contract, spec), and the STATUS and summary files for 4636, 4644 to 4649.
- Remote GitHub reads: `gh issue view` for 4637 and for issues 4224, 4634 to 4649, and 4636. `gh pr list` and `gh pr view` for PRs 4226 and 4596 and for the open PR overlap check. `gh api` for the main tree, blob reads, and the commit API.
- Local read-only Git: `git rev-parse HEAD`, `git log -1`, and `git hash-object`.
- Web sources: none. No behavior claim relies on an external page. No `web_fetch` call ran.

## R10. Skills

No skill was loaded. No listed skill covers Flask upload handling, Cisco configuration observations, or this converter. The container skills cover container work, and this record starts no container.

## R11. Open pull request overlap

Seven pull requests were open when the check ran.

- PR #4208 touches `web_portal/app.py`, `web_portal/templates/base.html`, and `changelog.d/pr-4208.md`.
- PR #4813 touches `changelog.d/issue-4776-csv-carriage-returns.md`.
- The other five open pull requests touch no file in the set of this change.

This change touches none of the files that PR #4208 owns. Its changelog name differs from PR #4813.

## R12. Unverified

These items stay unverified in this pass. Each one needs a later check or an owner answer.

- The contents of `ALLOWED_EXTENSIONS` in `web_portal/services/data_browser.py`. The line range was not read.
- The blueprint file that exposes the data browser preview route. Its authentication state was not read.
- Whether Flask-WTF stores its extension under `app.extensions["csrf"]` at run time. The local `.venv` source was not read, and no test ran.
- Whether Windows allows symbolic-link creation in the test environment. The tests use a documented fallback. They never skip.
- The sixty remote checks in issue 4636 were not repeated.
- The Python platform fact that `os.O_NOFOLLOW` is absent on Windows. No external source was fetched.
