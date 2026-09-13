# Phase 1 Data Model: Probe-Tailored Synthetic Tests

**Feature**: 1023-probe-tailored-synthetic-tests
**Date**: 2026-07-26
**Purpose**: Enumerate every entity touched by this feature, its attributes,
relationships, validation rules, and state transitions where applicable.

## Entity Index

| Entity                | Kind          | Persistence                                        |
|-----------------------|---------------|----------------------------------------------------|
| ProbeResult           | dataclass     | In-memory only (returned by `_probe_fqdn`)         |
| CENRHostEntry (v3)    | JSON object   | `data/zscaler_cenr_hostnames.json`                 |
| ZCCFqdnEntry (v3)     | JSON object   | `data/zscaler_client_connector_probes.json`        |
| SyntheticProbeTarget  | transient str | Emitted into Mist `custom_probes[i].target` field  |

---

## 1. `ProbeResult`

**Location**: `src/utils/zscaler_probe.py`

**Existing dataclass** extended by this feature. The full list below marks
which fields exist today and which are added.

### Attributes

| Field                 | Type                  | Status    | Notes                                                                 |
|-----------------------|-----------------------|-----------|-----------------------------------------------------------------------|
| `fqdn`                | `str`                 | existing  | The hostname probed.                                                  |
| `role`                | `str`                 | existing  | Catalogue role (e.g. `cenr_zen_https`, `zcc_health`).                 |
| `role_description`    | `str`                 | existing  | Human-readable description from catalogue.                            |
| `declared_ports`      | `tuple[int, ...]`     | existing  | Catalogue-declared TCP ports.                                         |
| `critical`            | `bool`                | existing  | Catalogue-declared critical flag.                                     |
| `ip`                  | `str \| None`         | existing  | Resolved A record (first).                                            |
| `dns_error`           | `str \| None`         | existing  | Populated when `_resolve` fails.                                      |
| `icmp_ok`             | `bool \| None`        | existing  | `True`/`False`/`None` when ping is inapplicable.                      |
| `tcp`                 | `dict[int, str]`      | existing  | Port -> `"open"` / `"no_reply"` / `"error:..."` / `"closed"`.         |
| `http_status`         | `int \| None`         | existing  | Status code from HTTP GET on 80/8080.                                 |
| `http_server`         | `str \| None`         | existing  | Server header.                                                        |
| `http_location`       | `str \| None`         | existing  | Location header on redirect.                                          |
| `https_status`        | `int \| None`         | existing  | Status code from HTTPS GET on 443.                                    |
| `https_server`        | `str \| None`         | existing  | Server header over TLS.                                               |
| `https_location`      | `str \| None`         | existing  | Location header over TLS.                                             |
| `tls_subject`         | `str \| None`         | existing  | Peer certificate subject CN/O.                                        |
| `tls_issuer`          | `str \| None`         | existing  | Peer certificate issuer CN/O.                                         |
| `tls_error`           | `str \| None`         | existing  | TLS handshake failure summary.                                        |
| `responding_protocols`| `list[str]`           | existing  | Human-readable tokens (extended below).                               |
| `server_class`        | `str`                 | existing  | Coarse classification tag.                                            |
| `notes`               | `list[str]`           | existing  | Additional diagnostic notes.                                          |
| **`udp`**             | **`dict[int, str]`**  | **NEW**   | **Port -> `"open"` / `"no_reply"` / `"error:<ExcName>"`.**            |

### Validation Rules

- `udp` keys MUST be in `IKE_UDP_PORTS = (500, 4500)`.
- `udp` values MUST be one of `"open"`, `"no_reply"`, or a string beginning
  with `"error:"` followed by a Python exception class name.
- When `udp[500] == "open"`, `"UDP/500"` MUST appear in
  `responding_protocols`. Same for 4500.
- `udp` MAY be empty (no UDP probe fired for this host).

### Relationships

- Referenced by `run_full_validation()` return value (a `list[ProbeResult]`).
- Its serialised outcome flows into `CENRHostEntry.observed_protocol` and
  `observed_port` inside the catalogue write path.

### State Transitions

`ProbeResult` is immutable once returned. Field population order inside
`_probe_fqdn` is: DNS -> ICMP -> TCP -> HTTP/HTTPS -> UDP (conditional).

---

## 2. `CENRHostEntry` (schema v3)

**Location**: `data/zscaler_cenr_hostnames.json`

**Container**: appears inside four bags in the CENR file:
- Top-level `proxy_hostnames` list
- Top-level `vpn_hostnames` list
- `by_city[<city>].proxy_hostnames` list
- `by_city[<city>].vpn_hostnames` list

### v3 Object Shape

```json
{
  "host": "chi1-2-vpn.zscaler.net",
  "observed_protocol": "UDP",
  "observed_port": 500,
  "last_probed": "2026-07-26T14:22:03Z"
}
```

### Attributes

| Field               | Type                    | Required   | Notes                                                                                          |
|---------------------|-------------------------|------------|------------------------------------------------------------------------------------------------|
| `host`              | `str`                   | yes        | Fully qualified hostname.                                                                      |
| `observed_protocol` | `str \| null`           | no         | One of `"HTTPS"`, `"TCP/<port>"`, `"UDP"`, `"UDP/<port>"`, or `null` when no observation.      |
| `observed_port`     | `int \| null`           | no         | The port on which the observation succeeded. `null` when no observation.                       |
| `last_probed`       | `str \| null` (ISO8601) | no         | UTC timestamp of the observation write. `null` when no observation.                            |

### Validation Rules

- `host` MUST be non-empty and match a DNS-legal FQDN pattern.
- If any observation field is set, all three (`observed_protocol`,
  `observed_port`, `last_probed`) SHOULD be set together (writer emits them
  atomically). Loader tolerates any subset being null for forward robustness.
- `observed_port` MUST be in `[1, 65535]` when non-null.
- `last_probed` MUST be parseable by `datetime.fromisoformat` (accept `Z` or
  `+00:00` suffix).

### Backward-Compatibility Adapter (v2 -> v3)

When the loader sees `schema_version < 3` OR missing, every bare string in
`proxy_hostnames` / `vpn_hostnames` / `by_city[*].{proxy,vpn}_hostnames` is
wrapped as `{"host": "<string>"}`. Observation fields remain absent (treated
as `null` when read).

### State Transitions

1. **Load**: adapter promotes v2 bare strings -> v3 objects with only `host`
   set. Single `logger.info` per load.
2. **Refresh probe**: `run_full_validation` returns fresh results; the write
   path indexes by FQDN and populates observation fields.
3. **Atomic write**: `_atomic_write_json` emits `schema_version: 3` and the
   full v3-shaped entries.

---

## 3. `ZCCFqdnEntry` (schema v3)

**Location**: `data/zscaler_client_connector_probes.json`

**Container**: appears inside `roles[<role>].fqdns` list.

### v3 Object Shape

Identical to `CENRHostEntry`:

```json
{
  "host": "gateway.zscaler.net",
  "observed_protocol": "HTTPS",
  "observed_port": 443,
  "last_probed": "2026-07-26T14:22:03Z"
}
```

### Validation Rules

Same as `CENRHostEntry`. The two entries share one shape and one adapter so
the loader has a single code path.

### Backward-Compatibility Adapter

Same v2-string-to-v3-object promotion. Fires once per load with a single
`logger.info`.

---

## 4. `SyntheticProbeTarget` (transient string)

**Location**: emitted by
`src/org/org_synthetic_probes_manager.py::_probe_target()` into the value of
each Mist `custom_probes[i].target` field.

### Shapes (three-way dispatch)

| Shape                     | Trigger                                                         | Example                                     |
|---------------------------|-----------------------------------------------------------------|---------------------------------------------|
| `https://<fqdn>`          | `observed_protocol` is `HTTPS` or `TCP/443`                     | `https://chi1-2.sme.zscaler.net`            |
| `<fqdn>:<observed_port>`  | `observed_protocol` is any UDP-family or non-HTTP TCP token     | `chi1-2-vpn.zscaler.net:500`                |
| catalogue default + WARN  | `observed_protocol` is `null` (no observation cached)           | falls back to `probe_default.protocol/port` |

### Validation Rules

- MUST be a non-empty string.
- MUST NOT contain whitespace.
- HTTPS shape MUST elide the default port (443).
- Bare host:port shape MUST NOT include a scheme prefix (no `udp://`).
- Fallback branch MUST emit exactly one `logger.warning` naming the host and
  the reason `"no observation cached"`.

### Relationships

- Consumes `CENRHostEntry` / `ZCCFqdnEntry` observation fields.
- Consumed by Mist API surface (`updateOrgSettings.custom_probes[i].target`).

### State Transitions

Recomputed on every Menu 206 invocation. No persistence of the emitted
string itself.

---

## Cross-Entity Invariants

- **INV-1**: For every FQDN with `observed_protocol == "HTTPS"`, the
  emitted `SyntheticProbeTarget` for that FQDN MUST equal
  `f"https://{fqdn}"`. (SC-001 companion invariant.)
- **INV-2**: For every FQDN with `observed_protocol` in the UDP family, the
  emitted `SyntheticProbeTarget` MUST NOT begin with `https://`. (SC-001
  direct invariant.)
- **INV-3**: For every `CENRHostEntry` with any observation field set,
  `last_probed` MUST be no older than the last successful
  `run_full_validation` call. (Freshness invariant enforced by writer.)
- **INV-4**: `schema_version` in the JSON file MUST equal `3` after any
  successful `_atomic_write_json` from this feature's code path.

---

## Non-Entities (explicitly out of scope)

- **IKE responder replies** are not modelled beyond `"open"` / `"no_reply"`.
  See R-002.
- **A separate observations sidecar file** is rejected. See R-003.
- **GRE probe results** are not added. See FR-011.
