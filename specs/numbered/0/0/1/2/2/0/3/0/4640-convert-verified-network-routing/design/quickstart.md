# Quickstart: Convert Verified Network and Routing Settings

## Prerequisites

Run the implementation only in a new worktree for the branch `feat/4640-convert-verified-network-routing`. Start only after the sequencing steps in `plan.md` finish. Set the GitHub account variables before each `gh` command. Do not print the token value.

```text
$env:GH_HOST = 'github.com'
$env:GH_TOKEN = $env:COPILOT_GH_ACCOUNT_github_2E_com_jmorrison_2D_juniper
```

Create the environment in the new worktree with these commands.

```text
uv python install 3.15.2
uv run --no-project --python 3.15.2 python scripts/bootstrap_worktree.py
.venv\Scripts\Activate.ps1
```

## Reproduction Of The Current Gap

1. Run the DNS tests on `main`. Each command must pass.

```text
python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py
python -m pytest tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py
```

2. Run the new conversion tests after task T004 and before task T010. Each test must fail. The failure shows a missing module or a missing unresolved item.

```text
python -m pytest tests/integration/web_portal/cisco_config_converter/conversion
```

3. Confirm the gap in the current DNS converter. Interface, DHCP, route, BGP, and NTP lines appear only as unsupported items. The file `conversion.py` line 26 holds the first known-gap sentence that task T008 revises.

## Verification After Implementation

Compile each changed Python file.

```text
python -m py_compile src/interfaces/portals/cisco_config_converter/conversion/common/dns.py
python -m py_compile src/interfaces/portals/cisco_config_converter/conversion/common/fragment.py
python -m py_compile src/interfaces/portals/cisco_config_converter/conversion/common/syntax.py
python -m py_compile src/interfaces/portals/cisco_config_converter/conversion/network/__init__.py
python -m py_compile src/interfaces/portals/cisco_config_converter/conversion/network/interfaces.py
python -m py_compile src/interfaces/portals/cisco_config_converter/conversion/network/dhcp.py
python -m py_compile src/interfaces/portals/cisco_config_converter/conversion/network/routing.py
python -m py_compile src/interfaces/portals/cisco_config_converter/conversion/network/ntp.py
python -m py_compile src/interfaces/portals/cisco_config_converter/state/proposal.py
```

Run the four new test modules. Each run must pass.

```text
python -m pytest tests/integration/web_portal/cisco_config_converter/conversion/test_network.py
python -m pytest tests/integration/web_portal/cisco_config_converter/conversion/test_services.py
python -m pytest tests/integration/web_portal/cisco_config_converter/conversion/test_routing.py
python -m pytest tests/integration/web_portal/cisco_config_converter/conversion/test_compat.py
```

Run the existing DNS tests again. Each command must pass.

```text
python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py
python -m pytest tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py
```

Run the guard tests.

```text
python -m pytest tests/guardrails
```

Check the symbol names of the moved module. Each new module needs its own symbol check.

```text
symbol-diff --base origin/main src/interfaces/portals/cisco_config_converter/conversion/common/dns.py
```

Check that no old import path remains. Each command must print no line.

```text
git grep -n "cisco_config_converter.models"
git grep -n "cisco_config_converter.conversion import"
```

Check the complexity of the converter package.

```text
radon cc src/interfaces/portals/cisco_config_converter -j | complexity-gate --max 10
```

Run the full shards on Windows. Each shard prints one summary line.

```text
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\unit --split tests\unit\upgrade_portal
pytest-chunks -x --chunk-timeout 900 --test-timeout 120 tests\contract tests\guardrails tests\integration --split tests\contract\upgrade_portal --split tests\integration\upgrade_portal
```

## Remote Checks Before The Pull Request

List the open pull requests and their changed files. Compare each file with the file set of this record.

```text
gh pr list -R jmorrison-juniper/MistHelper --state open --json number,title,headRefName,files
```

Confirm that the route folder for this record is absent until the record merges.

```text
gh api repos/jmorrison-juniper/MistHelper/contents/specs/numbered/0/0/1/2/2/0/3/0?ref=main
```

Confirm that the OpenAPI file matches the blob SHA in the research record. The local hash must equal `b7fc2bfbe0aa9d718f2a91a5bd1ff07c3b612f14`.

```text
git hash-object documentation/mist-api-openapi31yaml.yaml
```
