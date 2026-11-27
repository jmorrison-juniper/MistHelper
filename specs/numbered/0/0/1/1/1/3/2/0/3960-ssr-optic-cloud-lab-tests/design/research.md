# Research: SSR optic and Mist cloud path lab tests

Each decision names its alternatives, the chosen option, the rationale, and the risk. The remote verification table holds every remote check in this record. Facts come from the issue thread, the merged pull requests, remote blobs on main, and local files whose hashes match those blobs.

## Decisions

### D-1. Reuse the merged section 14 subsection

- **Decision**: Reuse the verification subsection that pull request #4114 merged. Edit its rows. Add no second table.
- **Alternatives considered**:
  - Open a new pull request that rewrites the subsection.
  - Reuse the merged subsection and edit its rows. This option is chosen.
- **Rationale**: Remote checks C-16 and C-17 show the subsection and six Not run rows on main. Check C-65 shows the merge commit 400899f4. A rewrite would duplicate the text and invite drift.
- **Risk**: Readers see Not run until the owner records a result.
- **Human decision required**: no.

### D-2. The owner runs every lab step

- **Decision**: The owner runs H-1 to H-6 on a lab SSR. The agent holds no lab device access and no lab credential.
- **Alternatives considered**:
  - The agent runs the steps through an authorized console.
  - The owner runs every step. This option is chosen.
  - The owner runs some steps and the agent runs the rest.
- **Rationale**: The orchestrator instruction forbids credential use. The owner comment dated 2026-10-21 requires an identified lab SSR and a typed confirmation before H-6. This session has no lab device.
- **Risk**: Lab evidence arrives later than an agent run would. The quickstart gives exact commands to reduce owner effort.
- **Human decision required**: no. The orchestrator instruction sets the credential rule. A future credential policy needs a separate issue.

### D-3. Closing keyword rule

- **Decision**: Use `Refs #3960` in a pull request that holds partial results. Use `Closes #3960` only in the final pull request, after six outputs exist.
- **Alternatives considered**:
  - Always use `Closes #3960`, as the handoff template states.
  - Always use `Refs #3960`.
  - Use `Refs` until six outputs exist, then use `Closes`. This option is chosen.
- **Rationale**: The owner comment dated 2026-10-21 keeps #3960 open until sanitized output exists. The close-linked-issues workflow closes the issue that a merged pull request names (C-53). AGENTS.md line 224 requires the closing keyword in the body.
- **Risk**: Partial results need an extra pull request before closure. The final pull request carries all six outputs.
- **Human decision required**: no.

### D-4. The verifier and its test stay unchanged

- **Decision**: Leave scripts/verify_ssr_commands.py and tests/unit/scripts/test_verify_ssr_commands.py unchanged. Open a separate issue for the verifier defects.
- **Alternatives considered**:
  - Repair the verifier in this issue.
  - Leave the verifier unchanged and open a separate issue. This option is chosen.
- **Rationale**: The AGENTS.md Git flow rule says one issue holds one subject. The handoff assigns the verifier to pull request #3953, which merged on 2026-10-06, so that assignment lapsed. Defects A4 to A7 need separate evidence.
- **Risk**: The verifier keeps reporting `show route` and the section 13 labels. The lab outputs are the proof for H-1 and H-2.
- **Human decision required**: no.

### D-5. Claim comment and label cleanup

- **Decision**: Post the claim comment on #3960, not on #3959. Remove the stale in-progress label now. The implementer adds the label again at T002.
- **Alternatives considered**:
  - Comment on #3959 and keep the label.
  - Claim on #3960 and remove the label now. This option is chosen.
- **Rationale**: Issue #3959 closed on 2026-10-21. The fleet comments released the claim on 2026-10-07. AGENTS.md line 187 requires the label before the branch. AGENTS.md line 260 places a handoff in a comment on the issue.
- **Risk**: Another agent could read the removed label as free work. The implementer adds the label at T002 before any edit.
- **Human decision required**: no.

### D-6. Scope of the verification table

- **Decision**: Keep the section 14 table at six rows. Record each other unverified statement as unresolved item U-3.
- **Alternatives considered**:
  - Add rows now for every vendor-sourced statement.
  - Keep six rows and record the gap. This option is chosen.
- **Rationale**: The issue defines six tasks. A new row needs lab or vendor evidence, and this run cannot fetch the vendor sources.
- **Risk**: Readers may treat an unlisted statement as verified. U-3 names the gap for the owner.
- **Human decision required**: no.

### D-7. Output targets

- **Decision**: Record each output in the step that its runbook row names. Record H-2 in the section 11 table, as the issue states.
- **Alternatives considered**:
  - Record every output in the step that its row names. This rule puts H-2 in step C2.
  - Record every output where the issue names it. This rule moves H-3 and H-5 away from their rows.
  - Use the runbook rule for each output except H-2. This option is chosen.
- **Rationale**: The rule at lines 367 to 370 (C-18) matches the issue for H-1, H-3, H-4, H-5, and H-6. The issue names section 11 for H-2. The exact error text of a failing command belongs with the section 11 failing commands.
- **Risk**: H-2 has two locations. Row 361 points to the section 11 row to remove the ambiguity.
- **Human decision required**: no.

### D-8. Typed confirmation for H-6

- **Decision**: Before H-6 blocks TCP port 443, the owner types `BLOCK-443` followed by the lab router name.
- **Alternatives considered**:
  - Require a yes answer only.
  - Require a typed phrase with the router name. This option is chosen.
  - Require the router name only.
- **Rationale**: The owner comment dated 2026-10-21 requires an explicit typed confirmation. The repository uses typed words for risky operations (C-40). The router name binds the phrase to one device.
- **Risk**: The owner types the wrong router name. The agent never runs H-6, and the owner checks the name before the block.
- **Human decision required**: no.

## Remote verification table

All checks use ref main. A commit check holds the commit hash in the path column and `none` in the blob column. A local file matched the remote blob SHA in the sources section, so its line numbers apply to the remote blob.

| ID | Claim | Path | Blob SHA | Result | Line |
|----|-------|------|----------|--------|------|
| C-01 | Runbook exists on main with 385 lines. | documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md | 4fe23574f2f66792139b4c84132a85a21f3dda03 | present | 1 |
| C-02 | Step C2 names the optics-statistics command, the SSR 7.1.0 condition, and the example port xe-0-1. | documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md | 4fe23574f2f66792139b4c84132a85a21f3dda03 | present | 104 |
| C-03 | Section Check an optic without optics-statistics exists. | documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md | 4fe23574f2f66792139b4c84132a85a21f3dda03 | present | 113 |
| C-04 | Step D7 names show mist detail, the Agent field, and the Connection field. | documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md | 4fe23574f2f66792139b4c84132a85a21f3dda03 | present | 141 |
| C-05 | Section Test the path to the Mist cloud exists. | documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md | 4fe23574f2f66792139b4c84132a85a21f3dda03 | present | 143 |
| C-06 | Sentence reports a 2026-10-05 ICMP observation with no source in the repository. | documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md | 4fe23574f2f66792139b4c84132a85a21f3dda03 | present | 149 |
| C-07 | Rule names the MGMT port mgmt-0-0 for an SSR1300. The vendor source is not fetched. | documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md | 4fe23574f2f66792139b4c84132a85a21f3dda03 | present | 153 |
| C-08 | Last sentence of the cloud path section names the Testing Tools. | documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md | 4fe23574f2f66792139b4c84132a85a21f3dda03 | present | 166 |
| C-09 | Section 11 row lists show device-interface with the optics-statistics value and no name keyword. | documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md | 4fe23574f2f66792139b4c84132a85a21f3dda03 | present | 245 |
| C-10 | Section 11 row lists show device-interface with the extended-statistics value and no name keyword. | documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md | 4fe23574f2f66792139b4c84132a85a21f3dda03 | present | 246 |
| C-11 | Section 11 row lists show route as a command that no SSR release accepts. | documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md | 4fe23574f2f66792139b4c84132a85a21f3dda03 | present | 240 |
| C-12 | Section 13 names the labels Show Summary, Show Path, and Refresh ARP. | documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md | 4fe23574f2f66792139b4c84132a85a21f3dda03 | present | 297 |
| C-13 | Section 14 names scripts/fetch_ssr_docs.py and scripts/pdf_to_markdown.py. | documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md | 4fe23574f2f66792139b4c84132a85a21f3dda03 | present | 328 |
| C-14 | Section 14 holds the subsection Sources for the optic check and the cloud path check. | documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md | 4fe23574f2f66792139b4c84132a85a21f3dda03 | present | 333 |
| C-15 | Section 14 cites the SSR 7.1 release notes for item I95-44742. | documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md | 4fe23574f2f66792139b4c84132a85a21f3dda03 | present | 339 |
| C-16 | Section 14 holds the subsection Verification status of the optic check and the cloud path check. | documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md | 4fe23574f2f66792139b4c84132a85a21f3dda03 | present | 347 |
| C-17 | The verification table holds six rows, and each Lab test cell reads Not run. | documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md | 4fe23574f2f66792139b4c84132a85a21f3dda03 | present | 360 |
| C-18 | Section 14 gives the record rule for lab outputs. | documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md | 4fe23574f2f66792139b4c84132a85a21f3dda03 | present | 367 |
| C-19 | Verifier file scripts/verify_ssr_commands.py exists. | scripts/verify_ssr_commands.py | d6d4041fcc7f7e0f0adc677a11debfadbbb305e0 | present | 1 |
| C-20 | Verifier removes fenced blocks before it pairs inline code spans. | scripts/verify_ssr_commands.py | d6d4041fcc7f7e0f0adc677a11debfadbbb305e0 | present | 45 |
| C-21 | Verifier accepts a command when a parent command matches. | scripts/verify_ssr_commands.py | d6d4041fcc7f7e0f0adc677a11debfadbbb305e0 | present | 58 |
| C-22 | Verifier main block reads only the console health check runbook. | scripts/verify_ssr_commands.py | d6d4041fcc7f7e0f0adc677a11debfadbbb305e0 | present | 67 |
| C-23 | Verifier input documentation/references/ssr/cli_reference.md is absent from main. | documentation/references/ssr/cli_reference.md | none | absent | 0 |
| C-24 | Git ignores the documentation/references/ folder. | .gitignore | 17eadfadb35a59e191a61c78877569ad747ddcc7 | present | 28 |
| C-25 | Verifier test file exists and writes its own inputs. | tests/unit/scripts/test_verify_ssr_commands.py | 08843e3c358c8da874b7ae76f0bf50996528b7e6 | present | 10 |
| C-26 | Fetch script exists and writes to documentation/references/ssr. | scripts/fetch_ssr_docs.py | 8cda26884a8a17b02cf1f7c1c7132a340d1e6283 | present | 85 |
| C-27 | PDF converter script exists. | scripts/pdf_to_markdown.py | 558e96a13de42cf5a82e0ab5b6c4d25ff1e2f94a | present | 1 |
| C-28 | Changelog README gives the file name table. | changelog.d/README.md | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 24 |
| C-29 | Fragment from pull request #4114 exists. | changelog.d/issue-3960-ssr-lab-verification-status.md | bbcbbf602eef34185d3a6f3c0aa8f8dd27a8aa37 | present | 1 |
| C-30 | Fragment from pull request #3951 exists. | changelog.d/issue-3946-kms-optic-health-ping-commands.md | cf74c70b36a8b05ddf8c5ea6ddff8e849b8510e4 | present | 1 |
| C-31 | Fragment from pull request #3953 exists. | changelog.d/issue-3947-verify-ssr-command-count.md | 72efa2106a5da1078f293f86b4e0a5b870431ba2 | present | 1 |
| C-32 | Changelog guard test checks the allowed fragment name patterns. | tests/guardrails/test_changelog_fragment_policy.py | dbd5e8776797f12536b3bc2bd613143b85f3fc4a | present | 38 |
| C-33 | Quality gates document gives the ste-linter command. | documentation/quality-gates.md | 6776d334cca5d9b43273473a06da367a65605c6d | present | 283 |
| C-34 | Development tooling document names the markdown-link-check pre-commit hook. | documentation/development-tooling-migration.md | 7a512059a87c07345728032ac684843d04005e9c | present | 201 |
| C-35 | Local gates table lists the STE command. | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| C-36 | Numbered records use the managed roots and the base-5 route. | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 159 |
| C-37 | Fragment name rule for an issue without a pull request. | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| C-38 | The container build workflow runs only for a push that changes a product file. | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 473 |
| C-39 | MistHelper is a public repository. | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 478 |
| C-40 | The safety section requires a typed word for destructive operations. | .github/copilot-instructions.md | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 309 |
| C-41 | Claim the issue with the in-progress label before the branch. | AGENTS.md | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 187 |
| C-42 | Write Closes with the issue number in the pull request body. | AGENTS.md | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 224 |
| C-43 | Add the auto-merge label only after each check and CodeQL show green. | AGENTS.md | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 229 |
| C-44 | Put a handoff in a comment on the issue or the pull request. | AGENTS.md | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 260 |
| C-45 | Each Markdown file passes the STE gate and each hyperlink resolves. | AGENTS.md | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 340 |
| C-46 | Route width default is eight base-5 segments. | .specify/scripts/powershell/spec-route.ps1 | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 7 |
| C-47 | Route guard rejects a parent that already holds five children. | .specify/scripts/powershell/spec-route.ps1 | 37293a255f9b5de20ccb2b3ef0ad15717bab2826 | present | 92 |
| C-48 | Five-item rule requires five children or fewer at each level. | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| C-49 | Required labels section names the type, scope, and status labels. | .specify/memory/constitution.md | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 487 |
| C-50 | STE linter config file exists. | .ste-linter.toml | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 1 |
| C-51 | STE workflow file exists. | .github/workflows/ste-lint.yml | abaeff6d5e299bfa7de4dc15d04f4ef31cf13b5f | present | 1 |
| C-52 | Auto-merge workflow file exists. | .github/workflows/auto-merge.yml | 9d26134dd84cf50008a17fd878772102ce355983 | present | 1 |
| C-53 | Close-linked-issues workflow file exists. | .github/workflows/close-linked-issues.yml | 42a085ac6240518b028862c290ec9502a5b13b2a | present | 1 |
| C-54 | CodeQL workflow file exists. | .github/workflows/codeql.yml | 2ef072fbddd473f841c5877f4d89b7c7760aeaf0 | present | 1 |
| C-55 | Pull request template exists. | .github/PULL_REQUEST_TEMPLATE.md | ed03e8f36f20962d9c7bbd74cde192d5adfdcc77 | present | 1 |
| C-56 | GW_PORT_DOWN.md holds Junos commands in a command table at lines 165 to 171. | documentation/noc-runbooks/GW_PORT_DOWN.md | df79e601daa3bffbff40a715a13c95bc6a6b8ef7 | present | 165 |
| C-57 | _shared_common.md holds Junos commands in a command table at lines 89 to 107. | documentation/noc-runbooks/_shared_common.md | 1b2d4f584bc4a217418926cfecc02dc8a1ffcc45 | present | 89 |
| C-58 | GATEWAY_DOWN.md exists. | documentation/noc-runbooks/GATEWAY_DOWN.md | 451a771d2755516e59d6f7bdc169dce9cf7fc52d | present | 1 |
| C-59 | GW_VPN_PATH_DOWN.md exists. | documentation/noc-runbooks/GW_VPN_PATH_DOWN.md | d63d995080c0f5526c5e6b8a1f48c6d5e7fc011c | present | 1 |
| C-60 | GW_VPN_PEER_DOWN.md exists. | documentation/noc-runbooks/GW_VPN_PEER_DOWN.md | 7a2f0079363ca1969b261c0414b90dc6763adfa2 | present | 1 |
| C-61 | SSR_ALARM_INDEX.md exists. | documentation/noc-runbooks/SSR_ALARM_INDEX.md | df77ec9364561763f7200f2fac819211d05138e8 | present | 1 |
| C-62 | SSR_APPLICATION_PERFORMANCE.md exists. | documentation/noc-runbooks/SSR_APPLICATION_PERFORMANCE.md | 57937af2bb22f79e43e77f5f52a0fa8c445ab848 | present | 1 |
| C-63 | SSR_FIRMWARE_HEALTH.md exists. | documentation/noc-runbooks/SSR_FIRMWARE_HEALTH.md | 710430e7b2b9df26cf3192d620f6431f5f950a39 | present | 1 |
| C-64 | Commit 35177f4a7bd597520e0e956156c4e9b6f1f86e53 exists on main. It is the merge commit of pull request #3951. | commit 35177f4a7bd597520e0e956156c4e9b6f1f86e53 | none | present | 0 |
| C-65 | Commit 400899f46934c0da25425ce4a0bdb4c1dc966544 exists on main. It is the merge commit of pull request #4114. | commit 400899f46934c0da25425ce4a0bdb4c1dc966544 | none | present | 0 |
| C-66 | No record folder whose name starts with 3960- exists under specs. | specs/**/3960-* | none | absent | 0 |
| C-67 | Route folder specs/numbered/0/0/1/1/1 holds one child before this record. | specs/numbered/0/0/1/1/1 | 9697b2094fa4d784f54b0f3d3226a92ec43320e5 | present | 0 |
| C-68 | The Mist OpenAPI file names ep-terminator in one field description only. | documentation/mist-api-openapi31yaml.yaml | b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14 | partial | 109123 |
| C-69 | The runbook Caution names optic part 740-021309 in ports xe-0-0 through xe-0-3 on SSR1300 and SSR1400. The vendor source is not fetched. | documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md | 4fe23574f2f66792139b4c84132a85a21f3dda03 | present | 125 |

## Pull request, issue, and label facts

These facts come from GitHub reads. They are not remote checks, because they describe state and not files.

- Issue #3960: OPEN. Labels: device-specific, manual-review, chore, docs, in-progress, networking. Created 2026-10-06. Updated 2026-10-21.
- Issue #3959: CLOSED on 2026-10-21T04:50:58Z. Title: chore(agent): resume the issue fleet after PR #3953.
- Issue #3946: CLOSED on 2026-10-06T05:39:47Z, completed by pull request #3951.
- Issue #3947: CLOSED on 2026-10-06T07:36:21Z, completed by pull request #3953.
- Pull request #4114: MERGED on 2026-10-10T03:45:01Z. Merge commit 400899f46934c0da25425ce4a0bdb4c1dc966544. Head branch jmorrison-jnpr-docs-ssr-lab-runbook-validation. Files: changelog.d/issue-3960-ssr-lab-verification-status.md (+7 and -0) and documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md (+27 and -2). Check runs: 34 SUCCESS, 10 SKIPPED, 1 CANCELLED, 0 FAILURE.
- Pull request #3951: MERGED on 2026-10-06T05:39:46Z. Merge commit 35177f4a7bd597520e0e956156c4e9b6f1f86e53.
- Pull request #3953: MERGED on 2026-10-06T07:36:19Z. Head branch fix/3947-verify-ssr.
- Open pull requests on 2026-11-26: seven. None changes documentation/noc-runbooks/SSR_CONSOLE_HEALTH_CHECK.md, scripts/verify_ssr_commands.py, or changelog.d/issue-3960-ssr-lab-results.md. Two open pull requests change other changelog fragments.
- Repository labels that exist: in-progress, stage:speckit-artifacts-emitted, manual-review, device-specific, chore, docs.

## Sources

- Issue #3960 body and its four comments, read on 2026-11-26 with `gh issue view`. The comment of 2026-10-21 (ID IC_kwDOQltU8c8AAAABeA_H3g) holds the owner decision.
- Issue #3959 body, read with `gh issue view`.
- Local checks with read-only git commands. `git -C` with `rev-parse HEAD` returned f03c6c9b36d612a48d7b9652998c2fd87dd777ca. That value equals the remote main head.
- Local blob hashes with `git -C` and `hash-object` (no write flag). The hashes equal the remote blob SHAs for the runbook (4fe23574), the 3960 fragment (bbcbbf60), and the verifier (d6d4041f). They also equal the SHAs for the verifier test (08843e3c), the fetch script (8cda2688), and .gitignore (17eadfad).
- Local hashes also equal the remote SHAs for changelog.d/README.md (fcbde10e), copilot-instructions (f1ec2a46), AGENTS.md (44a9afff), and the constitution (4584997a). They match for spec-route.ps1 (37293a25), quality-gates (6776d334), development-tooling-migration (7a512059), .ste-linter.toml (d9f28ef8), and the OpenAPI file (b7fc2bfb).
- Local search of specs: no file or folder name starts with 3960-.
- Reference record shape: local folder specs\numbered\0\0\1\2\4\1\4\0\4920-ex-hardware-inventory-csv. The spec, research, analysis, and checklist files supplied the layout only.
- Juniper skill juniper-hw-ssr1000, at C:\Users\jmorrison\.copilot\skills\juniper-hw-ssr1000. SKILL.md line 10 and its answer rules. 02-ports.md lines 7, 9, 10, 11, and 16. Line 10 says SSR1300 has four 10GbE SFP+ ports named 0/0 to 0/3 and one 1GbE management port. Line 11 says SSR1400 has the same 10GbE group. The skill routes optic qualification to juniper-optical-transceivers, which this run did not load.
- mistapi: not used. This record makes no SDK claim. The Mist OpenAPI file was checked for ep-terminator only (C-68).
- Remote tree: one `gh api` call on git/trees/main with recursive set to 1. PowerShell filtered the JSON in place of the --jq option.
- Docs that do not apply: architecture.md, development-setup.md, container-deployment.md, and operator-guide.md. A case-insensitive search for runbook, SSR, ste-linter, markdown-link, Testing Tools, show mist, and ep-terminator found no match in these four files.
- Mist endpoint docs: MIST_API_GET_ENDPOINTS.md (lines 532 and 1715 to 1723) and MIST_API_MISSING_ENDPOINTS.md (lines 527 to 532 and 1586 to 1588) list SSR registration and upgrade REST endpoints only. No endpoint covers the runbook commands or the cloud link.
- Web sources attempted with web_fetch. https://docs.128technology.com/docs/release_notes_128t_7.1 returned a blocked-address error, because the host resolves to 100.64.1.110. https://www.juniper.net/documentation/us/en/software/mist/mist-management/topics/ref/firewall-ports-to-open.html redirected to networkingdocs.hpe.com, which returned a blocked-address error, because the host resolves to 100.64.1.101.
- Commands not run: no build, test, linter, formatter, package install, container, or repository script (brief rule 2). The GitHub reads set GH_HOST and GH_TOKEN from the account variable named in the brief. No value was printed.

## Unverified

- U-1 (C-06, line 149): The 2026-10-05 observation has no source in the repository or the issue. The reason is that no evidence file exists. H-7 covers this statement.
- U-2 (C-02 and C-69, lines 104 and 125): The runbook port names xe-0-x differ from the local hardware reference names 0/x. The reason is that the device prints the names only in H-3.
- U-3 (C-07 and C-69, lines 123, 125, and 153): Vendor-sourced statements have no lab row. The reason is decision D-6. The vendor sources are blocked in this run.
- U-4 (C-20, C-21, C-22, and C-23): Verifier defects A4 to A7. The reason is that they need separate evidence and a separate issue (D-4).
- U-5 (C-08, C-15, and C-69, lines 166 and 339 to 345): Vendor pages were not fetched. The reason is the blocked-address error. H-2 and H-4 test the release note claim (C-15). H-6 tests the Testing Tools claim (C-08).
- U-6 (C-04 and C-10, lines 141 and 246): `show mist detail` is covered by H-5. The command `show device-interface name <name> extended-statistics` has no lab test. The reason is that no vendor command reference is available in this run.
- U-7 (C-69, line 125): The optic part 740-021309 and the knowledge base article I95-65908 are not confirmed. The reason is that juniper-optical-transceivers was not loaded and the knowledge base host is blocked.
