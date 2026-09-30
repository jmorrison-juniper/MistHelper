# Validation Guide: Maps Title Contrast

## Environment

Use the worktree's Python 3.13 environment.
Install requirements only after the selected command reports a missing dependency.
The tests use a simulated cloud and a local test server.
They need no Mist credentials, containers, or production stores.

## Browser Journey

```bash
rtk proxy .venv/bin/python -m pytest tests/e2e/test_map_title_contrast.py tests/e2e/test_map_viewer_image.py tests/e2e/test_brand_theme_contrast.py -q --browser chromium --output test-results/issue3365 --tracing retain-on-failure --screenshot only-on-failure
```

The title checks measure actual colors in the browser.
They cover both theme-change directions and preserve the floor plan view.
The original dark gray title must fail the dark-theme measurement.

## Offline Checks

```bash
rtk proxy .venv/bin/python -m pytest tests/unit/web_portal/test_map_title_theme.py tests/unit/web_portal/test_map_image_route.py tests/unit/web_portal/test_map_viewer_xss.py tests/unit/web_portal/test_brand_theme_default.py -q
```

The guard checks reject the original insufficient contrast and missing measurement inputs.
The related route and template checks preserve existing map behavior.

## Quality Checks

```bash
rtk proxy .venv/bin/python -m py_compile MistHelper.py tests/e2e/test_map_title_contrast.py tests/unit/web_portal/test_map_title_theme.py
rtk proxy .venv/bin/python -m ruff check .
rtk proxy .venv/bin/python -m black --check MistHelper.py tests/e2e/test_map_title_contrast.py tests/unit/web_portal/test_map_title_theme.py
rtk proxy .venv/bin/python -m mypy $MYPY_PATHS --config-file pyproject.toml
rtk proxy .venv/bin/test-quality-analyzer --gate --roots tests/e2e/test_map_title_contrast.py tests/unit/web_portal/test_map_title_theme.py --config .github/test-quality-config.toml --baseline .github/test-quality-baseline.json
```

Read the current `MYPY_PATHS` in `.github/workflows/ci.yml` before execution.
Use the repository analyzer settings and baseline.
Do not change either file to admit a new finding.

## Local Results

The browser batch passed 51 checks.
The offline batch passed 84 checks.
The original dark title failed at 1.290847:1.
The repaired dark title measured 8.693491:1.
The repaired light title measured 15.426285:1.
The ratchet checked both regression files and found no new finding or parse error.

The Python type check passed for 608 source files.
Ruff, Black, Python syntax, JavaScript syntax, and Bandit passed.
The runtime dependency audit found no known vulnerability.
The audit used UV-resolved requirements because the standard macOS resolver could not load its copied Python library.

## Merged Revision

After the squash merge, fetch the merge SHA.
Run the browser and offline commands on that exact tree inside this session's checkout.
Do not push another commit to the merged branch.
