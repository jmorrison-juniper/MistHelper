[<- Back to Diagram Index](../README.md)

# Deployment Pipeline

Quality gates, container publishing, and release artifacts for MistHelper.

## Quality Gate Flow

From code change through quality gates to a merge.

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
    A[Code Push] --> B[GitHub Actions CI]

    B --> C1[Ruff lint]
    B --> C2[Black format]
    B --> C3[mypy types]
    B --> C4[pytest + coverage]
    B --> C5[Security gates]
    B --> C6[Doc and diagram gates]
    B --> C7[Browser and portal gates]

    C1 --> D{All Gates Pass?}
    C2 --> D
    C3 --> D
    C4 --> D
    C5 --> D
    C6 --> D
    C7 --> D

    D -->|Yes| E[Auto-Merge PR]
    D -->|No| F[Block + Fix]
    F --> A

    E --> G[Main branch push]
    G --> H[container-build.yml]
    H --> I[Validate, test, build]
    I --> J[Push amd64 and arm64 images to GHCR]
    J --> K[Operator Pulls Image]

    K --> L1[Host: systemd restart]
    K --> L2[Container: Quadlet restart]

    style A fill:#E20074,stroke:#99004D,color:#E0E0E0
    style D fill:#FFD600,stroke:#FFD600,color:#1A1A2E
    style E fill:#00C853,stroke:#00C853,color:#1A1A2E
    style F fill:#FF1744,stroke:#FF1744,color:#E0E0E0
    style J fill:#E20074,stroke:#99004D,color:#E0E0E0
```

## Container and Release Jobs

The container workflow runs after a main push or a manual request. The release
workflow runs only for tags that match `v*.*.*`.

```mermaid
%%{init: {'theme': 'dark', 'themeVariables': {
  'primaryColor': '#E20074',
  'primaryTextColor': '#E0E0E0',
  'gridColor': '#16213E',
  'todayLineColor': '#FF1744'
}}}%%
flowchart TD
    A["Main push or workflow_dispatch"] --> B["Validate MistHelper.py syntax"]
    B --> C["Run tests/unit/"]
    C --> D["Build linux/amd64 and linux/arm64"]
    D --> E["Push version tag and latest to GHCR"]

    T["Tag v*.*.*"] --> R1["Build wheel and sdist"]
    T --> R2["Build standalone zip"]
    T --> R3["Build container image"]
    R1 --> R4["Create GitHub Release"]
    R2 --> R4
    R3 --> R4
```

## Branching Strategy

How feature branches flow through the auto-merge pipeline.

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
gitGraph
    commit id: "main"
    branch feat/3411-docs-audit
    checkout feat/3411-docs-audit
    commit id: "implement feature"
    commit id: "add tests"
    commit id: "update docs"
    checkout main
    merge feat/3411-docs-audit id: "squash merge docs" type: HIGHLIGHT
    commit id: "container build triggers"
    branch fix/3412-firmware-fix
    checkout fix/3412-firmware-fix
    commit id: "fix firmware logic"
    commit id: "add safety tests"
    checkout main
    merge fix/3412-firmware-fix id: "squash merge fix" type: HIGHLIGHT
    commit id: "v26.09.25 tag" tag: "v26.09.25"
```

---

## Related Diagrams

- [Architecture Overview](../core/architecture-overview.md) - System context showing CI/CD as external actor
- [Container Architecture](container-architecture.md) - What gets deployed
- [Development Workflow](../operations/development-workflow.md) - SpecKit feature lifecycle
