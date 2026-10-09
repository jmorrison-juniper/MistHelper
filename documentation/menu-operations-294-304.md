# Menu operations 294 to 304

This page explains the eleven Juniper RMA operations. The operations read the
Juniper service APIs. They cover service requests, RMAs, reference data,
software releases, and warranty data. Each operation writes local exports under
`data/`. No operation sends a change to Juniper.

The Operations portal lists the operations under the group "Juniper RMA". Read
[the menu reference](menu_reference.md) for the full table of every menu.

Warning: The exports contain personal data. Each export keeps contact names,
e-mail addresses, telephone numbers, and street lines in full. Store the `data/`
folder on an approved system. Remove the files when you no longer need them.

## Set up the access

Juniper issues the application ID, the customer source ID, the client ID, and
the client secret during onboarding. Add these values to your local `.env` file.
The file `deploy/.env.example` lists every value with a placeholder.

Warning: The client secret grants access to your Juniper service requests. Do
not paste it into a ticket, a chat, a log, or a commit. The `.env` file is
git-ignored.

Every menu needs these values:

- `JUNIPER_APP_ID`
- `JUNIPER_CUSTOMER_SOURCE_ID`
- `JUNIPER_CLIENT_ID`
- `JUNIPER_CLIENT_SECRET`
- `JUNIPER_USER_ID`
- `JUNIPER_ACCOUNT_ID`

Menus 294 to 297, 301, 302, and 303 also need `JUNIPER_CONTACT_EMAIL`. Menus
298 to 300 and 304 do not need it.

Run menu 301 first. It confirms that Juniper accepts the settings.

These optional values have a default. Change a value only when your network or
Juniper requires it.

| Variable | Default | Meaning |
| - | - | - |
| `JUNIPER_TOKEN_URL` | The Juniper production token endpoint | The OAuth 2.0 token address. It must use HTTPS and an allowed host. |
| `JUNIPER_CASE_BASE_URL` | The Juniper production Case API | The base address of the Case API. |
| `JUNIPER_ASSET_BASE_URL` | The Juniper production Asset API | The base address of the Asset API. |
| `JUNIPER_ALLOWED_HOSTS` | `apigw.juniper.net` | The comma-separated hosts that the client may call. |
| `JUNIPER_MAX_REQUESTS_PER_SECOND` | `2`, range 0.5 to 10 | The request rate limit. |
| `JUNIPER_MAX_RETRY_ATTEMPTS` | `3`, range 1 to 5 | The attempts for a temporary failure: HTTP 429, 502, 503, 504, or a connection error. |
| `JUNIPER_CA_BUNDLE` | Empty | The path to a CA bundle. Empty uses the system certificate store. |
| `JUNIPER_PII_RETENTION_DAYS` | `180`, range 1 to 730 | The age in days of an export before a run removes it. |
| `JUNIPER_TICKET_KEY_FIELD` | `case_number` | The Mist ticket field for the match: `case_number` or `id`. |
| `JUNIPER_LIVE_TESTS` | Unset | Set to `1` to allow one live read-only check in an automated test mode. |

The automated test modes `--test` and `--testinteractive` refuse every Juniper
call. A live call runs only when `JUNIPER_LIVE_TESTS` is `1`. Set it for one
check, and remove it when the check ends.

## The menus

Each menu prints every field of every row. It saves a CSV file under `data/`.
When you select the database output, the rows also reach the SQLite database or
the ArangoDB store.

| Menu | What it reads | Prompts | Writes |
| - | - | - | - |
| 294 | Juniper service requests in a date window | Start date and end date. A blank start date uses 90 days ago. A blank end date uses today. | `JuniperRequestList.csv` |
| 295 | One service request with every field | Key type (request number or customer case number), then the identifier. | `JuniperRequestDetail.csv`, `JuniperRequestDetailRecords.csv` |
| 296 | One RMA with its header and its items | RMA number and service request number, both required. Customer case number, optional. | `JuniperRmaDetail.csv`, `JuniperRmaDetailItems.csv` |
| 297 | Notes of one service request | Key type and identifier, then an optional note identifier. | `JuniperRequestNotes.csv` |
| 298 | The Juniper list of values | None | `JuniperLovs.csv` |
| 299 | Juniper software versions by product series and platform | None | `JuniperSoftwareVersions.csv` |
| 300 | Asset bulk snapshot file links for a date window | Start date and end date. A blank start date uses 7 days ago. A blank end date uses yesterday. | `JuniperAssetBulkLinks.csv`, and `JuniperAssetBulkNoData.csv` for each snapshot date with no data |
| 301 | Juniper service API access | None | None. The menu prints the result and the reason. |
| 302 | Mist support tickets and the Juniper requests that match them | The organization. The terminal asks only when no cached organization exists. | `JuniperCorrelation.csv`, `JuniperServiceRequests.csv`, `JuniperRmaItems.csv`, `JuniperRunRecords.csv` |
| 303 | One service request or one RMA | Key type and identifier, then an optional RMA number. | `JuniperLookup.csv`, `JuniperLookupRmaItems.csv` |
| 304 | Warranty, contract, and status data for serial numbers | One line of serial numbers, separated by commas or spaces. Required. | `JuniperAssets.csv`, `JuniperAssetCoverage.csv` |

## Match tickets to RMAs (menu 302)

Menu 302 matches each Mist support ticket to every Juniper service request with
the same customer case number. The ticket field for the match comes from
`JUNIPER_TICKET_KEY_FIELD`. A ticket older than 90 days uses a detail lookup.
Each matched request leads to its RMAs and their items. The menu never reads the
comments of a ticket.

When no ticket matches a Juniper request, the menu logs one warning. The
reason names the likely cause. Mist case numbers may not be visible to the
Juniper account of the application.

## Keep personal data under control

Each export keeps the personal fields in full. The run log masks these fields
in every line. At the start of each run, the menus remove export files that are
older than `JUNIPER_PII_RETENTION_DAYS`.

## Troubleshoot

| Symptom | Likely cause | Action |
| - | - | - |
| The log names missing settings. | A required value is not in `.env`. | Add the named value. The message never prints a value. |
| The menu prints "Juniper live calls are refused in automated test modes." | An automated mode runs without the opt-in. | Set `JUNIPER_LIVE_TESTS=1` for one check, and then remove it. |
| Menu 300 returns HTTP 401. | Juniper has not enabled the asset API for the application. | Ask Juniper to enable the asset API for the application ID. |
| Menu 302 finds no match. | The key field or the case numbers do not agree. | Check `JUNIPER_TICKET_KEY_FIELD`. Confirm the case numbers with Juniper. |
| A read reports an HTTP status, a connection error, or a timeout. | The Juniper service did not answer. | Run the menu again later. Check the proxy setting and `JUNIPER_CA_BUNDLE`. |
