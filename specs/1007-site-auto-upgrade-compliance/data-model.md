# Data model 1007 — SiteAutoUpgradeConfig

Immutable, kwargs-only configuration record for
`SiteAutoUpgradeConfigurator`. Mirrors the pattern established in PR #4
(`spec 1006 org_ap_upgrader`).

## Definition

```python
@dataclass(frozen=True, slots=True, kw_only=True)
class SiteAutoUpgradeConfig:
    org_id: str
    apisession: Any
    safe_input_fn: SafeInputFn
    fetch_sites_fn: FetchSitesFn
    check_stop_fn: CheckStopFn
    dry_run: bool = False
```

## Field table

| Field | Type | Required | Default | Purpose | Validation |
| - | - | - | - | - | - |
| `org_id` | `str` | yes | — | Mist organization UUID for all API calls | `__post_init__` asserts `isinstance(str)`; empty string allowed for graceful degradation |
| `apisession` | `Any` (mistapi session) | yes | — | Authenticated mistapi session used by all API helpers | No `None`-rejection — helpers gracefully degrade with a log line and `False`/`{}` return |
| `safe_input_fn` | `Callable[[str, str], str]` | yes | — | EOF-safe interactive input helper (raises `SystemExit` on EOF) | No callable check — duck-typed to preserve testability with `MagicMock` |
| `fetch_sites_fn` | `Callable[[str], list[dict]]` | yes | — | Returns the org's sites | Duck-typed |
| `check_stop_fn` | `Callable[[], bool]` | yes | — | Cooperative stop-signal predicate | Duck-typed |
| `dry_run` | `bool` | no | `False` | Suppress API mutation; print-only mode | `__post_init__` asserts `isinstance(bool)` |

## Construction contracts

### From kwargs (new)

```python
cfg = SiteAutoUpgradeConfig(
    org_id="org-123",
    apisession=session,
    safe_input_fn=safe_input,
    fetch_sites_fn=fetch_sites,
    check_stop_fn=check_stop,
    dry_run=False,
)
configurator = SiteAutoUpgradeConfigurator(config=cfg)
```

### From legacy dataclass (unchanged tests + MistHelper.py)

```python
deps = SiteAutoUpgradeCoreDeps(
    apisession=session,
    safe_input_fn=safe_input,
    fetch_sites_fn=fetch_sites,
    check_stop_fn=check_stop,
    dry_run=False,
)
configurator = SiteAutoUpgradeConfigurator(org_id="org-123", deps=deps)
```

Both invocations resolve to the same internal state via
`_resolve_configurator_kwargs(cfg)`:

- If `config` key present → use it directly.
- Else if `org_id` + `deps` keys present → convert to `SiteAutoUpgradeConfig`
  by pulling `org_id` from kwargs and remaining fields from
  `deps.<attr>`.
- Else → raise `TypeError("SiteAutoUpgradeConfigurator requires either
  config=... or org_id=..., deps=...")`.

## Applied instance attributes

After `__init__`, the configurator exposes the following attributes
(names unchanged from the pre-refactor state so existing tests and internal
references continue to work byte-for-byte):

- From config:
  - `self.org_id: str`
  - `self.apisession: Any`
  - `self.safe_input_fn: SafeInputFn`
  - `self.fetch_sites_fn: FetchSitesFn`
  - `self.check_stop_fn: CheckStopFn`
  - `self.dry_run: bool`

- Workflow-scoped (reset by `_reset_workflow_state`):
  - `self.all_sites: list[dict[str, Any]] = []`
  - `self.selected_sites: list[dict[str, Any]] = []`
  - `self.available_versions: list[Any] = []`
  - `self.model_version_map: dict[str, list[Any]] = {}`
  - `self.custom_versions: dict[str, str] = {}`
  - `self.schedule: dict[str, Any] = {}`
  - `self.current_site_versions: dict[str, str] = {}`
  - `self.is_single_site: bool = False`
  - `self.msp_all_sites_mode: bool = False`
  - `self.org_name: str = ""`
  - `self.shared_versions: dict[str, str] | None = None`

## Invariants preserved

1. **Lenient `apisession=None`**: helpers may receive `None` and must
   log-and-return; the config dataclass does not raise.
2. **Test compatibility**: tests use
   `SiteAutoUpgradeConfigurator(org_id=..., deps=...)` via kwargs. The
   `**cfg` constructor accepts both forms.
3. **Mutable workflow state**: the 11 workflow attributes remain mutable and
   are reset by `_reset_workflow_state` at construction. External callers
   (`_apply_to_all_orgs`, tests) mutate them directly.
