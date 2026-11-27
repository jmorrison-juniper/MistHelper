# Data Model: Mist API Contract Evidence for the Cisco Converter

This file defines the entities of the record, their natural keys, and their state transitions. The record holds no runtime data. The entities describe the contract rows, the fixtures, and the checks.

## Terms

- **Write operation**: A Mist operation with verb POST, PUT, or DELETE.
- **Read operation**: A Mist operation with verb GET.
- **Contract row**: One table row for one operation. Write rows use IDs W-01 to W-22. Read rows use IDs R-01 to R-18.
- **Identity status**: The result of the check for operation ID, verb, path, SDK function, and SDK signature.
- **Field status**: The result of the check for request body fields and schema constraints.
- **Behavior status**: The result of the check for declared responses, SDK retry, timeout, and logging.
- **Verified field**: A body field with schema evidence and a passing synthetic fixture.
- **Synthetic fixture**: A test body written from the schema. It holds no customer or production data.
- **Allowlist**: The set of top-level field names that a request body may hold. The tests derive it from the schema properties.
- **Unverified item**: A claim with no local or remote evidence. The research file lists each one with a reason.
- **Remote check**: One comparison of a repository path or commit with GitHub `main`.
- **Family**: An apply family in record 4644 (F-01 to F-08).
- **Gate**: A gate of the parity plan (G1 to G5).
- **Disabled**: The default state of each write operation in this change.
- **Excluded**: A write operation outside the converter scope. Decision D-4 excludes one operation.
- **Indeterminate**: A write outcome that the executor cannot prove. Record 4644 defines this term.

## Entities

### WriteOperation

Natural key: `operation_id` plus `verb` plus `path`. The `contract_id` column holds W-01 to W-22.

| Attribute | Meaning |
| --- | --- |
| `contract_id` | W-01 to W-22 |
| `operation_id` | Exact OpenAPI operation ID |
| `verb` | POST, PUT, or DELETE |
| `path` | Exact OpenAPI path |
| `openapi_location` | Object path in the JSON file |
| `yaml_line` | Line of the `operationId` key in the YAML file |
| `sdk_function` | Exact mistapi function name |
| `sdk_location` | Module path and function line |
| `sdk_call_line` | Line of the session call in the function body |
| `request_schema` | Bundled schema name, or none |
| `success_schema` | Bundled response schema name, or none |
| `family` | Record 4644 family ID, or none |
| `scope` | In scope or excluded |
| `identity_status` | verified-present or absent |
| `field_status` | partial, or verified-present for verified fields |
| `behavior_status` | partial |
| `enablement` | disabled (the only value in this change) |

Transitions: `identity_status` moves from open to verified-present or to absent. `field_status` moves from partial to verified-present only after its fixtures pass. `enablement` never changes in this change.

### ReadOperation

Natural key: `operation_id` plus `path`. The `contract_id` column holds R-01 to R-18.

| Attribute | Meaning |
| --- | --- |
| `contract_id` | R-01 to R-18 |
| `operation_id` | Exact OpenAPI operation ID |
| `path` | Exact OpenAPI path |
| `sdk_function` | Exact mistapi function name |
| `sdk_location` | Module path and function line |
| `role` | reference, read-back, or candidate |
| `used_by` | Write operations that use the read |
| `identity_status` | verified-present or absent |
| `behavior_status` | partial |

### FieldEvidence

Natural key: `operation_id` plus `field_name`.

| Attribute | Meaning |
| --- | --- |
| `schema_pointer` | Object path of the field in the bundled schema |
| `json_type` | Declared type, enum, or reference |
| `required` | yes or no |
| `constraints` | Format, minimum, maximum, minItems, or uniqueItems |
| `semantic_note` | Meaning from the schema description, or none |
| `verified` | yes after a passing fixture, otherwise no |
| `fixture_ids` | Synthetic fixtures that cover the field |

Transitions: `unverified` moves to `schema-verified` when the schema location matches. It moves to `verified` when a fixture passes.

### SyntheticFixture

Natural key: `fixture_id`.

| Attribute | Meaning |
| --- | --- |
| `fixture_id` | Short name, such as GT-POS-01 |
| `operation_id` | Write operation that the fixture covers |
| `expectation` | accept or reject |
| `mechanism` | schema, allowlist, or SDK |
| `test_name` | Test function that uses the fixture |
| `status` | planned, passing, or failing |

Transitions: `planned` moves to `passing` or `failing` after a test run.

### SdkBehavior

Natural key: `sdk_file` plus `symbol` plus `line`.

| Attribute | Meaning |
| --- | --- |
| `behavior` | Retry count, wait formula, timeout presence, or logging |
| `value` | Observed value |
| `test_name` | Test function that pins the value |

### RemoteCheck

Natural key: `path` plus `ref`.

| Attribute | Meaning |
| --- | --- |
| `claim` | Statement that the check tests |
| `blob_sha` | Blob or tree SHA on main, or not-a-blob for local paths |
| `result` | present, absent, partial, or stale |
| `line` | Line number, or 0 for presence or count checks |

### UnverifiedItem

Natural key: `unverified_id` (U-01 to U-18).

| Attribute | Meaning |
| --- | --- |
| `reason` | Why the claim lacks evidence |
| `blocks` | Operation IDs or families that the item blocks |

### Decision

Natural key: `decision_id` (D-1 to D-18).

| Attribute | Meaning |
| --- | --- |
| `alternatives` | Two or more options |
| `chosen` | Recommended option |
| `human_decision_required` | true for D-4 and D-8, otherwise false |

## Relationships

- A write operation has one or more field evidence rows. A write operation with no body has none.
- A write operation has zero or more synthetic fixtures.
- A read operation supports zero or more write operations through `used_by`.
- A write operation belongs to zero or one family.
- A write operation blocks on zero or more unverified items.
- A decision can reference zero or more contract rows and zero or more unverified items.

Each relationship above uses the natural keys of the entities. The record defines no other relationship.
