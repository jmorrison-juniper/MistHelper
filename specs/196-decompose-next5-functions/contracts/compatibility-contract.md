# Compatibility Contract: Next-5 Function Decomposition

This contract defines mandatory invariants for refactoring targets in `specs/196-decompose-next5-functions/spec.md`.

## Contract A: Entry stability and invocation compatibility

| Contract Item | Requirement |
| - | - |
| Existing `MistHelper.py` entrypoints | Must remain callable and signature-compatible |
| Menu IDs and menu labels | Must remain unchanged |
| Existing invocation patterns | Must remain backward compatible for operators and automation |

## Contract B: Prompt and interaction parity

| Contract Item | Requirement |
| - | - |
| Prompt sequence | Equivalent order for operator-critical prompts |
| Prompt intent/text | Equivalent user-facing semantics |
| Cancellation/early-return paths | Equivalent behavior on invalid input or user cancel |
| Confirmation/safety gates | Preserved where currently present |

## Contract C: Output and side-effect parity

| Contract Item | Requirement |
| - | - |
| Output schema and key names | Backward compatible |
| Output artifacts (files/tables) | Equivalent naming and write behavior |
| API and execution side effects | Equivalent workflow semantics and guardrails |

## Contract D: Maintainability and observability constraints

| Contract Item | Requirement |
| - | - |
| Cyclomatic complexity | Each target function in scope must be `<=10` |
| Thin-wrapper prohibition | Extracted modules/classes must own logic, not just delegate |
| Inline comments | Every touched executable line must include meaningful same-line intent comments |
| Action logging | Every meaningful action in touched blocks logs before (`info`) and after (`debug`) |
| Error logging | Exceptions in touched blocks must log contextual `error` entries |

## Target Mapping Contract

| Original Function | Required Extracted Owner |
| - | - |
| `_start_site_scan_capture_all_aps` | `src/capture/multi_ap_scan_workflow.py::MultiApScanCaptureWorkflow` |
| `_wait_and_download_pcap` | `src/capture/site_pcap_wait_download_workflow.py::SitePcapWaitDownloadWorkflow` |
| `_wait_and_download_pcap_org` | `src/capture/org_pcap_wait_download_workflow.py::OrgPcapWaitDownloadWorkflow` |
| `wifi_clients` | `src/export/wifi_clients_exporter.py::WifiClientsExporter` |
| `run_interactive_test` | `src/troubleshooting/interactive_test_runner.py::InteractiveTestRunner` |

## Verification Matrix

| Target | Required Verification |
| - | - |
| `_start_site_scan_capture_all_aps` | Unit tests + integration prompt parity + CC gate |
| `_wait_and_download_pcap` | Polling/download unit tests + failure branch tests + CC gate |
| `_wait_and_download_pcap_org` | Org polling/download unit tests + parity checks + CC gate |
| `wifi_clients` | Export schema/unit tests + output parity checks + CC gate |
| `run_interactive_test` | Interactive path unit tests + prompt parity checks + CC gate |
