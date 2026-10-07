# Partial failure verdict for insight exports

## Problem

Menus 74 and 76 can write valid rows after other metric requests return HTTP errors.
The portal sees the file and reports `Operation completed`.

## Decision

Keep valid rows in the partial file. Mark the operation as failed when any metric request
returns HTTP 400 or another non-success HTTP status.

## Contract

Each refused request emits this exact operator line:

`! Error fetching <operation>: HTTP <status> from <url>`

Menu 74 uses `getSiteInsightMetrics` and the site insight request path.
Menu 76 uses `getSiteInsightMetricsForDevice` and the device insight request path.

The wording uses the `error fetching` marker from issue #3168.
The portal then reports a failed run instead of a successful partial result.
