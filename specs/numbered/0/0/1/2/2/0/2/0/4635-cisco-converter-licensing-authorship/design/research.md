# Research: Cisco converter licensing and authorship decisions

## Evidence boundary

- The evidence comes from GitHub read calls on 2026-11-26, from public Creative Commons legal code, and from local draft files.
- No repository file changed. No build, test, linter, or package install ran.
- Remote main is the truth for whether code exists. Local files support context only.
- The remote tree of main is complete. The API reports no truncation.
- No protected source expression was copied. No source code was compared in this pass.
- The record makes no Mist API claim and no mistapi claim.
- No skill was used. The record asks no Podman question and no Juniper device question.
- The architecture, development setup, container deployment, and operator guide documents do not apply. They describe runtime and setup behavior, and this record changes neither.

## Issue facts

- Title: "[Spec]: Resolve Cisco converter licensing and authorship decisions". State: OPEN. Created 2026-11-07. Updated 2026-11-08.
- Labels: feature, web-portal, needs-human-review, feature-spec.
- The body asks for an owner or legal decision for each reuse category. It also asks for the approved distribution path, blocked source reuse, and separate implementation and cloud gates.
- The body names task T002 of the full-parity task list, the parent issue 4224, and PR 4596 as the task map.
- The owner comment (author association OWNER, 2026-11-08) states that source-use and distribution decisions remain unresolved. It adds the needs-human-review label.
- A pull request search for "4635" returns no pull request. The working copy has no path that starts with 4635- under specs.

## Route derivation

Issue 4635 in base 5 has the digits 1 2 2 0 2 0. The arithmetic follows.

```text
4635 = 1 x 5^5 + 2 x 5^4 + 2 x 5^3 + 0 x 5^2 + 2 x 5^1 + 0 x 5^0
     = 3125 + 1250 + 250 + 0 + 10 + 0
```

Padded to eight places, the digits give 0 0 1 2 2 0 2 0. This matches the requested route. The same method gives 0 0 1 1 3 3 4 4 for issue 4224. It gives 0 0 1 2 4 1 4 0 for issue 4920.

## Decisions

Each legal decision carries the HUMAN-DECISION-REQUIRED marker. The drafting agent gives a recommended option. The recommended option is not a decision.

### D-1 Licensor and holder of the source (HUMAN-DECISION-REQUIRED)

- **Question**: Who holds the copyright in the source, and who may license it?
- **Options**:
  - A. The owner holds the copyright and grants written permission for named reuse.
  - B. A third party holds the copyright. Reuse needs written permission from that party.
  - C. The holder is unknown. Treat all protected source expression as blocked until written confirmation exists.
- **Evidence by option**:
  - A. RC-50 states the CC BY-NC 4.0 title. RC-02 names jmorrison-juniper as the holder of MistHelper. RC-62 shows the source repository under the account jmorrison-juniper.
  - B. RC-51 shows that the copyright line names no holder. A third-party holder needs contact. No repository evidence names one.
  - C. RC-51 shows the missing holder. RC-50 confirms the license title. Option C keeps all reuse blocked.
- **Recommended option**: C. The source license names no holder. Option C keeps reuse blocked until written confirmation exists.
- **Owner**: jmorrison-juniper, the repository owner, with legal review.
- **Risk**: Option A still needs legal review of the license terms. Option B needs contact with a third party.

### D-2 Source-code reuse category (HUMAN-DECISION-REQUIRED)

- **Question**: May protected source code be reused in the converter?
- **Options**:
  - A. No source-code reuse. Write all converter code independently. Recommended.
  - B. Reuse source code under CC BY-NC 4.0 with attribution. Legal review must decide whether this fits the NonCommercial term and the ShareAlike condition of the MistHelper license.
  - C. Reuse named files only with written permission from the holder.
- **Evidence by option**:
  - A. RC-44 forbids copying protected code. RC-42 records the decision not to copy code. RC-43 rejects a port as-is before license approval. RC-36 blocks reuse without legal and owner approval.
  - B. RC-52 states the NonCommercial term. RC-03 states the ShareAlike clause of the MistHelper license. RC-66 defines the ShareAlike condition for adapted material. Legal review decides the fit.
  - C. RC-36 requires approval for each reuse. Written permission needs a known holder, so option C depends on D-1.
- **Recommended option**: A. The issue requires blocked reuse until an explicit compatible path exists. Option A meets that requirement without a legal finding.
- **Owner**: jmorrison-juniper, with legal review.
- **Risk**: Option A adds effort to the converter work. Option B can save effort but may create legal exposure.

### D-3 Text reuse category (HUMAN-DECISION-REQUIRED)

- **Question**: May protected source text be reused in the converter, its documents, or its user interface?
- **Options**:
  - A. No text reuse. Write all text independently. Recommended.
  - B. Reuse documentation text with attribution. Legal review must decide whether the NonCommercial term applies.
  - C. Reuse short factual phrases only, after legal review of whether the phrases are protected.
- **Evidence by option**:
  - A. RC-44 names text as protected. RC-42 records the decision not to copy documentation text. RC-41 forbids reuse of prose and styles.
  - B. RC-54 and RC-55 show the source user guide and interface guide. Legal review decides whether the NonCommercial term applies to documentation.
  - C. Whether short factual phrases are protected is a legal question. No repository evidence answers it. RC-30 shows a same-license attribution note for another package.
- **Recommended option**: A. Option A removes the need for a text-protection finding.
- **Owner**: jmorrison-juniper, with legal review.
- **Risk**: Option A adds effort to the documentation. Options B and C need legal review before use.

### D-4 Mapping reuse category (HUMAN-DECISION-REQUIRED)

- **Question**: May protected source mappings be reused in the converter?
- **Options**:
  - A. No reuse of the mapping document. Derive mappings from public Mist API contract facts. Recommended.
  - B. Reuse mapping facts with independent wording, after legal review of whether the facts are protected.
  - C. Reuse the mapping document with attribution.
- **Evidence by option**:
  - A. RC-44 requires public contract facts for mappings. Issue 4634, which verifies the Mist API contracts for mappings, is open (Sources).
  - B. RC-53 shows the mapping reference document. Whether mapping facts are protected is a legal question. No repository evidence answers it.
  - C. RC-53 shows the mapping document. RC-44 names mappings as protected, so reuse needs approval under RC-36.
- **Recommended option**: A. The 4224 specification already requires public contract facts (RC-44). Option A follows that rule.
- **Owner**: jmorrison-juniper, with legal review.
- **Risk**: Option A needs contract verification work under issue 4634. Options B and C need legal review.

### D-5 Asset reuse category (HUMAN-DECISION-REQUIRED)

- **Question**: May protected source assets be reused in the converter?
- **Options**:
  - A. No asset reuse. Create new screens, styles, and images. Recommended.
  - B. Reuse the four source screenshots with attribution.
  - C. Reuse the source stylesheet or template with written permission from the holder.
- **Evidence by option**:
  - A. RC-41 forbids reuse of screenshots, assets, templates, prose, and styles. RC-42 forbids copying images.
  - B. RC-56 to RC-59 show the four screenshots. Attribution does not change the approval rule of RC-44. Legal review decides the fit.
  - C. RC-60 shows the stylesheet. RC-61 shows the HTML template. Both need written permission from the holder (D-1).
- **Recommended option**: A. The 4224 specification and the parity quickstart both forbid asset reuse (RC-42, RC-41).
- **Owner**: jmorrison-juniper, with legal review.
- **Risk**: Option A adds design work. Options B and C need legal review and, for C, written permission.

### D-6 Independent-authorship rules (HUMAN-DECISION-REQUIRED)

- **Question**: Which independent-authorship rules apply to converter work?
- **Options**:
  - A. Observation only. Authors read public contract facts and record behavior notes. Authors copy no source text. A reviewer compares each diff with the source before merge. Recommended.
  - B. Clean room. Authors do not open the source repository after the rule starts.
  - C. No reading limit. Only the final review checks the result.
- **Evidence by option**:
  - A. RC-33 states "Observation only and independent authorship" in the parity plan. RC-41 limits visual captures to independently authored screens. Local draft 4647 (provenance checklist items PRV003 and PRV004) asks for an origin review before presentation files change.
  - B. RC-39 shows the unchecked legal review box. RC-37 rates gate G1 HIGH. RC-33 allows observation, so a clean room is stricter than the parity plan.
  - C. RC-36 requires approval for reuse. Option C leaves no check before merge. RC-40 states that CC BY-NC 4.0 is not permission for unrestricted reuse. Local draft 4636 (decision D-14) allows independent authorship only.
- **Recommended option**: A. It matches the parity plan text (RC-33). Option B is stronger, but it may block the observation work that the parity plan allows.
- **Owner**: jmorrison-juniper, with legal review.
- **Risk**: Option A depends on reviewer discipline. Option C leaves no check before merge.

### D-7 Distribution path (HUMAN-DECISION-REQUIRED)

- **Question**: Which distribution path applies to converter code?
- **Options**:
  - A. Pause publication of converter code in releases and container images until the owner approves a path. Recommended.
  - B. Continue publication of independently authored converter code under the MistHelper license after the audit in T011 passes.
  - C. Remove converter files from main and from images until the owner approves a path.
- **Evidence by option**:
  - A. RC-27 shows that the container image copies src. RC-28 shows that the container build runs on pushes to main for listed paths. RC-29 shows that the release workflow runs on version tags. Pausing these paths limits exposure until approval. Unverified item U-2 covers the image contents.
  - B. RC-62 and RC-63 show that both repositories are public. RC-02 and RC-03 state the MistHelper license terms. RC-48 shows the merge of PR 4226 onto main. Option B depends on the audit in T011.
  - C. RC-48 shows the merge commit that a revert would remove. RC-30 shows a same-license attribution precedent. Option C changes main and needs a reviewed pull request.
- **Recommended option**: A. Option A keeps the publication state stable until the audit and the legal review finish.
- **Owner**: jmorrison-juniper, with legal review.
- **Risk**: Option A delays releases. Warning: A published image or release asset cannot be recalled from every copy. Option B may publish protected expression if the audit fails. Option C changes main and needs a reviewed pull request.

### D-8 Gate statement in every implementation task

- **Question**: How does the record keep protected source expression blocked until approval?
- **Options**:
  - A. Add a gate statement to each implementation task that names this record. Chosen.
  - B. Rely on the reviewer alone.
- **Chosen**: A. FR-006 and the issue acceptance criteria require a block. T012 adds the link.
- **Risk**: Each implementation task gains one more condition. Implementation runs more slowly.

### D-9 Gate G1 stays separate from gates G2 to G5

- **Question**: Does the legal gate merge with the other gates of the parity plan?
- **Options**:
  - A. Keep G1 separate from G2 to G5. Chosen.
  - B. Merge G1 with G4 (cloud owner) and approve cloud work with the legal decision.
- **Chosen**: A. The issue requires separate implementation and cloud gates. RC-34 and RC-35 show the separate gate rows.
- **Risk**: More evidence must stay current across gates.

### D-10 No license or legal text in this record

- **Question**: Does this record draft a license or a legal notice?
- **Options**:
  - A. Write no legal text. Chosen.
  - B. Draft a notice for the owner to review.
- **Chosen**: A. Legal text belongs to the owner and legal review. The issue body states that it grants no legal approval (RC-64).
- **Risk**: The owner writes the legal text later.

### D-11 No changelog fragment for this record

- **Question**: Does this internal-only record need a changelog fragment?
- **Options**:
  - A. Add no fragment. State the reason in the PR body. Chosen.
  - B. Add the fragment issue-4635-cisco-converter-licensing-authorship.md.
- **Chosen**: A. The changelog README says that an internal-only change adds no fragment (RC-17). The repository instructions limit the fragment rule to a change that a user sees (RC-74). PR 4596, the parity record, added no fragment (RC-31).
- **Risk**: The constitution requires one fragment for each change (RC-14). Analysis item A-6 records the conflict for the maintainer.

### D-12 Branch name chore/4635-cisco-converter-licensing-authorship

- **Question**: Which branch type applies?
- **Options**:
  - A. chore/4635-cisco-converter-licensing-authorship. Chosen.
  - B. docs/4635-cisco-converter-licensing-authorship.
  - C. feat/4635-cisco-converter-licensing-authorship.
- **Chosen**: A. The constitution lists fix, feat, and chore only (RC-15). AGENTS.md also lists docs (RC-07). The constitution is stricter for MistHelper, so the branch uses chore.
- **Risk**: None for the merge.

### D-13 Keep needs-human-review and block auto-merge until review

- **Question**: When may auto-merge start for the record PR?
- **Options**:
  - A. Add the auto-merge label only after CI passes, the review removes needs-human-review, and the orchestrator authorizes the merge. Chosen.
  - B. Add the auto-merge label after CI passes.
- **Chosen**: A. Issue 4635 carries the needs-human-review label (RC-64). The auto-merge workflow merges a labeled pull request after checks pass (RC-75). FR-017 keeps the review point. One serial merge slot applies until the owner validates a merge queue (RC-76).
- **Risk**: The merge waits for the review.

### D-14 Omit the design/contracts folder

- **Question**: Does an interface contract apply to this record?
- **Options**:
  - A. Omit the folder. The record defines no command, API, or portal interface. Chosen.
  - B. Add a contract for the decision register.
- **Chosen**: A. The record layout in the local brief allows omission when no contract applies.
- **Risk**: None.

### D-15 Describe the decision entities in data-model.md

- **Question**: Does the record need a data model?
- **Options**:
  - A. Describe the entities and state transitions in data-model.md. Chosen.
  - B. Write the single line "Not applicable" with a reason.
- **Chosen**: A. The record has entities, keys, and state transitions for reuse categories, decisions, options, and evidence rows.
- **Risk**: None.

## Remote verification table

Each row lists one check. Line 0 means a presence check only. "Not applicable" means the check uses metadata, a commit, a pull request, an issue, or a URL.

| ID | Claim | Path | Ref | Blob SHA | Result | Line |
| - | - | - | - | - | - | - |
| RC-01 | MistHelper license names CC BY-NC-SA 4.0 | LICENSE | main | d115eeab9dbd6f61d0233b0894d3f8309bb976e8 | present | 1 |
| RC-02 | MistHelper license names jmorrison-juniper as holder | LICENSE | main | d115eeab9dbd6f61d0233b0894d3f8309bb976e8 | present | 3 |
| RC-03 | MistHelper license has a ShareAlike clause | LICENSE | main | d115eeab9dbd6f61d0233b0894d3f8309bb976e8 | present | 14 |
| RC-04 | README names the license that covers MistHelper | README.md | main | 331a4567f72156fe2a3e3ee91005d2cbbcaed6d0 | present | 136 |
| RC-05 | AGENTS.md has the writing style section | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 40 |
| RC-06 | AGENTS.md requires each Markdown file to pass the STE gate | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 340 |
| RC-07 | AGENTS.md branch type list includes docs | AGENTS.md | main | 44a9afffb5bd6f774973a845d27343e4e528b6ad | present | 194 |
| RC-08 | Local gates table lists the STE command with threshold 80 | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 74 |
| RC-09 | Local gates table lists the Tests command | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 61 |
| RC-10 | STE CI job named STE lint exists | .github/workflows/ste-lint.yml | main | abaeff6d5e299bfa7de4dc15d04f4ef31cf13b5f | present | 17 |
| RC-11 | STE configuration file exists | .ste-linter.toml | main | d9f28ef8faf4a4c36a4e967d5b978f96eb306253 | present | 0 |
| RC-12 | Constitution Principle I is the Five-Item Rule | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 38 |
| RC-13 | Constitution requires managed roots and the eight-level base-5 route | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 57 |
| RC-14 | Constitution requires one changelog fragment for each change | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 409 |
| RC-15 | Constitution lists branch types fix, feat, and chore | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 478 |
| RC-16 | Constitution requires type, scope, and status labels | .specify/memory/constitution.md | main | 4584997a264c5a7ade2ca7441246e1f067083aa1 | present | 489 |
| RC-17 | Changelog README says add no fragment for an internal-only change | changelog.d/README.md | main | fcbde10e0c293390bd9df8d62a5d61f158eca384 | present | 58 |
| RC-18 | Spec template heading structure | .specify/templates/spec-template.md | main | 083ef123c7a2e56e21f3062173fb003258f927e2 | present | 1 |
| RC-19 | Plan template heading structure | .specify/templates/plan-template.md | main | 1a54553bd85cbef2178aa55efbeeb0c1942ffdde | present | 1 |
| RC-20 | Tasks template heading structure | .specify/templates/tasks-template.md | main | 7e5170324d41a6736c498d6b9fc83651f31d0778 | present | 6 |
| RC-21 | Checklist template heading structure | .specify/templates/checklist-template.md | main | 806657da09d1058823923e346a323b633114971a | present | 1 |
| RC-22 | Reference record spec has the Clarifications section | specs/numbered/0/0/1/2/4/1/4/0/4920-ex-hardware-inventory-csv/spec.md | main | 83b950279e45704943ad6942d23c8fc99cced492 | present | 11 |
| RC-23 | Process folder guard test file exists | tests/guardrails/test_process_folder_structure.py | main | f3b3f7f6853ff8652e44455f54e88cfd4d12b1f5 | present | 0 |
| RC-24 | Process folder baseline file exists | tests/guardrails/process_folder_baseline.json | main | f3eb8a7b6c62f3154ac6fa867a8948504818798b | present | 0 |
| RC-25 | Route leaf specs/numbered/0/0/1/2/2/0/2/0 is absent | specs/numbered/0/0/1/2/2/0/2/0 | main | not applicable | absent | 0 |
| RC-26 | Route level specs/numbered/0/0/1/2/2 holds children 1, 3, and 4 | specs/numbered/0/0/1/2/2 | main | not applicable | present | 0 |
| RC-27 | Containerfile copies src into the image | Containerfile | main | bc9249a19f6f181e7ea0e2c4b565a139d16d9253 | present | 127 |
| RC-28 | Build and Push Container workflow runs on pushes to main for listed paths | .github/workflows/container-build.yml | main | 737325976de75e90aa4526ab1cf2978782e648ce | present | 1 |
| RC-29 | Release Artifacts workflow runs on version tags | .github/workflows/release.yml | main | e81c05798c7609344d2d59b94114d7d9f76263be | present | 5 |
| RC-30 | Repository documents same-license attribution for another package | documentation/licensing-comparison-attribution.md | main | 16ab847a15c5ad25f666b5d89505ad4827c59e84 | present | 4 |
| RC-31 | PR 4596 body states that no release fragment is required | pull request 4596 body | main | not applicable | present | 0 |
| RC-32 | Parity task T002 requires G1 legal review | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 29 |
| RC-33 | Parity plan source license row says observation only and independent authorship | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/plan.md | main | 97960674f86e6c7c2e40f9b51cef5272e194a66f | present | 50 |
| RC-34 | Parity plan G1 Legal gate row | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/plan.md | main | 97960674f86e6c7c2e40f9b51cef5272e194a66f | present | 125 |
| RC-35 | Parity plan G4 Cloud owner gate row | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/plan.md | main | 97960674f86e6c7c2e40f9b51cef5272e194a66f | present | 128 |
| RC-36 | Parity spec FR-031 blocks reuse without legal and owner approval | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/spec.md | main | 8d160a44577d31ef88bbf87917026fcc524c5f2c | present | 137 |
| RC-37 | Parity analysis G1 finding rates the risk HIGH | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/analysis.md | main | a08601943e89b95af5ebe9530c0d8b9bb47459ab | present | 23 |
| RC-38 | Parity research cites source license link S8 | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md | main | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 51 |
| RC-39 | Parity research legal review checkbox is unchecked | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md | main | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 186 |
| RC-40 | Parity research states CC BY-NC 4.0 is not permission for unrestricted reuse | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/research.md | main | 34a4cbf7d6ea3390df8970191c292a04962aaa90 | present | 232 |
| RC-41 | Parity quickstart forbids reuse of source screenshots, assets, templates, prose, or styles | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/design/quickstart.md | main | 127f0f4d5f3f5819446592a681710d5d689aa047 | present | 111 |
| RC-42 | 4224 research: do not copy code, mappings, documentation text, or images | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/research.md | main | 50bc18526b0c29d782566a32d8fc50fe7975c5a0 | present | 39 |
| RC-43 | 4224 research: porting the source converter as-is is rejected before license approval | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/research.md | main | 50bc18526b0c29d782566a32d8fc50fe7975c5a0 | present | 49 |
| RC-44 | 4224 spec FR-015 forbids copying protected code, mappings, text, or assets | specs/numbered/0/0/1/1/3/3/4/4/4224-cisco-config-converter/spec.md | main | 5e8b1bc162cbfe2e9a3d604420c42e670dd0cd97 | present | 77 |
| RC-45 | Converter routes build a blueprint on main | src/interfaces/portals/cisco_config_converter/routes.py | main | 373138dcf471ce1ccb760ddb2b48ca284d161d1a | present | 51 |
| RC-46 | Converter presentation HTML exists on main | src/interfaces/portals/cisco_config_converter/presentation/converter.html | main | 270c3e40e226c026a54aef846f9b341d6a76eee9 | present | 0 |
| RC-47 | Converter presentation JavaScript exists on main | src/interfaces/portals/cisco_config_converter/presentation/converter.js | main | 9c7ad354600aade5b3a37bbd536ac49486edfd6e | present | 0 |
| RC-48 | PR 4226 merge commit exists on main | commit 14ac97942f1e575edd7dbf8c4bbfb517ef58fad3 | main | 14ac97942f1e575edd7dbf8c4bbfb517ef58fad3 | present | 0 |
| RC-49 | Pinned commit exists in the source and equals the default branch head | commits/d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c and commits/main of jmorrison-juniper/MistCiscoConfigConverter | main | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | present | 0 |
| RC-50 | Source license names CC BY-NC 4.0 | LICENSE of jmorrison-juniper/MistCiscoConfigConverter | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | e9ae5eff92457c2372db3be30a3d99166aeee547 | present | 1 |
| RC-51 | Source license copyright line names no holder | LICENSE of jmorrison-juniper/MistCiscoConfigConverter | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | e9ae5eff92457c2372db3be30a3d99166aeee547 | present | 3 |
| RC-52 | Source license states a NonCommercial term | LICENSE of jmorrison-juniper/MistCiscoConfigConverter | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | e9ae5eff92457c2372db3be30a3d99166aeee547 | present | 16 |
| RC-53 | Source mapping reference document exists | docs/CISCO_TO_MIST_MAPPING.md | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | dcc40aa14339a12e242fbfa0c76648342bf0859c | present | 0 |
| RC-54 | Source user guide exists | docs/USER_GUIDE.md | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | 4badf004a01b37bf75b6ca0c3539f07be85a8bbf | present | 0 |
| RC-55 | Source interface guide exists | docs/INTERFACE.md | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | 32eb81b906e39b85d29f82608dcbc1298c039e92 | present | 0 |
| RC-56 | Source screenshot landing.png exists | docs/screenshots/landing.png | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | be5ce6ddac31562b43aba684f6275934a6ef8536 | present | 0 |
| RC-57 | Source screenshot selection.png exists | docs/screenshots/selection.png | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | 4cbaa3b52849aeca38068bb1b881ff0e76746300 | present | 0 |
| RC-58 | Source screenshot proposal.png exists | docs/screenshots/proposal.png | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | 59da3f5ee87845378f5a2f95673fb89838f222d3 | present | 0 |
| RC-59 | Source screenshot config-review.png exists | docs/screenshots/config-review.png | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | 105aa4c46a46d07759857c9e857b429d6ff03e4a | present | 0 |
| RC-60 | Source stylesheet exists | static/css/themes.css | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | a19e59d2cfdf446a5e290e0520e4f2f850a1ddc3 | present | 0 |
| RC-61 | Source HTML template exists | templates/index.html | d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c | 3fd0e57946842ab5b1fc78fbafb7275954388efc | present | 0 |
| RC-62 | Source repository is public and its license key is other | repository metadata of jmorrison-juniper/MistCiscoConfigConverter | main | not applicable | present | 0 |
| RC-63 | MistHelper repository is public and its license key is other | repository metadata of jmorrison-juniper/MistHelper | main | not applicable | present | 0 |
| RC-64 | Issue 4635 is open, labeled needs-human-review, its body states it grants no legal approval, and an owner comment exists | issue 4635 metadata of jmorrison-juniper/MistHelper | main | not applicable | present | 0 |
| RC-65 | CC BY-NC 4.0 defines NonCommercial in Section 1 item 9 | https://creativecommons.org/licenses/by-nc/4.0/legalcode | fetched 2026-11-26 | not applicable | present | 0 |
| RC-66 | CC BY-NC-SA 4.0 defines the BY-NC-SA Compatible License and the ShareAlike condition in Section 3(b) | https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode | fetched 2026-11-26 | not applicable | present | 0 |
| RC-67 | Parity dependency table lists T002 as a prerequisite of T022, T028, and T033 | specs/live/0/0/0/1/2/1/3/3/2/1/4/2/1/4/1/3/0/20261105-170040-cisco-converter-full-parity/tasks.md | main | 810dc376034a1d9febce428bb2f9e73d74065f8f | present | 157 |
| RC-68 | Converter model file exists on main | src/interfaces/portals/cisco_config_converter/models.py | main | 815f4b6b45aa48680e0c72bd9edf598068ab5455 | present | 0 |
| RC-69 | Converter conversion file exists on main | src/interfaces/portals/cisco_config_converter/conversion.py | main | 2b9c4ceaee3c3d95d285e24293e70567df4ed537 | present | 0 |
| RC-70 | Converter package initializer exists on main | src/interfaces/portals/cisco_config_converter/__init__.py | main | 5e34b005c2ae54d3f2a766dd8ab0be7ceab40a7e | present | 0 |
| RC-71 | Converter integration test package initializer exists on main | tests/integration/web_portal/cisco_config_converter/__init__.py | main | 43a141c1406a21b339a111b3791274aa3eee784d | present | 0 |
| RC-72 | Converter integration route test exists on main | tests/integration/web_portal/cisco_config_converter/test_routes.py | main | a7ad7067ca7727ca5fad5508cc36de133b478d27 | present | 0 |
| RC-73 | Converter unit test exists under the marvis resources path on main | tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py | main | 31a84e3795665ebea1a9346fd835fffc619a9fe7 | present | 0 |
| RC-74 | Changelog rule: a change that a user sees adds one fragment | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 451 |
| RC-75 | Auto-merge workflow squash merges a labeled pull request after each required check passes | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 471 |
| RC-76 | Serial merge slot until the owner validates a merge queue | .github/copilot-instructions.md | main | f1ec2a4694d0bdfb05f0bc97c9a9cbe02913c179 | present | 485 |
| RC-77 | Quality gates document shows the Windows STE command from the repository virtual environment | documentation/quality-gates.md | main | 6776d334cca5d9b43273473a06da367a65605c6d | present | 283 |

## Source facts

- The source repository is public. Its owner account is jmorrison-juniper. Its license key is other (RC-62).
- The default branch head of the source equals the pinned commit d9be92f91e0f74fef711e9f7d30b59bf71ffdf4c (RC-49). The parity research cites the same commit in its S8 source link (RC-38).
- The source LICENSE file names CC BY-NC 4.0 at line 1 (RC-50). Line 3 reads "Copyright (c) 2026" with no holder (RC-51). Line 16 states the NonCommercial term (RC-52).
- The source contains a mapping reference document, two guides, four screenshots, one stylesheet, and one HTML template (RC-53 to RC-61).
- The PR 4226 merge commit is 14ac97942f1e575edd7dbf8c4bbfb517ef58fad3, dated 2026-10-26 (RC-48). The PR added the offline Cisco DNS converter to main.

## Related records

These drafts exist in the spec-drafts folder. They are context, not proof. Each one waits for issue 4635 or cites it.

- 4636 (state model): decision D-14 allows independent authorship only until issue 4635 records a legal decision (_meta/4636-STATUS.json line 48).
- 4644 (apply path): decision D-21 writes the apply path independently and holds release for gate G1 (4644/design/research.md line 68).
- 4645 (administration): gate G1 row names the issue 4635 decision and independent authorship only (4645/plan.md line 129).
- 4646 (restore): the plan requires the licensing decision before any reused source expression (4646/plan.md line 169).
- 4647 (visual journeys): legal review of source reuse stays with issue 4635 (4647/spec.md line 178). Provenance items PRV003 and PRV004 ask for an origin review before presentation files change.
- 4648 (privacy and portal): the owner of issue 4635 records the license basis (4648/analysis.md line 110).
- 4649 (evidence gaps): lists issue 4635 as a prerequisite (4649/analysis.md line 32).
- 4870 (backlog handoff): decision H-2 asks the owner to decide the licensing of issue 4635 first (_meta/4870-summary.md line 20).

## Sources

1. GitHub issue 4635, read 2026-11-26 with the gh issue view command. Comment IC_kwDOQltU8c8AAAABkIAecg has author association OWNER.
2. Pull request search for "4635" (gh pr list): no pull request.
3. Pull request search for "cisco" (gh pr list): PR 4596 merged 2026-11-13 (docs record). PR 4226 merged 2026-10-26 (offline Cisco DNS converter).
4. PR 4596 body (gh pr view 4596): states that no release fragment is required and that legal review remains open.
5. Issue states on 2026-11-26 (gh issue view): 4224 OPEN. 4632 CLOSED. 4633 CLOSED. 4634 OPEN. 4636 OPEN. 4643 OPEN. 4644 OPEN. 4645 OPEN. 4646 OPEN. 4647 OPEN. 4648 OPEN. 4649 OPEN. 4870 OPEN.
6. CC BY-NC 4.0 legal code, https://creativecommons.org/licenses/by-nc/4.0/legalcode, fetched 2026-11-26. Section 1 items 1 to 3 define Adapted Material, Adapter's License, and Copyright and Similar Rights. Item 9 defines NonCommercial.
7. CC BY-NC-SA 4.0 legal code, https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode, fetched 2026-11-26. Section 1 item 3 defines the BY-NC-SA Compatible License. Section 3(b)(1) requires the Adapter's License to use the same license elements, this version or later, or a BY-NC-SA Compatible License.
8. Local brief, spec-brief.md, sections 4 and 6. This instruction file is local context, not repository evidence.
9. Local working copy search for specs/**/4635-*: no match on 2026-11-26. The remote tree of main has no path that contains 4635. RC-25 covers the route leaf.
10. Mist API, OpenAPI files, and the mistapi SDK: not used. The record makes no claim about them.
11. Repository instructions, read in full on 2026-11-26: AGENTS.md, .github/copilot-instructions.md, and .specify/memory/constitution.md. The line numbers come from the remote decode in the RC rows.

## Unverified

- U-1: Whether any converter file on main holds protected source expression. Reason: No file comparison ran in this pass. Task T011 covers it.
- U-2: Whether the current container image holds the converter files. Reason: No image build and no image inspection ran. RC-27 shows that the Containerfile copies src.
- U-3: Who holds the copyright in the source. Reason: This is a legal question (D-1). RC-51 names no holder.
- U-4: Whether facts or mappings in the source are protected. Reason: This is a legal question (D-4).
- U-5: Whether the owner accepts the recommended options. Reason: The owner has not answered D-1 to D-7.
- U-6: Whether legal review exists and how long it takes. Reason: The evidence does not name a counsel or a date.
- U-7: The call path from the portal to the converter, and the bodies of the converter callers and tests. Reason: The issue names no code path, and the licensing decision does not depend on it. Task T011 reads the converter files.
