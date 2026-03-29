[<- Back to Diagram Index](../README.md)

# Development Workflow

SpecKit-driven feature lifecycle from specification through implementation to deployment.

## Feature Lifecycle Board

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {
  'primaryColor': '#E20074',
  'primaryTextColor': '#E0E0E0',
  'primaryBorderColor': '#99004D',
  'lineColor': '#FF4DA6',
  'secondaryColor': '#16213E',
  'tertiaryColor': '#1A1A2E',
  'fontFamily': 'ui-monospace, monospace'
}}}%%
kanban
    column backlog["Backlog"]
        ticket["Feature Request"]
        ticket["Bug Report"]
        ticket["Dependency Update"]

    column specify["Specify"]
        ticket["/speckit.specify"]
        ticket["/speckit.clarify"]

    column plan["Plan"]
        ticket["/speckit.plan"]
        ticket["/speckit.tasks"]
        ticket["/speckit.checklist"]

    column implement["Implement"]
        ticket["/speckit.implement"]
        ticket["TDD: Tests First"]
        ticket["Code Changes"]

    column review["CI + Review"]
        ticket["Ruff + mypy"]
        ticket["pytest + Coverage"]
        ticket["Bandit + pip-audit"]
        ticket["Playwright E2E"]

    column deploy["Deploy"]
        ticket["Auto-Merge"]
        ticket["Container Build"]
        ticket["GHCR Push"]
```

## Workflow Stages

| Stage | Tool | Output |
|-------|------|--------|
| Specify | `/speckit.specify` + `/speckit.clarify` | `spec.md` with user stories and acceptance criteria |
| Plan | `/speckit.plan` | `plan.md`, `research.md`, `data-model.md`, contracts |
| Tasks | `/speckit.tasks` + `/speckit.checklist` | `tasks.md` with dependency-ordered implementation plan |
| Analyze | `/speckit.analyze` | Cross-artifact consistency report |
| Implement | `/speckit.implement` | Code changes following task order |
| CI | GitHub Actions | Quality gate matrix (7 parallel checks) |
| Deploy | Auto-merge + container build | GHCR image + GitHub Release |

---

## Related Diagrams

- [Deployment Pipeline](../infrastructure/deployment-pipeline.md) - CI/CD flow details
- [Operations Reference](operations-reference.md) - Operation lifecycle after deployment
- [Architecture Overview](../core/architecture-overview.md) - System context for features
