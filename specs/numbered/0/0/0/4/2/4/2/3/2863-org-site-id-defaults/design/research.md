# Research: Organization and site identifier defaults

**Main revision checked**: `f03c6c9b36d612a48d7b9652998c2fd87dd777ca` (GitHub `main`, read with `gh api`). The local checkout has the same HEAD. Four governance files have the same blob hash locally and on main.

**Interpretation rule**: A claim that code exists needs a path, a ref, a blob SHA, and a line. A claim about an absent path uses the value `absent-in-main-tree` and line 0. A folder row uses the tree SHA and line 0.

## Decisions

**D-1. Scope of this record**
- Decision: Plan five batches. Implement batch 1 now. Keep issue #2863 open.
- Alternatives: (a) One pull request for all 110 occurrences. (b) A ratchet guard only. (c) Batch 1 only, with no later plan.
- Chosen: The five-batch plan.
- Reason: The owner limits the claim to one bounded repair (2026-10-01). Destructive paths need human review. The counts cannot be reproduced (Unverified).
- Risk: The audit runs for several batches.
- Recommended option: The five-batch plan.
- Human decision: No.

**D-2. Refusal contract**
- Decision: Raise `ValueError` with a fixed message. Write one error log record that names the field. Never return an empty result for a refusal.
- Alternatives: (a) Return an empty list. This hides the missing input. (b) Return a sentinel value. This needs caller changes. (c) Add `ValueError` to the existing handlers. This turns the refusal into an empty result.
- Chosen: Raise and log.
- Reason: FR-005 and FR-006. The legacy record reached the same result (legacy research, "Decisions").
- Risk: Callers must handle an exception. Only service ping discovery calls the class (RC-31 to RC-34).
- Recommended option: Raise and log.
- Human decision: No.

**D-3. Optional site identifier**
- Decision: `None` selects organization-only scope. An empty, whitespace-only, or non-string value causes a refusal before any SDK call.
- Alternatives: (a) Treat an empty value as `None`. This masks the missing input. (b) Keep `if site_id:` at `tenant_fetch.py:156` and `:180`. This is the current behavior and masks the input. (c) Refuse only empty strings. This leaves non-string values open.
- Chosen: Refuse every value that is not `None` and not a non-blank string.
- Reason: Owner decision of 2026-10-21. FR-003 and FR-004.
- Risk: A caller that sends an empty string now receives an error. Service ping discovery sends `None` only when no site applies (RC-31).
- Recommended option: Refuse every invalid value.
- Human decision: No.

**D-4. Format of valid identifiers**
- Decision: Accept any non-blank string unchanged. Add no UUID check.
- Alternatives: (a) Check the UUID format. The OpenAPI file declares `format: uuid` (RC-20, RC-21). This rejects the opaque test values such as `org-1` (RC-35). (b) Trim the value before use. This changes the value sent to the cloud.
- Chosen: Accept opaque values unchanged.
- Reason: Owner decision of 2026-10-21. FR-007.
- Risk: A malformed but non-blank identifier reaches the SDK. The cloud can return an HTTP error, and the existing HTTP contract returns an empty result (FR-009). This residual risk stays in the record.
- Recommended option: Accept opaque values unchanged.
- Human decision: No.

**D-5. Validator location**
- Decision: Add `TenantIdentifierValidator` and `TenantNameCollector` inside `src/mist/access/api/tenant_fetch.py`.
- Alternatives: (a) A new module such as `src/mist/access/api/tenant_identifiers.py`. This adds a child to a noncompliant folder (RC-10, RC-36). (b) `ValidationUtils.validate_site_id` (RC-54). It accepts non-string values and does not check the organization identifier. (c) A new folder under `src/foundation/`. This widens the change to another folder.
- Chosen: The existing module.
- Reason: The constitution forbids a new direct child in a noncompliant folder (RC-10). The change replaces two helper functions with two classes.
- Risk: The module keeps its existing debt (plan, Complexity Tracking).
- Recommended option: The existing module.
- Human decision: No.

**D-6. Test location**
- Decision: Add `tests/unit/api/test_tenant_identifier_validation.py`.
- Alternatives: (a) Add tests to `test_api_tenant_fetch.py`. This changes an existing file, which SC-006 forbids (RC-35). (b) Omit the test file. This leaves FR-001 to FR-011 without a test.
- Chosen: The new file in `tests/unit/api/`.
- Reason: `tests/unit/api/` holds four children (RC-37). One file makes five, which the constitution allows.
- Risk: The folder reaches its limit. Later API tests need a nested folder.
- Recommended option: The new file.
- Human decision: No.

**D-7. Pull request wording**
- Decision: Batch 1 uses `Part of #2863`. Only the batch that completes the audit uses `Closes #2863`.
- Alternatives: (a) `Closes #2863` in every batch. This closes the open audit. (b) `Refs #2863`. The repository accepts this form, but the owner wrote `Part of`.
- Chosen: `Part of #2863` for batch 1.
- Reason: Owner comments of 2026-10-01 ("A future pull request will state Part of #2863") and 2026-10-21 ("Keep #2863 open").
- Risk: The orchestrator template asks for `Closes`. The orchestrator confirms the wording at T-PR (analysis A26).
- Recommended option: `Part of #2863`.
- Human decision: No.

**D-8. Batch order**
- Decision: Run five batches in this order. Batch 1 covers the tenant boundary. Batch 2 covers the ratchet after remediation. Batch 3 covers menu 145. Batch 4 covers menus 158, 161, and 162. Batch 5 covers menu 239 and needs a new specification.
- Alternatives: (a) Guard first. This is blocked by folder placement (D-14). (b) SSID first, as the 2026-10-06 comment suggests. The comment misnumbers the menu (RC-58). (c) Upgrade portal first. This path is destructive and its manifest is stale.
- Chosen: The order above.
- Reason: The owner approved batch 1, and batch 1 has a preserved implementation.
- Risk: The guard starts late.
- Recommended option: The order above.
- Human decision: No.

**D-9. Count source**
- Decision: The implementation batch reruns the scan at its revision and records its own count. This record uses no earlier count as a target.
- Alternatives: (a) Use 102 from PR #2864. (b) Use 110 from the 2026-10-06 comment. (c) Use 145 from PR #3035 or 76 from PR #3098. (d) Run a scan in this record. Rule 2 forbids execution.
- Chosen: A new count at the implementation revision.
- Reason: The counts use different rules and revisions (Unverified).
- Risk: The new count differs from every earlier count.
- Recommended option: A new count.
- Human decision: No.

**D-10. Masking-default rule**
- Decision: The rule counts three forms in tracked non-test Python files. Form one: a `.get` call with an identifier key and an empty default. Form two: a `str(` wrapper around such a call. Form three: an expression followed by `or ""`. Fixtures prove each form.
- Alternatives: (a) A text search. It gives false positives in comments and strings. (b) Only form one. It misses `MistHelper.py:3615` (RC-75).
- Chosen: All three forms.
- Reason: RC-65, RC-68, RC-73, and RC-75 show all three forms in production code.
- Risk: The rule can overcount. Each occurrence needs a Class A or Class B label.
- Recommended option: All three forms.
- Human decision: No.

**D-11. Human review for destructive batches**
- Decision: Keep `needs-human-review` on the issue. Batches 4 and 5 never carry the `auto-merge` label. A human removes the label after review.
- Alternatives: (a) Enable auto-merge for every batch. This breaks AGENTS.md. (b) Remove the label now. This breaks the owner hold.
- Chosen: Keep the label and the rule.
- Reason: `AGENTS.md:230-231` and the owner comment of 2026-10-30.
- Risk: Merges wait for a human.
- Recommended option: Keep the label and the rule.
- Human decision: No. The rule is an existing repository rule.

**D-12. Reservation update**
- Decision: Post a new reservation comment with the current paths before any source edit. The new comment replaces `api/tenant_fetch.py` (retired src root), the folder `specs/2863-tenant-identifier-slice/`, and `websocket/service_ping_discovery.py` (retired src root).
- Alternatives: (a) Keep the old reservation. Its paths do not exist (RC-28, RC-48, RC-51). (b) Skip the reservation. This breaks `AGENTS.md:246-247`.
- Chosen: A new reservation.
- Reason: RC-04 and RC-28.
- Risk: None known.
- Recommended option: A new reservation.
- Human decision: No.

**D-13. Python version**
- Decision: Validate with Python 3.15.2 through the repository bootstrap.
- Alternatives: (a) Python 3.13. The legacy record used it (RC-52). The repository requires 3.15 (RC-06, RC-11).
- Chosen: Python 3.15.2.
- Reason: The constitution requires Python 3.15 or newer.
- Risk: Environment setup takes longer.
- Recommended option: Python 3.15.2.
- Human decision: No.

**D-14. Guard placement**
- Decision: The guard test and its baseline do not enter `tests/guardrails/` or `.github/`. Batch 2 starts after a remediation issue creates a compliant folder. The orchestrator opens that issue.
- Alternatives: (a) Add the guard to `tests/guardrails/`. This adds a child to a folder that holds 79 children (RC-38). (b) Add the guard to an unrelated nested folder, such as `tests/guardrails/e2e_timeout_budget/`. The topic does not match, so maintainers cannot find the guard. (c) Add the guard to `tests/unit/api/`. Batch 1 uses its last slot (D-6). (d) Add the baseline to `.github/`. That folder holds 14 children (RC-39).
- Chosen: Remediation first, then batch 2.
- Reason: `.specify/memory/constitution.md:42-43` forbids a new direct child in a noncompliant folder.
- Risk: The guard starts later.
- Recommended option: Remediation first.
- Human decision: No.

## Remote Verification

Columns: ID, claim, path, ref, blob SHA (tree SHA for folders and commits), result, line. Result values follow the brief: present, absent, partial, or stale.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
|----|-------|------|-----|----------|--------|------|
| RC-01 | Writing style rules bind this record | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| RC-02 | Branch name uses type, issue, and slug | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 194 |
| RC-03 | No auto-merge label on destructive pull requests | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 230 |
| RC-04 | Declare the file set before editing | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 246 |
| RC-05 | Preserve unmerged work before closing a pull request | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 271 |
| RC-06 | Python 3.15 or newer is required | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 20 |
| RC-07 | Destructive category lists 154-187, 239, and 305-306 | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 221 |
| RC-08 | Changelog fragment naming rule | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| RC-09 | Five-item rule for each hierarchy level | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RC-10 | No direct child in a noncompliant parent | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 43 |
| RC-11 | Python 3.15 or newer is required | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 278 |
| RC-12 | Required labels include type and scope sets | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 487 |
| RC-13 | Mypy paths for the type gate | .github/workflows/ci.yml | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| RC-14 | Hypothesis is a development dependency | requirements-dev.txt | main | 9a528bfe03a10f7bc903f5768ef26de765bbff43 | present | 116 |
| RC-15 | Blind-handler guard scanner class is the pattern to copy | tests/guardrails/test_blind_exception_handler_ratchet.py | main | 3cab97e42178b7b978bcc78eab73d8a0fb3eae27 | present | 50 |
| RC-16 | Blind-handler baseline has a schema version field | .github/blind-exception-handler-baseline.json | main | f3a2ee54395a205b422bcbdb0bea9d489a06d951 | present | 2 |
| RC-17 | Inventory default section heading holds 2749 rows | specs/1924-failure-evidence/inventory.md | main | 9d5724dbdf6811d9458e60937e7afcb8d9d28e36 | present | 2623 |
| RC-18 | Organization networks path | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 15118 |
| RC-19 | Site derived networks path | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 35430 |
| RC-20 | Organization identifier path parameter is required and uses UUID format | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 59899 |
| RC-21 | Site identifier path parameter is required and uses UUID format | documentation/mist-api-openapi31yaml.yaml | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 60286 |
| RC-22 | Tenant fetch class at the current module path | src/mist/access/api/tenant_fetch.py | main | ba7e74141e32b6d0a4d4edfbeeff618290a9641f | present | 52 |
| RC-23 | Organization resolver value reaches the network list call without a check | src/mist/access/api/tenant_fetch.py | main | ba7e74141e32b6d0a4d4edfbeeff618290a9641f | present | 78 |
| RC-24 | Handled exception tuple for tenant discovery | src/mist/access/api/tenant_fetch.py | main | ba7e74141e32b6d0a4d4edfbeeff618290a9641f | present | 103 |
| RC-25 | Site identifier reaches the derived network call without a check | src/mist/access/api/tenant_fetch.py | main | ba7e74141e32b6d0a4d4edfbeeff618290a9641f | present | 118 |
| RC-26 | A falsy optional site selects organization-only policy scope | src/mist/access/api/tenant_fetch.py | main | ba7e74141e32b6d0a4d4edfbeeff618290a9641f | present | 156 |
| RC-27 | A falsy optional site selects organization-only template scope | src/mist/access/api/tenant_fetch.py | main | ba7e74141e32b6d0a4d4edfbeeff618290a9641f | present | 180 |
| RC-28 | Reserved module path api/tenant_fetch.py exists (retired src root) | api/tenant_fetch.py (retired src root) | main | absent-in-main-tree | absent | 0 |
| RC-29 | Reserved test path exists before batch 1 | tests/unit/api/test_tenant_identifier_validation.py | main | absent-in-main-tree | absent | 0 |
| RC-30 | Reserved changelog fragment exists before batch 1 | changelog.d/issue-2863-tenant-identifier-validation.md | main | absent-in-main-tree | absent | 0 |
| RC-31 | Discovery skips site tenants when the site identifier is None | src/mist/realtime/websocket/service_ping_discovery.py | main | 5bc92f63a0045c0b19b776461cef143305433744 | present | 69 |
| RC-32 | Discovery passes a possibly empty policy site identifier | src/mist/realtime/websocket/service_ping_discovery.py | main | 5bc92f63a0045c0b19b776461cef143305433744 | present | 76 |
| RC-33 | Manager collects tenants before the prompts | src/mist/realtime/websocket/service_ping_manager.py | main | 3d4b4b27bcc724f162085d976ce0af6179f88035 | present | 423 |
| RC-34 | Manager prints a workflow error | src/mist/realtime/websocket/service_ping_manager.py | main | 3d4b4b27bcc724f162085d976ce0af6179f88035 | present | 467 |
| RC-35 | Existing tests use valid opaque identifiers | tests/unit/marvis/standalone/mist/access/api/test_api_tenant_fetch.py | main | 37b3029288c1f78f14bd08def7a812151811011a | present | 409 |
| RC-36 | Folder src/mist/access/api holds eight children | src/mist/access/api | main | 4ec10e478f3b370be159b98442a1a72ad88f3b90 | present | 0 |
| RC-37 | Folder tests/unit/api holds four children | tests/unit/api | main | 5345eedbb25005a1176188979807257e1cc8aa41 | present | 0 |
| RC-38 | Folder tests/guardrails holds 79 children | tests/guardrails | main | 17c7b7f3c0ec8acc4c4d338ea27a8eb1fa2203da | present | 0 |
| RC-39 | Folder .github holds 14 children | .github | main | 698ed28caaebf2e4b9b871c2228f3a4e0d92261e | present | 0 |
| RC-40 | Folder changelog.d holds 335 children | changelog.d | main | ece56396f47d31dfed7bebe6c69f6dda39f53d83 | present | 0 |
| RC-41 | Organization networks SDK builds its path from the identifier | .venv\Lib\site-packages\mistapi\api\v1\orgs\networks.py | installed mistapi 0.64.1 | 13c142d7fd215700217c96559cdfedf068647d70 | present | 48 |
| RC-42 | Site derived networks SDK builds its path from the identifier | .venv\Lib\site-packages\mistapi\api\v1\sites\networks.py | installed mistapi 0.64.1 | 6603d15b0f6c0d73b9dff2d202436537f3dea8be | present | 43 |
| RC-43 | Organization policies SDK builds its path from the identifier | .venv\Lib\site-packages\mistapi\api\v1\orgs\servicepolicies.py | installed mistapi 0.64.1 | b1c6ab1bc13c6925db80dfd30105f6b7166f1a74 | present | 48 |
| RC-44 | Site derived policies SDK builds its path from the identifier | .venv\Lib\site-packages\mistapi\api\v1\sites\servicepolicies.py | installed mistapi 0.64.1 | 65215b139c22433cbf21723b75cf9d1d96a070e0 | present | 43 |
| RC-45 | Organization templates SDK builds its path from the identifier | .venv\Lib\site-packages\mistapi\api\v1\orgs\gatewaytemplates.py | installed mistapi 0.64.1 | 6b82963804738f1a6a85af80dab4b3c7d9b67735 | present | 48 |
| RC-46 | Site derived templates SDK builds its path from the identifier | .venv\Lib\site-packages\mistapi\api\v1\sites\gatewaytemplates.py | installed mistapi 0.64.1 | 5e555e38819f03b81b2f15c267b659db4353abc7 | present | 43 |
| RC-47 | Legacy: module path api/tenant_fetch.py (retired src root) | api/tenant_fetch.py (retired src root) | 188956f937019a0e07cab73919ebd289179c5def | a3db77a6507a9d37fd3a9f1cd51d3f8ee3c53e4c | stale | 0 |
| RC-48 | Legacy: record folder specs/2863-tenant-identifier-slice is a direct child of specs | specs/2863-tenant-identifier-slice | 188956f937019a0e07cab73919ebd289179c5def | a5628cc408a6b66df24637972bd4c9cc60a32fad | stale | 0 |
| RC-49 | Legacy: quickstart test path tests/unit/test_api_tenant_fetch.py | tests/unit/test_api_tenant_fetch.py | main | absent-in-main-tree | stale | 0 |
| RC-50 | Legacy: quickstart test path tests/unit/test_issue_2971_status_before_count.py | tests/unit/test_issue_2971_status_before_count.py | main | absent-in-main-tree | stale | 0 |
| RC-51 | Legacy: read-only caller path websocket/service_ping_discovery.py (retired src root) | websocket/service_ping_discovery.py (retired src root) | main | absent-in-main-tree | stale | 0 |
| RC-52 | Legacy: plan requires Python 3.13 or newer | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | stale | 278 |
| RC-53 | Legacy: private name helpers have no caller outside the module | src/mist/access/api/tenant_fetch.py | main | ba7e74141e32b6d0a4d4edfbeeff618290a9641f | present | 40 |
| RC-54 | Legacy: validate_site_id accepts non-string values | src/foundation/runtime/validation/validation_utils.py | main | 8fed7ee47971d7968e776f253209ce341637e0a6 | present | 38 |
| RC-55 | Legacy: starting revision a5d465a exists | commit | a5d465a461d2512b717e943278fdff2b1897df84 | 8fd5f211bb74c6421f29ea27af865ad8d33994d3 | present | 0 |
| RC-56 | Legacy: preserved branch head 188956f exists | commit | 188956f937019a0e07cab73919ebd289179c5def | 0703b6e7ed2ce477da81df9b7288bb557ac4b62d | present | 0 |
| RC-57 | Issue comment: batch-1 branch head 6eec0e4 exists | commit | 6eec0e4bf09a6ca5deb1bb78c008337bab6e7464 | 472e71cb1d1aa6209f0cc6e9e84696b644cbb3be | present | 0 |
| RC-58 | Issue comment: menu 159 is the SSID workflow (registry line says Bounce port) | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | stale | 232 |
| RC-59 | SSID consolidation title belongs to menu 145 | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 6131 |
| RC-60 | Menu 145 category is interactive | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 251 |
| RC-61 | Menu 158 category is destructive | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 183 |
| RC-62 | Menu 161 category is destructive | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 184 |
| RC-63 | Menu 239 category is destructive | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | present | 636 |
| RC-64 | Issue comment: reboot and chassis paths are outside the destructive set | src/foundation/support/utils/operation_registry.py | main | ad30bc79d75f73db7d3a8c9e5cadfe45ec8d6891 | stale | 183 |
| RC-65 | SSID phase 2 site identifier default in the cached lookup | src/operations/execution/ssid_consolidation/_ssid_template_phase2.py | main | 647c597c257077243bfd280f939d5a82c7422818 | present | 72 |
| RC-66 | SSID phase 2 site identifier default in the entry builder | src/operations/execution/ssid_consolidation/_ssid_template_phase2.py | main | 647c597c257077243bfd280f939d5a82c7422818 | present | 132 |
| RC-67 | SSID phase 2 per-site write call | src/operations/execution/ssid_consolidation/_ssid_template_phase2.py | main | 647c597c257077243bfd280f939d5a82c7422818 | present | 274 |
| RC-68 | Chassis convert site identifier default | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 579 |
| RC-69 | Chassis convert helper refuses a blank site and returns False | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 583 |
| RC-70 | Chassis preflight site identifier default | src/mist/resources/device/virtual_chassis.py | main | 751a13c68d62086d158cbae68c0d3d8727348ce2 | present | 820 |
| RC-71 | Gateway reboot site identifier default | src/mist/resources/device/device_reboot_manager.py | main | c4a127cb591ff9e7ca47c94550c37f6343b0a5c7 | present | 367 |
| RC-72 | Path device/virtual_chassis.py (retired src root) from PR #3035 | device/virtual_chassis.py (retired src root) | main | absent-in-main-tree | absent | 0 |
| RC-73 | Upgrade portal passes an organization default to the planner | src/interfaces/portals/upgrade_portal/app/wiring.py | main | 78a1f4c825fb10f5e4ae7c2ef689ef01c45ecc85 | present | 1309 |
| RC-74 | Issue comment: wiring.py line 747 is the organization default example | src/interfaces/portals/upgrade_portal/app/wiring.py | main | 78a1f4c825fb10f5e4ae7c2ef689ef01c45ecc85 | stale | 747 |
| RC-75 | Organization default with an empty string in the dependency kwargs | MistHelper.py | main | 98d7828479ded6bc4c83d15e0c1847171cfbfd49 | present | 3615 |
| RC-76 | Organization resolver defined in the configuration utilities | src/foundation/runtime/config/config_utils.py | main | b63d83c1cfad322df7442a2241d8e614c1d6fdfa | present | 181 |
| RC-77 | Environment default for the organization identifier in the web server entry | wsgi.py | main | e8b2be7cb33c54266afcd5723293b7487df4d365 | present | 55 |
| RC-78 | SSID consolidation test file exists | tests/unit/prod_readiness/standalone/operations/execution/ssid/test_ssid_template_consolidation.py | main | 326cc798c6780c44435de42ea4814747eb3f524e | present | 1 |
| RC-79 | Device reboot test file exists | tests/unit/device/test_device_reboot_manager.py | main | 0b4e6134ec51583263f126ce9f122183d7e406f7 | present | 1 |
| RC-80 | Virtual chassis test file exists | tests/unit/test_virtual_chassis.py | main | 530fda76b86af6234154d0faf5771c3b3398176f | present | 1 |
| RC-81 | Second virtual chassis test file exists | tests/test_virtual_chassis.py | main | 45f1a45a5f500cc2aa1f2d6c8b1159971d43aecf | present | 1 |
| RC-82 | Changelog fragment policy guard exists | tests/guardrails/test_changelog_fragment_policy.py | main | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 1 |

Row count: 82. The STATUS file lists the same 82 checks.

## Legacy Record Verification

The legacy record is `specs/2863-tenant-identifier-slice/` on branch `recovery/2863-handoff-20261004` (commit `188956f937019a0e07cab73919ebd289179c5def`). The record holds five files: `spec.md` (133 lines), `research.md` (67 lines), `plan.md` (153 lines), `tasks.md` (87 lines), and `quickstart.md` (187 lines). Each file was read in full. Each file is a draft to verify, not proof.

Counts for the legacy claims among rows RC-47 to RC-56:
- Verified: 4 (RC-53, RC-54, RC-55, RC-56).
- Stale: 6 (RC-47, RC-48, RC-49, RC-50, RC-51, RC-52).
- Absent: 0.

Reuse decision: The legacy spec, research decisions, and tenant test names are reused as draft content. The legacy module path, record location, Python version, quickstart paths, and branch name are not reused. The legacy result numbers are not reused (Unverified).

## Issue and Pull Request Facts

- Issue #2863: open. Title "chore: audit org and site ID defaults that mask missing inputs". Labels: `chore`, `tests`, `in-progress`, `backend`, `src`, `priority:P2`, `severity:high`, `needs-human-review`. Created 2026-09-17. Updated 2026-11-10. Seven comments, dated 2026-10-01 to 2026-11-10.
- Issue body: names 102 deferred candidates from the visible inventory. Each repair must fail visibly at the missing identifier.
- PR #2864, merged 2026-09-17, branch `chore/2753-masking-defaults`. Body gives the triage count of 102 organization or site candidates deferred to #2863.
- PR #3035, merged 2026-09-19, branch `fix/2863-scope-id-defaults`. Body says "Refs #2863". Changed `device/` files (retired src root) that main no longer holds (RC-72).
- PR #3098, merged 2026-09-20, branch `fix/2863-scope-id-defaults`. Body says "Part of #2863". Changed `scripts/probe_pk_strategy.py`.
- PR #3997, merged 2026-10-06 22:54:03 UTC, branch `jmorrison-juniper-fix/2926-walk-blind-handler`. Changed `src/interfaces/portals/upgrade_portal/upgrade/org_cascade/walk.py`.
- PR #4521, merged 2026-11-05, for issue #2753 only.
- PR #4498, merged 2026-10-30, for issue #2753 only.
- PR #4055, closed without merge, for issue #2753 batch 1 only.
- Open pull requests on 2026-11-26: seven. No open pull request changes a planned path (scan of changed files).
- Issue #2977 is open. The 2026-10-01 comment places the tenant slice at queue position 31 after #2977.
- Issue #2862 is closed (2026-09-20). Issue #2861 is open. Issue #2753 is open. Issue #1924 is closed (2026-09-16).
- Issue #2926 is closed (2026-10-30). Issue #3824 is open. Issue #4747 is open. PR #4358 merged 2026-11-13.

## Sources

Local paths (read in this session):
- `AGENTS.md`, `.github/copilot-instructions.md`, `.specify/memory/constitution.md` (full read).
- `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, `checklist-template.md` (full read).
- `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/` (reference record). Headings and the first sections of `spec.md`, `plan.md`, `analysis.md`, and `design/checklists/requirements.md` were read.
- `documentation/mist-api-openapi31yaml.yaml` (lines 15118, 35430, 59899, 60286). The file blob matches main.
- `.venv\Lib\site-packages\mistapi\api\v1\` (six SDK files, version 0.64.1, read with view and select string).
- `documentation/diagrams/class-hierarchy/infrastructure.md:98` maps `APITenantFetchUtils` to `src/mist/access/api/tenant_fetch.py`.
- `documentation/menu-api/websocket.md:470-479` lists six endpoint calls. The table names the tenant methods. The record makes no change to that file.
- `documentation/quality-gates.md:1-60` lists the CI job IDs and the baseline commands.
- `documentation/architecture.md:270` lists `src/mist/access/api/` with status "In Progress" for incremental migration. The plan treats the folder debt as separate remediation.
- `documentation/MIST_API_GET_ENDPOINTS.md` lines 559, 730, 833, 1251, 1360, and 1442 list the six tenant functions. The file serves as coverage only. No claim depends on it.
- `documentation/development-setup.md:155` and `documentation/operator-guide.md:517-664` describe the organization prompt and environment settings. This record changes no operator behavior in those files.

Remote sources (GitHub read with `gh`):
- Issue #2863 body and seven comments: https://github.com/jmorrison-juniper/MistHelper/issues/2863
- Pull requests listed in the section above: https://github.com/jmorrison-juniper/MistHelper/pull/3035 and the other numbers.
- Git objects at the commits in RC-55 to RC-57, and the main tree.

No web source was used. No `web_fetch` call was made, because each claim had a local or remote source.

## Unverified

- The count of 110 occurrences in 38 files, and the count of 997 tracked non-test Python files, from the 2026-10-06 comment. No scan ran (rule 2).
- The count of 102 organization or site candidates from PR #2864. The inventory section holds 2749 rows, but the file does not state the subset rule. The count is not reproduced.
- The counts of 145 (PR #3035) and 76 (PR #3098). They use different scan rules.
- The legacy record reports 309 focused tests, 149 new tests, 88 refusal cases, and 98.31 percent branch coverage. It also reports Pylint 10.00, Black checking 2,009 files, mypy checking 663 files, and pip-audit checking 105 dependencies. These figures came from a prior run.
- The legacy STE result. It is partial, because the licensed dictionary was unavailable.
- The 2026-11-09 comment claim that the committed tenant test file passed 149 cases in an isolated setup.
- The 2026-11-10 comment claims about offline helper controls for device IDs. No live call and no control run is reproduced.
- The runtime result of the six SDK functions with an empty identifier. The record reads the f-string that builds the path (RC-41 to RC-46). It does not run the function.
- The service ping output text for a refusal. The record reads the manager code (RC-34). It does not run the workflow.
- The menu-to-function trace for menus 158, 161, and 162. The record reads the registry and the callee functions only.
- The menu-to-function trace for menu 145 beyond the handler call at `MistHelper.py:6130`.
- The reason that issue #2862 closed on 2026-09-20.

## Skills

No skill was loaded. No Podman, Juniper device, or container question applies to this record.
