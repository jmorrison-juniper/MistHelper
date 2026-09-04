# Handoff: the upgrade rehearsal harness, issue #1992

Written 2026-09-04 at the request of the operator, who is changing the agent
model. This file holds the state and the reasoning that was still in flight.

Delete this file before the pull request merges. It is a note between agents and
it is not a document of the repository.

## Where the work sits

| Item | Value |
| - | - |
| Branch | `feat/1992-upgrade-rehearsal`, pushed to `origin` |
| Commit | `c146459a`, 28 files, 4401 insertions |
| Worktree | `../MistHelper-agent-1992`, bootstrapped, `.venv` ready |
| Base | `a21236f2`, the head of `main` at the time |
| Pull request | **None yet. Not opened.** |

The work is committed and pushed, so no disk loss can destroy it. That was
deliberate. This same session filed issue #2251, which records five branches
that were deleted with unpushed work on them.

## What the next agent should do first

1. Open the pull request. The body needs the measurements, which sit in section
   "Evidence already gathered" below.
2. Wait for the full check set. Read the caution about the changelog below
   first, because a rebase may be needed.
3. Do **not** merge until the two open questions below are answered.

## The state of the speckit workflow

| Step | State |
| - | - |
| `speckit.specify` | Done. `specs/1992-upgrade-rehearsal/spec.md` |
| `speckit.clarify` | Skipped on purpose. The specification holds no open clarification, and the requirements checklist passes all 16 items |
| `speckit.plan` | Done. `plan.md`, `research.md`, `data-model.md`, two contract files |
| `speckit.tasks` | Done. `tasks.md`, 53 tasks in 7 phases |
| `speckit.implement` | Reports all 53 tasks done |
| `speckit.analyze` | **Not run.** This is the natural next step |

## What I verified myself, and what I did not

I do not take an agent report as proof. These are the checks I ran with my own
hands.

Verified:

- The 48 rehearsal tests pass in 2.67 seconds. I ran them.
- `harness.py` imports the shipped `driver`, `events`, `gate`, and `phase_gate`,
  and it builds the shipped `gate.SettleGate`. The harness therefore drives the
  shipped path and not a copy of it. This was the single claim most worth
  checking, because a harness that misses the shipped gate proves nothing.
- All four clock seats that the plan depends on exist in the shipped code:
  `SettleGate.__init__(clock=)` at `gate.py:928`, `PhaseGateDeps.sleep`,
  `CloudReconnectReader` at `phase_gate.py:246`, and `RunDriverDeps` at
  `driver.py:722` with the `Clock` protocol at line 244.
- `drain_device_events` at `events.py:470` and `read_fleet_statistics` at
  `gate.py:817` exist, which is where the stand-in attaches.

Not verified by me, and reported by the implement agent alone:

- The full portal suite at 2856 passed. The agent reports it, and the number is
  consistent with the earlier baseline of 2808 plus the 48 new tests. I did not
  re-run it. It takes about 6 minutes.
- Every Phase 7 quality gate. The agent reports each one as a pass with a
  number. The continuous integration run will settle this, so it needs no
  separate local run.
- The three defect drills. The agent reports that each drill fails the
  rehearsal. **This is the claim worth checking by hand**, for the reason in the
  next section.

## The one thing I would check next, and why

Run the defect drills and read what they assert.

```powershell
cd ..\MistHelper-agent-1992
.venv\Scripts\python.exe -m pytest tests/unit/upgrade_portal/test_rehearsal_defects.py -v
```

A drill that passes for the wrong reason is the failure mode that matters here.
The whole value of this feature rests on the claim that the harness catches a
broken settle gate. If a drill asserts something weaker than a real failure, the
harness gives false confidence about a code path that writes firmware to
production hardware.

The implement agent reported one such error in its own work and repaired it: its
first cascade fleet passed `started_at=0.0` while the clock starts at an epoch
moment, so every scripted event sat far in the past and two tests passed for the
wrong reason. That the agent found and stated this raises my confidence in the
report. It does not replace a read of the drill assertions.

## Two open questions that block a merge

**1. Does the pull request close issue #1992, or only advance it?**

My reading: it advances the issue and does not close it. The acceptance of
#1992 asks that `quickstart-results.md` record every scenario as pass with none
blocked, and that T232 carry a check. Scenario C and scenario D still need a
live run against real hardware, which the issue itself says is a human
decision. The commit message therefore says `Refs #1992` and not `Closes`.

The next agent should keep that unless the operator decides otherwise.

**2. Should the harness also run in continuous integration as a gate?**

The tests sit under `tests/unit/upgrade_portal/`, so the existing pytest gate
picks them up with no workflow change. That is the cheap and correct answer, and
it needs no action. Raise this only if the operator wants a separate named gate.

## Cautions for the next agent

**The changelog is a conflict source.** This commit touches `CHANGELOG.md` with
84 changed lines. Issue #1899 records that every concurrent pull request
collides on the changelog head. If the pull request reports a conflict, rebase
onto `main` and keep both entries.

**The `ops-portal` check can fail for a reason that is not yours.** It reaches
the npm advisory service. Pull request #2271 bounded that call, so a failure now
should be a real finding. It is not a required check, so it does not block a
merge.

**Never run scenario C or scenario D.** The portal at port 8056 points at the
live Morrison House Site. That site holds one EX4100-F-12P that carries power
over Ethernet for six access points. Issue #2007 records that this switch
rebooted once with the reboot control off and the site lost service for about
six minutes. The rehearsal exists so that no one has to discover portal logic
against that hardware.

**The operator asked for a speckit workflow.** Stay in it. `speckit.analyze` is
the remaining step, and it cross-checks the specification, the plan, and the
tasks against the delivered code.

## Evidence already gathered, for the pull request body

- 48 rehearsal tests, 2.67 seconds. Budgets are 60 seconds for the suite and 1
  real second for any single test, so both hold with wide margin.
- The whole portal suite: 2856 passed, from a baseline of 2808.
- Gates as reported: ruff clean, black clean, mypy clean, pylint 9.78 against a
  floor of 9.5, radon with no block at C, vulture clean, pydocstyle clean,
  interrogate at 100 percent of 71 objects, and the Simplified Technical English
  linter between 95 and 99 on 11 Markdown files.
- Two gate commands needed a change, and both are recorded in section 13 of
  `specs/1992-upgrade-rehearsal/quickstart.md`. `pyproject.toml` excludes
  `tests` from mypy, so the run uses a small separate configuration file.
  Pylint needs an init hook, because the worktree directory name carries a dash
  and pylint then reports a false import error.

## The reasoning behind the shape of this feature, which no artifact states

I chose this feature over two alternatives, and the choice is worth knowing.

The obvious reading of issue #1992 is "run scenarios C and D". I refused that,
because it writes firmware to the operator's production site and the issue says
a person must make that call.

The second option was a runbook that makes the live run safer. I rejected it
because a document proves nothing about the code.

The third option, which I took, treats the pass conditions of C and D as what
they mostly are: statements about portal logic that the answers of the cloud
drive. The cascade order, the three settle signals, the stop partition, and the
automatic post-check are all decided by what the cloud reports. Only two facts
truly need hardware, and those are that the cloud accepts the call and that a
device reboots. `live-checklist.md` holds exactly those.

That is why the feature is a rehearsal and not a runbook, and why it advances
issue #1992 rather than closing it.
