# Tasks: Triage Hypothesis / pytest dev-deps compatibility

Overview: Ordered, actionable tasks to reproduce the issue across a matrix, triage root cause, propose pinned dev-requirements, optionally implement a minimal workaround, and add CI coverage.

1. Prepare reproducible environment (Dev/Machine/CI)
   - Create ephemeral environments (virtualenv or tox) for Python 3.11, 3.12, 3.13 where available
   - Ensure pip and virtualenv are up-to-date
   - Acceptance: For each Python version, a virtualenv can be activated and pip works

2. Define test matrix and automation script
   - Implement a small script (bash/PowerShell) that iterates the matrix of Hypothesis/importlib-metadata/pytest combos
   - For each combo:
     - Create venv
     - pip install --no-cache-dir pytest==<version> hypothesis==<version> importlib-metadata==<version> (where importlib-metadata may be omitted to rely on stdlib)
     - Run `pytest -q` capturing stdout/stderr and exit code into data/<python>-<pytest>-<hypothesis>-<importlib>.log
     - Also run `pytest -q -p no:hypothesis` as control
   - Acceptance: Script runs and produces one log per combo with exit code

3. Execute matrix (prioritise likely combos)
   - Run the script across the targeted Python interpreters
   - Collect logs into `specs/dev-deps-hypothesis-compat/results/`
   - Acceptance: Collected logs for all attempted combos

4. Analyse results and identify failing combinations
   - Produce a matrix table (CSV or markdown) mapping combo -> pass/fail -> error summary
   - Acceptance: A clear list of combinations that reproduce the AttributeError and which do not

5. Propose pinned requirements-dev.txt
   - Based on results, select the minimal set of pins that avoids the crash while staying recent
   - Candidate policy: prefer upgrading Hypothesis to a release that uses importlib.metadata API correctly; otherwise pin importlib-metadata backport to a compatible version; avoid downgrading pytest unless necessary
   - Acceptance: `requirements-dev.txt` installs cleanly and `pytest -q` runs successfully on selected Python versions

6. If pinning insufficient, implement workaround patch
   - Minimal runtime shim: in conftest.py or test bootstrap, monkeypatch hypothesis.entry_points.get usage before Hypothesis imports, or vendor a small compatibility helper
   - Add a regression test proving pytest runs with plugin auto-load
   - Acceptance: Tests pass with the shim and fail on the same combos without the shim

7. Draft CI workflow patch
   - Add a job (e.g., `.github/workflows/dev-deps.yml`) that creates an isolated environment, installs `requirements-dev.txt`, and runs `pytest -q` and `pytest -q -p no:hypothesis` as a control
   - Acceptance: The CI job fails the pipeline if pytest fails to start due to plugin crash

8. Create PR with changes and detailed description
   - Include link to this spec and collected logs
   - Explain recommended pinned versions, why they were chosen, and any temporary workarounds
   - Acceptance: PR has passing CI and reviewer signoff

9. Post-merge follow-up
   - Monitor CI for regressions
   - Open upstream issues/PRs against Hypothesis or upstream packages if a code change is required


## Tasks ordering and estimations
- Task 1-4 (reproduce + analysis): 2-3 hours on CI with parallel runners
- Task 5 (pin proposal): 30-60 minutes
- Task 6 (workaround if needed): 1-2 hours
- Task 7-8 (CI + PR): 1 hour


## Acceptance criteria (high level)
- Reproduction logs attached in the spec directory
- requirements-dev.txt proposal validated on at least Python 3.12 and 3.11
- CI workflow added (or proposed) that fails when plugin crash occurs


---

*End of tasks file.*
