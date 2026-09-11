# Quickstart: Organization Upgrade Mode for Many Sites

**Feature**: Organization upgrade mode for many sites
**Application**: `src/upgrade_portal` (Flask, Jinja, plain JavaScript)

## Goal

Add an organization scope to the upgrade portal. The operator picks many sites
in one organization. The portal sends one job to the Mist cloud. The job
upgrades access points only.

## Before You Start

Read these files first:

| File | Why |
| - | - |
| `spec.md` | The requirements and the risks |
| `contracts/api-contract.md` | The exact HTTP paths and SDK calls |
| `contracts/ui-contract.md` | The templates and the test identifiers |
| `src/firmware/org_upgrade_body.py` | The body rules |
| `src/firmware/org_upgrade_service.py` | The cloud calls |

Warning: the portal writes firmware to live access points, and a wrong body can
interrupt service at many sites. Run every test offline before a live check.

## Environment

```powershell
cd C:\Users\jmorrison\MistHelper
.\.venv\Scripts\Activate.ps1
python --version    # 3.13 or newer
```

## Baseline

The route lane already exists. `src/upgrade_portal/app/routes/org_upgrade.py`
serves seven paths. `factory.py` registers the blueprint `org_upgrade`.

Two offline suites already pass with 180 tests. Run them first:

```powershell
cd C:\Users\jmorrison\MistHelper
.\.venv\Scripts\python.exe -m pytest tests\contract\upgrade_portal\test_org_upgrade_routes.py tests\unit\upgrade_portal\test_org_upgrade_service.py -q
```

These steps close the remaining gaps.

## Step 1 - Verify the Site Counts

Confirm that `status_summary` reads the target arrays from each site upgrade.
Confirm that it sums the total, upgraded, and failed values.

- **File**: `src/upgrade_portal/app/routes/org_upgrade.py`

## Step 2 - Verify the Write Session

Each portal sign-in sets `_MAX_429_RETRIES` to zero. The transport adapter also
permits zero retries. `OrgUpgradeService._check_write_session` verifies both
conditions before a write.

Warning: do not enable a retry. A repeated request can start a second upgrade
job at every selected site.

## Step 3 - Complete the Options Page

`options_page` already renders `upgrade/org_options.html`. `save_options`
already validates the body with `OrgUpgradeBody.build`.

Add a `serial` strategy option. Add a `force` control. Add a pre-check column to
the site table.

Move the stored body from the session key `org_upgrade_options` to the run
record. The run must recover its options after a worker restart.

## Step 4 - Verify the Browser Confirmation Gate

`org_confirm.html` and `submit_upgrade` use the field `confirmation`. The input
uses the shared gate attributes. The start button is disabled in the markup.
`applyConfirmGate` enables the button only after the exact word `CONFIRM`.

## Step 5 - Add the Write Guards

`submit_upgrade` already checks the mode, the site set, the options, and the
word `CONFIRM`. Add two guards before the write:

1. The portal holds a live lock for every selected site.
2. Every selected site holds a verified pre-check.

Answer `site_locked` with HTTP 409. Answer `lock_store_unreachable` with HTTP
503. Answer `precheck_missing` with HTTP 409.

Warning: do not repeat the write after a transport error, because a second write
can start a second upgrade job. The route answers HTTP 503 with
`org_upgrade_submission_failed` instead.

## Step 6 - Add the Live Poll and the History

`upgrade_status` answers `GET /api/org-upgrades/<upgrade_id>`. The progress page
offers a refresh link and a timed page reload. Verify the interval through
`data-poll-seconds`.

Add `GET /api/org-upgrades` with `listOrgDeviceUpgrades`. The operator reads it
after an uncertain answer.

## Step 7 - Add the Post-Check and the Comparison

Start a post-check for each site when the job reaches a final state. Reuse
`POST /api/runs/<run_id>/capture/start`.

Add one comparison link for each site on the progress page. The link opens
`/compare` with the two capture identifiers.

## Step 8 - Release the Locks

Release every site lock when the run ends. Use
`DELETE /api/sites/<site_id>/lock`.

Release every lock when one acquire fails. A partial lock set must never start a
job.

## Validation Commands

### Lint the Python code

```powershell
cd C:\Users\jmorrison\MistHelper
python -m ruff check src\upgrade_portal src\firmware
python -m ruff format --check src\upgrade_portal src\firmware
```

### Run the focused tests

```powershell
python -m pytest tests\contract\upgrade_portal\test_org_upgrade_routes.py -q
python -m pytest tests\unit\upgrade_portal\test_org_upgrade_service.py -q
python -m pytest tests\unit\firmware\test_org_upgrade_body.py -q
```

### Run the whole portal suite

```powershell
python -m pytest tests\unit\upgrade_portal tests\contract\upgrade_portal tests\e2e\upgrade_portal -q
```

### Check the single-site flow for a regression

```powershell
python -m pytest tests\contract\upgrade_portal\test_select.py tests\e2e\upgrade_portal\test_site_selection.py -q
```

### Grade the Markdown

```powershell
python -m tools.ste_linter --min-score 80 specs\2200-org-multisite-firmware-upgrade\spec.md
```

## Offline Test Rules

`tests/conftest.py` blocks every outbound socket. A test that opens a socket
fails at once.

Use these stand-ins:

| Need | Stand-in | Path |
| - | - | - |
| The Mist SDK | `FakeMistApi` | `tests/contract/upgrade_portal/conftest.py` |
| The capture store | `FakeCaptureStorage` | `tests/contract/upgrade_portal/conftest.py` |
| The org service | `OrgUpgradeServiceStandIn` | `tests/contract/upgrade_portal/test_org_upgrade_routes.py` |
| The SDK endpoints | `EndpointStandIn` | `tests/unit/upgrade_portal/test_org_upgrade_service.py` |
| The HTTP answer | `ResponseStandIn` | `tests/unit/upgrade_portal/test_org_upgrade_service.py` |

Inject a stand-in through the Flask config:

```python
app.config["ORG_UPGRADE_SERVICE"] = OrgUpgradeServiceStandIn()
```

`upgrade_service()` reads that key. The default is the class
`OrgUpgradeService`.

## Manual Check

Run the portal with a test account after the offline tests pass.

1. Sign in at `/auth/signin`.
2. Pick an organization at `/select/org`.
3. Pick `Multi-site` at `/select/mode`.
4. Pick two laboratory sites at `/select/site`.
5. Capture a pre-check for each site.
6. Set the version and the strategy at `/upgrade/org/options`.
7. Read the scope at `/upgrade/org/confirm`.
8. Type `CONFIRM` and start the job.
9. Watch `/upgrade/org/jobs/<upgrade_id>`.
10. Open the comparison for each site.

Warning: use a laboratory organization for the manual check, because a live job
can interrupt service at every selected site.

## Success Checklist

- The seven present routes keep their behavior.
- The single-site paths keep their current behavior.
- The progress page shows a true device count.
- One submission produces one call to `upgradeOrgDevices`.
- A missing confirmation word produces no cloud call.
- A locked site produces HTTP 409.
- An unreachable lock store produces HTTP 503.
- A missing pre-check produces HTTP 409.
- The progress page shows one row for each site job.
- Every test runs offline in under 30 seconds.
- Every changed Markdown file scores 80 or more.
