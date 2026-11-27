# Quickstart: Reproduction and verification for issue #3392

Run each command from the repository root. Authenticate `gh` as the repository owner account before each read. Never print a token.

## 1. Read the issue state

Read the issue and its comments. This command only reads.

```text
gh issue view 3392 -R jmorrison-juniper/MistHelper --json number,state,labels,comments
```

Expected: the state is OPEN. The comments include the 2026-10-21 owner comment. The comments hold no lab answer until T010 is complete.

## 2. Reproduce the access point refusal

```text
python -m pytest tests/contract/upgrade_portal/test_org_advanced_options.py
```

Expected: all tests pass. The refused case at line 133 passes. It proves that the save refuses the stable word for a plan with an access point (RC-84, RC-41, RC-42, RC-43).

## 3. Reproduce the builder guard

```text
python -m pytest tests/unit/prod_readiness/operations/execution/firmware/upgraders/upgrades/test_org_advanced_bodies.py
```

Expected: all tests pass. The test at line 158 proves that the access point body builder refuses the stable build (RC-30, RC-31, RC-92).

## 4. Reproduce the router channel controls

```text
python -m pytest tests/unit/upgrade_portal/test_upgrade_ssr_options.py
python -m pytest tests/contract/upgrade_portal/test_upgrade_options.py
python -m pytest tests/e2e/upgrade_portal/test_org_advanced_options.py
```

Expected: all tests pass. The channel values alpha, beta, and stable pass through the reader and the single-site page (RC-49, RC-51, RC-96). The end-to-end test shows no channel control without a router (RC-93).

## 5. Owner lab steps (run by the owner only)

The agent never runs these steps. Each step uses a fixed contract.

1. Choose the lab organization, one lab site, one lab access point, and the lab routers. Decision D-18 applies.
2. Run lab check L-AP-STABLE with the body in `design/contracts/org-access-point-stable-request.md`. Send the call through the SDK function `upgradeOrgDevices`. Read the job with `getOrgDeviceUpgrade`.
3. Run lab checks L-SSR-STABLE, L-SSR-BETA, and L-SSR-ALPHA with the body in `design/contracts/ssr-channel-request.md`. Send each call through `upgradeOrgSsrs`. Read each job with `listOrgSsrUpgrades`.
4. Draft one lab answer for each check with the fields of `design/contracts/lab-answer-record.md`.
5. Post the four answers as comments on issue #3392 (T010).

Caution: a lab device can reboot during its job.
Warning: never send these calls to a production organization.

## 6. Local gates for each changed file

Run each gate that applies to the changed files. Gate rows follow the Local gates table in `.github/copilot-instructions.md`.

```text
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
python -m mypy src/ MistHelper.py wsgi.py scripts/mist_ideas_analyzer_pkg/__init__.py scripts/mist_ideas_distiller_v2_pkg/__init__.py --config-file pyproject.toml
python -m pytest tests/contract/upgrade_portal/test_org_advanced_options.py
python -m pytest tests/unit/prod_readiness/operations/execution/firmware/upgraders/upgrades/test_org_advanced_bodies.py
python -m pytest tests/e2e/upgrade_portal/test_org_advanced_options.py
python -m pytest tests/unit/upgrade_portal/test_upgrade_ssr_options.py
python -m pytest tests/contract/upgrade_portal/test_upgrade_options.py
python -m pytest tests/e2e/upgrade_portal/journeys/test_parity_pages.py
python -m pytest tests/guardrails
radon cc src/operations/execution/firmware -j | complexity-gate --max 10
radon cc src/interfaces/portals/upgrade_portal -j | complexity-gate --max 10
bandit -c pyproject.toml -r src/operations/execution/firmware -q
bandit -c pyproject.toml -r src/interfaces/portals/upgrade_portal -q
pylint src/ --fail-under=9.5
vulture src/ MistHelper.py wsgi.py web_portal --min-confidence 70
pydocstyle src/ wsgi.py web_portal
interrogate src/ MistHelper.py wsgi.py wsgi_capture.py web_portal --fail-under 90
symbol-diff --base origin/main <each changed Python file>
ste-linter --config .ste-linter.toml --min-score 80 <each changed Markdown file>
```

Gate rules for this issue:

- The dependency audit row (`pip-audit -r requirements.txt`) applies only when `requirements.txt` changes. This issue does not change it (RC-25).
- The menu reference rows apply only when a menu changes. This issue adds no menu.
- The ops portal and ops platform rows apply only when `ops-portal/` or `mist-ops-platform/` changes. This issue changes neither.
- The test quality ratchet follows the procedure in `.github/copilot-instructions.md`. The configuration files are not read in this record (Unverified item 4).

Expected: each applicable gate prints its expected result from the table.

## 7. Evidence audit (TST-13)

Read the posted answers, then check each one against the checklist `design/checklists/lab-evidence.md`.

```text
gh issue view 3392 -R jmorrison-juniper/MistHelper --json comments --jq ".comments[].body"
```

Expected: four answers exist, one for each check ID. Each answer holds only the fixed fields. The audit finds no identifier, no token, and no response body. Any finding stops the branch decision until the owner corrects the comment.

## 8. Citation audit (TST-14)

Recheck the remote table in `design/research.md`. Each command reads main or the installed package.

```text
gh api "repos/jmorrison-juniper/MistHelper/git/trees/main?recursive=1" --jq ".tree[] | select(.path == \"AGENTS.md\") | .sha"
gh api "repos/jmorrison-juniper/MistHelper/contents/AGENTS.md?ref=main" --jq .sha
```

Expected: both commands return 44a9afffb5bd6f774973a845d27343e4e528b6ad.

Count the rows of the remote table:

```text
(Select-String -LiteralPath design\research.md -Pattern "^\| RC-").Count
```

Expected: 120. The count must match the `remote_checks` array in STATUS.json and the summary.

Check the installed SDK file hash:

```text
(Get-FileHash -LiteralPath .venv\Lib\site-packages\mistapi\api\v1\orgs\ssr.py -Algorithm SHA256).Hash
```

Expected: 312EEADA911529F97998F239FEEF84A24CEAC4877E3F6D5502630DE45694A12B (letter case does not matter), which matches RC-115.
