# Handoff: upgrade capture portal (issue #1823)

**Last updated**: 2026-08-21.
**Branch**: `feat/1823-upgrade-capture-portal`.
**Pull request**: [#1825](https://github.com/jmorrison-juniper/MistHelper/pull/1825).

Read this file first if you take over this feature. It states what is complete,
what waits, and what a person must decide. The other files in this folder state
the design. This file states the position.

---

## 1. Status at a glance

| Item | State |
| --- | --- |
| Tasks in `tasks.md` | 224 of 233 complete. An audit removed 13 checks, and 4 are back |
| Continuous integration on the pull request | 18 checks pass, 2 skip |
| Pull request | Open, mergeable, not a draft, no review yet |
| Local commits not pushed | None |
| Uncommitted work | None from this feature |
| Portal tests | 2591 unit and contract, all pass. 132 browser tests, all pass, 0 skip |
| Statement coverage of the package | 94.18 percent |
| Blocking defects | None. The eight defects of `audit-2026-08-20.md` sections 2.1, 6, 7, 8, 9, and 10 are fixed |

The code is written, the code tests pass, and the browser suite drives every
journey with no skip. An audit on 2026-08-20 found 25 defects. The 8 that could
mislead or stop an operator are fixed. The rest are recorded and open.

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

Read `audit-2026-08-20.md` before you merge. It holds the 13 tasks that lost a
check, the 4 that earned it back, the defects inside tasks that keep a check,
and the order to fix them in.

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

### 4.0 The audit of 2026-08-20

`audit-2026-08-20.md` holds the whole result. The short form:

| Group | Count | Where | State |
| --- | --- | --- | --- |
| Tasks that lost a check | 13 | Audit section 1.1 | 4 are back |
| Defects that can hurt a device | 2 | Audit section 2.1 | Both fixed |
| Defects of high severity | 2 | Audit section 2.2 | Both fixed |
| Other defects | 17 | Audit sections 2.3 to 2.7 | Open |
| Defects the browser tests found | 4 | Audit sections 6 to 9 | All fixed |
| Defects a person found by eye | 2 | Audit section 10 | Both fixed |

The two defects of audit section 2.1 told an operator that the cloud stopped a
device, when the code cannot know that. An operator who reads that word can cut
power to a switch that is writing firmware, and that switch does not start
again. Commit `4a9d028` fixed both.

Nine tasks still carry no check. They are the remaining browser identifiers of
T172, the two measurement tasks T153 and T219, the two field tasks T067 and
T080, the three audit tasks T227, T228, and T233, and the quickstart run T232.

### 4.1 Merge the pull request

Pull request #1825 is open and mergeable. Every gate passes, and no blocking
defect remains. Run every scenario of `quickstart.md` against a real site first,
which is task T232, because no run of this feature has ever reached a real site.

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

### Style

- Simplified Technical English governs every word a person reads. The guide is
  `documentation/ASD-STE100_writing-guide.md`. It outranks the caveman rules.
- Every module, class, and function needs a docstring with a `Why` section.
  `interrogate` holds the floor at 90 percent.
- Line length is 120.

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

---

## 9. How to check the work yourself

Run the portal suite:

```powershell
$env:PATHEXT = ".COM;.EXE;.BAT;.CMD;.VBS;.JS;.WS;.MSC;.PS1"
.\.venv\Scripts\python.exe -m pytest tests/unit/upgrade_portal tests/contract/upgrade_portal -q -p no:playwright
```

Expect 2591 passes.

Run the browser suite. It starts a portal of its own, so free port 8056 first:

```powershell
$env:PATHEXT = ".COM;.EXE;.BAT;.CMD;.VBS;.JS;.WS;.MSC;.PS1"
$env:MISTHELPER_STANDALONE = "true"
$env:REDIS_HOST = "127.0.0.1"
.\.venv\Scripts\python.exe -m pytest tests/e2e/upgrade_portal -q
```

Expect 132 passes and no skip. A skip means the harness hid a broken portal.
The portal writes its own log to `$env:TEMP\upgrade_portal_e2e_8056.log`, which
states what the server did during the run.

Then open the portal and look at it. Do not skip this step. Rule 4 of
`contracts/ui-testids.md` states that a test selects by `data-testid` only, so no
test in this repository reads what an operator sees. Defects 26 and 27 both
passed the whole browser suite, and a person found both in a few minutes.

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
Defect 26 wrote 23 blocked-resource messages there while every test passed.

Read the state of the pull request:

```powershell
$env:APPDATA = "C:\Users\jmorrison\AppData\Roaming"
gh pr checks 1825
```

`gh pr checks` exits with a non-zero code while a check still runs. That is not
a failure.

---

## 10. The other files in this folder

| File | What it holds |
| --- | --- |
| `spec.md` | The requirements, numbered `FR-nnn` |
| `plan.md` | The design and the success criteria |
| `research.md` | The findings that shaped the design |
| `data-model.md` | The collections, the fields, and the schema version |
| `contracts/` | The HTTP interface and the site lock interface |
| `tasks.md` | All 233 tasks. 220 carry a check |
| `audit-2026-08-20.md` | The task audit and the defect list. Read this before a merge |
| `analysis.md` | The cross-artifact review, findings `G1` to `G6` |
| `quickstart.md` | How to run the portal |
| `quickstart-results.md` | What a real run produced |

The changelog entry sits in `CHANGELOG.md` under the heading
"Add the upgrade capture portal, menu 238 (issue #1823)".
