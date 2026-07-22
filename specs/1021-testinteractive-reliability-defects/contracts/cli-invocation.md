# Contract: CLI Invocation and Safety

## Supported interactive-test flag

| Invocation | Exit behavior | Required operator result |
|---|---|---|
| `MistHelper.py --testinteractive` | Normal interactive-test dispatch | Runs the supported harness after ordinary setup. |
| `MistHelper.py --test-interactive` | Non-zero | Clearly states that the spelling is unsupported and suggests `--testinteractive`; it must not fall through to the normal menu. |

`--test-interactive` is intentionally not an alias. This preserves the spelling
for a possible future flag with unrelated semantics.

## Help

| Invocation | Exit behavior | Side-effect contract |
|---|---|---|
| `MistHelper.py --help` | Zero after usage output | Must not call deferred import initialization, dependency initialization, Mist session establishment, or interactive dispatch. |
| `MistHelper.py -h` | Zero after usage output | Same as `--help`. |
| `MistHelper.py --testinteractive --help` | Zero after usage output | Help wins regardless of order; same no-side-effect guarantee. |

## Site selection

When `MIST_INTERACTIVE_TEST_SITE` is non-empty, it must match exactly a site
id or a full site name (case-insensitive comparison may be retained). A
partial name is not a match. An unmatched supplied selector is a terminal,
prominently reported error before any operation runs. The normal path for an
unset selector is not changed by this contract.

## Remote and local safety

- Automated tests use mocked/stubbed Mist clients and no mutation.
- An optional smoke test may issue only documented read-only calls and requires
  an explicitly supplied, authorized read-only credential and exact selector.
- Logs and telemetry remain local under controlled `data/` locations; command
  output and telemetry must not reveal credentials.
