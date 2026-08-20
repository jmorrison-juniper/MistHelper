# Quickstart Results: Upgrade Pre-Check and Post-Check Portal

**Feature**: 1823-upgrade-capture-portal
**Task**: T232
**Date**: 2026-08-20
**Source**: `specs/1823-upgrade-capture-portal/quickstart.md`

This file records the result of every scenario in `quickstart.md`. Each scenario
carries one result: PASS, FAIL, or BLOCKED. BLOCKED means the environment
prevented the run. A scenario that did not run never counts as a PASS.

---

## 1. Environment

| Item | Value |
| --- | --- |
| Platform | Windows 11, `sys.platform` reports `win32` |
| Interpreter | `.venv\Scripts\python.exe`, called by path |
| WSGI server | Waitress, the sanctioned Windows stand-in |
| WSGI target | `wsgi_capture:app` |
| Bind address | `127.0.0.1:8056` |
| `MISTHELPER_STANDALONE` | `true` |
| `REDIS_HOST` | `127.0.0.1` |
| `CAPTURE_PORT` | Unset, so the portal took the default of 8056 |
| pytest flag | `-p no:playwright` on every call |

Gunicorn cannot run on this platform, because `gunicorn.util` imports `fcntl`
and Windows ships no such module. `src/upgrade_portal/runtime/server.py:52`
selects Waitress on Windows for this reason. The choice is by design.

The port was clear before each start. Waitress sets `SO_REUSEADDR`, so a stale
listener can hide behind a new one.

### The controlling blocker

The file `.env` is absent from this working directory. No cloud token, no Redis
password, and no database password are present. The task forbids reading `.env`,
and no scenario may reach the Mist cloud or live hardware. Every scenario that
needs a cloud session, the site lock, or the database is therefore BLOCKED.

`GET /readyz` reports `database: unreachable` and `redis: unreachable`. The lock
store logs an authentication error. Both results follow from the absent
credentials. Neither result is a product defect.

---

## 2. Results

| # | Scenario | Result | Evidence |
| --- | --- | --- | --- |
| 1 | Prerequisites (section 1) | BLOCKED | `.env` is absent, so no cloud token, no Redis password, and no database password exist. `GET /readyz` answers 503 with `database: unreachable` and `redis: unreachable`. |
| 2 | Start from the command line (section 2) | BLOCKED | `python MistHelper.py --capture-portal` exits before it opens a port. The log reads `Credential/config preflight failed: no API token found - set MIST_APITOKEN or MIST_API_TOKEN`. See section 3 below. |
| 3 | Start from the container (section 2) | BLOCKED | The shared container host already runs Redis, ArangoDB, and another lane's container. `podman compose up -d` would disturb work that other lanes depend on. |
| 4 | Scenario A, the first capture (section 3) | BLOCKED | The scenario needs a signed-in operator, a cloud organization, and a database write. No token and no database credential exist. |
| 5 | Scenario B, compare two captures (section 4) | BLOCKED | The scenario needs two stored captures. No capture can be written without the database credential. |
| 6 | Scenario C, upgrade with the settle gate (section 5) | BLOCKED | The scenario writes firmware to real devices. The task forbids live hardware. No laboratory site and no token exist. |
| 7 | Scenario D, the stop control (section 6) | BLOCKED | The scenario needs a running upgrade, which needs live hardware. |
| 8 | Scenario E, two operators and one site (section 7) | BLOCKED | The site lock lives in Redis. The local Redis demands a password that lives in `.env`. The lock request answers 503 and the log names an authentication error. |
| 9 | Scenario F, the history view (section 8) | BLOCKED | The history page reads stored captures. No capture exists without the database credential. |
| 10 | pytest unit and contract (section 9) | PASS | `pytest tests/unit/upgrade_portal tests/contract/upgrade_portal -p no:playwright` reported 2461 passed and 0 failed. |
| 11 | pytest browser journeys (section 9) | BLOCKED | The task requires `-p no:playwright`. That flag removes the `context` and `page` fixtures, so all 129 tests skipped with cause `('context', <SubRequest 'page' ...>)`. Playwright and its Chromium build are installed, so the browsers are not the blocker. |
| 12 | ruff (section 9) | PASS | `ruff check src/upgrade_portal src/firmware/upgrade_service.py` exited zero with no finding. |
| 13 | mypy (section 9) | PASS | `Success: no issues found in 40 source files`. |
| 14 | black --check (section 9) | PASS | 40 files reported unchanged. |
| 15 | interrogate (section 9) | PASS | Coverage reached 100.0 percent against the floor of 90.0 percent. |
| 16 | pydoclint (section 9) | BLOCKED | `No module named pydoclint`, exit 1. The tool is absent from the virtual environment and from `pyproject.toml`. The task forbids installing it. See section 4. |
| 17 | bandit (section 9) | PASS | `No issues identified`. |
| 18 | Menu registration guardrail (section 10) | PASS | `test_menu_238_carries_the_destructive_registry_entry` passed in `tests/unit/upgrade_portal/test_guardrails.py`. |
| 19 | Primary key strategy guardrail (section 10) | PASS | `test_the_portal_write_endpoint_uses_natural_pk` passed for `upgradeCaptureWrite` and `upgradeRunWrite`. Both use `natural_pk`. |
| 20 | Theme file tracked (section 10) | PASS | `magenta.css` is tracked and no ignore rule matches it. The name holds none of the excluded brand strings. |
| 21 | Container assets (section 10) | BLOCKED | The check needs `podman build` on the shared container host. See scenario 3. |
| 22 | No credential appears (section 11.1) | PASS | A search of the portal log and three rendered pages against every credential value in the process environment returned 0 matches. |
| 23 | Every asset loads from the portal (section 11.2) | PASS | The content security policy is `'self'` only. The vendored Bootstrap asset answered 200 from the portal. No outside host appears in any page. |
| 24 | The log is ASCII only (section 11.3) | PASS | No character above the ASCII range appears in the log output. |
| 25 | The packet-capture word never appears (section 11.4) | PASS | The word `capture` always means a record of site state. No packet sense appears. |
| 26 | The reserved word stays reserved (section 11.5) | PASS | The word `snapshot` appears as an identifier only at `src/firmware/upgrade_service.py:66`, where it is the field name the cloud upgrade body demands for a Junos file action. Other uses are prose about statistics readings. The feature never names its own record with the reserved word. |

**Totals**: 26 scenarios. 13 PASS. 0 FAIL. 13 BLOCKED.

---

## 3. Why the command-line launcher does not start

The launcher at `python MistHelper.py --capture-portal` stops before it binds a
port. The reason is the credential preflight.

`src/refactors/main_entrypoint.py:56` establishes the Mist session. Line 58 then
dispatches the mode. `MistHelper.py:5315` runs the token preflight inside the
session step, so the preflight always runs first.

The existing web portal sits at `MistHelper.py:5794` in the same dispatch table.
The capture portal sits at line 5795. Both portal modes follow the same session
step, so both need a token to start.

This behavior is not new and it is not a defect of this feature. The capture
portal inherits the entry sequence that the web portal already uses. Section 1 of
`quickstart.md` names the cloud token as a prerequisite, and that prerequisite is
unmet here.

The portal application itself starts without a token. Waitress served
`wsgi_capture:app` on port 8056, `GET /healthz` answered 200, and the sign-in
page rendered. This proves the fault lies in the absent credential and not in the
portal.

---

## 4. Findings for the lead

1. **`pydoclint` is absent.** Section 9 of `quickstart.md` lists
   `pydoclint --style=google src/upgrade_portal` as an automated check. The tool
   is in neither the virtual environment nor `pyproject.toml`. The docstring gate
   that this project actually runs is `pydocstyle`. Either add the dependency or
   correct the quickstart command. This is a tooling gap, not a code defect.
2. **File contents flapped during the test run.** This working directory sits on
   a synchronized OneDrive path. Two early test runs reported different failures
   in `src/upgrade_portal/runtime/identity.py`. A read from disk showed the file
   held correct content, and the reported line differed from the stored line. A
   later run of the same tests passed. Treat any lone test failure in this
   directory as suspect and repeat the run before you record it.
3. **No product defect appeared.** Every check that the environment allowed
   passed. No scenario failed.
