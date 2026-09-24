# Quickstart: Menu 270 mode 4, the closed Marvis Actions report

**Feature**: `3342-marvis-closed-report` | **Issue**: #3342

Mode 4 writes a report of the closed Marvis Actions of your organization. It
changes nothing in Mist.

## Before you start

1. Set `MIST_APITOKEN` and `org_id` in `.env`.
2. Make sure that the token can read the organization.

## Command line

### Export every closed action

```powershell
python MistHelper.py --menu 270
```

Answer the prompts as follows.

| Prompt | Answer |
| - | - |
| `Enter the mode number (1, 2, 3, or 4) [1]:` | `4` |
| `Enter the categories to include ... [all]:` | Press Enter. |
| `Enter the subcategories to include ... [all]:` | Press Enter. |

The run writes `data/OrgMarvisActions.csv`. Each row holds `is_open` False.

### Export the closed actions of one topic

Answer `4`, then `switch`, then `sw_offline`. The tables show only the topics
that hold a closed action. The Closed column shows the count for each row.

### Write the report to SQLite

```powershell
python MistHelper.py --menu 270 --output-format sqlite
```

The run writes the table `OrgMarvisActions` in `data/mist_data.db`, and it writes
no CSV file. The table keeps the rows of earlier runs, so filter it on `is_open`.

```sql
SELECT status_name, COUNT(*) FROM OrgMarvisActions WHERE is_open = 0 GROUP BY status_name;
```

## Operations portal

1. Open `http://<host>:8055/operations`.
2. Expand the Marvis Actions group, and select menu 270.
3. In the Mode list, select `4 - Export the closed Marvis Actions (report only)`.
4. Select a category and a subcategory, or keep "All".
5. Click Run. The portal offers `OrgMarvisActions.csv` when the run ends.

## SSH

1. Connect with `ssh -p 2200 misthelper@<host>`.
2. Type `270` at the main menu.
3. Answer the prompts as in the command line section.

## Read how each action closed

| Column | Meaning |
| - | - |
| `status_name` | The closed status, such as AI Validated or Resolved By User. |
| `label_name` | The resolution code of an action that an operator resolved. |
| `comment` | The comment of the last resolve. |
| `resolve_time_iso` | When the action closed. |
| `validation_time_iso` | When Marvis checked the fix. |

If a row shows a status key instead of a name, MistHelper does not know that key.
The run logs a caution line for each unknown key. Compare those actions with the
Mist UI.
