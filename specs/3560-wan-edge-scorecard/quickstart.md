# Quickstart: Organization WAN Edge Scorecard

## Prerequisites

1. Use Python `3.13` or newer.
2. Bootstrap the worktree before tests if `.venv` is absent.
3. Keep implementation edits in the later package `src/mist/intelligence/reports/wan_edge_scorecard/`.
4. Keep implementation tests in `tests/unit/reports/wan_edge_scorecard/`.

## Validation scenario 1: unit fixture export

1. Create a gateway statistics fixture with two sites and at least three gateways.
2. Include one gateway without DHCP statistics.
3. Include one DHCP pool below `80` percent and one at or above `80` percent.
4. Include one VPN peer with `up` false.
5. Include one BGP peer that is not established.
6. Run the targeted unit tests.

```powershell
python -m pytest tests\unit\reports\wan_edge_scorecard
```

Expected outcome:

- The test creates `WanEdgeScorecard.csv`.
- The test creates `WanEdgeDhcpPools.csv`.
- The test creates `WanEdgeScorecardBySite.csv`.
- The gateway without DHCP statistics has DHCP pool count `0`.
- The down VPN peer and the non-established BGP peer are counted correctly.

## Validation scenario 2: menu test mode

1. Configure the test harness to call menu `279`.
2. Ensure the test path does not ask for operator input.
3. Run the safe test path.

```powershell
python MistHelper.py --test
```

Expected outcome:

- Menu `279` completes in `--test`.
- The operation writes all three output files under `data/`.
- The console summary prints organization-wide values.

## Validation scenario 3: local quality gates

Run the smallest gates that cover changed files.

```powershell
python -m py_compile MistHelper.py
python -m ruff check MistHelper.py src\mist\intelligence\reports\wan_edge_scorecard tests\unit\reports\wan_edge_scorecard
python -m black --check MistHelper.py src\mist\intelligence\reports\wan_edge_scorecard tests\unit\reports\wan_edge_scorecard
```

Expected outcome:

- The compile check exits with no output.
- Ruff reports no findings for the changed implementation files.
- Black reports no files that need formatting.
