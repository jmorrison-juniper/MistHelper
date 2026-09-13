# Phase 0 Research: OpenAPI MIB Generator

Every unknown of the Technical Context is closed below. No `NEEDS CLARIFICATION` marker remains.

## R1. How to load a 16.6 MB JSON file inside the memory limit

**Decision**: Read the whole file with `json.load` in one call, and hold the result in one
`OpenApiDocument` instance for the life of the run.

**Rationale**: The cost is measured, not guessed. The measurement ran on this workstation with
CPython 3.13.3 against the real file:

| Reading | Value |
|---|---|
| File size | 16.6 MB |
| `json.load` wall time, warm cache | 0.262 s |
| `json.load` wall time, cold run | 0.491 s |
| `tracemalloc` peak, Python objects | 69.7 MB |
| Paths parsed | 719 |
| Component schemas parsed | 1,799 |
| `openapi` version field | `3.1.0` |

The budget in SC-007 is 30 s and 1 GB. The load uses under 2 percent of the time budget and under 7
percent of the memory budget. A streaming parser would buy nothing and would cost a dependency, an
index pass, and a large rise in code complexity. `$ref` resolution needs random access into
`components.schemas`, which a streaming parser cannot give without building the same dictionary.

**Alternatives considered**:

- `ijson` streaming: rejected. It adds a third-party dependency and it cannot answer a `$ref`
  lookup without a second pass that rebuilds the dictionary in memory anyway.
- `mmap` plus a hand-written scanner: rejected. It re-implements a JSON parser, which is a
  correctness risk with no measured benefit.
- Pre-split the file into per-schema files: rejected. It adds a second generated artifact and a
  second staleness risk.

**Guard**: `test_runner.py` holds a performance test that measures the run with `tracemalloc` and
fails above the stated limits, so a future growth of the Mist file cannot pass unnoticed.

## R2. How to join `oneOf`, `anyOf`, and `allOf` into one property set

**Decision**: `SchemaFlattener` treats all three keywords as a union of property sets. It walks each
branch, it merges the property maps in branch order, and it records the branch name on each
`FieldRecord`. A property that two branches both hold keeps the first branch that defined it and the
flattener logs the second.

**Rationale**: The counts across the 1,799 schemas are 1,229 with `properties`, 32 with `oneOf`, 26
with `anyOf`, and 4 with `allOf`. The union is the only choice that works for `stats_device`, which
is `oneOf: [stats_ap, stats_switch, stats_gateway]` with a discriminator and no properties of its
own. SNMP has one device table, and the agent already serves the access point, the switch, and the
gateway from that one table. A union of the three branches is exactly the column set that table
needs. A discriminator adds no column, because the row identity column already tells a poller which
row it read.

`getOrgStats` returns `allOf: [$ref stats_org, {description, examples}]`, so `allOf` in this file is
a `$ref` plus annotation, and a plain merge is correct.

**Alternatives considered**:

- Emit one table for each `oneOf` branch: rejected. It contradicts the catalog, which holds one
  device table on purpose, and it would break every live OID.
- Refuse a schema with no properties: rejected. It fails on `stats_device`, which the gateway needs.

## R3. How to read the OpenAPI 3.1 nullable form

**Decision**: When `type` is a list, drop `"null"` and take the first remaining entry. When nothing
remains, skip the field and log the skip.

**Rationale**: The file uses the 3.1 form `type: ["string", "null"]` and never the 3.0 `nullable`
keyword. SNMP has no null value. The agent already answers `NONE` for an absent reading, which ends
a walk correctly, so the MIB needs no null marker. The non-null type is the type of every value the
agent can ever return.

## R4. How to stop a `$ref` cycle

**Decision**: `OpenApiDocument.resolve` carries a depth counter with a fixed limit of 12. At the
limit it stops the walk, it logs the reference chain that it cut, and it returns the partial schema.

**Rationale**: A cycle is real in a large OpenAPI file, and an unbounded walk ends in a
`RecursionError` that tells an operator nothing. A limit of 12 is far above the deepest real Mist
statistics schema, which nests 4 levels, so the limit only ever fires on a cycle or on a nesting
depth that SNMP cannot represent anyway. The log line names the chain, so an engineer can act.

## R5. Where the object set comes from: the catalog, not the OpenAPI file

**Decision**: The catalog decides which objects the MIB holds. The OpenAPI file decides the type and
the description of each of them, and it proves the field still exists.

**Rationale**: FR-013 states the reason: a MIB object the agent never answers returns
`No Such Instance`, and a NOC engineer reads that as a fault. The catalog is the only file that
knows what the agent answers. This makes the drift check a three-way join:

| Case | Action |
|---|---|
| The catalog names a field and the OpenAPI schema holds it | Emit the object. |
| The catalog names a field and the OpenAPI schema lost it | Stop with an error. Mist removed a field. |
| The OpenAPI schema holds a field and the catalog does not | Report it. Do not emit it. |
| The catalog names a field with an empty `source` | Emit the object. The collector derives the value, so no OpenAPI field exists. Take the description from `help_text`. |

The fourth row matters. The catalog holds several derived readings, such as
`mist_org_sle_ratio`, `mist_device_up`, and the three `mist_scrape_*` readings. Their `source` is
empty on purpose, so the OpenAPI check must not run against them.

## R6. Why JSON and not YAML for the two data files

**Decision**: JSON, with a JSON Schema for each file in `contracts/`.

**Rationale**: JSON is in the standard library and the repository already reads JSON in this area.
`PyYAML` is present, but a YAML file would add an import, a safe-load rule, and a second syntax an
operator must learn, and it buys only a comment character. The `notes` field of a ledger entry gives
the same explanation power that a YAML comment would give, and it survives a rewrite by `save`.
A comment in YAML would not survive a rewrite, so YAML would be the worse choice here.

## R7. How the number stability promise holds

**Decision**: A ledger keyed by `<scope>/<source path>`, never by descriptor. A removed field keeps
its entry with `state: "obsolete"`. `claim` gives a new field the lowest free column of its subtree,
counting only columns below 90.

**Rationale**: A key on the descriptor would move an OID when a person improves a name, which is
exactly the failure that SC-005 forbids. A key on the scope and the source path is stable across a
rename. The reserved band matters: the catalog already uses columns 90 to 92 for the gateway health
readings and column 99 for the row identity, so `claim` must never hand out a number in that band.
The ledger is checked in, so the promise survives a fresh clone.

## R8. Which descriptor rule, and which collision rule

**Decision**: See [data-model.md](./data-model.md) for the full rule. The short form: build the name
from the scope and the field path, keep letters and digits only, lower the first letter, cut to 62
characters, and add a numeric suffix on a collision. Record the result in the ledger, so the name
never changes again.

**Rationale**: SMIv2 gives three hard rules, and Hypothesis can check all three against random
input. The ledger record turns a computed name into a stored name after the first run, so a change
to the rule cannot rename a live object.

## R9. Which tests need `snmptranslate`, and how the Windows gate stays green

**Decision**: One contract test calls `snmptranslate -Tp -m <file>`. It carries
`@pytest.mark.skipif(shutil.which("snmptranslate") is None, ...)`.

**Rationale**: The quality gate runs on a Windows workstation that has no Net-SNMP. A hard failure
there would block every merge for a reason that has nothing to do with the change. A skip keeps the
gate honest on Windows, and CI installs Net-SNMP so the test truly runs before a merge. Every other
MIB test parses the text directly and needs no binary, which is the rule the existing
`test_mib_matches_catalog.py` already follows.

## R10. Which coverage number applies

**Decision**: 90 percent for the new package.

**Rationale**: FR-046 asks for 80 percent. `pyproject.toml` sets `fail_under = 90` for the whole
repository. The stricter number wins, because a lower local target cannot pass the repository gate.
