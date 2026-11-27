# Research: Gated Converter Apply and Reconciliation

## Questions

1. Does `main` hold an apply path for the converter? Answer: No. Rows 1 to 3 in the remote table show no apply route.
2. Which Mist operations back the apply families? Answer: Eight write operations and five read operations exist in the OpenAPI file and in the pinned SDK. Rows 41 to 64.
3. What does the pinned SDK do on failure? Answer: It retries HTTP 429 for every method. It sets no timeout on writes. It returns the response for 4xx and 5xx statuses. Rows 65 to 70.
4. Which gateway template fields are verified? Answer: `name`, `type`, and optional `dns_servers`. Rows 6 and 37.
5. Can the executor fit inside the five-item rule? Answer: Yes, after amendment X-1 moves two state modules under `state/records/`. See `plan.md`, Structure Decision.
6. Which sibling drafts conflict with this record? Answer: Issues 4646, 4647, and 4648. See `analysis.md`, Findings F-08 to F-11.

## Sources

Remote sources are read from `main` at commit `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, retrieved on 2026-11-26. Local SDK sources are read from the pinned environment. Blob SHA values for SDK files come from a local SHA-1 computation over the git blob format.

- `AGENTS.md`, sections Writing style (line 40), Code quality (line 73), Tests (line 133), Secrets (line 172). Remote row 24 cites line 48.
- `.github/copilot-instructions.md`, sections Local gates (line 50), Spec Kit layout (line 159), Structural directories (line 167), SDK compatibility (line 254), Safety (line 309). Remote rows 22 and 23.
- `.specify/memory/constitution.md`, Principle I (line 38), Principle III (line 113), Principle VII (line 235), Technology constraints (line 279), Operational Store (line 315). Remote rows 15, 20, and 21.
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, and `checklist-template.md`. The headings in this record follow those templates.
- `.specify/scripts/powershell/spec-route.ps1`, lines 7 and 17. Remote row 25.
- `documentation/quality-gates.md`, section The writing gate (line 277). Remote row 40.
- `documentation/container-deployment.md`, section Test and debug containers (line 141). Read only. No container starts in this record.
- `documentation/architecture.md`, `development-setup.md`, and `operator-guide.md`. Read the section headings. No decision in this record depends on them.
- `documentation/mist-api-openapi31yaml.yaml`, operation lines in rows 41 to 53. The JSON twin `documentation/mist-api-openapi31json.json` names the same operation IDs.
- Parent record `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/contracts/mist-apply.md`, lines 5, 11, 13, and 20. Remote rows 36 and 37.
- Full-parity record `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/`. Remote rows 26 to 35.
- Reference record `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/`. Read for the shape. No content is copied.
- Sibling drafts in `files/spec-drafts/`: `4636` (state model, complete), `4645` to `4649` (partial drafts). The drafts are local only. They are not on `main`.
- Pinned SDK `.venv\Lib\site-packages\mistapi\` version 0.64.1. Rows 54 to 71.
- GitHub issues and pull requests, read with `gh` on 2026-11-26. Issues 4224, 4632 to 4649 (states and titles). Issue 4633 closing comments. PR #4208 (open), PR #4596 (merged 2026-11-13), and PR #4615 (merged 2026-11-13).
- Live Mist MCP tools were not called. The brief requires local sources for each Mist claim. This record needs no live Mist data.
- No web source was fetched. No local skill was loaded. Podman, storage, networking, and Juniper device behavior are outside this change.

## Findings Summary

- The converter currently exposes preview, review, and export. Approval lives in the Flask session and covers export only (rows 1 to 5).
- The parent contract verifies three gateway template fields only (rows 36 and 37). The converter's `GatewayTemplate` type declares the same three fields (row 6).
- All eight apply families exist in the pinned SDK 0.64.1 (rows 54 to 64) and in the OpenAPI file (rows 41 to 53).
- The SDK wraps every request in one retry loop. The loop repeats HTTP 429 for writes (rows 65 and 66). The write calls pass no timeout (rows 67 and 68).
- No route registers the converter in the web portal (row 8). The apply route cannot run in production until the integration change lands.

## Decisions

Human decisions are marked `true`. A decision marked `false` is a decision this record makes.

| ID | Decision | Alternatives considered | Reason and risk | Human |
| --- | --- | --- | --- | --- |
| D-1 | Register eight families, F-01 to F-08. Exclude delete, unassign, restore, inventory assignment, and device update. | All 21 candidate operations. Gateway templates only. | Parent C22 maps to templates, profiles, site settings, and proposed sites. Excluded families map to issues 4645 and 4646, or they lack field evidence. Risk: device assignment stays partial. | false |
| D-2 | Each allow-list holds only verified fields. F-04 starts with `name`, `type`, and `dns_servers`. Other lists start empty. | Forward the converter output. Build allow-lists from the OpenAPI file alone. | Parent `mist-apply.md` verifies only the three gateway template fields (rows 36 and 37). Risk: converter fields have no apply path until issue 4634 adds evidence. | false |
| D-3 | Each family starts disabled in `MistWriteAdapter.FAMILIES`. No environment variable controls enablement. | Environment variable. Runtime setting in the portal. | A code constant needs a reviewed change, and no deploy file changes. Risk: a reviewed code change can enable a family. The gate G5 review covers it. | false |
| D-4 | One approval per operation. The typed word is `APPLY`, exact and case-sensitive. The approval lasts 15 minutes, allows one use, and binds the operator and both digests. | Case-insensitive word. Checkbox. Client-chosen identifier. | Parent FR-016 names the exact word (row 34). Issue 4636 D-6 and D-7 set the lifetime and the use. The Flask-session approval covers export only (row 5). | false |
| D-5 | Refuse every approval and write without a verified operator identity. | Accept the browser user name. Use the Flask session as identity. | No identity provider exists on `main`. A browser value is not verified. Risk: no write runs until this decision closes. | true |
| D-6 | Preflight each object before the first write. Re-read each object before its own write. Stop on any digest mismatch. | Check once before the run. Use the lock alone. | Parent FR-017 and FR-018 need both checks. Risk: Mist offers no compare-and-set (residual risk R-1). | false |
| D-7 | Never retry a write in executor code. Count the SDK's internal HTTP 429 retries as one attempt. A final 429 is indeterminate. | Executor retry with backoff. Disable the SDK retry. | An unknown outcome needs reconciliation first. Disabling the SDK retry needs a shim or an owned transport, which the constitution limits. Risk: a create repeats after a 429. Test TST-14 counts the attempts. | false |
| D-8 | Bound each write wait at 90 seconds and each run at 10 minutes. A missed bound is indeterminate, and no new write starts. | No bound. Patch the SDK session. | The SDK sets no timeout on write calls (rows 67 and 68). The 90-second bound exceeds the SDK's total 429 sleep of about 35 seconds, based on the default delay (row 65 and `__api_request.py` line 201). Risk: a late write completes after the bound. Reconciliation reads it. | false |
| D-9 | Map HTTP 400, 401, 403, and 404 to failed. Map a final 429, a 5xx status, a timeout, a connection loss, a proxy error, a malformed success, and a missing ID to indeterminate. | Map every 4xx and 5xx to failed. | The parent contract lists 400, 401, 403, 404, and 429 as documented responses (row 72). No documented response covers 5xx. Risk: a 4xx can still change state. The read-back covers it. | false |
| D-10 | Reconcile each partial or indeterminate outcome with read-only lookups before any new approval. | Trust the write response. | A write response can differ from the stored object. Risk: more read calls. | false |
| D-11 | Build each write body from the current object and the approved fields. Send the complete body. Compare the read-back digest. | Send only the changed fields. | The Mist PUT semantics are unverified (U-1). The complete body preserves unrelated fields under either semantics. Risk: a larger request. | false |
| D-12 | A create needs a natural ID in the response or in a read. A missing ID is indeterminate. A name collision refuses the create. | Match by name after a create. | Name matching can select the wrong object. The parent research requires natural IDs. Risk: a read adds one call. | false |
| D-13 | Cancel voids the approval under the approval lock and keeps the operation in `reviewed`. | Delete the approval. Keep it unused. | Deletion removes evidence. An unused approval can still run. Risk: the operator must create a new approval after cancel. | false |
| D-14 | Place the executor in `state/execution.py`. Move records into `state/records/` under amendment X-1. Add the gates to existing modules. Add the route as `ConverterInput.apply_action`. | A new package. A new route class. The executor inside `routes.py`. | Each new package breaks the five-item rule at `state/` or at the converter root. A route class adds a top-level name to `routes.py`. Risk: issue 4636 must apply X-1 first. | false |
| D-15 | Put the apply tests in `tests/integration/web_portal/cisco_config_converter/apply/`, not in `tests/contract/`. | The parent T021 path. | `tests/contract/` holds 17 children (row 12). Issue 4636 D-2 makes the same choice. | false |
| D-16 | Assign file owners. This record owns the executor, the gates, the adapter, and `apply_action`. Issue 4647 owns the browser controls. Issue 4646 owns restore and reuses the reconciliation here. Issue 4648 owns the shared portal integration. | One combined owner. | Each file has one owner and one change, which keeps the hot-file rule. Risk: this record waits on issue 4647 for the browser controls. | false |
| D-17 | No family is enabled by this record. Enabling a family needs G2 evidence, G4 approval, G5 evidence, and a human decision. | Enable by default. Enable per environment. | The issue forbids a production operation. Enablement can change a production organization. Risk: a later release date. | true |
| D-18 | The approval seal uses `PORTAL_SECRET_KEY` through issue 4636. The apply path refuses every write when the key is empty. | Use the Flask session key. Generate a random key. | Issue 4636 D-5 and D-15 set the key use. A random key, as `web_portal/services/config.py` line 113 creates, makes approvals unreadable after restart (row 9). | true |
| D-19 | Tests use a recording SDK double at the method boundary. No live request runs. No credential appears in a test. | Live sandbox tests. | The issue forbids live credentials in tests. Risk: the double can differ from Mist. Gate G2 evidence covers the field shapes. | false |
| D-20 | Each action logs an info line before and a debug line after. The log holds the operation ID, family ID, object ID, and outcome. The log never holds a payload value or a secret. | Log payloads for debugging. | Constitution Principles III, V, and VII require these rules (rows 15 and 21). Risk: less detail during an incident. The operation record keeps the detail. | false |
| D-21 | Write the apply path independently. Reuse no external source expression or asset. Release waits for gate G1. | Reuse external converter code. | The coordinator decision on issue 4633 bars reuse. Issue 4635 remains open. Risk: a longer implementation. | false |

## Remote Verification

Result labels: `present`, `absent`, `partial`, or `stale`. A line of 0 means that the check covers existence only. Rows 54 to 71 use the local `.venv` path and the label `local-venv`. A blob value of `not-a-blob` marks a directory or a missing path.

| # | Claim | Path | Ref | Blob SHA | Result | Line |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | ConverterRoutes registers the root, preview, review, and export rules | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 61 |
| 2 | No apply route exists in the converter routes | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | absent | 0 |
| 3 | ConverterInput.action binds review and export | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 130 |
| 4 | ConverterRoutes holds five methods | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 45 |
| 5 | ReviewState writes the approval to the Flask session | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 112 |
| 6 | GatewayTemplate holds name, type, and optional dns_servers | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 13 |
| 7 | IOSDnsConverter.convert builds the proposal | src/interfaces/portals/cisco_config_converter/conversion.py | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 15 |
| 8 | The web portal app registers no converter blueprint | web_portal/app.py | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | absent | 0 |
| 9 | The portal secret falls back to a random UUID4 value | web_portal/services/config.py | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 113 |
| 10 | The integration route test imports the routes module | tests/integration/web_portal/cisco_config_converter/test_routes.py | main | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 15 |
| 11 | The unit converter test imports the models module | tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py | main | 31a84e3795665ebea1a9346fd835fffc619a9fe7 | present | 6 |
| 12 | tests/contract holds 17 direct children | tests/contract | main | not-a-blob | present | 0 |
| 13 | tests/contract/cisco_config_converter does not exist | tests/contract/cisco_config_converter | main | not-a-blob | absent | 0 |
| 14 | The nested package guard sets MAX_CHILDREN to 5 | tests/guardrails/test_nested_package_structure.py | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 17 |
| 15 | Constitution Principle I limits each level to five children | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 40 |
| 16 | Firmware ownership uses a non-blocking exclusive flock | web_portal/routes/firmware_policy/jobs/ownership/__init__.py | main | 0cc40a4942129a1c08f5c68d2013e5ee974bb863 | present | 39 |
| 17 | The shipped container runs one Gunicorn worker | container/scripts/start.sh | main | 3b138807883a8a8785bac7d8c9b7f9a79458ed0c | present | 225 |
| 18 | The data directory is git-ignored | .gitignore | main | 17eadfadb35a59e191a61c78877569ad747ddcc7 | present | 95 |
| 19 | requirements.txt pins mistapi 0.64.1 | requirements.txt | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| 20 | The constitution names mistapi 0.59 or newer | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | stale | 279 |
| 21 | The constitution requires a verified durable write before success | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 319 |
| 22 | The local gates table names the Tests gate | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| 23 | The SDK compatibility gate rejects forwarded arguments | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 254 |
| 24 | The writing rule limits an instruction to 20 words | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 48 |
| 25 | The spec route uses base 5 | .specify/scripts/powershell/spec-route.ps1 | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 17 |
| 26 | Parent task T021 names the tests/contract apply path | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 76 |
| 27 | Parent task T022 names models.py as the implementation file | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | stale | 77 |
| 28 | Parent keeps live apply prohibited without owner approval | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 80 |
| 29 | Parent plan defines gate G2 for API evidence | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/plan.md | main | 97960674f86e6c7c2e40f9b51cef5272e194a66f | present | 126 |
| 30 | Parent plan defines gate G4 for cloud owner approval | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/plan.md | main | 97960674f86e6c7c2e40f9b51cef5272e194a66f | present | 128 |
| 31 | Parent plan defines gate G5 for operator evidence | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/plan.md | main | 97960674f86e6c7c2e40f9b51cef5272e194a66f | present | 129 |
| 32 | Parent cloud contract keeps each write row blocked | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 49 |
| 33 | Parent cloud contract keeps G2 and G4 closed | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 163 |
| 34 | Parent FR-016 requires exact typed APPLY | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md | main | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 122 |
| 35 | Parent research maps C24 to duplicates, stale state, 429, timeout, and unknown results | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md | main | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 108 |
| 36 | Parent apply contract defers cloud apply | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/contracts/mist-apply.md | main | fbb549f8077f9d73773e7ca1ff8c5d3a3878615d | present | 20 |
| 37 | Parent apply contract verifies the gateway template fields | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/contracts/mist-apply.md | main | fbb549f8077f9d73773e7ca1ff8c5d3a3878615d | present | 11 |
| 38 | Record 4636 is absent from main | specs/numbered/0/0/1/2/2/0/2/1/4636-converter-package-state-model | main | not-a-blob | absent | 0 |
| 39 | The route folder for record 4644 is absent | specs/numbered/0/0/1/2/2/0/3/4/4644-gated-converter-apply-reconcile | main | not-a-blob | absent | 0 |
| 40 | The writing gate section exists | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 277 |
| 41 | The OpenAPI file defines createOrgGatewayTemplate | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 9764 |
| 42 | The OpenAPI file defines updateOrgGatewayTemplate | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 9951 |
| 43 | The OpenAPI file defines getOrgGatewayTemplate | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 9929 |
| 44 | The OpenAPI file defines createOrgDeviceProfile | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 7988 |
| 45 | The OpenAPI file defines updateOrgDeviceProfile | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 8187 |
| 46 | The OpenAPI file defines assignOrgDeviceProfile | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 8370 |
| 47 | The OpenAPI file defines getOrgDeviceProfile | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 8164 |
| 48 | The OpenAPI file defines createOrgSite | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 20047 |
| 49 | The OpenAPI file defines listOrgSites | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 20022 |
| 50 | The OpenAPI file defines updateSiteInfo | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 26004 |
| 51 | The OpenAPI file defines getSiteInfo | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 25978 |
| 52 | The OpenAPI file defines updateSiteSettings | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 37086 |
| 53 | The OpenAPI file defines getSiteSetting | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 37065 |
| 54 | The SDK defines updateSiteSettings | .venv\Lib\site-packages\mistapi\api\v1\sites\setting.py | local-venv | eee049fe9c5b77edb2facf6ad076594740571a18 | present | 42 |
| 55 | The SDK defines getSiteSetting | .venv\Lib\site-packages\mistapi\api\v1\sites\setting.py | local-venv | eee049fe9c5b77edb2facf6ad076594740571a18 | present | 17 |
| 56 | The SDK defines updateSiteInfo | .venv\Lib\site-packages\mistapi\api\v1\sites\sites.py | local-venv | 3b110ec432906c3b9ef438712816a3faf960817a | present | 67 |
| 57 | The SDK defines getSiteInfo | .venv\Lib\site-packages\mistapi\api\v1\sites\sites.py | local-venv | 3b110ec432906c3b9ef438712816a3faf960817a | present | 17 |
| 58 | The SDK defines createOrgGatewayTemplate | .venv\Lib\site-packages\mistapi\api\v1\orgs\gatewaytemplates.py | local-venv | 6b82963804738f1a6a85af80dab4b3c7d9b67735 | present | 58 |
| 59 | The SDK defines updateOrgGatewayTemplate | .venv\Lib\site-packages\mistapi\api\v1\orgs\gatewaytemplates.py | local-venv | 6b82963804738f1a6a85af80dab4b3c7d9b67735 | present | 145 |
| 60 | The SDK defines createOrgDeviceProfile | .venv\Lib\site-packages\mistapi\api\v1\orgs\deviceprofiles.py | local-venv | b603220c8e11b8c64b523b4c9e683d3408eff299 | present | 63 |
| 61 | The SDK defines updateOrgDeviceProfile | .venv\Lib\site-packages\mistapi\api\v1\orgs\deviceprofiles.py | local-venv | b603220c8e11b8c64b523b4c9e683d3408eff299 | present | 150 |
| 62 | The SDK defines assignOrgDeviceProfile | .venv\Lib\site-packages\mistapi\api\v1\orgs\deviceprofiles.py | local-venv | b603220c8e11b8c64b523b4c9e683d3408eff299 | present | 182 |
| 63 | The SDK defines createOrgSite | .venv\Lib\site-packages\mistapi\api\v1\orgs\sites.py | local-venv | b33331fbb12f81106e79799e9b5d0486c218b47c | present | 58 |
| 64 | The SDK defines listOrgSites | .venv\Lib\site-packages\mistapi\api\v1\orgs\sites.py | local-venv | b33331fbb12f81106e79799e9b5d0486c218b47c | present | 17 |
| 65 | The SDK retry constant allows three HTTP 429 retries | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 59 |
| 66 | The SDK retries HTTP 429 for every method | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 229 |
| 67 | The SDK PUT call passes no timeout | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 324 |
| 68 | The SDK POST call passes no timeout | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 300 |
| 69 | A SDK connection error stops without a retry | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 225 |
| 70 | The SDK APIResponse carries the response and the proxy flag | .venv\Lib\site-packages\mistapi\__api_request.py | local-venv | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 258 |
| 71 | The local environment holds mistapi 0.64.1 | .venv\Lib\site-packages\mistapi-0.64.1.dist-info | local-venv | not-a-blob | present | 0 |
| 72 | The parent apply contract lists the documented responses 200, 400, 401, 403, 404, and 429 | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/contracts/mist-apply.md | main | fbb549f8077f9d73773e7ca1ff8c5d3a3878615d | present | 13 |

The table holds 72 rows. The count matches `remote_checks` in `META_DIR\4644-STATUS.json`.

## Unverified

- U-1: The Mist PUT semantics for omitted fields are unverified. The OpenAPI operations give one-line descriptions only (rows 42 and 52). Decision D-11 covers the risk. Reason: no live test is allowed.
- U-2: Mist does not document whether a write that returns HTTP 429 was processed. The parent contract declares the status without detail (row 72). Decision D-7 covers the risk.
- U-3: The OpenAPI file documents no 5xx response for the families in scope. Decision D-9 maps every 5xx to indeterminate. Reason: the status meaning is unknown.
- U-4: The response of each create operation may or may not include the new `id` field. This record did not inspect each response schema. Decision D-12 requires a read when the ID is missing.
- U-5: The existing credential service returns an mistapi session that the adapter can use. Parent task T020 assumes it. No file cited in this table verifies it.
- U-6: Mist may process a request after the SDK client stops waiting. Decision D-8 and the reconciliation step cover the risk.
