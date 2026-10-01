# Contract: Direct Guidance Guardrail

**Specification**: [spec.md](../../spec.md)

**Command contract**: [local-commands.md](local-commands.md)

This contract defines an internal pytest check and its measured report.
It does not define a new command-line application or network API.

## Direct Invocation

After implementation, run:

```powershell
rtk proxy python -B -m pytest -p no:cacheprovider -s -q tests/guardrails/local_test_quality_loop/test_guidance.py::TestLiveGuides
```

`TestLiveGuides` calls the class-based guard directly.
It does not delegate through a wrapper function.
Use the existing pytest import and PyYAML patterns.
Place test-support classes inside the five-file package.

## Required Reads

| Input | Validation |
|-------|------------|
| `.github/copilot-instructions.md` | Required active procedure in its exact section |
| `agents.md` | Required active procedure in its exact section |
| `.github/instructions/git-flow-multi-agent.instructions.md` | Required active procedure under Part 3 |
| `.github/workflows/ci.yml` | Named job, unique named step, supported run script, and event scope |
| `.github/test-quality-config.toml` | Successful UTF-8 read and TOML parsing |
| `.github/test-quality-baseline.json` | Successful UTF-8 read and usable JSON baseline identities |

Read each input once and retain its text only for that invocation.
Never use a cached CI command or path list.
Attempt independent reads even when another input fails.
Do not execute a document, workflow script, or shell expression.

Unreadable means that the required file read cannot complete.
Missing files, directory inputs, permission errors, and invalid text encoding must produce named failures.
Malformed settings, baseline, or workflow content also fails.

Readable empty TOML uses the analyzer's documented defaults.
Do not add a new analyzer rule or change `ConfigLoader`.
The existing ratchet tests retain their separate repository settings checks.
A missing settings file still fails this guard's direct read.

Accept an empty baseline list in isolated fixture cases.
Validate identity fields in any supplied baseline records.
Do not require the fixture to copy the repository's 728 accepted findings.

## Live CI Decoding

1. Parse YAML with `yaml.safe_load`.
2. Locate job `test_quality_gate`.
3. Require exactly one step named `Run test quality ratchet`.
4. Read that step's `run` script and environment bindings.
5. Decode its empty scope and pull-request-only scope assignment.
6. Decode its one analyzer invocation and scope-array insertion.

The supported current script has `scope=()` outside the pull-request condition.
The condition populates `scope` only for `pull_request`.
The analyzer receives the expanded array at `"${scope[@]}"`.
Push and manual runs therefore retain no changed-scope controls.

Read `BASE_REF` from the live step's base binding.
Require the intended `origin/` comparison and matching local expansion.
Do not read an old command from a comment or another step.

Derive explicit paths from repeated live `--full-gate-path` controls.
Derive automatic paths from the live settings and baseline arguments.
Validate the required repository settings and baseline paths.
A future extra live trigger changes the comparison automatically.

If the script cannot be interpreted within this grammar, fail with its named source.
Do not guess a successful command or evaluate shell conditions.

## Guide Parsing

Locate headings outside code fences, HTML comments, and quoted examples.
Use the exact heading chains in the command contract.
Stop at the next heading with the same or a higher level.

Read only fences introduced by the four active labels.
Require one supported executable fence for each label.
Require one analyzer invocation in each analyzer fence.
Reject commands inside dormant functions, comment-only examples, or unsupported control structures.

The active base fence binds the intended variable, fetches its matching remote reference, and verifies a commit.
The active preflight fence invokes the direct live-guide class.
The scoped and full-suite fences provide their respective analyzer controls.
Correct text elsewhere does not repair an incorrect active fence.

## Semantic Normalization

Allow these equivalent forms:

- Plain `test-quality-analyzer` or the token-preserving `rtk proxy` prefix.
- Different option order.
- Harmless single or double quotes around static path values.
- Separate option values or supported `--option=value` forms.
- A leading `./` on repository-relative static paths.
- Bash backslash continuation or PowerShell terminal backtick continuation.
- `$BASE_REF` or `${BASE_REF}` where the selected shell expands either form.

Recommend `rtk proxy` in the guides because it preserves complete evidence output.
Other RTK wrappers remain unsupported without actual semantic verification.
Normalization must not erase expansion meaning.
Single-quoted base variables fail.
Command strings passed to `echo`, comments, and quoted whole scripts are not executable analyzer invocations.
Preserve literal HTML markers and quote operators inside code fences.
Remove Markdown comments and quoted procedures only outside those fences.
Recognize both HTML comment terminators, `-->` and `--!>`.
Accept `-->` as the supported Markdown terminator.
If an outside-fence comment uses `--!>`, reject the input with a named error.
That HTML form does not restore CommonMark headings.
If a comment remains unclosed, keep its remaining text inactive.
Preserve both literal forms inside executable fences.
Remove shell comments only at a real unquoted token boundary.
Reject quote concatenation, doubled quotes, and unsupported escape grammar.
Do not guess PowerShell semantics from Bash concatenation.
Validate the base assignment before tokenization removes its quotes.
This procedure requires a quoted PowerShell branch value and the `$BASE_REF` variable.
Bash and `sh` require `BASE_REF=value` without spaces around `=`.
An assignment from another shell must fail, even when its normalized tokens look correct.

Reject these forms:

- An omitted required control or an empty required value.
- A different executable or obsolete module entry point.
- Conflicting repeated settings, baseline, or base values.
- Duplicate explicit path values or additional paths absent from live CI.
- An incorrect intended-base expression or mismatched fetch destination.
- `--roots`, `--disable-rule`, or `--include-mist-api`.
- `--write-baseline` or `--prune-baseline`.
- Unknown controls, pipelines, command substitution, or hidden analyzer invocations.
- Changed-scope controls on the full-suite command.

Identical repeated singleton values can normalize to one value.
Conflicting singleton values must fail even when the final value matches CI.
Do not accept shell last-value behavior as contract compliance.

## Measured Reports

Print one ASCII summary on both pass and failure.
Also print each named error on failure.
Derive every count from the invocation's completed operations.

The current successful shape is:

```text
local_test_quality_guard: status=pass inputs_attempted=6 input_reads=6 input_validations=6 guide_reads=3 guide_checks=3 explicit_paths=2 automatic_paths=2 effective_paths=4
```

These numbers describe current successful observations.
Do not store them as constant output values.
The runtime ledger supplies input and guide counts.
The decoded live contract supplies distinct path counts.

| Count | Meaning |
|-------|---------|
| `inputs_attempted` | Required read operations that began |
| `input_reads` | Successful complete UTF-8 reads |
| `input_validations` | Required inputs with successful complete validation |
| `guide_reads` | Guide documents in successful reads |
| `guide_checks` | Guides with a completed pass or failure decision |
| `explicit_paths` | Distinct additional controls successfully decoded from live CI |
| `automatic_paths` | Settings and baseline path controls successfully decoded from live CI |
| `effective_paths` | Union of decoded explicit and automatic controls |

Path counts do not measure file readability.
A missing settings file can leave decoded path counts intact while the input read count falls.
If CI cannot supply a contract, report zero decoded path controls.
Do not claim that guide comparisons ran without a live contract.

Use a named failure shape such as:

```text
local_test_quality_guard: error input=.github/test-quality-config.toml reason=read_failed
```

The detailed error includes the exception type and safe context.
Do not print credentials or file contents.
A failed read never increments `input_reads`.
A parse or comparison failure never increments that input's successful validation count.

## Logging and Comments

Use `logging.info()` before meaningful reads, parsing, comparisons, and fixture subprocesses.
Use `logging.debug()` afterward with measured counts and results.
Use error logging with exception context for read or parse failures.
Use ASCII messages and `%s` formatting.

Give executable Python lines short purpose comments under the constitution.
Keep comments specific to safety, expansion, source authority, and measurement.
Keep methods within 25 lines and five parameters.
Keep helper responsibilities inside named classes.

## Required Negative Proof

Mutate each of the three guides and each required control separately.
Mutate each required input to missing or unreadable form.
Use malformed content variants for CI, settings, and baseline.
Add a live CI trigger while leaving guides unchanged.
Confirm a named failure and measured partial counts.

Accept supported normalization variants as positive cases.
Reject a valid-looking inactive example when the active command is wrong.
Do not fabricate analyzer evidence inside guard tests.
Real installed analyzer evidence belongs to the scope tests.

## Local Validation Status

The live preflight passed after the three authorized guide edits.
It measured six reads, six validations, three guide decisions, and four effective paths.
The complete guidance module passed 397 cases without skips.
The fixture-only run passed 396 cases with only the live class excluded.
That exclusion does not remove mutation cases whose old text names `TestLiveGuides`.

PowerShell is unavailable, so no native PowerShell command ran.
The guard tests prove the supported bounded grammar, not native shell execution.
Missing, directory, invalid UTF-8, malformed, and unusable inputs all have direct failing-decision coverage.
Settings use unchanged installed pure table validators after one required file read.
No settings file is read again through `ConfigLoader.load`.
