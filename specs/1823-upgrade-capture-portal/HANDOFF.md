# Handoff: upgrade capture portal (issue #1823)

**Last updated**: 2026-08-25.
**Branch**: `feat/1823-upgrade-capture-portal`.
**Pull request**: [#1825](https://github.com/jmorrison-juniper/MistHelper/pull/1825).

Read this file first if you take over this feature. It states what is complete,
what waits, and what a person must decide. The other files in this folder state
the design. This file states the position.

---

## 1. Status at a glance

| Item | State |
| --- | --- |
| Tasks in `tasks.md` | 232 of 233 complete. Only T232 waits, and it needs an upgrade of a real device |
| Continuous integration on the pull request | **21 checks run and pass.** The merge of 2026-08-24 ended the conflict. Section 4.1 holds the detail |
| Pull request | Open, not a draft, no review yet. The merge state is `CLEAN` |
| Local commits not pushed | None |
| Uncommitted work | None from this feature |
| Portal tests | 2211 unit and contract for the portal package, all pass. 154 browser tests, all pass, 0 skip |
| Statement coverage of the package | 95.19 percent. Every module now reaches the 90 percent floor |
| Blocking defects | None. Every defect of `audit-2026-08-20.md` and of the live run of 2026-08-24 is fixed |

Warning: this feature has now written firmware to a real device, and the run
caused an outage. On 2026-08-24 an upgrade of one EX4100-F-12P carried
`reboot: false` and the switch rebooted anyway, four seconds after it installed
the image. That switch carries power over Ethernet for six access points, so all
six dropped with it and the site lost service for about six minutes. Issue
[#2007](https://github.com/jmorrison-juniper/MistHelper/issues/2007) holds the
event record and the cause. Read it before you run another upgrade.

The read half also runs against a real organization now.
`live-run-2026-08-24.md` holds that record. A browser drove the Morrison House
organization and its site of 8 devices. The sign-in, both pickers, the inventory
page, the site lock, and a tier 2 capture all pass. The capture read 8 devices,
37 wired clients, and 16 wireless clients in about 3 seconds.

That run found six defects that 2686 code tests and 154 browser tests had all
passed over. Four of the six share one cause, and the cause is worth reading
before you write another test. A stand-in answered a simpler shape than the
library or the module really answers, so every reader passed its own test and
failed the cloud. `tests/unit/upgrade_portal/test_privilege_shapes.py` now holds
the real shapes.

The code is written, the code tests pass, and the browser suite drives every
journey with no skip. The audit of 2026-08-20 found 21 defects, numbered 1 to
21. The work that followed found 12 more. Four came from the browser suite once
the harness stopped hiding them. Six came from looking at the portal, and two
came from the bug scrubs. Three later items carry no number. That is 36 records
in all. Section 3 of the audit refuted two of them, and every remaining defect
is fixed.

Three items stay open, and none of the three is a defect that an operator can
meet. Section 4.0 of this file names all three.

Warning: the pass of the browser suite carries one condition. The 13 tests of
`test_two_operators.py` need a Redis on port 6379. Without one, 12 of them skip
and the site lock goes untested. Section 8 states the answer.

Warning: an upgrade of this feature reboots a switch even when the operator
chooses no reboot. The measurement of 2026-08-24 is in issue #2007. The reboot
control is therefore not a promise today, and a window planned from it is too
small. Task T232 still needs a full quickstart run, and task T233 is closed.

Four defects hid behind the browser skips, and each one broke the feature for a
real operator:

| Defect | The harm | Commit |
| --- | --- | --- |
| 22 | The options page showed no device, so an upgrade reached no device | `9ddbe13` |
| 23 | Nothing wrote `pre_capture_id`, so no upgrade could start | `b2bd098` |
| 24 | With no database, the portal forgot every run and still reported success | `506250b` |
| 25 | A start that named no device reported a complete run | `cc92b79` |

Two more defects passed all 129 browser tests, because a test selects by
`data-testid` and never reads what an operator sees. Both were found by opening
the portal and looking at it. Section 10 of the audit holds the detail:

| Defect | The harm |
| --- | --- |
| 26 | The security policy blocked all 23 Bootstrap control graphics, so every radio, checkbox, switch, and selection list painted as an empty box |
| 27 | The site page rendered no link to the capture page, so the journey stopped at the device table |

Defect 26 was held in place by a contract test. That test banned the `data:`
scheme across the whole policy, so the correct fix read as a regression. The ban
now names the code-bearing directives alone.

A third by-eye drive found defect 28, in section 11 of the audit. It is a defect
of the browser harness, not of the shipped portal, and it matters anyway:

| Defect | The harm |
| --- | --- |
| 28 | The browser stand-in answered the wrong shape, so `GET /api/captures/<capture_id>` returned 500 for a capture the portal called verified. Every by-eye drive showed a red console message and a stored size of 0, and no browser test called that endpoint at all |

A request to make the brand theme dark uncovered two more, in section 12 of the
audit. Both are older than that request, and both are one defect in two places.
The stylesheet reads correctly in each case. The browser paints a different
color, because a rule that names one class loses to `.portal-shell a`, which
names one class and one element:

| Defect | The harm |
| --- | --- |
| 29 | The brand text and every navigation link took the page link color and ignored the header tokens. On a brand fill that is pale pink text on magenta |
| 30 | A link drawn as a button took the page link color and kept the underline of a link, so a magenta pill carried pale pink underlined text. Five pages carry such a link |

No test in this repository read a painted color, which is why 2733 tests passed
while the header looked wrong. `tests/e2e/upgrade_portal/test_assets.py` now
holds `TestThemeColorsReachThePaint`, which reads `getComputedStyle` under both
shipped themes. Eight of its ten cases fail against the reverted stylesheet.

A look at the same page after that fix found one more, in section 13 of the
audit. The scrollbar of the window and of every table box stayed light gray on
the near black page, because no stylesheet named its colors and the browser then
chose its own pair. Each theme now sets a thumb color and a track color, and
`TestTheScrollbarTakesTheThemeColors` reads what the browser painted on two
elements under both themes.

The bug scrub of section 2.6 closed last, in commit `776dddd`. It found three
items in the comparison code. Each one is small, and each one can put a wrong
line in a file that an operator attaches to a change record:

| Item | The harm |
| --- | --- |
| `compare/clients.py` | `VOLATILE_CLIENT_FIELDS` copied the volatile list of the digest builder, and no line read the copy. The last branch of `_compare_one_client` could not run, and it built a client record that names no field and called that record missing |
| `compare/download.py`, the export | A device whose every change named a credential field lost every row and vanished from the file. A reader takes that absence to mean that nothing happened to the device |
| `compare/download.py`, the formula guard | The guard omitted the minus sign, so a spreadsheet runs a cell that starts `-1+`. The guard now names all six leaders, and a negative number still reads as a number |

Read `audit-2026-08-20.md` before you merge. It holds the 13 tasks that lost a
check, the 4 that earned it back, the defects inside tasks that keep a check,
and the order to fix them in. Step 7 of that order is this file.

---

## 2. What the feature does

An operator records the state of one site before a firmware upgrade, runs the
upgrade, records the state again, and compares the two records. The portal is a
web page on its own port. Several operators can work several sites at the same
time.

The internal word for one record is `capture`. Do not use the word `snapshot` in
code or in the database. Junos already uses `snapshot` for a recovery image, and
the two meanings would collide.

---

## 3. What is complete

### Entry points

| Surface | Location |
| --- | --- |
| Menu entry 238 | `MistHelper.py`, key `"238"` |
| Command line flag | `--capture-portal` |
| Port | 8056, from `CAPTURE_PORT` |
| Container port map | `compose.yml`, `Containerfile` |

### Packages

The portal is `src/upgrade_portal/`, which holds 39 modules in five groups.

| Group | Purpose |
| --- | --- |
| `app/` | The Flask factory, the settings, the security rules, and five route modules |
| `capture/` | The collectors, the assembly, and the store |
| `compare/` | The difference, the statistics, and the download |
| `runtime/` | The site lock, the identity, the run records, the server, and the stop signals |
| `upgrade/` | The run driver, the events watch, the phase gate, and the stop control |

The package sits outside `web_portal/`. Ruff and mypy exclude `web_portal/`, so
a module inside it would escape those gates.

The upgrade seam is `src/firmware/upgrade_service.py`. The portal calls the
existing bulk firmware tools through that seam and never calls them directly.

### Behavior that is built and tested

- Both sign-in modes. A single token assumes the organization. A managed
  service provider account picks the organization first.
- A searchable site list, then a device type, then the firmware options.
- A capture at a standard tier or a full tier. The capture writes to ArangoDB,
  to a CSV file under `data/`, and to the page as a table.
- The typed word `CONFIRM` unlocks the start control. The control stays locked
  until the run also holds a verified pre-check capture and a plan that names at
  least one device. The start route refuses the same three states.
- A status page that refreshes every 30 seconds, with a manual refresh.
- The typed word `STOP` cancels every device that waits to start. A device that
  writes firmware always finishes.
- The settle logic. The portal reads the device events every 20 seconds, waits
  for the reconnect message, and then waits one more minute. Access points and
  wired clients wait for the switches. Wireless clients wait for the access
  points. Everything waits for the gateways.
- A second capture, repeatable, which locks the first capture against a rewrite.
- A compare page with two sorted tables side by side and a statistics summary.
  Both offer a CSV download.
- A site lock in Redis. The lock pairs a work email address with the browser, so
  one operator holds several sites in several tabs. An abandoned session frees
  the site after a five minute cooldown. A reader never needs a lock.
- History without an expiry. Each capture records its stored size.

---

## 4. What waits

### 4.-1 The work of 2026-08-25

This session worked the open issues of the feature. Each item below is on the
branch, and each one carries a comment on its issue.

| Issue | What changed | Proof |
| --- | --- | --- |
| [#1997](https://github.com/jmorrison-juniper/MistHelper/issues/1997) | `main` merged into the branch, so the pull request left the `DIRTY` state | 21 checks now run and pass. Section 4.1 |
| [#2007](https://github.com/jmorrison-juniper/MistHelper/issues/2007) | The per-device upgrade call exists. A one-device run with the reboot control off now takes `upgradeDevice`, whose schema holds no orchestration field | 25 tests. The 205 tests of the four existing files pass with no change |
| [#2003](https://github.com/jmorrison-juniper/MistHelper/issues/2003) | The access point warning names the count, and it now covers a scheduled run as well as a no-reboot run | 4 tests. Measured on the real site shape: one switch and six access points reads "6 access point(s)" |
| [#2008](https://github.com/jmorrison-juniper/MistHelper/issues/2008) | The bare `Warning:` is gone. The reported cause was wrong, and the real cause was the generated content of a hidden element | 2 browser tests. Verified in the live page both ways |
| [#1994](https://github.com/jmorrison-juniper/MistHelper/issues/1994) | The address column fills from the device statistics call | 11 unit tests and 1 browser test. All 8 devices of the live site show an address |
| [#1995](https://github.com/jmorrison-juniper/MistHelper/issues/1995) | The false docstring is corrected, and the live channel is declined with a reason. The page states when a count moves | Section 4.0 |
| [#1996](https://github.com/jmorrison-juniper/MistHelper/issues/1996) | All three modules reach the 90 percent floor | 42 tests. Coverage rose to 95.19 percent |
| [#1828](https://github.com/jmorrison-juniper/MistHelper/issues/1828) | Two comments cite line 132 and not line 103. The contract gained Appendix A | The appendix sits at the end of the file, so it moves no line the source cites |

Two issues opened from the same work:

| Issue | What it holds |
| --- | --- |
| [#2027](https://github.com/jmorrison-juniper/MistHelper/issues/2027) | No table of this portal sorts by a column, so an operator cannot group the devices that need the upgrade |
| [#2036](https://github.com/jmorrison-juniper/MistHelper/issues/2036) | A stalled runner reports as a pytest failure, because the coverage job passes no per-test timeout |

The cause behind issue #2036 is found and fixed, and it belonged to this branch.
The pytest gate reached its 15 minute limit twice and reported as a test failure
both times. Both logs showed the same shape: exactly three passing tests each
minute for eleven minutes, which is 20 seconds for each test. The two stalls hit
two different files of `tests/contract/upgrade_portal/`.

The `portal_app` fixture is function scoped, so a contract test builds one whole
application for each test. `create_app` calls `install_seams`, which calls
`prepare_storage`, which calls `bootstrap_storage`. That reaches
`connect_database`. This function caches a handle and never caches a failure.
An unreachable store is therefore probed again on every call.
`DatabaseConfig.from_env` then
resolves the database host and the lock store host to decide the standalone mode.
A workstation fails those names at once. A runner that does not costs about 20
seconds for each application the suite builds.

`prepare_storage` now runs once for each process. Every step of the bootstrap
repeats without harm, so a second run adds nothing and only costs the probe. The
flag is set before the call, so a store that raises leaves no retry loop. That
case is the exact one that stalled the runner. `reset_storage_bootstrap` clears
the flag for a test and for a worker that meets a database restart. The pytest
gate now finishes in 7 minutes 7 seconds.

Warning: the per-device call of issue #2007 removes a contradiction and proves
nothing. No lab switch has yet held the no-reboot choice through it. The plan
still carries the warning that a switch may reboot, and that issue stays open
until a switch proves it either way.

One correction belongs here, because this file carried the wrong claim. The
report of issue #2007 asked the verification path to read the device events.
It named `version`, `uptime`, and `reboot_in_progress` as the readings to drop.
The settle gate already reads the events. `upgrade/gate.py` opens the gate on the
reconnect event. No statistics reading counts before that event arrives.
`_screen_reading` also drops a record that repeats an older snapshot, which is
FR-046. The four lying
signals never misled the portal. They misled the person who ran the upgrade
outside it.

### 4.-0.5 The site at the end of 2026-08-24

A read of the site about 7 hours and 40 minutes after the upgrade. Nothing was
queued: `listSiteDeviceUpgrades` answered zero jobs, so no device could reboot on
its own.

| Device | Version | Uptime | `fwupdate_stat` |
| --- | --- | --- | --- |
| Morrison-Switch | 25.4R1-S2.3 | 27454 s | `success` and `Upgraded` |
| SRX-1500 | 23.4R2-S5.5 | 2094315 s | `inprogress` and `Installing image` |
| Office AP | 0.15.34994 | 27303 s | `success` |
| The other 5 access points | 0.15.34994 | about 1232000 s | 3 `success`, 2 `inprogress` |

**A fifth reading goes stale, and it is the one the record called truthful.** The
SRX reports that it installs an image while the site holds no upgrade job at all.
It has reported that for over seven hours. Its uptime of about 24 days shows
that it never rebooted.

`live-run-2026-08-24.md` section 5.1 names four readings that mislead after an
upgrade, and it names `fwupdate_stat.progress_brief` as one of two that told the
truth. That is wrong for this device. A reader who waits for `Upgraded` on this
gateway waits forever. Only `searchSiteDeviceEvents` has stayed honest.

**A correction to the outage record.** The uptime readings refine what the six
`AP_DISCONNECTED` events meant. Only the Office AP power cycled, and its uptime
matches the switch reboot. The other five access points hold an uptime of about
14 days, so they lost the network path and kept their power. The outage is no
smaller for it, because every access point left the cloud and the site lost
wireless service either way. The record should say one power cycle and five path
losses, and not six power cycles.

The staged image on the SRX activates on the next reboot, whenever a person
chooses to give it one. Do not wait on the progress field.

### 4.0 The audit of 2026-08-20

`audit-2026-08-20.md` holds the whole result. The short form:

| Group | Count | Where | State |
| --- | --- | --- | --- |
| Tasks that lost a check | 13 | Audit section 1.1 | 4 are back |
| Defects that can hurt a device | 2 | Audit section 2.1 | Both fixed |
| Defects of high severity | 2 | Audit section 2.2 | Both fixed |
| Defects of the test harness | 2 | Audit section 2.3 | Both fixed |
| Defects of the settle gates | 4 | Audit section 2.4 | All fixed |
| Defects of the site lock | 6 | Audit section 2.5 | 4 fixed, 1 refuted, 1 refuted in part |
| Defects of lower severity | 9 | Audit section 2.6 | All fixed |
| Defects the browser tests found | 4 | Audit sections 6 to 9 | All fixed |
| Defects a person found by eye | 6 | Audit sections 10 to 13 | All fixed |
| Defects the fault message scrub found | 1 | Audit section 15 | Fixed |

Three items stay open. None of the three is a defect that an operator can meet.

| Open item | Where | Why it stays open |
| --- | --- | --- |
| No phase progress reaches the page during a wait | Audit section 2.4, the last paragraphs | This is a design change, not a defect fix. A live channel costs 30 to 90 extra store writes for each phase. The false docstring at `upgrade/phase_gate.py` is the part to fix first |
| Three modules sit under the 90 percent floor on their own | Audit section 2.7 | The aggregate of 94.26 percent hides them. `app/wiring.py` reaches 82 percent, `app/routes/select.py` 85 percent, and `app/routes/review.py` 89 percent. The audit table names `upgrade/wiring.py`, and no module of that path exists |
| Four document corrections | Audit section 4 | Four rows of that table read `Open`. They are stale line citations and two counts, and no gate checks a line citation |

**Update of 2026-08-25.** Two of those three are closed.

The phase progress item is closed as a recorded decision, not as a build. The
docstring of `PhaseProgress` now states what the code does, and it names the
reason the live channel is absent. The progress page states that each phase count
moves once, when its phase ends. That removes the harm the report named. A still
count reads as a stall, and a stalled page during a firmware write is the moment
an operator reaches for the power. Issue
[#1995](https://github.com/jmorrison-juniper/MistHelper/issues/1995) holds the
decision.

The coverage item is closed with tests. Every module now reaches the floor:
`review.py` at 96 percent, `wiring.py` at 91 percent, and `select.py` at 90
percent. The package aggregate rose to 95.19 percent. Issue
[#1996](https://github.com/jmorrison-juniper/MistHelper/issues/1996) holds the
detail of what the uncovered half held.

The four document corrections stay open. Issue
[#1998](https://github.com/jmorrison-juniper/MistHelper/issues/1998) holds them.
Two stale citations of `contracts/http-api.md` are fixed, and the contract gained
Appendix A, which names all three `site_locked` refusal shapes together.

The two defects of audit section 2.1 told an operator that the cloud stopped a
device, when the code cannot know that. An operator who reads that word can cut
power to a switch that is writing firmware, and that switch does not start
again. Commit `4a9d028` fixed both.

Nine tasks still carry no check. They are the remaining browser identifiers of
T172, the two measurement tasks T153 and T219, the two field tasks T067 and
T080, the three audit tasks T227, T228, and T233, and the quickstart run T232.

**Update of 2026-08-24.** Eight of those nine are closed. Each one carries its
evidence in `tasks.md`, and two carry a record of their own:
`ste-audit-2026-08-24.md` for T228 and `live-run-2026-08-24.md` for the run that
closed T233 and moved T232. T232 alone stays open, because it needs an upgrade
of a real device and a store that verifies. Section 4 of the live run record
names both conditions.

### 4.1 Merge the pull request

**Resolved on 2026-08-24.** `origin/main` merged into the branch. The pull
request now reads `MERGEABLE` and `CLEAN`, and 21 checks run and pass.

The choice was a merge and not a rebase, for the reason stated above. The
repository squash-merges a pull request, so the merge commit disappears when the
pull request lands and the history stays one commit either way. The merge
therefore costs nothing that a rebase would save, and it keeps every hash
citation true.

Three files conflicted, and the start script needed real care. `main` brought the
supervision work of issue #1925, which reports the real exit status of a crashed
service instead of a fixed 0, and that work names two services. This branch adds
a third, the capture portal. The merged script keeps the issue #1925 structure
and adds the capture portal to the supervision line, the `wait -n` list, the
crashed-service report, and the shutdown.

`main` also changed `su misthelper` to `su - misthelper`. The merge keeps the
form with no dash. A dash starts a login shell, which clears the environment, and
the portal then starts with no database address and no allow list.

The first green run found one real CodeQL alert at high severity,
`py/bad-tag-filter` in `scripts/extract_page_strings.py`. It is fixed and not
suppressed.

Warning: a push while a run is in flight cancels that run, and the cancelled
check reads as a failure on the pull request. Let a run finish before you push
again. Issue
[#2036](https://github.com/jmorrison-juniper/MistHelper/issues/2036) records a
second cause of the same reading: the coverage job carries a 15 minute limit and
passes no per-test timeout, so a stalled runner reports as a pytest failure.

The previous text of this section, kept because it explains the choice:

Warning: the pull request cannot merge today. The branch sits 66 commits behind
`main`, and GitHub reports the merge state `DIRTY`. No check runs against a
conflicted pull request, so `gh pr checks 1825` answers "no checks reported".
The last green run covers `fc11b9e0`, which is one commit behind the head.

`git merge-tree --write-tree --name-only origin/main HEAD` names the whole
conflict. Three files conflict, and no more:

| File | Branch commits that touch it |
| --- | --- |
| `CHANGELOG.md` | 3 |
| `container/scripts/start.sh` | 2 |
| `tests/unit/org/test_org_synthetic_probes_manager.py` | 1 |

A rebase therefore stops at most six times. A person must choose the way,
because a rebase carries one cost that this feature feels more than most. It
rewrites all 56 commits, so every commit hash in `audit-2026-08-20.md` and in
this file then names nothing. Those two documents cite about 20 hashes, and the
audit already records what a stale citation costs a reader.

Do this after the merge state is clean. Run every scenario of `quickstart.md`
against a real site, which is task T232. The read half of that run is complete,
and `live-run-2026-08-24.md` holds it. The upgrade, the stop, and the compare
scenarios still wait. Issue
[#1992](https://github.com/jmorrison-juniper/MistHelper/issues/1992) tracks them.

### 4.2 Issue #1824, which is separate work

`DatabaseRouter` drops every ArangoDB write and every Redis write when the
process runs outside a container. The portal works around this. An operator must
set two settings before a real run on a desktop:

```
MISTHELPER_STANDALONE=true
REDIS_HOST=127.0.0.1
```

Issue [#1824](https://github.com/jmorrison-juniper/MistHelper/issues/1824) is
open and tracks the real fix. Do not fix it inside this feature. The change
touches every caller of `DatabaseRouter`, and a change that wide belongs in its
own pull request with its own review.

### 4.3 Two issues that this feature raised

Both came out of a source review during the handoff. Neither blocks the merge.

| Issue | Subject | Kind |
| --- | --- | --- |
| [#1827](https://github.com/jmorrison-juniper/MistHelper/issues/1827) | An unreachable lock store lets a second operator start an upgrade on a held site | Safety defect |
| [#1828](https://github.com/jmorrison-juniper/MistHelper/issues/1828) | Two comments cite the wrong line of the HTTP contract | Documentation |

Issue #1827 is the one to read. The write path in `app/routes/upgrade.py` reads
the lock as two states, free or held. The read-only path in `app/routes/select.py`
reads the same index as three states, and names the third one `unknown`. A store
that does not answer therefore reads as free on the path that sends firmware.
`contracts/site-lock.md:136` already fixes the rule. The issue holds the whole
trace.

Warning: do not answer #1827 by making every read fail closed, because that
change can stop the capture start and both read-only pages. No operator can then
see the state of any site while the lock store is down. Those three paths are
correct today, and issue #1827 names each one.

---

## 5. Decisions that are closed

Do not reopen these. A person decided each one. The number is the order of the
question, not a priority.

| # | Question | Decision |
| --- | --- | --- |
| 1 | The word for one record | `capture`, never `snapshot` |
| 2 | When to capture after an upgrade | Read the device events every 20 seconds. After the reconnect message, wait one more minute |
| 3 | The order of the device types | Gateways first, then switches, then access points, then clients. Each layer waits for the layer above it |
| 4 | The stores | ArangoDB for the data, Redis for the lock, CSV for the fallback |
| 5 | The identity | A work email address paired with the browser. A five minute cooldown. `CONFIRM` to take over. `continue` to resume. A reader types nothing |
| 6 | The scope | One site for now. Build so a list of sites fits later |
| 7 | The gateway hardware | A mixed fleet of SRX and SSR |
| 8 | The size of a capture | A standard tier, with a full tier toggle. Carry a schema version from the first record |
| 9 | Retention | Keep every capture. No expiry. Record the stored size |
| 10 | The stop control | Cancel every device not yet started, behind the typed word `STOP` |
| 11 | The post-upgrade capture | Automatic for now. The seam to switch to manual exists |
| 12 | The theme | The brand theme is dark, and it is the default. The neutral theme stays light |

Two later decisions carry the same weight.

- **A lost lock is not a failed upgrade.** The portal submits the upgrade to the
  cloud, and the cloud then owns the work. If the portal loses the lock, the
  banner states that the upgrade continues and that the devices still reboot. An
  operator who reads the word `failed` would think nothing happened, and would
  then not understand a reboot an hour later.
- **The word `partial` stays.** An earlier plan renamed it to `degraded`. Do not
  do that rename.

---

## 6. Open questions for a person

These need a product decision. None of them blocks the merge.

| Question | Where | Note |
| --- | --- | --- |
| The capture start reads the tier before the lock | `app/routes/capture.py` | A refused operator still spends the read. Harmless today |
| A run record does not survive a restart | `runtime/runs.py` | The captures survive. The in-flight run state does not |
| The refusal body carries a plain email address | `app/routes/select.py`, `holder_details` | This is deliberate. The waiting operator needs to know who to ask. The address is never written to a log. A log always uses `identity.email_digest` |

An earlier version of this file listed two more questions. A source review
answered both, so neither needs a person.

- **The lock read of the write path.** This is a defect, not a question. The
  contract already fixes the rule. Issue #1827 holds it.
- **The shape of the `site_locked` refusal.** The portal sends three bodies, and
  the contract asks for all three. The capture start sends no details, the three
  run routes send the address, and the lock acquire sends the address and the
  cooldown. The cooldown belongs to the acquire alone, because only the acquire
  offers a takeover after the wait. Do not make the three bodies one body. Issue
  #1828 corrects the comments that made this look wrong.

---

## 7. Rules that the code depends on

Break one of these and a gate turns red, or worse, a secret leaks.

### Security

- `.env` holds live production tokens. Never read it, echo it, log it, or commit
  it. It lives in the main checkout, not in this worktree.
- Never log a whole record, job, session, or settings object. A session object
  carries an API token inside it.
- Never log an email address in plain text. Use `email_digest` from
  `src/upgrade_portal/runtime/identity.py`.
- A caught fault logs `type(fault).__name__` alone. A driver message can carry a
  connection string.
- Never name the end customer in code, in documentation, or in a commit message.
- Stage explicit paths. Never run `git add -A`.

### Tests

- A test opens no socket, binds no port, reaches no cloud, and reads no `.env`.
- `create_app` wires a real run driver. A test that starts a run spawns a real
  thread that races the assertion. Empty that seam in the test.
- `register_readiness` drops the cached readiness answer. Do not delete that
  call. It reads as a no-op, because production registers one application for
  each process. Every contract fixture is function-scoped, so without it a stale
  answer leaks from one test to the next and 9 older tests fail. A test that
  needs a fresh probe from one application calls `reset_readiness_cache`.

### Style

- Simplified Technical English governs every word a person reads. The guide is
  `documentation/ASD-STE100_writing-guide.md`. It outranks the caveman rules.
- Every module, class, and function needs a docstring with a `Why` section.
  `interrogate` holds the floor at 90 percent.
- Line length is 120.

### Themes

- `portal.css` holds no color value. Every color comes from a custom property
  that a theme file sets. Two unit tests hold this, so a literal color in that
  file fails the suite.
- Both shipped themes set exactly the same 71 property names. A property that
  only one theme sets makes the page change shape as well as color.
- Do not rename `themes/magenta.css`. The brand name stays inside the file
  content. The repository ignore rules exclude a path that carries the brand
  name, so a file named for the brand would never reach a commit.
  `tests/unit/upgrade_portal/test_guardrails.py` proves this.
- Section 5 of `portal.css` colors a link with `.portal-shell a`. A new rule that
  names one class alone loses to it. Read the painted color of the element, not
  the stylesheet, whenever a color looks wrong.
- The theme name drives `data-bs-theme` on the `html` element. Bootstrap draws
  its own fields and its 23 vendored control graphics from that attribute. It
  does not draw the scrollbar from it.
- `portal.css` names `scrollbar-color` on `:root`. Do not move that rule to
  `.portal-shell`. The browser reads the root element to paint the scrollbar of
  the window, and the shell sits on `body`, which is a child of the root. The
  property also inherits, so the one rule on `:root` reaches every box that
  scrolls inside the page. A rule on the shell still paints the table box and
  still leaves the window scrollbar light, and only a browser test catches that.

---

## 8. Environment traps

Each of these cost real time. Read them before you debug.

| Trap | Sign | Answer |
| --- | --- | --- |
| `PATHEXT` holds `.CPL` alone | `git` and `python` report "not recognized" | Set `$env:PATHEXT = ".COM;.EXE;.BAT;.CMD;.VBS;.JS;.WS;.MSC;.PS1"` first |
| `APPDATA` is empty | `gh` looks signed out. Podman loses its connection list | Set `$env:APPDATA = "C:\Users\jmorrison\AppData\Roaming"`. Never cycle the podman machine for this |
| A stale copy of `src/` sits in `.venv/Lib/site-packages/src/` | A script reports a missing module for a file that exists | Run from the repository root. Check `module.__file__`. If it points inside `.venv`, this is the cause |
| `src/dataclasses/` shadows the standard library | Strange import faults | Never put `src` on `sys.path`. Import as `src.<package>` |
| Bandit `exclude_dirs` uses forward slashes | 42 local findings that CI never reports | Judge a local run by the paths, not the exit code. All 42 sit in `tools/test_quality_analyzer/fixtures/` |
| The lint tools live in the virtual environment | `python -m ruff` fails | Call `.\.venv\Scripts\python.exe` by path |
| Playwright cannot re-enter a nested run | A pytest run inside a pytest run fails | Pass `-p no:playwright` |
| Gunicorn cannot start on Windows | An import fault on `fcntl` | The portal picks Waitress on Windows already |
| A stray listener holds port 8056 | An end-to-end run fails almost every test with 401 | Kill the listener first. The fixture attaches to any listener, and a listener from another run holds no test record. Commit `6ce6fb4` turned this skip into a failure, so a broken portal can no longer read as a pass |
| ArangoDB and Redis do not answer from this shell | The portal writes the CSV backup alone | Set `MISTHELPER_STANDALONE=true` and `REDIS_HOST=127.0.0.1`. Commit `506250b` added a process-local mirror, so a run still reads back |
| No Redis answers on port 6379 | 12 of the 13 tests of `test_two_operators.py` skip and name a 503 from the lock route | Start one, then set `REDIS_PASSWORD`. Section 9 holds the command. The site lock is the one part of the portal that a browser test cannot reach without a store |
| A test job stalls at about 20 seconds for each test | The pytest gate reaches its 15 minute limit and reports as a test failure. Every test still passes. The log shows exactly 3 passing tests each minute | The `portal_app` fixture builds one application for each test, and each one probed the database host. `prepare_storage` now runs once for each process. If this returns, read the log timestamps first. A uniform time for every test names a fixture and never a test body. Issue #2036 |
| A cloud module reaches the network from a contract test | A contract test hangs or reaches a real account | A seam fell back to the real module because only its sibling seam was injected. `select.statistics_reader` shows the rule: read the real module only when no stand-in is in place anywhere |

---

## 9. How to check the work yourself

Run the portal suite:

```powershell
$env:PATHEXT = ".COM;.EXE;.BAT;.CMD;.VBS;.JS;.WS;.MSC;.PS1"
.\.venv\Scripts\python.exe -m pytest tests/unit/upgrade_portal tests/contract/upgrade_portal -q -p no:playwright
```

Expect 2686 passes.

Start a Redis before the browser suite. Without one the site lock answers 503,
and 12 of the 13 two-operator tests skip:

```powershell
podman run -d --name misthelper-redis-e2e -p 6379:6379 `
  -e REDIS_ARGS="--requirepass misthelper" docker.io/redis/redis-stack:latest
```

Run the browser suite. It starts a portal of its own, so free port 8056 first:

```powershell
$env:PATHEXT = ".COM;.EXE;.BAT;.CMD;.VBS;.JS;.WS;.MSC;.PS1"
$env:MISTHELPER_STANDALONE = "true"
$env:REDIS_HOST = "127.0.0.1"
$env:REDIS_PASSWORD = "misthelper"
.\.venv\Scripts\python.exe -m pytest tests/e2e/upgrade_portal -q
```

Expect 154 passes and no skip. A skip means the harness hid a broken portal, or
the Redis is not running. Run with `-rs` to read the reason. The portal writes
its own log to `$env:TEMP\upgrade_portal_e2e_8056.log`, which states what the
server did during the run.
Then open the portal and look at it. Do not skip this step. Rule 4 of
`contracts/ui-testids.md` states that a test selects by `data-testid` only, so no
test in this repository reads what an operator sees. Defects 26, 27, and 28 all
passed the whole browser suite, and a person found each one in a few minutes.

Start the production portal:

```powershell
$env:PATHEXT = ".COM;.EXE;.BAT;.CMD;.VBS;.JS;.WS;.MSC;.PS1"
$env:MISTHELPER_STANDALONE = "true"
$env:REDIS_HOST = "127.0.0.1"
.\.venv\Scripts\python.exe -m waitress --listen=127.0.0.1:8056 --threads=4 wsgi_capture:app
```

That portal reaches the sign-in page alone, because the next page needs a live
Mist cloud. To read the inner pages with no cloud, start the stand-in
application of the browser fixture instead:

```powershell
$env:UPGRADE_PORTAL_E2E_SESSION = "1"
.\.venv\Scripts\python.exe -m waitress --listen=127.0.0.1:8056 --threads=4 "tests.e2e.upgrade_portal.conftest:app"
```

`tests/e2e/upgrade_portal/conftest.py` states the cookie settings that the
stand-in needs. The session cookie carries the `HttpOnly` flag, so a browser
script cannot write it. A test tool must set it through a response header.

Read the browser console on each page. An empty console is part of the result.
Defect 26 wrote 23 blocked-resource messages there while every test passed, and
defect 28 wrote a 500 there for every capture that finished.

Read the state of the pull request:

```powershell
$env:APPDATA = "C:\Users\jmorrison\AppData\Roaming"
gh pr checks 1825
```

`gh pr checks` exits with a non-zero code while a check still runs. That is not
a failure. It answers "no checks reported" while the branch conflicts with
`main`, because GitHub starts no check against a conflicted pull request. Read
`gh pr view 1825 --json mergeStateStatus` to tell the two apart.

---

## 10. The other files in this folder

| File | What it holds |
| --- | --- |
| `spec.md` | The requirements, numbered `FR-nnn` |
| `plan.md` | The design and the success criteria |
| `research.md` | The findings that shaped the design |
| `data-model.md` | The collections, the fields, and the schema version |
| `contracts/` | The HTTP interface and the site lock interface |
| `tasks.md` | All 233 tasks. 232 carry a check |
| `ste-audit-2026-08-24.md` | The Simplified Technical English audit of task T228 |
| `live-run-2026-08-24.md` | The first run against a real organization, and the six defects it found |
| `audit-2026-08-20.md` | The task audit and the defect list. Read this before a merge |
| `analysis.md` | The cross-artifact review, findings `G1` to `G6` |
| `quickstart.md` | How to run the portal |
| `quickstart-results.md` | What a real run produced |

The changelog entry sits in `CHANGELOG.md` under the heading
"Add the upgrade capture portal, menu 238 (issue #1823)".
