# Runbook Requirements Checklist: NOC runbook for the Juniper Mist to IBM Netcool alarm integration

**Purpose**: Test the quality of the runbook requirements. Each item asks about the requirement text, not the code.
**Created**: 2026-11-25
**Feature**: [spec.md](../../spec.md) and [plan.md](../../plan.md). The design files are in `design/`.

**Note**: Each checked item records an agent evaluation of the requirement text. The reviewer owns the final state of each item.

## Document outline and structure

- [x] CHK001 - Does FR-001 name one Markdown file for the runbook? [Completeness, Spec FR-001]
  - Result: Met. spec.md FR-001 names the file path and requires one self-contained Markdown file.
- [x] CHK002 - Does FR-002 fix the H1 title and the order of the 20 H2 headings? [Completeness, Spec FR-002]
  - Result: Met. spec.md FR-002 lists each heading in order. design/contracts/runbook-structure.md sections 1 and 2 give the exact strings.
- [ ] CHK003 - Does FR-001 define self-contained for the runbook file? [Clarity, Spec FR-001, FR-027]
  - Result: Not met. FR-027 requires links to per-alarm runbooks, but no requirement states which other links the file can hold.
- [x] CHK004 - Does FR-002 place the table of contents and state the anchor rule? [Completeness, Spec FR-002, SC-002]
  - Result: Met. spec.md FR-002 places the contents list after the Overview table. design/contracts/runbook-structure.md section 4 gives the three-step anchor rule.
- [ ] CHK005 - Does FR-002 define the content of Appendix D and Appendix E? [Ambiguity, Spec FR-002]
  - Result: Not met. The revised design defines Appendix D as a glossary and Appendix E as a revision table. The spec, FR-002, still gives Not applicable for both appendices. The spec must change.
- [ ] CHK006 - Does FR-002 name the live catalog that decides whether Appendix B.4 appears? [Clarity, Spec FR-002]
  - Result: Not met. The revised design names the live system event catalog as the test for Appendix B.4. The spec, FR-002, still says a live catalog. The spec must change.
- [ ] CHK007 - Does a requirement set the offline test result for Appendix B.4? [Ambiguity, Spec FR-049, FR-052]
  - Result: Not met. FR-049 forbids network access, so the offline test cannot read the live catalog. The revised design accepts Appendix B.4 present or absent in the offline test. spec.md must state this rule.
- [x] CHK008 - Does the design map each Appendix B table to one catalog? [Completeness, Spec FR-002]
  - Result: Met in design. design/contracts/runbook-structure.md section 8 maps tables B.1 to B.5 to five catalog keys. spec.md FR-002 names the tables only.
- [x] CHK009 - Does FR-002 name the columns of each Appendix A table? [Completeness, Spec FR-002]
  - Result: Met. spec.md FR-002 names the five columns. design/contracts/runbook-structure.md section 7 gives the exact header row.
- [x] CHK010 - Does the design define the rows of each endpoint family table? [Completeness, Spec FR-002]
  - Result: Met in design. design/contracts/runbook-structure.md section 6 lists eleven row labels for sections 6.1 to 6.4.
- [ ] CHK011 - Does FR-002 define the content of the clear and recovery matrix? [Clarity, Spec FR-002, FR-013]
  - Result: Not met. FR-002 names the matrix only. No file gives its rows, its columns, or the condition for a clear.
- [ ] CHK012 - Does FR-052 check the heading order that FR-002 requires? [Consistency, Spec FR-002, FR-052]
  - Result: Not met. FR-002 requires the same order. FR-052 checks only that each heading exists, and runbook-structure.md section 11 also checks existence only. The revised design requires the heading order in the offline test, so FR-052 and the contract must change.
- [ ] CHK013 - Does FR-050 check each Mist API path in the runbook, or only the Appendix A paths? [Consistency, Spec FR-050]
  - Result: Not met. FR-050 covers each Mist API path in the runbook. The file runbook-structure.md, section 10, rule 5, reads only the Appendix A rows as paths. The contract must change. The revised design checks each path anywhere in the runbook.

## Verification marks

- [x] CHK014 - Does FR-003 name the six verification marks and their meanings? [Completeness, Spec FR-003]
  - Result: Met. spec.md FR-003 lists the six marks and their meanings. design/contracts/runbook-structure.md section 3 gives the exact strings.
- [x] CHK015 - Does FR-003 tie the Verified (live) mark to a dated run? [Clarity, Spec FR-003, FR-028]
  - Result: Met. spec.md FR-003 ties the mark to the date in Section 13. FR-028 requires that date in UTC ISO 8601 form.
- [ ] CHK016 - Does FR-004 define a technical claim so that a reviewer can count the claims? [Measurability, Spec FR-004]
  - Result: Not met. FR-004 requires one mark for each technical claim. No requirement defines a claim or lists the claims for review.
- [ ] CHK017 - Does a requirement map each research mark to one of the six runbook marks? [Consistency, Spec FR-003, FR-004]
  - Result: Not met. design/research.md uses three marks that FR-003 does not list: Pending live verification, Pending Netcool administrator confirmation, and Open, confirm with Mist. No rule maps them to the runbook marks.

## Integration team questions

- [x] CHK018 - Does FR-005 list the six questions with the required content of each answer? [Completeness, Spec FR-005]
  - Result: Met. spec.md FR-005 lists six questions. Each question has one row with its required answer content.
- [ ] CHK019 - Does a requirement name an answer source for each Question 1 attribute of system events? [Gap, Spec FR-005]
  - Result: Not met. design/research.md D9 leaves the meaning of each system event type to the live catalog. FR-003 has no mark for an answer that waits for live data.
- [x] CHK020 - Does FR-005 list each diagnostic step for Question 4 and Question 6? [Completeness, Spec FR-005]
  - Result: Met. spec.md FR-005 lists twelve steps for Question 4 and ten steps for Question 6.
- [ ] CHK021 - Does a requirement define acceptable for one AP Warning report run each hour? [Measurability, Spec FR-005, FR-006]
  - Result: Not met. FR-005 Question 2 asks whether one hourly run is acceptable. No criterion defines acceptable. FR-006 lists the hourly run as a proposal only.
- [ ] CHK022 - Does a requirement give the keys that map AP Warning report rows to Netcool events? [Completeness, Spec FR-005]
  - Result: Not met. data-model.md section 6.1 gives deduplication key shapes for four families only. No shape or clear key covers the rows of menu 307.
- [ ] CHK023 - Does a requirement define concurrency and the maximum collection time for site queries? [Completeness, Spec FR-005]
  - Result: Not met. FR-005 Question 3 names both topics. No requirement or design file gives a value, a method, or a limit for either topic.
- [ ] CHK024 - Does a requirement define the clear mapping and the rule for informational device events? [Clarity, Spec FR-005]
  - Result: Not met. FR-005 Question 5 names both topics. data-model.md section 6 sets the state of device events to unknown and does not define either topic.

## Collection rules

- [x] CHK025 - Does FR-006 mark the five-minute poll and the hourly report as proposals? [Clarity, Spec FR-006]
  - Result: Met. spec.md FR-006 marks both items as proposals and names REST polling as the baseline.
- [ ] CHK026 - Does FR-007 quantify a short time for the window end lag? [Clarity, Spec FR-007]
  - Result: Not met. FR-007 says a short time. FR-008 moves the value to the runbook. design/research.md D3 gives 2 minutes, but spec.md gives no value.
- [x] CHK027 - Does FR-008 require the window end lag and the overlap as values with a mark? [Completeness, Spec FR-008]
  - Result: Met. spec.md FR-008 requires both values. design/data-model.md section 3 gives 2 minutes and 5 minutes, both as proposals.
- [x] CHK028 - Does FR-009 forbid an assumption that a larger page size is valid? [Clarity, Spec FR-009]
  - Result: Met. spec.md FR-009 requires limit=1000 and forbids any assumption of a larger page size.
- [x] CHK029 - Does FR-010 define the format of a type filter value? [Clarity, Spec FR-010]
  - Result: Met. spec.md FR-010 requires a comma-separated list with no spaces, brackets, or quotes.
- [x] CHK030 - Does FR-011 require a check of the HTTP status and the error body for each call? [Completeness, Spec FR-011]
  - Result: Met. spec.md FR-011 requires both checks. It also states that an empty SDK list is not proof of success.
- [x] CHK031 - Does FR-012 define the meaning of each of the nine collection result states? [Clarity, Spec FR-012]
  - Result: Met. spec.md FR-012 gives a meaning for each of the nine states in its table.
- [ ] CHK032 - Does a requirement define the retry limit behind FAILED_HTTP for the collector? [Clarity, Spec FR-012]
  - Result: Not met. FR-012 says after the allowed retries. The Assumptions set retries for the smoke test only. No collector retry rule exists.
- [ ] CHK033 - Does a requirement define a collection result state for a request timeout? [Coverage, Spec FR-012]
  - Result: Not met. FAILED_HTTP covers HTTP statuses and connection failures. No state covers a timeout in spec.md FR-012 or in data-model.md section 5.
- [ ] CHK034 - Does a requirement name the pagination metadata that FAILED_INCOMPLETE_PAGINATION uses? [Clarity, Spec FR-012]
  - Result: Not met. FR-012 names missing pagination metadata as a cause. No requirement names the fields that carry that metadata.
- [ ] CHK035 - Does a requirement define the durable buffer that FAILED_DELIVERY and FR-017 use? [Clarity, Spec FR-012, FR-017]
  - Result: Not met. FR-012 and FR-017 name a durable buffer. No file defines what the buffer stores or how long it keeps each record.
- [x] CHK036 - Does FR-013 state that an empty result does not clear an open alarm? [Completeness, Spec FR-013]
  - Result: Met. spec.md FR-013 states the rule. The edge case for zero alarms repeats it.
- [ ] CHK037 - Does a requirement define the parse state that FR-014 resets for each event? [Clarity, Spec FR-014]
  - Result: Not met. FR-014 names a parse state. No file defines it. data-model.md sections 5 and 6 repeat the rule without a definition.
- [ ] CHK038 - Does a requirement define the environment file for each scheduled job? [Clarity, Spec FR-015]
  - Result: Not met. FR-015 requires each scheduled job to name its environment file. No file gives the format, the location, or the naming rule for that file.
- [x] CHK039 - Does the design define the checkpoint rule during replay? [Completeness, Spec FR-002]
  - Result: Met in design. design/data-model.md section 4 states that a checkpoint never moves to an earlier time, including during replay.
- [ ] CHK040 - Does a requirement define the restart behavior of the collector? [Completeness, Spec FR-002]
  - Result: Not met. FR-002 requires restart content in Section 8. No requirement or design file defines the restart behavior.
- [x] CHK041 - Does the design define the rate-limit sizing rule for the collector? [Completeness, Spec FR-002]
  - Result: Met in design. design/research.md D5 gives the formula `R_hour = 12 times C, plus O` for a five-minute poll.

## Netcool proposals

- [x] CHK042 - Does FR-016 list each Netcool item that carries the Proposal mark? [Completeness, Spec FR-016]
  - Result: Met. spec.md FR-016 lists seven items, from the delivery path to delivery reliability.
- [x] CHK043 - Does FR-016 state that the runbook names no Netcool receiver? [Clarity, Spec FR-016]
  - Result: Met. spec.md FR-016 states that the runbook names no receiver and that the Netcool administrator selects one.
- [ ] CHK044 - Does a requirement resolve the mark for a Netcool item that is also an IBM fact? [Conflict, Spec FR-004, FR-016]
  - Result: Not met. FR-016 marks each Netcool item as a proposal, and it marks each IBM fact as verified. design/research.md D11 splits the two by item type. No requirement states that split.
- [ ] CHK045 - Does a requirement define the severity mapping from Mist values to Netcool values? [Completeness, Spec FR-002]
  - Result: Not met. FR-002 requires a severity mapping. data-model.md section 7 refers to a severity table, but no file gives its rows.
- [x] CHK046 - Does the design define the field mapping for the normalized record and the Netcool event? [Completeness, Spec FR-002]
  - Result: Met in design. design/data-model.md sections 6 and 7 give the record fields and the proposed Netcool fields.
- [ ] CHK047 - Does a requirement name the source field of the explicit clear for each family? [Clarity, Spec FR-013]
  - Result: Not met. data-model.md section 7 says a resolution follows an explicit clear. It does not name the source field of that clear for each family.
- [ ] CHK048 - Does FR-017 define how a reviewer verifies each receiver capability? [Measurability, Spec FR-017]
  - Result: Not met. FR-017 names durable delivery, retry, replay, and reconciliation. It does not state how a reviewer verifies that a receiver provides them.
- [x] CHK049 - Does FR-018 require a separate approval for each enhancement? [Completeness, Spec FR-018]
  - Result: Met. spec.md FR-018 requires separate approval for correlation, automatic clear, and the hybrid design. FR-020 names the change approver.
- [x] CHK050 - Does the requirement mark correlation and automatic clear as enhancements? [Completeness, Spec FR-018]
  - Result: Met. spec.md FR-018 and the Out of Scope section mark both items as enhancements.

## Scope and device classes

- [ ] CHK051 - Does FR-019 use the device class names of the Mist API? [Consistency, Spec FR-019, FR-025]
  - Result: Not met. FR-019 names routers. design/contracts/smoke-cli.md section 5.10 uses the Mist types ap, switch, and gateway. The spec does not map routers to gateways.
- [ ] CHK052 - Does a requirement name the default device classes in scope? [Completeness, Spec FR-019]
  - Result: Not met. FR-019 lets the owners choose the classes but names no default. design/research.md D7 sends `device_type=ap`, and no requirement states that as the scope.

## Roles and naming rules

- [x] CHK053 - Does FR-020 define each of the seven roles with its duties? [Completeness, Spec FR-020]
  - Result: Met. spec.md FR-020 lists seven roles and their duties.
- [x] CHK054 - Does FR-021 limit the named person to the author? [Clarity, Spec FR-021]
  - Result: Met. spec.md FR-021 names only the author, Joseph Morrison, and names no customer.
- [ ] CHK055 - Does FR-022 cover each product name that FR-016 uses? [Consistency, Spec FR-016, FR-022]
  - Result: Not met. FR-016 cites IBM documentation. FR-022 names IBM Netcool but not the vendor name alone. The list does not state whether the vendor name is allowed.
- [x] CHK056 - Does FR-023 give generic terms for the other products? [Clarity, Spec FR-023]
  - Result: Met. spec.md FR-023 gives two generic terms as examples: the legacy event manager and another monitoring tool.
- [ ] CHK057 - Does FR-024 list each placeholder that the design uses for an identifier? [Consistency, Spec FR-024]
  - Result: Not met. FR-024 and runbook-structure.md section 9 allow five placeholders. data-model.md section 6.1 uses `{event_id}` and `{mxedge_id}`, which the list omits.
- [ ] CHK058 - Does the spec use one term for each concept, such as time window and collection window? [Consistency, Spec FR-025]
  - Result: Not met. FR-005 and User Story 1 use time window. Key Entities uses collection window for the same concept. FR-025 requires one term for each concept.
- [x] CHK059 - Does FR-025 forbid the word store for the site concept? [Clarity, Spec FR-025]
  - Result: Met. spec.md FR-025 requires the word site and forbids the word store.
- [x] CHK060 - Does FR-026 define the form of each safety statement? [Completeness, Spec FR-026]
  - Result: Met. spec.md FR-026 requires the word Warning or Caution at the start, and the consequence in each statement.
- [x] CHK061 - Does the design define the writing rules for the runbook prose? [Traceability, Spec SC-001]
  - Result: Met in design. design/research.md D15 lists the writing rules and cites AGENTS.md. spec.md SC-001 sets the score.

## Alarm handling links

- [ ] CHK062 - Does FR-027 define the location and form of each per-alarm runbook link? [Clarity, Spec FR-027]
  - Result: Not met. FR-027 refers to a per-alarm runbook. No requirement states where those runbooks are kept or how the procedure links to them.
- [ ] CHK063 - Does FR-027 define the procedure for an alarm type that has no per-alarm runbook? [Coverage, Spec FR-027]
  - Result: Not met. FR-027 applies only when the runbook exists. No requirement gives a fallback for an alarm type without one.

## Live record and open decisions

- [x] CHK064 - Does FR-028 limit the committed record to statuses, field names, catalog names, and catalog sizes? [Clarity, Spec FR-028]
  - Result: Met. spec.md FR-028 uses an exhaustive list, and it excludes identifiers and organization data volume.
- [ ] CHK065 - Does a requirement define the layout of the live verification record in Section 13? [Completeness, Spec FR-028]
  - Result: Not met. FR-002 and runbook-structure.md section 2 name Section 13. No requirement gives its subsections, tables, or fields.
- [x] CHK066 - Does FR-029 require an owner role for each open decision? [Completeness, Spec FR-029]
  - Result: Met. spec.md FR-029 requires an owner role for each open decision in Section 15. FR-003 defines the Open decision mark.
- [ ] CHK067 - Does a requirement list the open decisions that Section 15 must hold? [Completeness, Spec FR-029]
  - Result: Not met. FR-029 names only the token layout. design/research.md names more items for owner or Mist confirmation. For example, the redelivery rule in D1 and the signature encoding in D12 need confirmation.

## Measurability of success criteria

- [x] CHK068 - Does SC-001 define a score that a reviewer can measure in both modes? [Measurability, Spec SC-001]
  - Result: Met. spec.md SC-001 sets a score of 80 or more in both modes. design/quickstart.md section 4 gives both commands.
- [x] CHK069 - Does SC-002 define the link and anchor checks with a rule or a tool? [Measurability, Spec SC-002]
  - Result: Met. design/contracts/runbook-structure.md section 4 gives the anchor rule. design/quickstart.md section 4 names the link check.
- [ ] CHK070 - Does SC-003 test the same condition as FR-050 and runbook-structure.md? [Consistency, Spec SC-003]
  - Result: Not met. SC-003 requires that each path exists in the file. The revised design requires a GET operation at each path for SC-003 and FR-050, as runbook-structure.md section 11 does. spec.md SC-003 must change.
- [ ] CHK071 - Does SC-004 define the run result that shows the catalog names? [Measurability, Spec SC-004]
  - Result: Not met. The revised design requires SMK-05 to run and report PASS for each Appendix B name. A run that stops before SMK-05 does not satisfy SC-004. spec.md SC-004 must state this rule.
- [ ] CHK072 - Does SC-006 define customer identifier so that the offline scan can test it? [Measurability, Spec SC-006, FR-051]
  - Result: Not met. SC-006 uses the term customer identifier. The revised design defines the term by identifier class. The offline scan checks the four pattern classes, and a name scan runs outside the offline test. spec.md SC-006 must cite the definition.
- [ ] CHK073 - Does a requirement map each of the six questions to a runbook section? [Traceability, Spec SC-009]
  - Result: Not met. SC-009 requires an answer section for each question. No requirement or design file names the section for each question.

## Edge cases that affect runbook text

- [ ] CHK074 - Does a requirement name the section that gives the host check and the network checks? [Traceability, Spec Edge Cases]
  - Result: Not met. The edge cases for a wrong regional host and a connection failure say the runbook gives these checks. No outline row names the section.
- [x] CHK075 - Does FR-038 require the runbook to state that the SDK can sleep for the full Retry-After value? [Completeness, Spec FR-038]
  - Result: Met. spec.md FR-038 requires the statement. design/quickstart.md section 5 contains it.
- [x] CHK076 - Does the spec give the zero-result procedure and the rule for an empty result? [Completeness, Spec Edge Cases]
  - Result: Met. spec.md FR-005 Question 4 gives the procedure. The zero-records edge case and FR-013 give the empty-result rule.
- [x] CHK077 - Does the spec list the causes for HTTP 403 and HTTP 404 responses? [Completeness, Spec Edge Cases]
  - Result: Met. spec.md edge cases name the token scope check for HTTP 403, and a wrong organization identifier or a wrong path for HTTP 404.
- [x] CHK078 - Does the spec define the correction step for a catalog name that the live catalog lacks? [Coverage, Spec Edge Cases]
  - Result: Met. The spec.md edge case says the integration engineer corrects the runbook before any team uses the Verified (live) mark.
- [x] CHK079 - Does the spec define the error for a runbook that lacks a required section? [Coverage, Spec Edge Cases]
  - Result: Met. The spec.md edge case says the test returns an error that names the missing heading. design/contracts/smoke-cli.md section 5.2 gives FAIL and names each missing value.

## Notes

- Mark each completed item with `[x]`.
- Add a comment or a finding in the item note.
- Add a link to each resource or document that a note cites.
- Item numbers increase by one, for easy reference.
- Each checked item records an agent evaluation. The reviewer owns the final state and must confirm each checked item.
- Item IDs in this file start at CHK001. The file `security.md` in this folder has its own IDs.
