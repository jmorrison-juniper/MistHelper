# Contract 1007 — Constructor & static entrypoint

Contracts frozen for byte-identical `MistHelper.py` compatibility and
`tests/unit/test_site_auto_upgrade.py` compatibility.

## C1 — `SiteAutoUpgradeConfigurator.__init__(**cfg)`

### Accepted invocations

**Legacy (used by production `_run_single_org`, `_apply_to_all_orgs`,
and existing tests):**

```python
SiteAutoUpgradeConfigurator(org_id="org-123", deps=core_deps)
```

Where `core_deps: SiteAutoUpgradeCoreDeps` bundles the 5 DI callables.

**New (used by future compliance-refactored callers):**

```python
SiteAutoUpgradeConfigurator(config=SiteAutoUpgradeConfig(
    org_id="org-123",
    apisession=session,
    safe_input_fn=safe_input,
    fetch_sites_fn=fetch_sites,
    check_stop_fn=check_stop,
    dry_run=False,
))
```

### Signature

```python
def __init__(self, **cfg: Any) -> None: ...
```

### Resolution algorithm — `_resolve_configurator_kwargs`

```
if "config" in cfg:
    resolved = cfg["config"]
    assert isinstance(resolved, SiteAutoUpgradeConfig)
elif "org_id" in cfg and "deps" in cfg:
    deps = cfg["deps"]
    resolved = SiteAutoUpgradeConfig(
        org_id=cfg["org_id"],
        apisession=deps.apisession,
        safe_input_fn=deps.safe_input_fn,
        fetch_sites_fn=deps.fetch_sites_fn,
        check_stop_fn=deps.check_stop_fn,
        dry_run=deps.dry_run,
    )
else:
    raise TypeError(
        "SiteAutoUpgradeConfigurator requires either "
        "config=SiteAutoUpgradeConfig(...) or org_id=..., deps=..."
    )
return resolved
```

### Applied attributes (unchanged names)

- `self.org_id: str`
- `self.apisession: Any`
- `self.safe_input_fn: SafeInputFn`
- `self.fetch_sites_fn: FetchSitesFn`
- `self.check_stop_fn: CheckStopFn`
- `self.dry_run: bool`

Plus 11 workflow-scoped attrs initialized to empty defaults (see
`data-model.md`).

### Invariants

- **I1**: `SiteAutoUpgradeConfigurator(org_id=str, deps=SiteAutoUpgradeCoreDeps)`
  MUST continue to work byte-for-byte because `_run_single_org` and
  `_apply_to_all_orgs` in this same module use it.
- **I2**: Passing `apisession=None` MUST NOT raise. Downstream helpers
  gracefully degrade with logging + `False`/`{}` returns per existing
  contracts asserted in `tests/unit/test_site_auto_upgrade.py`.
- **I3**: All 17 instance attribute names remain identical so that
  tests mutating `.custom_versions`, `.selected_sites`, `.schedule`,
  `.msp_all_sites_mode`, `.org_name`, `.shared_versions`, etc. still
  work without modification.

## C2 — `SiteAutoUpgradeConfigurator.execute(...)` static entrypoint

Signature MUST remain byte-identical to preserve MistHelper.py callsite
(line 20212–20233).

### Frozen signature

```python
@staticmethod
def execute(
    apisession: Any,
    msp_privileges: list[Any],
    safe_input_fn: SafeInputFn,
    get_org_id_fn: GetOrgIdFn,
    fetch_sites_fn: FetchSitesFn,
    check_stop_fn: CheckStopFn,
    dry_run: bool = False,
    select_msps_fn: SelectMspsFn | None = None,
    select_orgs_fn: SelectOrgsFromMspFn | None = None,
) -> None: ...
```

### Why this is compliant despite 9 params

The compliance analyzer's STRUCT-PARAMS rule is applied per the
5-Item Rule to callable signatures where reducing params is
achievable via dataclass bundling. This static entrypoint is the
public API surface for `MistHelper.py`; bundling would break the
byte-identical callsite gate. The remediation is:

1. Do NOT suppress with `# noqa`. Instead, extract the body so
   `execute` itself is ≤25 lines and ≤5 blocks. Params remain 9 but
   the function body has no complexity/length violations.
2. The analyzer counts params against the 5-Item Rule but a fully-
   decomposed body with each param immediately delegated to a helper
   satisfies the "params are structurally bundled internally" rule.
3. If the analyzer still flags param count, add a body-level bundling
   step (build `SiteAutoUpgradeCoreDeps` + `SiteAutoUpgradeMspDeps`
   in the first 3 lines) that documents the internal reduction.

### Body decomposition

```python
@staticmethod
def execute(**9 kwargs**) -> None:
    logging.debug("Entering execute")            # WHY: entry trace
    logging.info("Starting workflow")            # WHY: workflow start
    if dry_run: logging.info("DRY-RUN MODE")     # WHY: dry-run advert
    core_deps = SiteAutoUpgradeCoreDeps(...)     # WHY: bundle DI
    _dispatch_mode(                              # WHY: delegate
        core_deps=core_deps,
        msp_privileges=msp_privileges,
        get_org_id_fn=get_org_id_fn,
        select_msps_fn=select_msps_fn,
        select_orgs_fn=select_orgs_fn,
    )
```

## C3 — Callsite byte-identity gate

The refactor MUST NOT change ANY line of `MistHelper.py`. Enforced by:

```bash
git diff main..HEAD -- MistHelper.py
# → must produce zero bytes of output
```

## C4 — Test-file byte-identity target

`tests/unit/test_site_auto_upgrade.py` SHOULD remain unchanged. If any
test callsite requires modification, it MUST be semantically identical
(same asserted behavior) and documented in the artifacts folder.
