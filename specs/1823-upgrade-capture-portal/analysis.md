# Cross-Artifact Analysis: Upgrade Pre-Check and Post-Check Portal

**Feature**: 1823-upgrade-capture-portal
**Branch**: `feat/1823-upgrade-capture-portal`
**Date**: 2026-08-19
**Mode**: Read-only. This analysis changed no source file.

## Scope

The analysis read `spec.md`, `plan.md`, `tasks.md`, `data-model.md`, `research.md`, the six
documents under `research/`, and the five documents under `contracts/`. It also read
`.specify/memory/constitution.md` version 1.4.0. Every finding carries a file path and a
line number.

## Verdict

The artifact set is strong. The cascade order, the settle timings, the storage model, the
key strategy, and the phase structure are consistent and complete. The task list is precise
and records its own trade-offs.

One defect needs an operator decision. One defect needs a recorded argument. Fourteen
further defects need a decision but do not block the start of work.

| Severity | Count |
| --- | --- |
| CRITICAL | 2 |
| HIGH | 4 |
| MEDIUM | 7 |
| LOW | 3 |
| **Total** | **16** |

---

## Findings

| ID | Category | Severity | Location | Summary | Recommendation |
| --- | --- | --- | --- | --- | --- |
| I1 | Inconsistency | CRITICAL | `spec.md:477`, `spec.md:671`, `contracts/http-api.md:226`, `tasks.md:296` | The spec starts the upgrade with `CONFIRM`. Every contract and every task uses `UPGRADE`. | Operator decision. See the detail below. |
| C1 | Constitution | CRITICAL | `.specify/memory/constitution.md:156-158`, `plan.md:95`, `tasks.md:44` | Principle V requires structured, machine-parseable log records for a new service. The plan mandates prose log lines and marks the principle PASS. | State how the design satisfies "or equivalent", or adopt a machine-parseable format. |
| G1 | Coverage gap | HIGH | `spec.md:582-587`, `contracts/http-api.md:311-317`, `tasks.md:248-249` | FR-069 names ten statistics. Four have no contract field and no task. | Add the four statistics to the contract, the data model, and T104. |
| I2 | Inconsistency | HIGH | `spec.md:610-611`, `contracts/site-lock.md:41-42`, `tasks.md:367` | FR-080 requires the owner to type `continue` to resume. Three artifacts grant a resume with no typing. | Choose one rule. Record the choice in the spec. |
| I3 | Inconsistency | HIGH | `spec.md:417-418`, `spec.md:765-767`, `data-model.md:43-68` | The spec selects one device type for each run and also runs a cascade across every device type. | Withdraw the single-device-type requirements, or state how the two models combine. |
| T1 | Terminology | HIGH | `research/upgrade-reuse.md:644` | A proposed internal field is named `snapshot`. The spec reserves that word. | Delete the proposal. The contract already names the field `junos_file_action`. |
| G2 | Coverage gap | MEDIUM | `spec.md:546-547`, `plan.md:265-268`, `tasks.md:315-316` | FR-055 releases the wired clients at the switch gate. No downstream artifact states that rule. | Add the wired client clause to T145. |
| I4 | Inconsistency | MEDIUM | `plan.md:64-67`, `spec.md:712-713`, `spec.md:718-720` | The plan cites SC-002 and SC-005 for targets that neither criterion states. | Correct both citations. |
| U1 | Underspecification | MEDIUM | `plan.md:64-66`, `data-model.md:74` | A 90-second capture target and a 3-second render target appear in no success criterion. | Add both targets to the spec, or remove them from the plan. |
| G3 | Coverage gap | MEDIUM | `spec.md:515`, `contracts/ui-testids.md:62-70` | FR-040 requires a manual refresh control. No task builds it and no test identifier exists. | Add the control, the identifier, and a task. |
| T2 | Terminology | MEDIUM | `research/capture-data-sources.md:12`, `research/capture-data-sources.md:194` | Two lines define this feature's own record with the reserved word. | Replace both with "capture". |
| G4 | Coverage gap | MEDIUM | `spec.md:608-609`, `tasks.md:370` | FR-079 erases the unfinished decisions or data after a takeover. No artifact defines the erase. | Define what a takeover erases, or withdraw the erase clause. |
| I5 | Inconsistency | MEDIUM | `tasks.md:510`, `tasks.md:317`, `tasks.md:605-607` | US3 lists US1 as a soft dependency. Two US3 tasks hard-depend on the US1 capture store. | Move US1 into the hard dependency column for US3. |
| G5 | Coverage gap | LOW | `spec.md:391-392`, `tasks.md:82` | FR-004 prints a clickable console link. The launcher task does not name that step. | Add the clause to T008. |
| U2 | Underspecification | LOW | `spec.md:427-430`, `contracts/ui-testids.md:103-104` | FR-017 requires radio groups. The contract uses a toggle and a select. FR-018 defaults are untasked. | Align the contract with FR-017, or relax FR-017. |
| G6 | Coverage | LOW | `contracts/http-api.md:316`, `tasks.md:248` | `client_return_rate` traces to no requirement. | Add a requirement, or drop the statistic. |

---

## Finding detail

### I1 (CRITICAL). The upgrade start uses two different confirmation words

`spec.md:477` states FR-033. The begin control stays disabled until the operator types the
exact text `CONFIRM`. `spec.md:671` turns that rule into an acceptance assertion. The word
also drives five user-story lines: `spec.md:115`, `:128`, `:135`, `:137`, and `:139`.

Every downstream artifact uses a different word.

| Artifact | Line | Word |
| --- | --- | --- |
| `contracts/http-api.md` | 226 | `{ "confirm": "UPGRADE" }` |
| `contracts/site-lock.md` | 129 | "`UPGRADE` starts the upgrade" |
| `contracts/ui-testids.md` | 108 | "The field for the word `UPGRADE`" |
| `tasks.md` | 271 | The Phase 5 goal: the operator "types `UPGRADE`" |
| `tasks.md` | 296 | T129 contract test asserts `{"confirm": "UPGRADE"}` |
| `tasks.md` | 322 | T152 refuses any other word |

**This finding is an operator decision, not a defect to repair by default.**

The word `CONFIRM` in the spec is not an accident and is not a stale draft. It is the
literal word the requester specified for the begin control. The spec records the request
faithfully. A silent change to `UPGRADE` would overwrite a stated requirement.

The contracts also had a reason. The spec gives one word two destructive jobs. FR-033
assigns `CONFIRM` to the upgrade start, and FR-079 at `spec.md:608-609` assigns `CONFIRM`
to the lock takeover. Both actions run in the same portal. `contracts/site-lock.md:129`
states the rule the contracts adopted: each word has one job. The project writing standard
supports that rule, because Simplified Technical English requires one word to carry one
meaning. `.specify/memory/constitution.md:99-106` shows the destructive-confirmation
pattern with a specific action word.

The two actions never appear on the same screen. The takeover word is typed at lock
acquisition. The begin word is typed at upgrade start. The collision is therefore a
consistency and habit risk, not a live ambiguity in one dialog.

**Recommendation**: Ask the requester. Both repairs are cheap and neither blocks the
current phase.

- Option A, keep `CONFIRM`: edit `contracts/http-api.md:226`,
  `contracts/site-lock.md:129`, `contracts/ui-testids.md:108`, and `tasks.md:271`, `:296`,
  `:322`. Six edits across four files. Honors the stated requirement.
- Option B, adopt `UPGRADE`: edit FR-033, FR-034, and the assertion at `spec.md:671`, plus
  the five user-story lines. Eight edits in one file. Honors one word for one job.

### I1 resolution, 2026-08-19: Option A

The word is `CONFIRM`. The requester asked for `CONFIRM` in their own words, and the spec
records that request in nine places. The contracts and the tasks derive from the spec, so
the contracts and the tasks carried the drift.

The six edits of Option A are applied. `contracts/site-lock.md:129` now states that one
word serves both acts, because the two acts never share a screen. The template holds the
word on one line, `upgrade/confirm.html:71`, and `portal.js` reads it from the
`data-confirm-word` attribute, so no script change was needed.

One consequence stays open for the user to overturn. `CONFIRM` now carries two destructive
jobs, the lock takeover and the upgrade start. The habit risk is real but small, because an
operator types the takeover word before any target is chosen and types the begin word after
reading the target table.


Phase 5 holds every task that reads the word. Work may continue through Phase 4 before the
decision is needed.

### C1 (CRITICAL). Principle V asks for structured logs and the plan does not argue for its exemption

`.specify/memory/constitution.md:156-158` states: "Structured, machine-parseable log
entries (via `structlog` or equivalent) are required for any new service or module."

The portal is a new service and a new package. `plan.md:95` marks Principle V PASS. The
stated reason is that every record is ASCII, every record uses `%s` placeholders, and every
record carries a run identifier and a site identifier. `plan.md:37` confines `structlog` to
`src/db`. `tasks.md:44` repeats that rule as a global constraint.

A `%s` format string produces a prose sentence. A prose sentence is not machine-parseable.
T212 at `tasks.md:457` audits the placeholders, the ASCII characters, the two identifiers,
and the absence of a credential. T212 does not audit machine-parseability.

The plan may still be right, because the constitution allows an equivalent. The gap is that
the plan never makes that argument, so the PASS verdict rests on criteria the principle
does not name.

**Recommendation**: Add one paragraph to the Constitution Check that tests the design
against the phrase "or equivalent". If the prose format cannot meet the test, adopt a
key-value log format inside `src/upgrade_portal/` and extend T212.

### G1 (HIGH). Four required comparison statistics have no home

`spec.md:582-587` states FR-069. The comparison must show ten statistics.

| Required statistic | Contract or task | State |
| --- | --- | --- |
| Device count before and after | `contracts/http-api.md:312` | Derivable from four counts |
| Device count for each firmware version | none | **Missing** |
| Wired client count | none | **Missing** |
| Wireless client count | none | **Missing** |
| Devices that changed version | `tasks.md:249` T105 | Present |
| Devices that did not change version | `contracts/http-api.md:312` | Present |
| Devices that failed | none | **Missing** |
| Clients lost | `contracts/http-api.md:315` | Present |
| Clients gained | `contracts/http-api.md:315` | Present |
| Clients that moved | `contracts/http-api.md:314` | Present |

The wired and wireless split is the cheapest of the four. The capture already separates the
two groups. `data-model.md:66` holds a `clients` object, and the digest map at
`data-model.md:80-83` names `clients_wired` and `clients_wireless`. The statistics layer
drops the split.

**Recommendation**: Extend the statistics block at `contracts/http-api.md:311-317`, the
summary at `data-model.md:369-370`, and T104 with the four missing counts.

### I2 (HIGH). The word `continue` exists in the spec only

`spec.md:610-611` states FR-080: "If the original session owner returns before the cooldown
ends, the portal MUST restore the run when that owner types `continue`."

Three artifacts state the opposite rule.

- `contracts/site-lock.md:41-42`: "The pair of `actor_email` and `browser_id` decides
  whether a request may resume a run without typing anything."
- `contracts/site-lock.md:57`: the acquire table returns state `resume` for the same
  operator, with no typed value.
- `data-model.md:328`: "Resume | The same `actor_email` and `browser_id` may continue
  without typing".
- `tasks.md:367`: T175 builds the four acquire outcomes. The same-operator outcome needs no
  typed word.

`contracts/ui-testids.md:72-81` holds six lock identifiers. None accepts a `continue` value.

The downstream rule is defensible. The returning owner already proved identity through the
email address and the browser cookie. A typed word adds friction and no safety. The rule
still contradicts a MUST in the spec, and the requester asked for the typed word.

**Recommendation**: Ask the requester alongside I1. Both findings concern a typed word that
the requester specified.

### I3 (HIGH). The spec holds two different run models

One group of requirements builds a run around one device type.

- `spec.md:417-418` FR-013: a dropdown of device type with the choices access point,
  gateway, and switch.
- `spec.md:425-426` FR-016: the upgrade options "for the selected device type".
- `spec.md:431-433` FR-019: "If the device type is gateway ..."
- `spec.md:451-453` FR-025: every capture records "the device type".
- `spec.md:482-483` FR-036: send the job "only for the devices of the selected device type".

A second group builds a run around the whole site.

- `spec.md:541-554` FR-052 to FR-058: a cascade across gateways, switches, access points,
  and clients in one run.
- `spec.md:765-767`, the Assumptions: "A site lock covers the whole site, not one device
  type. The cascade crosses device types."

The downstream artifacts chose the second model in silence.

- `contracts/http-api.md:186-191` creates a run with the body `{ "tier": 2 }`. No device
  type appears.
- `contracts/ui-testids.md:62-70` and `:85-95` hold no device type selector.
- `data-model.md:43-68` lists every top-level capture field. No `device_type` field exists,
  so FR-025 cannot be met as written.
- T082 at `tasks.md:205` cites FR-012 to FR-015 and builds the organization list and the
  site list. It builds no device type dropdown.

Caution. The requester asked for a device type dropdown in the original brief. The cascade
model came from the later settle-order decision. The two models are both traceable to a
stated request, so this needs a decision rather than a silent withdrawal.

**Recommendation**: Ask the requester whether one run covers one device type or the whole
site. A middle path exists: keep the dropdown as a filter that limits which devices the
upgrade touches, and keep the cascade for the settle order of whatever the run touched.

### T1 (HIGH). A reserved word appears as a proposed field name

`spec.md:776-778` reserves the word. `data-model.md:21` and `tasks.md:51` repeat the
prohibition. T218 at `tasks.md:463` proves the word appears in no identifier and no page
string.

`research/upgrade-reuse.md:644` declares a boolean field under the reserved name inside a
proposed `UpgradeOptions` dataclass. That is an internal term, which the spec forbids.

The resolved contradiction covers the case. `contracts/upgrade-service.md:56-63` defines
`UpgradeOptions` with exactly four fields, and it names the same concept
`junos_file_action`. The contract wins. The research text still reads as a live proposal.

Caution. Open decision 1 at `tasks.md:627-630` lists the reserved name among the fields
that the four-field `UpgradeOptions` cannot express. That decision is a known open item.
Any resolution that adds the field under that name would break `spec.md:776-778` and would
fail T218.

**Recommendation**: Mark `research/upgrade-reuse.md:624-707` as superseded, in the document
itself. Resolve open decision 1 with the contract name.

### G2 (MEDIUM). The wired client rule stops at the spec

`spec.md:546-547` states FR-055: "The portal MUST treat the wired clients as released by
the switch gate."

`plan.md:265-268` describes the cascade and the three signals. It states no wired client
rule. T145 at `tasks.md:315` builds the four phases. T146 at `tasks.md:316` opens the
wireless client gate after the access point gate. Neither task names a wired client.

The rule matters. A wired client hangs off a switch port. It returns with the switch. A
build that waits for the access point gate before it counts a wired client would report a
false loss.

**Recommendation**: Add the FR-055 clause to T145.

### I4 (MEDIUM). Two success criterion citations are wrong

`plan.md:64-67` states three performance goals and cites two criteria.

| Plan text | Cited | Actual criterion |
| --- | --- | --- |
| "A Tier 2 capture of a 250-device site completes in 90 seconds or less" | SC-002 | `spec.md:712-713` SC-002 is the full comparison read, under 30 seconds |
| "A comparison page renders in 3 seconds or less" | SC-005 | `spec.md:718-720` SC-005 is two-operator isolation |

The nearest true capture criterion is SC-001 at `spec.md:710-711`. It states 50 devices in
under 2 minutes.

**Recommendation**: Cite SC-001 for the capture goal. Remove the SC-005 citation.

### U1 (MEDIUM). Two performance targets have no source

The 90-second capture target at `plan.md:64` and the 3-second render target at `plan.md:66`
appear in no success criterion. `data-model.md:74` repeats the 3-second target and uses it
to justify the digest skip design.

The 3-second target is ten times stricter than SC-002. A stricter target is not a conflict.
An unsourced target still drives design work that no criterion demands.

**Recommendation**: Promote both numbers into the Success Criteria, or restate them as
design margins against SC-001 and SC-002.

### G3 (MEDIUM). The manual refresh control is missing

`spec.md:515` states FR-040: "The portal MUST offer a manual refresh control." The
requester asked for this control by name.

FR-040 sits inside the range FR-039 to FR-051, which T153 at `tasks.md:323` cites. T153
builds the status endpoint and the run page route. A refresh control is a browser control,
not a route. T159 at `tasks.md:329` adds the 30-second poll, which is the automatic path,
not the manual one.

`contracts/ui-testids.md:97-113` lists thirteen upgrade identifiers. None is a refresh
control. That breaks rule 1 at `contracts/ui-testids.md:17`, which requires a `data-testid`
on every control that a test drives.

**Recommendation**: Add a `run-refresh-button` identifier and a task under Phase 5.

The code now answers this finding with two identifiers instead of one.
`upgrade-refresh-button` sits on the progress page, and `capture-refresh-button`
sits on the capture page. Both names differ from the `run-refresh-button` above.
`contracts/ui-testids.md` lists both.

### T2 (MEDIUM). The reserved word defines the feature's own record twice

`research/capture-data-sources.md:12` and `research/capture-data-sources.md:194` both define
a capture with the reserved word.

Both lines use the word in prose, not as an identifier, so T218 would not catch them. Both
lines still define this feature's own concept with the reserved word. That is the exact
usage that `spec.md:776-778` forbids.

Every other appearance of the word in the artifact set is legitimate. The prohibition
statements at `spec.md:776-778`, `data-model.md:21`, and `tasks.md:51` must use the word to
forbid it. T218 at `tasks.md:463` must use it to test for it.
`research/storage-and-locking.md` and `research/concurrency-auth-conventions.md` catalogue
identifiers that already exist elsewhere in the repository.
`research/upgrade-reuse.md:204-470` and `research.md:199` quote a vendor cloud field, which
the portal never renames in its own model.

**Recommendation**: Rewrite both lines. "A capture is the state of one site at one moment"
carries the same meaning.

### G4 (MEDIUM). The takeover word authorizes an action that nobody defines

`spec.md:608-609` states FR-079. After the cooldown ends, the portal requires the text
`CONFIRM` from a different operator "before it erases the unfinished decisions or data".

`contracts/site-lock.md:101-110` defines the takeover. It requires the cooldown and the
word. It then states: "A takeover never cancels a running upgrade. It transfers who may
drive the portal." It defines no erase.

T178 at `tasks.md:370` builds the cooldown check and the word check. It defines no erase.
`data-model.md:326-327` states the same two conditions and no erase.

The operator types a destructive word and no destruction happens. That is a Safety-First
anomaly. `.specify/memory/constitution.md:99-106` ties the typed word to a stated
consequence.

**Recommendation**: Define what a takeover erases. The draft option selections are the
likely answer, because the requester asked to let the next operator "start over". Then add
the erase to T178.

### I5 (MEDIUM). US3 depends on US1 harder than the table says

`tasks.md:510` lists US1 as a soft dependency of US3, with the note "US1 for the two
captures". `tasks.md:492-494` uses stronger prose: "Needs User Story 1 for the pre-check
and the post-check."

Two US3 tasks cannot run without the US1 capture store.

- T147 at `tasks.md:317` writes a capture with `ordinal` 2 and `role` `post`. That needs
  `capture/assembly.py` and `capture/store.py` from T076 and T081.
- T152 at `tasks.md:322` refuses a run with no verified pre-check. That needs the
  `verified` state from T081 at `tasks.md:204`.

The classification matters, because the parallel plan relies on it. `tasks.md:605` gives
Developer A the whole of US1. `tasks.md:606` gives Developer B the whole of US3 at the same
time. Developer B blocks at T147 and at T152.

The table already knows the correct form. US6 at `tasks.md:513` names `capture/store.py` in
the hard dependency column.

**Recommendation**: Move `capture/store.py` into the US3 hard dependency column. Note in the
parallel plan that Developer B stops before T147 until T081 lands.

### G5 (LOW). No task prints the console link

`spec.md:391-392` states FR-004. The portal prints a clickable link to the console when it
starts. The requester asked for the clickable link by name.

T008 at `tasks.md:82` adds the command-line flag and the launcher function for menu 238. It
is the natural home for the link. It does not name the step.

Note. The launcher built in Phase 1 already prints the link, so the behavior exists. Only
the task text is missing the clause.

**Recommendation**: Add the clause to T008.

### U2 (LOW). The option control shapes do not match the spec

`spec.md:427-428` states FR-017: each option group is a radio group that accepts exactly one
selection. The requester asked for "a bubble menu list of selectable options" and for "only
1 bubble selected at a time for each option", which reads as a radio group.

`contracts/ui-testids.md:103-104` defines `upgrade-reboot-toggle` and
`upgrade-strategy-select`. A toggle and a select are not radio groups.
`contracts/http-api.md:212-215` sends `reboot` as a boolean and `strategy` as a string,
which matches the toggle and the select.

`spec.md:429-430` states FR-018: preselect the same default that the existing bulk firmware
upgrade flow uses. T134 and T135 name no default value.

**Recommendation**: Align the contract with FR-017, because the requester described the
control shape directly. Add the default values to T135.

### G6 (LOW). One statistic traces to no requirement

`contracts/http-api.md:316` returns `client_return_rate`. `data-model.md:369` and T104 at
`tasks.md:248` build it. T116 at `tasks.md:260` tests it.

FR-069 at `spec.md:582-587` does not ask for it. The value is useful and cheap. It is still
untraced work.

**Recommendation**: Add the statistic to FR-069.

---

## The six judgments

### 1. Requirement coverage — HOLDS with seven exceptions

Coverage is high. The task list cites requirement ranges against the route tasks, and the
ranges reach every functional requirement.

Seven requirements are not truly covered.

| Requirement | Location | State |
| --- | --- | --- |
| FR-004 console link | `spec.md:391-392` | No task clause. Behavior exists. See G5. |
| FR-013 device type dropdown | `spec.md:417-418` | Two run models. See I3. |
| FR-025 device type field | `spec.md:451-453` | No field in the capture record. See I3. |
| FR-040 manual refresh | `spec.md:515` | No task and no test identifier. See G3. |
| FR-069 four statistics | `spec.md:582-587` | No contract field and no task. See G1. |
| FR-079 erase action | `spec.md:608-609` | The word is tasked. The action is not. See G4. |
| FR-080 typed `continue` | `spec.md:610-611` | Contradicted downstream. See I2. |

No task serves no requirement. The infrastructure tasks T004 and T007 to T012 at
`tasks.md:78-86` serve the constitution and the deployment pipeline rather than a numbered
requirement. `plan.md:100-106` and `plan.md:94` justify them. That is correct work, not
orphaned work.

One statistic is untraced. See G6.

### 2. The settle cascade — HOLDS

The order is identical in every artifact. Only clients are downstream of the access points.
The access points and the wired clients are downstream of the switches. Everything is
downstream of the gateways.

| Artifact | Line | Text |
| --- | --- | --- |
| `spec.md` | 541-554 | FR-052 to FR-058 |
| `plan.md` | 265-266 | "gateway gate, then switch gate, then access point gate, then wireless client gate" |
| `contracts/http-api.md` | 245 | `phase_order: ["gateways","switches","aps","clients"]` |
| `data-model.md` | 245, 254 | The same four names in the same order |
| `tasks.md` | 315 | T145 builds the fixed order |
| `tasks.md` | 316 | T146 opens the client gate after the access point gate |

No artifact states any other order. No artifact allows a phase to start early.

One clause of the cascade is missing downstream. See G2.

### 3. The settle timings — HOLD

All three numbers agree everywhere they appear.

| Number | Spec | Plan | Tasks |
| --- | --- | --- | --- |
| 20-second poll | `spec.md:517` FR-042 | `plan.md:65` | `tasks.md:308` T138, `tasks.md:312` T142 |
| 60 seconds after the signals | `spec.md:521-522` FR-044 | `plan.md:267-268` | `tasks.md:310` T140 |
| 60 more seconds for an access point | `spec.md:549-550` FR-056 | `plan.md:268` | `tasks.md:310` T140 |

T140 at `tasks.md:310` carries both waits in one sentence. The phrase "the 60-second wait
and the 120-second wait" at `tasks.md:639` is not a fourth number. It is the correct total
for an access point.

### 4. The lock rules — FOUR OF FIVE HOLD

| Rule | State | Evidence |
| --- | --- | --- |
| Identity by work email plus browser | HOLDS | `spec.md:596-597` FR-073, `contracts/site-lock.md:38-42`, `data-model.md:328`, T175 at `tasks.md:367` |
| 5-minute abandonment cooldown | HOLDS | `spec.md:606-607` FR-078, `contracts/site-lock.md:23`, `:51`, `:105`, `data-model.md:326`, T178 at `tasks.md:370` |
| Type `CONFIRM` to erase after the cooldown | PARTLY HOLDS | The word and the cooldown are specified and tasked. The erase is defined nowhere. See G4. |
| Type `continue` to resume | FAILS | The spec requires the word. Three artifacts grant a resume with no typing. See I2. |
| Free read access with no typing | HOLDS | `spec.md:612-614` FR-081 and FR-082, `contracts/site-lock.md:14-15`, `:118`, `:127-128`, T179 at `tasks.md:371` |

The read rule is the strongest of the five. `contracts/site-lock.md:118` keeps a page
readable when Redis is unreachable, and it marks the lock state unknown rather than
refusing the page. That matches the requester's rule that a user never types anything to
view data.

### 5. Terminology — THREE LEAKS

| Location | Type |
| --- | --- |
| `research/capture-data-sources.md:12` | Definition of this feature's record |
| `research/capture-data-sources.md:194` | Definition of this feature's record |
| `research/upgrade-reuse.md:644` | Proposed internal field name |

Every other appearance is legitimate, as detailed under T1 and T2.

The open decision at `tasks.md:627-630` is a known item, not a leak. It is still the live
risk, because it invites a field under the reserved name.

### 6. Phase dependency soundness — HOLDS with one classification error

Phase 2 blocks every user story, and it earns that claim. `tasks.md:109-160` builds the
application shell, the shared templates, the runtime services, the storage bootstrap, and
the foundational tests before any story starts.

Every Phase 3 to Phase 9 task traced back to Phase 1, to Phase 2, or to an earlier task
inside its own phase. No task depends on something that no earlier phase produces.

Two points deserve a note.

- The three-developer plan at `tasks.md:607` gives Developer C User Story 5 before User
  Story 4. That inverts the phase numbers and it is safe. `tasks.md:498-499` and
  `tasks.md:511-512` show the two stories are independent of each other.
- US3 lists US1 as a soft dependency at `tasks.md:510`, and two US3 tasks hard-depend on
  the US1 capture store. See I5.

---

## Known items confirmed

All three known items are still accurate. None is reported above as a new finding.

**1. Two resolved contradictions.** `tasks.md:621-624` records both.

- The seam signatures. `contracts/upgrade-service.md:35-195` wins over
  `research/upgrade-reuse.md:624-707`. Confirmed. The contract defines `UpgradeOptions`
  with four fields at `contracts/upgrade-service.md:56-63` and defines seven functions.
- The coverage floor. `pyproject.toml:419-420` wins over `.github/workflows/ci.yml:71`.
  Confirmed. `tasks.md:47` records the floor as 90.

**2. Two out-of-scope prohibitions.** `tasks.md:53-66` and `plan.md:322-335` record both.

- Do not repair issue #1824. `_is_standalone_mode()` at `src/export/data_exporter.py:141`
  and `_csv_fallback` at `src/db/router.py:372-382` stay as they are. FR-031 makes the
  portal verify its own write instead.
- Do not repair `src/db/retention.py:100`. The attribute name mismatch stops the purge.
  FR-032 wants unlimited retention, so the defect is harmless here and a repair would
  delete captures.

**3. Five open decisions for User Story 3.** `tasks.md:625-640` holds exactly five. The
count is correct and none has been resolved in another artifact.

---

## Coverage summary

| Requirement group | Range | Tasks | State |
| --- | --- | --- | --- |
| Portal shell and port | FR-001 to FR-005 | T010 to T012, T025 | Covered except the FR-004 task clause |
| Sign in and organization | FR-006 to FR-011 | T036, T187 to T203 | Covered |
| Site and device type | FR-012 to FR-015 | T082 | Covered except FR-013 |
| Upgrade options | FR-016 to FR-020 | T134 to T136, T155 | Covered, shapes differ. See U2 |
| Capture | FR-021 to FR-028 | T070 to T084 | Covered except the FR-025 device type |
| Storage and retention | FR-029 to FR-032b | T081, T084, T211 | Covered |
| Confirmation and start | FR-033 to FR-038 | T151, T152 | Covered, word conflict. See I1 |
| Stop control | FR-038a to FR-038i | T149, T150, T154, and `test_a_stop_from_a_second_operator_is_refused_with_site_locked` | Covered. No task states the FR-038i lock check on the stop route |
| Progress and settle | FR-039 to FR-051 | T137 to T144, T153, T159 | Covered. FR-040 now ships two refresh controls. The FR-051 badge repaints on a page load only |
| Cascade | FR-052 to FR-058 | T145, T146 | Covered except FR-055 |
| Post-check | FR-059 to FR-063 | T147 | Covered |
| Comparison | FR-064 to FR-071 | T104, T105, T110 | Covered except four FR-069 statistics |
| Site lock | FR-072 to FR-083 | T173 to T186 | Covered except FR-079 erase and FR-080 |
| History | FR-084, FR-085 | T204 | Covered |
| Observability | FR-086 to FR-088 | T212 | Covered. Principle V open. See C1 |
| Performance | FR-089 to FR-093 | T072, T142, T092 | Covered |
| Theme | FR-094, FR-095 | T014 to T019 | Covered |

---

## Metrics

| Measure | Value |
| --- | --- |
| Functional requirements | 106 |
| Success criteria | 16 |
| Tasks | 233 |
| Requirements with at least one task | 100 of 106 |
| Coverage | 94 percent |
| Requirements with a downstream contradiction | 3 (FR-033, FR-013, FR-080) |
| Reserved word leaks | 3 |
| Ambiguity findings | 2 |
| Duplication findings | 0 |
| Critical issues | 2 |

No duplicate requirement was found. The requirement set is clean on that measure.

---

## Next actions

Three findings need the requester, because each one changes a behavior the requester stated
directly. None blocks the current phase. Phase 5 holds the first task that reads a
confirmation word.

1. **I1.** Choose the word that starts the upgrade. `CONFIRM` was requested. `UPGRADE` is
   what the contracts and the tasks build.
2. **I2.** Choose whether the returning owner types `continue`, or resumes on identity
   alone.
3. **I3.** Choose whether one run covers one device type or the whole site.

One finding needs a recorded argument.

4. **C1.** Test the log design against the phrase "or equivalent" in
   `.specify/memory/constitution.md:156-158`. Record the result at `plan.md:95`.

The remaining findings are repairs that need no decision.

5. **G1.** Add the four missing statistics to `contracts/http-api.md:311-317`,
   `data-model.md:369-370`, and T104.
6. **T1** and **T2.** Mark `research/upgrade-reuse.md:624-707` as superseded. Rewrite the
   two lines in `research/capture-data-sources.md`.
7. **G2.** Add the wired client clause to T145. Fix this first among the MEDIUM findings,
   because a missing wired client rule produces a wrong result rather than a missing
   feature.
8. **G3**, **G4**, **G5**, **I4**, **I5**, **U1**, **U2**, **G6.** Edit the named artifact
   in place.
