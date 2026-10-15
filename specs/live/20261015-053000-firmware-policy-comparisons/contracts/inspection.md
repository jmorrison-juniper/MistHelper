# Firmware inspection contract

## Prepared job

`POST /api/firmware-policy/jobs/<identifier>/comparison`

The body contains exactly `scope` and `id`.
The owning browser must select a ready live job row.
The response contains one firmware-only saved/current/proposed comparison.
Unknown and foreign jobs produce the same unavailable response.
No preparation, settings write, backup creation, or proof consumption occurs.

## Historical record

`POST /api/settings-restore/inspect`

The body contains exactly `bundle`, `record`, and `compare`.
`bundle` is an opaque UUID, `record` is a saved scoped UUID, and `compare`
is an explicit Boolean. Ownership and membership checks precede disclosure.
With `compare=false`, no current settings read occurs.
With `compare=true`, one current complete settings read supplies a firmware-only
comparison and an actual UTC observation time.
Bundle bytes and metadata remain unchanged.

## Privacy

Only schema-known firmware fields cross the boundary. Private settings,
arbitrary paths, raw files, server exception content, and unrelated siblings do not.
Source identity is checked after reads. Current failure does not become an empty policy.
