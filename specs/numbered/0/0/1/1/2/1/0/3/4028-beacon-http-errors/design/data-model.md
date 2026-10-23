# Data model

No schema changes are required.

The response has an optional integer `status_code` and a parsed `data` value.
An integer status outside 200 through 299 enters the existing failure path.
A successful response retains the existing mapping-to-row conversion.
Raw mappings and empty payloads retain existing behavior.
The exporter keeps its natural beacon key and endpoint metadata.
