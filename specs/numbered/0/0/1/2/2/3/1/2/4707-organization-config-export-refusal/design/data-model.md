# Data Model: Organization Config Export Refusal

Each entity lists its fields and constraints. A task cites a field as `Entity.field`. The bundle uses the natural keys from Mist, not artificial identifiers.

## ConfigurationType

One of the six configuration types that the export reads. The list is fixed in `OrgConfigMigrationManager.CONFIG_TYPES`.

| Field | Type | Constraint |
| --- | --- | --- |
| `ConfigurationType.key` | text | Required. One of `networks`, `services`, `vpns`, `gateway_templates`, `device_profiles`, or `service_policies`. Unique in the list. |
| `ConfigurationType.display_name` | text | Required. Used in logs and in the stop message. |
| `ConfigurationType.list_fn` | text | Required. Dotted path to a mistapi list function. |
| `ConfigurationType.list_kwargs` | mapping | Optional. Only `device_profiles` sets it, to `type` equal to `gateway`. |
| `ConfigurationType.import_order` | integer | Required. Dependency order for import. |

## ConfigFetchOutcome

The result of one fetch of one configuration type. It exists only in memory.

| Field | Type | Constraint |
| --- | --- | --- |
| `ConfigFetchOutcome.key` | text | Required. Must equal one `ConfigurationType.key`. |
| `ConfigFetchOutcome.verified` | boolean | Required. `True` only when every response passed the checks. |
| `ConfigFetchOutcome.items` | list of objects | Required. Holds every object when verified. Holds no object when not verified. |
| `ConfigFetchOutcome.failure_category` | enum or empty | One of `refused`, `unavailable`, `invalid`, or `exception`. Empty when verified. |
| `ConfigFetchOutcome.http_status` | integer or empty | The status of the failing response. Empty when verified, when no status exists, or for an exception. |

Rules:

- A verified outcome holds an empty `failure_category` and an empty `http_status`.
- A `refused` outcome holds an integer `http_status` outside 200 through 299.
- An `invalid` outcome holds an integer `http_status` from 200 through 299.
- An `unavailable` or `exception` outcome holds an empty `http_status`.

## BundleMetadata

The `metadata` section of a bundle file.

| Field | Type | Constraint |
| --- | --- | --- |
| `BundleMetadata.source_org_id` | text | Required. The organization identifier that the export read. |
| `BundleMetadata.source_org_name` | text | Required. The verified organization name, or `Unknown`. |
| `BundleMetadata.export_timestamp` | text | Required. UTC time in ISO 8601 form. |
| `BundleMetadata.schema_version` | text | Required. Exactly `1.1` for a bundle that this change writes. |
| `BundleMetadata.object_counts` | mapping | Required. Holds one non-negative integer for each of the six keys. |
| `BundleMetadata.fetch_status` | mapping | Required. Holds the value `verified` for each of the six keys. |

Natural key: `BundleMetadata.source_org_id` with `BundleMetadata.export_timestamp`.

## DestinationInventory

The in-memory cache of destination objects for conflict checks. It is held by the manager during one import.

| Field | Type | Constraint |
| --- | --- | --- |
| `DestinationInventory.items` | mapping | Holds one list for each of the six keys, when every key is verified. Holds nothing otherwise. |

## State transitions

Fetch of one configuration type:

1. Requested. The reader calls the list function.
2. Verified. Every response passed. The outcome holds all objects.
3. Not verified. A response failed a check. The category and the status are recorded.

Export:

1. Requested. The export fetches six types.
2. Saved. Every outcome is verified. The bundle file is written with schema 1.1 and the fetch status map.
3. Stopped. One or more outcomes are not verified. No file is written.

Import:

1. Loaded. The bundle file is read.
2. Rejected. The schema is not 1.1, or a fetch status is not verified. The import stops before the preview.
3. Accepted. The preview and the prompts run.
4. Destination cached. Every destination outcome is verified. The conflict checks run.
5. Destination stopped. One destination outcome is not verified. No create call occurs.
