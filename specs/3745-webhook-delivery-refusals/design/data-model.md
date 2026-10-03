# Data model: Webhook response decisions

This repair changes no stored data or key strategy.

## Response page

A response page contains a reliable HTTP status, a readable body, a record array, and an optional next link.
The collector accepts successful HTTP status values before it reads the body.
It accepts list and `results` arrays without changing row values.
It rejects unsupported record shapes and unusable page links.

## Response refusal

A passive refusal exception contains a safe reason only.
It performs no I/O, JSON parsing, or SDK operation.
The exporter adds resource, organization, webhook, page, and measured-page context.
Unexpected exceptions contribute their type, not their raw text or body.

## Collection state

The collector holds accepted rows and visited page links in memory.
A refusal discards the collection before persistence.
A successful final page permits the existing persistence operation.
A successful empty collection permits the existing empty-data notice.
