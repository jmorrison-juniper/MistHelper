# Research: Compliant Converter Package and State Model

## R1. Issue facts

Issue 4636 is open. Its title is "[Spec]: Define compliant converter package and state model". It carries the labels `feature` and `web-portal`.

- Problem: The parity plan needs a compliant package layout and private state contracts before feature behavior. The change must not alter portal behavior.
- Scope: Complete tasks T004 and T006 from the full-parity task map. Inventory the package capacity first. Then define source, review, proposal, approval, operation, and backup types with tests.
- Constraints: Use the existing application and service boundaries. Add no separate database, no Compose stack, and no compatibility shim. The 15-minute review lifetime stays a proposed default.
- Security: Keep credentials and source configuration out of logs, browser storage, and fixtures. Grant no production authorization.
- Acceptance: Record the capacity and compliant paths. Test the state transitions. Record the identity design or keep cloud work blocked. Verify restart and multiworker behavior. Do not claim cloud-write authorization.
- Comments: The coordinator denied cloud-write enablement on 2026-11-08. A later comment on 2026-11-09 states that main at `3964d21` already holds five root children and five model classes. The 2026-11-09 capacity comment names two candidate layouts and states that neither is approved.

Current `main` is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, dated 2026-11-26. The comments cite `3964d21`. The root count and the model class count are the same on the current commit (R4, rows 3 and 4).

Source: `https://github.com/jmorrison-juniper/MistHelper/issues/4636`

## R2. Linked and referenced PRs

A search of PRs for the text `4636` returned no result. The referenced PRs below carry the program history.

| PR | State | Merged or updated | Relevance |
| --- | --- | --- | --- |
| #4596 | MERGED | 2026-11-13 | Full-parity spec record and task map. Source of T004 and T006. |
| #4358 | MERGED | 2026-11-13 | Moved the converter unit test to `tests/unit/marvis/mist/resources/gateway/overrides/`. |
| #4226 | MERGED | 2026-10-26 | Added the isolated offline DNS converter. |
| #4208 | OPEN | Open at the time of this record | Owns `web_portal/app.py` and `web_portal/templates/base.html`. |

Open PR scan: seven open PRs. The only file overlap with the converter files is PR #4208 on the two shared portal files. This change edits neither file.

Sources: `https://github.com/jmorrison-juniper/MistHelper/pull/4596`, `https://github.com/jmorrison-juniper/MistHelper/pull/4358`, `https://github.com/jmorrison-juniper/MistHelper/pull/4226`, `https://github.com/jmorrison-juniper/MistHelper/pull/4208`

## R3. Existing record

No folder whose name starts with `4636-` exists under `specs/` on the local checkout. The route `specs/numbered/0/0/1/2/2/0/2/1` has no record yet. This record creates the folder `4636-converter-package-state-model` under that route.

Route check: 4636 equals `122021` in base 5. Padded to eight levels, the route is `0/0/1/2/2/0/2/1`. The reference record for issue 4920 follows the same rule with route `0/0/1/2/4/1/4/0`.

## R4. Remote verification table

All checks read GitHub `main` through `gh api` on 2026-11-26. Each blob SHA matches the local `HEAD` tree. Line numbers come from the decoded remote content, or from the identical local blob.

| # | Claim | Path | Ref | Blob SHA | Result | Line |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | The converter package holds five direct children, counting `__init__.py` and `presentation/` | `src/interfaces/portals/cisco_config_converter` | main | directory listing | present, count 5 | not applicable |
| 2 | Package docstring | `src/interfaces/portals/cisco_config_converter/__init__.py` | main | 5e34b005c2ae54d3f2a766dd8ab0be7ceab40a7e | present | 1 |
| 3 | `models.py` declares five top-level classes | `src/interfaces/portals/cisco_config_converter/models.py` | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 13, 21, 29, 38, 84 |
| 4 | `models.py` holds one `#` comment and no logger call | `src/interfaces/portals/cisco_config_converter/models.py` | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | local count, same blob |
| 5 | The source kind accepts only `standalone` and `spoke` | `src/interfaces/portals/cisco_config_converter/models.py` | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 51 |
| 6 | `conversion.py` imports from `models.py` | `src/interfaces/portals/cisco_config_converter/conversion.py` | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 6 |
| 7 | `routes.py` imports from `models.py` | `src/interfaces/portals/cisco_config_converter/routes.py` | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 12 |
| 8 | Blueprint template folder and URL prefix | `src/interfaces/portals/cisco_config_converter/routes.py` | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 54, 55 |
| 9 | `routes.py` holds three classes and no `#` comment | `src/interfaces/portals/cisco_config_converter/routes.py` | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 17, 45, 99 |
| 10 | Presentation page and script exist | `src/interfaces/portals/cisco_config_converter/presentation/converter.html` and `converter.js` | main | 270c3e40e226c026a54aef846f9b341d6a76eee9 and 9c7ad354600aade5b3a37bbd536ac49486edfd6e | present | not applicable |
| 11 | Converter integration package init | `tests/integration/web_portal/cisco_config_converter/__init__.py` | main | 43a141c1406a21b339a111b3791274aa3eee784d | present | not applicable |
| 12 | Route tests import the routes module | `tests/integration/web_portal/cisco_config_converter/test_routes.py` | main | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 15 |
| 13 | Route test for review invalidation | `tests/integration/web_portal/cisco_config_converter/test_routes.py` | main | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 80 |
| 14 | Unit test imports `SourceConfiguration` from `models.py` | `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py` | main | 31a84e3795665ebea1a9346fd835fffc619a9fe7 | present | 6 |
| 15 | Unit test expects `hub` to be refused | `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py` | main | 31a84e3795665ebea1a9346fd835fffc619a9fe7 | present | 39 |
| 16 | Old unit test path | `tests/unit/gateway/overrides/test_cisco_config_converter.py` | main | not applicable | absent | not applicable |
| 17 | Portal secret falls back to a random value | `web_portal/services/config.py` | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 113 |
| 18 | Portal application has no converter text | `web_portal/app.py` | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | absent | not applicable |
| 19 | Base template has no converter text | `web_portal/templates/base.html` | main | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | absent | not applicable |
| 20 | Portal has no user authentication | `deploy/.env.example` | main | 7137364423308485be734a391798d85c6a37eaf4 | present | 155 |
| 21 | Firmware ownership lock classes | `web_portal/routes/firmware_policy/jobs/ownership/__init__.py` | main | 0cc40a4942129a1c08f5c68d2013e5ee974bb863 | present | 23, 45, 108 |
| 22 | Firmware ownership uses a private `.workers` directory | `web_portal/routes/firmware_policy/jobs/ownership/__init__.py` | main | 0cc40a4942129a1c08f5c68d2013e5ee974bb863 | present | 114 |
| 23 | Native lock calls | `web_portal/routes/firmware_policy/jobs/ownership/__init__.py` | main | 0cc40a4942129a1c08f5c68d2013e5ee974bb863 | present | 35, 39, 64, 68 |
| 24 | Backup access helper class | `src/operations/execution/firmware_policy/recovery/backup.py` | main | 8ff5ba1da19a407e2041b018ae8e7a1cd90039c7 | present | 86 |
| 25 | Nested package guard constant | `tests/guardrails/test_nested_package_structure.py` | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 17 |
| 26 | Nested package guard functions | `tests/guardrails/test_nested_package_structure.py` | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 89, 106, 117 |
| 27 | Nested package baseline file | `tests/guardrails/nested_package_baseline.json` | main | 0d6c5ca933d83a4721c0bcc7220f69905fcf81f5 | present | not applicable |
| 28 | Git ignores the data directory | `.gitignore` | main | 17eadfadb35a59e191a61c78877569ad747ddcc7 | present | 95 |
| 29 | Shipped container runs one worker | `container/scripts/start.sh` | main | 3b138807883a8a8785bac7d8c9b7f9a79458ed0c | present | 225, 324 |
| 30 | Local web entry point runs one worker with four threads | `wsgi.py` | main | e8b2be7cb33c54266afcd5723293b7487df4d365 | present | 4 |
| 31 | Constitution Five-Item Rule | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38, 40 |
| 32 | Constitution operational store clause | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 315 |
| 33 | Local gates table and move rules | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50, 261 |
| 34 | Python version rule | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 20 |
| 35 | Managed roots and route rule | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 159, 161 |
| 36 | Five-children rule for structural directories | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 167, 168 |
| 37 | Nested source package gate row | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 259 |
| 38 | Inline comment rule | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 97 |
| 39 | Action logging rule | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 104 |
| 40 | STE rule for Markdown files | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 340 |
| 41 | Quality gates document exists | `documentation/quality-gates.md` | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | not applicable |
| 42 | OpenAPI defines `createOrgGatewayTemplate` | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 9764 |
| 43 | OpenAPI defines `updateOrgGatewayTemplate` | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 9951 |
| 44 | OpenAPI defines `updateSiteSettings` | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 37086 |
| 45 | OpenAPI has no idempotency text | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | absent | case-insensitive search returned 0 hits |
| 46 | Container runs as UID 1000 | `documentation/container-deployment.md` | main | f06228bc6bbe77cc009f956403872a06462466ea | present | 114 |
| 47 | Portal secret documented as auto-generated | `documentation/wiki/Web-Portal.md` | main | e9dac116b73e6284b46cb6220ec0ca75228fe90c | present | 282 |
| 48 | Per-worker random key risk documented | `specs/1823-upgrade-capture-portal/research/web-portal.md` | main | 92aeea695e5cee3a4a01d569b1db0e0e8318471f | present | 224 |
| 49 | Open question on mandatory portal secret for Labs | `specs/numbered/0/0/1/2/1/0/0/4/4504-dynamic-jvd-labs-planning/analysis.md` | main | f48c9a96067f0298927fb33ebc058cb2d196f328 | present | 28 |
| 50 | Full-parity task map defines T004 and T006 | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md` | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 31, 36 |
| 51 | Full-parity T006 proposes a test path under `tests/contract` | same tasks file | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 36 |
| 52 | Full-parity FR-005 requires Branch, Hub, and Standalone | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md` | main | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 111 |
| 53 | Full-parity plan names the old unit test folder | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/plan.md` | main | 97960674f86e6c7c2e40f9b51cef5272e194a66f | present | 84 |
| 54 | Full-parity plan requires one compliant layout before code | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/plan.md` | main | 97960674f86e6c7c2e40f9b51cef5272e194a66f | present | 79, 80 |
| 55 | Full-parity data model transition section | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/data-model.md` | main | afb08dab16578918a56d4a4cb95ddee998d99883 | present | 43, 45, 50 |
| 56 | Full-parity analysis forbids automatic purge | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/analysis.md` | main | a08601943e89b95af5ebe9530c0d8b9bb47459ab | present | 83 |
| 57 | Full-parity cloud contract lists 21 candidate writes | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md` | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 45, 49 |
| 58 | Full-parity portal contract says the secret falls back to a random value | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/portal.md` | main | 56e3b23b9ac04e4a733c62970811ca0ead4df83c | present | 34 |
| 59 | Parent record cites Python 3.13 | `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/plan.md` | main | 9c3fdacc929850e1ed923b248f1dc6520aa01fdd | present | 15 |
| 60 | Parent record cites the old unit test folder | same parent plan | main | 9c3fdacc929850e1ed923b248f1dc6520aa01fdd | present | 93 |

Row 4 counts comments with a local search of the same blob. Row 9 counts routes without a `#` comment. Row 45 searched the file with a case-insensitive pattern.

Counts that remain unchanged since the issue comments: the converter root has five children, and `models.py` has five classes (rows 1 and 3).

## R5. Converter source facts

- `models.py` declares `GatewayTemplate`, `UnsupportedItem`, `ConversionProposal`, `SourceConfiguration`, and `ReviewState`. These are the five top-level classes (row 3).
- `SourceConfiguration.read` validates the file name, the template name, the kind, and the text. The text limit is 16 MiB (row 3, in the same blob).
- `ReviewState` stores one proposal digest and one reviewed digest in the Flask session. Its digest uses `json.dumps` with sorted keys, compact separators, and `allow_nan=False`.
- `routes.py` builds a blueprint with the URL prefix `/cisco-config-converter` and the template folder `presentation` (rows 8 and 9).
- The route tests mount the blueprint in an isolated Flask app. They block socket connections and file opens during the offline journey.
- `conversion.py` converts only global IPv4 `ip name-server` lines. Every other line becomes an unsupported item.

## R6. Five-item capacity

| Directory | Count | Source |
| --- | --- | --- |
| `src/interfaces/portals/` | 6 physical, 5 guard | Directory listing (row 1 method) |
| `src/interfaces/portals/cisco_config_converter/` | 5 physical, 3 guard | Directory listing and guard functions (rows 1 and 26) |
| `tests/contract/` | 17 | Directory listing |
| `tests/contract/web_portal/` | 1 | Directory listing |
| `tests/integration/web_portal/` | 4 | Directory listing |
| `tests/integration/web_portal/cisco_config_converter/` | 2 | Directory listing |
| `tests/e2e/` | 5 | Directory listing |
| `tests/e2e/web_portal/` | 32 | Directory listing |
| `tests/unit/marvis/mist/resources/gateway/overrides/` | 5 | Directory listing |

The guard counts direct Python modules except `__init__.py`, plus directories with tracked Python files (rows 25 and 26). The constitution counts every child (row 31, line 40). The two measures differ for `src/interfaces/portals/cisco_config_converter`, which has three guard children and five physical children.

## R7. Persistence and secret facts

- `web_portal/services/config.py` line 113 reads `PORTAL_SECRET_KEY`. If the variable is absent, the code uses `str(uuid.uuid4())`. Each process then receives a different key (row 17).
- The 1823 record states that each worker picks a different key when the variable is absent (row 48).
- The Web Portal wiki documents the variable as auto-generated (row 47).
- Record 4504 lists the same question as an open decision, D-09 (row 49).
- The shipped container runs one worker (row 29). The local entry point runs one worker with four threads (row 30). Restart, not multiworker operation, is the live risk today.
- Firmware job ownership writes a private `.workers` directory and uses native locks (rows 21 to 23). This is the closest precedent in the repository.
- `.gitignore` ignores `data/` (row 28).

## R8. Operator identity facts

- `deploy/.env.example` line 155 states that the portal has no user authentication. The allowlist is the only access control (row 20).
- The full-parity portal contract states that an IP allowlist does not identify an operator (full-parity `design/contracts/portal.md`, row 58).
- The coordinator decision on issue 4636 denies cloud-write enablement until per-operator identity exists.
- No identity provider appears in the portal code on `main`. The search for converter text in `web_portal/app.py` and `base.html` returned no match (rows 18 and 19).

## R9. Restart and multiworker facts

- Session-bound review state is lost on restart when the secret is random (rows 17 and 48).
- Two worker processes with random secrets reject each other's sessions. The shipped container avoids this today by running one worker (row 29).
- The state package must survive a restart and a second process. The store therefore writes files under `data/` and uses native locks (decision D-3).
- Lock semantics: `msvcrt.locking` on Windows and `fcntl.flock` on POSIX (row 23).

## R10. Mist cloud facts

- The full-parity cloud contract inventories 21 candidate write operations. Each row stays blocked until payload, response, permission, and recovery evidence passes (row 57, lines 45 and 49).
- The local OpenAPI YAML defines `createOrgGatewayTemplate` at line 9764, `updateOrgGatewayTemplate` at line 9951, and `updateSiteSettings` at line 37086 (rows 42 to 44). The file has no idempotency text (row 45).
- The installed `mistapi` version is 0.64.1. The file `.venv/Lib/site-packages/mistapi-0.64.1.dist-info` names that version. The pin in `.github/copilot-instructions.md`, section Language and environment, matches it.
- The installed SDK defines `updateSiteSettings` at `.venv/Lib/site-packages/mistapi/api/v1/sites/setting.py` line 42. This file is local, outside the repository. Its evidence is local only.
- This change calls no Mist method. The claims above support the blocked status only.

## R11. Test layout facts

- The existing converter tests live in `tests/integration/web_portal/cisco_config_converter/` (row 11, row 12) and in `tests/unit/marvis/mist/resources/gateway/overrides/` (row 14).
- `tests/contract/` already holds 17 children (R6). The full-parity task map puts test modules under `tests/contract/cisco_config_converter/`, which adds a child to that noncompliant parent (row 51).
- Issue 4633 requires dedicated tests under the feature-owned test roots (issue 4633, coordinator decision). The integration converter folder is one of those roots.

## R12. Gates and tooling facts

- The local gates table in `.github/copilot-instructions.md` begins at line 50 (row 33).
- The table lists 20 gate rows, from compile to the ops platform check.
- The table names `MYPY_PATHS`, `VULTURE_PATHS`, `PYDOCSTYLE_PATHS`, and `INTERROGATE_PATHS` as values in `.github/workflows/ci.yml`. This record did not read that workflow. The values are unverified (U-12).
- The symbol gate uses `symbol-diff --base <base> <file>`. The table states that the gate expects `no module-level name changed`. A removed module needs a recorded exception.

## R13. Skills

No local skill was loaded. The issue concerns Python package layout and offline state. Podman, storage, networking, and Juniper device skills do not apply to this record.

## R14. Mist write inventory and approval gates

The full-parity record defines five approval gates. They apply to every cloud write.

- G1: Legal review for reuse and distribution.
- G2: API field evidence for each mapping and write.
- G3: Integration-owner handover for shared files.
- G4: Cloud-owner approval of operation families, scope, and recovery policy.
- G5: Operator confirmation for each write.

This record satisfies none of the five gates. It keeps every cloud write blocked.

## Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk. Decisions D-10, D-14, and D-15 need a human owner.

### D-1. Replace `models.py` with the `state/` package

- Alternatives:
  - Add the six new types to `models.py`. Rejected. The module would hold 11 top-level classes, which breaks the five-item limit.
  - Add `state/` as a sixth child of the converter root. Rejected. The root already holds five children.
  - Move `routes.py` and `conversion.py` into a `workflow/` package. Rejected. The blueprint module name changes, and the template and static paths need rework.
  - Create a sibling package under `src/interfaces/portals/`. Rejected. The parent already holds six children.
- Chosen: Replace `models.py` with `state/`. Keep `conversion.py` and `routes.py` in place.
- Reason: The root stays at five children. Blueprint paths do not change. Three import lines change, and no shim remains.
- Risk: The symbol gate reports the removed module. The symbol map in `plan.md` and the pull request body document the move.
- Human decision: No.

### D-2. Place the state tests under the converter integration folder

- Alternatives:
  - Use `tests/contract/cisco_config_converter/`. Rejected. It adds a child to `tests/contract/`, which already holds 17 children.
  - Use `tests/contract/web_portal/cisco_config_converter/`. Rejected. The `web_portal` contract root is shared, and issue 4633 requires feature-owned roots.
  - Use `tests/integration/web_portal/cisco_config_converter/state/`. Chosen.
- Reason: The folder is feature-owned. The new folder holds five children, and the parent holds three.
- Risk: The tests are classed as integration tests. The module docstrings state that they cover records, transitions, the store, and processes.
- Human decision: No.

### D-3. Use a private file store under `data/` with native locks

- Alternatives:
  - Create a new SQLite file. Rejected. The coordinator states that no separate database is allowed.
  - Add tables to `data/mist_data.db`. Rejected. The issue forbids schema changes without approval.
  - Use ArangoDB or Redis collections. Rejected. No operational store is declared, and the change needs Compose and schema approval.
  - Keep state in memory. Rejected. Records would not survive a restart.
  - Store state in browser storage. Rejected. The data model prohibits it.
- Chosen: A private file store under `data/cisco_config_converter/state/`, with native locks. Production writes stay disabled until owner approval (gate G4).
- Reason: No new service is needed. The repository already uses this pattern for firmware job ownership (R7).
- Risk: The store serves one host only. Windows directory permissions cannot match POSIX mode `0o700` (U-5).
- Human decision: No. The production gate follows the existing G4 approval.

### D-4. Use two digests and one seal

- Alternatives:
  - Use one digest over the full proposal. Rejected. The digest would no longer equal the existing `ReviewState` digest.
  - Use digest only, without a seal. Rejected. A changed file on disk would go undetected.
  - Use the Flask session to store records. Rejected. Browser-held private data is prohibited.
  - Use a separate key file. Rejected. It adds a second secret source.
- Chosen:
  - The legacy `proposal_digest` keeps the existing canonical form.
  - The `scope_digest` covers the version, the source, the target references, the contract versions, and the legacy digest.
  - Each stored record carries an HMAC-SHA256 seal with a key derived from `PORTAL_SECRET_KEY`.
- Reason: Existing review digests keep their values. Target changes change the scope digest and invalidate an approval.
- Risk: A rotated secret makes every sealed record unreadable. This behavior is intended and fails closed.
- Human decision: No.

### D-5. Refuse writes when the secret is missing

- Alternatives:
  - Change the shared fallback to stop the portal at start. Rejected. Shared behavior needs gate G3 and the integration owner.
  - Keep the random fallback. Rejected. Records would fail after a restart.
  - Store a generated key beside the records. Rejected. The key would sit with the data it protects.
- Chosen: The store refuses writes and reads when `PORTAL_SECRET_KEY` is empty. The shared fallback stays unchanged.
- Reason: The converter fails closed without a shared behavior change.
- Risk: Operators see refusals until they set the variable. The quickstart names the variable.
- Human decision: No. The shared policy is decision D-15.

### D-6. Use a 15-minute lifetime with inclusive expiry

- Alternatives: 5 minutes, 30 minutes, 60 minutes, or the browser session lifetime.
- Chosen: 15 minutes, as the issue proposes. `REVIEW_LIFETIME` in `state/intake.py` holds the single value. Approvals use the same value.
- Reason: The value matches the issue. The owner can approve another value by changing one constant.
- Risk: A short lifetime can frustrate reviewers. The expired message names the cause.
- Human decision: No.

### D-7. Make each approval one use

- Alternatives:
  - Allow reuse within the lifetime. Rejected. A reused approval can repeat a write.
  - Use revocation without consumption. Rejected. The approval has no one-use guarantee.
  - Bind the approval to the browser session. Rejected. The session has no operator identity and does not persist.
- Chosen: Each approval binds one operator, one proposal digest, one scope digest, and one expiry. The store consumes it under the approval lock.
- Reason: The one-use rule stops a second write from one approval.
- Risk: A crash after consumption and before the write leaves an approval consumed without an executed operation. The operation phase and reconciliation (issue 4644) handle that case.
- Human decision: No.

### D-8. Mark unknown write outcomes as indeterminate

- Alternatives:
  - Retry with an idempotency key. Rejected. The local OpenAPI file has no idempotency text (row 45).
  - Mark the write as failed. Rejected. The failure hides the ambiguity.
  - Mark the write as successful after a timeout. Rejected. The result may be false.
- Chosen: The phase `indeterminate` blocks execution until read-only reconciliation and a fresh approval.
- Reason: The write may have happened. A retry could repeat it.
- Risk: The operator waits for reconciliation. Issue 4644 owns that work.
- Human decision: No.

### D-9. Delete no record in this change

- Alternatives:
  - Purge expired reviews and approvals after 24 hours. Rejected. The full-parity analysis states that no automatic purge is approved (row 56).
  - Keep records with no policy. Rejected. The policy must exist before production.
- Chosen: Keep every record. A later owner-approved task adds any purge, with typed confirmation.
- Reason: No destruction occurs without approval.
- Risk: Disk use grows. Each record is small. The G4 review reviews the growth.
- Human decision: No. No destructive action is taken.

### D-10. Refuse write-capable approvals without a verified operator

- Alternatives:
  - Use the IP allowlist. Rejected. `deploy/.env.example` line 155 says the allowlist is not user authentication (row 20).
  - Use the shared Mist credential. Rejected. It identifies no operator.
  - Use the browser session. Rejected. It identifies no operator.
  - Select an identity provider now. Rejected. The coordinator requires deployment options and owner requirements first.
- Chosen: The approval refuses every operator that is not verified. Tests use synthetic verified identities only.
- Reason: No cloud write can proceed without a verified operator.
- Risk: No live cloud write can be tested. The restriction is intended.
- Human decision: HUMAN-DECISION-REQUIRED. The identity and authorization design is credential policy. The owner must approve it before any cloud write (U-9).

### D-11. Keep the role values `standalone` and `spoke`

- Alternatives:
  - Change the values to `Branch`, `Hub`, and `Standalone` now. Rejected. The current route tests and clients use the existing values.
  - Add an alias map. Rejected. The compatibility shim is prohibited.
  - Keep both vocabularies. Rejected. Two terms would name one concept.
- Chosen: Keep the existing values until tasks T011 and T012 change the contract in one change.
- Reason: The current behavior stays unchanged.
- Risk: Two vocabularies coexist until T012. The data model names both.
- Human decision: No.

### D-12. Extend the transition table with five groups of edges

- Alternatives:
  - Use only the documented edges. Rejected. The data model states rules for input change, target change, and failed recovery that no edge covers.
  - Allow any transition with guards only. Rejected. The test would prove less.
- Chosen: The documented edges plus the edges in `design/data-model.md`, section Added edges.
- Reason: Each added edge names its rule.
- Risk: An added edge can be wrong. Each edge has a test.
- Human decision: No.

### D-13. Keep routes, shared files, and cloud calls out of scope

- Alternatives:
  - Register the blueprint in the shared portal now. Rejected. PR #4208 owns the shared files, and issue 4633 requires a separate integration PR.
  - Add the store to the routes now. Rejected. Production writes are disabled, and gate G4 is open.
- Chosen: No route, no shared file, and no Mist call in this change.
- Reason: The scope matches the coordinator decision.
- Risk: The store is not reachable from the portal until a later task. That is intended.
- Human decision: No.

### D-14. Allow independent authorship only

- Alternatives:
  - Reuse source expression after a legal review. Deferred to issue 4635.
  - Reuse source expression now. Rejected. No legal decision exists.
- Chosen: Independent authorship only. No source expression is reused until a legal decision exists.
- Reason: The issue constraints forbid copying. Issue 4635 holds the legal decision.
- Risk: Legal review delays reuse. This record needs no reuse.
- Human decision: HUMAN-DECISION-REQUIRED. Licensing and reuse are legal decisions.

### D-15. Keep the shared secret fallback until the owner decides

- Alternatives:
  - Require `PORTAL_SECRET_KEY` across the whole portal now. Rejected. Shared behavior needs gate G3 and the integration owner.
  - Keep the random fallback for the whole portal. Rejected for the converter. It remains possible for other features.
  - Decide in this record. Rejected. Credential policy belongs to the owner.
- Chosen: The shared fallback stays unchanged. The owner decides whether the whole portal must require the variable. Record 4504 decision D-09 asks the same question for Labs.
- Reason: The converter guards itself, and the shared behavior stays unchanged.
- Risk: Other features keep random keys after a restart until the owner decides.
- Human decision: HUMAN-DECISION-REQUIRED. The question is credential policy.

## Sources

Local repository files are read from the checkout at `C:\Users\jmorrison\OneDrive - Hewlett Packard Enterprise\Code\MistHelper`. Each file matches its remote blob SHA in R4.

- Repository rules: `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md`, `.specify/templates/spec-template.md`, `.specify/templates/plan-template.md`, `.specify/templates/tasks-template.md`, `.specify/templates/checklist-template.md`.
- Reference record: `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/`.
- Full-parity record: `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/`.
- Parent record: `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/`.
- Converter code: `src/interfaces/portals/cisco_config_converter/`.
- Converter tests: `tests/integration/web_portal/cisco_config_converter/` and `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py`.
- Portal and deployment: `web_portal/services/config.py`, `web_portal/routes/firmware_policy/jobs/ownership/__init__.py`, `deploy/.env.example`, `container/scripts/start.sh`, `wsgi.py`, `.gitignore`, `documentation/container-deployment.md`, `documentation/wiki/Web-Portal.md`.
- Mist API: `documentation/mist-api-openapi31yaml.yaml`. Installed SDK: `.venv/Lib/site-packages/mistapi/api/v1/sites/setting.py`.
- Issues: `https://github.com/jmorrison-juniper/MistHelper/issues/4636`, `https://github.com/jmorrison-juniper/MistHelper/issues/4224`, `https://github.com/jmorrison-juniper/MistHelper/issues/4632`, `https://github.com/jmorrison-juniper/MistHelper/issues/4633`, `https://github.com/jmorrison-juniper/MistHelper/issues/4634`, `https://github.com/jmorrison-juniper/MistHelper/issues/4635`, `https://github.com/jmorrison-juniper/MistHelper/issues/4641`, `https://github.com/jmorrison-juniper/MistHelper/issues/4643`, `https://github.com/jmorrison-juniper/MistHelper/issues/4644`.
- Pull requests: `https://github.com/jmorrison-juniper/MistHelper/pull/4596`, `https://github.com/jmorrison-juniper/MistHelper/pull/4358`, `https://github.com/jmorrison-juniper/MistHelper/pull/4226`, `https://github.com/jmorrison-juniper/MistHelper/pull/4208`.

## Unverified

- U-1: The Windows native lock under contention was not executed.
- U-2: The constitution asks for structlog or an equivalent. The owner must confirm that stdlib key=value logs meet that rule.
- U-3: The constitution names a declared operational store. No document on `main` declares one. The grep found only the constitution.
- U-4: The existing data backup procedure may cover `data/cisco_config_converter/state/`. `documentation/backup-restoration.md` exists, but this record did not read it in full.
- U-5: Directory permissions on Windows and macOS cannot match POSIX mode `0o700`. The owner must confirm the host ACL.
- U-6: The symbol gate output for a removed module was not executed.
- U-7: Runtime and flake rate of the two-process tests on CI were not measured.
- U-8: Whether `ste-linter` accepts the new record files was not checked. The gate lists only specific Markdown files.
- U-9: Identity provider options were not researched. The coordinator decision defers that work.
- U-10: The legal status of reuse under CC BY-NC 4.0 is open under issue 4635.
- U-11: Whether any deployment sets `PORTAL_SECRET_KEY` today was not checked. No deployment data was read.
- U-12: The values of `MYPY_PATHS`, `VULTURE_PATHS`, `PYDOCSTYLE_PATHS`, and `INTERROGATE_PATHS` were not read from `.github/workflows/ci.yml`.
- U-13: The installed mistapi source is local to `.venv` and outside the repository. The remote evidence for the SDK call is absent.
