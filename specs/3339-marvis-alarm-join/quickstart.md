# Quickstart: Read the Marvis alarm of each Marvis Action

**Feature**: `3339-marvis-alarm-join` | **Issue**: #3339, phase 1

Modes 1, 2, and 4 of menu 270 add the Marvis alarm of each action to the export.
The join reads only. It changes nothing in Mist.

## Before you start

1. Set `MIST_APITOKEN` and `org_id` in `.env`.
2. Make sure that the token can read the organization alarms.

## Command line

### Export every action with its alarm

```powershell
python MistHelper.py --menu 270
```

Answer the prompts as follows.

| Prompt | Answer |
| - | - |
| `Enter the mode number (1, 2, 3, or 4) [1]:` | Press Enter. |
| `Enter the categories to include ... [all]:` | Press Enter. |
| `Enter the subcategories to include ... [all]:` | Press Enter. |

The run writes `data/OrgMarvisActions.csv`. The last eight columns hold the
alarm values. Before the write, the run shows two count lines.

```text
Marvis alarm join: 31 of 112 exported actions have a Marvis alarm. 81 have no alarm.
Marvis alarms in the search window without an action in the list: 2
```

The counts above come from the lab organization on 2026-09-24. Your counts can
differ.

### Write the report to SQLite

```powershell
python MistHelper.py --menu 270 --output-format sqlite
```

The run writes the table `OrgMarvisActions` in `data/mist_data.db`. The writer
adds the eight alarm columns to an older table.

```sql
SELECT alarm_type, alarm_status, COUNT(*) FROM OrgMarvisActions WHERE alarm_id != '' GROUP BY alarm_type, alarm_status;
```

### Read the report in ArangoDB

A portal run also writes the collection `listOrgMarvisActions`.

```aql
FOR d IN listOrgMarvisActions FILTER d.alarm_id != "" COLLECT alarm_type = d.alarm_type, alarm_status = d.alarm_status WITH COUNT INTO total RETURN {alarm_type, alarm_status, total}
```

Caution: an SSH session writes only the CSV file, so the ArangoDB collection can
keep the rows of an earlier run. Issue #3313 records this defect. Run the export
from the portal to update the collection.

## Operations portal

1. Open `http://<host>:8055/operations`.
2. Expand the Marvis Actions group, and select menu 270.
3. Select mode 1, 2, or 4.
4. Select a category and a subcategory, or keep "All".
5. Click Run. The log viewer shows the two count lines. The portal offers
   `OrgMarvisActions.csv` when the run ends.

## SSH

1. Connect with `ssh -p 2200 misthelper@<host>`.
2. Type `270` at the main menu.
3. Answer the prompts as in the command line section.

## Read the alarm columns

| Column | Meaning |
| - | - |
| `alarm_id` | The alarm identifier. On the lab organization, it equals the action `uuid`. |
| `alarm_type` | The alarm type, such as `switch_offline`. It differs from the action topic name. |
| `alarm_status` | `open` or `resolved`. Mist sets this status. |
| `alarm_resolved_time_iso` | When Mist resolved the alarm. |
| `alarm_acked` | True when an operator acknowledged the alarm. Empty when Mist sent no value. |
| `alarm_acked_time_iso` | When the operator acknowledged the alarm. |
| `alarm_ack_admin_name` | The operator who acknowledged the alarm. |
| `alarm_note` | The note of the alarm. |

If the eight columns of a row are empty, Mist returned no alarm for that action.
Mist keeps an alarm for a shorter time than an action, so an old action often has
no alarm.

If the run shows the line "The Marvis alarm search returned no usable result.",
every alarm column stays empty. The line names the reason, such as the HTTP
status. The export still holds every action.
