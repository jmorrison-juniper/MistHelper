# Contributor map for `MistHelper.py`

This guide helps a junior NOC engineer read `MistHelper.py` for the first time.
Use it before you add or change a menu operation.

## What `MistHelper.py` does

`MistHelper.py` starts the MistHelper application.
It checks Python and package needs before normal imports run.
It loads configuration from the environment.
It creates the Mist API session.
It connects command flags, menu actions, portals, and test modes.
It exports selected names through `__all__` for older tests and tools.

## What `MistHelper.py` does not hold

`MistHelper.py` does not hold the main product logic.
It does not hold large data transforms, portal pages, firmware workflows, or device workflows.
Those subjects live in packages under `src\`.
If a change adds behavior, put the code in the matching `src\` package.
Then connect that code from `MistHelper.py` only when the entry point needs it.

## Keep this map stable

Do not cite the number of a line or a range of lines for `MistHelper.py`.
Other work to refactor the file moves lines often.
Cite a stable symbol instead.
Use a class name, a function name, a constant name, or a named section.
Update this map when a symbol name changes.

## Map of `MistHelper.py` by symbol

| Stable symbol | What it holds |
| - | - |
| `MINIMUM_PYTHON_VERSION` | Defines the earliest Python version that the entry point accepts. |
| `LogRotationSettings` | Holds the settings that size and rotate the runtime log. |
| `_early_dependency_check` | Checks required packages before the normal import block runs. |
| `DEFAULT_API_PAGE_LIMIT` | Defines the default Mist page size for API list calls. |
| `_fallback_load_dotenv` | Loads `.env` values when `python-dotenv` cannot run. |
| `GlobalImportManager` | Installs, upgrades, and imports optional packages during startup. |
| `IS_TEST_MODE` | Marks whether the current run uses a test mode. |
| `OUTPUT_FORMAT` | Stores the selected output target for exports. |
| `_snapshot_session_globals_to_state` | Copies session globals into a state object before a mode change. |
| `_select_msp_and_org` | Starts the interactive choice of an MSP and an organization. |
| `_preflight_verify_credentials` | Checks Mist credentials before the tool creates a session. |
| `_build_session_attempts` | Builds the ordered list of session creation attempts. |
| `_configure_session_timeout` | Applies the request timeout policy to the Mist session. |
| `_dispatch_gateway_templates` | Connects a gateway template menu action to the gateway package. |
| `_build_ssh_runner_deps` | Creates the dependency object for SSH command runs. |
| `_build_firmware_manager` | Creates the firmware manager with its required helpers. |
| `_systematic_test_build_safe_list` | Builds the menu list that the safe test mode can run. |
| `_execute_systematic_test_loop` | Runs each selected operation during safe test mode. |
| `_run_web_portal_server` | Starts the web portal server. |
| `_run_capture_portal_server` | Starts the upgrade capture portal server. |
| `_launch_metrics_gateway` | Starts the metrics gateway mode. |
| `_initialize_deferred_imports` | Completes import work that must wait until startup settings exist. |
| `_build_argument_parser` | Defines command flags and direct menu execution flags. |
| `_FAST_MODE_CAPABLE_FUNCTIONS` | Lists operations that can use fast mode. |
| `_initialize_dependencies` | Selects the full or reduced dependency startup path. |
| `_establish_mist_session` | Creates the Mist API session for normal execution. |
| `_run_cli_mode` | Runs one menu action from command flags. |
| `_run_interactive_mode` | Runs the text menu loop for a person. |
| `_MAIN_MODE_TABLE` | Maps startup modes to the function that runs each mode. |
| `_dispatch_main_mode` | Selects the active startup mode from parsed arguments. |

## Where the real work lives

The `src\` tree holds the packages that do product work.
Use the package name as the first clue.
A firmware change starts in `src\firmware\`.
A site change starts in `src\site\`.
An export change starts in `src\export\`.
An upgrade portal change starts in `src\upgrade_portal\`.
A web portal change starts in `web_portal\`.

`MistHelper.py` imports from `src\`.
Code in `src\` must not import `MistHelper.py`.
That direction keeps the product packages testable.

## Keep the `__all__` contract

`__all__` names the public surface that older tests and tools can import.
If you add a public name, add it to `__all__` in the same change.
If you remove a public name, update the related test or tool first.

## Add a menu operation

Use the menu-operation rule in [`.github\copilot-instructions.md`](../.github/copilot-instructions.md#adding-new-menu-operations).
Keep the rule in one place, so the instructions cannot disagree.

In short, choose the endpoint in the Mist API first.
Define the primary key strategy before you export data.
Put the operation class in the matching `src\` package.
Register the menu entry after the operation exists.
Update the user documents and the release-note fragment.

## Validate a local change

Run these commands before you commit a code change.
Run them after a document change when a gate for the pull request needs the same proof.

```powershell
python -m py_compile MistHelper.py
python -m ruff check .
python -m black --check .
python -m mypy $MYPY_PATHS --config-file pyproject.toml
python -m pytest tests/ -x -q
```

Read `MYPY_PATHS` from `.github\workflows\ci.yml` before you run mypy.
The workflow owns that path list.

## Prove a new guard

If you add or change a guard, prove that it can fail.
The guard output must state how many files, records, events, tests, or call sites it checked.
A required guard must fail when it cannot read its input.
If a guard skips for an environmental reason, it must print that reason and name the missing capability.

Use one of two proofs.

1. Link a red run from a temporary bad commit, then remove the commit before merge.
2. Test the guard decision directly with no network and no environment need.

Pull request #2591 proves the first method.
Pull request #2611 proves the second method.
Issue #2689 shows why the count matters.
That SDK compatibility guard skipped all seven tests and still reported green.

## Hot-file rule

Caution: only one open pull request may change `MistHelper.py` at a time.
Two pull requests against that file can lose work during a rebase.
If another pull request changes `MistHelper.py`, choose a different file.

## How to find a thing

| If you need this subject | Start here |
| - | - |
| A firmware question | `src\firmware\` |
| A gateway question | `src\gateway\` |
| A site question | `src\site\` |
| An organization question | `src\org\` |
| A device question | `src\device\` |
| A packet capture question | `src\capture\` |
| An SSH command question | `src\ssh\` |
| A WebSocket question | `src\websocket\` |
| A web portal question | `web_portal\` |
| An upgrade portal question | `src\upgrade_portal\` |
| An export question | `src\export\` |
| A database question | `src\db\` |
| A menu category question | `src\utils\operation_registry.py` |
| An input prompt question | `src\input\` |
| A map question | `src\maps\` |
| A report question | `src\reports\` |
| A metric question | `src\metrics_gateway\` |
| An authentication question | `src\auth\` |
| A validation question | `src\validation\` |
| A constant value | `src\constants.py` |
