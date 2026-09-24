# Feature Specification: Report refused device insight metrics

## Problem

Menu 76 exports an HTTP error body as a metric row. mistapi 0.64.0 does not raise an exception for an HTTP 400. It returns a response that holds the status and the error body. The operation catches only an exception, so it counts each error body as a retrieved metric. The operator then reads a wrong count and gets no statement about the refused metrics.

## Evidence

The browser sweep of #3238 ran menu 76 for the gateway `Branch-SSR`. The run sent 44 metric requests. Five requests returned HTTP 400, and 39 requests returned HTTP 200. The summary said `! 44 device insight metrics exported`. The export file held five rows with only a `detail` column.

| Metric | Reason in the error body |
| - | - |
| `bgp-ribs-metrics` | `data temporary unavailable` |
| `port-metrics` | `port_id is required` |
| `gateway-metrics` | `metric parameter required and must be one of: rx_bytes, tx_bytes, byte...` |
| `top-flow-by-src` | `top_flows is only supported for switch devices or at site scope` |
| `top-flow-by-dst` | `top_flows is only supported for switch devices or at site scope` |

The issue first named the colon form of the MAC as the cause. The evidence does not support that cause, because 39 requests with the colon form returned HTTP 200.

## User Stories

### Story 1: The export holds only metric data

Given the Mist API refuses a metric, when menu 76 writes the export, then the export holds no row for that metric.

### Story 2: The count is correct

Given the Mist API refuses five of 44 metrics, when the export ends, then the summary states 39 metrics.

### Story 3: The operator sees each refusal

Given the Mist API refuses a metric, when the export ends, then the operator reads the metric name, the HTTP status, and the reason.

## Functional Requirements

- FR-001: A response with an HTTP status of 400 or more must not become an export row.
- FR-002: The retrieved count must include only the metrics that returned data.
- FR-003: After the export, the operation must list each refused metric with its HTTP status and its reason.
- FR-004: The reason must come from the error body. The reason must hold ASCII characters only, and 200 characters or fewer.
- FR-005: Each run must start with an empty refusal record.
- FR-006: If a response holds no integer HTTP status, the operation must keep its current behavior.

## Out of Scope

- The MAC form. The endpoint accepts the colon form.
- Menu 74 (#3266) and menu 75 (#3297). Those repairs can use the new refusal class.
- The extra parameters that some metrics need, such as `port_id`.
