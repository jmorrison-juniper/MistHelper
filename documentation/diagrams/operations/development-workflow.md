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
flowchart LR
    subgraph backlog["Backlog"]
        b1["Feature Request"]
        b2["Bug Report"]
        b3["Dependency Update"]
    end

    subgraph specify["Specify"]
        s1["/speckit.specify"]
        s2["/speckit.clarify"]
    end

    subgraph plan["Plan"]
        p1["/speckit.plan"]
        p2["/speckit.tasks"]
        p3["/speckit.checklist"]
    end

    subgraph implement["Implement"]
        i1["/speckit.implement"]
        i2["TDD: Tests First"]
        i3["Code Changes"]
    end

    subgraph review["CI + Review"]
        r1["Ruff + mypy"]
        r2["pytest + Coverage"]
        r3["Bandit + pip-audit"]
        r4["Playwright E2E"]
    end

    subgraph deploy["Deploy"]
        d1["Auto-Merge"]
        d2["Container Build"]
        d3["GHCR Push"]
    end

    backlog --> specify --> plan --> implement --> review --> deploy
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
