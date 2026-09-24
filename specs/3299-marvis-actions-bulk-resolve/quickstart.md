# Quickstart: Marvis Actions export and bulk resolve

**Feature**: `3299-marvis-actions-bulk-resolve` | **Issue**: #3299

This page shows an engineer how to run menu 270 in each place that MistHelper
serves it. Each example uses the lab organization. Replace the counts with the
counts that your organization shows.

## Before you start

1. Make sure that `.env` holds `MIST_APITOKEN`, `MIST_HOST`, and `org_id`.
2. Make sure that the token has an organization role that can write Marvis
   Actions (admin, write, or helpdesk). A read-only token can run modes 1 and 2
   only.
3. If you want a smaller or a larger cap for one resolve run, set
   `MARVIS_RESOLVE_MAX_ACTIONS` in `.env`. The default is 500.

## Command line

### Export every action (mode 1)

```powershell
.venv\Scripts\Activate.ps1
python MistHelper.py --menu 270
```

Press Enter at the mode prompt, at the category prompt, and at the subcategory
prompt. The console shows the category table and the subcategory table. The
last line is:

```text
Completed the Marvis Actions export and wrote results to OrgMarvisActions.csv
```

Open `data/OrgMarvisActions.csv`. It holds one row for each action.

### Export one topic

At the category prompt, enter `switch` or the number of the Wired row. At the
subcategory prompt, enter `sw_offline`, `switch/sw_offline`, or the number of the
Switch Offline row. You can enter a list, such as `ap,switch`.

### Export the open actions (mode 2)

Enter `2` at the mode prompt. The tables list only the topics that hold an open
action. An open action has the status Open, In Progress, or Reoccurred.

### Resolve the open actions of one topic (mode 3)

1. Enter `3` at the mode prompt.
2. Select the category and the subcategory.
3. Read the preview. It lists each target action with its site and its device.
4. Select the resolution code. Press Enter for code 1, `suggested`.
5. Enter a comment. Code 2, `nonsuggested`, needs a comment. Other codes accept an
   empty comment.
6. Type the confirmation exactly as the prompt shows it, such as `RESOLVE 12`.

Caution: Mist records the resolution code and the comment on each action. If you
resolve the wrong action, set its status back to Open in the Mist UI.

The operation writes `data/OrgMarvisActionsResolveResults.csv`. Each row shows the
outcome, the HTTP status, and the status that Mist reported after the run.

## Operations portal

1. Open `http://localhost:8055` and sign in.
2. Find "Marvis Actions" in the operation list, and select menu 270.
3. Select the mode, the category, and the subcategory.
4. For mode 3, first run mode 2 with the same filter. Read the open count in the
   log. Then select mode 3, select the code, enter the comment, and type
   `RESOLVE <count>` in the confirmation control.
5. Click Run. The log panel shows the tables and the result. The Results panel
   shows the CSV file.

If the confirmation count does not match the current target count, the run fails
and changes nothing.

## SSH

```powershell
ssh -p 2200 misthelper@localhost
```

Enter `270` at the main menu, then answer the prompts as on the command line.
The SSH session writes to the same `data/` directory as the portal.

## Undo a resolve

The Mist UI shows a status dropdown for an action that a user resolved. Select
Open or In Progress. The endpoint report
`documentation/marvis-actions-api-endpoints.md` shows the API body for the same
change.
