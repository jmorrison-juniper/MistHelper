# Security and Safety Requirements Checklist: NOC runbook for the Juniper Mist to IBM Netcool alarm integration

**Purpose**: Test the quality of the security and safety requirements for the smoke test and the runbook. Each item asks about the requirement text, not the code.
**Created**: 2026-11-25
**Feature**: [spec.md](../../spec.md) and [plan.md](../../plan.md). The design files are in `design/`.

**Note**: Each checked item records an agent evaluation of the requirement text. The reviewer owns the final state of each item.

## GET-only requests and the request budget

- [x] CHK001 - Does FR-030 limit the smoke test to the GET method? [Completeness, Spec FR-030]
  - Result: Met. spec.md FR-030 names GET as the only method. design/contracts/smoke-cli.md section 7 gives the client no other method.
- [ ] CHK002 - Does a requirement verify that each SDK call of the smoke test sends GET only? [Coverage, Spec FR-030, SC-005]
  - Result: Not met. The contract evidence in spec.md has no GET-only test. The offline test checks paths and names, not the HTTP method of each SDK call.
- [ ] CHK003 - Does SC-005 define the count that a run must not exceed? [Measurability, Spec SC-005, FR-034]
  - Result: Not met. SC-005 says no run exceeds its budget. FR-034 says the count can omit SDK retries, so actual requests can exceed the budget while the count stays at 60.
- [ ] CHK004 - Does a requirement state whether the login validation request counts against the budget? [Conflict, Spec FR-034]
  - Result: Not met. FR-034 says each attempt counts. The revised design counts the login validation as one request. design/contracts/smoke-cli.md section 6 still excludes the SDK login request, so the contract must change.
- [ ] CHK005 - Does a requirement bound the SDK retries that the request count can omit? [Measurability, Spec FR-034, FR-038]
  - Result: Not met. FR-038 sets three SDK retries for HTTP 429 only. No requirement states whether the SDK retries other responses.
- [x] CHK006 - Does a requirement set the default request budget and an owner option to change it? [Completeness, Spec FR-034]
  - Result: Met. spec.md FR-034 and the Assumptions set 60 requests. design/contracts/smoke-cli.md section 1 names the --max-requests option.
- [x] CHK007 - Does FR-033 limit the limit=5000 request to one request? [Clarity, Spec FR-033]
  - Result: Met. spec.md FR-033 names the SMK-09 probe as the only request above 1000. design/contracts/smoke-cli.md section 5.9 lists one such request.
- [ ] CHK008 - Does a requirement record the owner approval for the limit=5000 exception? [Traceability, Spec FR-033]
  - Result: Not met. FR-033 makes an explicit exception to limit=1000. No assumption or open decision records an owner approval. design/research.md D4 cites the owner rule.
- [x] CHK009 - Does FR-035 stop a query at the page ceiling and continue the run? [Completeness, Spec FR-035]
  - Result: Met. spec.md FR-035 requires the stop and the continuation. The page ceiling edge case gives WARN and the PageCeiling reason.

## Approved origin and paging

- [x] CHK010 - Does FR-031 name the approved origin as the regional host with https? [Clarity, Spec FR-031]
  - Result: Met. spec.md FR-031 names https://{api_host}. design/contracts/smoke-cli.md section 2 gives the approved origin of each run.
- [ ] CHK011 - Does a requirement define origin with scheme, host, and port? [Clarity, Spec FR-031, FR-036]
  - Result: Not met. No requirement defines origin. The revised design sets the origin as the HTTPS scheme, the approved host, and port 443 or no port. The contract, design/contracts/smoke-cli.md section 6, checks only the scheme and the host. The contract must change.
- [ ] CHK012 - Does a requirement name one source for the valid regional hosts? [Conflict, Spec SMK-01]
  - Result: Not met. SMK-01 uses a regional host table. smoke-cli.md section 2 uses the OpenAPI server list. It says that the runbook gives no list. runbook-structure.md section 5.5 gives 12 hosts.
- [x] CHK013 - Does FR-036 require a check of each next link before a request? [Completeness, Spec FR-036]
  - Result: Met. spec.md FR-036 requires the check. design/contracts/smoke-cli.md section 6 gives the accepted forms of a next value.
- [ ] CHK014 - Does a requirement limit the path of a relative next value? [Coverage, Spec FR-036]
  - Result: Not met. The revised design rejects a relative path with a `..` segment, a backslash, or `//` at its start. The contract, design/contracts/smoke-cli.md section 6, accepts any relative path that starts with /api/v1/. The contract must change. The file design/research.md, decision D4, requires a path check that the contract omits.
- [ ] CHK015 - Does FR-037 define a repeated page so that a test can detect it? [Clarity, Spec FR-037]
  - Result: Not met. FR-037 says a page that the run already read. The revised design also counts a page whose results hash matches an earlier page of the same query. The contract, design/contracts/smoke-cli.md section 6, defines a repeat only as the same next value. The contract must change.

## Token source and secret handling

- [x] CHK016 - Does FR-032 limit the token source to an environment variable or an ignored file? [Completeness, Spec FR-032]
  - Result: Met. spec.md FR-032 names both sources and bars a command-line token. smoke-cli.md section 1 accepts no token option.
- [x] CHK017 - Does a requirement name the token variables and the conflict rule? [Clarity, Spec FR-032, SMK-01]
  - Result: Met. smoke-cli.md section 2 names MIST_API_TOKEN and MIST_APITOKEN, gives the process environment precedence, and sets exit code 2 for a conflict.
- [ ] CHK018 - Does a requirement make the smoke test confirm that the env file is ignored by Git? [Gap, Spec FR-032]
  - Result: Not met. FR-032 requires an ignored file, but no requirement makes the smoke test check the ignore rule. The revised design accepts an env file path only outside the repository, or the path `<root>/.env`. The contract, design/contracts/smoke-cli.md section 1, accepts any --env-file path. The contract must change.
- [ ] CHK019 - Does a requirement limit the --output path to the ignored evidence folder? [Gap, Spec FR-042]
  - Result: Not met. FR-042 requires evidence under test-artifacts. The revised design accepts an --output path only under test-artifacts, and it gives exit code 2 for any other path. The contract, design/contracts/smoke-cli.md section 1, accepts any --output path. The contract must change.
- [ ] CHK020 - Does a requirement define redaction for the log records of the SDK? [Gap, Spec FR-044]
  - Result: Not met. FR-044 redacts tokens at the logging boundary. design/research.md D13 says the SDK logs response bodies at debug level. No requirement says whether SDK records pass that boundary.
- [x] CHK021 - Does the design redact secret values beyond the token? [Completeness, Spec FR-044]
  - Result: Met in design. evidence.md section 7 removes organization and site identifiers. It also removes MAC addresses and email addresses. smoke-cli.md section 5.10 omits webhook URLs, names, and secrets.
- [x] CHK022 - Does the design define the token-like pattern for redaction? [Clarity, Spec FR-044]
  - Result: Met in design. evidence.md section 7 first replaces each token value, then each string of 32 or more letters and digits.
- [ ] CHK023 - Does a requirement define the approved secret store and the token rotation interval? [Completeness, Spec FR-020, FR-002]
  - Result: Not met. FR-020 gives the Security owner the rotation policy, and FR-002 requires token rotation. No requirement names the secret store or the interval.

## Redaction and evidence content

- [x] CHK024 - Does FR-042 define the content of the evidence record? [Completeness, Spec FR-042]
  - Result: Met. spec.md FR-042 names check names, statuses, counts, and UTC timestamps. design/contracts/evidence.md section 1 lists the top-level keys.
- [x] CHK025 - Does FR-043 require an operator label in place of the organization identifier? [Clarity, Spec FR-043]
  - Result: Met. spec.md FR-043 requires the label. evidence.md sections 1 and 7 use org-1.
- [x] CHK026 - Does the design allow only listed keys in the evidence record? [Coverage, Spec FR-042, FR-043]
  - Result: Met in design. evidence.md states that the writer copies no HTTP response and keeps only the listed keys.
- [ ] CHK027 - Does a requirement state the evidence content for an HTTP 400 response body? [Conflict, Spec Edge Cases]
  - Result: Not met. The HTTP 400 edge case says the record holds the redacted error body. The revised design keeps at most 200 characters of the redacted error text, and it copies no other response body. The edge case and design/contracts/evidence.md section 7 must state this rule.
- [x] CHK028 - Does a requirement write the evidence record before each exit? [Completeness, Spec Contract Evidence]
  - Result: Met. spec.md names a Failure safety test for the evidence record. smoke-cli.md section 9 requires the write before each exit.
- [ ] CHK029 - Does FR-045 cover a failed write of the evidence record? [Conflict, Spec FR-045]
  - Result: Not met. The contract, design/contracts/smoke-cli.md section 9, gives exit code 2 for a failed write. The revised design lists the same case in exit code 2. FR-045 lists no write failure in the configuration error class, so FR-045 must change.

## Identifiers in output

- [x] CHK030 - Does a requirement print placeholders for the organization and the site in output and logs? [Completeness, Spec FR-043]
  - Result: Met in design. smoke-cli.md sections 4 and 8 print org-1 and site-1 and use placeholders in path labels.
- [x] CHK031 - Does a requirement limit the webhook data that the smoke test reads? [Coverage, Spec SMK-10]
  - Result: Met. spec.md SMK-10 records only the count, the topics, and the enabled flags of webhooks.

## Warning and Caution statements

- [ ] CHK032 - Does FR-026 define when a safety statement uses Warning or Caution? [Clarity, Spec FR-026]
  - Result: Not met. FR-026 requires one of the two words. No requirement states the irreversible or recoverable rule. AGENTS.md has the rule, but no requirement refers to it.
- [x] CHK033 - Does FR-044 give a Warning with its consequence? [Completeness, Spec FR-044]
  - Result: Met. spec.md FR-044 has a Warning that names unauthorized access to the Mist organization.
- [x] CHK034 - Does the spec give a Caution with its consequence for the shared token? [Completeness, Spec FR-048]
  - Result: Met. spec.md places a Caution after FR-048. The Caution names the slowdown of other jobs that use the same token.
- [ ] CHK035 - Does a requirement require the runbook to state the authentication and TLS needs of the Netcool receiver? [Gap, Spec FR-016]
  - Result: Not met. design/research.md D11 gives a Caution about the probe interface. No requirement makes the runbook state this need.
- [ ] CHK036 - Does a requirement require the runbook to state the webhook signature check and its encoding? [Gap, Spec FR-002]
  - Result: Not met. FR-002 requires a webhook check in Section 11. design/research.md D12 leaves the signature encoding open. No requirement defines the verification steps.

## Rate-limit protection

- [x] CHK037 - Does FR-038 define the rate-limit threshold? [Measurability, Spec FR-038, SMK-04]
  - Result: Met. spec.md FR-038 and SMK-04 stop the run when the remaining requests are fewer than twice the budget.
- [ ] CHK038 - Does a requirement define the SMK-04 result when the usage request fails? [Coverage, Spec FR-038]
  - Result: Not met. Neither FR-038 nor SMK-04 defines the result of an error or a timeout on the usage request.
- [ ] CHK039 - Does a requirement say whether the usage check repeats during the run? [Clarity, Spec FR-038]
  - Result: Not met. FR-038 reads usage before the search checks. No requirement says whether a later usage check runs.
- [ ] CHK040 - Does a requirement define the unit and format of the Retry-After value? [Clarity, Spec FR-038]
  - Result: Not met. The spec gives no unit. design/research.md D5 leaves the unit pending live verification. The HTTP-date form of the header is not addressed.
- [ ] CHK041 - Does a requirement define the result when a Retry-After wait exceeds the call timeout? [Conflict, Spec FR-038]
  - Result: Not met. smoke-cli.md section 6 lets the SDK sleep for the full Retry-After value, and the client waits at most the call timeout. The revised design gives a Timeout no retry, and the second Timeout in one run stops the run with exit code 3. The contract must state this rule.
- [x] CHK042 - Does a requirement set two retries for HTTP 5xx and connection failures? [Completeness, Spec Assumptions]
  - Result: Met. spec.md Assumptions set at most two retries. The Timeout edge case sets a default of 30 seconds.

## Exit codes and stops

- [ ] CHK043 - Does FR-045 define seven outcome classes with exit codes 0 to 6? [Completeness, Spec FR-045]
  - Result: Not met. The revised design adds exit code 6 for an unexpected internal error. The spec, FR-045, and the contract, smoke-cli.md section 3, still list six classes with exit codes 0 to 5. The reviewer checks this item again after the update.
- [x] CHK044 - Does the design give a stop priority over a check failure? [Clarity, Spec FR-045]
  - Result: Met in design. smoke-cli.md section 3 states that the first stop ends the run and that a stop has priority over a check failure.
- [ ] CHK045 - Does a requirement map a connection failure during token validation to an exit code? [Conflict, Spec Edge Cases]
  - Result: Not met. The wrong-host edge case records the connection error and gives no code. The plan.md file, in assumption A1, says the edge case supports exit code 2. The research.md file, in decision D13, says the spec does not state that mapping.
- [ ] CHK046 - Does a requirement give one rule for a missing runbook or spec file? [Conflict, Spec Edge Cases]
  - Result: Not met. The edge case says the test returns an error. smoke-cli.md section 5.2 gives SKIP when the default runbook file is missing.
- [ ] CHK047 - Does a requirement define an exit code for an unexpected internal error? [Gap, Spec FR-045]
  - Result: Not met. The revised design gives exit code 6 for an unexpected exception. spec.md FR-045 and smoke-cli.md section 3 do not list that code yet. Until then, an unhandled exception returns the default Python exit code 1, which the contract defines as Check failure.
- [ ] CHK048 - Does a requirement count only the checks that ran as examined, with SKIP results in a separate count? [Conflict, Spec FR-046, SC-010]
  - Result: Not met. FR-046 counts checks examined. The revised design counts only the checks that ran, and it reports SKIP results in a separate count. The contract, design/contracts/smoke-cli.md section 4, still counts each SKIP result as examined. The contract must change.
- [x] CHK049 - Does FR-046 require the count on every run, including failed runs? [Coverage, Spec FR-046, SC-010]
  - Result: Met. spec.md FR-046 and SC-010 require the count on every run, including failed runs.
- [x] CHK050 - Does FR-045 map HTTP 401 at any call to exit code 2? [Completeness, Spec FR-045]
  - Result: Met. spec.md FR-045 and the HTTP 401 edge case map the rejected token to exit code 2, at login and at any call.
- [x] CHK051 - Does FR-045 map a final HTTP 429 response and a low remainder to exit code 3? [Completeness, Spec FR-045]
  - Result: Met. spec.md FR-045 names exit code 3 for both triggers.
- [x] CHK052 - Does FR-045 map the budget stop and the paging stops to exit codes 4 and 5? [Completeness, Spec FR-045]
  - Result: Met. spec.md FR-045 names exit code 4 for the budget and exit code 5 for a foreign origin or a repeated page.
- [x] CHK053 - Does FR-045 state that a page ceiling is not a stop? [Clarity, Spec FR-045]
  - Result: Met. spec.md FR-045 states that the page ceiling is not a stop condition.

## Offline privacy scan

- [x] CHK054 - Does FR-049 forbid a token and network access for the offline test? [Completeness, Spec FR-049]
  - Result: Met. spec.md FR-049 forbids both. design/research.md D14 reads the source files without network access.
- [x] CHK055 - Does FR-050 name the specification file for the path comparison? [Clarity, Spec FR-050]
  - Result: Met in design. smoke-cli.md section 1 names documentation/mist-api-openapi31json.json as the default specification file.
- [ ] CHK056 - Does FR-051 define the token pattern that the privacy scan uses? [Clarity, Spec FR-051]
  - Result: Not met. FR-051 names tokens as a scan target but gives no pattern. The revised design sets the privacy scan pattern. The pattern has two forms. The first form is the word `Token`, a space, and 20 or more letters or digits. The second form is a run of 40 or more letters or digits. The contract, design/contracts/evidence.md section 7, defines a different token shape for records. The two patterns must be reconciled.
- [ ] CHK057 - Does the privacy scan cover each identifier class that SC-006 names? [Consistency, Spec SC-006, FR-051]
  - Result: Not met. SC-006 names customer identifiers, a term that the revised design defines by identifier class. FR-051 scans UUIDs, MAC addresses, email addresses, and tokens only. The name scan runs outside the offline test, so FR-051 must say so.
- [x] CHK058 - Does FR-051 forbid printing the matched value? [Completeness, Spec FR-051]
  - Result: Met. spec.md FR-051 states that the test never prints the matched value. runbook-structure.md section 11 repeats the rule.
- [x] CHK059 - Does FR-052 require a check that each FR-002 heading exists? [Completeness, Spec FR-052]
  - Result: Met. spec.md FR-052 requires the existence check. The heading order is a separate gap, as runbook.md CHK012 records.
- [ ] CHK060 - Does FR-053 name the same counts as the design files? [Consistency, Spec FR-053]
  - Result: Not met. FR-053 counts paths, identifiers, and headings. The revised design counts paths, headings, and lines scanned, as runbook-structure.md section 11 does. FR-053 must change.
- [x] CHK061 - Does a requirement fail the offline test when it examines zero items? [Coverage, Spec Edge Cases]
  - Result: Met. spec.md edge case says the test never reports a pass when it examines zero items. FR-053 requires a failure when a file cannot be read.
- [x] CHK062 - Does FR-054 require the offline test in the unit suite? [Traceability, Spec FR-054]
  - Result: Met. spec.md FR-054 requires the unit suite. design/research.md D14 names the test file.

## Output and check results

- [x] CHK063 - Does FR-047 require ASCII output and log lines? [Completeness, Spec FR-047]
  - Result: Met. spec.md FR-047 requires ASCII text for printed output and logs. smoke-cli.md section 8 repeats the rule.
- [x] CHK064 - Does FR-048 accept a complete response with zero records as valid? [Clarity, Spec FR-048]
  - Result: Met. spec.md FR-048 accepts the response. The malformed JSON and empty body edge cases remain failures.
- [x] CHK065 - Does FR-039 require the status and the error body before any record? [Completeness, Spec FR-039]
  - Result: Met. spec.md FR-039 requires both reads first. smoke-cli.md section 5 repeats the rule.
- [x] CHK066 - Does FR-040 define the pass rule for each smoke check? [Completeness, Spec FR-040]
  - Result: Met in design. smoke-cli.md section 5 gives the status rules for SMK-01 to SMK-10.
- [x] CHK067 - Does FR-041 require each Appendix B name to match the live catalog? [Completeness, Spec FR-041]
  - Result: Met. spec.md FR-041 requires the comparison. smoke-cli.md section 5.5 names the catalog for each table.

## Notes

- Mark each completed item with `[x]`.
- Add a comment or a finding in the item note.
- Add a link to each resource or document that a note cites.
- Item numbers increase by one, for easy reference.
- Each checked item records an agent evaluation. The reviewer owns the final state and must confirm each checked item.
- Item IDs in this file start at CHK001. The file `runbook.md` in this folder has its own IDs.
