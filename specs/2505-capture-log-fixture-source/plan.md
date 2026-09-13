# Plan: Capture log fixture source

## Approach

Group the fixture sites by their resolved source file.
Use the fixture `source` value when present.
Use the `--source` argument when the fixture omits `source`.

## Implementation

1. Add a small helper that resolves the source file for one fixture site.
2. Add a loader that parses each distinct source file one time.
3. Build one call index for each parsed source file.
4. Reuse the parsed module and call index while the main loop renders fixtures.
5. Keep the existing skip warning for a fixture that does not resolve.
6. Return code 1 when a source file cannot be read or parsed.

## Tests

Add a unit test that runs `main()` with two synthetic source files.
One fixture uses the CLI source.
One fixture uses a `source` override.
Add a unit test for a missing override source file.

## Performance

Measure the capture command before and after the change.
Confirm that the repair does not walk a whole syntax tree for each fixture.
