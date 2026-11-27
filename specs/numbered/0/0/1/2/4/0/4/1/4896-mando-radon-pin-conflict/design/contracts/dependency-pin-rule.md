# Contract: Mando pin and Dependabot rule

This contract defines the inputs and results of the dependency guard for issue #4896. The guard reads `requirements-dev.txt`, `.github/dependabot.yml`, and its own range table.

## Scope

- The file `requirements-dev.txt` supplies the pins for radon and mando.
- The file `.github/dependabot.yml` supplies the pip update rule.
- The module `tests/guardrails/test_dependency_lock_file.py` holds the checks, as methods of `DependencyLock` and five test functions.

## Range table

| Radon version | Declared range for mando | Source |
| - | - | - |
| 6.0.1 | `<0.8,>=0.6` | radon 6.0.1 `Requires-Dist` in the local METADATA file (line 31) and in the PyPI JSON |

A radon version that the table does not hold fails the check. The failure names the radon version.

## Pin rule

| Input | Rule | Result when the rule fails |
| - | - | - |
| `radon==X` in `requirements-dev.txt` | X must hold an entry in the range table. | The check raises an error that names X. Test TC-3 proves it. |
| `mando==Y` in `requirements-dev.txt` | Y must satisfy the range for the pinned radon. | The check reports one defect that names mando Y and the range. Test TC-2 proves it. |

The check prints the number of pins that it examined, as AGENTS.md requires for a guard.

## Dependabot rule

| Field | Required value |
| - | - |
| Ecosystem entry | The pip entry, which starts at line 3 of `.github/dependabot.yml` |
| Ignore dependency name | `mando` |
| Ignore update types | `version-update:semver-minor` and `version-update:semver-major` |
| Ignore versions | Not used. The pip syntax is unconfirmed (U-8). |

The check reports one defect when the rule is absent. Test TC-5 proves it. Test TC-4 proves the real file holds the rule.

## Change procedure

1. When radon publishes a version, add its declared range to the range table in the same change.
2. When a radon version accepts mando 0.8, remove the Dependabot rule in a separate change.
3. Do not add a suppression for a defect. Fix the pin or the range instead.
