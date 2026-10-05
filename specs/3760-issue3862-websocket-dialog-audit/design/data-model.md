# Audit Data Model

These are test coordination records, not product database entities.
Use nested records to keep constructors within five parameters.
Do not store credentials or raw target identifiers in sanitized records.

## Run record

- Identity: run key, audit parent `3862`, start time, and end time.
- Revision: repository SHA, dirty source digest, deployed revision, asset digests, and installed SDK version.
- Capability: Python, Chromium, portal, authentication availability, and server guard status.
- Mode: `isolated`, `live-inspection`, or `live-readonly` (one exact verified channel).
- Summary: separate status totals for each evidence dimension and policy violation count.

One run owns many operations, decisions, results, and local artifacts.
Unknown deployed revision prevents claims that source observations describe the live revision.
Each command record includes exit code, duration, selected scope, and sanitized arguments.

## Operation inventory entry

- Identity: kind, key, family, scope, and source revision.
- Display: observed title, purpose, action label, and safety warning.
- Fields: expected target and parameter records, plus observed DOM records.
- Oracle: SDK signature, channel definition, runner branch, purpose evidence, and completeness.
- Coverage: inspected, blocked, or missing with a specific reason.

Each field record contains name, label, type, required status, picker, dependencies, choices, defaults, and limits.
Nested records group these values.
Actual fields include visibility, enabled status, label association, selection multiplicity, and empty-state text.
The oracle must remain independent of displayed `description` and frontend safety classifications.

Reconcile source keys, live catalog keys, and rendered buttons.
Duplicate, missing, or unexpected keys fail inventory reconciliation.
An SDK-discovered utility count is version-dependent.
Never silently exclude a visible locked operation.

## Safety decision

- Subject: operation key or selector request.
- Boundary: browser origin and server Mist host.
- Evidence: SDK source/version, handler digest, method, target scope, and side-effect analysis.
- Rule: exact allowed envelope or denied behavior with reason.
- Validity: review time, revisions, reviewer, and expiry on any relevant change.

States: `unverified -> verified-candidate -> permitted` or `denied`.
The exact-key journey uses installed SDK/source agreement, deployed/base revision verification,
synthetic policy tests and the user's existing read-only authorization.
It does not require another approval or whole-server guard.
Candidate status alone never permits traffic.
Any changed revision returns the decision to `unverified`.
All utilities, shell, capture, command-output, and mutation paths remain `denied` for live execution.

## Journey result

- Subject: run key, operation key, and evidence dimension.
- Checks: purpose, required fields, dependencies, empty/failure behavior, cancel, and stop.
- Execution: command, duration, stage timings, and sanitized outcome.
- Status: `passed`, `failed`, `blocked`, or `skipped`.
- References: decision keys, local artifact references, and defect keys.

States: `pending -> inspecting -> terminal result`.
Live subscription states: `permitted -> selecting -> connecting -> observing -> stopping -> terminal result`.
Any forbidden action becomes a policy failure before transmission.
Any capability gap becomes `blocked`.
A deliberate exclusion becomes `skipped` with its policy reason.
Cleanup failure is `failed`, even when observation succeeds.

Observation outcome: `events`, `acknowledged-no-data`, `subscribe-denied`, `disconnected`, or `timed-out`.
No-data can satisfy bounded observation only with acknowledgement, correct UI state, and verified stop.
It cannot prove event rendering.
Selection and connection each have a 15-second limit.
Observation has a 30-second limit. Total duration, including cleanup, has a 90-second limit.
The outer pytest timeout is 120 seconds for fixture/browser startup and report teardown.
It does not extend the observation or journey budget. The exact-key journey observes for five seconds.
Stop has a five-second sub-limit.

## Defect record

- Identity: stable fingerprint and audit parent.
- Cause: verified behavior, affected operations, and repair boundary.
- Reproduction: sanitized steps, expected result, actual result, and exact validation command.
- Acceptance: regression requirement, original user story, and ownership requirements.
- Tracking: existing or new issue URL, phase, and verification results.

States: `candidate -> confirmed -> linked -> repairing -> verified -> release-ready`.
Candidates lack sufficient reproduction or cause evidence.
Repair cannot start without one linked issue and ownership clearance.
Several symptoms may share a record only when the cause and repair are proven identical.
An environment blocker is not a confirmed product defect.

## Local evidence artifact

- Identity: run key, result key, type, and local relative path.
- Integrity: digest, creation time, and evidence dimension.
- Sensitivity: private raw evidence or sanitized summary.
- Access: operator-only directory and file permissions.
- Retention: delete raw artifacts and authentication state after review, within seven days by default.

Use directory mode `0700` and file mode `0600` where supported.
On other platforms, verify equivalent operator-only permissions.
Do not publish raw traces, screenshots, event payloads, selector names, network addresses, or tokens.
The sanitized report may retain operation keys, status counts, timings, code revisions, and issue links.
Redact at collection and output boundaries.
Do not hash raw private identifiers into stable public correlation keys.
