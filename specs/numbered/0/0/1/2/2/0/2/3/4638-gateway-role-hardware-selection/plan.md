# Implementation Plan: Add explicit gateway role and hardware selection

**Branch**: `feat/4638-gateway-role-hardware-selection` | **Date**: 2026-11-26 | **Spec**: [spec.md](spec.md)

**Input**: Numeric record at `specs/numbered/0/0/1/2/2/0/2/3/4638-gateway-role-hardware-selection/`. Decimal 4638 equals `122023` in base 5. Padded to eight levels, it gives `0/0/1/2/2/0/2/3`.

## Summary

Add explicit role, family, model, and port selection to the Cisco converter. Map each selection to one local evidence row. Block each unverified, stale, unknown, or conflicting selection before review. Keep the DNS conversion unchanged. Add no Mist call, no route registration, and no apply path.

## Technical Context

- **Language/Version**: Python 3.15 or newer. Source: `.github/copilot-instructions.md`, line 20.
- **Primary Dependencies**: Flask, already used by the converter. The installed mistapi 0.64.1 is read as evidence only. No dependency change.
- **Storage**: None. The review digest stays in the Flask session. Source: `src/interfaces/portals/cisco_config_converter/models.py`, lines 84 to 112 on main.
- **Testing**: pytest under `tests/integration/web_portal/cisco_config_converter/` and the existing unit test path.
- **Target Platform**: Windows 11, macOS, Linux, and the Podman container. No platform change.
- **Project Type**: Feature package inside the web portal interface package.
- **Performance Goals**: None. Each preview evaluates one selection in memory.
- **Constraints**: Offline operation. No Mist call. No route registration. No shared portal change. Synthetic data only.
- **Scale/Scope**: One new package with three modules, four modified modules, two presentation files, three test files, and one changelog fragment.

## Constitution Check

| Rule | Result | Reason |
| --- | --- | --- |
| I. Five-Item Rule, levels | Pass after D-14 | The converter root keeps five children: `__init__.py`, `conversion/`, `presentation/`, `routes.py`, and `state/`. |
| I. Five-Item Rule, folders | Pass | `tests/contract/` stays untouched. The new test module goes to the integration folder (D-12). |
| I. Five-Item Rule, functions | Pass by plan | Each planned function has five parameters or fewer and 25 lines or fewer. T014 runs the complexity gate. |
| II. Class-based architecture | Pass | Behavior sits in `HardwareRegister`, `HardwareMapping`, and `ConverterInput`. No wrapper function is planned. |
| III. Safety-first input | Pass | The selection parser validates every field before use. Each input failure returns HTTP 400. |
| III. Destructive operations | Pass | No destructive operation is added. Apply stays out of scope. |
| III. Secrets in logs | Pass | No secret enters the register, the proposal, or a log line. |
| IV. Deployment pipeline | Pass by plan | T-LOCAL-GATES, T-PR, T-REMOTE-CI, and T-MERGE run in the constitution order. |
| V. ASCII logs | Pass | All new log text uses ASCII only. |
| V. Structured logs | Pass with inherited item | The change adds no service or module. Standard logging stays. Issue 4636 open item U-2 stays with the owner. |
| VI. Inline comments | Pass by plan | T014 audits each executable line. |
| VII. Action logging | Pass by plan | `HardwareMapping.attach` logs before and after evaluation. The parser logs before and after validation. |
| Technology: mistapi | Pass | No Mist call is made. Evidence cites local OpenAPI and SDK files. |
| Technology: owned WebSocket | Not applicable | No WebSocket transport is added. |
| Technology: UV and requirements | Pass | No dependency change. |
| Technology: Podman and test containers | Pass | No container is started or changed. |
| Technology: file paths | Pass | The code uses no hard-coded path separator. |
| Technology: operational store | Pass | No store is added. |
| Technology: export boundary | Pass | The export keeps its shape and adds the `hardware` key. |
| Technology: data directory | Pass | No file is written under `data/`. |
| Documentation | Pass | No user document names the converter. The changelog fragment records the change. |
| Escalation | Pass | More than three files change. This record exists. |
| Multi-agent git: issue first | Pass | Issue 4638 exists. T-PR applies the `in-progress` label before the branch. |
| Multi-agent git: overlap | Pass with sequencing | Seven open pull requests do not touch the converter files. Drafts 4637, 4640, 4641, and 4647 do. See Sequencing. |

Sequencing constraint: T008 edits two files that issue 4636 creates. This record cannot merge before issue 4636.

## Approved Package Structure

```text
src/interfaces/portals/cisco_config_converter/
  __init__.py                  unchanged
  conversion/                  replaces conversion.py (issue 4640 D-1, executed here)
    __init__.py                docstring only
    common/
      __init__.py              docstring only
      dns.py                   IOSDnsConverter moved from conversion.py
    hardware/                  reserved for issue 4638 (issue 4640 D-3)
      __init__.py              docstring only
      register.py              HardwareRegister
      mapping.py               GatewaySelection, HardwarePortAssignment, HardwareMapping
    network/                   issue 4640, not changed here
    management/                reserved for issue 4639, not changed here
  presentation/                converter.html and converter.js change
  routes.py                    changes here
  state/                       issue 4636 package, two files change
```

| Directory | Children after this change | Limit | Status |
| --- | --- | --- | --- |
| Converter root | 5: `__init__.py`, `conversion/`, `presentation/`, `routes.py`, `state/` | 5 | At limit. No child added. |
| `conversion/` | 3: `__init__.py`, `common/`, `hardware/` | 5 | Compliant. Issue 4640 adds `network/`. Issue 4639 adds `management/`. |
| `conversion/common/` | 2: `__init__.py`, `dns.py` | 5 | Compliant. Issue 4640 adds two modules. |
| `conversion/hardware/` | 3: `__init__.py`, `mapping.py`, `register.py` | 5 | Compliant. |

## Why conversion.py Moves Here

Issue 4640 decision D-1 replaces `conversion.py` with a `conversion/` package. Issue 4640 decision D-3 reserves `conversion/hardware/` for this issue. The `hardware/` package needs the `conversion/` package first. This record makes the move first. Issue 4640 keeps its network work and drops its own DNS move. The final layout matches both records.

If the owner rejects the issue 4640 layout, this record reverts to one module. That module would hold five top-level names and no room for the register and the mapping class.

## Architecture

1. The browser posts the file, the name, the role, the family, the model, and the `ports` JSON to `/preview`.
2. `ConverterInput.selection` validates each field and returns HTTP 400 for a format failure.
3. `IOSDnsConverter.convert` builds the DNS proposal. Its output does not change for DNS input.
4. `HardwareMapping.attach` reads the evidence row. It sets `gateway_template.type` only for a verified role. It adds the `hardware` block and each blocker.
5. `ReviewState.publish` stores the digest of the whole proposal. Any selection change alters the digest.
6. `/review` refuses a proposal whose `hardware.status` is not `verified`. `/export` requires an earlier review of the same digest.

## File-by-File Change Map

| Path | Action | Content |
| --- | --- | --- |
| `src/interfaces/portals/cisco_config_converter/conversion.py` | Delete | Moved to `conversion/common/dns.py`. |
| `src/interfaces/portals/cisco_config_converter/conversion/__init__.py` | Add | Module docstring only. |
| `src/interfaces/portals/cisco_config_converter/conversion/common/__init__.py` | Add | Module docstring only. |
| `src/interfaces/portals/cisco_config_converter/conversion/common/dns.py` | Add | Moved `IOSDnsConverter`. Changes the hardware sentence in `known_gaps`. Removes the `type` value from the DNS template. |
| `src/interfaces/portals/cisco_config_converter/conversion/hardware/__init__.py` | Add | Module docstring only. |
| `src/interfaces/portals/cisco_config_converter/conversion/hardware/register.py` | Add | `HardwareRegister` with the revision constant, the evidence rows, and `options`. |
| `src/interfaces/portals/cisco_config_converter/conversion/hardware/mapping.py` | Add | `GatewaySelection`, `HardwarePortAssignment`, and `HardwareMapping.attach`. |
| `src/interfaces/portals/cisco_config_converter/state/intake.py` | Modify | `SourceConfiguration.read` drops the `kind` argument. Issue 4636 creates this file. |
| `src/interfaces/portals/cisco_config_converter/state/proposal.py` | Modify | `GatewayTemplate.type` becomes `NotRequired`. Issue 4636 creates this file. |
| `src/interfaces/portals/cisco_config_converter/routes.py` | Modify | New imports. `ConverterInput.selection`. Preview composition. Review gate. Register data for the page. |
| `src/interfaces/portals/cisco_config_converter/presentation/converter.html` | Modify | Role, family, model, usage, and interface controls. The register data block. The retired type select is removed. |
| `src/interfaces/portals/cisco_config_converter/presentation/converter.js` | Modify | Builds model options and port rows from the register. Sends the `ports` JSON. Resets on `input` and `change`. |
| `tests/integration/web_portal/cisco_config_converter/test_hardware.py` | Add | Seventeen hardware tests (T002). |
| `tests/integration/web_portal/cisco_config_converter/test_routes.py` | Modify | Seven new route tests. Form fields change from `type` to the new fields. |
| `tests/unit/marvis/mist/resources/gateway/overrides/test_cisco_config_converter.py` | Modify | New import path. `SourceConfiguration.read` without `kind`. The DNS expectation has no template type. |
| `tests/e2e/web_portal/test_portal_smoke.py` | Modify after issue 4647 merges | One browser selector test (T013). |
| `changelog.d/issue-4638-gateway-role-hardware-selection.md` | Add | `Added` and `Changed` bullets that name issue 4638. |
| `specs/numbered/0/0/1/2/2/0/2/3/4638-gateway-role-hardware-selection/` | Add | This record. |

Unchanged paths: `web_portal/app.py`, `web_portal/templates/base.html`, `web_portal/services/config.py`, `compose.yml`, `.gitignore`, `requirements.txt`, and `documentation/`.

## Sequencing

1. Issue 4634 records field semantics for each verified row. T006 waits for this step.
2. Issue 4636 merges `state/`. T008 waits for this step.
3. Issue 4637 merges its review section and its route changes. T009 and T010 wait for this step.
4. This record merges through T-MERGE.
5. Issue 4640 rebases onto `conversion/common/dns.py` and `conversion/hardware/`. It keeps its network work.
6. Issue 4641 reads the `hardware` key. Issue 4647 rebases `converter.html`, `converter.js`, and `test_portal_smoke.py`. T013 waits for issue 4647.

## Risks and Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Issue 4634 rejects a row's field semantics. | The row must stay blocked. | Each row stands alone. Rejecting one row does not change the other rows. |
| The Branch mapping stays unverified. | Branch stays unusable. | Blocker `role_unverified` names the missing evidence. Decision D-3 records the choice. |
| Drafts 4637, 4640, 4641, and 4647 change the same presentation and route files. | Merge conflicts or lost changes. | The sequencing above applies. The second merge rebases. |
| An external script still posts the retired `type` field. | The script receives HTTP 400. | The 400 message names the replacement field. No external caller is known. |
| An operator types a Cisco interface name that the file does not contain. | The row stays blocked. | Blocker `source_interface_not_found` names the mismatch. |
| A banner line starts with `interface ` and creates a false candidate. | The operator could select a banner line. | The name must still match the file exactly. The test covers the banner case. |
| The OpenAPI example differs from the live Mist catalog. | A row could be wrong for live devices. | Issue 4634 verifies field semantics before merge. The revision constant forces re-review after a pin change. |

## Rollback Steps

1. Revert the squash commit through a pull request on `main`.
2. Confirm that `conversion.py` returns and that the `conversion/` package is gone.
3. Confirm that `state/intake.py` again accepts the `kind` argument.
4. Run `python -m pytest tests/integration/web_portal/cisco_config_converter/test_routes.py`.

No production record is written by this change. Rollback removes no stored data.

## Complexity Tracking

| Item | Type | Reason | Action |
| --- | --- | --- | --- |
| `conversion/` package | Structure change | `conversion.py` cannot hold the register and the mapping within five top-level names. | Follows issue 4640 decision D-1. |
| Register data in `register.py` | Placement | Keeps evidence data apart from decision logic. | None. |
| Integration test folder | Five children after issue 4640 | The new `test_hardware.py` becomes the fifth child. | Issue 4642 must not add a sixth child. See analysis F-13. |
| UI browser test | Deviation from the web UI rule | `tests/e2e/` and `tests/e2e/web_portal/` cannot take a new file. | T013 adds a function to the existing smoke file after issue 4647 merges. |
| `tests/contract/` | Avoided | The folder holds 17 children and cannot take another. | Decision D-12 places the module in the integration folder. |
