# Quickstart: Offline Device Report (Menu 158)

## Usage

### Interactive Mode

```bash
python MistHelper.py
# Select option 158 from the menu
# Enter offline threshold in hours (default: 48) or press Enter for default
```

### Direct Invocation

```bash
python MistHelper.py --menu 158
```

### Automated Test Mode

```bash
python MistHelper.py --test
# Menu 158 runs automatically with 48-hour default (classified as safe)
```

## Output

### Screen Display

1. **Summary block**: Total devices, offline count, per-type breakdown (APs/Switches/Gateways), top 5 affected sites
2. **Detail table**: PrettyTable showing first 50 devices sorted by offline duration (longest first)
3. **CSV confirmation**: Path to saved CSV file

### CSV File

- **Location**: `data/OfflineDeviceReport_YYYYMMDD_HHMMSS.csv`
- **Columns**: Device Name, Device Type, Site Name, MAC Address, Serial Number, Model, Last Seen, Offline Duration, Status
- **Encoding**: UTF-8 with BOM for Excel compatibility
- **Sorting**: By offline duration (longest first)

## Example Output

```text
=== Offline Device Report ===
Threshold: 48 hours

--- Summary ---
Total devices in org: 2,450
Devices offline > 48 hours: 23

By Type:
  APs: 15
  Switches: 6
  Gateways: 2

Top 5 Sites:
  1. NYC-Office: 8 offline
  2. LAX-Branch: 5 offline
  3. CHI-DC: 4 offline
  4. SEA-Office: 3 offline
  5. ATL-Branch: 3 offline

--- Offline Devices (showing 23 of 23) ---
+------------------+--------+-----------+-------------------+-------+---------+---------------------+-------------------+--------------+
| Device Name      | Type   | Site      | MAC Address       | Serial| Model   | Last Seen           | Offline Duration  | Status       |
+------------------+--------+-----------+-------------------+-------+---------+---------------------+-------------------+--------------+
| (unnamed)        | AP     | NYC-Office| aa:bb:cc:dd:ee:01 | ABC123| AP45    | Never Connected     | Never Connected   | disconnected |
| ap-lobby-nyc     | AP     | NYC-Office| aa:bb:cc:dd:ee:02 | ABC124| AP45    | 2026-03-10 08:30:00 | 18 days 4 hours   | disconnected |
| sw-floor3-lax    | Switch | LAX-Branch| 11:22:33:44:55:01 | DEF456| EX4100  | 2026-03-25 14:00:00 | 2 days 22 hours   | disconnected |
+------------------+--------+-----------+-------------------+-------+---------+---------------------+-------------------+--------------+

CSV saved: data/OfflineDeviceReport_20260328_120000.csv (23 devices)
```
