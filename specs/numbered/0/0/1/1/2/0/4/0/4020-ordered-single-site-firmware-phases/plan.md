# Plan: ordered single-site firmware phases

- Issue: #4020
- Specification: `spec.md` in this directory

## Approach

The change has three layers, and each layer owns one decision.

| Layer | File | Decision |
| - | - | - |
| Plan | `src/operations/execution/firmware/upgrade_service.py` | The order of the plans |
| Send | `src/interfaces/portals/upgrade_portal/app/wiring.py` | The firmware of one family |
| Drive | `src/interfaces/portals/upgrade_portal/upgrade/driver.py` | The moment of each send |

The plan layer is pure, so the portal never reorders a plan. The send layer is
the one place a firmware call leaves the portal. The drive layer holds the fail
closed rule.

## Layer 1: the pure plan order

`PLAN_FAMILY_ORDER` is a `Final` tuple of `gateway`, `switch`, `ap`.
`_family_rank(device_type)` reads the index of that tuple, and an unknown family
takes the rank after every known family. `_ordered_groups(groups)` sorts the
items of the group dictionary with that rank through `sorted`, which is stable,
so two version groups of one family keep their order. `plan_upgrade` reads
`_ordered_groups(groups)` in place of `groups.items()`.

`tests/unit/upgrade_portal/test_upgrade_service_prohibitions.py` forbids a
mutable module-level value, so the rank is a function and not a dictionary.

## Layer 2: the per-phase submitter

`CloudUpgradeSubmitter.submit(record) -> bool` becomes
`submit_phase(record, phase) -> str | None`. The answer is `None` when the phase
is done, and a sentence when the run must stop. The shape changes, and no
compatibility shim stays, because `AGENTS.md` forbids one.

- No plan at all gives `NO_PLAN_REASON`.
- No plan for this phase gives `None` with no cloud call.
- `_send_phase` walks the plans of that phase in the canonical order. It keeps
  each accepted row through `_persist_row`, which appends to
  `record["upgrades"]` and writes the run store before another plan can leave.
  It checks the durable stop request before every plan. A stop gives
  `STOP_REQUESTED_REASON`, and a lost row write gives
  `ACCEPTED_ROW_STORE_REASON`.
- `plan_phase(plan)` reads every target. An empty plan, an unknown family, or a
  plan that mixes families has no route. `submit_phase` validates every plan
  before the first cloud write and gives `UNROUTABLE_PLAN_REASON` on a gap.

## Layer 3: the interleaved cascade

`RunDriver.run` calls `_cascade(record)` only. `_cascade` advances the record to
`UPGRADE_SUBMITTING`, and then it walks `PHASE_ORDER`.

1. Beat the lock, and stop when an operator asked for a stop.
2. A lost upstream family blocks this family through `_block_phase`, except for
   the client phase, which carries no firmware and still counts the clients.
3. Otherwise `_submit_phase(record, name)` sends the firmware of this family.
   A refusal marks this phase failed and keeps the refusal inside the cascade.
   A durable stop request goes to `_stop` before the refusal branch.
4. Advance to the settle state of this family, and open the gate.
5. Record the first loss, and continue to the next family.

`_block_phase` advances the settle state first, because the state chain is
linear and no run can step over a family. It then marks the family `failed` with
`PHASE_BLOCKED_NOTE` when the site holds such a device, or `skipped` when it
does not.

`_submit_phase` returns a reason after it writes the accepted rows and the
tracker. `_refuse_phase` makes the refused family terminal. The cascade then
blocks later firmware families, runs the client observation path, and calls
`_finish(record, reason)`. The post-check evidence therefore survives a partial
upgrade. Nothing retries the refused write.

`_enter_running` advances to `UPGRADE_RUNNING` only from `UPGRADE_SUBMITTING`,
because the state machine refuses a repeated advance.

## Constraints

- Lines 1 through 20 of `driver.py` stay byte for byte, because pull request
  #4075 owns that module docstring.
- A failed settle blocks the firmware of a later family. It does not stop the
  settle cascade, because the existing tests read a state for every family.
- No test reaches the Mist cloud. Every test uses a double.

## Risks

| Risk | Control |
| - | - |
| A lost upstream family leaves the site in two firmware levels | The record names each held family, and the note tells the operator why |
| The protocol change breaks a caller | Each caller and each double changed in the same commit |
| `build_plans` now runs one time for each phase | The function is pure, and the plan count of one site is small |

## Verification

| Gate | Command |
| - | - |
| Unit | `python -m pytest tests/unit/upgrade_portal` |
| Contract | `python -m pytest tests/contract/upgrade_portal` |
| Lint | `python -m ruff check .` |
| Format | `python -m black --check .` |
| Types | `python -m mypy $MYPY_PATHS --config-file pyproject.toml` |
| Security | `bandit -c pyproject.toml -r src -q` |
