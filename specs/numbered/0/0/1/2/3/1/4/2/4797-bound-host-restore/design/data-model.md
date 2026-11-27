# Data Model: Bound host restore for the WLAN RADIUS fixture

## Entities

- **Shared resolver**: The instance `SourceDependencyResolver`. Test code imports it as `_MH` (RC-08). Its state lives in the attribute `_root_module` (RC-11, RC-12). Natural key: the instance identity within one process.
- **Bound host**: The value of `_root_module`. Natural key: object identity, compared with `is`. Possible values: the real MistHelper module, a fake host, a sentinel host, or None.
- **Fake host**: A MagicMock that the `fake_mh` fixture creates for one test (RC-07).
- **Previous host**: The bound host value captured before a fixture binds its fake host. The restore tests capture it in their own setup.
- **Restore case**: One parametrized case of the `previous_host_guard` fixture. Natural keys: `previous_host_guard[sentinel]` and `previous_host_guard[none]`.

## State transitions

| From | Event | To | Evidence |
| - | - | - | - |
| Real host bound | `fake_mh` setup | Fake host bound | Main binds with no restore (RC-08). PR head binds through `patch.object` (RC-10). |
| Fake host bound | Test body runs | Fake host bound | The body reads the fake host (RC-10). |
| Fake host bound | `fake_mh` teardown on PR head | Previous host bound | `patch.object` restores the captured value (RC-10). |
| Fake host bound | `fake_mh` teardown on main | Fake host leaks | No restore on main (RC-08). |
| Fake host leaks | Later context read | Test host returned | The identity check treats `sys.modules` as a test host (RC-14, RC-15). |

## Invariant

After each `fake_mh` teardown, `_root_module` is the object that the same test captured before setup. The restore tests check this invariant (T005). The mutation check proves the test detects a leak (T006).
