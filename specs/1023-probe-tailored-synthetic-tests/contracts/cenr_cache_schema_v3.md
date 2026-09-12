# Contract: CENR Cache Schema v3

**Feature**: 1023-probe-tailored-synthetic-tests
**Files**:
- `data/zscaler_cenr_hostnames.json`
- `data/zscaler_client_connector_probes.json` (same host-entry shape under
  `roles[].fqdns`)
**Kind**: Persistence-layer JSON schema contract

## Version Bump

- `schema_version` is bumped from **2** to **3**.
- Backward-compatible load path for v2 (and versions `< 3`) is required.

## v3 Top-Level Shape (`zscaler_cenr_hostnames.json`)

```jsonc
{
  "schema_version": 3,
  "fetched_utc": "2026-07-26T14:22:03Z",
  "source_urls": ["https://config.zscaler.com/api/zscaler.net/cenr/json", "..."],
  "description": "Merged Zscaler CENR ...",
  "probe_default": {
    "protocol": "https",
    "port": 443,
    "ignore_cert": false,
    "reason": "ZEN edges terminate TLS on 443 ..."
  },
  "proxy_hostnames": [
    {"host": "chi1-2.sme.zscaler.net", "observed_protocol": "HTTPS", "observed_port": 443, "last_probed": "2026-07-26T14:22:03Z"},
    // ... more entries
  ],
  "vpn_hostnames": [
    {"host": "chi1-2-vpn.zscaler.net", "observed_protocol": "UDP", "observed_port": 500, "last_probed": "2026-07-26T14:22:03Z"},
    // ... more entries
  ],
  "by_city": {
    "Chicago II": {
      "proxy_hostnames": [ /* same shape as top-level */ ],
      "vpn_hostnames":   [ /* same shape as top-level */ ],
      "seen_in_clouds":  ["zscaler.net"]
    }
    // ... more cities
  }
}
```

## Per-Host Entry (v3)

```jsonc
{
  "host": "chi1-2-vpn.zscaler.net",         // required, non-empty
  "observed_protocol": "UDP",                // optional; null when no observation
  "observed_port": 500,                      // optional; null when no observation
  "last_probed": "2026-07-26T14:22:03Z"      // optional; ISO8601 UTC
}
```

### `observed_protocol` valid tokens

| Token         | Meaning                                    | Consumed by URL builder as    |
|---------------|--------------------------------------------|-------------------------------|
| `"HTTPS"`     | HTTPS response observed on 443             | `https://<host>`              |
| `"TCP/443"`   | Raw TCP SYN+ACK on 443, no HTTPS parsed    | `https://<host>`              |
| `"TCP/<n>"`   | Raw TCP on other port                      | `<host>:<n>`                  |
| `"UDP"`       | UDP datagram back on the probe port        | `<host>:<observed_port>`      |
| `"UDP/500"`   | UDP datagram back on 500 specifically      | `<host>:500`                  |
| `"UDP/4500"`  | UDP datagram back on 4500 specifically     | `<host>:4500`                 |
| `null`        | No observation cached                      | catalogue fallback + WARN     |

## v3 Top-Level Shape (`zscaler_client_connector_probes.json`)

```jsonc
{
  "schema_version": 3,
  "roles": {
    "zcc_health": {
      "description": "...",
      "critical": true,
      "fqdns": [
        {"host": "gateway.zscaler.net", "observed_protocol": "HTTPS", "observed_port": 443, "last_probed": "2026-07-26T14:22:03Z"}
      ]
    }
  }
}
```

## Backward-Compatibility Adapter (v2 -> v3, load-time only)

### Detection

- Loader inspects top-level `schema_version`. Missing, non-int, or `< 3` ->
  adapter fires.

### Adaptation

For each bag in `{proxy_hostnames, vpn_hostnames, by_city[*].proxy_hostnames,
by_city[*].vpn_hostnames, roles[*].fqdns}`:

```python
def _promote(entry: str | dict) -> dict:
    if isinstance(entry, str):
        return {"host": entry}
    return entry  # already an object
```

### Logging

Exactly one `logger.info` per load:

```
zscaler_catalogue: loaded v%d cache (%d entries); observations absent
```

`%d` args: detected version (or 0 if missing), total hostname count.

## Write Path

- Writer runs from `zscaler_catalogue.ensure_fresh()` immediately after
  `run_full_validation` returns.
- Writer indexes the `list[ProbeResult]` by FQDN.
- For each entry across all four bags, writer sets `observed_protocol`,
  `observed_port`, `last_probed` when the probe result has any responding
  protocol; otherwise leaves them null.
- Priority when a host has multiple responding protocols:
  1. `HTTPS` (if `443` in `tcp` returned `"open"` AND `https_status` was
     set) -> `("HTTPS", 443)`
  2. UDP responses on 500 or 4500 -> `(f"UDP/{port}", port)`; 500 preferred
     over 4500 when both open.
  3. Other TCP `"open"` ports -> `(f"TCP/{port}", port)` (first port in
     `declared_ports` order that returned open).
- Writer uses `_atomic_write_json` (existing helper). No behavioural change
  to the atomic-write mechanic.
- Writer emits `schema_version: 3` unconditionally in the top-level dict.

## Non-Regression Assertions

- A round-trip write-then-load MUST produce a document structurally equal
  to the write input (aside from key ordering).
- A v2 fixture loaded and re-written MUST become a v3 document with
  observation fields all `null`.
- No key OTHER than the four host-bags is modified by the adapter.

## Non-Goals

- No new file locations.
- No embedded sidecar observation store (R-003 alternative rejected).
- Forward compatibility (older MistHelper reading a v3 file) is explicitly
  not required.
