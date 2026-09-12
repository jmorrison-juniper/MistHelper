# Contract: Probe-Payload Byte-Stability Invariant (INV-1 scoped to 1025)

**Feature**: `1025-probe-emission-log-fixes`
**Scope**: All non-VPN probe payloads emitted by
`manage_org_synthetic_probes` for any fixture org exercised by the 1025
test suite.
**Related FRs**: FR-003, FR-011, SC-004
**Origin**: Restated from spec 1024's INV-1 (the parent byte-stability
guarantee); this document narrows the invariant to the surface 1025
touches.

---

## 1. Statement

For any fixture-driven invocation of `manage_org_synthetic_probes` on a
site set whose non-VPN probe emission was baselined against `main` HEAD
prior to 1025 (or against the artifacts already captured during spec
1024's implementation), the emitted probe collection MUST be
byte-identical to that baseline.

Formally: let `B` be the pre-1025 baseline probe collection for a given
fixture and let `P` be the post-1025 probe collection for the same
fixture. Then `json.dumps(B, sort_keys=True) == json.dumps(P, sort_keys=True)`
for every non-VPN probe.

## 2. Why this matters

1. The whole point of 1025 is a *logging* change. Any probe-payload
   diff signals scope creep, an accidental refactor, or a subtle
   dependency between the WARNING move and the payload builder — all of
   which need explicit spec approval before merging.
2. Downstream: Mist stores custom-probe records verbatim. A byte-different
   probe body triggers a Mist-side update event, which cascades to every
   fabric that consumes the org setting. A silent byte diff can produce a
   real-world configuration churn event.
3. Operators baseline their day-2 monitoring against emitted probe
   fingerprints; a change here breaks their tooling.

## 3. Machine-checkable assertion

```python
# tests/unit/org/test_org_synthetic_probes_manager.py

def test_probe_payload_byte_stability_smoke(fake_session_smoke, org_id):
    """INV-1 restated. Fixture: smoke_org.json (reused from spec 1024)."""
    # Baseline captured during 1024 implementation and pinned in-tree.
    baseline_path = (
        Path(__file__).parent / "fixtures" / "smoke_probes_baseline.json"
    )
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))

    # Capture emitted probes without actually PUT-ing them.
    with patch_apply_to_capture() as captured:
        manage_org_synthetic_probes(fake_session_smoke, org_id)

    # Filter to non-VPN probes (VPN is spec 1024's own scope).
    non_vpn_emitted = {n: p for n, p in captured.items() if not is_vpn_probe(p)}
    non_vpn_baseline = {n: p for n, p in baseline.items() if not is_vpn_probe(p)}

    # Byte-identical when sorted-key-serialized.
    assert json.dumps(non_vpn_emitted, sort_keys=True) == json.dumps(
        non_vpn_baseline, sort_keys=True
    ), "non-VPN probe payload drifted from 1024 baseline (INV-1 violation)"
```

## 4. Scope carve-outs

- **VPN probes**: Explicitly out of scope of *this* invariant. Spec 1024
  owns their contract.
- **Foreign probes** (probes whose name does not start with `zcc-`):
  Preserved verbatim per FR-012 (spec 1024); their byte-stability is
  automatic (`_apply` does `{**foreign, **resulting_tool}`) but not
  asserted here.
- **`vlan_ids` field**: The operator supplies VLAN ids at prompt time.
  The baseline fixture pins a specific VLAN list; the test must supply
  the same list via a monkey-patched `_prompt_vlan_list` so the
  comparison is meaningful.

## 5. What triggers this contract to fail (intentional)

- The WARNING move accidentally references the `target` field and
  rewrites it — payload changes, test fails.
- A refactor of `_build_probe_set` reorders `dict.items()` in a way that
  changes iteration order and shows up in a diff (very unlikely under
  Python 3.7+ dict-order stability, but guarded).
- A future contributor adds a new field to the emitted probe body
  without also updating the baseline fixture — the test fails,
  prompting them to either revert or capture a new baseline in a
  targeted follow-up spec.

## 6. What does NOT trigger this contract

- Log-record content changes (the whole point of 1025).
- New INFO / DEBUG / WARNING records outside the probe-emission path.
- Region-classification changes for LATAM/Caribbean sites — none of
  those sites are in `smoke_org.json`, so their region resolution does
  not touch the baseline. If future test fixtures expand the smoke org
  to include LATAM sites, the baseline is re-captured in the same PR.
