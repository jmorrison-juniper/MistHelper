# Lock comparison for slice S2

This record compares `uv.lock` with the baseline freeze for issue #3400.

## Method

1. Install `requirements.txt` and `requirements-dev.txt` into a clean Python 3.13 environment. Save the sorted `pip freeze` as `test-artifacts/dependency-freeze-before.txt`. It holds 161 pinned packages.
2. Run `uv lock --exclude-newer 2026-10-20T05:03:53Z`. The date is the time of the freeze, so the lock cannot select a newer release. The lock stores the date in its `[options]` table.
3. Run `uv export --frozen --all-extras --no-hashes` and compare each version with the freeze.

## Result

- The lock holds 197 packages. The freeze holds 161.
- Each of the 161 frozen packages appears in the lock at the same version. No package is upgraded or downgraded, so blocker B-003 does not apply.
- Each of the 34 additional exported packages has a written reason:

| Packages | Reason |
| - | - |
| pre-commit, cfgv, identify, nodeenv, virtualenv, distlib, python-discovery | The `dev` extra declares `pre-commit`. No requirements file lists it. |
| uvicorn, httpx, httpcore | The `container` extra declares `uvicorn`. `httpx` and `httpcore` come from the spaCy chain and from `openai`. |
| spacy, spacy-legacy, spacy-loggers, thinc, blis, srsly, preshed, cymem, murmurhash, wasabi, weasel, confection, catalogue, cloudpathlib, smart-open, wrapt, typer, shellingham, annotated-doc | The `ste-linter` extra declares `spacy`. These packages are its dependencies. |
| waitress | The runtime list declares it under a Windows marker. The macOS freeze omits it. |
| jeepney, secretstorage, pywin32-ctypes | Keyring needs them on Linux and on Windows. The macOS freeze omits them. |
| httpx2-jsfetch | A marker-only dependency of `httpx2`, which `openai` requires. |

## Stored command

Run `uv lock` with `--exclude-newer` only to create the first lock. The guard `tests/guardrails/test_dependency_lock_file.py` reads the date from the lock and passes it to `uv lock --check`.
