# Analysis: WebSocket Dialog Target Wording

## Coverage

| Requirement | Task | Evidence |
| - | - | - |
| FR-001 EX target sets | T001, T002, T004 | `test_ws_utility_text_3890.py` checks the text and the SDK docstring. |
| FR-002 SRX and SSR target sets | T001, T002, T004 | The same test file checks both families. |
| FR-003 State change | T001, T004 | Each DHCP text holds the state-change sentence. |
| FR-004 Optional MAC filters | T001, T004 | The MAC table text test. |
| FR-005 No change to safety, fields, or lock | T003, T006 | The field test and the browser screenshot show the lock. |
| FR-006 Browser proof | T006 | `test_3890_dialog_wording.py` passes 4 of 4. |

## Consistency

- The spec, the plan, and the tasks use the same four utility keys.
- No task changes `websockets.js` or `test_websockets_page.py`.
- The generic `releaseDhcpLeases` fallback text stays unchanged.
- No critical, high, or medium finding remains.
