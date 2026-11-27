# Research: Reviewed Restore and Partial-Operation Recovery

## R1. Issue facts and linked work

- Issue 4646 is open. Its title is "[Spec]: Add reviewed restore and partial-operation recovery". It was created on 2026-11-07 at 16:19:11 UTC and has no comments. Its labels are `feature`, `web-portal`, and `needs-human-review`.
- The issue maps to parity tasks T027 and T028. Issue 4224 records this mapping in a comment of 2026-11-07 at 16:21:08 UTC.
- A search for "4646" in pull requests returns no pull request.
- The issue body names pull request 4596 as the full task map. Pull request 4596 is merged on 2026-11-13 at 09:41:52 UTC. It changed 10 files and has 49 status checks.
- Open draft pull request 4208 changes 82 files. It changes `web_portal/app.py` and `web_portal/templates/base.html`. No other open pull request touches a converter path. Seven pull requests are open in total.
- Related issue states on this date: issues 4224, 4634, 4635, 4636, 4643, 4644, 4645, 4646, 4647, 4648, and 4649 are open.
- Issues 4632 and 4633 are closed.
- The issue 4224 comment of 2026-11-09 assigns the shared portal files to draft pull request 4208. It also states that the handover gate stays open.

## R2. Existing record, route, and sibling records

- Local search of `specs` finds no folder whose name starts with `4646-`. The remote tree also has none (remote check 54).
- The route is computed from the base-5 rule. Decimal 4646 equals `122041` in base 5, which is 1x5^5 + 2x5^4 + 2x5^3 + 0x5^2 + 4x5 + 1. Padded to eight levels, the route is `0/0/1/2/2/0/4/1`. The same arithmetic gives the reference route `0/0/1/2/4/1/4/0` for decimal 4920.
- The route folder `specs/numbered/0/0/1/2/2/0` has no children on `main` (remote check 54). This record creates no file in the repository.
- Sibling record 4636 is complete as a draft. Its record path is `specs\numbered\0\0\1\2\2\0\2\1\4636-converter-package-state-model`. It replaces `models.py` with a `state/` package and keeps each level at five children or fewer. It defines decisions D-1 to D-15, which this record keeps consistent. Issue 4636 is not on `main` (remote check 55).
- The sibling STATUS file of issue 4636 lists 24 remote checks. Its summary states 60. The difference is recorded as finding F-23 in `analysis.md`.
- Sibling folders 4647, 4648, and 4649 held no files when this record was written. Their consistency is unverified (unverified item U-12).
- The reference record `specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv` exists on `main` (remote check 53). It holds `spec.md`, `plan.md`, `tasks.md`, `analysis.md`, and `design\` with `research.md`, `data-model.md`, `quickstart.md`, `contracts\`, and `checklists\`. This record uses the same shape.
- No skill was loaded. The issue has no Podman question and no Juniper device behavior question.

## R3. Parity contract and comparison rows

- Parity task T027 names the test file `tests/contract/cisco_config_converter/test_recovery.py` (remote check 57). Parity task T028 names `routes.py` and `models.py` (remote check 58).
- Parity row C28 covers policy, service, and network restore. It requires explicit conflict resolution and verified create and update results (remote check 66).
- Parity row C31 covers recovery after a partial apply. It states that no atomic rollback guarantee exists (remote check 67).
- Parity FR-020 requires complete verified backups, preserved unrelated changes, and fresh approval (remote check 62). FR-022 requires reviewed restore (remote check 63). FR-024 requires two confirmations and the exact typed word `CONFIRM` (remote check 64).
- Parity contract `design/contracts/mist.md` states that recovery uses object IDs and the operation record (remote check 72). It states that an object absent from a backup is never deleted (remote check 73). It states that unknown results stop automatic writes (remote check 71).
- Parity gate G4 requires implementation evidence for recovery behavior (remote check 68).

## R4. Mist OpenAPI contract (local file, remote blob verified)

The OpenAPI file `documentation/mist-api-openapi31yaml.yaml` is 4,317,370 bytes. Its Git blob SHA on `main` is `b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14` (remote check 75 line). The contents API does not return files above 1 MB. This record read the body through the Git blobs API for that blob.

- The restore uses twelve operations. Each list, get, create, and update operation exists. The line numbers are in remote checks 75 to 86.
- Each get operation documents a 404 response. The `getOrgNetwork` block documents 200, 400, 401, 403, 404, and 429 responses (line 15299, remote check 77).
- The schemas `network`, `org_service_policy`, and `service` declare `id`, `created_time`, `modified_time`, and `org_id` through component references (remote checks 88, 89, and 90). The components `id`, `created_time`, `modified_time`, and `org_id` each declare `readOnly: true` (remote checks 91 to 94).
- The `org_service_policy` schema declares `services` and `tenants` as `strings` (remote check 95). The `strings` component is an array of unique strings. No description states whether a value is a name or an ID (unverified item U-1).
- The `HTTP429` response component exists (remote check 87). Its description was not read (unverified item U-4).
- The create and update operations for policies, services, and networks use one schema each for the request body. The update operation for each family uses the same schema as the create operation.
- The JSON twin `documentation/mist-api-openapi31json.json` exists on `main` (remote check 96). This record cites the YAML file only.

## R5. mistapi SDK 0.64.1 (local installed package)

The installed package is at `.venv\Lib\site-packages\mistapi`. The `.venv` folder is ignored by Git, so the remote tree does not hold it. The SDK checks use the local path and the Git blob hash of each file (remote checks 97 to 104).

- The module `mistapi.api.v1.orgs.networks` defines `listOrgNetworks` (line 17), `createOrgNetwork` (line 58), `getOrgNetwork` (line 89), `deleteOrgNetwork` (line 117), and `updateOrgNetwork` (line 145).
- The module `services.py` defines the matching service functions. The module `servicepolicies.py` defines the matching service policy functions. Both modules use the same line numbers (remote checks 98 and 99).
- Every function takes `mist_session` as the first argument. The list functions take `limit` and `page`. The default `limit` is 100 (unverified item U-8 covers the maximum).
- The request module sets `_MAX_429_RETRIES` to 3 (line 59). The wrapper `_request_with_retry` (line 203) repeats the call after HTTP 429 for every method, including POST and PUT. The wait is 5 seconds, then 10, then 20, unless the response carries a `Retry-After` header.
- The request module contains no `timeout` keyword. Its PUT function (line 303) sends the body without a timeout argument (remote check 102).
- The wrapper catches connection, proxy, and other exceptions. It returns an `APIResponse` whose `status_code` stays `None` when no response exists (remote checks 101 and 103).
- The installed version is 0.64.1 (`METADATA` line 3, remote check 104). The pin in `requirements.txt` line 129 is `mistapi==0.64.1` (remote check 27).

## R6. Repository restore precedent (menu 306)

Menu 306 restores firmware policies. Its documentation gives the closest precedent in this repository (remote checks 28 to 34).

- Each target needs a durable verified recovery record before the first write.
- Organization writes precede site writes.
- The tool does not retry a settings write automatically.
- The first failed write stops later writes. Earlier changes can remain.
- No automatic rollback occurs.
- The SDK settings endpoints give no conditional update contract.
- Organization write locks refuse overlapping changes across sessions and workers.

This record follows the same pattern. Menu 306 uses the typed word `RESTORE`. This record uses `CONFIRM` because parity FR-024 names it for administrative writes (decision D-6).

## R7. Constitution and instruction constraints

- The five-item rule forbids a new direct child in a noncompliant parent (remote check 14). Grandfathered debt is not a permission to add a violation (remote check 18).
- Destructive changes to the Mist cloud need a typed confirmation (remote check 15).
- Secrets and credentials never appear in logs, outputs, or errors (remote check 105).
- Structured log entries are required for new services and modules (remote check 106).
- Every line of AI-generated code has an inline comment (remote check 107). Each action has a log statement before and after it (remote check 108).
- mistapi is the sole interface to the Mist REST API (remote checks 5 and 16).
- Operational store records need fail-closed behavior, backup and recovery, retention, and verified persistence (remote check 17).
- The Local gates table names each gate command (remote check 6). The copilot instructions name the MYPY, VULTURE, PYDOCSTYLE, and INTERROGATE path variables (remote checks 10 to 13).
- AGENTS.md requires a file set declaration before a change (remote check 4). It forbids a compatibility shim (remote check 3). It sets the writing style (remote check 1).
- The pull request title must use a Conventional Commits form (remote check 9).

## R8. Structure capacity and layout options

| Option | Result | Decision |
| --- | --- | --- |
| A. New package `state/recovery/` | `state/` would hold six children. Noncompliant. | Rejected. |
| B. Put all recovery code into existing modules | No module has room for the Mist gateway. A gateway class in `routes.py` adds a sixth name. | Rejected. |
| C. New package `cloud/` under the converter root | The converter root holds five children. Noncompliant. | Rejected. |
| D. Package `state/lifecycle/recovery/` after issue 4636 moves `backup.py` into it | Each level holds five children or fewer. | Chosen. Decision D-2. |

## Decisions

Each decision names the alternatives, the chosen option, the reason, and the risk. A decision marked HUMAN-DECISION-REQUIRED needs an owner answer before a write can run.

### D-1. Restore covers three object families

- Alternatives: Network, service, and service policy only. Or add the template and device profile families.
- Chosen: Network, service, and service policy only.
- Reason: Parity FR-022 and row C28 name these three families (remote checks 63 and 66).
- Risk: Template restore stays outside the scope. Operators need another reviewed path for templates.

### D-2. Recovery code enters `state/lifecycle/recovery/`

- Alternatives: A new `state/recovery/` package. Or put all logic into existing modules. Or put the gateway in `routes.py`.
- Chosen: `state/lifecycle/recovery/`, after issue 4636 moves `backup.py` into it (dependency R-4636-1).
- Reason: The constitution forbids a sixth child (remote check 14). Options A, B, and C in section R8 fail that rule.
- Risk: Issue 4636 must adopt the move before implementation starts.

### D-3. Tests use the integration folder

- Alternatives: Use `tests/contract/cisco_config_converter/` as parity T027 names. Or put the tests into `tests/integration/web_portal/cisco_config_converter/state/`.
- Chosen: `tests/integration/web_portal/cisco_config_converter/recovery/`.
- Reason: `tests/contract/` holds 17 children (remote check 44). The parity path would add a child to a noncompliant parent. Issue 4636 decision D-2 also uses the integration folder.
- Risk: The parity owner must accept the changed path.

### D-4. The Mist gateway sits in `state/lifecycle/recovery/gateway.py`

- Alternatives: Direct HTTP to Mist, which remote check 16 prohibits. A gateway in `routes.py`, which adds a name. A new `cloud/` package, which is noncompliant.
- Chosen: The gateway module calls the mistapi functions from section R5 with explicit arguments.
- Reason: The gateway is the only file that imports mistapi in the recovery package. The SDK compatibility guard covers it.
- Risk: The state tree imports mistapi. This departs from issue 4636 decision D-13 for this change only. The exception is recorded in `plan.md`.

### D-5. One route function serves status and commands

- Alternatives: One route per command. Or a separate blueprint module.
- Chosen: One function `restore_route` with `GET` for status and `POST` for commands under `/cisco-config-converter/admin/restore`.
- Reason: `routes.py` holds four top-level names (remote check 38). One new function reaches the limit of five. A second function would exceed it.
- Risk: Commands use a JSON field named `command`. The dispatcher validates each command.

### D-6. The typed word is `CONFIRM`

- Alternatives: `RESTORE`, which menu 306 uses (remote check 7). Or accept both words.
- Chosen: `CONFIRM`.
- Reason: Parity FR-024 names `CONFIRM` for administrative writes (remote check 64).
- Risk: Two features use two words for similar actions. The owner should align them. Finding F-4 records the difference.

### D-7. Two confirmations apply to each write

- Alternatives: One typed word only. Or one checkbox only.
- Chosen: A scope confirmation at approval, and the typed word `CONFIRM` at execution.
- Reason: Parity FR-024 names two confirmations and the typed word (remote check 64).
- Risk: The interface needs two steps. Issue 4647 designs the steps.

### D-8. Each backup object receives one decision

- Alternatives: Overwrite each changed object automatically. Or block every changed object with no override.
- Chosen: Five decisions: create, update, conflict, unchanged, and preserve. An update needs a recorded override for that object.
- Reason: The issue requires preserved unrelated objects. Parity row C28 requires explicit conflict handling (remote check 66). An override keeps the change reviewable.
- Risk: Operators can override a change that another operator made. The approval and the recovery backup cover that case. Warning: An override replaces a change that another operator made after the backup.

### D-9. Changed-after-backup detection compares digests

- Alternatives: Compare the `modified_time` value with the capture time. Or compare both values.
- Chosen: Compare normalized digests only.
- Reason: The meaning of `modified_time` after a write is unverified (unverified item U-5).
- Risk: A change with identical content is treated as unchanged. That result is correct for the restore.

### D-10. Duplicate names resolve only by exclusion

- Alternatives: Update the other object with the same name. Or rename the restored object.
- Chosen: Exclude the backup object from the proposal and report a duplicate-name conflict.
- Reason: Parity row C28 requires explicit resolution (remote check 66). Updating another object would overwrite an unrelated object. Renaming changes content that the backup does not contain.
- Risk: A duplicate stays in the cloud until an operator removes it through issue 4645.

### D-11. Unresolved references block the proposal

- Alternatives: Write the object anyway. Or skip the reference silently.
- Chosen: Each name in `services`, `tenants`, and `routed_for_networks` must resolve to a current object or to an earlier write in the same proposal. Otherwise the object becomes a conflict.
- Reason: The reference meaning is unverified (unverified item U-1). Failing closed avoids a wrong binding.
- Risk: Some valid backups block until an operator resolves the reference.

### D-12. Writes run in a fixed order

- Alternatives: Use the backup order. Or write in parallel.
- Chosen: Network, service, and service policy. Within a family, use ascending natural ID.
- Reason: Menu 306 writes organization records before site records (remote check 29). Policies can depend on services and networks.
- Risk: Networks that route to each other can form a cycle. Unresolved reference checks detect that case.

### D-13. The first failed, partial, or indeterminate outcome stops later writes

- Alternatives: Continue after a failure. Or run an automatic rollback.
- Chosen: Stop. Record the phase as failed, partial, or indeterminate. Do not reverse changes automatically.
- Reason: Menu 306 stops at the first failure and does not reverse changes automatically (remote checks 31 and 32). Parity row C31 states that no atomic rollback exists (remote check 67).
- Risk: Warning: A stop leaves earlier changes in place. The operator must review each recorded outcome.

### D-14. Write-capable approvals stay refused until the identity design is approved (HUMAN-DECISION-REQUIRED)

- Alternatives: Accept an unverified operator name. Or use an IP allowlist as the operator identity.
- Chosen: Refuse every write-capable approval. The owner must approve an authenticated identity design.
- Reason: Issue 4636 decision D-10 refuses the same case. The constitution requires typed confirmation for cloud changes (remote check 15). An IP allowlist does not identify an operator.
- Risk: Restore stays unusable until the owner decides. This decision needs owner approval for credential policy.

### D-15. Each operation holds at most 100 writes, and each write waits at most 60 seconds

- Alternatives: No limit. Or a limit of 25 writes.
- Chosen: 100 write decisions and a 60-second bound for each write.
- Reason: A large batch increases the risk and the lock time. The SDK sets no timeout (remote check 102). The owner can change these values.
- Risk: A large organization needs several operations. Each operation needs its own approval.

### D-16. Each write runs in a worker thread with a bounded wait

- Alternatives: Call the SDK directly with no bound. Or change the SDK session timeout for every caller.
- Chosen: Run each write in a worker thread. Wait at most 60 seconds. A missed bound yields an indeterminate outcome.
- Reason: The SDK sets no timeout (remote check 102). A global change affects other callers.
- Risk: Caution: A missed wait can still complete the write later. Reconciliation reads the object before any next step.

### D-17. A final HTTP 429 yields an indeterminate outcome

- Alternatives: Treat HTTP 429 as not applied and repeat the write. Or fail without reconciliation.
- Chosen: Treat the final HTTP 429 as indeterminate. Reconcile before any next write.
- Reason: The SDK already repeats writes after HTTP 429 (remote check 100). Mist does not document whether a 429 response means not processed (unverified item U-4).
- Risk: Extra read calls. Test E12 proves that reconciliation runs first.

### D-18. Recovery reverses an update only when the current digest matches

- Alternatives: Reverse every update. Or skip recovery for updates.
- Chosen: Reverse an update only when the current normalized digest equals the recorded after-digest.
- Reason: The parity Mist contract requires proof of ownership before a reverse change (remote check 72).
- Risk: A later change by another operator blocks the reverse update. The operator must resolve the conflict.

### D-19. Recovery keeps created objects by default

- Alternatives: Delete every created object. Or delete only after approval.
- Chosen: Keep each created object unless the owner permits deletion (decision D-20).
- Reason: The parity Mist contract says that an object absent from a backup is never deleted (remote check 73). Deletion is destructive.
- Risk: A partial create can remain in the cloud. The operator sees it in the recovery proposal.

### D-20. Deletion during recovery needs owner permission (HUMAN-DECISION-REQUIRED)

- Alternatives: Allow deletion of each created object by default. Or never allow deletion.
- Chosen: Allow deletion only when the owner records permission and the deletion path of issue 4645 runs. The default stays keep.
- Reason: The constitution requires typed confirmation for destructive changes (remote check 15). The owner must decide whether production deletion is allowed.
- Risk: Warning: Deleting a created object removes production data that operators can use. This decision needs owner approval for production data destruction.

### D-21. Approvals expire after 15 minutes and allow one use

- Alternatives: A longer lifetime. Or reuse an approval across operations.
- Chosen: Expiry 15 minutes after creation, inclusive. The approval binds one operator, one proposal digest, and one scope digest. It allows one use.
- Reason: Issue 4636 decisions D-6 and D-7 set the same rules.
- Risk: The owner may choose another value. The value is an assumption until then.

### D-22. The administrative gate comes from issue 4645

- Alternatives: Add a second gate for restore. Or hide the route in the interface only.
- Chosen: Use the gate that issue 4645 defines. This record adds no environment variable.
- Reason: The parity portal contract names hidden or denied mode for administration (remote check 74). A second gate would split the authority.
- Risk: The design of issue 4645 can change this decision.

### D-23. Issue 4647 renders the restore view

- Alternatives: Implement the view in this record. Or defer the view and its acceptance.
- Chosen: Issue 4647 renders the view from the response fields in `design/contracts/restore-api.md`.
- Reason: Presentation files belong to issues 4637, 4638, and 4647 (parity overlap comment of 2026-11-09). Remote checks 40 and 41 show the existing presentation files.
- Risk: The issue UI expectation stays open until issue 4647 merges.

### D-24. Logs and responses hold identifiers, digests, counts, and phases

- Alternatives: Log the object body for debugging. Or log nothing.
- Chosen: Log and respond with identifiers, digests, counts, and phases only.
- Reason: The constitution requires secret-free logs (remote check 105) and action logging (remote check 108).
- Risk: Debugging needs a separate private trace. This record adds none.

### D-25. The transition table adds `reconciled` to `verified`

- Alternatives: Keep `reconciled` terminal. Or move directly from `indeterminate` to `verified`.
- Chosen: Add the edge `reconciled` to `verified`. Use it when reconciliation proves that every write applied.
- Reason: The table in issue 4636 has no edge for that case. The alternative would hide a proven result.
- Risk: One more edge needs a test in `test_restore_decisions.py` or `test_recovery.py`.

### D-26. A scope lock uses the first 32 hexadecimal characters of the organization digest

- Alternatives: No lock. Or lock by operation only.
- Chosen: Lock by the first 32 hexadecimal characters of the SHA-256 digest of the organization ID. The lock file lives under the operation folder.
- Reason: The parity Mist contract requires serialized writes to one scope (remote check 70). Operation locks do not stop two operations on one organization.
- Risk: A stale lock blocks execution until its timeout. The store refuses execution on timeout.

### D-27. `BackupManifest` gains a private `objects` mapping

- Alternatives: A separate payload record kind. Or store the bodies in the operation record.
- Chosen: Add the normalized body of each object to the private manifest. Exclude the mapping from every public view.
- Reason: Restore needs the body of each object. A new kind changes the allow list of issue 4636. The operation record is shared and can reach exports.
- Risk: Issue 4643 must store the bodies in the same shape.

## Remote verification

The tree read for `main` returned 11404 entries and `truncated` was false. The commit SHA of `main` is `f03c6c9b36d612a48d7b9652998c2fd87dd777ca`, dated 2026-11-26 at 07:15:01 UTC. Each row below is one check. The count of rows is 108. Rows 97 to 104 use local SDK files and their Git blob hashes. Result `absent` means the path is absent on `main`, or the claimed text is absent from the file.

| # | Claim | Path | Ref | Blob SHA | Result | Line |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | AGENTS.md section Writing style | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| 2 | AGENTS.md section Secrets | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 172 |
| 3 | AGENTS.md compatibility shim rule | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 87 |
| 4 | AGENTS.md declares the file set before a change | `AGENTS.md` | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 246 |
| 5 | mistapi is the only interface to the Mist REST API | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 21 |
| 6 | Local gates table | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 50 |
| 7 | Menu 306 restores firmware policies with exact RESTORE | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 324 |
| 8 | Move a module gates | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 261 |
| 9 | Pull request title rule | `.github/copilot-instructions.md` | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 501 |
| 10 | MYPY_PATHS value | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 93 |
| 11 | VULTURE_PATHS value | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 101 |
| 12 | PYDOCSTYLE_PATHS value | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 104 |
| 13 | INTERROGATE_PATHS value | `.github/workflows/ci.yml` | main | d51efbc13c0f0a2076680030ed8be7ef7cf64523 | present | 107 |
| 14 | Five-item rule forbids a direct child in a noncompliant parent | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 42 |
| 15 | Typed confirmation for destructive changes to the Mist cloud | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 121 |
| 16 | mistapi is the sole Mist REST interface | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 280 |
| 17 | Operational store may hold coordination records | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 315 |
| 18 | Grandfathered debt is not a permission to add violations | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 552 |
| 19 | Spec template exists | `.specify/templates/spec-template.md` | main | 083ef123e7a2e56e21f3062173fb003258f927e2 | present | 0 |
| 20 | Plan template exists | `.specify/templates/plan-template.md` | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 0 |
| 21 | Tasks template exists | `.specify/templates/tasks-template.md` | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 0 |
| 22 | Checklist template exists | `.specify/templates/checklist-template.md` | main | 806657da09d1058823923e346a323b633114971a | present | 0 |
| 23 | Route calculation script exists | `.specify/scripts/powershell/spec-route.ps1` | main | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 0 |
| 24 | Nested package guard sets MAX_CHILDREN to 5 | `tests/guardrails/test_nested_package_structure.py` | main | 5678277a376271483a6d340751e4c8ff7b5d92a3 | present | 17 |
| 25 | Move-module guard exists | `tests/guardrails/test_move_module_guidance.py` | main | ae163b792b330285dba7a8c32cc957a78c3838d4 | present | 0 |
| 26 | SDK compatibility guard exists | `tests/integration/test_mistapi_sdk_compatibility.py` | main | cab2d602113012729f6c392dff43197d05913a38 | present | 0 |
| 27 | mistapi is pinned to 0.64.1 | `requirements.txt` | main | 50fe63d4cf5e6071612c62c288e965190c60b969 | present | 129 |
| 28 | Each target needs a durable verified recovery record before the first write | `documentation/backup-restoration.md` | main | f256e296c2e24a39f062627efbc531f9bcb0ebd5 | present | 66 |
| 29 | Organization writes precede site writes | `documentation/backup-restoration.md` | main | f256e296c2e24a39f062627efbc531f9bcb0ebd5 | present | 68 |
| 30 | The tool does not retry a settings write automatically | `documentation/backup-restoration.md` | main | f256e296c2e24a39f062627efbc531f9bcb0ebd5 | present | 71 |
| 31 | The first failed write stops later writes | `documentation/backup-restoration.md` | main | f256e296c2e24a39f062627efbc531f9bcb0ebd5 | present | 73 |
| 32 | No automatic rollback occurs | `documentation/backup-restoration.md` | main | f256e296c2e24a39f062627efbc531f9bcb0ebd5 | present | 77 |
| 33 | The SDK settings endpoints give no conditional update contract | `documentation/backup-restoration.md` | main | f256e296c2e24a39f062627efbc531f9bcb0ebd5 | present | 79 |
| 34 | Organization write locks refuse overlapping changes | `documentation/backup-restoration.md` | main | f256e296c2e24a39f062627efbc531f9bcb0ebd5 | present | 108 |
| 35 | models.py declares five top-level classes, the first at line 13 | `src/interfaces/portals/cisco_config_converter/models.py` | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 13 |
| 36 | conversion.py imports from models.py | `src/interfaces/portals/cisco_config_converter/conversion.py` | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 6 |
| 37 | routes.py imports from models.py | `src/interfaces/portals/cisco_config_converter/routes.py` | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 12 |
| 38 | routes.py holds four top-level names, the last at line 99 | `src/interfaces/portals/cisco_config_converter/routes.py` | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 99 |
| 39 | The converter root holds five children | `src/interfaces/portals/cisco_config_converter` | main | 363cf44f8bad5dfdcd344a76852a8a34146b9190 | present | 0 |
| 40 | The presentation template exists and issue 4647 owns it | `src/interfaces/portals/cisco_config_converter/presentation/converter.html` | main | 270c3e40e226c026a54aef846f9b341d6a76eee9 | present | 0 |
| 41 | The presentation script exists and issue 4647 owns it | `src/interfaces/portals/cisco_config_converter/presentation/converter.js` | main | 9c7ad354600aade5b3a37bbd536ac49486edfd6e | present | 0 |
| 42 | The state package is absent before issue 4636 | `src/interfaces/portals/cisco_config_converter/state` | main | not-a-blob | absent | 0 |
| 43 | The portals folder holds six children | `src/interfaces/portals` | main | 7f5ac6778b6a7a78ad7268542bb8de2a9c550926 | present | 0 |
| 44 | The contract folder holds 17 children | `tests/contract` | main | 3e544ef7c55adf7c8a8010e6da3afc345b27d57e | present | 0 |
| 45 | The parity test path tests/contract/cisco_config_converter is absent | `tests/contract/cisco_config_converter` | main | not-a-blob | absent | 0 |
| 46 | The converter test folder holds two children | `tests/integration/web_portal/cisco_config_converter` | main | 6538f20cdb454342a96e079a0e7678fb6baa7a42 | present | 0 |
| 47 | The existing route test file exists | `tests/integration/web_portal/cisco_config_converter/test_routes.py` | main | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 0 |
| 48 | The recovery test folder is absent before this record | `tests/integration/web_portal/cisco_config_converter/recovery` | main | not-a-blob | absent | 0 |
| 49 | app.py registers no converter blueprint | `web_portal/app.py` | main | 0fb25df1732815d18ff30d1823cbbdd30608aed6 | absent | 0 |
| 50 | base.html has no converter navigation | `web_portal/templates/base.html` | main | 351cc44aeeae0a6fd61d4205af2de6777d066b2f | absent | 0 |
| 51 | PORTAL_SECRET_KEY falls back to a random uuid4 value | `web_portal/services/config.py` | main | c198505a43bbd2faadfcffee6c8685c6ab5df17c | present | 113 |
| 52 | The firmware ownership lock is prior art | `web_portal/routes/firmware_policy/jobs/ownership/__init__.py` | main | 0cc40a4942129a1c08f5c68d2013e5ee974bb863 | present | 0 |
| 53 | The reference record exists | `specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md` | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 1 |
| 54 | The route folder for issue 4646 is absent before the write | `specs/numbered/0/0/1/2/2/0/4/1` | main | not-a-blob | absent | 0 |
| 55 | The issue 4636 record is absent from main | `specs/numbered/0/0/1/2/2/0/2/1/4636-converter-package-state-model` | main | not-a-blob | absent | 0 |
| 56 | The parent numbered record exists | `specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/plan.md` | main | 9c3fdacc929850e1ed923b248f1dc6520aa01fdd | present | 0 |
| 57 | Parity T027 names tests/contract/cisco_config_converter/test_recovery.py | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md` | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 92 |
| 58 | Parity T028 names routes.py and models.py | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md` | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 93 |
| 59 | The parity checkpoint approves no bulk production operation | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md` | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 96 |
| 60 | Parity T027 depends on T003 and T006 | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md` | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 151 |
| 61 | Parity T028 depends on T001, T002, T022, T026, and T027 | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md` | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 152 |
| 62 | Parity FR-020 requires complete verified backups and fresh approval | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md` | main | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 126 |
| 63 | Parity FR-022 requires reviewed restore | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md` | main | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 128 |
| 64 | Parity FR-024 requires two confirmations and the typed word CONFIRM | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md` | main | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 130 |
| 65 | Parity SC-004 requires an indeterminate result without repetition | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md` | main | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 165 |
| 66 | Parity row C28 covers policy, service, and network restore | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md` | main | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 112 |
| 67 | Parity row C31 covers recovery after a partial apply | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md` | main | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 115 |
| 68 | Parity gate G4 requires execution evidence for recovery | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/analysis.md` | main | a08601943e89b95af5ebe9530c0d8b9bb47459ab | present | 26 |
| 69 | Parity data model names the state transitions | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/data-model.md` | main | afb08dab16578918a56d4a4cb95ddee998d99883 | present | 43 |
| 70 | Parity Mist contract names the execution and unknown results rules | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md` | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 124 |
| 71 | Parity Mist contract stops automatic write retries | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md` | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 135 |
| 72 | Parity Mist contract names the backup and recovery rules | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md` | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 140 |
| 73 | Parity Mist contract never deletes an object merely absent from a backup | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/mist.md` | main | f57f068da5ffd7f3c8d499eab78c51b92f45aa3a | present | 150 |
| 74 | Parity portal contract names the administration row with hidden or denied mode | `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/contracts/portal.md` | main | 56e3b23b9ac04e4a733c62970811ca0ead4df83c | present | 65 |
| 75 | OpenAPI operation listOrgNetworks | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 15122 |
| 76 | OpenAPI operation createOrgNetwork | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 15161 |
| 77 | OpenAPI operation getOrgNetwork with a 404 response | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 15299 |
| 78 | OpenAPI operation updateOrgNetwork | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 15322 |
| 79 | OpenAPI operation listOrgServices | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 18494 |
| 80 | OpenAPI operation createOrgService | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 18527 |
| 81 | OpenAPI operation getOrgService | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 18587 |
| 82 | OpenAPI operation updateOrgService | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 18611 |
| 83 | OpenAPI operation listOrgServicePolicies | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 18345 |
| 84 | OpenAPI operation createOrgServicePolicy | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 18378 |
| 85 | OpenAPI operation getOrgServicePolicy | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 18434 |
| 86 | OpenAPI operation updateOrgServicePolicy | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 18458 |
| 87 | OpenAPI HTTP429 response component | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 62692 |
| 88 | OpenAPI network schema with readOnly component references | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 88200 |
| 89 | OpenAPI org_service_policy schema | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 89301 |
| 90 | OpenAPI service schema | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 99703 |
| 91 | OpenAPI id component is readOnly | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 81474 |
| 92 | OpenAPI created_time component is readOnly | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 76048 |
| 93 | OpenAPI modified_time component is readOnly | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 85212 |
| 94 | OpenAPI org_id component is readOnly | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 89137 |
| 95 | OpenAPI strings component is an array of strings | `documentation/mist-api-openapi31yaml.yaml` | main | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | present | 111562 |
| 96 | The JSON twin of the OpenAPI file exists | `documentation/mist-api-openapi31json.json` | main | 5f9f4ce94f812f0e818ee65f99f032118a28f56c | present | 0 |
| 97 | networks.py defines the four network functions, the last at line 145 | `.venv\Lib\site-packages\mistapi\api\v1\orgs\networks.py` | local-venv-0.64.1 | 13c142d7fd215700217c96559cdfedf068647d70 | present | 145 |
| 98 | services.py defines the four service functions, the last at line 145 | `.venv\Lib\site-packages\mistapi\api\v1\orgs\services.py` | local-venv-0.64.1 | 20e034e490c137209f284fc69b95b43e6f33eb24 | present | 145 |
| 99 | servicepolicies.py defines the four service policy functions, the last at line 145 | `.venv\Lib\site-packages\mistapi\api\v1\orgs\servicepolicies.py` | local-venv-0.64.1 | b1c6ab1bc13c6925db80dfd30105f6b7166f1a74 | present | 145 |
| 100 | The HTTP 429 retry limit of three applies to every method | `.venv\Lib\site-packages\mistapi\__api_request.py` | local-venv-0.64.1 | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 59 |
| 101 | The request wrapper catches failures and returns a response object | `.venv\Lib\site-packages\mistapi\__api_request.py` | local-venv-0.64.1 | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | present | 203 |
| 102 | The request module contains no timeout keyword | `.venv\Lib\site-packages\mistapi\__api_request.py` | local-venv-0.64.1 | 845318094ceaf3d2a7d7950ef4dbb93625defb54 | absent | 0 |
| 103 | APIResponse status_code defaults to None | `.venv\Lib\site-packages\mistapi\__api_response.py` | local-venv-0.64.1 | 2d878d79295fec79e6409f6243132c53280f15ab | present | 43 |
| 104 | The installed version is 0.64.1 | `.venv\Lib\site-packages\mistapi-0.64.1.dist-info\METADATA` | local-venv-0.64.1 | 86b3b7003d569a1311af4085e7e269a52decd795 | present | 3 |
| 105 | Secrets and credentials never appear in logs, outputs, or errors (constitution Principle III) | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 134 |
| 106 | Structured log entries are required for new services and modules (constitution Principle V) | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 193 |
| 107 | Every line of AI-generated code has an inline comment (constitution Principle VI) | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 206 |
| 108 | Each action has a log statement before and after it (constitution Principle VII) | `.specify/memory/constitution.md` | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 237 |

## Sources

- Local repository files, read only: `AGENTS.md`, `.github/copilot-instructions.md`, and `.github/workflows/ci.yml`.
- The constitution and the four templates are read from `.specify/`.
- `documentation/backup-restoration.md` and the Mist API documents are read from `documentation/`.
- `documentation/MIST_API_GET_ENDPOINTS.md` lists the GET operations at lines 729, 730, 832, 833, 839, and 840.
- `documentation/MIST_API_MISSING_ENDPOINTS.md` lists the missing GET operations at lines 704, 796, and 802.
- Local converter files on `main`, verified by the remote read: `src/interfaces/portals/cisco_config_converter/` and `web_portal/`.
- Parity record on `main`: `specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/`.
- Sibling STATUS file read only: `spec-drafts\_meta\4636-STATUS.json` and `spec-drafts\4636\` records.
- Installed SDK, read only: `.venv\Lib\site-packages\mistapi\`.
- GitHub reads through the `gh` command cover issue 4646 and the issue 4224 comments. They also cover issue states 4632 to 4649, pull requests 4596 and 4208, the labels list, and the tree of `main`.
- URLs read through GitHub: https://github.com/jmorrison-juniper/MistHelper/issues/4646 and https://github.com/jmorrison-juniper/MistHelper/pull/4596.
- No upstream URL was fetched through a web fetch.

## Unverified

- U-1. The meaning of the `services` and `tenants` strings in service policies, and the `routed_for_networks` names in networks, is not stated. The reason is that the OpenAPI describes them only as strings. Effect: decision D-11 blocks unresolved references.
- U-2. Whether a Mist update replaces or merges the object body is not stated. The reason is that the update descriptions do not say so. Effect: the read-back check reports a partial outcome when fields merge.
- U-3. Whether a create response returns a new natural ID and accepts the normalized body is not verified. The reason is that no payload fixture exists. Effect: a create without an ID is indeterminate.
- U-4. Whether an HTTP 429 response means the request was not processed is not verified. The reason is that the response description was not read. Effect: decision D-17 treats the final 429 as indeterminate.
- U-5. The meaning of `modified_time` after a write is not verified. The reason is that the field is only marked read-only. Effect: decision D-9 uses digests only.
- U-6. The name uniqueness rule for networks, services, and policies is not verified. The reason is that no document states it. Effect: decision D-10 treats duplicates as conflicts.
- U-7. Whether Mist refuses to delete a network or service that a policy references is not verified. The reason is that no document states it. Effect: the recovery delete path needs owner permission (decision D-20).
- U-8. The maximum page size for list operations is not verified. The reason is that only the default of 100 appears in the SDK docstring. Effect: the list loop reads pages until a page returns fewer items than the limit.
- U-9. Whether a retry after HTTP 429 creates a duplicate object in practice is not verified. The reason is that the server behavior is unknown. Effect: decision D-17 and test E12 reconcile before the next write.
- U-10. The live behavior of every Mist write is not verified. The reason is that this record makes no live call. Effect: every behavior in the tests is simulated.
- U-11. The decisions of issues 4634 and 4635 and the designs of issues 4643, 4644, and 4645 are not on `main`. The reason is that those records are not merged. Effect: the record lists each one as a prerequisite.
- U-12. The consistency of sibling records 4647, 4648, and 4649 is not verified. The reason is that those folders held no files at review time. Effect: each sibling review waits before T005.
- U-13. The test-quality configuration and baseline files named by the ratchet procedure are not in the remote check list. Their presence is not verified. Effect: T-LOCAL-GATES names the procedure only.
