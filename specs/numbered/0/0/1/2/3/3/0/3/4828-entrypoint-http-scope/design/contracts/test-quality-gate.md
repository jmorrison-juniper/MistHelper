# Contract: Test quality gate

## Command

Pull request runs use the changed-file scope. The command reads the changed test files and the two full-gate paths (`.github/workflows/ci.yml` and `requirements-dev.txt`). The live command is in `.github/workflows/ci.yml` lines 629 to 632 (RC-23).

```text
test-quality-analyzer --gate --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json --changed-from origin/main --full-gate-path .github/workflows/ci.yml --full-gate-path requirements-dev.txt
```

Push runs and manual runs omit the changed-file options and scan the full suite (RC-23).

## Inputs

The procedure reads four inputs. The preflight guard checks each one (RC-46, lines 18 to 21).

1. `.github/copilot-instructions.md`: the guide that states the procedure (RC-47).
2. `.github/workflows/ci.yml`: the live command that the guide must match.
3. `.github/test-quality-config.toml`: the rule settings. All rules that this change touches stay enabled (RC-21, RC-22).
4. `.github/test-quality-baseline.json`: the comparator of accepted findings.

## Output lines

- `gate_scope: <files> files checked, <findings> findings checked`. The line states the scope of the run (RC-23).
- `gate: <K> new findings vs baseline`. `K` must be zero before a push (RC-47).

## Exit codes

- Zero new findings: the gate exits successfully.
- One or more new findings: the gate exits with code 1. The issue body records this result for the help file.

## Baseline commands

- `--write-baseline` replaces the baseline with the current findings (RC-39, line 311). Run it on the full suite only.
- `--prune-baseline` drops stale entries for files that the scan does not reach (RC-38, line 352, and RC-37, line 160). It does not drop an entry for a file that the scan reaches.
- Do not add `--roots` to a baseline command. The command then deletes most of the baseline (RC-40, lines 41 to 42).

## Not in this contract

- The analyzer rules and the HTTP risk inference. Those belong to misthelper-devtools at the pinned commit (RC-32 to RC-36).
