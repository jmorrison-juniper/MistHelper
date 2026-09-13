# Feature Specification Summary – Issue #293

**Feature Directory**: `specs/190-reduce-cc-plotly-viewer`  
**Specification File**: `spec.md`  
**Checklist**: `checklists/requirements.md`  
**Status**: ✅ **APPROVED FOR PLANNING**  

---

## Quick Reference

| Item | Details |
|------|---------|
| **Issue** | #293: Reduce CC in `_launch_plotly_viewer` |
| **Current CC** | 138 (target: ≤10) |
| **File** | `src/maps/maps_manager.py` (lines 3010–8256, 5,247 lines) |
| **Proposed Classes** | 6 new classes: PlotlyMapViewer, FigureBuilder, HeatmapRenderer, CallbackManager, TemplateManager, Serializer |
| **Extraction Phases** | 6 phases, sequenced by risk (Phase 1: templates, Phase 6: integration) |
| **Test Strategy** | Unit tests, integration tests, regression tests (targeting ≥70% coverage) |
| **Quality Gates** | ruff, black, mypy --strict, CodeQL, pytest+cov |

---

## Specification Highlights

### Problem Statement
- Monolithic 5,247-line method with CC=138 (13.8× over target)
- Combines 6 distinct concerns: Dash init, HTML/CSS, figure building, heatmap rendering, UI layout, server startup
- Results: hard to test, maintain, reuse; slow code review; high regression risk

### Success Criteria (10 measurable outcomes)
1. **CC reduction**: `_launch_plotly_viewer` from 138 → ≤10
2. **Class-level CC**: Average MapsManager method CC ≤10
3. **Per-method CC**: All extracted classes ≤10 per method
4. **Test coverage**: ≥70% for `src/maps/`
5. **Test compatibility**: All 100+ existing tests pass unchanged
6. **Quality gates**: ruff, black, mypy, CodeQL all green
7. **Functional equivalence**: Web UI integration tests confirm identical behavior
8. **Performance**: <5% regression in app startup time
9. **Data integrity**: Callback serialization byte-for-byte identical
10. **Documentation**: Architecture diagram + complete docstrings

### Architecture (6-Class Decomposition)

```text
PlotlyMapViewer (orchestrator)
├── DashTemplateManager (CSS/HTML)
├── PlotlyMapFigureBuilder (walls, devices, clients, heatmap)
├── CoverageHeatmapRenderer (interpolation algorithm)
├── PlotlyMapCallbackManager (~25 callbacks)
└── PlotlyMapDataSerializer (JSON serialization)
```

### Extraction Phases (Lowest to Highest Risk)

| Phase | Component | Effort | Risk | Key Validation |
|-------|-----------|--------|------|---|
| 1 | Templates | 2–3h | Low | CSS/HTML byte-identical |
| 2 | Serialization | 2–3h | Low | JSON payloads byte-identical |
| 3 | Heatmap | 4–5h | Medium | Numeric output (rtol=1e-10) |
| 4 | Figures | 5–6h | Medium | Plotly figure JSON identical |
| 5 | Callbacks | 8–10h | High | All callbacks execute identically |
| 6 | Integration | 6–8h | High | Full E2E web UI tests pass |

### Key Risks & Mitigations

1. **Callback state serialization breaks** → Unit test every callback input/output pair
2. **Heatmap algorithm diverges numerically** → Use `np.allclose(rtol=1e-10)` for 5+ test sites
3. **Callback decorator registration fails** → Verify Dash discovers all callbacks
4. **Performance regression** → Benchmark <5% threshold
5. **Breaking public API** → Lock signature, return type
6. **Coverage drops below 70%** → Mandatory unit tests for all extracted classes

### Testing Strategy

| Type | Scope | Example |
|------|-------|---------|
| **Unit** | Per-component (isolated) | `test_build_walls_figure()`, `test_interpolate_grid()` |
| **Integration** | Full workflow | `test_viewer_initialization()`, `test_callback_execution()` |
| **Regression** | Behavior comparison | `test_figures_identical()`, `test_heatmap_output_identical()` |

---

## Acceptance Criteria Checklist (23 items)

✅ All items verified as part of specification quality validation:

- **CC Reduction** (3 items): CC ≤10 per method, class average ≤10
- **Testing** (4 items): All 100+ existing tests pass, new unit tests, coverage ≥70%
- **Quality** (5 items): ruff, black, mypy --strict, CodeQL, pytest coverage
- **Functionality** (6 items): App init, callbacks, figures, UI tests, heatmap, server config
- **Performance** (1 item): <5% regression
- **API** (2 items): Signature unchanged, return type unchanged
- **Documentation** (2 items): Architecture diagram, docstrings

---

## Implementation Guidance

### For Planning Phase (`/speckit.plan`)
- Use the 6 extraction phases as the task sequence
- Each phase includes effort, risk level, and validation approach
- Risk mitigations should be incorporated into task definitions

### For Task Phase (`/speckit.tasks`)
- Break Phase 5 (Callbacks) into sub-tasks (~25 callbacks × grouping)
- Create test task for each validation approach
- Include integration task at end (Phase 6)

### For Implementation Phase (`/speckit.implement`)
- Follow extraction sequence: templates → serialization → heatmap → figures → callbacks → integration
- After each phase, verify acceptance criteria
- Run full quality gate suite before merge

### Quality Gates (CI/CD)
```bash
# Pre-commit validation
python -m py_compile src/maps/
python -m ruff check src/maps/
python -m black --check src/maps/
python -m mypy --strict src/maps/

# Full pipeline
pytest --cov=src/maps/ --cov-fail-under=70
# CodeQL scanning in CI
```

---

## Non-Goals

❌ Redesigning map UI or Dash layout  
❌ Changing dependencies  
❌ Converting to async/await  
❌ Migrating to different web framework  
❌ Adding new features  
❌ Performance optimization beyond regression testing  
❌ API changes visible to external callers  

---

## Next Steps

1. ✅ **Specification Complete**: Ready for `/speckit.plan`
2. 📋 **Proceed to Planning**: Generate detailed task breakdown
3. 📝 **Create Tasks**: Sequence 6 phases with acceptance criteria
4. 🔨 **Implementation**: Follow phase order; validate each phase
5. ✔️ **Acceptance**: All checklist items verified before merge

---

## References

- **Specification**: [spec.md](spec.md)
- **Checklist**: [checklists/requirements.md](checklists/requirements.md)
- **Issue**: #293 on GitHub
- **Project Standards**: `.github/copilot-instructions.md`, `agents.md`
- **Source Code**: `src/maps/maps_manager.py` (lines 3010–8256)

