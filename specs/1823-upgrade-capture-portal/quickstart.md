# Quickstart: Upgrade Pre-Check and Post-Check Portal

**Feature**: 1823-upgrade-capture-portal
**Purpose**: Prove the feature works end to end. This file is a validation guide,
not an implementation guide.

Read `plan.md` for the design. Read `contracts/` for the interfaces. Read
`data-model.md` for the stored shapes.

---

## 1. Prerequisites

| Item | Requirement | How to check |
| --- | --- | --- |
| Python | 3.13 or later | `python --version` |
| Dependencies | Installed from `pyproject.toml` | `uv sync` |
| Cloud token | Present in the environment by variable name | The portal reads it by name and never prints it |
| ArangoDB | Reachable on port 8529 | `GET /readyz` reports `database: ok` |
| Redis | Reachable on port 6379 | `GET /readyz` reports `redis: ok` |
| Port 8056 | Free | The portal refuses to start if the port is busy |
| Playwright browsers | Installed | `playwright install chromium` |

Warning: The environment holds a live production token. Every scenario below acts
on a real organization. Run a capture scenario first. Run an upgrade scenario only
on a laboratory site.

---

## 2. Start the portal

### From the command line

```powershell
python MistHelper.py --capture-portal
```

Then open `http://127.0.0.1:8056/`.

The menu path also works. Choose menu **238** from the main menu.

### From the container

```powershell
podman compose up -d
podman ps
```

The container publishes port 8056 next to the existing port 8055. Both portals run
at the same time. Each portal owns its own process.

Expected result: `podman ps` shows the container with both ports published, and
`http://127.0.0.1:8056/healthz` answers `{"status": "ok", ...}`.

---

## 3. Scenario A — the first capture (User Story 1)

**Goal**: Record the state of a site and prove the portal stored it.

| Step | Action | Expected result |
| --- | --- | --- |
| 1 | Sign in with an operator account | The organization list appears |
| 2 | Choose an organization | The site list appears with a device count for each site |
| 3 | Choose a site | The inventory view appears |
| 4 | Leave the tier at 2 and start a capture | The progress region appears at once |
| 5 | Wait | The progress region updates about every 30 seconds |
| 6 | Wait for the finish | The verified badge appears |

**Pass conditions**

1. A 250-device site finishes in 90 seconds or less. This is a performance goal
   of `plan.md`, and not the success criterion SC-002. SC-002 is a 30-second
   read of the finished comparison. Issue #1998 records the correction.
2. The verified badge is present. The badge means the portal read the stored key
   back and matched the digest.
3. The stored size shows a value above zero.
4. The device count in the capture equals the count in the inventory view.
5. Every chassis member appears as its own row. A two-member virtual chassis shows
   two rows.

**Failure to investigate**

- A capture that finishes but shows no verified badge means the database write did
  not land. Check `GET /readyz`. Issue #1824 records the router defect that hides
  this failure from other callers.
- A capture with only access points in the device list means the code did not pass
  `type="all"` to the device statistics call.

---

## 4. Scenario B — compare two captures (User Story 2)

**Goal**: Show every difference between two records of the same site.

| Step | Action | Expected result |
| --- | --- | --- |
| 1 | Take a capture, then take a second capture a few minutes later | Two verified captures exist |
| 2 | Open the comparison page | The two captures appear in the picker |
| 3 | Choose the earlier capture as the before and the later as the after | The comparison renders |
| 4 | Read the statistics region | Counts appear for devices and for clients |
| 5 | Filter to the missing clients | Only missing clients remain |
| 6 | Download the comparison as CSV | The file downloads |

**Pass conditions**

1. The comparison renders in 3 seconds or less (SC-005).
2. A client that changed access point counts as `moved`, never as `missing`.
3. Two captures taken minutes apart on a quiet site show zero device changes.
4. The skipped section list names any section whose digest matched.
5. The CSV holds one row for each difference and no credential value.

**Failure to investigate**

- Every client shown as new means the code did not strip `timestamp` from the
  match key. The match key is `mac` alone.
- A comparison that refuses with `capture_site_mismatch` means the two chosen
  captures belong to different sites. That refusal is correct.

---

## 5. Scenario C — upgrade with the settle gate (User Story 3)

Warning: This scenario writes firmware to real devices. Run it on a laboratory
site only. The action cannot be undone.

| Step | Action | Expected result |
| --- | --- | --- |
| 1 | Open a laboratory site | The lock banner shows the site is free |
| 2 | Take the lock | The banner shows your name and a countdown |
| 3 | Take a pre-check capture | A verified pre-check exists |
| 4 | Choose target versions | The target table lists each device with its target |
| 5 | Try to start without typing | The portal refuses with `confirmation_required` |
| 6 | Type `CONFIRM` and start | The run state moves to `upgrade_submitting` |
| 7 | Watch the phase list | Phases settle in order: gateways, switches, access points, clients |
| 8 | Wait for the post-check | The post-check runs on its own |
| 9 | Read the comparison | The comparison opens with the two captures already chosen |

**Pass conditions**

1. The portal refuses to start the upgrade when no verified pre-check exists.
2. The phases settle in the fixed cascade order. A later phase never starts before
   an earlier phase settles.
3. A device counts as settled only after three signals: a reconnect event, an
   uptime that decreased together with a version that changed, and then an extra
   wait of 60 seconds. An access point waits a further 60 seconds.
4. The run status endpoint answers in under 1 second while an upgrade runs.
5. The post-check capture starts on its own after the client phase settles.

**Failure to investigate**

- A switch phase or a gateway phase that never settles means the event search did
  not pass `device_type`. The default value is `ap`, so the search finds nothing
  for another type.
- A device that settles at once means the gate read a cloud timestamp against the
  local clock. The gate must compare the reported uptime instead.
- A run that reports a missing phase field means the code read `phase`. The field
  is `current_phase`.

---

## 6. Scenario D — the stop control (FR-038a to FR-038i)

| Step | Action | Expected result |
| --- | --- | --- |
| 1 | Start an upgrade on a site with several devices | The run reaches `upgrade_running` |
| 2 | Press the stop control | A dialog asks for the word `STOP` |
| 3 | Type the wrong word and submit | The portal refuses with `confirmation_required` |
| 4 | Type `STOP` and submit | The outcome region appears |
| 5 | Read the outcome | Three lists appear, plus one plain sentence |

**Pass conditions**

1. The portal cancels every device that has not started writing firmware.
2. The portal never interrupts a device that is writing firmware. That device
   appears in the `already_writing` list.
3. The outcome message states plainly that a device in mid-flash will finish.
4. A session smart router cancels through the organization-scope call. The run
   record shows `scope: "org"` for that device.

**Reference**: The cancel functions exist. See `research.md` question Q1 for the
file and the line of each one. The cloud states the cancel is best effort.

---

## 7. Scenario E — two operators, one site (User Story 4)

| Step | Action | Expected result |
| --- | --- | --- |
| 1 | Sign in as operator A in one browser and take the lock | Operator A holds the lock |
| 2 | Sign in as operator B in a second browser and open the same site | Operator B sees the site and its data |
| 3 | Operator B tries to start an upgrade | The portal refuses with `409 site_locked` |
| 4 | Operator B opens a comparison and a history page | Both pages work with no typing |
| 5 | Operator A closes the browser and waits 5 minutes | The cooldown passes |
| 6 | Operator B takes the lock | The portal asks for the word `CONFIRM` |
| 7 | Operator B types `CONFIRM` | Operator B holds the lock |
| 8 | Operator A opens the site again in the same browser | Operator A sees that the lock moved |

**Pass conditions**

1. Viewing data never asks for typed text.
2. The refusal names the holder, so operator B knows whom to ask.
3. The lock survives a portal restart. Restart the portal at step 3 and repeat
   step 3. The refusal is the same.
4. Two portal workers give the same answer. The lock lives in Redis, never in
   process memory.

---

## 8. Scenario F — the history view (User Story 6)

| Step | Action | Expected result |
| --- | --- | --- |
| 1 | Open the history page for a site | Past captures appear in time order |
| 2 | Read the stored size column | Each row shows a size |
| 3 | Open an old capture | The capture page renders |
| 4 | Compare an old capture with a new one | The comparison works across any two captures of that site |

**Pass conditions**

1. No capture disappears with age. Retention is unlimited.
2. Every row shows the stored size, so an operator can watch the growth.
3. A capture written by an older schema version still opens, or the page says
   plainly that the version is too new to render.

---

## 9. Automated checks

Run each command from the repository root.

```powershell
# Unit and contract tests for the new package
pytest tests/unit/upgrade_portal tests/contract/upgrade_portal -v

# Browser journeys
pytest tests/e2e/upgrade_portal -v

# Lint and types. Both now cover the new package, because it lives under src/.
ruff check src/upgrade_portal src/firmware/upgrade_service.py
mypy src/upgrade_portal src/firmware/upgrade_service.py

# Formatting
black --check src/upgrade_portal src/firmware/upgrade_service.py

# Docstring coverage. The floor is 90.
interrogate -v src/upgrade_portal src/firmware/upgrade_service.py

# Docstring style. This project installs pydocstyle, and it installs no pydoclint.
pydocstyle --convention=google src/upgrade_portal

# Security
bandit -r src/upgrade_portal src/firmware/upgrade_service.py
```

**Expected result**: every command exits zero. Coverage for the new package is 90
or above.

---

## 10. Guardrail checks

These checks fail the build when the change misses a required step.

| Check | Command | Expected |
| --- | --- | --- |
| Menu registration | The operation registry guardrail test | Menu 238 has a category entry |
| Primary key strategy | The strategy guardrail test | `upgradeCaptureWrite` and `upgradeRunWrite` are present and use `natural_pk` |
| Theme file tracked | `git status --porcelain src/upgrade_portal/app/assets/static/css/themes/` | The file is tracked, not ignored |
| Container assets | `podman build` then list the image contents | The theme file is inside the image |

**Why the theme check matters.** `.gitignore` and `.dockerignore` exclude any path
that holds `tmo`, `TMO`, `t-mobile`, or `T-Mobile`. A brand-named stylesheet would
stay untracked and would never reach the image. The chosen name is `magenta.css`,
which holds none of those strings.

---

## 11. Manual checks that no automated test replaces

1. **No credential appears anywhere.** Search the portal log and the page source
   for the token variable value. Expected: zero matches. The portal names the
   variable, never the value.
2. **Every asset loads from the portal itself.** Open the browser network view.
   Expected: no request to an outside host. The content security policy is `'self'`
   only.
3. **The log is ASCII only.** Read `data/` log output. Expected: no character
   above the ASCII range.
4. **The word for a packet capture never appears.** The word `capture` in this
   portal always means a record of site state.
5. **The reserved word stays reserved.** The portal never uses the word that the
   cloud upgrade body already takes for a Junos file action.

---

## 12. Known limitation to expect

`GET /readyz` performs a real write and a real read-back. A plain connection check
would report ready while every write failed silently.
`src/export/data_exporter.py:141` gates polyglot writes on a container check, and
`src/db/router.py:372-382` returns success after writing zero rows. Issue #1824
tracks that repair. The portal does not wait for it, because the portal verifies
its own write.
