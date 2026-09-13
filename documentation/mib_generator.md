# The SNMP MIB generator

## What it does

The generator writes `documentation/mibs/MISTHELPER-MIB.mib`. A person no longer
edits that file by hand.

The generator reads three inputs:

| Input | Path | Question it answers |
| --- | --- | --- |
| The Mist OpenAPI file | `documentation/mist-api-openapi31json.json` | What type does a Mist field carry? |
| The metric catalog | `src/metrics_gateway/catalog.py` | Which readings does the agent answer? |
| The OID ledger | `data/mib_generator/oid_assignments.json` | Which number does each reading own? |

A fourth file, `data/mib_generator/allowlist.json`, names the Mist endpoints
that the generator reads.

## Why a ledger

A monitoring system stores years of history against an OID. If an object moves
to another number, that history points at the wrong thing, and nothing warns the
operator.

The ledger holds the number and the name of every field, live or removed. The
ledger wins over every rule in the code. A change to the naming rule therefore
cannot rename an object that already exists.

The ledger key is the scope and the source path, never the descriptor:

- `site/num_ap` for a field that Mist sends.
- `org/#mist_scrape_success` for a reading that the collector derives.

## The OID layout

The agent in `src/metrics_gateway/snmp.py` decides where an object answers. The
MIB states the same place:

- A scalar answers at `<base>.<subtree>.<column>.0`.
- A table cell answers at `<base>.<subtree>.1.<column>.<row>`.

The table node carries the subtree number. The entry node carries the 1. No node
sits between them. An earlier hand-written MIB added one level there, and every
table object became unreachable by name. The contract test
`tests/contract/test_generated_mib_matches_agent.py` stops that defect.

| Subtree | Contents |
| --- | --- |
| 1 | The organization scalars |
| 2 | The site table |
| 3 | The device table |
| 4 | The service level expectation table |

Column 99 of each table repeats the row identity. Column 100 is the index, and
the agent never answers it.

## Column bands

| Band | Owner |
| --- | --- |
| 1 to 89 | A data column. The generator hands out a free number from this band. |
| 90 to 98 | Reserved for the catalog. The gateway health readings live here. |
| 99 | The row identity column. |
| 100 | The index column. |

## How to run it

```powershell
# Write the MIB.
python MistHelper.py --mib-generate

# Print the MIB and write nothing.
python MistHelper.py --mib-dry-run

# List the Mist fields that the catalog does not yet serve.
python MistHelper.py --mib-report

# Exit 1 when the stored MIB is out of date. Continuous integration runs this.
python MistHelper.py --mib-check
```

Menu entry 243 runs the generate action.

## The type rule

The rule branches on the catalog kind first, because `OidTree._encode` in the
agent branches on the same value. The catalog therefore always wins over the
JSON type of the OpenAPI file.

| Test, in order | SYNTAX |
| --- | --- |
| The kind is `INFO` | `DisplayString (SIZE (0..255))` |
| The kind is `COUNTER` | `Counter64` |
| The SNMP scale is not 1 | `Gauge32` |
| The JSON type is `boolean` | `INTEGER { false(0), true(1) }` |
| The JSON type is `string` | `DisplayString (SIZE (0..255))` |
| Every other field | `Gauge32` |

## When Mist removes a field

The generator marks the ledger entry `obsolete` and keeps its number reserved
forever. The MIB still names the object, with `STATUS obsolete`. No later field
can take that number, so no stored history can change meaning.

## When Mist adds a field

The generator does not add a column on its own. Add the reading to
`src/metrics_gateway/catalog.py` first, then run the generator. Use
`--mib-report` to see which fields are available.
