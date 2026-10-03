# Target Boundary Map

| Target function | New/updated boundary owner | Notes |
| - | - | - |
| `_early_dependency_check` | `src/foundation/runtime/bootstrap/dependency_check.py` (`DependencyCheckOrchestrator`) | MistHelper now delegates early dependency bootstrap orchestration to extracted class. |
| `_execute_site_capture_loop` | `src/operations/execution/capture/site_capture_loop.py` (`SiteCaptureLoopRunner`) | Loop orchestration extracted from legacy body into reusable runner class. |
| `start_org_packet_capture` | `src/operations/execution/capture/org_capture_workflow.py` (`OrgCaptureWorkflow`) | Org capture selection/payload workflow extracted and delegated. |
| `device_events_52w` | `src/operations/exporting/export/device_events_52w_exporter.py` (`DeviceEvents52wExporter`) | 52-week exporter moved to dedicated streaming/checkpoint class. |
| `with_wan_overrides` | `src/mist/resources/gateway/gateway_override_analyzer.py` (`GatewayOverrideAnalyzer`) | MistHelper legacy heavy body replaced by delegation facade. |
