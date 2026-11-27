# Contract: Mist token resolution at the command line

## Inputs

- `MIST_API_TOKEN`: the canonical environment variable. Its value splits on commas and newlines.
- `MIST_APITOKEN`: the legacy environment variable. Its value splits the same way.
- A terminal prompt. It runs only when both standard streams are terminals.

## Output

One selected token list for the process, or a refusal with status 1.

## Rules

1. If neither value is usable and both streams are terminals, show one hidden prompt. The entered value becomes the token list.
2. If neither value is usable and a stream is not a terminal, refuse. Do not prompt.
3. If both values are usable and equal, accept the canonical list. Migration allows this case.
4. If both values are usable and different, refuse before organization lookup or session construction.
5. If the prompt reads end of file or receives an interrupt, refuse. Do not log the input.
6. Keep a prompted value in process memory only. Do not write it to a file, the environment, or a log line.

## Messages

Each message names variables only. A message never includes any part of a value.

- Missing token: `no API token found - set MIST_APITOKEN or MIST_API_TOKEN` (existing text, `MistHelper.py` line 2899).
- Conflict: `MIST_APITOKEN and MIST_API_TOKEN have conflicting values - unset one or set both to the same value` (existing text, `MistHelper.py` line 2881).

## Exit status

A refusal exits with status 1.
