# Upgrade capture portal

The upgrade capture portal is a web page for a firmware upgrade. The portal
records the state of a Juniper Mist site before the upgrade and after the
upgrade. The portal then shows you what changed.

In this portal, a **capture** is one record of the state of one site at one
moment. A capture holds the devices, the clients, and the alarms of that site.
A capture is not a packet capture.

The portal listens on port 8056. The data browsing portal listens on port 8055.
The two portals are different programs.

## The operator workflow

1. Start the portal.
2. Give your identity on the sign-in page.
3. Choose an organization.
4. Choose a site.
5. Take the pre-check capture.
6. Choose the target firmware version for each device.
7. Type the word `CONFIRM` to start the upgrade.
8. Read the progress page while the upgrade continues.
9. Wait. The portal takes the post-check capture without a command.
10. Read the comparison of the two captures.

## The five views

The portal offers five views. The table names each view, its address, and its
purpose.

| View | Address | Purpose |
| --- | --- | --- |
| Credential | `/auth/signin` and `/auth/twofactor` | Choose the credential mode and give your identity. |
| Selection | `/select/org`, `/select/site`, `/select/site/<site_id>`, and `/runs/<run_id>/options` | Choose the organization, the site, the device, and the upgrade options. |
| Capture | `/captures/<capture_id>` | Run a capture and read its tables. |
| Progress | `/runs/<run_id>` | Read the upgrade state of every device. |
| Comparison | `/compare` | Read the two captures side by side, with the statistics. |

The confirmation page at `/runs/<run_id>/confirm` sits between the selection
view and the progress view. That page holds the start control.

The progress view also holds the stop control. The page `/runs/<run_id>` renders
the template `upgrade/progress.html`. That template includes the template
`upgrade/stop.html`, so the portal needs no separate stop page.

The history view at `/history` sits outside the five views. Read
[The history page](#the-history-page) for that view.

## The confirmation phrases

Some actions need typed text. The portal compares the text exactly, so the
letter case must match.

| Phrase | Action | Where you type it |
| --- | --- | --- |
| `CONFIRM` | Start the upgrade. Take a quiet site from another operator. | The confirmation page. The site lock banner. |
| `STOP` | Stop a run that already started. | The stop control on the run page. |
| `continue` | Return to your own quiet session. | The site lock banner. |
| `CANCEL <run-count> RUNS` | Cancel selected pre-cloud runs. | The bulk preview dialog. |
| `RETRY <run-count> RUNS` | Retry selected final runs. | The bulk preview dialog. |
| `RECONCILE <run_id>` | Reconcile one stale run. | The run page. |

Type `CONFIRM` and `STOP` in capital letters. Type `continue` in small letters.
Type the bulk and reconciliation phrases exactly as the page shows them.

**Caution:** wrong text causes a refusal, and the portal changes nothing. If
the portal refuses the text, type it again with the correct letter case.

## Before you start

| Item | Requirement |
| --- | --- |
| Python | 3.13 or later |
| Port 8056 | Free on the host |
| ArangoDB | Reachable. The portal writes every capture there. |
| Redis | Reachable. Redis holds the site lock. |
| Browser | A current browser with JavaScript enabled |
| Cloud credential | An API token in the environment, or a Mist account with a password |

Open `http://127.0.0.1:8056/readyz` to test the two stores. A good answer
reports `"status": "ready"`, `"database": "ok"`, and `"redis": "ok"`. The route
writes a record and reads the record back, so a `ready` answer is a real test
and not a guess.

Open `http://127.0.0.1:8056/healthz` to test the web process alone. That route
reads no store.

## Start the portal

The portal has two start paths. Both paths reach the same program.

**From the menu.** Start MistHelper, then choose menu entry **238**. The entry
text is `Launch the upgrade capture portal on port 8056 (pre-check, upgrade,
post-check)`.

**From the command line.** Run this command:

```bash
python MistHelper.py --capture-portal
```

The console prints the address. Open that address in a browser.

To stop the portal, press `Ctrl+C` in the console.

The command validates `MIST_HOST`, but it does not require `MIST_APITOKEN` or
`MIST_API_TOKEN` at startup. Without an environment token, the sign-in page
offers the browser token mode.

### Environment variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `CAPTURE_PORT` | `8056` | The listen port. Text that is not a number falls back to 8056. |
| `CAPTURE_HOST` | loopback, or every address in a container | The listen address of the launcher. |
| `CAPTURE_SECRET_KEY` | none | The key that signs the session cookie. |
| `CAPTURE_POLL_SECONDS` | `30` | The wait between two browser status calls. The range is 5 to 3600. |
| `CAPTURE_THEMES` | `default,magenta` | The stylesheet names that the portal offers. |
| `CAPTURE_ALLOWED_IPS` | none | A comma list of networks that may reach the portal. |
| `CAPTURE_PROXY_HOPS` | `0` | The count of trusted reverse proxies in front of the portal. |
| `ARANGO_HOST` | `http://misthelper-arangodb:9529` | The URL of the primary store. |
| `ARANGO_DATABASE` | `misthelper` | The database name inside that store. |
| `ARANGO_USERNAME` | `root` | The account name for the store. |
| `ARANGO_ROOT_PASSWORD` | none | The store password. |
| `REDIS_HOST` | `redis-stack` | The host that holds the site lock. |
| `REDIS_PORT` | `6379` | The port of that host. |
| `REDIS_PASSWORD` | none | The Redis password. |
| `MIST_APITOKEN` or `MIST_API_TOKEN` | none | The cloud API token. |

The two store defaults are container service names. No desktop host uses the
name `arangodb` or the name `redis-stack`. If you start the portal on a
desktop, set `ARANGO_HOST` and `REDIS_HOST` to your own addresses.

On a desktop, the launcher binds loopback only. The portal then accepts a
connection from that desktop alone. In a container, the launcher binds every
address, because a published port cannot reach a loopback bind. A `CAPTURE_HOST`
value wins over both defaults.

**Warning:** a person who reaches this portal can start a firmware upgrade on
your production hardware. The portal has no password. The work email holds the
site lock and names the operator. It does not stop a stranger. If you set
`CAPTURE_HOST` to an address of your network, add an authenticating proxy in
front of the portal. You can also set `CAPTURE_ALLOWED_IPS` to the networks that
may reach the portal.

## Give your identity

The sign-in page asks for your work email address. The portal uses that address
as your name on the site lock and on every record that you write.

The page offers three credential modes.

| Mode | Value in the request | Password needed |
| --- | --- | --- |
| Environment API token | `environment_token` | **No** |
| Mist account | `provider_login` | **Yes** |
| Browser API token | `browser_token` | **No** |

The browser token control appears only when the portal starts without an
environment token. The portal sends the token to Mist for the current browser
session. It reads the safe token name from Mist and uses that name for the
audit record and site lock. The portal does not store, show, or log the token.

**Environment API token.** The portal reads the token from the environment
variable `MIST_APITOKEN` or `MIST_API_TOKEN`. You type your email address and
no password. The portal offers this mode only when one of the two variables
holds a value. The portal tests for the presence of the variable and never
prints the value.

**Mist account.** This is the default mode. You type your email address, your
password, and you choose a cloud. If your account has a second factor, the
portal asks for the code on a second page. The portal accepts a cloud from its
own catalog only, so a password never travels to an unknown server. The
default cloud label is `Global 01`.

The portal writes no credential to disk and no credential to the log.

If the sign-in fails, the page shows one of these messages:

- `The portal could not sign you in. Check the address and the password, then try again.`
- `The portal received no password. Type your password, then try again.`
- `The second factor step is no longer open. Start the sign-in again.`

The portal also writes a cookie named `browser_id`. That cookie lives 365 days.
The cookie identifies your browser, and the site lock needs it. Read
[The site lock](#the-site-lock) for the reason.

## Choose an organization and a site

After the sign-in, the portal opens the organization page at `/select/org`.
Choose one organization. The portal then lists the sites of that organization.

Each site row shows the lock state.

| State | Meaning |
| --- | --- |
| `free` | No operator holds the site. You can take the site. |
| `locked` | An operator holds the site. |
| `unknown` | The portal cannot read Redis, so it cannot answer. |

Choose one site. The portal takes the site lock for you.

### When the portal refuses a choice

The portal refuses a choice that it cannot use. For example, it refuses a
multi-site choice with no site, or a site that the organization does not hold.
If the refusal comes from a picker page, the portal opens the correct picker
page again. The page shows one sentence that starts with `Caution:`, and the
sentence tells you what to choose. The portal keeps your earlier choices. Make
the choice again, and then continue.

| Refusal | The page that opens |
| --- | --- |
| No organization, or an organization outside this sign-in | `/select/org` |
| No upgrade mode | `/select/mode` |
| A site choice outside multi-site mode | `/select/mode` |
| No site, or a site that the organization does not hold | `/select/site` |

A script that sends `X-Requested-With` or `Accept: application/json` still
gets the JSON refusal with the same status. Issue #3240 records the change.

## Device types

The portal works with three device types.

| Type | Value in the portal | Note |
| --- | --- | --- |
| Access point | `ap` | The cloud restarts an access point on its own after the upgrade. |
| Switch | `switch` | |
| Gateway | `gateway` | A site with two gateway families gets one result for each family. |

## Take the pre-check capture

The pre-check capture is the first record. The portal refuses to start an
upgrade until a verified pre-check capture exists.

To take the capture, choose the data tier and start the capture. The portal
shows `The portal queued the capture.` and then `The portal is reading the
site.`

A capture moves through four states.

| State | Meaning |
| --- | --- |
| `pending` | The portal queued the capture. |
| `collecting` | The portal is reading the site. |
| `verified` | The portal wrote the record and read the record back. |
| `failed` | The capture stopped. Read the portal log for the cause. |

Only a `verified` capture can start an upgrade, and only a `verified` capture
can enter a comparison. A capture that is not verified gives this message:
`The portal did not read this capture back, so it may not be compared.`

### The two data tiers

| Tier | Sections that the portal reads |
| --- | --- |
| 2 | `devices`, `clients_wired`, `clients_wireless`, `clients_guest` |
| 3 | The four tier 2 sections, and `extras` and `alarms` |

Tier 3 adds the port state, the Power over Ethernet state, the radio state, the
tunnels, the peers, and the alarms. Tier 3 makes more cloud calls and takes
more time. Choose tier 3 when you must prove that a port or a tunnel returned.

A tier value that is not 2 and not 3 gives this message: `Choose the data tier
2 or the data tier 3.`

## Choose the upgrade options

The options page lists every device of the site with its firmware version. It
also provides separate access point, switch, and gateway target controls. Each
control selects the highest numeric version returned for every eligible device
of that type. You can still change an individual device target.

Set `CAPTURE_DEFAULT_AP_VERSION`, `CAPTURE_DEFAULT_SWITCH_VERSION`, or
`CAPTURE_DEFAULT_GATEWAY_VERSION` to prefer an approved target for one type.
The portal uses the value only when it exactly matches a version returned for
every eligible device of that type. A blank, malformed, unavailable, or
incompatible setting falls back to the safe highest compatible version. A type
with no common version remains unselected and the page explains why.

The page also offers three controls.

| Control | Default | Meaning |
| --- | --- | --- |
| `reboot` | on | The device restarts after the firmware write. |
| `junos_file_action` | on | The cloud completes the Junos file action after the device reboots. Clear this option to skip the action. |
| `strategy` | `big_bang` | The order in which the cloud sends the upgrade. The four values are `big_bang`, `canary`, `rrm`, and `serial`. |

The page shows a warning in two cases:

- `The site holds two gateway families. The portal reports the result of each family on its own.`
- `One device already runs the version that you chose. The portal still sends the upgrade.`
- `No common compatible version exists for the <device type> devices.`

Saving options re-reads current inventory and available versions. It rejects an
unknown or unavailable target without changing the saved plan. Saving never
starts an upgrade; only the later `CONFIRM` action can start one.

Select all supported device types, one device type, or more than one device
type. The selected types limit the target rows and the saved upgrade plan. The
pre-check capture still records every device.

The page marks a known running firmware version when it differs from the safe
target. A compatible configured type target has priority. Otherwise, the portal
uses the highest compatible version for the device model. An unknown running
version has no mismatch mark.

## Confirm and start the upgrade

The confirmation page asks you to type one word. Type `CONFIRM` in capital
letters. The portal compares the text exactly.

**Warning:** the start control writes firmware to a production device and can
cause an outage. A device that restarts drops every client on that device.

The portal refuses the start in three cases.

| Cause | Message |
| --- | --- |
| The word is wrong | `The start control needs the exact text CONFIRM.` |
| No verified pre-check capture | `Save a verified pre-check capture before you start the upgrade.` |
| Another operator holds the site | `Another operator holds this site. Ask that operator before you try again.` |

### One click starts one multi-site upgrade

Each multi-site form sends one request for one click. Issue #3242 records the
defect that this rule repairs. The rule applies to the forms for the options,
the start, the reschedule, the cancel, the retry, and the reconciliation.

1. When you click the form button, the page disables the form until the portal
   answers. A second click sends nothing.
2. If the portal starts the upgrade, the page opens the progress page.
3. If the request started an upgrade before, the portal refuses with the code
   `org_upgrade_already_submitted` and the HTTP status 409. The message is
   `This confirmed request already started a multi-site upgrade.` The page
   keeps the form disabled, clears the typed word, and puts the focus on a link
   to the progress page of that upgrade.
4. If the portal refuses for a cause that started nothing, the page enables the
   form again. The typed word stays, so you can try again. The code
   `lock_store_unreachable` is one example of such a cause.

A second browser tab of the same operator gets the same refusal and the same
link. The refusal protects the site from a second firmware start.

If the browser shows a page again from its cache, the page loads again from
the portal. A form therefore never stays disabled after you go back and forward
in the browser.

A normal start costs the server no extra work. A refusal reads the stored
upgrade one time to find the link. In the browser test, each journey takes 0.75
to 4 seconds.

## Read the progress page

The run page shows the state of every device. The browser asks the portal for
the state every 30 seconds. The portal sends no push message, so the page can
be up to 30 seconds behind the site.

The portal upgrades the site in four phases, in this order:

1. Gateways
2. Switches
3. Access points
4. Wireless clients

The portal starts a phase only after the phase before it is complete.

### How the portal decides that a device returned

The portal watches three signals for each device:

- A reconnect event from the cloud.
- A decrease of the device uptime, which proves a restart.
- A change of the firmware version.

After the three signals, the portal waits 60 more seconds. An access point
waits 60 seconds more again, so an access point waits 120 seconds in total.
The portal polls the cloud every 20 seconds and gives one device at most one
hour.

The portal marks each device with one of three version outcomes:
`version_match`, `version_mismatch`, or `version_pending`. A `version_mismatch`
device returned on a version that nobody requested. Read that device by hand.

## The post-check capture

The portal takes the post-check capture without a command from you. The
post-check capture uses the same data tier as the pre-check capture.

The portal takes the post-check capture in every end case. A run that finishes
gets a post-check capture. A run that you stop also gets a post-check capture.
The portal takes the capture before it writes the final state of the run.

### The post-check captures of a multi-site upgrade

A multi-site upgrade takes one post-check capture of each site. The portal
takes the captures after the last phase ends, and also after you cancel the
operation. The portal reads one site at a time, in the order of your site
selection. Each capture uses the data tier of the pre-check capture of that
site.

The progress page shows the card "Post-check captures", with one row for each
site. The page repaints each row on each status poll, and the page does not
reload.

| Label | Meaning |
| --- | --- |
| Waiting | The portal takes this capture after the last phase ends. |
| Running | The portal reads the site now. |
| Verified | The portal read the capture back, and the record matches. |
| Failed | The capture did not verify. If no phase failed, the watch reason names the first site with a failed capture. |
| Held | The post-check mode is manual, so the portal took no capture. |
| Skipped | The cloud accepted no firmware write for the site. |
| Not taken | The phase watch ended before the portal took this capture. |

A verified row links to the capture and to the comparison. The comparison link
appears only when the operation holds a pre-check capture of that site. The
link opens `/compare` with the two captures of that site.

The operation reads "Finished" or "Stopped" only after the last capture ends.
If one capture fails, the portal continues with the next site.

## Read the comparison

Open the comparison page at `/compare` and choose the two captures. The two
captures must name the same site, and both must be `verified`.

The comparison page has one filter bar with these labels:

| Label | Meaning |
| --- | --- |
| All rows | Every row |
| Unchanged | The value is the same in both captures |
| Changed | The value is different |
| Added | The row is in the post-check capture only |
| Removed | The row is in the pre-check capture only |
| Present | The client is on the site in both captures |
| Moved | The client is on a different device |
| Missing | The client did not return |

The page refuses a bad request with a plain cause:

| Cause | Message |
| --- | --- |
| The capture is not verified | `A comparison reads a verified capture only.` |
| The two captures name two sites | `The two captures name different sites.` |

You can download the comparison. The page offers a CSV file and a JSON file.
Both links reach `/api/comparisons/export`. A format that is not `csv` and not
`json` gives this message: `Ask for the csv format or the json format.`

## The history page

Open the history page at `/history` to read the past captures of a site and the
past runs of a site. The page shows 25 rows at a time, and the largest page is
200 rows.

The run table comes before the capture table. Each run row shows the run
identifier, the site, the state, the device count, the start time, the end
time, and the last-update age.

The server marks a run as stale when these facts are true:

1. The run is not in a final state.
2. The run has a valid `updated_at` time.
3. The last update is at least 86400 seconds old.

The final states are `complete`, `failed`, `stopped`, and `cancelled`.
The browser does not decide that a run is stale. The browser only refreshes the
visible age text once each minute.

If the time is missing, invalid, or in the future, the page shows `unknown`.
The server does not mark that run as stale.

If the run is stale, the row shows the badge `Stale`.
Open the run to see the same last-update age and stale badge.

Each capture row shows the capture identifier, the role, the start time, the
capture state, the operator email address, and the stored size in bytes.

The history is free to read. Any person with a session can read the history of
any site in the organization.

The history page asks for typed text only when you submit a bulk action. The
server checks the site lock before each run write.

### Bulk preview

Use bulk preview before you cancel or retry selected runs. The server owns the
preview. The server removes runs that are not visible in the current history
scope.

The preview gives the exact run count, site count, site counts, and
confirmation phrase. The browser replaces the selection with the visible run
list from the server.

If you select no run, the bulk buttons stay disabled. If you select one or more
runs, the page enables these controls:

- `Cancel selected`
- `Retry selected`
- `Clear selection`

Press `Cancel selected` to ask for a cancel preview.
Press `Retry selected` to ask for a retry preview.
Read the preview dialog before you continue.
Type the confirmation phrase exactly as the dialog shows it.

For cancel, the phrase has this form:

```text
CANCEL <run-count> RUNS
```

For retry, the phrase has this form:

```text
RETRY <run-count> RUNS
```

Type the capital letters exactly. A lowercase letter causes a refusal.

The preview uses `/api/runs/bulk-actions/preview`.
The action uses `/api/runs/bulk-actions`.
If the response is lost, use `Read stored result` to read
`/api/run-actions/by-request-key`.

### Bulk cancel

Use bulk cancel only for selected pre-cloud runs. A pre-cloud run has not sent
firmware work to Mist.

Before each cancel, the server checks the site lock and the write permission
again. If one site fails that check, the server stops later writes for that
site. Other sites continue.

Bulk cancel sends no cloud request. A successful cancel changes the run state
to `cancelled`.

### Bulk retry

Use bulk retry for selected runs that are `failed`, `stopped`, or `cancelled`.

A retry creates a new run. The new run starts at `created` and links to the
source run. Open `Start fresh pre-check` from the result. Then run a new
pre-check before you confirm firmware work.

For one site, the newest selected source wins. The server uses `updated_at` and
then `run_id` to select that source.

The server copies only approved targets and options from the source run. It
does not copy old pre-checks, confirmations, task identifiers, or invalid
absolute schedules.

### Bulk result

The result shows these counts:

- Succeeded
- Refused
- Failed
- Unknown

Each run also shows its reason and message. A result link opens the changed run
or the new run. A retry result can show `Start fresh pre-check`.

The portal stores each action result in the durable action store. The portal
does not report success until the store verifies the transaction.

### Action recovery

Use `Read stored result` when the browser loses the first action response. The
server reads the stored result with the same request key.

If the first request still has a live worker lease, the server returns the
stored processing action. It does not repeat a write.

If the worker lease expired, one new worker can take the action. That worker
processes only pending items. It does not repeat a claimed or final item.

If a claimed item has no final outcome, recovery finalizes it as `unknown` with
the reason `processing_interrupted`.

If one site loses its guard, recovery finalizes later items for that site as
`unknown` with the reason `not_processed_after_site_guard_loss`.

## The site lock

One site takes one operator. The site lock stops two operators from upgrading
one site at the same time. Redis holds the lock.

| Value | Seconds | Meaning |
| --- | --- | --- |
| Lock life | 300 | The lock expires this long after the last heartbeat. |
| Heartbeat | 60 | The browser and the run driver renew the lock this often. |
| Quiet period | 300 | Another operator may take a quiet site after this long. |

The heartbeat is 60 seconds and the lock life is 300 seconds, so a lock
survives four missed heartbeats. A closed browser does not drop a live upgrade,
because the run driver sends its own heartbeat from the run thread.

### The same operator in two browser tabs

The lock owner is the pair of your work email address and your `browser_id`
cookie. Two tabs of one browser send the same cookie, so both tabs hold the
same owner. You can therefore work on one site in two tabs, and you can hold
several sites at one time.

A different browser sends a different cookie. The same person in a second
browser is a second owner, and the second browser sees a locked site.

### What a second operator sees

A second operator who opens the site sees the state `locked` with the name of
the holder. Every write refuses with this message: `Another operator holds this
site. Ask that operator before you try again.` The capture route gives a
different sentence for the same cause: `Another operator holds this site. Wait
for that run to end.`

The refusal carries the code `site_locked` and the HTTP status 409. The answer
asks the browser to try again after 30 seconds.

Only one operator can own one site at one time. This rule also applies to bulk
cancel, bulk retry, and reconciliation. If another operator holds the site, the
action refuses before it writes the run.

### Take a site from a quiet operator

A holder is quiet when no heartbeat arrives for 300 seconds. A second operator
can then take the site. The portal asks that operator to type `CONFIRM`.

**Caution:** a takeover moves the lock only, so the upgrade of the other
operator can continue. The device work does not stop.

If you return to your own quiet session, the portal asks for a lighter word.
Type `continue` in small letters.

If the portal cannot reach Redis, it cannot grant a lock. The site shows the
state `unknown`, and the lock request answers with the code
`lock_store_unreachable` and the HTTP status 503.

## Stop a run

The stop control is on the run page. Type `STOP` in capital letters. A wrong
word gives this message: `The stop control needs the exact text STOP.`

**Warning:** an interrupted firmware write can leave a device unable to start.
The portal therefore never interrupts a device that writes firmware. A stop
cannot save a device that already started its write.

The portal sorts every device of the run into four groups:

| Group | Meaning |
| --- | --- |
| `cancelled` | The portal withdrew the upgrade before the device started. |
| `already_writing` | The device is writing firmware. The portal did not touch it. |
| `no_cancel_available` | The cloud offers no cancel for this device. |
| `status_unknown` | The portal could not read the state of the device. |

A device counts as stopped only when it is in the `cancelled` group and in
neither of the two protected groups.

After a stop, the portal takes the post-check capture. Read the comparison to
learn which devices changed before the stop.

### Cancel a multi-site upgrade

The progress page of a multi-site upgrade holds the cancel form. Type `CANCEL`
in capital letters to cancel each child job that waits to start.

A multi-site upgrade in a final state cannot change. The final states are
`cancelled`, `completed`, and `failed`. The states `planned`, `running`,
`partial`, and `attention_required` keep the cancel form.

For a final upgrade, the page shows no cancel form. The page shows this note
instead: `The operation is final: <state>. The portal sends no cancel request
for it.` If a status poll reports a final state, the page hides the form and
disables its controls. Issue #3225 records the defect that this rule repairs.

If a cancel request reaches the portal for a final upgrade, the portal refuses
with the code `org_upgrade_not_cancellable` and the HTTP status 409. The
message is `The operation is final: <state>. The portal sent no cancel
request.` The portal sends no request to Mist. The single-site stop page obeys
the same rule for a final run.

An organization job of an earlier release has no stored record. For that job,
the portal reads the state that the last page view or the last poll stored.

The Cancellation column of the site table shows one text for each child job.
The text holds the cancel status, the cloud message, and three device lists:
`Cancelled`, `Writing firmware`, and `No cancel available`. The first render
and each poll show the same text.

## Reconcile a stale run

Open a stale run to find the reconciliation control. The control appears only
when the server decides that the run is stale and reconcilable.

The reconciliation control uses `/api/runs/<run_id>/reconcile`.

Type the phrase that the run page shows. The phrase has this form:

```text
RECONCILE <run_id>
```

Type the run identifier exactly. A changed letter causes a refusal.

Use reconciliation for a stale pre-cloud run or a stale `stopping` run. A
stale pre-cloud run can become `cancelled`.

Use reconciliation for a `stopping` run only when the evidence is complete.
The server reads stored target evidence and cloud evidence. It sends no
firmware, stop, or cancel request to Mist.

The server changes a `stopping` run only to `stopped`. It does that only when
the evidence proves these facts:

1. No target writes firmware.
2. No cloud task is active.
3. No target evidence conflicts.
4. The target evidence is complete.

If evidence is incomplete, unavailable, or in conflict, the run stays
`stopping`. The result shows an `unknown` outcome with the cause.

If a target still writes firmware, the run stays `stopping`. If a cloud task is
active, the run stays `stopping`.

## Where the data goes

ArangoDB is the primary store. The portal writes captures to the collection
`upgrade_captures`, runs to the collection `upgrade_runs`, and the link between
them to the edge collection `capture_for_run`.

ArangoDB is also the durable action store for run controls. It stores the bulk
preview source, reconciliation source, item claims, outcomes, and counts.

The portal keeps each action record for the lifetime of its run record. It has
no automatic cleanup for action records in this release.

The portal verifies every write. It reads the key back and compares the schema
version and the digest. A verified record reports: `The database holds this
record. The portal read the key back and matched the digest.`

If the database write fails, the portal writes a CSV backup file under `data/`.
A capture backup uses the name `upgrade_capture_<key>.csv`, and a run backup
uses the name `upgrade_run_<key>.csv`. Each backup row holds the scalar fields
as columns and the whole record as JSON in a `document_json` column. A record
that lives in a backup file reports: `The backup file under data/ holds this
record.`

Every capture carries a schema version. A capture that a later portal wrote
gives this message: `This record comes from a later version of the portal. This
portal is too old to show it. Upgrade the portal.`

The portal keeps every capture forever. No code path in the portal deletes a
capture and no index expires a capture. Each record reports its size in the
field `stored_size_bytes`, so you can measure the growth. Delete an old capture
by hand when you need the space.

## Troubleshooting

### The portal will not start on Windows

Gunicorn cannot run on Windows. Gunicorn imports the module `fcntl`, and
Windows ships no such module. The portal therefore names Waitress as the server
on Windows, and Gunicorn as the server on every other platform.

Waitress is a core dependency with a platform marker. A Windows install gets
Waitress, and a Linux install does not. If a start on Windows reports a missing
`fcntl` module, the process tried to use Gunicorn. Run `uv sync` on the Windows
host to install Waitress.

### Port 8056 is busy

The portal cannot start when port 8056 is busy. A portal that you stopped can
hold the port for a short time. Run this command to find the listener:

```powershell
Get-NetTCPConnection -LocalPort 8056
```

Stop the process that owns the port, or start the portal on a different port
with `CAPTURE_PORT`.

### The portal says `site_locked`

Another operator holds the site. The refusal names the holder. Do one of these
three things:

- Ask that operator to finish the run.
- Wait 300 seconds after the holder becomes quiet, then take the site with the
  word `CONFIRM`.
- Choose a different site.

A `site_locked` refusal for your own site in a second browser is correct
behavior. The second browser has a different `browser_id` cookie, so the portal
counts it as a second operator. Return to the first browser.

### The page shows the lock state `unknown`

The portal cannot reach Redis. Open `/readyz`. If that route reports
`"redis": "unreachable"`, check `REDIS_HOST` and `REDIS_PORT`. Remember that
the default host name `redis-stack` works inside a container network only.

### A capture stays at `collecting`

The portal is still reading the site. A large site with tier 3 takes longer
than a small site with tier 2. If the state changes to `failed`, read the
portal log. The failure message is: `The capture stopped. Read the portal log
for the cause.`

### A device never returns

The portal gives one device at most one hour. The portal marks a device that
does not return inside that hour as failed for that phase. Read that device in
the Mist cloud by hand.

### A bulk preview refuses the selection

If the page says `Select between 1 and 50 runs.`, change the selection count.
One bulk request can hold 1 through 50 run identifiers.

If the page says `A run identifier occurs more than once.`, clear the
selection and select the rows again. The server refuses duplicate identifiers.

If the page says `No selected run is visible in this history scope.`, refresh
the history page. The server removed each hidden or out-of-scope run.

### A bulk action refuses after preview

If the page says `The typed confirmation does not match.`, type the phrase
again with the same capital letters.

If the page says `The action preview expired.`, request a new preview.

If the page says `The action request does not match its preview.`, request a
new preview. The selection or scope changed after the preview.

If the page says `The durable action store is unavailable.`, stop. The portal
cannot safely write the run result.

### A site guard refuses a run control

If the result says `site_write_forbidden`, ask an administrator to check your
site permission.

If the result says `site_lock_not_owned`, take the site lock before you try
again.

If the result says `site_lock_token_changed`, refresh the site page before you
try again. Another session changed the site lock.

### A cancel or retry refuses one run

If a cancel result says `run_not_precloud`, the run already reached cloud work.
Use the single-run stop control instead.

If a retry result says `run_not_retryable`, select a run that is `failed`,
`stopped`, or `cancelled`.

If a retry result says `retry_source_time_unknown`, use another source run.
The source run has no valid update time.

If a retry result says `retry_options_unsupported` or `retry_options_invalid`,
create a new upgrade plan by hand. The source options are not safe to copy.

If a retry result says `upgrade_already_running`, finish the live run for that
site first.

### A reconciliation refuses one run

If a result says `run_not_stale`, wait until the run is stale or refresh the
page.

If a result says `run_not_reconcilable`, use reconciliation only for a
pre-cloud run or a `stopping` run.

If a result says `firmware_write_active` or `cloud_task_active`, wait for the
firmware work to finish.

If a result says `cloud_evidence_incomplete`,
`cloud_evidence_unavailable`, or `cloud_evidence_conflict`, read the run in
Mist before you try again.

## Current limits

These limits are the behavior of the code today.

**The menu starts the development server.** menu 239 and the `--capture-portal`
flag start the Flask development server. Neither path starts Waitress, and
neither path starts Gunicorn. The container path prints this advice and then
starts the same development server:
`>> For production, use: gunicorn wsgi_capture:app -w 1 -k gthread --threads 4`
Use the file `wsgi_capture.py` with Gunicorn for a production service.

**A run can hold at `upgrade_submitting`.** The portal sends the upgrade
through a run driver. If the run driver is not connected, the portal writes
this line to the log: `The portal cannot send an upgrade yet, because the run
driver is not wired.` The run then holds at the state `upgrade_submitting`, and
no device receives an upgrade. Check the log when a run does not advance.

**A stop does not always reach the cloud.** The stop control shows `The portal
recorded the stop and starts no further device.` If the stop driver is not
connected, the portal keeps the stop request and cancels no device at the
cloud. Read the cloud to confirm the result.

**Run rows can disappear at a restart.** Without a database run store, the
portal holds the run rows in memory. Those rows do not survive a restart of the
portal. A capture is safe, because a capture goes to the database or to a CSV
backup file.

## Two defects outside this portal

The repository holds two known defects. Both defects sit outside the portal
code. This feature repairs neither defect. Read this section to learn why the
portal behaves as it does.

### The write path reports success after zero rows

`_is_standalone_mode()` at `src/export/data_exporter.py:141` returns `True` when
the process does not run inside a container. The export path then skips the
polyglot database. `_csv_fallback` at `src/db/router.py:372-382` returns
`success=True` with `records_written=0`. A caller therefore reads a success
after a write of zero rows. Issue #1824 tracks this defect.

The portal does not trust that report. The portal reads every key back and
compares the schema version and the digest. A capture reaches the state
`verified` only after that test succeeds.

### The retention purge never runs

`src/db/retention.py:100` reads the attribute `_database` from the ArangoDB
writer. `src/db/arango_writer.py:3903` names that handle `self._db`. The read
therefore answers `None`, the usage measure answers `0.0`, and the purge never
starts.

The portal needs unlimited retention, so this defect causes the portal no harm
today. The portal keeps every capture on purpose.

**Warning:** a repair of this defect can cause the permanent loss of stored
captures. A delete is irreversible. Measure the growth with the
`stored_size_bytes` field before you ask for a repair.
