# Offline Validation Guide: Packet Length Limits

**Issue**: #3337

This guide describes the parent's final implementation validation.
Documentation alignment executes no test or gate.
The parent supplied verified final local results for T001 through T029.
The commands remain references for authorized rebase validation.
The local implementation commit and cross-artifact analysis are complete.
Remote delivery remains blocked.
The normal requirements audit failed before scanning, and the local alternative left one Git-pinned package unaudited.
Run these commands only in the existing issue worktree.
Do not start MistHelper interactively, a capture, a container, or a Mist cloud session.

## Prerequisites

1. Keep branch `jmorrison-juniper-packet-length-validation`.
2. Use the existing isolated Python 3.13.13 environment.
3. Use the current requirements and development tools without changes to dependencies.
4. Read [../plan.md](../plan.md) for the approved file manifest and delivery restrictions.

Commands below assume the repository root.
They use the macOS environment path.
Do not run bootstrap or installation commands.

```bash
rtk proxy .venv/bin/python --version
rtk git --no-pager branch --show-current
```

Expected results are `Python 3.13.13` and the existing issue branch.
If a required tool is unavailable, report the missing capability.
Do not change dependencies, shared configuration, instructions, or baselines to enable a gate.

## 1. Prove the Old Source Fails

Restore `tests/unit/test_packet_capture.py` exactly to base `9148155c95e1f502abb0a09fd69f5a928b3bf22f`.
Append two parameterized functions to existing `tests/unit/capture/test_multi_ap_scan_workflow.py`.
Use `test_packet_length_prompt_limits` and `test_packet_length_prompt_defaults`.
Preserve existing tests apart from necessary imports and the module docstring.
Use the real entry points and case table in [contracts/prompt-limits.md](contracts/prompt-limits.md).
Keep each function within five parameters and 25 lines.
The file increases from three definitions to five without a new directory child.
Substitute only `builtins.input`.
Do not substitute `safe_input`, validator results, or the wireless collector.
Do not add a class, fixture, helper, wrapper, module, or production construct.
Run the red test with both production files unchanged.

```bash
rtk proxy mkdir -p data/issue-3337
rtk proxy env -u MIST_APITOKEN -u MIST_API_TOKEN .venv/bin/python -m pytest \
  tests/unit/capture/test_multi_ap_scan_workflow.py::test_packet_length_prompt_limits \
  tests/unit/capture/test_multi_ap_scan_workflow.py::test_packet_length_prompt_defaults \
  -q --tb=short --junitxml=data/issue-3337/red-pytest.xml
```

Expected result: a nonzero exit caused by the old maximum or its actual messages.
Values 1537 and 2048 must expose the former acceptance error.
Import failures, missing tools, and collection failures do not count as the required red evidence.
Record the source revision and the actual test counts.

## 2. Prove the Six-Literal Correction Passes

Apply only the six production changes in the plan.
Use the existing coverage API for the focused run.
Keep its branch data under `data/issue-3337/`.

```bash
rtk proxy env -u MIST_APITOKEN -u MIST_API_TOKEN COVERAGE_FILE=data/issue-3337/.coverage \
  .venv/bin/python -m coverage run --branch \
  --source=src.operations.execution.capture._packet_capture_prompts,src.foundation.support.refactors.serial_cc.start_site_client_capture_wireless \
  -m pytest \
  tests/unit/capture/test_multi_ap_scan_workflow.py::test_packet_length_prompt_limits \
  tests/unit/capture/test_multi_ap_scan_workflow.py::test_packet_length_prompt_defaults \
  -q --junitxml=data/issue-3337/green-pytest.xml
rtk proxy .venv/bin/python -c '
import coverage, logging  # Use the installed coverage API without another helper file.
logging.basicConfig(level=logging.DEBUG)  # Show coverage actions and their results.
logging.info("Opening measured coverage data %s", "data/issue-3337/.coverage")  # Identify the existing focused-run data.
measurement = coverage.Coverage(data_file="data/issue-3337/.coverage")  # Select the recorded branch data.
logging.debug("Selected coverage data file %s", measurement.config.data_file)  # Confirm the selected file.
logging.info("Loading measured coverage data")  # State the read before it occurs.
measurement.load()  # Require the focused run data rather than a new measurement.
logging.debug("Loaded coverage data file %s", measurement.config.data_file)  # Confirm the completed read.
logging.info("Writing coverage JSON %s", "data/issue-3337/coverage.json")  # Identify the report before writing it.
percentage = measurement.json_report(outfile="data/issue-3337/coverage.json")  # Export the existing data for region checks.
logging.debug("Wrote coverage JSON with aggregate percentage %s", percentage)  # Report the export result without a whole-module gate.
'
```

Expected result: all focused cases pass through real input handling.
Assert the returned values and complete wireless tuples.
Assert the actual prompt arguments, shared printed errors, wireless warnings, and safety notices.
Do not replace return-value assertions with mock call checks.

Report 1473 accepted and 513 required rejected integers for each path.
Report additional cases separately.
Include empty text, whitespace-only text, padded integers, nonnumeric text, EOF, cancellation, and shared default 1300.
Report the pytest item counts and the count for each real path.
The supplied final matrix executed 4010 items, with 2005 per path.
Each path executed 1473 supported integers, 513 required rejected integers, and 19 additional cases.
Each parameterized item executes one prompt path.
The final green run passed all 4010 cases with zero failures, errors, or skips.
The final red run recorded 4010 failures with zero errors or skips on base-identical source.
Shared input 1537 returned `1537`, and wireless input 1537 returned `(120, 7, 1537)`.
Both results violate the required maximum.

Do not apply pytest-cov's whole-module 90% threshold to this focused function run.
This run does not measure all behavior in either module.
Do not set `--cov-fail-under=0` or change coverage configuration.
The repository's global coverage threshold remains unchanged and required in CI.

## 3. Measure Guard Coverage

Measure statements inside the real shared validator and wireless bounded validator.
Also report coverage for the real wireless collector.
Use the current source regions, not whole-module percentages.

```bash
rtk proxy .venv/bin/python -c '
import ast, json, logging  # Measure real source regions without executing a capture.
from pathlib import Path  # Read only the local source and report files.
logging.basicConfig(level=logging.DEBUG)  # Show each measurement action and result.
logging.info("Reading coverage report %s", "data/issue-3337/coverage.json")  # Identify the required input before reading it.
report_text = Path("data/issue-3337/coverage.json").read_text(encoding="utf-8")  # Fail if the actual report is unavailable.
logging.debug("Read coverage report characters %s", len(report_text))  # Confirm the input size without printing its contents.
logging.info("Parsing measured coverage report")  # State the transformation before it occurs.
report = json.loads(report_text)  # Require valid JSON from the focused run.
logging.debug("Parsed measured files %s", len(report["files"]))  # Confirm the measured scope.
logging.info("Selecting actual validation regions")  # State the bounded measurement scope.
regions = (("src/operations/execution/capture/_packet_capture_prompts.py", "prompt_max_packet_length"), ("src/foundation/support/refactors/serial_cc/start_site_client_capture_wireless.py", "_prompt_bounded_int"), ("src/foundation/support/refactors/serial_cc/start_site_client_capture_wireless.py", "_collect_bounded_ints"))  # Select the existing validation regions.
logging.debug("Selected validation regions %s", len(regions))  # Confirm that all three regions remain required.
for filename, method in regions:  # Report each region separately.
    logging.info("Reading current source %s", filename)  # Identify the region owner before reading it.
    source_text = Path(filename).read_text(encoding="utf-8")  # Fail if the actual source is unavailable.
    logging.debug("Read source characters %s", len(source_text))  # Confirm the read without printing source.
    logging.info("Parsing current AST for %s", filename)  # State the transformation before it occurs.
    tree = ast.parse(source_text)  # Locate current regions rather than stale line numbers.
    logging.debug("Parsed AST type %s", type(tree).__name__)  # Confirm a valid source tree.
    logging.info("Locating actual region %s", method)  # Require the named production method.
    node = next(item for item in ast.walk(tree) if isinstance(item, ast.FunctionDef) and item.name == method)  # Require the real method.
    logging.debug("Located region lines %s through %s", node.lineno, node.end_lineno)  # Confirm the current bounds.
    logging.info("Selecting measured source file %s", filename)  # Require coverage for this region owner.
    measured = report["files"][filename]  # Fail if coverage did not measure this source file.
    logging.debug("Selected measurement for %s", filename)  # Confirm the source lookup.
    logging.info("Counting measured statements in %s", method)  # State the regional calculation before it occurs.
    total = {line for line in measured["executed_lines"] + measured["missing_lines"] if node.lineno <= line <= node.end_lineno}  # Count measured statements inside the method.
    logging.debug("Measured region statements %s", len(total))  # Expose an empty region instead of treating it as passed.
    logging.info("Counting executed statements in %s", method)  # State the execution calculation before it occurs.
    executed = total.intersection(measured["executed_lines"])  # Count only executed statements.
    logging.debug("Executed region statements %s", len(executed))  # Confirm the numerator.
    logging.info("Reporting regional coverage for %s", method)  # State the result action before output.
    percentage = 100.0 * len(executed) / len(total) if total else 0.0  # Keep empty measurements below the required threshold.
    print("%s::%s: %s/%s statements (%s%%)" % (filename, method, len(executed), len(total), percentage))  # Show both counts and the percentage.
    logging.debug("Reported region percentage %s", percentage)  # Confirm the result after output.
    if not total or percentage < 80.0:  # Reject empty measurements or insufficient coverage in any region.
        logging.error("Coverage failed for %s::%s", filename, method)  # Identify the failing region.
        raise SystemExit("FAIL: %s" % method)  # Return a nonzero result without an optional assertion.
'
```

Expected result: each reported region meets or exceeds 80%.
An empty region or absent report fails the check.
Keep the raw branch report with the statement counts.
Coverage does not replace boundary and message assertions.
Earlier measurements were shared 11/11, wireless bounded 12/12, and collector 8/8, each at 100%.
The supplied final measurements confirmed those same counts with the two final functions.
Repeat the required measurements after an authorized rebase.

## 4. Run Adjacent Capture Tests

```bash
rtk proxy env -u MIST_APITOKEN -u MIST_API_TOKEN .venv/bin/python -m pytest \
  tests/unit/test_packet_capture.py \
  tests/unit/capture \
  tests/unit/serial_cc/test_start_site_client_capture_wireless.py \
  tests/unit/serial_cc/test_start_site_scan_capture.py \
  tests/integration/test_packet_capture_org_compatibility.py \
  -q --tb=short --junitxml=data/issue-3337/adjacent-pytest.xml
```

Expected result: the existing capture tests pass without network contact.
The wireless test module is a read-only regression target, not an approved edit target.
The large packet-capture test file must match the source base exactly.
Record collected, executed, passed, failed, and skipped counts.
Do not start a capture to prove behavior for a sender with a fixed length.
The completed review remains valid because those files stay unchanged.
The supplied final adjacent run passed 4373 cases with zero failures or skips.

## 5. Run Required Local Gates

```bash
rtk proxy .venv/bin/python -m py_compile MistHelper.py \
  src/operations/execution/capture/_packet_capture_prompts.py \
  src/foundation/support/refactors/serial_cc/start_site_client_capture_wireless.py \
  tests/unit/capture/test_multi_ap_scan_workflow.py
rtk proxy .venv/bin/python -m ruff check .
rtk proxy .venv/bin/python -m black --check --diff .
rtk proxy .venv/bin/python -c '
import logging, shlex, subprocess, sys, yaml  # Use the configured repository type scope without a copied path list.
from pathlib import Path  # Read the existing CI configuration only.
logging.basicConfig(level=logging.DEBUG)  # Show the configured-scope check and its result.
logging.info("Reading CI configuration %s", ".github/workflows/ci.yml")  # Identify the scope owner before reading it.
workflow_text = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")  # Require the existing repository configuration.
logging.debug("Read CI configuration characters %s", len(workflow_text))  # Confirm the read without printing configuration.
logging.info("Parsing CI configuration")  # State the transformation before it occurs.
workflow = yaml.safe_load(workflow_text)  # Keep CI as the scope owner.
logging.debug("Parsed CI configuration")  # Confirm the parse.
logging.info("Resolving configured MYPY_PATHS")  # State the scope transformation before it occurs.
paths = shlex.split(workflow["env"]["MYPY_PATHS"])  # Use every configured type-check path.
logging.debug("Resolved type-check paths %s", len(paths))  # Confirm the configured scope.
logging.info("Running mypy for configured paths %s", len(paths))  # State the required gate before execution.
result = subprocess.run(["rtk", "proxy", sys.executable, "-m", "mypy", *paths, "--config-file", "pyproject.toml"], check=True)  # Fail on the real repository-scope result.
logging.debug("Completed mypy with exit code %s", result.returncode)  # Confirm the actual gate result.
'
rtk proxy .venv/bin/python -m bandit -c pyproject.toml -r . \
  -f json -o data/issue-3337/bandit.json
rtk proxy .venv/bin/python -m pip_audit -r requirements.txt
```

If the normal requirements audit fails before auditing, record the exact error before the local alternative.
Supplied macOS evidence identifies an ensurepip SIGABRT and copy error.
Then audit the installed isolated environment:

```bash
rtk proxy .venv/bin/python -m pip_audit --local --skip-editable
```

Identify this as the local macOS fallback, not a successful requirements-resolution audit.
The supplied final local alternative found no known vulnerabilities in audited installed packages.
It explicitly skipped the Git-pinned `misthelper-devtools` version `0.5.2` because PyPI does not contain it.
That package remains unaudited.
The normal audit of requirements remains a delivery check.
Do not suppress vulnerabilities or install different dependencies.

Run the configured ratchet against the current test tree, including uncommitted test edits:

```bash
rtk proxy .venv/bin/test-quality-analyzer --gate \
  --config .github/test-quality-config.toml \
  --baseline .github/test-quality-baseline.json \
  --report data/issue-3337/test-quality-report.json \
  --summary data/issue-3337/test-quality-summary.md
```

Do not use `--changed-from` before commit to measure uncommitted edits.
Do not use `--write-baseline`, `--prune-baseline`, rule exclusions, or suppressions.
Record the analyzer scope, checked counts, and result.
The rejected large-file manifest produced 23 new line-sensitive `weak_zero_assertions` findings.
That file still contained 24 findings, with zero semantic new findings.
Restore it exactly to the base.
Do not change a baseline, add a suppression, or repair unrelated tests.
The final test file started with zero findings.
The supplied final ratchet checked 944 files and 728 existing findings.
It reported zero new findings, 42 configured skips, and zero parse errors.
Repeat the configured ratchet after the authorized rebase.

The final compile check passed four files.
The full Black check passed 1882 files without changes.
Repository-scope Ruff passed.
The final mypy run passed the exact CI scope across 608 source files.
The configured Bandit run reported zero findings across 206617 lines.
Its JSON report is `data/issue-3337/bandit.json`.
These are supplied verified results, not gate execution by the documentation owner.

## Completion Evidence

The parent's final implementation record must include these results:

- The unchanged source failed the focused behavior tests for the old maximum or its messages.
- The six-literal correction passed the same tests and adjacent capture tests.
- All three actual regions met the coverage threshold with nonzero statement counts.
- Every required local gate passed, or the record identified a bounded blocker.
- One `Fixed` fragment at `changelog.d/issue-3337-packet-length-validation.md` referenced #3337.

Do not create that fragment during documentation alignment.
The parent owns cross-artifact analysis and T030 before any local commit.
The coordinator's verified stable `main` SHA is required before a push or pull request.
It does not block the parent's local commit after verified local work and cross-artifact analysis.
The plan identifies position 9 in the queue, the required stable `main` SHA, and the protected delivery sequence.
