# Phase 1 Data Model: OpenAPI MIB Generator

## 1. Entities

### 1.1 `FieldRecord` (`schema.py`)

A frozen dataclass with slots. One scalar field of one selected schema.

| Field | Type | Meaning |
|---|---|---|
| `scope` | `MetricScope` | The Mist object the field describes. Comes from the allow list entry. |
| `path` | `str` | The dotted path into the Mist reading, such as `user_minutes.total`. This is the join key against `MetricDefinition.source`. |
| `json_type` | `str` | The non-null JSON type: `integer`, `number`, `string`, or `boolean`. |
| `description` | `str` | The OpenAPI description, or an empty string. |
| `branch` | `str` | The `oneOf` or `anyOf` branch that gave the field, or an empty string. |
| `format_hint` | `str` | The OpenAPI `format`, such as `int64`. Empty when absent. |

**Validation**: `path` must be non-empty. `json_type` must be one of the four names above. A field
whose resolved type is `object` or `array` never becomes a `FieldRecord`, because SNMP has no nested
table (FR-031).

### 1.2 `AllowListEntry` (`assignment.py`)

| Field | Type | Meaning |
|---|---|---|
| `operation_id` | `str` | The `operationId` of a GET operation. |
| `scope` | `MetricScope` | The scope the readings of that operation carry. |
| `notes` | `str` | Why the operator selected it. |

**Validation** (FR-011): the `operationId` must exist in the document, and the operation must be a
GET. Either failure stops the run before the writer opens a file.

### 1.3 `LedgerEntry` (`assignment.py`)

| Field | Type | Meaning |
|---|---|---|
| `key` | `str` | `<scope>/<path>`. The stable identity. Never the descriptor. |
| `subtree` | `int` | From `SUBTREE_BY_SCOPE`. |
| `column` | `int` | The column below the subtree. |
| `descriptor` | `str` | The SMIv2 name. Stored, so it never changes after the first run. |
| `state` | `"live"` or `"obsolete"` | A removed field turns obsolete and keeps its number. |
| `notes` | `str` | Free text for a person. |

### 1.4 `MibObject` (built inside `mib.py`, not persisted)

The join of one `MetricDefinition`, one `LedgerEntry`, and zero or one `FieldRecord`. It is what
`MibWriter.render` turns into text.

### 1.5 Relationships

```text
AllowListEntry --(operation_id)--> OpenAPI operation --> response schema
                                                              |
                                                     SchemaFlattener
                                                              v
                                                        FieldRecord
                                                              |
                     MetricDefinition.source == FieldRecord.path
                                                              v
LedgerEntry --(key = scope/path)------------------------> MibObject --> SMIv2 text
```

The catalog decides which `MibObject` values exist. The `FieldRecord` supplies the type and the
description. The `LedgerEntry` supplies the number and the name.

## 2. The allow list file

**Location**: `data/mib_generator/allowlist.json`
**Schema**: [contracts/allowlist.schema.json](./contracts/allowlist.schema.json)

The default holds exactly the three endpoints the gateway reads today (FR-009). The `operationId`
values below are read from the real file, not guessed.

```json
{
  "version": 1,
  "entries": [
    {
      "operation_id": "getOrgStats",
      "scope": "org",
      "notes": "Supplies the organization scalars and the sle array. The response is allOf: [stats_org, annotation]."
    },
    {
      "operation_id": "listOrgSiteStats",
      "scope": "site",
      "notes": "Supplies the site table. The response is an array of stats_site."
    },
    {
      "operation_id": "listOrgDevicesStats",
      "scope": "device",
      "notes": "Supplies the device table. The response is an array of stats_device, which is oneOf: [stats_ap, stats_switch, stats_gateway]."
    }
  ]
}
```

**Note on the SLE scope**: `MetricScope.SLE` needs no entry of its own. The SLE readings come from
the `sle` array inside the `getOrgStats` response, so the `org` entry covers them. `SchemaFlattener`
emits an SLE field with the path form `sle[].user_minutes.total`, and `MibGeneratorRunner` maps it
to the SLE scope through the catalog `source` value. The catalog is the authority for the scope of
each reading, and the allow list only names the endpoint that carries the data.

## 3. The OID assignment file

**Location**: `data/mib_generator/oid_assignments.json`
**Schema**: [contracts/oid-assignments.schema.json](./contracts/oid-assignments.schema.json)

The file is sorted by subtree and then by column, so a run writes stable bytes and a review shows a
small diff. A worked example, seeded from the catalog:

```json
{
  "version": 1,
  "base_oid": ".1.3.6.1.4.1.11.2147483646",
  "entries": [
    {
      "key": "org/num_sites",
      "subtree": 1,
      "column": 2,
      "descriptor": "mistOrgSites",
      "state": "live",
      "notes": "Seeded from mist_org_sites in the catalog."
    },
    {
      "key": "org/",
      "subtree": 1,
      "column": 90,
      "descriptor": "mistScrapeSuccess",
      "state": "live",
      "notes": "A derived reading. The catalog source is empty, so no OpenAPI field backs it."
    },
    {
      "key": "device/rx_bytes",
      "subtree": 3,
      "column": 11,
      "descriptor": "mistDeviceReceivedBytes",
      "state": "live",
      "notes": "A counter. Counter64, because a Mist byte count passes 2^32 within one day."
    },
    {
      "key": "device/num_wired_clients",
      "subtree": 3,
      "column": 14,
      "descriptor": "mistDeviceWiredClients",
      "state": "obsolete",
      "notes": "Mist removed the field in the 2026-08 release. The number stays reserved."
    }
  ]
}
```

`base_oid` in this file must equal `DEFAULT_BASE_OID` in `src/metrics_gateway/snmp.py`. A difference
stops the run (FR-017).

### 3.1 The column bands

| Band | Use | Who assigns it |
|---|---|---|
| 1 to 89 | A data column. | `OidLedger.claim` hands out the lowest free number in this band. |
| 90 to 98 | Reserved. The catalog already uses 90, 91, and 92 for the gateway health readings. | The catalog only. `claim` never enters this band. |
| 99 | The row identity column, as `ROW_IDENTITY_COLUMN` states. | The writer emits it for each table. It is never in the ledger. |

### 3.2 The stop conditions of `OidLedger.validate` (FR-024)

The run stops and writes no MIB when any of these holds:

1. Two entries share a `key`.
2. Two entries in one subtree share a `column`.
3. Two entries share a `descriptor`.
4. A `subtree` value is not a value of `SUBTREE_BY_SCOPE`.
5. A `column` value is outside 1 to 98, or it sits in the reserved band while the catalog does not
   claim it.
6. `base_oid` differs from `DEFAULT_BASE_OID`.

## 4. The type mapping

`SnmpTypeMapper.syntax_for(definition, field)` reads the catalog `MetricDefinition` first and the
`FieldRecord` second. The catalog wins on every conflict, because the catalog decides what the agent
actually puts on the wire in `OidTree._encode`.

| Case | Test in order | SYNTAX | UNITS | Why |
|---|---|---|---|---|
| Informational reading | `definition.kind is MetricKind.INFO` | `DisplayString (SIZE (0..255))` | none | `OidTree._encode` returns `TYPE_STRING` for a sample that carries text. |
| Counter | `definition.kind is MetricKind.COUNTER` | `Counter64` | `"bytes"` when the path ends in `_bytes`, else none | `OidTree._encode` returns `TYPE_COUNTER64` for a counter. A Mist byte count passes 2^32 within one day (FR-026, FR-030). |
| Scaled fraction, ratio | `definition.snmp_scale == 10000` | `Gauge32` | `"ten-thousandths"` | `RATIO_SNMP_SCALE`. The agent sends `round(value * 10000)`, so 0.97 arrives as 9700 (FR-027). |
| Scaled fraction, duration | `definition.snmp_scale == 1000` | `Gauge32` | `"milliseconds"` | `SECONDS_SNMP_SCALE`. A duration below one second stays visible. |
| JSON `boolean` | `field.json_type == "boolean"` | `INTEGER { false(0), true(1) }` | none | FR-028. |
| JSON `string` | `field.json_type == "string"` | `DisplayString (SIZE (0..255))` | none | FR-029. The size limit is stated, because Observium needs a bound. |
| JSON `integer` or `number`, gauge kind | default | `Gauge32` | from the name suffix: `seconds`, `bytes`, `watts`, `degrees Celsius` | FR-026. |
| A row identity column | the writer emits it | `DisplayString (SIZE (0..255))` | none | `OidTree._add_identity_column` publishes `TYPE_STRING`. |

### 4.1 The fractional case in detail

A JSON `number` never reaches SNMP as a fraction. The mapper reads `definition.snmp_scale`, it emits
`Gauge32`, and it appends one sentence to the DESCRIPTION that names the unit and the scale, in the
same words the catalog `help_text` already uses:

> `SNMP reports ten-thousandths.`

This keeps the MIB text and the catalog text in agreement, and a NOC engineer who reads 9700 knows
it means 0.97.

### 4.2 The 64-bit case in detail

The trigger is the catalog kind, not the JSON type. `MetricKind.COUNTER` gives `Counter64`. This is
the correct trigger, because `OidTree._encode` branches on the same value. A JSON `format: int64`
hint on a gauge field does not force `Counter64`, because the agent clamps a gauge to
`GAUGE_CEILING` and a `Counter64` on a falling value would be wrong SNMP semantics.

### 4.3 The nullable case in detail

`type: ["string", "null"]` resolves to `string` before the table above runs. The MIB gains no null
marker, because SNMP has none. The agent answers `NONE` for an absent reading, which ends a walk
correctly.

## 5. The descriptor rule

`DescriptorMaker.make(scope, path, taken)` returns a valid, unique SMIv2 descriptor.

**The steps, in order:**

1. Start with the literal `mist`.
2. Append the scope word, capitalised: `Org`, `Site`, `Device`, `Sle`.
3. Split the field path on `.`, `_`, `[`, and `]`. Drop an empty part.
4. Capitalise the first letter of each part and join the parts with no separator.
5. Remove every character that is not a letter or a digit.
6. Lower the first letter of the whole name, so it always starts with a lowercase `m`.
7. Cut the name to 62 characters, on a part boundary when one exists inside the last 8 characters,
   so the name stays readable.
8. Apply the collision rule below.

**Worked examples:**

| Scope | Path | Descriptor |
|---|---|---|
| `device` | `rx_bytes` | `mistDeviceRxBytes` |
| `sle` | `user_minutes.total` | `mistSleUserMinutesTotal` |
| `org` | `num_devices_disconnected` | `mistOrgNumDevicesDisconnected` |
| `device` | `if_stat.eth0.rx_bytes` | `mistDeviceIfStatEth0RxBytes` |

**The three SMIv2 rules the result always meets** (FR-032): it starts with a lowercase letter
(step 6 guarantees it, and `mist` is a constant prefix), it holds letters and digits only (step 5),
and it never passes 64 characters (step 7 caps it at 62 and the collision rule adds at most 2).

### 5.1 The collision rule (FR-033, FR-034)

1. **The ledger wins.** When the ledger already holds an entry for the key, `make` is never called.
   The stored descriptor is used. A change to the rule above therefore can never rename a live
   object.
2. **First claim wins.** For a new key, the candidate name from step 7 is used when no live or
   obsolete entry holds it.
3. **A numeric suffix breaks a tie.** When the name is taken, append `2`. When `…2` is taken, append
   `3`, and so on to `99`. The base name is cut to 62 characters first, so the suffix keeps the
   whole name at or below 64.
4. **A 100th collision stops the run.** Ninety-nine names that differ only by a digit means the
   naming rule is broken, and an automatic 100th name would hide the defect.
5. **The chosen name is written to the ledger** in the same run, so the second run reads it back at
   step 1 and the name is stable forever.

The obsolete entries take part in the uniqueness check. A retired descriptor is never reused, in the
same way its number is never reused.

## 6. The output MIB shape

```text
<base>                                   mistHelperMIB   MODULE-IDENTITY
<base>.1                                 mistOrg         OBJECT-IDENTITY
<base>.1.<column>.0                      a scalar        OBJECT-TYPE
<base>.2                                 mistSiteTable   SEQUENCE OF MistSiteEntry
<base>.2.1                               mistSiteEntry   INDEX { mistSiteIndex }
<base>.2.1.<column>.<row>                a table cell    OBJECT-TYPE
<base>.2.1.99.<row>                      mistSiteId      the row identity column
<base>.3 …                               the device table, in the same shape
<base>.4 …                               the SLE table, in the same shape
```

The table sits directly below the module root, and the entry sits directly below the table. There is
no node between them. This is the defect the hand-written MIB carried, and the shape above is what
`OidTree._oid_for` actually answers (FR-019).

Each table holds an `INDEX` clause that names its index column (FR-037). The index is a
`Integer32 (1..2147483647)` position column, because the agent numbers a row by its sort position on
each read. The row identity column at 99 carries the real identity, and the MIB DESCRIPTION of the
index column says so in plain words, so no operator treats a row number as a key.

An obsolete entry is emitted with `STATUS obsolete` and a DESCRIPTION that names the release in which
Mist removed the field (FR-023).
