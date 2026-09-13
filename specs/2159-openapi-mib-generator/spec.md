# Feature Specification: OpenAPI MIB Generator

**Feature Branch**: `2159-openapi-mib-generator`

**Created**: 2026-09-04

**Status**: Draft

**Input**: User description: "build a python module, that can take the mistapi openapi JSON spec file and injest it, and crank out a MIB file, that can be imported into a snmp monitoring tool like observiium or solarwinds. that way if Mist releases new api endpoints and a corresponding JSON file container the new openapi schemas, we can run this python module and programitcly update the MIB."

## Overview

MistHelper serves Mist Cloud health over SNMP. The gateway is in `src/metrics_gateway/`. It reads three Mist endpoints and it publishes 35 readings. A person wrote the MIB at `documentation/mibs/MISTHELPER-MIB.mib` by hand. A person must edit that file each time Mist adds a field. The hand work already made one defect. The first version put every table one level too deep, so no table object was reachable by name.

This feature adds a module that reads the Mist OpenAPI file and writes the MIB. The module removes the hand editing. A person runs the module after Mist ships a new OpenAPI file, and the MIB is correct again.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate the MIB from the OpenAPI file (Priority: P1)

An engineer has a new Mist OpenAPI file. The engineer runs the module against that file. The module writes a MIB file. The MIB loads in Net-SNMP without an error, and it loads in Observium and in SolarWinds.

**Why this priority**: This is the feature. Without it the hand editing stays.

**Independent Test**: Run the module against the OpenAPI file in the repository. Load the output with `snmptranslate`. The command reports no error and it prints the object names.

**Acceptance Scenarios**:

1. **Given** the OpenAPI file in `documentation/mist-api-openapi31json.json`, **When** the engineer runs the module, **Then** the module writes a MIB file and it reports the count of objects it wrote.
2. **Given** the written MIB file, **When** `snmptranslate -Tp -m <file>` runs, **Then** the command exits with code 0 and it prints no parse error.
3. **Given** the written MIB file, **When** an operator imports it into Observium and into SolarWinds, **Then** each tool accepts the file and it lists the objects.
4. **Given** the written MIB file, **When** a poller walks the running agent at `.1.3.6.1.4.1.11.2147483646`, **Then** each name in the MIB maps to an OID the agent answers.

---

### User Story 2 - Keep every OID stable across runs (Priority: P1)

A monitoring system stores history against an OID. An engineer runs the module again after Mist adds fields and removes fields. Every field that stayed keeps the same OID. Only a new field gets a new number.

**Why this priority**: A renumber destroys the stored history of the customer. That is worse than the hand editing this feature replaces.

**Independent Test**: Run the module twice. Between the runs, add a field to a copy of the OpenAPI file and remove another field. Compare the two MIB files. Every kept object holds its first number.

**Acceptance Scenarios**:

1. **Given** a checked-in assignment file that records the number of each field, **When** the module runs again on the same input, **Then** the output is byte-identical except for the revision date.
2. **Given** an input that adds a new field, **When** the module runs, **Then** the new field takes the next free number and it appends one line to the assignment file.
3. **Given** an input that removes a field, **When** the module runs, **Then** the module keeps the number reserved, it marks the object `obsolete` in the MIB, and it never gives that number to another field.
4. **Given** an assignment file that gives one number to two fields, **When** the module runs, **Then** the module stops with an error and it writes no MIB.

---

### User Story 3 - Change the endpoint selection without a code change (Priority: P2)

An operator wants a Mist statistics endpoint that the module did not select. The operator edits a selection file. The operator runs the module again. The new endpoint is in the MIB.

**Why this priority**: The selection rule decides the size of the MIB. An operator must be able to change it, but the default rule already covers the common need.

**Independent Test**: Add one `operationId` to the selection file. Run the module. The MIB holds the objects of that endpoint.

**Acceptance Scenarios**:

1. **Given** the default selection file, **When** the module runs, **Then** it selects only the endpoints that the file names.
2. **Given** an `operationId` in the selection file that the OpenAPI file does not hold, **When** the module runs, **Then** the module stops with an error that names the missing `operationId`.
3. **Given** a selection file that names an endpoint that is not a GET, **When** the module runs, **Then** the module stops with an error.

---

### User Story 4 - Move from the hand-written MIB (Priority: P2)

An engineer replaces the hand-written MIB with the generated MIB. Every object that a poller reads today keeps its name and its OID.

**Why this priority**: A live poller must not break on the day of the change.

**Independent Test**: Compare the object list of the hand-written MIB with the object list of the generated MIB. Each name and each OID of the old file is in the new file.

**Acceptance Scenarios**:

1. **Given** the hand-written MIB and the generated MIB, **When** a test compares the two object lists, **Then** each of the 35 readings holds the same name and the same OID in both files.
2. **Given** the generated MIB, **When** a test reads the table shape, **Then** each table cell sits at `<base>.<subtree>.1.<column>.<row>` and no table is one level too deep.
3. **Given** the merge of this feature, **When** the repository builds, **Then** the hand-written MIB is gone and the build makes the MIB from the OpenAPI file.

---

### Edge Cases

- A schema holds no properties, as `stats_device` does. That schema is `oneOf: [stats_ap, stats_switch, stats_gateway]` with a discriminator. The module must join the branches into one set of columns and it must not fail.
- A property uses the OpenAPI 3.1 nullable form `type: ["string", "null"]`. The module must read the first non-null type.
- A property is an array of objects. SNMP has no nested table, so the module must not make a column for it.
- Two different fields make the same descriptor after the SMIv2 name rules run. The module must make the second name unique and it must record the chosen name in the assignment file.
- A descriptor would pass 64 characters. The module must shorten it and it must keep it unique.
- A `$ref` points to itself, directly or through a chain. The module must stop the walk at a depth limit and it must log the cut.
- The input file is not valid JSON, or it is not OpenAPI 3.1. The module must stop with a clear message.
- A number field holds a value above the 32-bit ceiling, such as a byte count. The module must choose a 64-bit type.

## Requirements *(mandatory)*

### Functional Requirements

#### Input and parsing

- **FR-001**: The module MUST read an OpenAPI 3.1 JSON file from a local path. It MUST NOT use the network.
- **FR-002**: The module MUST accept the file in `documentation/mist-api-openapi31json.json`, which holds 16.6 MB, 719 paths, and 1,799 component schemas.
- **FR-003**: The module MUST resolve an internal `$ref`. It MUST stop a walk at a fixed depth limit, and it MUST log each cut.
- **FR-004**: The module MUST join an `allOf` list into one property set. It MUST join a `oneOf` list and an `anyOf` list into one property set, and it MUST record the branch that gave each property.
- **FR-005**: The module MUST read the OpenAPI 3.1 nullable form `type: ["string", "null"]` as the non-null type.
- **FR-006**: The module MUST stop with a clear message when the file is not valid JSON, or when the OpenAPI version is not 3.1.

#### Endpoint selection (design answer 1)

- **FR-007**: The module MUST NOT turn all 508 GET operations into MIB objects. A MIB of that size is too large for a monitoring system to load, and most of those endpoints return configuration, not telemetry.
- **FR-008**: The module MUST select an endpoint by an explicit allow list. The allow list is a checked-in file that names each `operationId` and the scope of the readings it makes.
- **FR-009**: The module MUST ship a default allow list. The default MUST hold the three endpoints the gateway reads today. The default MUST NOT hold more, because a MIB object with no answer looks like a fault.
- **FR-010**: The module MUST offer a report mode. That mode reads the OpenAPI file, it finds each candidate statistics endpoint by `/stats` in the path or `Stats` in a tag, and it prints the candidates with the count of columns each one would add. The report mode MUST NOT write the MIB. An operator uses the report to choose what to add to the allow list.
- **FR-011**: The module MUST stop with an error when the allow list names an `operationId` that the OpenAPI file does not hold, or that is not a GET.
- **FR-012**: An operator MUST be able to change the selection by editing the allow list only. No code change is needed.

#### Coverage of the generated MIB (design answer 2)

- **FR-013**: The generated MIB MUST describe only the readings that the agent serves. A MIB object that the agent never answers returns "No Such Instance" and a NOC engineer reads that as a fault.
- **FR-014**: The module MUST take the served set from the gateway catalog in `src/metrics_gateway/catalog.py`. The OpenAPI file gives the type, the description, and the check that the field still exists. The catalog gives the truth about what the agent answers.
- **FR-015**: The module MUST stop with an error when the catalog names a source field that the selected OpenAPI schema no longer holds. That error tells the team that Mist removed a field.
- **FR-016**: The module MUST report, but MUST NOT emit, a field that the OpenAPI file holds and the catalog does not. That report is the work list for the next catalog change.

#### OID layout and stability

- **FR-017**: The MIB root MUST be `.1.3.6.1.4.1.11.2147483646`. That value MUST match `DEFAULT_BASE_OID` in `src/metrics_gateway/snmp.py`. The module MUST stop with an error when the two differ.
- **FR-018**: A scalar MUST sit at `<base>.<subtree>.<column>.0`.
- **FR-019**: A table cell MUST sit at `<base>.<subtree>.1.<column>.<row>`. The module MUST NOT add a level below the table entry.
- **FR-020**: A subtree number MUST come from `SUBTREE_BY_SCOPE`. Column 99 MUST hold the row identity, as `ROW_IDENTITY_COLUMN` states.
- **FR-021**: The module MUST read a checked-in assignment file that maps a field key to a subtree, a column, and a descriptor. The field key MUST hold the scope and the source path, so a rename of the descriptor does not move the OID.
- **FR-022**: The module MUST give a new field the next free column in its subtree. It MUST append the new entry to the assignment file.
- **FR-023**: The module MUST keep the number of a removed field reserved. It MUST mark that object `STATUS obsolete` in the MIB, and it MUST NOT give the number to another field.
- **FR-024**: The module MUST stop with an error, and it MUST write no MIB, when the assignment file holds a duplicate number, a duplicate name, or a number outside its subtree.
- **FR-025**: Two runs on the same input and the same assignment file MUST write the same bytes, except for the revision date.

#### Type mapping

- **FR-026**: The module MUST map a JSON `integer` to `Gauge32` when the catalog kind is a gauge, and to `Counter64` when the catalog kind is a counter.
- **FR-027**: The module MUST map a JSON `number` to `Gauge32` after the catalog scale. The scale is 10000 for a ratio and 1000 for a duration in seconds. The DESCRIPTION of the object MUST name the unit and the scale.
- **FR-028**: The module MUST map a JSON `boolean` to `INTEGER { false(0), true(1) }`.
- **FR-029**: The module MUST map a JSON `string` to `DisplayString` with a stated size limit.
- **FR-030**: The module MUST use `Counter64` for a value that can pass the 32-bit ceiling, such as a byte count.
- **FR-031**: The module MUST NOT make a column for an array of objects, or for a nested object. SNMP has no nested table.

#### SMIv2 output rules

- **FR-032**: A descriptor MUST start with a lowercase letter, MUST hold letters and digits only, and MUST NOT pass 64 characters.
- **FR-033**: No two objects MUST share a descriptor, and no two objects MUST share an OID.
- **FR-034**: The module MUST make a unique descriptor when two fields collide, and it MUST record the chosen descriptor in the assignment file so the name is stable.
- **FR-035**: The MIB MUST hold a `MODULE-IDENTITY` with a `LAST-UPDATED` value, an `ORGANIZATION` value, and a `REVISION` history.
- **FR-036**: Each object MUST hold a `DESCRIPTION`. The text MUST come from the OpenAPI description when one exists, and from the catalog help text when one does not. The text MUST follow Simplified Technical English.
- **FR-037**: Each table MUST hold an `INDEX` clause that names the index column.

#### Interface

- **FR-038**: The module MUST offer a class-based Python interface. No wrapper function.
- **FR-039**: The module MUST offer a command line entry point with these actions: generate, report candidates, and check. The check action MUST validate the current MIB against the OpenAPI file and the catalog, and it MUST exit non-zero on a drift. CI uses the check action.
- **FR-040**: The module MUST log one line before an action and one line after it.
- **FR-041**: The module MUST write the MIB to a path the caller gives. It MUST NOT overwrite a file when the caller asks for a dry run.

#### Quality

- **FR-042**: The module MUST target Python 3.13 or newer.
- **FR-043**: Each function MUST hold at most 5 parameters, at most 5 blocks, and at most 25 lines.
- **FR-044**: Each executable line MUST carry an inline comment that states the reason.
- **FR-045**: The module MUST pass ruff, black, mypy, bandit, vulture, pydocstyle, pylint at 9.5, radon complexity at 10, and interrogate at 90 percent.
- **FR-046**: Tests MUST live under `tests/unit/`. Coverage MUST reach 80 percent. Hypothesis MUST test the descriptor rules and the number stability.

### Key Entities

- **OpenAPI document**: The local JSON file. It holds the paths, the operations, and the component schemas.
- **Endpoint selection**: A checked-in list of `operationId` values and the scope of each one. It decides which endpoints reach the MIB.
- **Field**: One property of a selected schema. It holds a name, a JSON type, a description, and a source path.
- **OID assignment**: A checked-in record that maps a field key to a subtree, a column, a descriptor, and a state of live or obsolete. It holds the stability promise.
- **MIB module**: The output text file in SMIv2 form.
- **Drift report**: The list of fields that the OpenAPI file holds and the catalog does not, and the list of catalog fields that the OpenAPI file lost.

## Test Plan

- **Unit**: The parser reads a small OpenAPI fixture. The tests cover `allOf`, `oneOf` with a discriminator, `anyOf`, the nullable form, a self `$ref`, and an empty schema.
- **Unit**: The name maker turns a field name into a descriptor. Hypothesis feeds random names and checks the three SMIv2 rules and the uniqueness.
- **Unit**: The number keeper. Hypothesis adds and removes fields in a random order and checks that a kept field never changes its number.
- **Unit**: The type mapper. Each JSON type gives the stated SNMP type, and a scaled ratio gives a whole number.
- **Contract**: The generated MIB parses with `snmptranslate`. The test skips when Net-SNMP is absent, and CI installs Net-SNMP so the test runs there.
- **Contract**: Every OID in the generated MIB matches an OID that `src/metrics_gateway/snmp.py` answers.
- **Regression**: The 35 objects of the hand-written MIB keep the same name and the same OID.
- **Performance**: A run against the 16.6 MB file finishes inside the stated limit and stays inside the stated memory limit.
- **Manual, once**: Import the output into Observium and into SolarWinds and record the result in the pull request.

## Migration Path

1. Add the module, the allow list, and the assignment file. Seed the assignment file from the hand-written MIB, so every live OID keeps its number.
2. Generate the MIB to a new path. Compare it with the hand-written MIB. The 35 live objects must match.
3. Replace `documentation/mibs/MISTHELPER-MIB.mib` with the generated file. Fix the table depth defect as part of the replacement, and note the fix in the revision history of the MIB.
4. Add the check action to CI, so a drift between the OpenAPI file, the catalog, and the MIB fails the build.
5. Record in `CHANGELOG.md` that a person must not edit the MIB by hand again.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: An engineer updates the MIB for a new Mist OpenAPI release in under 10 minutes, with no hand edit of the MIB text.
- **SC-002**: `snmptranslate` loads the generated MIB with 0 errors and 0 warnings.
- **SC-003**: Observium and SolarWinds each import the generated MIB and list every object.
- **SC-004**: 100 percent of the 35 objects the agent serves today keep the same name and the same OID after the change.
- **SC-005**: Across 100 randomized add and remove runs, 0 kept fields change an OID.
- **SC-006**: 0 objects in the generated MIB return "No Such Instance" during a full walk of the agent.
- **SC-007**: A run against the 16.6 MB input finishes in under 30 seconds and uses under 1 GB of memory.
- **SC-008**: The check action detects a removed Mist field and fails the build within one CI run.
- **SC-009**: The module reaches 80 percent test coverage and passes every quality gate.

## Assumptions

- The OpenAPI file stays in the repository and a person updates it by hand or by a separate job. This feature does not download it.
- The agent OID root stays `.1.3.6.1.4.1.11.2147483646`. A change of the root is a separate decision, because it breaks every poller.
- SMIv2 is the target syntax. SMIv1 is out of scope, because Observium and SolarWinds both read SMIv2.
- The gateway catalog stays the source of truth for what the agent answers. This feature reads the catalog, and it does not change the catalog.
- Only GET operations can make readings. A POST search endpoint is out of scope for the first version.
- The default allow list holds the three endpoints the gateway reads today. Growth of the served set is a separate change to the catalog and to the allow list together.
- The Mist enterprise number in the OID root is inherited from the running agent. This feature does not request a new number.
