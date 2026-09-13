# Command Line Reference

MistHelper runs in two ways. With no `-M` flag it opens the interactive menu.
With `-M` it runs one operation and exits, which suits a scheduled job.

## Flags

| Flag | Purpose |
|------|---------|
| `-O, --org` | Organization ID |
| `-M, --menu <id>` | Execute a single menu action non-interactively |
| `-S, --site` | Human-readable site name |
| `-D, --device` | Human-readable device name |
| `-P, --port` | Port ID |
| `--output-format {csv,sqlite}` | Select output backend (default csv) |
| `--test` | Run systematic safe-operation test suite |
| `--fast` | Enable fast mode heuristics (threading and reduced retries) |
| `--skip-deps` | Skip dependency auto-install and upgrade phase |
| `--debug` | Enable debug output (includes detailed table data in logs) |
| `--delay <seconds>` | Fixed delay between loop iterations (in seconds) |
| `--address-check` | Enable external address validation using Nominatim API |
| `--skip-ssl-verify` | Skip SSL certificate verification for external API calls |
| `--no-env` | Disable .env file loading for SSH operations |
| `--dry-run` | Preview destructive operations without making changes |
| `--tui` | Launch Terminal User Interface mode for visual API navigation |
| `--login` | Use interactive login (email and password) instead of API token. This enables MSP-level API access. |
| `--web-portal` | Launch the web portal interface on port 8055 (or WEB_PORT env var) |
| `--capture-portal` | Launch the upgrade capture portal on port 8056 (or CAPTURE_PORT env var). Same as menu 239. |
| `--metrics-gateway` | Serve Mist Cloud health to a monitoring system on port 8057 (or METRICS_PORT env var). Same as menu 241. |
| `--metrics-snmp` | Answer Net-SNMP `pass_persist` requests on standard input. Start this from `snmpd.conf`, not by hand. |
| `--testinteractive` | Run systematic test of read-only interactive menu options |

Warning: `--skip-ssl-verify` turns off certificate checking. An attacker on the
network path can then read your Mist API token. Use the flag on a laboratory
network alone, and never with a production token.

## Examples

```powershell
python .\MistHelper.py -M 11 --output-format sqlite
python .\MistHelper.py -M 13 --output-format sqlite --fast
python .\MistHelper.py --test --output-format sqlite --debug
python .\MistHelper.py -M 11 --debug
python .\MistHelper.py -M 16 --fast
```

## The two test modes

| Mode | What it runs |
|------|--------------|
| `--test` | Every operation that the registry names `safe` |
| `--testinteractive` | The `safe` set, and every operation that the registry names `interactive_safe` |

`src/utils/operation_registry.py` decides. The classifier fails closed, so an
operation that the registry does not name never runs in an automated pass. That
rule keeps every destructive operation out of both modes.

## Output files

MistHelper writes every output under `data/`.

| Output | Place |
|--------|-------|
| CSV files | `data/` |
| SQLite database | `data/mist_data.db` |
| Runtime log | `data/script.log` |
| Per-host SSH logs | `data/per-host-logs/` |
| Packet captures of menu 197 | `data/packet_captures/<mac>/vlan_<id>/` |
| Weekly inventory | `CombinedInventory_ByWeek/` |
